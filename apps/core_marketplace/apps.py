import hashlib
import time
from pathlib import Path

from django.apps import AppConfig
from django.conf import settings


class CoreMarketplaceConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.core_marketplace"
    verbose_name = "Core Marketplace"

    def ready(self) -> None:
        """Inicializar Métabase + crear ModuleRegistry default."""
        # 1. Crear ModuleRegistry default si no existe
        try:
            from apps.core_marketplace.models import ModuleRegistry
            if not ModuleRegistry.objects.filter(is_default=True).exists():
                ModuleRegistry.objects.get_or_create(
                    name="GitHub Official",
                    defaults={
                        "source_type": "github",
                        "url": getattr(settings, "GITHUB_ORG", "ERPNexusGroup"),
                        "description": "Official GitHub organization modules",
                        "is_active": True,
                        "is_default": True,
                        "priority": 100,
                    },
                )
        except Exception:
            # Base de datos no lista aún (migraciones pendientes)
            pass

        # 2. Watch modules_enabled.py para desarrollo
        # En producción: este chequeo se hace en el script de inicio (systemd/docker)
        try:
            from django.utils import autoreload

            modules_path = Path(settings.BASE_DIR) / "erp_nexus" / "modules_enabled.py"

            if modules_path.exists():
                last_hash = None

                def check_modules_file() -> bool:
                    nonlocal last_hash
                    try:
                        current_hash = hashlib.sha256(modules_path.read_bytes()).hexdigest()
                        if last_hash is None:
                            last_hash = current_hash
                            return False
                        if current_hash != last_hash:
                            print(f"\n🔄  modules_enabled.py changed. Restart Django to load new modules.")
                            last_hash = current_hash
                            return True
                    except Exception:
                        pass
                    return False

                if settings.DEBUG:
                    autoreload.file_changed.connect(check_modules_file)
        except Exception:
            pass
