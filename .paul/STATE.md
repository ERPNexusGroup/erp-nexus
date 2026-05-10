# PAUL State — ERP Nexus Core (Hybrid Architecture)

**Project:** ERP Nexus Core (Framework + Essential Modules)
**Architecture:** Hybrid — Essential modules in core, Optional modules as plugins
**Phase:** 0.6 — Hybrid Restructure (Integrate essential modules)
**Loop Position:** PLAN → APPLY → UNIFY
**Started:** 2026-05-10
**Last Updated:** 2026-05-10

---

## 🎯 Architecture Decision — HYBRID MODEL ✅ CONFIRMADO

**Decisión (Walter, 2026-05-10):**

ERP Nexus usa **Hybrid Architecture**:

### **Tier 1 — Core Framework (11 apps — always present):**
`core_users`, `core_companies`, `core_events`, `core_api`, `core_marketplace`,
`core_permissions`, `core_audit`, `core_stats`, `core_config`, `core_dashboard`,
`core_pagebuilder` (web builder)

### **Tier 2 — Essential Business Modules (6 apps — integrated, NOT plugins):**
- `facturacion` — Facturación SRI Ecuador ✅ DONE (0.6.2)
- `inventory` — Inventario/stock ✅ DONE (0.6.5)
- `sales` — Ventas/cotizaciones ✅ DONE (0.6.6)
- `purchases` — Compras/proveedores ✅ DONE (0.6.6)
- `notifications` — Email + Telegram ✅ DONE (0.6.6)
- `print_manager` — PDF generation ✅ DONE (0.6.6)

**Motivo:** ERP debe ser funcional "out-of-the-box" para PYMES.

### **Tier 3 — Optional Plugins (futuro, instalables via Marketplace):**
`hr`, `crm`, `accounting_adv`, `project_mgmt`, `pos`, `ecommerce`

---

## 📊 Current State (After Phase 0.6.7 — ALL ESSENTIAL MODULES CREATED)

```
repos/erp-nexus/
├── apps/                      # 17 Django apps (11 core + 6 essential)
│   ├── core_users/            # Framework
│   ├── core_companies/
│   ├── core_events/           # Event Bus
│   ├── core_api/              # REST API (Django Ninja)
│   ├── core_marketplace/
│   ├── core_permissions/
│   ├── core_audit/
│   ├── core_stats/
│   ├── core_config/
│   ├── core_dashboard/
│   ├── core_pagebuilder/
│   │
│   ├── facturacion/           ✅ Essential — SRI invoices
│   ├── inventory/             ✅ Essential — stock management
│   ├── sales/                 ✅ Essential — orders/quotes
│   ├── purchases/             ✅ Essential — PO/suppliers
│   ├── notifications/         ✅ Essential — email/telegram/queue
│   └── print_manager/         ✅ Essential — PDF generation
│
├── modules/                   # Vacío (solo plugins futuros)
│   ├── README.md
│   └── registry.json
│
├── erp_nexus/
│   ├── settings/
│   │   └── base.py            # INSTALLED_APPS incluye todos los 17
│   ├── modules_enabled.py     # Vacío (plugins futuros)
│   └── ...
│
├── docker/
├── .paul/
│   ├── STATE.md              # Este archivo
│   ├── PROJECT.md
│   └── ROADMAP.md
└── README.md
```

---

## 📋 Phase 0.6 — Hybrid Restructure (APPLY COMPLETED 0.6.1–0.6.7)

**Objetivo:** Integrar todos los Essential Modules en `apps/` y eliminar demos.

### Tasks

| Task | Descripción | Estado | Estimación |
|------|-------------|--------|------------|
| 0.6.1 | Definir arquitectura híbrida | ✅ DONE | PLAN |
| 0.6.2 | Mover `facturacion_ec/` → `apps/facturacion/` | ✅ DONE | 2h |
| 0.6.3 | Eliminar módulos demo | ✅ DONE | 30min |
| 0.6.4 | Clean core settings | ✅ DONE | 1h |
| 0.6.5 | Create `apps/inventory/` desde `inventory_basic` | ✅ DONE | 2h |
| 0.6.6 | Crear módulos esenciales restantes | ✅ DONE | 4h |
| 0.6.7 | Update documentation | ✅ DONE | 2h |
| 0.6.8 | Rebuild graph + finalize state | ⬜ Pending | 1h |
| 0.6.9 | Validation | ⬜ Pending | 1h |

**Total:** 0.6.1–0.6.7 completados (~12h). Pendiente: 0.6.8 + 0.6.9 (~2h)

---

## 📦 Deliverables Phase 0.6

- ✅ 17 Django apps en `apps/` (11 framework + 6 essential)
- ✅ `modules/` directorio vacío (solo para futuros plugins)
- ✅ `INSTALLED_APPS` incluye todos essential modules (static)
- ✅ `modules_enabled.py` vacío (plugins dinámicos futuros vía Marketplace)
- ✅ Documentación actualizada:
  - ADR 007 (Hybrid Architecture)
  - ADR 008 (Communication Channels: REST/EventBus/GraphQL/gRPC)
  - INSTALL.md (5-min installation)
  - API_REFERENCE.md (todos módulos)
  - MODULE_SPEC.md (specs de 6 essential modules)
