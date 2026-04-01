"""
InstallationStats — Métricas de instalación y uso del ERP.
"""
import uuid
from django.db import models
from django.utils import timezone


class Installation(models.Model):
    """
    Registro de instalación del ERP (una por instancia).
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    instance_id = models.CharField(max_length=100, unique=True, help_text="ID único de la instancia")
    version = models.CharField(max_length=50)
    environment = models.CharField(max_length=20, default="production")
    domain = models.CharField(max_length=200, blank=True, default="")

    # Stats
    total_users = models.IntegerField(default=0)
    total_companies = models.IntegerField(default=0)
    total_modules_installed = models.IntegerField(default=0)
    total_modules_active = models.IntegerField(default=0)

    # Timestamps
    installed_at = models.DateTimeField(auto_now_add=True)
    last_seen = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Installation"
        verbose_name_plural = "Installations"

    def __str__(self):
        return f"{self.instance_id} v{self.version}"

    def touch(self):
        """Actualiza last_seen."""
        self.last_seen = timezone.now()
        self.save(update_fields=["last_seen"])


class UsageMetric(models.Model):
    """
    Métrica de uso (contadores diarios).
    """
    METRIC_TYPES = [
        ("api_requests", "API Requests"),
        ("logins", "Logins"),
        ("module_installs", "Module Installs"),
        ("module_activations", "Module Activations"),
        ("errors", "Errors"),
    ]

    date = models.DateField(db_index=True)
    metric_type = models.CharField(max_length=50, choices=METRIC_TYPES, db_index=True)
    value = models.IntegerField(default=0)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        unique_together = ["date", "metric_type"]
        ordering = ["-date"]
        verbose_name = "Usage Metric"
        verbose_name_plural = "Usage Metrics"

    def __str__(self):
        return f"{self.date}: {self.metric_type} = {self.value}"

    @classmethod
    def increment(cls, metric_type: str, amount: int = 1, metadata: dict = None):
        """Incrementa una métrica para hoy."""
        today = timezone.now().date()
        obj, created = cls.objects.get_or_create(
            date=today,
            metric_type=metric_type,
            defaults={"value": amount, "metadata": metadata or {}},
        )
        if not created:
            obj.value += amount
            obj.save(update_fields=["value"])

    @classmethod
    def get_daily_stats(cls, days: int = 30) -> dict:
        """Obtiene estadísticas de los últimos N días."""
        from datetime import timedelta
        start_date = timezone.now().date() - timedelta(days=days)

        metrics = cls.objects.filter(date__gte=start_date)
        result = {}
        for m in metrics:
            if m.metric_type not in result:
                result[m.metric_type] = []
            result[m.metric_type].append({
                "date": str(m.date),
                "value": m.value,
            })

        return result


class SystemHealth(models.Model):
    """
    Snapshot de salud del sistema.
    """
    timestamp = models.DateTimeField(auto_now_add=True)
    db_status = models.CharField(max_length=20, default="ok")
    cache_status = models.CharField(max_length=20, default="ok")
    disk_usage_percent = models.FloatField(default=0)
    memory_usage_percent = models.FloatField(default=0)
    active_users_count = models.IntegerField(default=0)
    pending_events = models.IntegerField(default=0)

    class Meta:
        ordering = ["-timestamp"]
        verbose_name = "System Health"
        verbose_name_plural = "System Health"

    def __str__(self):
        return f"{self.timestamp}: DB={self.db_status}, Cache={self.cache_status}"
