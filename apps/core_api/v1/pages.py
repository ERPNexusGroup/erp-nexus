"""
Router de page builder — CRUD de páginas y componentes (extendido).

Endpoints autenticados (admin):
  /api/v1/pages/              — CRUD
  /api/v1/pages/{id}/publish/ — publicar
  /api/v1/pages/components/  — catálogo componentes

Endpoints públicos (fuera de API, por urls_public.py):
  /pages/<slug>/              — vista HTML pública
  /pages/<slug>/render/       — JSON con HTML renderizado
"""
from ninja import Router, Schema
from typing import List, Optional, Any
from django.shortcuts import get_object_or_404

from apps.core_api.auth import JWTAuth
from apps.core_pagebuilder.models import Page, Component
from apps.core_pagebuilder.validators import validate_layout_schema


# ─── Schemas ──────────────────────────────────────────────────────────

class PageOut(Schema):
    id: int
    title: str
    slug: str
    status: str
    component_count: int
    updated_at: str
    published_at: Optional[str]


class PageDetail(Schema):
    id: int
    title: str
    slug: str
    description: str
    status: str
    layout: List[Any]
    meta_title: str
    meta_description: str
    created_by: str
    created_at: str
    updated_at: str
    published_at: Optional[str]


class PageCreate(Schema):
    title: str
    slug: Optional[str] = None
    description: str = ""
    layout: List[Any]
    meta_title: str = ""
    meta_description: str = ""

    def validate_layout(self, value):
        validate_layout_schema(value)
        return value


class PageUpdate(Schema):
    title: Optional[str] = None
    slug: Optional[str] = None
    description: Optional[str] = None
    layout: Optional[List[Any]] = None
    meta_title: Optional[str] = None
    meta_description: Optional[str] = None


class ComponentOut(Schema):
    id: int
    name: str
    component_type: str
    description: str
    default_props: dict
    is_active: bool


class MessageResponse(Schema):
    message: str


# ─── Router ────────────────────────────────────────────────────────────

router = Router(auth=JWTAuth(), tags=["pages"])


# ─── CRUD Autenticado ─────────────────────────────────────────────────

@router.get("/", response=List[PageOut])
def list_pages(request, status: str = None):
    """Lista todas las páginas (admin)."""
    qs = Page.objects.all()
    if status:
        qs = qs.filter(status=status)
    return [
        PageOut(
            id=p.id,
            title=p.title,
            slug=p.slug,
            status=p.status,
            component_count=p.component_count,
            updated_at=str(p.updated_at),
            published_at=str(p.published_at) if p.published_at else None,
        )
        for p in qs
    ]


@router.get("/{page_id}", response=PageDetail)
def get_page(request, page_id: int):
    """Detalle de una página por ID (admin)."""
    p = get_object_or_404(Page, id=page_id)
    return PageDetail(
        id=p.id,
        title=p.title,
        slug=p.slug,
        description=p.description,
        status=p.status,
        layout=p.layout,
        meta_title=p.meta_title,
        meta_description=p.meta_description,
        created_by=p.created_by,
        created_at=str(p.created_at),
        updated_at=str(p.updated_at),
        published_at=str(p.published_at) if p.published_at else None,
    )


@router.post("/", response=PageDetail)
def create_page(request, data: PageCreate):
    """Crea una nueva página (admin)."""
    user = getattr(request, "auth", None)
    page = Page.objects.create(
        title=data.title,
        slug=data.slug,  # save() auto-genera si es None
        description=data.description,
        layout=data.layout,
        meta_title=data.meta_title,
        meta_description=data.meta_description,
        created_by=user.username if user else "",
    )
    return _page_detail_response(page)


@router.put("/{page_id}", response=PageDetail)
def update_page(request, page_id: int, data: PageUpdate):
    """Actualiza una página (admin)."""
    page = get_object_or_404(Page, id=page_id)

    if data.title is not None:
        page.title = data.title
    if data.slug is not None:
        page.slug = data.slug
    if data.description is not None:
        page.description = data.description
    if data.layout is not None:
        validate_layout_schema(data.layout)
        page.layout = data.layout
    if data.meta_title is not None:
        page.meta_title = data.meta_title
    if data.meta_description is not None:
        page.meta_description = data.meta_description

    page.save()
    return _page_detail_response(page)


@router.delete("/{page_id}")
def delete_page(request, page_id: int):
    """Elimina (archiva) una página."""
    page = get_object_or_404(Page, id=page_id)
    page_title = page.title
    page.delete()
    return {"detail": f"Página '{page_title}' eliminada."}


@router.post("/{page_id}/publish", response=MessageResponse)
def publish_page(request, page_id: int):
    """Publica una página (cambia status a 'published')."""
    page = get_object_or_404(Page, id=page_id)
    page.publish()
    return {"message": f"Página '{page.title}' publicada exitosamente."}


# ─── Components Catálogo ───────────────────────────────────────────────

@router.get("/components/", response=List[ComponentOut])
def list_components(request):
    """Lista componentes activos (admin)."""
    components = Component.objects.filter(is_active=True)
    return [
        ComponentOut(
            id=c.id,
            name=c.name,
            component_type=c.component_type,
            description=c.description,
            default_props=c.default_props,
            is_active=c.is_active,
        )
        for c in components
    ]


# ─── Helper ────────────────────────────────────────────────────────────

def _page_detail_response(page: Page) -> PageDetail:
    return PageDetail(
        id=page.id,
        title=page.title,
        slug=page.slug,
        description=page.description,
        status=page.status,
        layout=page.layout,
        meta_title=page.meta_title,
        meta_description=page.meta_description,
        created_by=page.created_by,
        created_at=str(page.created_at),
        updated_at=str(page.updated_at),
        published_at=str(page.published_at) if page.published_at else None,
    )
