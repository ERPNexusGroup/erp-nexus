from django.apps import AppConfig


class CoreStatsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.core_stats"
    verbose_name = "Installation & Usage Stats"
