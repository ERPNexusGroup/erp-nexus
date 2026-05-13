# Phase 0.6.2 — core_pagebuilder: API + Frontend Completion
**Módulo:** core_pagebuilder (Tier 1 — Core Framework)
**Estado actual:** Modelos + Admin ✅ | API + Frontend ❌
**Objetivo:** Implementar API REST + servicio de renderizado + frontend components
**Duración estimada:** 8-12 horas
**Dependencias:** Ninguna (independiente)

---

## 📋 Task Breakdown

### 0.6.2.1 — Serializers & API Foundation (2h)
- [ ] Crear `apps/core_pagebuilder/serializers.py`
  - `PageSerializer` (read/write con validación de layout JSON)
  - `ComponentSerializer`
  - Campos: `title`, `slug`, `status`, `layout` (validación schema)
  - Nested `Component` list en Page para crear/editar en una llamada
- [ ] Crear `apps/core_pagebuilder/views.py`
  - `PageViewSet` (CRUD completo: list, retrieve, create, update, partial_update, destroy, publish)
  - `ComponentViewSet` (read-only + admin CRUD)
  - Filtros: `?status=published`, `?slug=...`
  - Permisos: `IsAdminOrReadOnly` (páginas published son públicas, borrador solo admin)
- [ ] Crear `apps/core_pagebuilder/urls.py`
  - Router: `/api/v1/pages/` (page CRUD)
  - Router: `/api/v1/components/` (component catalog)
  - Endpoint: `/api/v1/pages/<slug>/` (retrieve público — siempre visible si published)
  - Endpoint: `/api/v1/render/<slug>/` (HTML renderizado directo)

### 0.6.2.2 — Layout Validation Schema (1h)
- [ ] Definir schema JSON para `Page.layout`:
  ```json
  [
    {
      "type": "heading|text|image|button|columns|spacer|divider|html",
      "props": { ... campos específicos ... },
      "id": "uuidv4"  // único por componente
    }
  ]
  ```
- [ ] Implementar `validators.py`:
  - `validate_layout_schema(layout)` — valida estructura, tipos, campos requeridos
  - `validate_component_props(props, component_type)` — valida props por tipo
- [ ] Tests unitarios para validators (10 casos: válido, tipo inválido, props faltantes, tipo desconocido)

### 0.6.2.3 — Render Service (2h)
- [ ] Crear `apps/core_pagebuilder/renderer.py`:
  - `PageRenderer` class
  - `render_to_html(page) → str` — convierte layout JSON → HTML seguro
  - `render_to_context(page) → dict` — para templates Django
  - Lógica por tipo de componente:
    - `heading`: `<h1..6>{{ text }}</h1..6>`
    - `text`: `<p>{{ content }}</p>`
    - `image`: `<img src="{{ src }}" alt="{{ alt }}">`
    - `button`: `<a href="{{ url }}" class="btn">{{ label }}</a>`
    - `columns`: `<div class="row"><div class="col">{{ children }}</div></div>`
    - `spacer`: `<div class="spacer" style="height: {{ height }}px"></div>`
    - `divider`: `<hr class="divider">`
    - `html`: `{{ safe_html | safe }}`
- [ ] Templates partials en `templates/core_pagebuilder/components/`:
  - `_heading.html`, `_text.html`, `_image.html`, etc.
  - O alternatively: render inline sin templates (más simple)
- [ ] Cache de renders: `@cache_page(60*5)` para páginas published

### 0.6.2.4 — Template Views + Public URLs (1.5h)
- [ ] Crear `apps/core_pagebuilder/views_public.py`:
  - `page_detail(request, slug)` — vista pública de página
  - Usa `Page.objects.get(slug=slug, status='published')`
  - Context: `page`, `components_html` (renderizados)
  - Template: `core_pagebuilder/page_detail.html`
- [ ] `apps/core_pagebuilder/urls_public.py`:
  - `path('<slug:slug>/', page_detail, name='page_detail')`
  - Incluir en `erp_nexus/urls.py` bajo `path('pages/', include('core_pagebuilder.urls_public'))`
- [ ] Template base: `templates/core_pagebuilder/page_detail.html`
  - Extiende `base.html`
  - Renderiza cada componente vía partials o inline

### 0.6.2.5 — Frontend Components Library (2h)
- [ ] Crear `apps/core_pagebuilder/static/core_pagebuilder/`:
  - `page-builder.css` — estilos base para componentes:
    - `.cp-heading`, `.cp-text`, `.cp-image`, `.cp-button`, `.cp-columns`, `.cp-spacer`, `.cp-divider`
    - Grid system para columns (CSS grid o flex)
  - `page-builder.js` — librería cliente (opcional, para futura edición inline)
- [ ] Integrar CSS en template público: `{% static 'core_pagebuilder/page-builder.css' %}`
- [ ] Ejemplo de uso en `page_detail.html` que aplica clases automáticamente

### 0.6.2.6 — Management Commands (0.5h)
- [ ] `apps/core_pagebuilder/management/commands/create_demo_pages.py`:
  - Crea 3 páginas demo: Home, About, Contact
  - Layouts predefinidos en JSON
  - Flag `--reset` para eliminar y recrear
- [ ] `apps/core_pagebuilder/management/commands/publish_all.py`:
  - Publica todas las páginas en draft (bulk action)

