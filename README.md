# Sistema de Cotizaciones para Negocios — versión en Python (Flask)

Aplicación web para que talleres, carpinterías, herrerías y servicios
técnicos creen cotizaciones en minutos, con folio, vigencia, cálculo
automático de subtotal, descuento e IVA del 16%, PDF listo para WhatsApp,
catálogo reutilizable, clientes e historial con estados (pendiente,
aceptada, rechazada, vencida) y panel de montos pendientes y aceptados.

Proyecto de Diego Rodriguez Zamora (GitHub: egooxX), estudiante de
Ingeniería en Sistemas Computacionales en el ITES Zamora. Es la versión en
Python de la primera versión (React/TypeScript) del mismo sistema.

## Cómo correrlo

```bash
python -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python seed.py   # opcional: datos de ejemplo
.venv/bin/python app.py    # abre http://127.0.0.1:5000
```

## Qué incluye

- `app.py` — app Flask: panel, cotizaciones, catálogo, clientes, perfil del
  negocio y PDF con fpdf2. Base de datos SQLite (`instance/cotizaciones.db`).
- `totales.py` — cálculo de subtotal, descuento, IVA y total con `Decimal`
  (sin errores de centavos por float).
- `schema.sql` — tablas: negocio, catálogo, clientes, cotizaciones y
  partidas. Misma estructura que la v1 web.
- `seed.py` — datos de ejemplo (taller mecánico + cotización COT-2026-001).
- `tests/test_totales.py` — pruebas de los totales (`pytest tests/ -v`).

## Ejemplo verificado

2 unidades de $1,500 con 10% de descuento e IVA 16%:

| Concepto | Monto |
|---|---|
| Subtotal | $3,000.00 |
| Descuento (10%) | −$300.00 |
| IVA (16%) | $432.00 |
| **Total** | **$3,132.00** |

## Subirlo a GitHub

```bash
git init
git add .
git commit -m "Sistema de cotizaciones para negocios (Flask + SQLite)"
gh repo create sistema-de-cotizaciones-para-negocios --public --source=. --push
```

Descripción sugerida del repo: "Sistema web para crear cotizaciones en
minutos: catálogo, IVA 16%, PDF y WhatsApp, para negocios locales."

## Próximos pasos

- Login por negocio y suscripción mensual ($149 MXN/mes).
- Envío del PDF por WhatsApp Business API.
- Migrar a Flask-SQLAlchemy / FastAPI si el proyecto crece.
