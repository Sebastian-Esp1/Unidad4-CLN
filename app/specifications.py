"""Specification Pattern (Parte 2): reglas de negocio que se combinan con & | ~.

Una Specification responde True/False sobre un pedido y NUNCA lo modifica.
    &  -> AND        |  -> OR        ~  -> NOT
"""
from decimal import Decimal


class Specification:
    def is_satisfied_by(self, order) -> bool:
        raise NotImplementedError

    def __and__(self, other):
        return AndSpec(self, other)

    def __or__(self, other):
        return OrSpec(self, other)

    def __invert__(self):
        return NotSpec(self)


class AndSpec(Specification):
    def __init__(self, left, right):
        self.left, self.right = left, right

    def is_satisfied_by(self, order) -> bool:
        return self.left.is_satisfied_by(order) and self.right.is_satisfied_by(order)


class OrSpec(Specification):
    def __init__(self, left, right):
        self.left, self.right = left, right

    def is_satisfied_by(self, order) -> bool:
        return self.left.is_satisfied_by(order) or self.right.is_satisfied_by(order)


class NotSpec(Specification):
    def __init__(self, spec):
        self.spec = spec

    def is_satisfied_by(self, order) -> bool:
        return not self.spec.is_satisfied_by(order)


# ------------------------------------------------------------ reglas simples
class MinimumAmountSpec(Specification):
    """Total ESTRICTAMENTE mayor que el umbral (un total igual al umbral NO cumple)."""

    def __init__(self, threshold: Decimal):
        self.threshold = threshold

    def is_satisfied_by(self, order) -> bool:
        return order.total.amount > self.threshold


class VIPCustomerSpec(Specification):
    def is_satisfied_by(self, order) -> bool:
        return order.customer.is_vip


class MinimumUnitsSpec(Specification):
    """Al menos `minimum` unidades (suma de cantidades)."""

    def __init__(self, minimum: int):
        self.minimum = minimum

    def is_satisfied_by(self, order) -> bool:
        return order.units >= self.minimum


class ActivePromotionSpec(Specification):
    def is_satisfied_by(self, order) -> bool:
        return order.has_promotion


# ------------------------------------------------------- reglas de descuento
# 10 %: cliente VIP, total > 500, al menos 4 unidades y SIN promoción.
ten_percent_rule = (
    MinimumAmountSpec(Decimal("500"))
    & VIPCustomerSpec()
    & MinimumUnitsSpec(4)
    & ~ActivePromotionSpec()
)

# 5 %: total > 5000 y SIN promoción.
five_percent_rule = MinimumAmountSpec(Decimal("5000")) & ~ActivePromotionSpec()

# Combinación con OR: ¿califica a algún descuento?
any_discount_rule = ten_percent_rule | five_percent_rule


def discount_rate(order) -> Decimal:
    """Tasa de descuento del pedido. Si cumple ambas reglas gana el 10 %."""
    if ten_percent_rule.is_satisfied_by(order):
        return Decimal("0.10")
    if five_percent_rule.is_satisfied_by(order):
        return Decimal("0.05")
    return Decimal("0")
