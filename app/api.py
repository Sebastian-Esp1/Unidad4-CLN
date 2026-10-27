"""API REST de TechStore U4 (FastAPI). Parte de Sebastian, bloque 04.

Un controlador solo: (1) recibe la solicitud, (2) llama al OrderService,
(3) devuelve la respuesta. Las validaciones de negocio NO se copian aquí.

Traducción de errores (un solo lugar, ver handlers al final):
    OrderNotFound            -> 404 Not Found
    InvalidOrderTransition   -> 409 Conflict          (estado no permite la operación)
    InvalidOrderData         -> 422 Unprocessable     (datos o precondición inválidos)
    OrderItemLimitExceeded   -> 422 Unprocessable     (regla de máximo 20 unidades)
    cualquier DomainException-> 400 Bad Request

Ejecutar:  uvicorn app.api:app --reload      Documentación: /docs   Contrato: /openapi.json
"""
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from app.domain import (
    DomainException,
    InvalidOrderData,
    InvalidOrderTransition,
    OrderItemLimitExceeded,
)
from app.services import OrderNotFound, OrderService
from cargar_csv import load_fixture

app = FastAPI(
    title="TechStore U4",
    version="1.0.0",
    description=(
        "API REST sobre el núcleo de negocio de TechStore. Repositorio en memoria: "
        "los cambios se pierden al reiniciar. Los pedidos inician en DRAFT."
    ),
)

# Repositorio en memoria cargado al iniciar. Se comparte con el servicio.
orders: dict = load_fixture()
service = OrderService(orders)


def reload_fixtures() -> None:
    """Restaura los 16 pedidos a DRAFT (útil para pruebas y para las capturas de Swagger)."""
    orders.clear()
    orders.update(load_fixture())


# ---------- cuerpos de solicitud ----------
class ShipRequest(BaseModel):
    tracking_number: str = Field(description="Número de guía. El dominio rechaza una guía vacía.")


class CancelRequest(BaseModel):
    reason: str = Field(description="Motivo de la cancelación. El dominio rechaza un motivo vacío.")


# ---------- documentación de errores en Swagger ----------
R404 = {"description": "El pedido no existe"}
R409 = {"description": "Transición no permitida desde el estado actual"}
R422 = {"description": "Datos o precondiciones inválidos (guía/motivo vacío, pedido vacío, cliente inactivo...)"}


# ---------- endpoints ----------
@app.get("/orders", summary="Listar pedidos")
def list_orders():
    return service.list_orders()


@app.get("/orders/{order_id}", summary="Consultar un pedido", responses={404: R404})
def get_order(order_id: str):
    return service.get(order_id)


@app.post("/orders/{order_id}/confirm", summary="Confirmar pedido (DRAFT -> CONFIRMED)",
          responses={404: R404, 409: R409, 422: R422})
def confirm_order(order_id: str):
    return service.confirm(order_id)


@app.post("/orders/{order_id}/ship", summary="Enviar pedido (CONFIRMED -> SHIPPED)",
          responses={404: R404, 409: R409, 422: R422})
def ship_order(order_id: str, body: ShipRequest):
    return service.ship(order_id, body.tracking_number)


@app.post("/orders/{order_id}/cancel", summary="Cancelar pedido (CONFIRMED -> CANCELLED)",
          responses={404: R404, 409: R409, 422: R422})
def cancel_order(order_id: str, body: CancelRequest):
    return service.cancel(order_id, body.reason)


@app.post("/orders/{order_id}/deliver", summary="Entregar pedido (SHIPPED -> DELIVERED)",
          responses={404: R404, 409: R409})
def deliver_order(order_id: str):
    return service.deliver(order_id)


@app.post("/orders/{order_id}/return", summary="Devolver pedido (SHIPPED -> RETURNED)",
          responses={404: R404, 409: R409})
def return_order(order_id: str):
    return service.return_order(order_id)


@app.post("/fixtures/reload", summary="Recargar los 16 pedidos (solo didáctico)")
def reload_endpoint():
    reload_fixtures()
    return {"loaded": len(orders)}


# ---------- manejo de excepciones de dominio -> HTTP ----------
def _error(status: int):
    async def handler(request, exc):
        return JSONResponse(status_code=status, content={"detail": str(exc)})
    return handler


app.add_exception_handler(OrderNotFound, _error(404))
app.add_exception_handler(InvalidOrderTransition, _error(409))
app.add_exception_handler(InvalidOrderData, _error(422))
app.add_exception_handler(OrderItemLimitExceeded, _error(422))
app.add_exception_handler(DomainException, _error(400))
