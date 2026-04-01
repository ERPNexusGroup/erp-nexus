"""
Router de módulos — endpoints para gestión de módulos.
Protegido con JWT Auth.
"""
from ninja import Router, Schema
from typing import Optional
from datetime import datetime

from apps.core_marketplace.models import ModuleCatalogItem
from apps.core_api.auth import JWTAuth

router = Router(auth=JWTAuth())


class ModuleOut(Schema):
    technical_name: str
    version: str
    status: str
    is_active: bool
    django_app: Optional[str]
    installed_path: Optional[str]
    installed_at: Optional[datetime]


class ModuleStats(Schema):
    total: int
    active: int
    inactive: int


class MessageResponse(Schema):
    message: str


@router.get("/", response=list[ModuleOut])
def list_modules(request):
    """Lista todos los módulos instalados."""
    return list(ModuleCatalogItem.objects.all())


@router.get("/stats", response=ModuleStats)
def module_stats(request):
    """Estadísticas de módulos."""
    qs = ModuleCatalogItem.objects.all()
    return {
        "total": qs.count(),
        "active": qs.filter(is_active=True).count(),
        "inactive": qs.filter(is_active=False).count(),
    }


@router.get("/{technical_name}", response=ModuleOut)
def get_module(request, technical_name: str):
    """Detalle de un módulo por nombre técnico."""
    return ModuleCatalogItem.objects.get(technical_name=technical_name)


@router.post("/{technical_name}/activate", response=MessageResponse)
def activate_module(request, technical_name: str):
    """Activa un módulo instalado."""
    module = ModuleCatalogItem.objects.get(technical_name=technical_name)

    if module.django_app:
        from apps.core_marketplace.models import EnabledModule
        from apps.core_marketplace.activation import write_modules_enabled

        EnabledModule.objects.update_or_create(
            technical_name=technical_name,
            defaults={"django_app": module.django_app, "status": "active"},
        )
        write_modules_enabled()

    module.status = "active"
    module.is_active = True
    module.save(update_fields=["status", "is_active"])

    return {"message": f"Módulo {technical_name} activado"}


@router.post("/{technical_name}/deactivate", response=MessageResponse)
def deactivate_module(request, technical_name: str):
    """Desactiva un módulo activo."""
    module = ModuleCatalogItem.objects.get(technical_name=technical_name)

    module.status = "inactive"
    module.is_active = False
    module.save(update_fields=["status", "is_active"])

    # Remover de enabled
    try:
        from apps.core_marketplace.models import EnabledModule
        from apps.core_marketplace.activation import write_modules_enabled

        EnabledModule.objects.filter(technical_name=technical_name).delete()
        write_modules_enabled()
    except Exception:
        pass

    return {"message": f"Módulo {technical_name} desactivado"}
