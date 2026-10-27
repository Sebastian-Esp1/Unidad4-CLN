"""Pruebas del Application Service (sin HTTP). Parte de Sebastian."""
from decimal import Decimal

import pytest

from app.domain import InvalidOrderData, InvalidOrderTransition
from app.services import OrderNotFound, OrderService


@pytest.fixture
def service(orders):
    return OrderService(orders)


def test_get_o001_inicia_draft_con_4_unidades_y_2100(service):
    view = service.get("O001")
    assert view["status"] == "DRAFT"
    assert view["units"] == 4
    assert Decimal(view["total"]) == Decimal("2100.00")
    assert view["events"] == []


def test_pedido_inexistente_lanza_not_found(service):
    with pytest.raises(OrderNotFound):
        service.get("O999")
    with pytest.raises(OrderNotFound):
        service.confirm("O999")


def test_confirmar_cambia_estado_y_registra_un_evento(service):
    view = service.confirm("O013")
    assert view["status"] == "CONFIRMED"
    assert view["events"] == ["OrderConfirmed"]


def test_confirmar_dos_veces_falla_y_no_agrega_evento(service):
    service.confirm("O013")
    with pytest.raises(InvalidOrderTransition):
        service.confirm("O013")
    view = service.get("O013")
    assert view["status"] == "CONFIRMED"
    assert view["events"] == ["OrderConfirmed"]


def test_confirmar_pedido_vacio_falla_y_sigue_draft(service):
    with pytest.raises(InvalidOrderData):
        service.confirm("O007")
    view = service.get("O007")
    assert view["status"] == "DRAFT" and view["events"] == []


def test_confirmar_cliente_inactivo_falla(service):
    with pytest.raises(InvalidOrderData):
        service.confirm("O003")
    assert service.get("O003")["status"] == "DRAFT"


def test_enviar_sin_guia_falla_y_sigue_confirmed(service):
    service.confirm("O012")
    with pytest.raises(InvalidOrderData):
        service.ship("O012", "")
    view = service.get("O012")
    assert view["status"] == "CONFIRMED"
    assert view["events"] == ["OrderConfirmed"]


def test_cancelar_desde_shipped_falla(service):
    service.confirm("O014")
    service.ship("O014", "GUIA-001")
    with pytest.raises(InvalidOrderTransition):
        service.cancel("O014", "ya no lo quiere")
    view = service.get("O014")
    assert view["status"] == "SHIPPED"
    assert view["events"] == ["OrderConfirmed", "OrderShipped"]


def test_cancelar_sin_motivo_falla(service):
    service.confirm("O014")
    with pytest.raises(InvalidOrderData):
        service.cancel("O014", "  ")
    assert service.get("O014")["status"] == "CONFIRMED"


def test_flujo_devolucion_y_entrega(service):
    service.confirm("O015"); service.ship("O015", "G-15")
    assert service.return_order("O015")["status"] == "RETURNED"
    service.confirm("O016"); service.ship("O016", "G-16")
    assert service.deliver("O016")["status"] == "DELIVERED"
