"""Signals for automatic commission generation."""
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db import transaction

from .models import CommissionRecord
from .services import CommissionCalculator


@receiver(post_save, sender='sales.Order')
def create_commission_record_on_order_complete(sender, instance, created, **kwargs):
    """
    Signal: Cuando una Order cambia su estado a 'completed',
    crea automáticamente un CommissionRecord.

    No dispara en.created (orden nueva) — solo en transición a completada.
    """
    order = instance

    # Solo procesar si el status es 'completed'
    if order.status != 'completed':
        return

    # Evitar duplicados: verificar si ya existe un CommissionRecord para esta orden
    if CommissionRecord.objects.filter(order=order).exists():
        return

    # Calcular y crear registro
    record = CommissionCalculator.calculate_for_order(order)
    if record:
        # Usar transaction.on_commit para evitar race conditions en post_save
        transaction.on_commit(lambda: record.save())


@receiver(post_save, sender='purchases.PurchaseOrder')
def create_commission_record_on_po_received(sender, instance, created, **kwargs):
    """
    Signal: Cuando una PurchaseOrder cambia su estado a 'received',
    crea automáticamente un CommissionRecord.

    No dispara en.created (PO nueva) — solo en transición a recibida.
    """
    po = instance

    # Solo procesar si el status es 'received'
    if po.status != 'received':
        return

    # Evitar duplicados: verificar si ya existe un CommissionRecord para esta PO
    if CommissionRecord.objects.filter(purchase_order=po).exists():
        return

    # Calcular y crear registro
    record = CommissionCalculator.calculate_for_purchase_order(po)
    if record:
        transaction.on_commit(lambda: record.save())
