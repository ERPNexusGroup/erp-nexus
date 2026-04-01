"""
Router de marketplace — búsqueda e instalación de módulos.
"""
from ninja import Router, Schema
from typing import List, Optional

from apps.core_api.auth import JWTAuth
from apps.core_marketplace.registry import ModuleRegistry, search_modules, ModuleDownload

router = Router(auth=JWTAuth())


class RegistryOut(Schema):
    id: int
    name: str
    source_type: str
    url: str
    is_active: bool
    is_default: bool
    module_count: int
    last_sync: Optional[str]


class ModuleSearchResult(Schema):
    name: str
    description: str
    source: str
    version: str
    registry: str


class MessageResponse(Schema):
    message: str


@router.get("/registries", response=List[RegistryOut])
def list_registries(request):
    """Lista registros de módulos configurados."""
    registries = ModuleRegistry.objects.filter(is_active=True)
    return [
        RegistryOut(
            id=r.id,
            name=r.name,
            source_type=r.source_type,
            url=r.url,
            is_active=r.is_active,
            is_default=r.is_default,
            module_count=len(r.cached_modules or {}),
            last_sync=str(r.last_sync) if r.last_sync else None,
        )
        for r in registries
    ]


@router.post("/registries/{registry_id}/sync", response=MessageResponse)
def sync_registry(request, registry_id: int):
    """Sincroniza un registro (actualiza lista de módulos disponibles)."""
    registry = ModuleRegistry.objects.get(id=registry_id)
    count = registry.sync()
    return {"message": f"Sincronizado: {count} módulos encontrados"}


@router.get("/search", response=List[ModuleSearchResult])
def search(request, q: str = "", registry: str = None, category: str = None):
    """Busca módulos disponibles en los registros."""
    results = search_modules(query=q, registry_name=registry, category=category)
    return [
        ModuleSearchResult(
            name=r["name"],
            description=r["description"],
            source=r["source"],
            version=r["version"],
            registry=r["registry"],
        )
        for r in results
    ]


@router.get("/downloads")
def list_downloads(request, limit: int = 20):
    """Lista descargas recientes de módulos."""
    downloads = ModuleDownload.objects.all()[:limit]
    return [
        {
            "module_name": d.module_name,
            "version": d.version,
            "status": d.status,
            "downloaded_at": str(d.downloaded_at),
            "error": d.error_message,
        }
        for d in downloads
    ]
