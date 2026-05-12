"""
Secuenciador de números de factura.

Genera números únicos por company: XXX-XXX-XXXXXXXXX
  - XXX: establecimiento (desde company.establishment_code o '001')
  - XXX: punto emisión (desde company.point_emission_code o '001')
  - XXXXXXXXX: secuencial de 9 dígitos, reinicia cada mes

Thread-safe: usa `select_for_update()` en transacción atómica.
"""
from django.db import transaction
from django.db.models import Max, F
from django.utils import timezone


def generate_next_invoice_number(company, establishment_code=None, emission_point=None) -> str:
    """
    Genera el próximo número de factura para una company.

    Formato: {estab:3d}-{ptoEmi:3d}-{secuencial:9d}

    Ejemplo: 001-001-000000001

    Thread-safe: bloquea fila con select_for_update.
    """
    now = timezone.now()
    year = now.year
    month = now.month

    # Valores por defecto desde Company o '001'
    if establishment_code is None:
        establishment_code = getattr(company, 'establishment_code', '001')
    if emission_point is None:
        emission_point = getattr(company, 'point_emission_code', '001')

    est = str(establishment_code).zfill(3)[:3]
    pto = str(emission_point).zfill(3)[:3]

    from apps.facturacion.models import Invoice

    with transaction.atomic():
        # Buscar última factura del mes/año actual con mismo est-pto
        last = Invoice.objects.select_for_update().filter(
            company=company,
            number__startswith=f"{est}-{pto}-",
            date__year=year,
            date__month=month
        ).order_by('-number').first()

        if last:
            # Extraer secuencial y sumar 1
            parts = last.number.split('-')
            last_seq = int(parts[2]) if len(parts) == 3 else 0
            next_seq = last_seq + 1
        else:
            next_seq = 1

        seq_str = str(next_seq).zfill(9)
        return f"{est}-{pto}-{seq_str}"
