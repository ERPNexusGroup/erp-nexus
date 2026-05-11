# ERP Nexus — Roadmap (PAUL)

**Version:** 1.0.0-alpha
**Last Updated:** 2026-05-12

---

## 🎯 Milestones

### **M0 — Core Foundation** ✅ COMPLETED
**Target:** Semana 1
**Status:** ✅ Done (2026-05-10)

**Deliverables:**
- [x] 11 core Django apps (framework)
- [x] Multi-tenant middleware
- [x] Settings base (dev + prod)
- [x] Docker stack (PostgreSQL + Redis)
- [x] Project documentation (15+ docs)

---

### **M1 — Hybrid Restructure — Essential Modules** ✅ COMPLETED
**Target:** Semana 2
**Status:** ✅ Done (2026-05-10)

**Objective:** Integrar módulos esenciales en core (no plugins).

**Phases (9 tasks):**

| Phase | Descripción | Estado |
|-------|-------------|--------|
| 0.6.1 | Definir arquitectura híbrida | ✅ |
| 0.6.2 | Mover `facturacion_ec/` → `apps/facturacion/` | ✅ |
| 0.6.3 | Eliminar módulos demo | ✅ |
| 0.6.4 | Clean core settings | ✅ |
| 0.6.5 | Crear `apps/inventory/` | ✅ |
| 0.6.6 | Crear sales, purchases, notifications, print_manager | ✅ |
| 0.6.7 | Update documentation | ✅ |
| 0.6.8 | Rebuild graph + finalize state | ✅ |
| 0.6.9 | Validation | ✅ |

**Outcome:** ERP Nexus funcional out-of-the-box con 6 business modules.

**Total:** 17 Django apps (11 core + 6 essential)

---

### **M2 — Marketplace & Plugin System** ✅ COMPLETED
**Target:** Semana 4-5
**Status:** ✅ Done (2026-05-11)

**Objective:** Sistema de marketplace funcional para instalar módulos.

#### Phase 1.1 — Marketplace Foundation — ✅ DONE
Catalog, install/uninstall, API, Admin UI básico.

#### Phase 1.2 — License Management + Jazzmin UI — ✅ DONE (2026-05-11)

**Deliverables:**
- [x] `ModuleLicense` model (seat tracking, expiry, types: free/trial/paid/perpetual)
- [x] License validation in `module_install` (reject invalid/expired/over-seat)
- [x] REST API (4 endpoints: POST create, GET list, GET validate, DELETE revoke)
- [x] Public catalog page (`/marketplace/`) con filtros, badges, precios, botón staff
- [x] Admin UI mejorado: seat usage bar, status badges, actions (generate key, revoke, install, uninstall)
- [x] **Sidebar dinámico ERPNext-style**: sección "Marketplace — Aplicaciones" agrupada por `admin_menu_category`
- [x] **Dashboard integrado**: tarjetas métricas (installed, licenses active/expiring/expired) + últimos 5 instalados
- [x] **Cache invalidation automática**: `module_install`/`module_uninstall` eliminan cache → modules aparecen inmediatamente
- [x] 17 E2E tests passing (catalog, install flow, license flow, public page)
- [x] Campo `admin_menu_category` en `ModuleCatalogItem` (default: 'Aplicaciones')
- [x] Context processor `admin_metrics` con `jazzmin_apps` + `dashboard_cards` (cached 5/10 min)

**Applied doc:** `.paul/phases/01-marketplace/01-02-MARKETPLACE-UI-LICENSE-APPLIED.md`

**Files changed (18+):**
- `apps/core_marketplace/models.py` (+ ModuleLicense, +admin_menu_category)
- `apps/core_marketplace/admin.py` (Jazzmin enhancements, actions, sync button)
- `apps/core_marketplace/views.py` + `templates/core_marketplace/catalog_public.html`
- `apps/core_marketplace/management/commands/refresh_catalog.py` (nuevo)
- `apps/core_marketplace/management/commands/module_install.py` (+ cache invalidation)
- `apps/core_marketplace/management/commands/module_uninstall.py` (+ cache invalidation)
- `apps/core_marketplace/migrations/0002_add_description_field.py`, `0003_add_admin_menu_category.py`
- `apps/core_dashboard/context_processors.py` (jazzmin_apps + dashboard_cards + cache helpers)
- `apps/core_dashboard/templates/admin/base.html` (sidebar override completo)
- `apps/core_dashboard/templates/admin/base_site.html` (site base)
- `apps/core_dashboard/templates/admin/index.html` (dashboard sections)
- `apps/core_dashboard/static/core_dashboard/dashboard.css` (metric card styles)
- `apps/core_api/v1/marketplace.py` (4 API endpoints)
- `erp_nexus/settings.py` (JAZZMIN_SETTINGS side_menu updates)
- `apps/core_marketplace/tests/conftest.py` (mock + cache invalidation)
- `apps/core_marketplace/tests/test_marketplace_license.py` (+3 public tests → total 15)

