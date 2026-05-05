from django.apps import AppConfig


class FacturacionEcConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "modules.facturacion_ec"
    verbose_name = "Facturación Electrónica Ecuador"

    def ready(self):
        """Import signals to register"""
        import modules.facturacion_ec.signals  # noqa
