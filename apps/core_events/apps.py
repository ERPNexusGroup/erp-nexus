from django.apps import AppConfig


class CoreEventsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.core_events"
    verbose_name = "Event Bus"

    def ready(self):
        """Registrar signals al iniciar."""
        import apps.core_events.signals  # noqa: F401
