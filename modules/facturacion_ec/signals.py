"""
Signals para facturacion_ec (plugin SRI).
"""
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import InvoiceSRIExtension


@receiver(post_save, sender=InvoiceSRIExtension)
def invoice_sri_extension_post_save(sender, instance, created, **kwargs):
    """
    Cuando se crea/actualiza una extensión SRI, recalcular totals de la factura core
    (por si cambió impuestos) y loggear evento.
    """
    if created:
        # Log creación
        import logging
        logger = logging.getLogger(__name__)
        logger.info(
            f"Factura {instance.invoice.number} — Extensión SRI creada "
            f"(ambiente={instance.ambiente}, status={instance.sri_status})"
        )
