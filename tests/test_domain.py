"""Pruebas del dominio: Value Objects, Order y máquina de estados."""
import dataclasses
from decimal import Decimal

import pytest

from app.domain import (
    Customer, InvalidOrderData, InvalidOrderTransition, Money, Order,
    OrderItem, OrderItemLimitExceeded, OrderStatus,
)


def item(sku="SKU001", qty=1, price="100"):
    return OrderItem(sku, qty, Money(Decimal(price)))


def order_with(units=1, active=True, vip=False, promo=False):
    o = Order(customer=Customer("C", vip, active), id="T1", has_promotion=promo)
    if units:
        o.add_item(item(qty=units))
    return o


# ---------------- Value Objects ----------------
def test_money_negativo_rechazado():
    with pytest.raises(InvalidOrderData):
        Money(Decimal("-1"))


def test_money_rechaza_float():
    with pytest.raises(InvalidOrderData):
        Money(10.5)


def test_money_add_devuelve_objeto_nuevo():
    a, b = Money(Decimal("1.10")), Money(Decimal("2.20"))
    assert a.add(b).amount == Decimal("3.30")
    assert a.amount == Decimal("1.10")


def test_money_add_monedas_distintas_rechazado():
    with pytest.raises(InvalidOrderData):
        Money(Decimal("1")).add(Money(Decimal("1"), "USD"))


def test_money_es_inmutable():
    m = Money(Decimal("5"))
    with pytest.raises(dataclasses.FrozenInstanceError):
        m.amount = Decimal("6")


def test_item_cantidad_cero_o_negativa_rechazada():
    for qty in (0, -3):
        with pytest.raises(InvalidOrderData):
            item(qty=qty)


def test_item_sku_vacio_rechazado():
    with pytest.raises(InvalidOrderData):
        item(sku="  ")


def test_item_subtotal_se_calcula():
    assert item(qty=2, price="600.00").subtotal.amount == Decimal("1200.00")


# ---------------- Order: datos y límite ----------------
def test_pedido_o001_inicia_draft_con_4_unidades_y_2100(orders):
    o = orders["O001"]
    assert o.status == OrderStatus.DRAFT
    assert o.units == 4
    assert o.total.amount == Decimal("2100.00")
    assert o.events == []


def test_cargan_16_pedidos_en_draft(orders):
    assert len(orders) == 16
    assert all(o.status == OrderStatus.DRAFT for o in orders.values())


def test_units_suma_cantidades_no_renglones(orders):
    assert len(orders["O008"].items) == 1 and orders["O008"].units == 20


def test_21_unidades_rechazadas_y_no_se_agrega(orders):
    o = orders["O009"]  # ya tiene 19
    with pytest.raises(OrderItemLimitExceeded):
        o.add_item(OrderItem("SKU003", 2, Money(Decimal("120.00"))))
    assert o.units == 19


def test_20_unidades_exactas_permitidas():
    o = order_with(units=19)
    o.add_item(item(qty=1))
    assert o.units == 20


def test_no_se_agregan_articulos_si_no_es_draft():
    o = order_with()
    o.confirm()
    with pytest.raises(InvalidOrderTransition):
        o.add_item(item())


def test_moneda_distinta_de_mxn_rechazada():
    o = Order(customer=Customer("C"), id="T")
    with pytest.raises(InvalidOrderData):
        o.add_item(OrderItem("SKU", 1, Money(Decimal("1"), "USD")))


def test_total_exacto_500_de_o010(orders):
    assert orders["O010"].total.amount == Decimal("500.00")


# ---------------- máquina de estados ----------------
def test_confirmar_cambia_estado_y_registra_un_evento(orders):
    o = orders["O013"]
    o.confirm()
    assert o.status == OrderStatus.CONFIRMED
    assert [e.name for e in o.events] == ["OrderConfirmed"]


def test_confirmar_dos_veces_falla_sin_nuevo_evento(orders):
    o = orders["O013"]
    o.confirm()
    with pytest.raises(InvalidOrderTransition):
        o.confirm()
    assert len(o.events) == 1


def test_confirmar_pedido_vacio_falla(orders):
    o = orders["O007"]
    with pytest.raises(InvalidOrderData):
        o.confirm()
    assert o.status == OrderStatus.DRAFT and o.events == []


def test_confirmar_cliente_inactivo_falla(orders):
    o = orders["O003"]
    with pytest.raises(InvalidOrderData):
        o.confirm()
    assert o.status == OrderStatus.DRAFT and o.events == []


def test_confirmar_20_unidades_ok(orders):
    orders["O008"].confirm()
    assert orders["O008"].status == OrderStatus.CONFIRMED


def test_enviar_sin_guia_falla_y_sigue_confirmed(orders):
    o = orders["O012"]
    o.confirm()
    for guia in ("", "   ", None):
        with pytest.raises(InvalidOrderData):
            o.ship(guia)
    assert o.status == OrderStatus.CONFIRMED
    assert [e.name for e in o.events] == ["OrderConfirmed"]


def test_enviar_desde_draft_falla(orders):
    with pytest.raises(InvalidOrderTransition):
        orders["O012"].ship("G-1")


def test_enviar_ok(orders):
    o = orders["O012"]
    o.confirm(); o.ship("G-1")
    assert o.status == OrderStatus.SHIPPED
    assert [e.name for e in o.events] == ["OrderConfirmed", "OrderShipped"]


def test_cancelar_desde_confirmed_con_motivo(orders):
    o = orders["O014"]
    o.confirm(); o.cancel("cliente se arrepintió")
    assert o.status == OrderStatus.CANCELLED
    assert o.events[-1].name == "OrderCancelled"


def test_cancelar_sin_motivo_falla(orders):
    o = orders["O014"]
    o.confirm()
    with pytest.raises(InvalidOrderData):
        o.cancel("  ")
    assert o.status == OrderStatus.CONFIRMED


def test_cancelar_desde_shipped_falla_sin_cambios(orders):
    o = orders["O014"]
    o.confirm(); o.ship("G-14")
    with pytest.raises(InvalidOrderTransition):
        o.cancel("tarde")
    assert o.status == OrderStatus.SHIPPED
    assert [e.name for e in o.events] == ["OrderConfirmed", "OrderShipped"]


def test_entregar_y_devolver_desde_shipped(orders):
    a, b = orders["O016"], orders["O015"]
    for o in (a, b):
        o.confirm(); o.ship("G")
    a.deliver(); b.return_order()
    assert a.status == OrderStatus.DELIVERED and a.events[-1].name == "OrderDelivered"
    assert b.status == OrderStatus.RETURNED and b.events[-1].name == "OrderReturned"


def test_entregar_o_devolver_fuera_de_shipped_falla(orders):
    o = orders["O016"]
    with pytest.raises(InvalidOrderTransition):
        o.deliver()
    with pytest.raises(InvalidOrderTransition):
        o.return_order()
    assert o.events == []


def test_estados_finales_no_aceptan_mas_operaciones(orders):
    o = orders["O015"]
    o.confirm(); o.ship("G"); o.return_order()
    for op in (o.confirm, o.deliver, o.return_order):
        with pytest.raises(InvalidOrderTransition):
            op()
    with pytest.raises(InvalidOrderTransition):
        o.ship("G2")
    with pytest.raises(InvalidOrderTransition):
        o.cancel("x")
