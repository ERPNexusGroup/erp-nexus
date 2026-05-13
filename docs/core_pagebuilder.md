# core_pagebuilder — Page Builder Module

**Tier:** 1 — Core Essential
**Status:** ✅ Production Ready (Phase 0.6.2 — 2026-05-13)
**Architecture:** Hybrid — JSON layout storage + server-side rendering

---

## 📖 Overview

`core_pagebuilder` es un sistema de construcción de páginas web sin headless CRM:
- **Admin:** Crea/edita páginas con layouts JSON (drag-drop futuro)
- **Public:** Páginas renders servidas desde Django (SSR — sin JS obligatorio)
- **API:** REST endpoints para CRUD + JSON render endpoint

---

## 🏗️ Architecture

```
Page (model)
  └─ layout: JSON array de componentes
        ├─ heading   → <h1>…</h1>
        ├─ text      → <div>…</div>
        ├─ image     → <img …>
        ├─ button    → <a class="btn" …>
        ├─ columns   → CSS Grid con hijos recursivos
        ├─ spacer    → <div style="height:…">
        ├─ divider   → <hr>
        └─ html      → contenido HTML directo (admin only)

PageRenderer (renderer.py)
  └─ Recorre layout → _render_component() → mark_safe HTML string

Views
  ├─ PageDetailView (HTML template) — /pages/<slug>/
  └─ render_page   (JSON endpoint) — /pages/<slug>/render/

Templates
  ├─ base.html  (layout base con CSS)
  └─ page_detail.html (extiende base, inserta components_html)
```

---

## 📁 Project Structure

```
apps/core_pagebuilder/
├── __init__.py
├── admin.py              # PageAdmin con preview button
├── apps.py               # AppConfig
├── models.py             # Page + Component models
├── serializers.py        # Django Ninja serializers (API)
├── validators.py         # JSON schema validation
├── renderer.py           # PageRenderer (HTML generation)
├── views.py              # API viewsets (Django Ninja router)
├── views_public.py       # Vistas HTML + JSON endpoint
├── urls.py               # Router API (/api/v1/pages/)
├── urls_public.py        # URLs públicas (/pages/<slug>/)
├── templates/
│   └── core_pagebuilder/
│       ├── base.html              # Layout base
│       └── page_detail.html       # Página individual
├── static/
│   └── core_pagebuilder/
│       └── page-builder.css        # Component CSS
├── management/
│   └── commands/
│       ├── create_demo_pages.py    # Crear pages demo
│       └── publish_all.py          # Publicar todas
└── migrations/
    └── 0001_initial.py
```

---

## 🔌 API Reference

### Public Endpoints (sin autenticación)

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | `/pages/<slug>/` | Vista HTML pública de página (solo `status='published'`) |
| GET | `/pages/<slug>/render/` | JSON `{title, slug, html}` con HTML renderizado |

### Admin Endpoints (JWT required — `/api/v1/`)

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | `/api/v1/pages/` | Listar páginas (query: `?status=` filtro opcional) |
| GET | `/api/v1/pages/{id}/` | Detalle página por ID |
| POST | `/api/v1/pages/` | Crear nueva página |
| PUT | `/api/v1/pages/{id}/` | Actualizar página |
| DELETE | `/api/v1/pages/{id}/` | Eliminar (archivar) página |
| POST | `/api/v1/pages/{id}/publish/` | Publicar página (status→'published') |
| GET | `/api/v1/pages/components/` | Catálogo de componentes disponibles |

**Auth:** Todos los endpoints admin requieren header `Authorization: Bearer <jwt_token>`.

---

## 📦 Models

### Page

```python
class Page(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Borrador'),
        ('published', 'Publicada'),
        ('archived', 'Archivada'),
    ]

    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True, blank=True)  # auto-genera si blank
    description = models.TextField(blank=True, default='')
    layout = models.JSONField(default=list)  # [{type, props}, …]
    meta_title = models.CharField(max_length=200, blank=True, default='')
    meta_description = models.TextField(blank=True, default='')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    created_by = models.CharField(max_length=150, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    published_at = models.DateTimeField(null=True, blank=True)

    component_count = property(lambda self: len(self.layout or []))

    def publish(self):
        self.status = 'published'
        if not self.published_at:
            self.published_at = timezone.now()
        self.save()
```

### Component (Catalog)

```python
class Component(models.Model):
    name = models.CharField(max_length=100)
    component_type = models.CharField(max_length=50)  # heading, text, image…
    description = models.TextField(blank=True)
    default_props = models.JSONField(default=dict)   # {…default values}
    is_active = models.BooleanField(default=True)
```

---

## 🎨 Component Types

| Type | Props | Render Output |
|------|-------|---------------|
| `heading` | `level` (1-6), `text` | `<h{level}>{text}</h{level}>` |
| `text` | `content` (HTML allowed) | `<div>{content}</div>` |
| `image` | `src`, `alt`, `width`, `height` | `<img src="{src}" … loading="lazy">` |
| `button` | `label`, `url`, `target`, `rel` | `<a href="{url}" class="btn">{label}</a>` |
| `spacer` | `height` (px) | `<div style="height:{height}px">` |
| `divider` | — | `<hr class="cp-divider">` |
| `html` | `content` (raw HTML) | `{content}` (admin-only trusted) |
| `columns` | `children` (list components), `gap` | CSS Grid con hijos recursivos |

