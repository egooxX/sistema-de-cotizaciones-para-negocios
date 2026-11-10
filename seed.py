"""Carga datos de ejemplo para probar y demostrar el sistema.

Uso:  .venv/bin/python seed.py
Deja un negocio de ejemplo (taller), 4 productos del catálogo y una
cotización de ejemplo con los números que ya probamos en la v1:
2 unidades de $1,500 con 10% de descuento -> total $3,132.00.
"""

import sqlite3
import time

from app import app, init_db

CATALOGO = [
    ("Cambio de aceite y filtro", "Aceite 5W-30 + filtro", 850, "servicio", "Taller"),
    ("Afinación mayor", "Bujías, filtros y revisión general", 1500, "servicio", "Taller"),
    ("Balatas delanteras", "Juego de balatas + mano de obra", 1200, "pieza", "Taller"),
    ("Revisión de frenos", "Diagnóstico y ajuste", 350, "servicio", "Taller"),
]

with app.app_context():
    init_db()
    db = sqlite3.connect(app.config["DATABASE"])
    db.row_factory = sqlite3.Row
    ahora = int(time.time() * 1000)
    db.execute(
        "UPDATE business_profile SET name=?, tagline=?, owner=?, phone=?,"
        " email=?, address=? WHERE id = 1",
        ("Taller Mecánico Ejemplo", "Servicio y confianza",
         "Diego Rodriguez Zamora", "+52 33 35 5865 21",
         "diego.rzof0@gmail.com", "Tangancícuaro, Michoacán"),
    )
    for nombre, desc, precio, unidad, cat in CATALOGO:
        db.execute(
            "INSERT OR IGNORE INTO catalog_items"
            " (name, description, price, unit, category, created_at)"
            " VALUES (?, ?, ?, ?, ?, ?)",
            (nombre, desc, precio, unidad, cat, ahora),
        )
    db.execute(
        "INSERT OR IGNORE INTO clients (id, name, company, phone, email, created_at)"
        " VALUES (1, 'Cliente Ejemplo', '', '+52 33 0000 0000', '', ?)",
        (ahora,),
    )
    db.execute(
        "INSERT OR IGNORE INTO quotes (id, folio, title, client_id, client_name,"
        " status, valid_until, discount_percent, tax_percent, notes,"
        " created_at, updated_at) VALUES"
        " (1, 'COT-2026-001', 'Cotización de servicios', 1, 'Cliente Ejemplo',"
        " 'pendiente', '2026-11-21', 10, 16, '', ?, ?)",
        (ahora, ahora),
    )
    db.execute(
        "INSERT OR IGNORE INTO quote_items (id, quote_id, description, quantity,"
        " unit_price, unit, sort_order) VALUES"
        " (1, 1, 'Afinación mayor', 2, 1500, 'servicio', 0)"
    )
    db.commit()
    print("Datos de ejemplo cargados. Abre http://127.0.0.1:5000")
