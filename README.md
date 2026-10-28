# TechStore — Unidad 4: núcleo de negocio

Proyecto educativo en Python 3.11+ para demostrar entidades y Value Objects, Specification Pattern, máquina de estados, Domain Events, API REST y pruebas automáticas.

## Contenido
- `app/domain.py`: Money, Customer, OrderItem, Order, estados, eventos y reglas.
- `app/specifications.py`: especificaciones componibles con AND (`&`), OR (`|`) y NOT (`~`).
- `app/api.py`: API FastAPI y documentación OpenAPI/Swagger.
- `cargar_csv.py`: carga de datos desde CSV.
- `datos/`: archivos CSV de ejemplo compatibles con la guía. Si el profesor entregó los CSV originales, conserva los originales y reemplaza estos archivos por aquellos.
- `tests/`: pruebas unitarias y de API.
- `docs/`: bitácora de escenarios, diagrama de estados y guía de evidencias.

## Instalar en Windows
```powershell
python --version
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```
Si PowerShell bloquea la activación, abre CMD y usa `.venv\Scripts\activate.bat`, o instala con el ejecutable de Python disponible.

## Ejecutar la carga CSV
Desde la carpeta raíz:
```bash
python cargar_csv.py
```
Debe listar 16 pedidos en estado `DRAFT`. En los datos incluidos, `O001` debe mostrar 4 unidades y un total de `2100.00 MXN`, y `O010` un total de `500.00 MXN`.

## Ejecutar las pruebas
```bash
python -m pytest -q
```

## Ejecutar API y abrir Swagger
```bash
uvicorn app.api:app --reload
```
Abre `http://127.0.0.1:8000/docs`. También está disponible `http://127.0.0.1:8000/openapi.json`.

Endpoints principales:
- `GET /orders`
- `GET /orders/{order_id}`
- `POST /orders`
- `POST /orders/{order_id}/items`
- `POST /orders/{order_id}/confirm`
- `POST /orders/{order_id}/ship`
- `POST /orders/{order_id}/cancel`
- `POST /orders/{order_id}/deliver`
- `POST /orders/{order_id}/return`

Respuestas previstas:
- `404`: pedido inexistente.
- `409`: transición inválida o identificador duplicado.
- `422`: datos inválidos o regla del dominio incumplida.

## Reglas de negocio implementadas
1. `Money` es inmutable, usa `Decimal` y no admite cantidades negativas ni monedas distintas de MXN.
2. Cada artículo necesita SKU y cantidad entera positiva.
3. El máximo es 20 unidades sumadas en todo el pedido; no se cuentan renglones.
4. Solo pedidos `DRAFT` aceptan artículos.
5. Solo se confirma un pedido con artículos y cliente activo.
6. Enviar requiere estado `CONFIRMED` y guía no vacía.
7. Cancelar requiere estado `CONFIRMED` y motivo no vacío.
8. Entregar y devolver requieren estado `SHIPPED`.
9. Los eventos se registran únicamente después de una transición válida.
10. Descuento del 10 %: total estrictamente mayor a 500 MXN, cliente VIP, al menos 4 unidades y sin promoción activa.
11. Descuento del 5 %: total estrictamente mayor a 5000 MXN y sin promoción activa. Si aplican ambos, tiene prioridad el 10 %.

## Evidencias pendientes de generar localmente
La carpeta `docs` contiene una bitácora inicial y el diagrama de estados. Para la entrega, ejecuta el proyecto en tu computadora y agrega capturas reales de:
- `python cargar_csv.py` con los 16 pedidos.
- `python -m pytest -q` sin fallos.
- Swagger `/docs` con una petición exitosa y otra rechazada.
No se incluyen capturas simuladas ni se afirma que se hayan ejecutado en el equipo del estudiante.
