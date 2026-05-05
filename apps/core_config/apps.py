from django.apps import AppConfig


class CoreConfigConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.core_config"
    verbose_name = "Core - Configuraciones"

    def ready(self):
        """
        Seed de claves de configuración.
        Se ejecuta una vez por migración (post_migrate signal).
        """
        from django.db.models.signals import post_migrate

        def seed_configs(sender, **kwargs):
            try:
                from .models import seed_default_config_keys
                seed_default_config_keys()
            except Exception:
                pass  # DB no lista, ignorar

        post_migrate.connect(seed_configs, sender=self)
