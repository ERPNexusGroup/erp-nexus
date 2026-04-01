"""
Router de módulos — endpoints para gestión de módulos.
"""
from ninja import Router, Schema
from typing import Optional
from datetime import datetime

from apps.core_marketplace.models import ModuleCatalogItem

router = Router()


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
