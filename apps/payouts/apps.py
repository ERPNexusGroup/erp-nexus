from django.apps import AppConfig


class PayoutsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.payouts'
    verbose_name = 'Payouts & Comisiones'

    def ready(self):
        """Import signals to register them."""
        import apps.payouts.signals  # noqa
