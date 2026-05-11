# PAUL State — ERP Nexus Core (Hybrid Architecture)

**Project:** ERP Nexus Core (Framework + Essential Modules)
**Architecture:** Hybrid — Essential modules in core, Optional modules as plugins
**Current Phase:** 1.4 — Version Management + Dependencies Solver (PLAN)
**Loop Position:** PLAN → READY FOR APPLY
**Last Completed:** Phase 0.6 — Hybrid Restructure (2026-05-10) ✅
**Last Completed:** Phase 1.1 — Marketplace Foundation (2026-05-10) ✅
**Last Completed:** Phase 1.2 — Marketplace UI Polish + License Management (2026-05-11) ✅
**Last Completed:** Phase 1.3 — GitHub Auto-discovery + Sync (2026-05-12) ✅
**Next Milestone:** M2 Phase 1.4 — Version Management + Dependencies Solver

---

## ✅ Phase 0.6 — Hybrid Restructure (COMPLETED)

**Status:** ✅ ALL 9 TASKS DONE

| Task | Descripción | Estado |
|------|-------------|--------|
| 0.6.1 | Definir arquitectura híbrida | ✅ |
| 0.6.2 | Mover `facturacion_ec/` → `apps/facturacion/` | ✅ |
| 0.6.3 | Eliminar módulos demo | ✅ |
| 0.6.4 | Clean core settings | ✅ |
| 0.6.5 | Crear `apps/inventory/` | ✅ |
| 0.6.6 | Crear sales, purchases, notifications, print_manager | ✅ |
| 0.6.7 | Update documentation | ✅ |
| 0.6.8 | Rebuild graph + finalize state | ✅ |
| 0.6.9 | Validation | ✅ |

**Result:** 17 Django apps (11 core + 6 essential). ERP funcional out-of-the-box.

---

## ✅ Phase 1.1 — Marketplace Foundation (APPLIED — COMPLETE)

**Status:** ✅ ALL 7 TASKS DONE

### Tasks

| Task | Descripción | Estado |
|------|-------------|--------|
| 1.1.1 | Extender ModuleCatalogItem metadata | ✅ |
| 1.1.2 | Auto-Discover GitHub Organization (scan_github_org) | ✅ |
| 1.1.3 | Install/Uninstall management commands | ✅ |
| 1.1.4 | Dynamic App Loading (modules_enabled.py watcher) | ✅ |
| 1.1.5 | Admin UI — Marketplace tab | ✅ |
| 1.1.6 | API Endpoints (catalog, install, uninstall, installed) | ✅ |
| 1.1.7 | Validation & Security | ✅ |

**Total:** ~9h — COMPLETADO
**Commit:** `feat(1.1): marketplace foundation — phase complete` (1229197)

---

## 🔹 Phase 1.2 — Marketplace UI Polish + License Management (APPLIED — COMPLETE)

**Fecha:** 2026-05-11
**Estado:** ✅ APPLIED + UNIFY COMPLETE
**Commit:** `feat(marketplace): Phase 1.2 — License Management + Jazzmin UI Integration` (cbbc240)

**Objetivo:** Interfaz de catálogo rica + gestión de licencias.

**Entregables (9 tasks):**
- [x] `ModuleLicense` model (seats, expiry, types: free/trial/paid/perpetual)
- [x] License validation en `module_install` (consume/release en transacción)
- [x] REST API licencias (4 endpoints: POST create, GET list, GET validate, DELETE revoke)
- [x] Public catalog page `/marketplace/` con filtros, badges, precios, botón staff
- [x] Admin UI mejorado: seat usage bar, status badges, actions (generate key, revoke, install, uninstall)
- [x] Sidebar dinámico ERPNext-style agrupado por `admin_menu_category`
- [x] Dashboard integrado: tarjetas métricas + últimos 5 instalados
- [x] Cache invalidation automática post install/uninstall
- [x] 17 E2E tests passing

**Tests:** 15 → 17 passing (+2)
**Referencia:** `.paul/phases/01-marketplace/01-02-MARKETPLACE-UI-LICENSE-APPLIED.md`

---

