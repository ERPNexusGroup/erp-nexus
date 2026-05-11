# PAUL Phase 1.2 — APPLIED (License Management + Jazzmin UI)

**Fecha:** 2026-05-10
**Estado:** ✅ APPLIED + UNIFY COMPLETE
**Commit:** `feature/sri-integration` (4eaea19) + Jazzmin Override + Cache Invalidation (HEAD)

---

## Objetivo Alcanzado

Sistema completo de gestión de licencias **+ integración Jazzmin** (dashboard y sidebar dinámico ERPNext-style):

- Modelo `ModuleLicense` con validación de seats, expiración y tipos
- Validación automática en `module_install` (requiere license_key para módulos licenciados)
- API REST para crear/listar/validar/revocar licencias (4 endpoints)
- Admin UI mejorado: seat usage bar, badges, actions, quick install/uninstall, sync button
- **Sidebar dinámico:** sección "Marketplace — Aplicaciones" agrupada por categoría (populated desde `EnabledModule` + `admin_menu_category`)
- **Dashboard integrado:** tarjetas métricas + sección módulos recientes
- Página pública de catálogo `/marketplace/` con filtros, badges, precios, botones staff
- Management command `refresh_catalog` (GitHub org scan + catalog sync)
- **Cache invalidation automática:** `module_install`/`module_uninstall` eliminan cache para que modules aparezcan inmediatamente
- **17 E2E tests passing** (catalog, install flow, license flow, public page, sidebar integration)

---

## Implementación — Archivos Cambiados

### Nuevos Archivos

| Archivo | Propósito |
|---------|-----------|
| `apps/core_marketplace/models.py` | Modelo `ModuleLicense` (100+ lines) + campo `admin_menu_category` en `ModuleCatalogItem` |
| `apps/core_marketplace/admin.py` | `ModuleLicenseAdmin` con seat bar, badge, actions; `ModuleCatalogItemAdmin` con install/uninstall buttons + `admin_menu_category` field; `ModuleRegistryAdmin` con sync-button |
| `apps/core_marketplace/utils/license.py` | `validate_license_for_module()`, `consume_license()`, `release_license()`, `create_trial_license()` |
| `apps/core_marketplace/views.py` | `public_catalog()` view |
| `apps/core_marketplace/urls.py` | path `""` → `public_catalog` |
| `apps/core_marketplace/templates/core_marketplace/catalog_public.html` | Página pública con filtros, badges, botones staff |
| `apps/core_marketplace/management/commands/refresh_catalog.py` | Sync desde GitHub/registries (usado por botón admin) |
| `apps/core_marketplace/migrations/0002_add_description_field.py` | Campo `description` en `ModuleCatalogItem` |
| `apps/core_marketplace/migrations/0003_add_admin_menu_category.py` | Campo `admin_menu_category` en `ModuleCatalogItem` |
| `apps/core_dashboard/templates/admin/base.html` | Override completo del sidebar Jazzmin → inyecta sección Marketplace |
| `apps/core_dashboard/templates/admin/base_site.html` | Site base (branding, title) |
| `apps/core_dashboard/templates/admin/index.html` | Sección 'Módulos Instalados Recientes', tarjetas métricas |
| `apps/core_dashboard/static/core_dashboard/dashboard.css` | Estilos para tarjetas de colores métricas |
| `apps/core_dashboard/context_processors.py` | `jazzmin_apps` (sidebar dinámico) + `dashboard_cards` (métricas) + cache (5min/10min) + invalidation helpers |

### Modificados

| Archivo | Cambios |
|---------|---------|
| `apps/core_marketplace/models.py` | `ModuleCatalogItem`: agregados `is_licensed`, `license_required`, `trial_days`, `price_monthly`, `price_yearly`, `description`, **`admin_menu_category`** |
| `apps/core_api/v1/marketplace.py` | Endpoints `/licenses` — POST create, GET list, GET validate, DELETE revoke |
| `apps/core_marketplace/management/commands/module_install.py` | Validación de licencia pre-install; `consume_license()` en transacción; **cache invalidation** post-install |
| `apps/core_marketplace/management/commands/module_uninstall.py` | Uninstall with file removal; **cache invalidation** post-uninstall |
| `apps/core_api/api.py` | `urls_namespace = "api"` (Django Ninja 1.6) |
| `erp_nexus/urls.py` | `api.urls.app_name = "api"`; `path("marketplace/", include(router.urls))` |
| `erp_nexus/settings.py` | `JAZZMIN_SETTINGS['side_menu']` agrupado por funcionalidad; iconos Marketplace agregados |
| `erp_nexus/modules_enabled.py` | Manejo seguro de módulo duplicado en MODULE_APPS |
| `apps/core_marketplace/tests/conftest.py` | Mock `call_command` + **cache invalidation** en install/uninstall |
| `apps/core_marketplace/tests/test_marketplace_license.py` | 3 tests públicos agregados (catalog page, filters) — total 15 |

