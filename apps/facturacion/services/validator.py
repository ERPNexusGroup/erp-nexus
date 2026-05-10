# Validaciones de negocio para facturación electrónica
from decimal import Decimal, ROUND_HALF_UP, InvalidOperation
from typing import Optional, List


class ValidationError(Exception):
    """Error de validación de factura"""
    def __init__(self, field: str, message: str):
        self.field = field
        self.message = message
        super().__init__(f"{field}: {message}")


class InvoiceValidator:
    """Validador de facturas antes de envío a SRI"""

    @staticmethod
    def validate_ruc(ruc: str) -> bool:
        """
        Valida RUC ecuatoriano (13 dígitos) con algoritmo módulo 10.
        """
        if len(ruc) != 13 or not ruc.isdigit():
            return False

        # Algoritmo módulo 10 para RUC Ecuador
        # Primeros 10 dígitos + algoritmo, últimos 3 tipo contribuyente
        digits = [int(d) for d in ruc[:10]]
        multipliers = [2, 1, 2, 1, 2, 1, 2, 1, 2, 1]
        total = 0

        for digit, mult in zip(digits, multipliers):
            prod = digit * mult
            if prod >= 10:
                prod = (prod // 10) + (prod % 10)
            total += prod

        remainder = total % 10
        check_digit = 0 if remainder == 0 else 10 - remainder

        return check_digit == int(ruc[10])

    @staticmethod
    def validate_cedula(cedula: str) -> bool:
        """Valida cédula ecuatoriana (10 dígitos)"""
        if len(cedula) != 10 or not cedula.isdigit():
            return False

        digits = [int(d) for d in cedula[:9]]
        multipliers = [2, 1, 2, 1, 2, 1, 2, 1, 2]
        total = 0

        for digit, mult in zip(digits, multipliers):
            prod = digit * mult
            if prod >= 10:
                prod = (prod // 10) + (prod % 10)
            total += prod

        remainder = total % 10
        check_digit = 0 if remainder == 0 else 10 - remainder

        return check_digit == int(cedula[9])

    @staticmethod
    def validate_invoice_lines(lines: List) -> None:
        """Valida líneas de factura"""
        if not lines:
            raise ValidationError("lines", "La factura debe tener al menos una línea")

        total_subtotal = Decimal('0.00')
        total_tax = Decimal('0.00')

        for i, line in enumerate(lines):
            if line.quantity <= 0:
                raise ValidationError(f"line[{i}].quantity", "Cantidad debe ser mayor a 0")
            if line.unit_price <= 0:
                raise ValidationError(f"line[{i}].unit_price", "Precio debe ser mayor a 0")
            if line.tax_rate < 0:
                raise ValidationError(f"line[{i}].tax_rate", "Impuesto no puede ser negativo")

            expected = (line.quantity * line.unit_price).quantize(Decimal('0.01'))
            if abs(line.subtotal - expected) > Decimal('0.01'):
                raise ValidationError(f"line[{i}].subtotal", f"Subtotal incorrecto: esperado {expected}, got {line.subtotal}")

            total_subtotal += line.subtotal
            total_tax += line.tax_amount

        return total_subtotal, total_tax

    @staticmethod
    def validate_number_format(number: str) -> bool:
        """Valida formato número factura: 001-001-000000001"""
        parts = number.split('-')
        if len(parts) != 3:
            return False
        estab, pto, seq = parts
        return len(estab) == 3 and estab.isdigit() and \
               len(pto) == 3 and pto.isdigit() and \
               len(seq) == 9 and seq.isdigit()

    @staticmethod
    def calculate_totals(lines: List) -> tuple[Decimal, Decimal, Decimal]:
        """
        Calcula y valida totales de factura.

        Returns:
            (subtotal, tax_total, total)
        """
        subtotal = Decimal('0.00')
        tax_total = Decimal('0.00')

        IVA_RATES = {12: Decimal('0.12'), 0: Decimal('0.00')}

        for line in lines:
            line_sub = (line.quantity * line.unit_price).quantize(Decimal('0.01'))
            line_tax_rate = IVA_RATES.get(int(line.tax_rate), Decimal('0.00'))
            line_tax = (line_sub * line_tax_rate).quantize(Decimal('0.01'))

            subtotal += line_sub
            tax_total += line_tax

        total = subtotal + tax_total
        return subtotal.quantize(Decimal('0.01')), tax_total.quantize(Decimal('0.01')), total.quantize(Decimal('0.01'))
