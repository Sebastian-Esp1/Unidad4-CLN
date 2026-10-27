"""Application Service de TechStore (parte de Sebastian, bloque 04).

Coordina: busca el pedido, llama al método de Order y devuelve una vista.
NO contiene reglas de negocio: todas viven en app/domain.py. Si una operación
es inválida, Order lanza una excepción de dominio y el servicio la deja pasar;
la capa HTTP (app/api.py) la traduce a un código de estado.
"""
from __future__ import annotations


class OrderNotFound(Exception):
    """El pedido pedido no existe en el repositorio en memoria."""


def to_view(order) -> dict:
    """DTO de lectura. No se reutiliza como modelo de escritura."""
    return {
        "id": order.id,
        "customer_id": order.customer.id,
        "status": order.status.value,
        "units": order.units,
        "total": str(order.total.amount),
        "currency": order.total.currency,
        "has_promotion": order.has_promotion,
        "items": [
            {
                "sku": i.sku,
                "quantity": i.quantity,
                "unit_price": str(i.unit_price.amount),
                "subtotal": str(i.subtotal.amount),
            }
            for i in order.items
        ],
        "events": [e.name for e in order.events],
    }


class OrderService:
    def __init__(self, orders: dict):
        self._orders = orders  # repositorio en memoria: {order_id: Order}

    def _get(self, order_id: str):
        order = self._orders.get(order_id)
        if order is None:
            raise OrderNotFound(f"No existe el pedido {order_id}")
        return order

    def list_orders(self) -> list[dict]:
        return [
            {"id": o.id, "status": o.status.value, "units": o.units, "total": str(o.total.amount)}
            for o in self._orders.values()
        ]

    def get(self, order_id: str) -> dict:
        return to_view(self._get(order_id))

    def confirm(self, order_id: str) -> dict:
        order = self._get(order_id)
        order.confirm()
        return to_view(order)

    def ship(self, order_id: str, tracking_number: str) -> dict:
        order = self._get(order_id)
        order.ship(tracking_number)
        return to_view(order)

    def cancel(self, order_id: str, reason: str) -> dict:
        order = self._get(order_id)
        order.cancel(reason)
        return to_view(order)

    def deliver(self, order_id: str) -> dict:
        order = self._get(order_id)
        order.deliver()
        return to_view(order)

    def return_order(self, order_id: str) -> dict:
        order = self._get(order_id)
        order.return_order()
        return to_view(order)
