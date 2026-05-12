"""
Secuenciador de números de cotización.

Formato: COT-YYYY-NNNNNN (ej: COT-2026-000001)
Reinicia cada año.
"""
from django.db import transaction
from django.utils import timezone


def generate_next_quote_number(company) -> str:
    """
    Genera próximo número de cotización.

    Formato: COT-{year}-{seq:6d}
    """
    now = timezone.now()
    year = now.year

    from apps.facturacion.models import Quote

    with transaction.atomic():
        last = Quote.objects.select_for_update().filter(
            company=company,
            quote_number__startswith=f"COT-{year}-"
        ).order_by('-quote_number').first()

        if last:
            # Extraer secuencial: COT-2026-000001 → 1
            parts = last.quote_number.split('-')
            last_seq = int(parts[2]) if len(parts) == 3 else 0
            next_seq = last_seq + 1
        else:
            next_seq = 1

        return f"COT-{year}-{str(next_seq).zfill(6)}"
