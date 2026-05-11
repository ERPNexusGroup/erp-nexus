# Señales del módulo facturacion
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings
from .models import Invoice
from .services import send_invoice_to_sri
import threading


@receiver(post_save, sender=Invoice)
def invoice_created_handler(sender, instance, created, **kwargs):
    """
    Al crear factura, disparar envío a SRI en background (no bloquear response).

    Para producción con Celery/ARQ:
        send_invoice_task.delay(instance.id)

    Para desarrollo sin Celery:
        threading.Thread(target=send_invoice_to_sri, args=(instance.id,)).start()
    """
    if created and instance.sri_status == 'pending':
        # Solo si configuración permite auto-envío
        if settings.DEBUG or getattr(settings, 'FACTURACION_EC_AUTO_SEND', True):
            thread = threading.Thread(
                target=send_invoice_to_sri,
                args=(instance.id,),
                daemon=True
            )
            thread.start()
