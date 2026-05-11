"""
Mi Módulo — AppConfig Django.
"""

from django.apps import AppConfig


class MiModuloConfig(AppConfig):
    """Configuración de la app mi_modulo."""
    default_auto_field = "django.db.models.BigAutoField"
    name = "modules.mi_modulo"
    verbose_name = "Mi Módulo"

    def ready(self):
        """Registrar signals al cargar la app."""
        import modules.mi_modulo.signals  # noqa: F401
