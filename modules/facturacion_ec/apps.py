from django.apps import AppConfig


class FacturacionEcConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "modules.facturacion_ec"
    verbose_name = "Facturación Electrónica Ecuador (Plugin SRI)"
    label = "facturacion_ec"

    def ready(self):
        """Import signals. Nota: puede fallar si dependencies no están instaladas."""
        try:
            import modules.facturacion_ec.signals  # noqa
        except Exception:
            # Señales opcionales — plugin puede funcionar sin settings completos
            pass
