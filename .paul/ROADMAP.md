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
**Status:** ✅ Done (2026-05-12)

**Objective:** Sistema de marketplace completo para instalar módulos.

#### Phase 1.1 — Marketplace Foundation — ✅ DONE (2026-05-10)
Catalog, install/uninstall, API, Admin UI básico.

#### Phase 1.2 — License Management + Jazzmin UI — ✅ DONE (2026-05-11)
- [x] ModuleLicense model (seats, expiry, types)
- [x] License validation en module_install
- [x] REST API (4 endpoints)
- [x] Public catalog page `/marketplace/`
- [x] Admin UI mejorado (seat bar, badges, actions)
- [x] Sidebar dinámico ERPNext-style
- [x] Dashboard integrado con métricas
- [x] Cache invalidation automática
- [x] 17→19 E2E tests passing

**Applied doc:** `.paul/phases/01-marketplace/01-02-MARKETPLACE-UI-LICENSE-APPLIED.md`

#### Phase 1.3 — GitHub auto-discovery + sync — ✅ DONE (2026-05-12)
- [x] `refresh_catalog` command: escanea GitHub org, upsert catalog
- [x] Admin: botón "Sync" por registry + acción Jazzmin
- [x] Auto-creación de `ModuleRegistry` default ("GitHub Official")
- [x] `parse_meta_file` utility (AST parser seguro)
- [x] GITHUB_TOKEN + GITHUB_ORG settings
- [x] Fix: timezone.now() en refresh
- [x] 2 tests nuevos (default registry + dry-run)
- [x] Mock mejorado: `refresh_catalog` ejecuta real sin recursion

**Files changed:** admin.py, apps.py, refresh_catalog.py, module_loader.py, conftest.py, test_marketplace_license.py, settings.py
**Tests:** +2 → **19 passing**

#### Phase 1.4 — Version Management + Dependencies Solver — 🔄 IN PROGRESS (2026-05-12)

**Objective:** Gestión robusta de versiones y resolución de dependencias entre módulos.

**Tasks (10):**
1. `ModuleVersionConstraint` model — rangos de versiones compatibles (semver)
2. `ModuleDependency` model — dependencias entre módulos (required, optional, conflict)
3. Semver parser + compatibility checker
4. Dependency resolver algorithm (topological sort + conflict detection)
5. Conflict detection UI en Admin (pre-flight warnings)
6. Auto-dependency installation (--with-deps flag)
7. Upgrade path analysis (backward compatibility checks)
8. Tests E2E (conflicts, circular deps, version mismatches)
9. Cache invalidation + admin integration
10. Documentation (DEPENDENCIES.md, upgrade guide)

**Estimated:** ~20h
**Commit branch:** `feat/marketplace/version-deps-solver`
**Current task:** 1.4.1 — ModuleVersionConstraint model

**Success:** Admin puede instalar módulos con dependencias resueltas automáticamente; conflictos detectados antes de install.

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

**Sprint:** M2 Phase 1.4 — Version Management + Dependencies Solver (IN PROGRESS — Task 1.4.1)

**Last Sprint:** M2 Phase 1.3 — GitHub Auto-discovery + Sync — ✅ COMPLETADO (2026-05-12)

**Phase 1.3 Deliverables:** 7 archivos modificados, GitHub auto-discovery funcional, `refresh_catalog` command, sync button admin, default registry auto-creation, 19 E2E tests passing.

---

## 🔮 Future Vision (M5+)

- **M5 — AI Integration:** OCR para facturas, predictive inventory
- **M6 — E-commerce Sync:** WooCommerce/Shopify connectors
- **M7 — Accounting:** Integration with local accounting software (Ecuador)
- **M8 — POS Module:** Point of Sale for retail

---

**Last milestone completion:** M0, M1, M2-1.1, M2-1.2, M2-1.3 ✅
**Current milestone:** M2 Phase 1.4 — APPLY IN PROGRESS (Task 1.4.1)
**Estimated velocity:** 2-3 phases/semana
