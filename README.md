# TechStore U4 – Núcleo de negocio con API REST

**Universidad Autónoma de Nuevo León – FIME**
**Materia:** Componentes de lógica de negocios · **Unidad 4:** Desarrollo de componentes de negocio
**Docente:** Miguel Ángel Gómez Marroquín · **Equipo:** 3

| Nombre | Matrícula | Carrera |
|---|---|---|
| Jaime Sebastian Esparza Leyva | 2097304 | ITS |
| Alan Joel Sánchez García | 2082464 | ITS |
| Jorge Alejandro Jiménez González | 2097849 | ITS |

## 1. Qué es

Programa para administrar pedidos de una tienda ficticia (TechStore). Lee clientes, productos y pedidos de archivos CSV, los convierte en objetos del dominio, aplica reglas de descuento con Specifications, controla el estado de cada pedido con una máquina de estados y expone las operaciones mediante una API REST (FastAPI). Los datos viven en memoria: al cerrar el programa, los cambios se pierden.

## 2. Estructura del repositorio

| Ruta | Contenido |
|---|---|
| `app/domain.py` | Money, Customer, OrderItem, Order (Aggregate Root), OrderStatus, DomainEvent y excepciones de dominio |
| `app/specifications.py` | Specification Pattern con composición AND / OR / NOT y reglas de descuento |
| `app/services.py` | Application Service (`OrderService`): coordina, no contiene reglas |
| `app/api.py` | API REST con FastAPI y traducción de excepciones a códigos HTTP |
| `tests/` | Pruebas pytest del dominio, las Specifications, el servicio y la API |
| `datos/` | CSV del paquete: clientes, productos, pedidos, detalle de pedidos y escenarios |
| `cargar_csv.py` | Cargador de datos (viene en el paquete del alumno) |
| `docs/` | Bitácora E01–E15, diagrama de estados, capturas y reflexión |

## 3. Instalación

Requiere Python 3.11 o superior.

```bash
python -m venv .venv
# Windows PowerShell:  .venv\Scripts\Activate.ps1
# Windows CMD:         .venv\Scripts\activate.bat
# macOS / Linux:       source .venv/bin/activate
python -m pip install -r requirements.txt
```

## 4. Ejecución

| Qué | Comando |
|---|---|
| Cargar los 16 pedidos y ver su estado | `python cargar_csv.py` |
| Correr las pruebas | `python -m pytest -q` |
| Levantar la API | `uvicorn app.api:app --reload` |
| Documentación interactiva (Swagger) | http://127.0.0.1:8000/docs |
| Contrato OpenAPI | http://127.0.0.1:8000/openapi.json |

Ejecuta todos los comandos desde la raíz del proyecto (donde están `app/` y `cargar_csv.py`).

## 5. Reglas de negocio

| Regla | Detalle |
|---|---|
| Dinero | `Money` es inmutable, usa `Decimal` (no `float`) y no admite importes negativos |
| Límite de unidades | Máximo 20 unidades por pedido; es la **suma de cantidades**, no el número de renglones |
| Artículo válido | SKU no vacío y cantidad mayor que 0 |
| Descuento del 10 % | Cliente VIP, total > 500 MXN, al menos 4 unidades y sin promoción activa |
| Descuento del 5 % | Total > 5000 MXN y sin promoción activa |
| Prioridad | Si se cumplen ambos descuentos se aplica el 10 % |
| Confirmar | Solo desde DRAFT, con artículos y cliente activo |
| Enviar | Solo desde CONFIRMED y con número de guía no vacío |
| Cancelar | Solo desde CONFIRMED y con motivo no vacío |
| Entregar / devolver | Solo desde SHIPPED |
| Operación inválida | No cambia el estado y no registra ningún evento |
| Inventario | El campo `existencia` es solo información de catálogo; no se descuenta stock |

## 6. Máquina de estados y Domain Events

```
DRAFT --confirm--> CONFIRMED --ship--> SHIPPED --deliver--> DELIVERED
                       |                  |
                    cancel              return
                       |                  |
                   CANCELLED           RETURNED
```

| Operación | Evento publicado |
|---|---|
| `confirm()` | `OrderConfirmed` |
| `ship(tracking_number)` | `OrderShipped` |
| `cancel(reason)` | `OrderCancelled` |
| `deliver()` | `OrderDelivered` |
| `return_order()` | `OrderReturned` |

## 7. Endpoints

| Método | Ruta | Descripción | Respuestas |
|---|---|---|---|
| GET | `/orders` | Lista los pedidos | 200 |
| GET | `/orders/{id}` | Consulta un pedido | 200, 404 |
| POST | `/orders/{id}/confirm` | DRAFT → CONFIRMED | 200, 404, 409, 422 |
| POST | `/orders/{id}/ship` | CONFIRMED → SHIPPED. Cuerpo: `{"tracking_number": "..."}` | 200, 404, 409, 422 |
| POST | `/orders/{id}/cancel` | CONFIRMED → CANCELLED. Cuerpo: `{"reason": "..."}` | 200, 404, 409, 422 |
| POST | `/orders/{id}/deliver` | SHIPPED → DELIVERED | 200, 404, 409 |
| POST | `/orders/{id}/return` | SHIPPED → RETURNED | 200, 404, 409 |
| POST | `/fixtures/reload` | Restaura los 16 pedidos a DRAFT (uso didáctico) | 200 |

| Código | Cuándo |
|---|---|
| 404 | El pedido no existe |
| 409 | El estado actual no permite la operación (por ejemplo, confirmar dos veces o cancelar desde SHIPPED) |
| 422 | Datos o precondiciones inválidos (pedido vacío, cliente inactivo, guía o motivo vacío, más de 20 unidades) |

## 8. Evidencias

| Evidencia | Ubicación |
|---|---|
| Carga exitosa de los 16 pedidos | `docs/` |
| Bitácora de los escenarios E01–E15 | `docs/` |
| Resultados de pytest | `docs/` |
| Swagger: una operación exitosa y una rechazada | `docs/` |
| Diagrama de estados y explicación de los Domain Events | `docs/` |
| Reflexión del equipo | `docs/` |
