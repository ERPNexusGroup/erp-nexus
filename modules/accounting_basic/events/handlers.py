"""
Handlers de eventos para accounting_basic.

Este módulo emite:
  - accounting.entry_posted  → cuando se contabiliza un asiento
  - accounting.balance_generated → cuando se genera un balance

Puede suscribirse a eventos de otros módulos (ej: invoicing).
"""
import logging

logger = logging.getLogger(__name__)


def on_invoice_created(payload: dict):
    """
    Handler para evento 'invoice.created' del módulo de facturación.
    Genera automáticamente el asiento contable de la factura.
    """
    logger.info(f"Factura recibida para contabilizar: {payload}")

    # En una implementación real, aquí se crearía el asiento contable
    # automáticamente cuando se crea una factura.

    # Ejemplo:
    # from accounting_basic.core.models import JournalEntry, JournalLine
    # entry = JournalEntry.objects.create(
    #     reference=f"INV-{payload['invoice_id']}",
    #     description=f"Factura #{payload['invoice_id']}",
    # )
    # JournalLine.objects.create(
    #     journal_entry=entry,
    #     account_id=cuenta_clientes_id,
    #     entry_type="debit",
    #     amount=payload["total"],
    # )
    # JournalLine.objects.create(
    #     journal_entry=entry,
    #     account_id=cuenta_ventas_id,
    #     entry_type="credit",
    #     amount=payload["total"],
    # )
    # entry.post()


def on_payment_received(payload: dict):
    """Handler para evento 'payment.received'."""
    logger.info(f"Pago recibido para contabilizar: {payload}")
