"""
Router de page builder — CRUD de páginas y componentes.
"""
from ninja import Router, Schema
from typing import List, Optional, Any

from apps.core_api.auth import JWTAuth
from apps.core_pagebuilder.models import Page, Component

router = Router(auth=JWTAuth())


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
    updated_at: str


class PageCreate(Schema):
    title: str
    description: str = ""
    layout: List[Any] = []


class ComponentOut(Schema):
    id: int
    name: str
    component_type: str
    description: str
    default_props: dict


class MessageResponse(Schema):
    message: str


@router.get("/", response=List[PageOut])
def list_pages(request, status: str = None):
    """Lista páginas creadas."""
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
    """Detalle de una página con su layout."""
    p = Page.objects.get(id=page_id)
    return PageDetail(
        id=p.id,
        title=p.title,
        slug=p.slug,
        description=p.description,
        status=p.status,
        layout=p.layout,
        meta_title=p.meta_title,
        meta_description=p.meta_description,
        updated_at=str(p.updated_at),
    )


@router.post("/", response=PageDetail)
def create_page(request, data: PageCreate):
    """Crea una nueva página."""
    user = getattr(request, "auth", None)
    page = Page.objects.create(
        title=data.title,
        description=data.description,
        layout=data.layout,
        created_by=user.username if user else "",
    )
    return PageDetail(
        id=page.id,
        title=page.title,
        slug=page.slug,
        description=page.description,
        status=page.status,
        layout=page.layout,
        meta_title=page.meta_title,
        meta_description=page.meta_description,
        updated_at=str(page.updated_at),
    )


@router.put("/{page_id}", response=PageDetail)
def update_page(request, page_id: int, data: PageCreate):
    """Actualiza una página."""
    page = Page.objects.get(id=page_id)
    page.title = data.title
    page.description = data.description
    page.layout = data.layout
    page.save()
    return PageDetail(
        id=page.id,
        title=page.title,
        slug=page.slug,
        description=page.description,
        status=page.status,
        layout=page.layout,
        meta_title=page.meta_title,
        meta_description=page.meta_description,
        updated_at=str(page.updated_at),
    )


@router.post("/{page_id}/publish", response=MessageResponse)
def publish_page(request, page_id: int):
    """Publica una página."""
    page = Page.objects.get(id=page_id)
    page.publish()
    return {"message": f"Página '{page.title}' publicada"}


@router.get("/components/available", response=List[ComponentOut])
def list_components(request):
    """Lista componentes disponibles para el page builder."""
    components = Component.objects.filter(is_active=True)
    return [
        ComponentOut(
            id=c.id,
            name=c.name,
            component_type=c.component_type,
            description=c.description,
            default_props=c.default_props,
        )
        for c in components
    ]
