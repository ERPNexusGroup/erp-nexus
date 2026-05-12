"""
Celery Tasks — ERP Nexus
========================
Tareas asíncronas comunes: notificaciones, emails, reportes, SRI.
Cada app puede definir sus propias tareas en `tasks.py`.
"""

from celery import shared_task
from django.core.mail import send_mail, EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings


# ─── Notifications ────────────────────────────────────────────────────────────
@shared_task(queue='notifications', bind=True, max_retries=3, default_retry_delay=60)
def send_email_task(self, subject: str, message: str, recipient_list: list, html_message: str = None):
    """
    Envía email de forma asíncrona.
    Retry automático en fallos (max 3 intentos, 60s entre ellos).
    """
    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=recipient_list,
            html_message=html_message,
            fail_silently=False,
        )
        return {"status": "sent", "recipients": recipient_list}
    except Exception as exc:
        raise self.retry(exc=exc, countdown=60)


@shared_task(queue='notifications', bind=True, max_retries=3)
def send_templated_email_task(self, template_name: str, context: dict, recipient_list: list):
    """
    Envía email usando template HTML + texto plano.
    Context debe ser serializable (dict).

    Templates:
      - emails/invoice_sent.html
      - emails/welcome.html
    """
    try:
        subject = render_to_string(f"emails/{template_name}_subject.txt", context).strip()
        text_body = render_to_string(f"emails/{template_name}.txt", context)
        html_body = render_to_string(f"emails/{template_name}.html", context)

        msg = EmailMultiAlternatives(
            subject=subject,
            body=text_body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=recipient_list,
        )
        msg.attach_alternative(html_body, "text/html")
        msg.send()
        return {"status": "sent", "template": template_name}
    except Exception as exc:
        raise self.retry(exc=exc, countdown=60)


# ─── SRI (Facturación Electrónica Ecuador) ───────────────────────────────────
@shared_task(queue='sri', bind=True, max_retries=3, default_retry_delay=120)
def send_invoice_to_sri_task(self, invoice_id: int):
    """
    Tarea asíncrona para enviar factura al SRI (Ecuador).
    Se ejecuta en cola de alta prioridad (sri).
    """
    from apps.facturacion.models import Invoice

    try:
        invoice = Invoice.objects.get(id=invoice_id)
        # Lógica de envío a SRI (XML, firma digital, POST a endpoint SRI)
        # Esta es una place-holder — implementar en facturacion/services/sri.py
        # sri_client.send_invoice(invoice)

        # Simulación:
        invoice.sri_status = 'sent'
        invoice.sri_authorization_code = f"AUTH-{invoice_id}-{invoice.created_at.timestamp():.0f}"
        invoice.save()

        # Encolar notificacion de confirmacion
        send_email_task.delay(
            subject=f"Factura {invoice.number} enviada al SRI",
            message=f"Su factura {invoice.number} ha sido enviada exitosamente.",
            recipient_list=[invoice.partner_email],
        )

        return {"status": "sri_sent", "invoice_id": invoice_id}
    except Invoice.DoesNotExist:
        # No retry si no existe
        return {"status": "error", "error": "invoice_not_found"}
    except Exception as exc:
        raise self.retry(exc=exc, countdown=120)


# ─── Reports (PDF/Excel) ────────────────────────────────────────────────────
@shared_task(queue='reports', bind=True, max_retries=2, default_retry_delay=300)
def generate_invoice_pdf_task(self, invoice_id: int):
    """
    Genera PDF de factura en background (tarea pesada).
    Guarda en media/invoices/pdf/ y notifica por email.
    """
    from apps.facturacion.models import Invoice
    from io import BytesIO
    # Placeholder: usar weasyprint o reportlab
    # pdf = generate_pdf(invoice)
    # save to file

    try:
        invoice = Invoice.objects.get(id=invoice_id)
        # Simulación de generación
        import time
        time.sleep(5)  # Simulate heavy work

        return {"status": "pdf_generated", "invoice_id": invoice_id}
    except Invoice.DoesNotExist:
        return {"status": "error", "error": "invoice_not_found"}
    except Exception as exc:
        raise self.retry(exc=exc, countdown=300)


# ─── Webhooks ────────────────────────────────────────────────────────────────
@shared_task(queue='webhooks', bind=True, max_retries=3)
def send_webhook_task(self, url: str, payload: dict, headers: dict = None):
    """
    Envía webhook HTTP POST a URL externa.
    Retry automático en fallos de red.
    """
    import requests
    from requests.exceptions import RequestException

    try:
        resp = requests.post(url, json=payload, headers=headers or {}, timeout=10)
        resp.raise_for_status()
        return {"status": "delivered", "url": url, "code": resp.status_code}
    except RequestException as exc:
        raise self.retry(exc=exc, countdown=60)


# ─── Periodic Tasks (ejemplos) ───────────────────────────────────────────────
# Se ejecutan via celery beat (crontab/interval)
@shared_task(queue='default')
def cleanup_old_sessions():
    """Limpia sesiones expiradas (diario)."""
    from django.contrib.sessions.models import Session
    Session.objects.filter(expire_date__lt=timezone.now()).delete()
    return {"status": "sessions_cleaned"}


@shared_task(queue='default')
def refresh_marketplace_cache():
    """Refresca cache del marketplace (cada hora)."""
    from apps.core_marketplace.utils.cache import invalidate_catalog_cache
    invalidate_catalog_cache()
    return {"status": "cache_invalidated"}