**Layout JSON example:**
```json
[
  {
    "type": "heading",
    "props": { "level": 1, "text": "Bienvenido" }
  },
  {
    "type": "columns",
    "props": {
      "gap": "1rem",
      "children": [
        { "type": "text", "props": { "content": "<h3>Columna 1</h3><p>…</p>" } },
        { "type": "image", "props": { "src": "/static/img/photo.jpg", "alt": "…" } }
      ]
    }
  },
  {
    "type": "button",
    "props": { "label": "Comenzar", "url": "/auth/login/", "target": "_self" }
  }
]
```

---

## 🔧 Renderer

**File:** `apps/core_pagebuilder/renderer.py`

```python
from core_pagebuilder.renderer import PageRenderer

renderer = PageRenderer()
html = renderer.render_to_html(page)  # → SafeString (mark_safe)
```

**Strategy:**
- Plantillas inline por tipo (sin archivos .html externos para componentes)
- Recursión para `columns` (CSS Grid)
- `mark_safe()` al final — contenido admin es trusted

**Custom component:**
```python
from core_pagebuilder.renderer import PageRenderer

class MyRenderer(PageRenderer):
    COMPONENT_TEMPLATES = {
        **PageRenderer.COMPONENT_TEMPLATES,
        'mytype': '<div class="my-class">{content}</div>',
    }
```

---

## 🎯 Management Commands

### `create_demo_pages`
Crea 3 páginas demo: Home, About, Contact.
```bash
uv run python manage.py create_demo_pages
```
**Output:**
```
✅ Home page creada: /pages/home/
✅ About page creada: /pages/about/
✅ Contact page creada: /pages/contact/
```

### `publish_all`
Publica todas las páginas en estado draft.
```bash
uv run python manage.py publish_all
```

---

## 🧪 Testing

### Manual QA (verificada 2026-05-13)
```bash
# HTML pages
curl http://localhost:8000/pages/home/      # 200 + HTML
curl http://localhost:8000/pages/about/     # 200 + HTML
curl http://localhost:8000/pages/contact/   # 200 + HTML

# JSON render
curl http://localhost:8000/pages/home/render/ | python3 -m json.tool

# Admin API (requiere JWT)
curl -H "Authorization: Bearer <token>" http://localhost:8000/api/v1/pages/
```

### Django Check
```bash
uv run python manage.py check        # 0 issues
uv run python manage.py makemigrations --check  # sin cambios pendientes
```

---

## ⚙️ Settings

Configuración en `erp_nexus/settings.py`:

```python
INSTALLED_APPS = [
    # …
    'apps.core_pagebuilder',
]

# Static files (CSS)
STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']  # desarrollo
STATIC_ROOT = BASE_DIR / 'staticfiles'    # producción
```

**Cache (opcional — actualmente 5 min inline):**
```python
#views_public.py
@cache_page(60 * 5)  # 5 minutos CDN/browser cache
def render_page(request, slug): …
```

---

## 🔐 Security Notes

- **Public pages:** Solo `status='published'` visibles
- **Admin API:** Protegida por JWT (`JWTAuth` en Django Ninja)
- **HTML injection:** `mark_safe()` solo en contenido trusted (admin-only `html` component)
- **CSRF:** Vistas públicas no requieren CSRF (GET only)
- **XSS:** Escape automático de variables en templates Django

---

## 📈 Performance

- **Render time:** ~2-5ms por página (layout small < 10 components)
- **Cache:** `@cache_page(300)` en endpoint público (5 min HTTP cache)
- **DB queries:** 1 SELECT por página (Page.objects.get)
- **Tamaño HTML:** ~3-15KB típico (sin minificar)

---

## 🚀 Deployment

### Prereqs
```bash
cd erp-nexus
uv sync  # instalar dependencias
uv run python manage.py migrate          # aplicar migraciones
uv run python manage.py collectstatic    # recoger estáticos
```

### Docker Production
El stack Docker ya incluye `core_pagebuilder` como app instalada.
No configuración adicional necesaria.

---

## 🐛 Troubleshooting

| Síntomo | Causa probable | Solución |
|---------|----------------|----------|
| `/pages/<slug>/` → 404 | Página no existe o no está `published` | `manage.py shell` → `Page.objects.filter(slug='…').update(status='published')` |
| JSON render 500 — `TypeError: render_page() missing ...` | `@method_decorator` en función | Usar `@cache_page` (ya corregido) |
| CSS no carga | `{% load static %}` faltante en `base.html` | Verificar template |
| HTML components no renderizan | `mark_safe` omission | `renderer.py` línea 120 — retornar `mark_safe(result)` |

---

## 📚 Related

- **STATE.md** — `.paul/STATE.md` (fases 0.6.2 applied complete)
- **MEMORY.md** — core_pagebuilder completion log (2026-05-13)
- **PAUL Phase Doc** — `.paul/phases/00-foundation/00-06-PAGEBUILDER-API.md`
- **Django Ninja** — https://django-ninja.rest-framework.com/
- **Django caching** — https://docs.djangoproject.com/en/5.0/topics/cache/

---

**Last updated:** 2026-05-13 | Phase 0.6.2 — COMPLETE ✅ | JARVIS
