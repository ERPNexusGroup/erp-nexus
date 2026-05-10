"""
Router de marketplace — catálogo, instalación y desinstalación de módulos.
"""
from ninja import Router, Schema
from typing import List, Optional

from apps.core_api.auth import JWTAuth
from apps.core_marketplace.models import ModuleCatalogItem, EnabledModule, ModuleDownload
from apps.core_marketplace.utils.module_loader import read_modules_enabled, write_modules_enabled
from django.core.management import call_command

router = Router(auth=JWTAuth())


# ─── Schemas ──────────────────────────────────────────────────────────
class ModuleCatalogOut(Schema):
    technical_name: str
    display_name: str
    version: str
    module_type: str
    repo_url: Optional[str]
    min_erp_version: str
    max_erp_version: Optional[str]
    python_dependencies: dict
    system_dependencies: dict
    documentation_url: Optional[str]
    is_installed: bool
    installed_at: Optional[str]


class EnabledModuleOut(Schema):
    technical_name: str
    django_app: str
    status: str
    enabled_at: str


class MessageResponse(Schema):
    message: str
    success: bool


# ─── GET /api/v1/marketplace/catalog/ ─────────────────────────────────
@router.get("/catalog", response=List[ModuleCatalogOut])
def list_catalog(request, module_type: Optional[str] = None, installed: Optional[bool] = None):
    """
    Lista todos los módulos disponibles en el catálogo.

    Query params:
      - module_type: filter por tipo ('essential', 'optional', 'plugin')
      - installed: true (solo instalados) | false (solo no instalados)
    """
    qs = ModuleCatalogItem.objects.filter(is_active=True)

    if module_type:
        qs = qs.filter(module_type=module_type)
    if installed is True:
        qs = qs.filter(installed_at__isnull=False)
    elif installed is False:
        qs = qs.filter(installed_at__isnull=True)

    enabled_apps = read_modules_enabled()
    installed_technical_names = set(
        EnabledModule.objects.values_list("technical_name", flat=True)
    )

    result = []
    for item in qs:
        is_installed = item.technical_name in installed_technical_names or item.installed_at is not None
        result.append(ModuleCatalogOut(
            technical_name=item.technical_name,
            display_name=item.display_name or item.technical_name,
            version=item.version,
            module_type=item.module_type,
            repo_url=item.repo_url,
            min_erp_version=item.min_erp_version,
            max_erp_version=item.max_erp_version,
            python_dependencies=item.python_dependencies,
            system_dependencies=item.system_dependencies,
            documentation_url=item.documentation_url,
            is_installed=is_installed,
            installed_at=str(item.installed_at) if item.installed_at else None,
        ))
    return result


# ─── POST /api/v1/marketplace/{name}/install/ ─────────────────────────
@router.post("/{technical_name}/install", response=MessageResponse)
def install_module(request, technical_name: str):
    """
    Instala un módulo desde el catálogo.

    - Clona el repositorio a modules/{technical_name}/
    - Valida __meta__.py
    - Registra en EnabledModule
    - Actualiza modules_enabled.py
    """
    try:
        call_command("module_install", technical_name, stdout=StdoutCapture(), stderr=StdoutCapture())
        return {"message": f"Module '{technical_name}' installed successfully", "success": True}
    except Exception as exc:
        return {"message": f"Install failed: {str(exc)}", "success": False}


# ─── POST /api/v1/marketplace/{name}/uninstall/ ───────────────────────
@router.post("/{technical_name}/uninstall", response=MessageResponse)
def uninstall_module(request, technical_name: str):
    """
    Desinstala un módulo.

    - Elimina de modules/{technical_name}/ (opcional: keep-data)
    - Elimina de EnabledModule
    - Actualiza modules_enabled.py
    """
    try:
        call_command("module_uninstall", technical_name, stdout=StdoutCapture(), stderr=StdoutCapture())
        return {"message": f"Module '{technical_name}' uninstalled successfully", "success": True}
    except Exception as exc:
        return {"message": f"Uninstall failed: {str(exc)}", "success": False}


# ─── GET /api/v1/marketplace/installed/ ───────────────────────────────
@router.get("/installed", response=List[EnabledModuleOut])
def list_installed(request):
    """Lista módulos actualmente instalados/habilitados."""
    modules = EnabledModule.objects.all().order_by("-enabled_at")
    return [
        EnabledModuleOut(
            technical_name=m.technical_name,
            django_app=m.django_app,
            status=m.status,
            enabled_at=str(m.enabled_at),
        )
        for m in modules
    ]


# ─── GET /api/v1/marketplace/status ───────────────────────────────────
@router.get("/status")
def marketplace_status(request):
    """Estado del marketplace: módulos instalados vs catálogo."""
    installed = EnabledModule.objects.count()
    catalog = ModuleCatalogItem.objects.filter(is_active=True).count()
    return {
        "installed_modules": installed,
        "available_in_catalog": catalog,
        "marketplace_ready": True,
    }


# ─── Helper para capturar output de call_command ──────────────────────
class StdoutCapture:
    def write(self, msg):
        pass
    def flush(self):
        pass
