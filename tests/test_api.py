"""Pruebas de la API REST con TestClient (necesita httpx). Parte de Sebastian.

Ejecutar desde la raíz del proyecto:  python -m pytest -q
"""
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient

from app import api


@pytest.fixture(autouse=True)
def fresh_state():
    """Cada prueba empieza con los 16 pedidos en DRAFT."""
    api.reload_fixtures()
    yield


client = TestClient(api.app)


def test_get_o001():
    r = client.get("/orders/O001")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "DRAFT" and body["units"] == 4
    assert Decimal(body["total"]) == Decimal("2100.00")


def test_listar_carga_16_pedidos():
    r = client.get("/orders")
    assert r.status_code == 200 and len(r.json()) == 16


def test_pedido_inexistente_404_en_get_y_confirm():
    assert client.get("/orders/O999").status_code == 404
    assert client.post("/orders/O999/confirm").status_code == 404


def test_confirmar_ok_200():
    r = client.post("/orders/O013/confirm")
    assert r.status_code == 200
    assert r.json()["status"] == "CONFIRMED"
    assert r.json()["events"] == ["OrderConfirmed"]


def test_confirmar_20_unidades_permitidas_200():
    assert client.post("/orders/O008/confirm").status_code == 200


def test_confirmar_dos_veces_409_sin_nuevo_evento():
    assert client.post("/orders/O013/confirm").status_code == 200
    r = client.post("/orders/O013/confirm")
    assert r.status_code == 409
    assert client.get("/orders/O013").json()["events"] == ["OrderConfirmed"]


def test_confirmar_pedido_vacio_422():
    r = client.post("/orders/O007/confirm")
    assert r.status_code == 422
    assert client.get("/orders/O007").json()["status"] == "DRAFT"


def test_confirmar_cliente_inactivo_422():
    assert client.post("/orders/O003/confirm").status_code == 422


def test_enviar_sin_guia_422_y_sigue_confirmed():
    client.post("/orders/O012/confirm")
    r = client.post("/orders/O012/ship", json={"tracking_number": ""})
    assert r.status_code == 422
    assert client.get("/orders/O012").json()["status"] == "CONFIRMED"


def test_enviar_sin_cuerpo_422():
    client.post("/orders/O012/confirm")
    assert client.post("/orders/O012/ship").status_code == 422


def test_enviar_con_guia_200():
    client.post("/orders/O012/confirm")
    r = client.post("/orders/O012/ship", json={"tracking_number": "GUIA-123"})
    assert r.status_code == 200 and r.json()["status"] == "SHIPPED"


def test_cancelar_desde_confirmed_200():
    client.post("/orders/O014/confirm")
    r = client.post("/orders/O014/cancel", json={"reason": "cliente se arrepintió"})
    assert r.status_code == 200 and r.json()["status"] == "CANCELLED"


def test_cancelar_sin_motivo_422():
    client.post("/orders/O014/confirm")
    r = client.post("/orders/O014/cancel", json={"reason": ""})
    assert r.status_code == 422


def test_cancelar_desde_shipped_409():
    client.post("/orders/O014/confirm")
    client.post("/orders/O014/ship", json={"tracking_number": "G-14"})
    r = client.post("/orders/O014/cancel", json={"reason": "tarde"})
    assert r.status_code == 409
    assert client.get("/orders/O014").json()["status"] == "SHIPPED"


def test_devolucion_y_entrega_200():
    for oid, accion, final in (("O015", "return", "RETURNED"), ("O016", "deliver", "DELIVERED")):
        client.post(f"/orders/{oid}/confirm")
        client.post(f"/orders/{oid}/ship", json={"tracking_number": f"G-{oid}"})
        r = client.post(f"/orders/{oid}/{accion}")
        assert r.status_code == 200 and r.json()["status"] == final


def test_entregar_desde_draft_409():
    assert client.post("/orders/O016/deliver").status_code == 409


def test_reload_restaura_estado():
    client.post("/orders/O013/confirm")
    assert client.post("/fixtures/reload").json() == {"loaded": 16}
    assert client.get("/orders/O013").json()["status"] == "DRAFT"


def test_openapi_documenta_las_rutas():
    paths = client.get("/openapi.json").json()["paths"]
    assert "/orders/{order_id}/confirm" in paths and "/orders/{order_id}/ship" in paths
