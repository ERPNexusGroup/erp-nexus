"""
EventLog — Registro persistente de eventos entre módulos.

Los módulos emiten eventos via EventBus.emit() y otros módulos
se suscriben via EventBus.subscribe(). El procesamiento puede
ser síncrono (dev) o async via Celery (production).
"""
import uuid
from django.db import models
from django.utils import timezone


class EventLog(models.Model):
    """
    Log de eventos del sistema. Cada evento es inmutable una vez creado.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Identificación del evento
    event_type = models.CharField(
        max_length=200,
        db_index=True,
        help_text="Tipo de evento: 'invoice.created', 'payment.received', etc.",
    )
    source_module = models.CharField(
        max_length=100,
        help_text="Módulo que emitió el evento",
    )

    # Datos del evento
    payload = models.JSONField(
        default=dict,
        help_text="Datos del evento (serializado JSON)",
    )

    # Estado de procesamiento
    processed = models.BooleanField(
        default=False,
        db_index=True,
    )
    processed_at = models.DateTimeField(
        null=True,
        blank=True,
    )
    error_message = models.TextField(
        blank=True,
        default="",
    )

    # Metadata
    created_at = models.DateTimeField(
        default=timezone.now,
        db_index=True,
    )

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["event_type", "created_at"]),
            models.Index(fields=["source_module", "created_at"]),
        ]
        verbose_name = "Event Log"
        verbose_name_plural = "Event Logs"

    def __str__(self):
        status = "✓" if self.processed else "⏳"
        return f"{status} {self.event_type} from {self.source_module}"

    def mark_processed(self):
        self.processed = True
        self.processed_at = timezone.now()
        self.save(update_fields=["processed", "processed_at"])

    def mark_failed(self, error: str):
        self.error_message = error
        self.save(update_fields=["error_message"])


class EventSubscription(models.Model):
    """
    Registro de suscripciones de módulos a tipos de eventos.
    """
    event_type = models.CharField(max_length=200, db_index=True)
    subscriber_module = models.CharField(
        max_length=100,
        help_text="Módulo suscrito al evento",
    )
    handler_path = models.CharField(
        max_length=500,
        help_text="Ruta al handler: 'module.events.handle_event'",
    )
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ["event_type", "subscriber_module"]
        verbose_name = "Event Subscription"
        verbose_name_plural = "Event Subscriptions"

    def __str__(self):
        return f"{self.subscriber_module} → {self.event_type}"
