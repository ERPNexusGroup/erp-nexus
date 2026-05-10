"""
Models for notifications module.
"""
from django.db import models
from django.contrib.auth import get_user_model


User = get_user_model()


class Notification(models.Model):
    """Notificación entregada a un usuario."""
    NOTIFICATION_TYPES = [
        ("email", "Email"),
        ("telegram", "Telegram"),
        ("inbox", "Bandeja de entrada"),
        ("push", "Push (futuro)"),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="notifications")
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES)
    title = models.CharField(max_length=200)
    message = models.TextField()
    data = models.JSONField(default=dict, blank=True)  # metadata
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    delivered_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "Notificación"
        verbose_name_plural = "Notificaciones"
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["user", "is_read", "created_at"], name="notification_user_created_idx")]

    def __str__(self):
        return f"{self.notification_type}: {self.title} → {self.user}"


class NotificationTemplate(models.Model):
    """Plantilla de notificación (subject + body)."""
    name = models.CharField(max_length=100, unique=True)
    notification_type = models.CharField(max_length=20, choices=Notification.NOTIFICATION_TYPES)
    subject = models.CharField(max_length=200)
    body_template = models.TextField(help_text="Template con {{variables}} jinja2-style")
    variables = models.JSONField(default=list, blank=True, help_text="Lista de variables esperadas")

    class Meta:
        verbose_name = "Plantilla de Notificación"
        verbose_name_plural = "Plantillas de Notificación"

    def __str__(self):
        return f"{self.name} ({self.notification_type})"


class NotificationQueue(models.Model):
    """Cola de notificaciones pendientes (procesadas por worker)."""
    STATUS_CHOICES = [
        ("pending", "Pendiente"),
        ("processing", "Procesando"),
        ("sent", "Enviada"),
        ("failed", "Fallida"),
    ]

    notification_type = models.CharField(max_length=20, choices=Notification.NOTIFICATION_TYPES)
    recipient = models.CharField(max_length=200)  # email o chat_id
    title = models.CharField(max_length=200)
    message = models.TextField()
    template = models.ForeignKey(
        NotificationTemplate,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    context = models.JSONField(default=dict, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    attempts = models.IntegerField(default=0)
    last_error = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "Cola de Notificación"
        verbose_name_plural = "Cola de Notificaciones"
        ordering = ["created_at"]
        indexes = [models.Index(fields=["status", "created_at"], name="notif_q_stats_created_idx")]

    def __str__(self):
        return f"{self.notification_type} → {self.recipient} [{self.status}]"
