from django.apps import AppConfig


class CoreAuditConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.core_audit"
    verbose_name = "Audit Log"
