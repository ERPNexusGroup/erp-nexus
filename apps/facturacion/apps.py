from django.apps import AppConfig


class FacturacionEcConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.facturacion"
    verbose_name = "Facturación Electrónica Ecuador"

    def ready(self):
        """Import signals to register"""
        import apps.facturacion.signals  # noqa