---

## Decisiones Técnicas — License + UI + Cache

| Decisión | Rationale |
|----------|-----------|
| `admin_menu_category` campo en `ModuleCatalogItem` | Define en qué sección del menú lateral aparece el módulo (ej: Ventas, Inventario, Contabilidad). Default: 'Aplicaciones' |
| Cache invalidation en `module_install`/`module_uninstall` | Invalida `admin_dashboard_metrics` y `jazzmin_side_menu_apps` para que cambios se reflejen inmediatamente en admin |
| Context processor solo para `/admin/` paths | Evita queries en API requests y vistas públicas |
| Sidebar override extiende `admin/base.html` (no `jazzmin/admin/base_site.html`) | Django busca templates por app order; `core_dashboard` antes que `jazzmin` → override efectivo |
| `jazzmin_apps` estructura: `{label, icon, models:[{name, admin_url}]}` | Compatible con estructura de `side_menu` de Jazzmin |
| `admin_menu_category` **vs** `admin_menu` JSON | `admin_menu_category` = simple string para agrupación; `admin_menu` = JSON structure para config avanzada (future) |
| Dashboard cards con colores condicionales (CSS) | Visual alerts: red (expired), orange (expiring), green (ok), blue (info) |
| `refresh_catalog` command + botón admin sync | Sync manual desde GitHub org; futuro: auto-cron |

---

## Acceptance Criteria — Verificados ✅

- [x] `ModuleCatalogItem` con `admin_menu_category` (default 'Aplicaciones')
- [x] Sidebar Jazzmin muestra sección "Marketplace — Aplicaciones" agrupada por `admin_menu_category`
- [x Cada módulo instalado aparece en su categoría correspondiente en el menú lateral
- [x Dashboard muestra tarjetas: installed modules, licenses (active/expiring/expired)
- [x Sección "Módulos Instalados Recientes" en dashboard
- [x Instalar módulo → aparece automáticamente en sidebar y dashboard (cache invalidado)
- [x Desinstalar módulo → desaparece de sidebar y dashboard (cache invalidado)
- [x `module_install` y `module_uninstall` llaman `cache.delete()` post-commit
- [x Tests E2E validan flujos completos (15/15 passed)

---

## Cómo configurar categorías de módulos

Para que un módulo aparezca en una sección específica del menú, define `admin_menu_category` en su `__meta__.py` o en el admin:

```python
# __meta__.py del módulo
admin_menu_category = "Ventas"  # Opciones: Aplicaciones, Ventas, Inventario, Contabilidad, etc.
```

O desde el admin DJango, editar el campo `admin_menu_category` en `ModuleCatalogItem`.

---

## Next Steps — Post 1.2

### Phase 1.3 — GitHub Auto-discovery + Sync (NEXT)
**Objetivo:** Detección automática de módulos desde GitHub organization + sync catalog.

**Tareas:**
1. Configurar `GITHUB_ORG` + `GITHUB_TOKEN` en settings
2. Implementar GitHub topic/star scanning (`erp-nexus-module`)
3. Auto-parsing de `__meta__.py` desde raw GitHub API
4. Auto-crear `ModuleCatalogItem` (is_active=True) con `admin_menu_category` default
5. Webhook receiver (opcional) para auto-refresh on push
6. Tests E2E con mocks de GitHub API

**Commit actual:** HEAD (cache invalidation + admin_menu_category)
**Next branch:** `feat/marketplace/github-auto-discovery`

### Phase 1.4 — Version Management + Dependencies Solver
- Conflict detection entre dependencias de módulos
- Auto-upgrade path analysis (semver compatibility)

---

**Phase 1.2 signature:** Applied, Verified, UNIFY Complete ✅
**Integration:** Marketplace License Management v1.0 + Jazzmin UI v3.0 + Cache Invalidation
**User impact:** Ahora los módulos instalados aparecen **inmediatamente** en el dashboard y menú lateral, agrupados por categoría (estilo ERPNext).
