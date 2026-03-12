from django.db import models
from django.utils import timezone


class ModuleCatalogItem(models.Model):
    technical_name = models.CharField(max_length=100, unique=True)
    version = models.CharField(max_length=50)
    source = models.CharField(max_length=500, blank=True, null=True)
    installed_path = models.CharField(max_length=500, blank=True, null=True)
    installed_at = models.DateTimeField(blank=True, null=True)
    status = models.CharField(max_length=20, default="active")
    is_active = models.BooleanField(default=True)
    django_app = models.CharField(max_length=200, blank=True, null=True)
    admin_menu = models.JSONField(blank=True, null=True)

    def __str__(self) -> str:
        return f"{self.technical_name} ({self.version})"

    def mark_inactive(self) -> None:
        self.status = "inactive"
        self.is_active = False
        self.save(update_fields=["status", "is_active"])

    def touch_installed(self) -> None:
        self.installed_at = timezone.now()
        self.status = "active"
        self.is_active = True
        self.save(update_fields=["installed_at", "status", "is_active"])


class EnabledModule(models.Model):
    technical_name = models.CharField(max_length=100, unique=True)
    django_app = models.CharField(max_length=200)
    status = models.CharField(max_length=20, default="active")
    enabled_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return f"{self.technical_name} ({self.status})"