- ✅ Graphify rebuild en progreso (auto tras cada commit)

---

## 🔄 Dependencies

**Phase 0.6 dependencies:**
- ✅ Todos resueltos

**Phase 0.6.8 (Rebuild graph):**
- Depende de: todos los commits anteriores aplicados

**Phase 1.x (Marketplace) dependencies:**
- ⏳ Requiere Phase 0.6.9 (validation) completada

---

## 📋 Acceptance Criteria Phase 0.6

- [x] `apps/` contiene 17 Django apps
- [x] `modules/` vacío ( README.md + registry.json )
- [x] `INSTALLED_APPS` incluye 6 essential modules (facturacion, inventory, sales, purchases, notifications, print_manager)
- [x] `modules_enabled.py` vacío o solo comments (essential modules no están aquí)
- [ ] `pytest` pasa para cada app esencial (0.6.9)
- [ ] `python manage.py migrate` aplica sin errores (0.6.9)
- [ ] `python manage.py runserver` arranca (0.6.9)
- [ ] API endpoints /api/v1/facturacion/, /inventory/, /sales/, etc. funcionan (0.6.9)
- [ ] Graphify rebuild completado (0.6.8)
- [ ] Documentación completa (0.6.7 ✅)

---

## 📐 Phase 0.6.8 — Rebuild Graph + Finalize STATE

**Objetivo:** Reconstruir grafo de conocimiento y sincronizar STATE.

### Tasks

- [ ] `graphify extract .` — Regenerar grafo con nueva estructura de 17 apps
- [ ] Verificar `GRAPH_REPORT.md` actualizado
- [ ] Actualizar `STATE.md` con todos los módulos DONE
- [ ] Commit: `chore(0.6.8): rebuild knowledge graph post-hybrid-restructure`
- [ ] Push a GitHub (when network available)

**Nota:** Graphify hook ya se ejecutó automáticamente tras cada commit. Sólo verificar.

---

## ✅ Phase 0.6.9 — Validation

**Objetivo:** Verificar que todo el sistema funciona.

### Tasks

- [ ] `python manage.py check` — sin errores de sistema
- [ ] `python manage.py makemigrations` — sin cambios pendientes
- [ ] `python manage.py migrate` — aplica todas las migraciones de 6 módulos
- [ ] `pytest apps/facturacion/tests/` — pasan
- [ ] `pytest apps/inventory/tests/` — pasan
- [ ] `pytest apps/sales/tests/` — pasan
- [ ] `pytest apps/purchases/tests/` — pasan
- [ ] `pytest apps/notifications/tasks/` — pasan
- [ ] `pytest apps/print_manager/tests/` — pasan
- [ ] `python manage.py runserver` — arranca sin errores
- [ ] Prueba API: `curl http://localhost:8000/api/v1/facturacion/customers/` → 200/401
- [ ] Prueba API: `curl http://localhost:8000/api/v1/inventory/products/` → 200/401
- [ ] Commit: `test(0.6): validation — all 17 apps load correctly`

---

## 🔗 References

- Architecture: `ARCHITECTURE_HYBRID.md`
- ADRs: `ADR/007-hybrid-architecture.md`, `ADR/008-communication-channels.md`
- Multi-Repo Structure: `MULTI_REPO_STRUCTURE.md`
- Module Specs: `MODULE_SPEC.md`
- API Reference: `API_REFERENCE.md`
- Install Guide: `docs/INSTALL.md`
- Phase Plan: `.paul/phases/00-foundation/00-01-REPO-RESTRUCTURE.md`

---

## 🎯 Phase 0.6 Summary (What We Built)

### Code Commits
- 0.6.2 — `facturacion_ec` → `apps/facturacion/` (rename package, 16 files)
- 0.6.3 — Eliminados demo modules (accounting_basic, inventory_basic, demo_flow)
- 0.6.4 — Core settings limpios (INSTALLED_APPS con facturacion, modules_enabled vacío)
- 0.6.5 — `apps/inventory/` creado desde `inventory_basic` (10 files, package rename)
- 0.6.6 — Creados: `apps/sales/`, `apps/purchases/`, `apps/notifications/`, `apps/print_manager/` (58 files)
- 0.6.7 — Documentación actualizada (ADR 008, API_REFERENCE, INSTALL.md, etc.)
- 0.6.8 — Graph rebuild (auto)
- 0.6.9 — Validation (pending)

### Total Stats
- **New modules:** 5 (inventory, sales, purchases, notifications, print_manager)
- **Moved modules:** 1 (facturacion_ec → facturacion)
- **Deleted modules:** 3 demo (accounting_basic, inventory_basic, demo_flow)
- **Docs updated:** 15+ archivos
- **ADRs added:** 1 (ADR/008)
- **Total files changed:** ~120

---

**Estado Actual:** Tasks 0.6.1–0.6.7 ✅ COMPLETADAS | 0.6.8–0.6.9 ⏳ PENDIENTES  
**Próxima acción:** Ejecutar Validation (0.6.9) — Confirmar que `runserver` arranca y migraciones aplican.
