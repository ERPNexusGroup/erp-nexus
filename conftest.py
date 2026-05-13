# conftest.py global — carga módulos dinámicos antes de Django setup
import os
import sys
from pathlib import Path

def pytest_configure():
    """Configura Django para tests incluyendo MODULE_APPS."""
    # Asegurar que el proyecto esté en path
    BASE_DIR = Path(__file__).resolve().parent.parent / "repos/erp-nexus"
    if str(BASE_DIR) not in sys.path:
        sys.path.insert(0, str(BASE_DIR))

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "erp_nexus.settings")

    # Cargar MODULE_APPS antes de django.setup()
    try:
        from erp_nexus.modules_enabled import MODULE_APPS
        from django.conf import settings
        for app in MODULE_APPS:
            if app not in settings.INSTALLED_APPS:
                settings.INSTALLED_APPS.append(app)
    except ImportError:
        pass

    # pytest-django llamará a django.setup() después de este hook
