# ERP Nexus — PAUL Project Context

**Why this project exists:**
ERP Nexus es un ERP modular hybrid para empresas ecuatorianas: core integrado (facturación, inventario, ventas, compras) + plugins opcionales (HR, CRM, etc.). Instalación única, funcionalidad completa out-of-the-box.

**What problem it solves:**
- ERP tradicional = monolito (todo o nada)
- Modular plugin-only = fricción (instalar 6 plugins para ERP funcional)
- Actualizaciones = deploy completo (riesgoso)

**ERP Nexus solution (Hybrid Architecture):**
- Core mínimo (11 framework apps)
- Essential modules integrados (6 business apps) — siempre presentes
- Optional plugins instalables via Marketplace (hr, crm, …)
- Actualizaciones granulares por módulo

---

## 🎯 Project Value

**Para empresas:**
- Instalación única → ERP funcional en 5 min
- Paga/usa solo módulos opcionales extra
- Implementación incremental

**Para desarrolladores:**
- Framework estructurado para módulos
- Marketplace para publicar
- Standards claros (CODING_STANDARDS, MODULE_SPEC)
- Tests + CI/CD

**Para el mercado:**
- Open source (MIT)
- Enfoque Ecuador (SRI nativo)
- Expandible a Latinoamérica

---

## 🎯 Success Criteria

**v0.6 (Hybrid Restructure) — COMPLETED ✅**
- ✅ Core estable (11 framework apps)
- ✅ 6 essential modules integrados
- ✅ Architecture híbrida validada
- ✅ Documentación completa
- ✅ Tests básicos por módulo

**v1.1 (Marketplace Foundation) — COMPLETED ✅**
- ✅ Marketplace con catálogo y metadata extendida
- ✅ Comandos CLI: module_install / module_uninstall
- ✅ Admin UI con botones de instalar/desinstalar
- ✅ API REST (catalog, install, uninstall, installed)
- ✅ modules_enabled.py dinámico + watcher
- ✅ Validación básica de __meta__.py

**v1.0.0 (12 semanas):**
- ✅ Marketplace funcional completo
- ✅ Módulo HR oficial (primer plugin)
- ✅ Docker + PostgreSQL + Redis production-ready
- ✅ 80% test coverage core + essential

**v2.0 (Año 2):**
- 100+ empresas usando ERP Nexus
- 10+ módulos oficiales
- Marketplace community con 20+ módulos
- Frontend React SPA

---

## 🏗️ Current State (2026-05-10)

### **Architecture: Hybrid Model**

```
Tier 1 — Core Framework (11 apps)
  core_users, core_companies, core_events, core_api, core_marketplace,
  core_permissions, core_audit, core_stats, core_config, core_dashboard,
  core_pagebuilder

Tier 2 — Essential Business (6 apps) — integrated
  facturacion, inventory, sales, purchases, notifications, print_manager

Tier 3 — Optional Plugins (futuro) — via Marketplace
  hr, crm, accounting_adv, project_mgmt, pos, ecommerce
```

### **Completed Milestones**

| Milestone | Fecha | Estado |
|-----------|-------|--------|
| M0 — Core Foundation | 2026-05-10 | ✅ |
| M1 — Hybrid Restructure (0.6) | 2026-05-10 | ✅ |
| M2-1.1 — Marketplace Foundation | 2026-05-10 | ✅ |

### **Next Milestone**

**M2 Phase 1.2 — Marketplace UI + License Management**
- Inicio: 2026-05-10
- Estimación: 1-2 semanas
- Objetivo: Interfaz de catálogo más rica + gestión de licencias

---

## 📊 Phase 0.6 — Lo que construimos

**17 Django apps** en `apps/`:
- 11 core framework (siempre cargados)
- 6 essential business (integrados, no plugins)

**6 Essential Modules:**
1. `facturacion` — Facturación SRI Ecuador (XML, firma digital, envío)
2. `inventory` — Gestión de stock (productos, categorías, movimientos)
3. `sales` — Cotizaciones + Órdenes + integración facturación
4. `purchases` — Órdenes de compra + proveedores + recepción
5. `notifications` — Email + Telegram + cola asincrónica
6. `print_manager` — Generación PDFs (template-based)

**Documentación:**
- INSTALL.md (5-min install)
- API_REFERENCE.md (6 módulos)
- MODULE_SPEC.md
- ARCHITECTURE_HYBRID.md
- ADR/007, ADR/008 (comunicación channels)

---

## 🔄 Phase 1.1 — Marketplace Foundation (COMPLETED)

**Objetivo:** Sistema de Marketplace para plugins opcionales.

**Entregables:**

| Task | Descripción | Estado |
|------|-------------|--------|
| 1.1.1 | Extender ModuleCatalogItem (metadata) | ✅ |
| 1.1.2 | Auto-Discover GitHub Org (scan_github_org) | ✅ |
| 1.1.3 | Install/Uninstall commands | ✅ |
| 1.1.4 | Dynamic App Loading (watcher) | ✅ |
| 1.1.5 | Admin UI (Marketplace tab) | ✅ |
| 1.1.6 | API Endpoints | ✅ |
| 1.1.7 | Validation & Security | ✅ (basic) |

**Result:**
- Admin puede instalar `hr` desde GitHub (cuando repo exista)
- Validación de `__meta__.py` (AST-safe)
- modules_enabled.py gestionado dinámicamente
- 4 management commands: `scan_github_org`, `module_install`, `module_uninstall`, `refresh_catalog`
- 5 REST endpoints (catalog, install, uninstall, installed, status)

---

## 📈 Metrics

**Code Stats (Phase 0.6 + 1.1):**
- New modules: 6 essential + 4 marketplace models
- New management commands: 3
- New API endpoints: 5 (marketplace)
- Total apps: 17 + 1 core_marketplace
- Commits: 20+ (Phases 0.6 + 1.1)
- Files changed: ~150

**Quality:**
- Django check: ✅ OK
- Migrations apply: ✅ OK (2 migrations core_marketplace)
- Server starts: ✅ OK
- No lint errors (pending)

---

## 🎯 Decisiones Arquitectónicas

| Decisión | Opción | Elegido | Razón |
|----------|--------|---------|-------|
| Essential modules position | Separate repo vs apps/ | ✅ `apps/` | ERP funcional sin fricción |
| Marketplace command | Management vs web UI first | ✅ CLI first | Automatización + API después |
| modules_enabled.py | DB storage vs file | ✅ File | Simplicidad, Django standard |
| Validation approach | Schema library vs AST | ✅ AST safe | Sin dependencias externas |
| API authentication | Session vs Token | ✅ JWTAuth | REST API stateless |
| Admin actions | Custom view vs admin_action | ✅ Custom view | Mejor UX, botones dedicados |

---

## 🔗 References

- Architecture: `ARCHITECTURE_HYBRID.md`
- ADRs: `ADR/007-hybrid-architecture.md`, `ADR/008-communication-channels.md`
- Phase 0.6 Plan: `.paul/phases/00-foundation/00-01-REPO-RESTRUCTURE.md`
- Phase 1.1 Plan: `.paul/phases/01-marketplace/01-01-MARKETPLACE-FOUNDATION.md`

---

**Current Status:** Phase 0.6 ✅ | Phase 1.1 ✅ | Phase 1.2 📋 NEXT
**Next Action:** Phase 1.2 — Marketplace UI Polish + License Management