### 0.6.2.7 — Tests (2h)
- [ ] `apps/core_pagebuilder/tests/test_models.py`:
  - Page slug auto-generation
  - Component creation
  - `publish()` method
- [ ] `apps/core_pagebuilder/tests/test_serializers.py`:
  - Validación layout schema (válido/inválido)
  - CRUD pages via serializers
- [ ] `apps/core_pagebuilder/tests/test_views.py` (API):
  - List pages (admin vs anon)
  - Create page (admin)
  - Retrieve published page (anon allowed)
  - Retrieve draft page (anon → 404)
  - Publish endpoint
- [ ] `apps/core_pagebuilder/tests/test_renderer.py`:
  - Cada tipo de componente rendered a HTML correctamente
  - Sanitización de HTML en `html` component type
- [ ] `apps/core_pagebuilder/tests/test_urls.py`:
  - Public URL resuelve correctamente
  - Admin URLs requieren auth
- [ ] Coverage target: 85%+

### 0.6.2.8 — Documentation (1h)
- [ ] `docs/core_pagebuilder.md`:
  - Overview + arquitectura
  - JSON schema de layout (con ejemplo completo)
  - API endpoints (request/response ejemplos)
  - Cómo crear componentes personalizados
  - Cómo extender renderer
  - Templates disponibles
- [ ] `README.md` en el directorio del módulo:
  - Quick start (5 min)
  - Comandos management
  - Testing

### 0.6.2.9 — Integration & Polish (1h)
- [ ] Verificar que `Page` aparece en admin dashboard
- [ ] Agregar botón "Preview" en admin Page change view (link a `/pages/<slug>/`)
- [ ] Añadir `Page` a `ERPNexusStats` (core_stats) para mostrar count en dashboard
- [ ] Validar `python manage.py check` sin errores
- [ ] Ejecutar seed y verificar páginas demo creadas
- [ ] Commit con mensaje estructurado

---

## 🎯 Success Criteria

| Criterio | Medición | Mínimo |
|----------|----------|--------|
| API endpoints funcionando | `curl /api/v1/pages/` | 200 OK |
| Páginas publicadas accesibles | GET `/pages/home/` | 200 + HTML |
| Layout validation | Post inválido → 400 | Sí |
| Tests unitarios | `pytest` | 85% coverage |
| Admin preview button | Page change view | Enlace visible |
| Demo pages | `create_demo_pages` | 3 páginas creadas |

---

## 🔄 Dependencies & Order

```
0.6.2.1 (Serializers)  → 0.6.2.3 (Renderer)  → 0.6.2.4 (Views Public)
     ↓                       ↓                        ↓
0.6.2.2 (Validation)  → 0.6.2.5 (Frontend)   → 0.6.2.7 (Tests)
                              ↓
                      0.6.2.6 (Commands) → 0.6.2.8 (Docs) → 0.6.2.9 (Polish)
```

**Secuencia óptima:**
1 → 2 → 3 → 4 → 5 → 6 → 7 → 8 → 9

---

## 📁 File Manifest (New/Modified)

```
apps/core_pagebuilder/
├── serializers.py              [NEW]
├── views.py                    [NEW]
├── views_public.py             [NEW]
├── urls.py                     [NEW]
├── urls_public.py              [NEW]
├── renderer.py                 [NEW]
├── validators.py               [NEW]
├── management/commands/
│   ├── create_demo_pages.py    [NEW]
│   └── publish_all.py          [NEW]
├── templates/
│   └── core_pagebuilder/
│       └── page_detail.html    [NEW]
├── static/
│   └── core_pagebuilder/
│       ├── page-builder.css    [NEW]
│       └── page-builder.js     [NEW]
├── tests/
│   ├── test_models.py          [UPDATE]
│   ├── test_serializers.py     [NEW]
│   ├── test_views.py           [NEW]
│   ├── test_renderer.py        [NEW]
│   └── test_urls.py            [NEW]
└── admin.py                    [UPDATE: add preview button]

docs/
└── core_pagebuilder.md         [NEW]

README.md (update: add pagebuilder section) [UPDATE]
```

---

## 🧪 Test Plan

### Unit Tests
- Serializer validation (layout schema)
- Renderer output por componente
- `Page.publish()` cambia status + timestamp

### Integration Tests
- API CRUD (admin user)
- Public retrieval (anon user)
- Draft page → 404 para anon
- Publish endpoint → status cambia

### Manual QA
1. Admin crea página con layout JSON
2. Publish → ver `/pages/slug/` público
3. Componentes se renderizan con estilos
4. Admin preview button funciona

---

## ⚠️ Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Layout JSON muy complejo | Alto | Limitamos a 8 tipos por ahora; documentar extensibilidad |
| HTML injection en `html` component | Alto | Usar `mark_safe()` solo para contenido admin-confiable; sanitizar entrada |
>| Performance: N+1 queries al renderizar | Medio | Cache por página (5 min); prefetch related si hay FK |
| URL conflicts con otras apps | Bajo | Namespace `pages/` exclusivo; verificar `urls.py` raíz |

---

## 📈 Metrics (Post-MVP)

- Páginas creadas (admin)
- Páginas published vs draft
- Visitas a páginas públicas (Analytics futuro)
- Tiempo promedio de creación (admin UX)

---

**Status:** 📋 PLANNED | **Phase:** 0.6.2 | **Owner:** PAUL
**Next:** Implementar 0.6.2.1 → serializers + validación schema
