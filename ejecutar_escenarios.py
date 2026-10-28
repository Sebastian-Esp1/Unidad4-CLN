"""Ejecuta los 15 escenarios E01–E15 de datos/escenarios.csv sobre el dominio.

Uso (desde la raíz del proyecto):   python ejecutar_escenarios.py
Cada escenario carga los datos de nuevo para no arrastrar estado del caso anterior.
Sirve para llenar la bitácora: caso, estado inicial, operación, resultado real,
estado final y eventos emitidos (o «ninguno» si la operación falló).
"""
import json
import sys
from decimal import Decimal

from app.domain import DomainException, Money, OrderItem
from app.specifications import discount_rate
from cargar_csv import load_fixture


def _descuento(order):
    return f"Descuento {int(discount_rate(order) * 100)} %"


def _confirmar(order):
    order.confirm()
    return "Éxito: pedido confirmado"


def _agregar_21(order):
    order.add_item(OrderItem("SKU003", 2, Money(Decimal("120.00"))))
    return "Éxito"


def _enviar_sin_guia(order):
    order.confirm()          # la confirmación sí es válida
    order.ship("")           # falta la guía
    return "Éxito"


def _confirmar_dos_veces(order):
    order.confirm()
    order.confirm()
    return "Éxito"


def _cancelar_enviado(order):
    order.confirm(); order.ship("GUIA-14"); order.cancel("ya no lo quiere")
    return "Éxito"


def _devolver(order):
    order.confirm(); order.ship("GUIA-15"); order.return_order()
    return "Éxito: pedido devuelto"


def _entregar(order):
    order.confirm(); order.ship("GUIA-16"); order.deliver()
    return "Éxito: pedido entregado"


ESCENARIOS = [
    ("E01", "O001", "Evaluar descuento", _descuento),
    ("E02", "O002", "Evaluar descuento", _descuento),
    ("E03", "O003", "Confirmar (cliente inactivo)", _confirmar),
    ("E04", "O005", "Evaluar descuento (promoción activa)", _descuento),
    ("E05", "O006", "Evaluar descuento", _descuento),
    ("E06", "O007", "Confirmar (sin artículos)", _confirmar),
    ("E07", "O008", "Confirmar (20 unidades)", _confirmar),
    ("E08", "O009", "Agregar SKU003 x 2 (ya tiene 19 unidades)", _agregar_21),
    ("E09", "O010", "Evaluar descuento (total exactamente 500)", _descuento),
    ("E10", "O011", "Evaluar descuento (3 unidades)", _descuento),
    ("E11", "O012", "Confirmar y enviar sin guía", _enviar_sin_guia),
    ("E12", "O013", "Confirmar dos veces", _confirmar_dos_veces),
    ("E13", "O014", "Confirmar, enviar y cancelar", _cancelar_enviado),
    ("E14", "O015", "Confirmar, enviar y devolver", _devolver),
    ("E15", "O016", "Confirmar, enviar y entregar", _entregar),
]


def ejecutar():
    filas = []
    for caso, pedido, operacion, accion in ESCENARIOS:
        order = load_fixture()[pedido]
        inicial = order.status.value
        try:
            resultado = accion(order)
        except DomainException as exc:
            resultado = f"Rechazo ({type(exc).__name__}): {exc}"
        eventos = [e.name for e in order.events]
        filas.append({
            "caso": caso, "pedido": pedido, "estado_inicial": inicial, "operacion": operacion,
            "resultado": resultado, "estado_final": order.status.value,
            "eventos": ", ".join(eventos) if eventos else "ninguno",
        })
    return filas


if __name__ == "__main__":
    filas = ejecutar()
    if "--json" in sys.argv:
        print(json.dumps(filas, ensure_ascii=False, indent=2))
    else:
        for f in filas:
            print(f"{f['caso']} {f['pedido']} | {f['estado_inicial']} -> {f['estado_final']} | "
                  f"{f['operacion']} | {f['resultado']} | eventos: {f['eventos']}")