**Tests:** 15 → 19 passing

#### Phase 1.3 — GitHub auto-discovery + sync — ✅ DONE (2026-05-12)

**Deliverables:**
- [x] `refresh_catalog` command: escanea GitHub org (topic `erp-nexus-module` + `__meta__.py`), upsert catalog
- [x] Admin: botón "Sync" por registry + acción Jazzmin "Sync selected"
- [x] Auto-creación de `ModuleRegistry` default ("GitHub Official") si no existe:
  - Señal `apps.py` `ready()` → crea al iniciar Django
  - Lógica en `refresh_catalog` → crea en primer run si no hay registros activos
- [x] `parse_meta_file` utility (AST parser seguro para `__meta__.py`)
- [x] GITHUB_TOKEN + GITHUB_ORG settings (rate-limit awareness)
- [x] Fix: `settings.timezone.now()` → `timezone.now()` en refresh
- [x] 2 tests nuevos: default registry creation + dry-run behavior
- [x] Mock `call_command` mejorado: `refresh_catalog` ejecuta real sin recursion

**Files changed (7):** admin.py, apps.py, refresh_catalog.py, module_loader.py,
conftest.py, test_marketplace_license.py, settings.py

**Tests:** +2 → **19 passing**

#### Phase 1.4 — Version management + dependencies solver — 📋 PLAN

**Success:** Admin puede instalar módulos desde GitHub con un click; aparecen inmediatamente en dashboard y menú.

---

### **M3 — Production Ready** 📋 PLANNED
**Target:** Semana 6-7
**Status:** ⬜ Planned

**Objective:** Despliegue en producción.

**Phases:**
- **Phase 2.1** — Docker production image (multi-stage build)
- **Phase 2.2** — PostgreSQL + Redis (production config)
- **Phase 2.3** — Celery workers (async notifications, SRI auto-send)
- **Phase 2.4** — SSL + Nginx reverse proxy
- **Phase 2.5** — Monitoring (Prometheus + Grafana + Sentry)

**Success:** `docker compose up -d` levanta ERP completo en producción.

---

### **M4 — Advanced Features** 📋 Planned
**Target:** Semana 8-10
**Status:** ⬜ Planned

**Objective:** Features avanzadas.

**Phases:**
- **Phase 3.1** — GraphQL API (para frontend complejo)
- **Phase 3.2** — Mobile app API optimizada
- **Phase 3.3** — Multi-company enhancements
- **Phase 3.4** — Reporting engine (PDF reports, Excel export)

**Success:** ERP con API moderna y reporting avanzado.

---

## 📊 Current Sprint

**Sprint:** M2 (Marketplace License Management 1.2) — ✅ COMPLETADO (2026-05-11)

**Next Sprint:** M2 Phase 1.3 — GitHub Auto-discovery + Sync

**Phase 1.2 Deliverables:** 18+ archivos modificados, **17 tests passing**, sidebar + dashboard integrados con cache invalidation instantánea.

**Documentación:** Reorganización completa — `.architecture/` con 17 archivos técnicos + `READM`e índices para desarrolladores.

---

## 🔮 Future Vision (M5+)

- **M5 — AI Integration:** OCR para facturas, predictive inventory
- **M6 — E-commerce Sync:** WooCommerce/Shopify connectors
- **M7 — Accounting:** Integration with local accounting software (Ecuador)
- **M8 — POS Module:** Point of Sale for retail

---

**Last milestone completion:** M0, M1, M2-1.1, M2-1.2, M2-1.3 ✅
**Current milestone:** M2 Phase 1.4 — IN PROGRESS
**Estimated velocity:** 2-3 phases/semana
