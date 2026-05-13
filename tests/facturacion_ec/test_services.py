# Tests básicos para services
import pytest
from decimal import Decimal
from modules.facturacion_ec.services.code_unique import (
    generate_access_key,
    generate_invoice_number,
    parse_invoice_number,
    get_next_sequential,
)
from modules.facturacion_ec.services.validator import InvoiceValidator, ValidationError
from datetime import datetime


class TestCodeUnique:

    def test_generate_access_key_format(self):
        """Genera clave de 49 dígitos"""
        key = generate_access_key(
            ruc="1791234567001",
            ambiente=1,
            establishment_code="001",
            emission_point="001",
            sequential="000000001",
            date=datetime(2024, 1, 15)
        )
        assert len(key) == 49
        assert key.isdigit()

    def test_generate_invoice_number(self):
        """Formato 001-001-000000001"""
        num = generate_invoice_number("001", "001", 1)
        assert num == "001-001-000000001"

    def test_parse_invoice_number(self):
        """Descompone número correctamente"""
        est, pto, seq = parse_invoice_number("001-001-000000001")
        assert est == "001"
        assert pto == "001"
        assert seq == "000000001"


class TestValidator:

    def test_validate_ruc_valid(self):
        """RUCS válidos pasan (algoritmo mód 10)."""
        # RUC: 1791234567 1 01  → dígito verificador=1, tipo=01 (2 dígitos) = 13 total
        assert InvoiceValidator.validate_ruc("1791234567101") is True
        # RUC: 1792369238 3 01  → dv=3, tipo=01
        assert InvoiceValidator.validate_ruc("1792369238301") is True

    def test_validate_ruc_invalid_length(self):
        """RUCS con longitud incorrecta"""
        assert InvoiceValidator.validate_ruc("179123456700") is False

    def test_calculate_totals(self):
        """Totales se calculan correctamente"""
        class MockLine:
            def __init__(self, qty, price, tax=12):
                self.quantity = qty
                self.unit_price = price
                self.tax_rate = tax

        lines = [MockLine(2, Decimal('10.00'))]
        subtotal, tax, total = InvoiceValidator.calculate_totals(lines)
        assert subtotal == Decimal('20.00')
        assert tax == Decimal('2.40')  # 12% de 20
        assert total == Decimal('22.40')
