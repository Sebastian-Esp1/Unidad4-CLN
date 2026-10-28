"""Carga clientes, catálogo, pedidos y detalles desde ./datos."""
import csv
from decimal import Decimal
from pathlib import Path
from app.domain import Customer, Money, Order, OrderItem

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "datos"


def _read_csv(filename):
    path = DATA_DIR / filename
    if not path.exists():
        raise FileNotFoundError(f"No se encontró {path}.")
    with path.open("r", encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def _truth(value):
    return str(value).strip().lower() in {"1", "true", "sí", "si", "yes", "y"}


def load_fixture():
    customers = {}
    for row in _read_csv("clientes.csv"):
        customer_id = row.get("cliente_id") or row.get("id") or row.get("customer_id")
        customers[customer_id] = Customer(
            id=customer_id,
            is_vip=_truth(row.get("es_vip", row.get("is_vip", "0"))),
            active=_truth(row.get("activo", row.get("active", "1"))),
        )

    products = {}
    for row in _read_csv("productos.csv"):
        sku = row.get("sku") or row.get("producto_id")
        price = row.get("precio_mxn", row.get("price", "0"))
        products[sku] = Money(Decimal(str(price)))

    orders = {}
    for row in _read_csv("pedidos.csv"):
        order_id = row.get("pedido_id") or row.get("id")
        customer_id = row.get("cliente_id") or row.get("customer_id")
        promotion = _truth(row.get("promocion_activa", row.get("has_promotion", "0")))
        orders[order_id] = Order(customer=customers[customer_id], id=order_id, has_promotion=promotion)

    for row in _read_csv("detalle_pedidos.csv"):
        order_id = row.get("pedido_id")
        sku = row.get("sku")
        quantity = int(row.get("cantidad", "0"))
        orders[order_id].add_item(OrderItem(sku, quantity, products[sku]))

    return orders


if __name__ == "__main__":
    orders = load_fixture()
    for order in orders.values():
        print(
            f"{order.id} | {order.status.value} | unidades={order.units} | "
            f"total=${order.total.amount:.2f} MXN | descuento={order.discount_rate:.0%}"
        )
