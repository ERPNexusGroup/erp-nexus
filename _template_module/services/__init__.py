"""Servicios de lógica de negocio — independientes de Django ORM."""
from decimal import Decimal
from typing import Optional


def calculate_total(amount: Decimal, tax_rate: Decimal = Decimal("0.12")) -> Decimal:
    """Calcula total con impuestos.

    Args:
        amount: Monto base
        tax_rate: Tasa de impuesto (default 12%)

    Returns:
        Total (amount + tax)
    """
    tax = amount * tax_rate
    return amount.quantize(Decimal("0.01")) + tax.quantize(Decimal("0.01"))


def validate_example_name(name: str) -> bool:
    """Valida que el nombre cumpla reglas de negocio."""
    if len(name) < 3:
        return False
    if len(name) > 200:
        return False
    # Más reglas...
    return True
