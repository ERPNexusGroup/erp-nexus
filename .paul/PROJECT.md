# ERP Nexus — PAUL Project Context

**Why this project exists:**
ERP Nexus es un ERP modular hybird para empresas ecuatorianas: core integrado (facturación, inventario, ventas, compras) + plugins opcionales (HR, CRM, etc.). Instalación única, funcionalidad completa out-of-the-box.

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
- ✅ 6 essential modules integrados (facturacion, inventory, sales, purchases, notifications, print_manager)
- ✅ Architecture híbrida validada
- ✅ Documentación completa
- ✅ Tests básicos por módulo

**v1.0.0 (12 semanas):**
- ✅ Marketplace funcional (instalar/desinstalar plugins)
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

### **Next Milestone**

**M2 — Marketplace & Plugin System** (Phase 1.1 en PLAN)
- Inicio: 2026-05-10
- Estimación: 2-3 semanas
- Objetivo: Admin puede instalar `hr` desde GitHub con un click

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

**Estado repo:** `erp-nexus/` (único repo necesario para MVP)

---

## 🔄 Phase 1.1 — Próximo Sprint

**Objetivo:** Marketplace para plugins opcionales.

**Tasks:**
1. Extender ModuleCatalogItem (metadata completa)
2. Auto-discover GitHub org (ERPNexus)
3. Install/uninstall commands
4. Dynamic module loading (modules_enabled.py reload)
5. Admin UI (Marketplace tab)
6. API endpoints
7. Validation + security (__meta__.py schema)

**Duración estimada:** 9h

---

## 📈 Metrics

**Code Stats (Phase 0.6):**
- New modules: 6
- Moved: 1 (facturacion_ec → facturacion)
- Deleted: 3 demo
- Total apps: 17
- Commits: 10+ (Phase 0.6)
- Files changed: ~120

**Quality:**
- Django check: ✅ OK
- Migrations apply: ✅ OK
- Server starts: ✅ OK
- No lint errors (ruff, mypy pending)

---

## 🎯 Decisiones Arquitectónicas (Phase 0.6)

| Decisión | Opción | Elegido | Razón |
|----------|--------|---------|-------|
| Essential modules position | Separate repo vs apps/ | ✅ `apps/` | ERP funcional sin fricción |
| Permissions module | Nuevo vs core_permissions | ✅core_permissions` | Ya existe, extender |
| Notifications module | Separede vs core_events | ✅ Separado | Event Bus ≠ delivery |
| Print manager | En facturacion vs separate | ✅ Separate | Reutilizable por múltiples módulos |
| API REST vs GraphQL | GraphQL early vs REST-first | ✅ REST-first | Simplicidad, GraphQL solo cuando frontend justifique |
| gRPC | Sí vs No | ❌ No | Overkill para monorepo |
| Event Bus use | Todo via eventos vs REST directo | ✅ Híbrido | Loose-coupling para side-effects |

---

## 🔗 References

- Architecture: `ARCHITECTURE_HYBRID.md`
- ADRs: `ADR/007-hybrid-architecture.md`, `ADR/008-communication-channels.md`
- Phase Plan: `.paul/phases/00-foundation/00-01-REPO-RESTRUCTURE.md`
- Next Phase: `.paul/phases/01-marketplace/01-01-MARKETPLACE-FOUNDATION.md`

---

**Current Status:** Phase 0.6 ✅ COMPLETADO | Phase 1.1 📋 PLAN
**Next Action:** Execute Phase 1.1 — Marketplace Foundation
