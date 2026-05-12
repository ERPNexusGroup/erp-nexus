"""
Signals para facturación core.

Auto-numbering de Invoice y cálculo de totals automático.
"""
from django.db.models.signals import pre_save, post_save, post_delete
from django.dispatch import receiver

from .models import Invoice, InvoiceLine


# =========== INVOICE ===========

@receiver(pre_save, sender=Invoice)
def invoice_pre_save(sender, instance, **kwargs):
    """
    Asigna número único a Invoice si es nuevo (status=draft).
    Formato: XXX-XXX-XXXXXXXXX
    """
    if instance._state.adding and not instance.number:
        from .services.invoice_sequencer import generate_next_invoice_number
        instance.number = generate_next_invoice_number(instance.company)


@receiver(post_save, sender=Invoice)
def invoice_post_save(sender, instance, created, **kwargs):
    """
    Actualiza totals sumando líneas.
    """
    lines = instance.facturacion_lines.all()
    subtotal = sum(l.subtotal for l in lines)
    tax_total = sum(l.tax_amount for l in lines)
    total = subtotal + tax_total

    Invoice.objects.filter(pk=instance.pk).update(
        subtotal=subtotal,
        tax_total=tax_total,
        total=total
    )


@receiver(post_delete, sender=InvoiceLine)
def invoice_line_post_delete(sender, instance, **kwargs):
    """
    Al eliminar una línea, recalcular totals de la factura.
    """
    invoice = instance.invoice
    lines = invoice.facturacion_lines.all()
    subtotal = sum(l.subtotal for l in lines)
    tax_total = sum(l.tax_amount for l in lines)
    total = subtotal + tax_total

    Invoice.objects.filter(pk=invoice.pk).update(
        subtotal=subtotal,
        tax_total=tax_total,
        total=total
    )
