"""Pruebas del Specification Pattern y de las reglas de descuento (E01, E02, E04, E05, E09, E10)."""
from decimal import Decimal

from app.domain import Customer, Money, Order, OrderItem
from app.specifications import (
    ActivePromotionSpec, MinimumAmountSpec, MinimumUnitsSpec, Specification,
    VIPCustomerSpec, discount_rate, five_percent_rule, ten_percent_rule,
)


class Always(Specification):
    def __init__(self, value):
        self.value = value

    def is_satisfied_by(self, order):
        return self.value


def make(price="100", qty=1, vip=False, promo=False):
    o = Order(customer=Customer("C", vip), id="T", has_promotion=promo)
    o.add_item(OrderItem("SKU", qty, Money(Decimal(price))))
    return o


# ---------------- composición ----------------
def test_and_or_not_tabla_de_verdad():
    T, F = Always(True), Always(False)
    assert (T & T).is_satisfied_by(None) and not (T & F).is_satisfied_by(None)
    assert (T | F).is_satisfied_by(None) and not (F | F).is_satisfied_by(None)
    assert (~F).is_satisfied_by(None) and not (~T).is_satisfied_by(None)


def test_composicion_anidada():
    T, F = Always(True), Always(False)
    assert ((T & ~F) | F).is_satisfied_by(None)


# ---------------- reglas simples ----------------
def test_monto_minimo_es_estrictamente_mayor():
    spec = MinimumAmountSpec(Decimal("500"))
    assert not spec.is_satisfied_by(make(price="500"))
    assert spec.is_satisfied_by(make(price="500.01"))


def test_unidades_minimas_son_al_menos():
    spec = MinimumUnitsSpec(4)
    assert not spec.is_satisfied_by(make(qty=3))
    assert spec.is_satisfied_by(make(qty=4))


def test_vip_y_promocion():
    assert VIPCustomerSpec().is_satisfied_by(make(vip=True))
    assert not VIPCustomerSpec().is_satisfied_by(make(vip=False))
    assert ActivePromotionSpec().is_satisfied_by(make(promo=True))
    assert not ActivePromotionSpec().is_satisfied_by(make(promo=False))


def test_la_specification_no_modifica_el_pedido():
    o = make(vip=True, qty=4)
    antes = (o.status, o.units, o.total.amount, list(o.events))
    ten_percent_rule.is_satisfied_by(o)
    assert (o.status, o.units, o.total.amount, list(o.events)) == antes


# ---------------- reglas de descuento ----------------
def test_diez_por_ciento_requiere_las_cuatro_condiciones():
    base = dict(price="150", qty=4, vip=True, promo=False)
    assert ten_percent_rule.is_satisfied_by(make(**base))
    assert not ten_percent_rule.is_satisfied_by(make(**{**base, "vip": False}))
    assert not ten_percent_rule.is_satisfied_by(make(**{**base, "qty": 3}))
    assert not ten_percent_rule.is_satisfied_by(make(**{**base, "promo": True}))
    assert not ten_percent_rule.is_satisfied_by(make(**{**base, "price": "125"}))  # total 500 exacto


def test_cinco_por_ciento_requiere_mas_de_5000_y_sin_promocion():
    assert five_percent_rule.is_satisfied_by(make(price="5000.01"))
    assert not five_percent_rule.is_satisfied_by(make(price="5000"))
    assert not five_percent_rule.is_satisfied_by(make(price="9000", promo=True))


def test_si_cumple_ambas_gana_el_diez_por_ciento():
    o = make(price="2000", qty=4, vip=True)  # total 8000, VIP, 4 unidades
    assert ten_percent_rule.is_satisfied_by(o) and five_percent_rule.is_satisfied_by(o)
    assert discount_rate(o) == Decimal("0.10")


# ---------------- escenarios del paquete ----------------
def test_e01_o001_diez_por_ciento(orders):
    assert discount_rate(orders["O001"]) == Decimal("0.10")


def test_e02_o002_cero(orders):
    assert discount_rate(orders["O002"]) == Decimal("0")


def test_e04_o005_promocion_activa_bloquea(orders):
    assert discount_rate(orders["O005"]) == Decimal("0")


def test_e05_o006_cinco_por_ciento(orders):
    assert discount_rate(orders["O006"]) == Decimal("0.05")


def test_e09_o010_umbral_estricto(orders):
    assert orders["O010"].total.amount == Decimal("500.00")
    assert discount_rate(orders["O010"]) == Decimal("0")


def test_e10_o011_solo_tres_unidades(orders):
    assert orders["O011"].units == 3
    assert discount_rate(orders["O011"]) == Decimal("0")
