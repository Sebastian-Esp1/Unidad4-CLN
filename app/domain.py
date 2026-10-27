"""Núcleo de negocio de TechStore (Partes 1 y 3).

Aquí viven las reglas de los pedidos. Ninguna otra capa (API, servicio, pruebas)
debe repetirlas. Toda operación sigue el mismo orden:
    1) validar  ->  2) cambiar el estado  ->  3) registrar el evento.
Si algo falla en el paso 1, el pedido NO cambia y NO se registra ningún evento.
"""
from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal
from enum import Enum


# ---------------------------------------------------------------- excepciones
class DomainException(Exception):
    """Violación de una regla del negocio."""


class InvalidOrderData(DomainException):
    """Datos o precondiciones inválidos (monto negativo, pedido vacío, guía vacía...)."""


class InvalidOrderTransition(DomainException):
    """El estado actual del pedido no permite la operación pedida."""


class OrderItemLimitExceeded(DomainException):
    """El pedido superaría el máximo de unidades permitido."""


MAX_UNITS = 20
CURRENCY = "MXN"


# ------------------------------------------------------------- Value Objects
@dataclass(frozen=True)
class Money:
    """Dinero: inmutable, con Decimal (nunca float) y sin importes negativos."""

    amount: Decimal
    currency: str = CURRENCY

    def __post_init__(self):
        if not isinstance(self.amount, Decimal):
            raise InvalidOrderData("El monto debe ser Decimal, no float ni int")
        if not self.amount.is_finite() or self.amount < 0:
            raise InvalidOrderData("Monto inválido")

    def add(self, other: "Money") -> "Money":
        if self.currency != other.currency:
            raise InvalidOrderData("Monedas distintas")
        return Money(self.amount + other.amount, self.currency)


@dataclass(frozen=True)
class OrderItem:
    """Un producto del pedido con su cantidad y precio unitario."""

    sku: str
    quantity: int
    unit_price: Money

    def __post_init__(self):
        if not isinstance(self.sku, str) or not self.sku.strip():
            raise InvalidOrderData("Artículo inválido: SKU vacío")
        if not isinstance(self.quantity, int) or isinstance(self.quantity, bool) or self.quantity <= 0:
            raise InvalidOrderData("Artículo inválido: la cantidad debe ser mayor que 0")
        if not isinstance(self.unit_price, Money):
            raise InvalidOrderData("Artículo inválido: precio unitario inválido")

    @property
    def subtotal(self) -> Money:
        # Se calcula; nunca se captura a mano (evita discrepancias).
        return Money(self.unit_price.amount * self.quantity, self.unit_price.currency)


@dataclass(frozen=True)
class Customer:
    id: str
    is_vip: bool = False
    active: bool = True


# ------------------------------------------------------------ estados y eventos
class OrderStatus(str, Enum):
    DRAFT = "DRAFT"
    CONFIRMED = "CONFIRMED"
    SHIPPED = "SHIPPED"
    DELIVERED = "DELIVERED"
    CANCELLED = "CANCELLED"
    RETURNED = "RETURNED"


@dataclass(frozen=True)
class DomainEvent:
    """Hecho del negocio que YA ocurrió."""

    name: str
    order_id: str
    occurred_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


# ------------------------------------------------------------- Aggregate Root
@dataclass
class Order:
    customer: Customer
    id: str
    has_promotion: bool = False
    status: OrderStatus = OrderStatus.DRAFT
    items: list = field(default_factory=list)
    events: list = field(default_factory=list)

    # --- consultas ---
    @property
    def units(self) -> int:
        """Suma de CANTIDADES (no cuenta renglones)."""
        return sum(item.quantity for item in self.items)

    @property
    def total(self) -> Money:
        amount = sum((item.subtotal.amount for item in self.items), Decimal("0"))
        return Money(amount)

    # --- artículos ---
    def add_item(self, item: OrderItem) -> None:
        if self.status != OrderStatus.DRAFT:
            raise InvalidOrderTransition("Solo un pedido DRAFT admite artículos")
        if item.unit_price.currency != CURRENCY:
            raise InvalidOrderData("Solo se admite MXN")
        if self.units + item.quantity > MAX_UNITS:
            raise OrderItemLimitExceeded(f"Máximo {MAX_UNITS} unidades por pedido")
        self.items.append(item)

    # --- máquina de estados ---
    def _record(self, event_name: str) -> None:
        self.events.append(DomainEvent(event_name, self.id))

    def _require_status(self, expected: OrderStatus, action: str) -> None:
        if self.status != expected:
            raise InvalidOrderTransition(
                f"No se puede {action} un pedido en estado {self.status.value}; se requiere {expected.value}"
            )

    def confirm(self) -> None:
        self._require_status(OrderStatus.DRAFT, "confirmar")
        if not self.items:
            raise InvalidOrderData("No se puede confirmar un pedido sin artículos")
        if not self.customer.active:
            raise InvalidOrderData("No se puede confirmar: el cliente está inactivo")
        self.status = OrderStatus.CONFIRMED
        self._record("OrderConfirmed")

    def ship(self, tracking_number: str) -> None:
        self._require_status(OrderStatus.CONFIRMED, "enviar")
        if not isinstance(tracking_number, str) or not tracking_number.strip():
            raise InvalidOrderData("El envío requiere un número de guía")
        self.status = OrderStatus.SHIPPED
        self._record("OrderShipped")

    def cancel(self, reason: str) -> None:
        self._require_status(OrderStatus.CONFIRMED, "cancelar")
        if not isinstance(reason, str) or not reason.strip():
            raise InvalidOrderData("La cancelación requiere un motivo")
        self.status = OrderStatus.CANCELLED
        self._record("OrderCancelled")

    def deliver(self) -> None:
        self._require_status(OrderStatus.SHIPPED, "entregar")
        self.status = OrderStatus.DELIVERED
        self._record("OrderDelivered")

    def return_order(self) -> None:
        self._require_status(OrderStatus.SHIPPED, "devolver")
        self.status = OrderStatus.RETURNED
        self._record("OrderReturned")
