"""Pruebas de los totales. Uso: .venv/bin/python -m pytest tests/ -v"""

from decimal import Decimal

from totales import calcular_totales


def test_ejemplo_v1():
    # El ejemplo probado en la v1: 2 x $1,500 con 10% de descuento.
    t = calcular_totales([(2, 1500)], descuento_pct=10, iva_pct=16)
    assert t["subtotal"] == Decimal("3000.00")
    assert t["descuento"] == Decimal("300.00")
    assert t["base"] == Decimal("2700.00")
    assert t["iva"] == Decimal("432.00")
    assert t["total"] == Decimal("3132.00")


def test_sin_descuento():
    t = calcular_totales([(1, 1000), (3, 250)])
    assert t["subtotal"] == Decimal("1750.00")
    assert t["descuento"] == Decimal("0.00")
    assert t["iva"] == Decimal("280.00")
    assert t["total"] == Decimal("2030.00")


def test_vacio():
    t = calcular_totales([])
    assert t["total"] == Decimal("0.00")