## ✅ Phase 1.3 — GitHub Auto-discovery + Sync (APPLIED — COMPLETE)

**Fecha:** 2026-05-12
**Estado:** ✅ APPLIED + UNIFY COMPLETE
**Commit:** `feat(marketplace): GitHub auto-discovery + admin UI polish + default registry` (2f5977d)

**Objetivo:** Detección automática de módulos desde GitHub + sincronización de catálogo.

**Entregables:**
- [x] `refresh_catalog` command — escanea GitHub org (topic `erp-nexus-module` + `__meta__.py`), upsert catalog
- [x] Admin: botón "Sync" por registry + acción Jazzmin "Sync selected"
- [x] Auto-creación de `ModuleRegistry` default ("GitHub Official") — señal `apps.py` `ready()` + lógica en `refresh_catalog`
- [x] `parse_meta_file` utility (AST parser seguro para `__meta__.py`)
- [x] Settings: `GITHUB_TOKEN` + `GITHUB_ORG` (rate-limit awareness)
- [x] Fix: `settings.timezone.now()` → `timezone.now()` en refresh
- [x] 2 tests nuevos: default registry creation + dry-run behavior
- [x] Mock `call_command` mejorado: `refresh_catalog` ejecuta real sin recursion

**Tests:** +2 → **19 passing** (total marketplace suite)
**Referencia:** `.paul/phases/01-marketplace/01-03-GITHUB-DISCOVERY.md`

---

## 📊 Code Stats Cumulative (Phases 0.6 + 1.1 + 1.2 + 1.3)

**New files cumulative:** ~28
- 4 management commands (scan_github_org, module_install, module_uninstall, refresh_catalog)
- 4 utils (module_loader.py, github.py, license.py, parse helpers)
- 6+ migrations (core_marketplace, core_dashboard)
- Admin/API/views/templates/static extensions
- Context processors + cache helpers

