"""Cálculo de totales de una cotización.

Reglas (iguales que en la v1 web):
- subtotal = suma(cantidad * precio_unitario)
- descuento = subtotal * descuento_pct / 100
- base = subtotal - descuento
- iva = base * iva_pct / 100   (por defecto 16%)
- total = base + iva

Se usa Decimal para que los centavos no se desvíen por errores de float.
"""

from decimal import Decimal, ROUND_HALF_UP

CENT = Decimal("0.01")


def _d(value) -> Decimal:
    return Decimal(str(value))


def _money(value: Decimal) -> Decimal:
    return value.quantize(CENT, rounding=ROUND_HALF_UP)


def calcular_totales(items, descuento_pct=0, iva_pct=16):
    """items: iterable de (cantidad, precio_unitario).

    Devuelve un dict con subtotal, descuento, base, iva y total (Decimal).
    """
    subtotal = sum((_d(cant) * _d(precio) for cant, precio in items), Decimal("0"))
    subtotal = _money(subtotal)
    descuento = _money(subtotal * _d(descuento_pct) / Decimal("100"))
    base = _money(subtotal - descuento)
    iva = _money(base * _d(iva_pct) / Decimal("100"))
    total = _money(base + iva)
    return {
        "subtotal": subtotal,
        "descuento": descuento,
        "base": base,
        "iva": iva,
        "total": total,
    }


def formato_mxn(valor) -> str:
    """$3,132.00"""
    return f"${_d(valor):,.2f}"
