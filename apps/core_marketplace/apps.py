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
        """Watch modules_enabled.py for changes and suggest restart."""
        # En desarrollo: verificar si modules_enabled.py cambió
        # En producción: este chequeo se hace en el script de inicio (systemd/docker)
        try:
            from django.utils import autoreload

            modules_path = Path(settings.BASE_DIR) / "erp_nexus" / "modules_enabled.py"

            if modules_path.exists():
                # Calcular hash para detecting cambios
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

                # Registrar callback con el autoreloader de Django (solo en DEBUG=True)
                if settings.DEBUG:
                    autoreload.file_changed.connect(check_modules_file)
        except Exception:
            # Ignorar errores en producción (DEBUG=False)
            pass