**Updated files:** ~25
- `apps/core_marketplace/`: models, admin, apps, views, urls, tests
- `apps/core_dashboard/`: context_processors.py, templates/*, static/*
- `apps/core_api/v1/marketplace.py` — license endpoints
- `erp_nexus/`: settings.py, urls.py, modules_enabled.py
- Documentation reorganization (`.architecture/`, `docs/`)

**Total code churn:** ~35k lines added/modified across all completed phases

**Quality Metrics:**
- ✅ `manage.py check` — 0 issues
- ✅ `makemigrations --check` — no pending migrations
- ✅ `manage.py migrate` — all applied cleanly
- ✅ Django server starts without errors
- ✅ **19 E2E tests passing** (marketplace catalog, install/uninstall, license flow, public page, GitHub sync, sidebar integration)

---

## 🔗 Dependencies Resolved

✅ Phase 0.6 — Baseline hybrid architecture (17 Django apps)
✅ Phase 1.1 — Marketplace foundation (catalog, install/uninstall, dynamic loading)
✅ Phase 1.2 — License management + Jazzmin UI polish (dashboard, sidebar, cache invalidation)
✅ Phase 1.3 — GitHub auto-discovery + registry sync

---

## 🎯 Acceptance Criteria — All Phases Verified

### Phase 1.1 ✅
- [x] ModuleCatalogItem extendido con metadata completa
- [x] scan_github_org command implementado
- [x] module_install / module_uninstall commands funcionan
- [x] modules_enabled.py dinámico + watcher
- [x] Admin UI con Marketplace tab y botones de acción
- [x] API endpoints funcionan (JWTAuth protected)
- [x] __meta__.py validation implementada
- [x] All migrations applied, no pending changes
- [x] Django check passes, server starts cleanly

### Phase 1.2 ✅
- [x] `ModuleLicense` model con seat tracking, expiry, types
- [x] License validation en `module_install`
- [x] REST API 4 endpoints licencias
- [x] Public catalog page `/marketplace/`
- [x] Admin UI mejorado: seat bar, badges, actions
- [x] Sidebar dinámico ERPNext-style
- [x] Dashboard integrado con métricas
- [x] Cache invalidation automática
- [x] 17 E2E tests passing

### Phase 1.3 ✅
- [x] `ModuleRegistry` funciona con `source_type='github'`
- [x] Command `refresh_catalog` escanea org y upsert catalog
- [x] Filtrado por `__meta__.py` y topic `erp-nexus-module`
- [x] Repos sin metadata se omiten (log warning)
- [x] Auto-creación de registry default
- [x] Admin: botón "Sync Now" en `ModuleRegistryAdmin`
- [x] Tests: 2 E2E con mocks GitHub API (total 19)

---

## 📋 Next Phase — Phase 1.4 — Version Management + Dependencies Solver (PLAN)

**Objetivo:** Gestión robusta de versiones y resolución de dependencias entre módulos.

**Estado:** 📋 PLAN — Esperando APPLY

### Tasks Phase 1.4

| Task | Descripción | Estimado |
|------|-------------|----------|
| 1.4.1 | `ModuleVersionConstraint` model — rango de versiones compatibles (semver) | 2h |
| 1.4.2 | `ModuleDependency` model — dependencias entre módulos (required, optional, conflicts) | 2h |
| 1.4.3 | Semver parser + compatibility checker — `is_compatible(module_version, constraint)` | 2h |
| 1.4.4 | Dependency resolver algorithm — topological sort + conflict detection | 3h |
| 1.4.5 | Conflict detection UI en Admin — warnings pre-install, auto-suggest resolutions | 2h |
| 1.4.6 | Auto-dependency installation — instalar dependencias requeridas automáticamente | 2h |
| 1.4.7 | Upgrade path analysis — determinar si actualización es segura (backward compatible) | 2h |
| 1.4.8 | Tests E2E — conflict scenarios, circular deps, version mismatches | 3h |
| 1.4.9 | Cache + admin integration — invalidate metadata post-install/upgrade | 1h |
| 1.4.10 | Documentation — DEPENDENCIES.md, upgrade guide | 1h |

**Total estimado:** ~20h

### Deliverables

1. **Models:**
   ```python
   class ModuleVersionConstraint(models.Model):
       module = ForeignKey(ModuleCatalogItem)
       min_version = CharField()  # semver
       max_version = CharField()  # semver (exclusive)
       operator = CharField()  # '=', '~', '^', '>', '>=', '<', '<='

   class ModuleDependency(models.Model):
       module = ForeignKey(ModuleCatalogItem, related_name='dependencies')
       depends_on = ForeignKey(ModuleCatalogItem, related_name='dependents')
       required = BooleanField()  # True = hard requirement, False = optional
       conflict = BooleanField()  # True = cannot coexist
   ```

2. **Commands:**
   - `check_dependencies <module_name>` — muestra árbol de dependencias
   - `resolve_dependencies <module_name>` — calcula install order + conflicts
   - `validate_version_compatibility <module> <version>` — check contra installed

3. **Admin UI:**
   - `ModuleCatalogItemAdmin`: sección "Dependencies" + "Version Constraints"
   - `module_install` view: pre-flight check, muestra conflictos, sugiere soluciones
   - Dashboard: dependencia graph visualization (simple Mermaid)

4. **API Extensions:**
   - `GET /api/v1/marketplace/dependencies/{module}` — devuelve dependency tree
   - `POST /api/v1/marketplace/validate-install/{module}` — pre-flight validation

**Success criteria:**
- [ ] `module_install` rechaza instalación si dependencias no satisfechas (con mensaje claro)
- [ ] `module_install` auto-instala dependencias opcionales (flag `--with-deps`)
- [ ] Admin muestra warnings de conflictos antes de install
- [ ] Upgrade path analysis evita breaking changes
- [ ] 5+ tests E2E cubriendo conflictos, ciclos, versiones

**Commit branch:** `feat/marketplace/version-deps-solver`

---

**Estado fases completadas:**
- ✅ Phase 0.6: Hybrid Restructure (2026-05-10)
- ✅ Phase 1.1: Marketplace Foundation (2026-05-10)
- ✅ Phase 1.2: License Management + UI Polish (2026-05-11)
- ✅ Phase 1.3: GitHub Auto-discovery + Sync (2026-05-12)
- 🔄 Phase 1.4: Version Management + Dependencies Solver — SIGUIENTE
