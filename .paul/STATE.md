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
- `inventory` — Inventario/stock ⏳ Pending (0.6.5)
- `sales` — Ventas/cotizaciones ⏳ Pending (0.6.6)
- `purchases` — Compras/proveedores ⏳ Pending (0.6.6)
- `notifications` — Email + Telegram ⏳ Pending (0.6.6)
- `print_manager` — PDF generation ⏳ Pending (0.6.6)

**Motivo:** ERP debe ser funcional "out-of-the-box" para PYMES.

### **Tier 3 — Optional Plugins (futuro, instalables via Marketplace):**
`hr`, `crm`, `accounting_adv`, `project_mgmt`, `pos`, `ecommerce`

---

## 📊 Current State (After Phase 0.6.3 — DONE)

```
repos/erp-nexus/
├── apps/                      # 11 core + 1 essential (facturacion)
│   ├── core_users/
│   ├── core_companies/
│   ├── core_events/
│   ├── core_api/
│   ├── core_marketplace/
│   ├── core_permissions/
│   ├── core_audit/
│   ├── core_stats/
│   ├── core_config/
│   ├── core_dashboard/
│   ├── core_pagebuilder/
│   │
│   ├── facturacion/           ✅ MOVED (0.6.2)
│   │   ├── models.py
│   │   ├── api/routes.py
│   │   ├── services/
│   │   └── ...
│   │
│   ├── inventory/             ⏳ 0.6.5 (recuperar de inventory_basic)
│   ├── sales/                 ⏳ 0.6.6 (crear nuevo)
│   ├── purchases/             ⏳ 0.6.6 (crear nuevo)
│   ├── notifications/         ⏳ 0.6.6 (crear nuevo)
│   └── print_manager/         ⏳ 0.6.6 (crear nuevo)
│
├── modules/                   # ✅ Vacío (demo eliminados en 0.6.3)
│   ├── README.md
│   └── registry.json
│
├── erp_nexus/
│   ├── settings/
│   │   └── base.py            # INSTALLED_APPS incluye facturacion
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

**Completado (0.6.1 — 0.6.3):**
- ✅ Arquitectura híbrida definida (ADR/007, ADR/008)
- ✅ `facturacion_ec/` → `apps/facturacion/` (rename package preservado)
- ✅ Demo modules eliminados (`accounting_basic`, `inventory_basic`, `demo_flow`)
- ✅ Settings limpios (INSTALLED_APPS actualizado, modules_enabled.py vacío)
- ✅ Documentación arquitectónica actualizada

---

## 📋 Phase 0.6 — Hybrid Restructure (PLAN → APPLY → UNIFY)

**Objetivo:** Integrar todos los Essential Modules en `apps/` y eliminar demos.

### Tasks

| Task | Descripción | Estado | Estimación |
|------|-------------|--------|------------|
| 0.6.1 | Definir arquitectura híbrida | ✅ DONE | PLAN |
| 0.6.2 | Mover `facturacion_ec/` → `apps/facturacion/` | ✅ DONE | 2h |
| 0.6.3 | Eliminar módulos demo | ✅ DONE | 30min |
| 0.6.4 | Clean core settings | ⬜ Pending | 1h |
| 0.6.5 | Create `apps/inventory/` desde `inventory_basic` | ⬜ Pending | 2h |
| 0.6.6 | Crear módulos esenciales restantes (sales, purchases, notifications, print_manager) | ⬜ Pending | 4h |
| 0.6.7 | Update documentation | ⬜ Pending | 2h |
| 0.6.8 | Rebuild graph + finalize state | ⬜ Pending | 1h |
| 0.6.9 | Validation | ⬜ Pending | 1h |

**Total pendiente:** ~12h

---

## 📈 Expected State After Phase 0.6.9 (VALIDATION)

```
repos/erp-nexus/
├── apps/                      # 17 Django apps (11 core + 6 essential)
│   ├── core_users/            # Framework
│   ├── core_companies/
│   ├── core_events/           # Event Bus
│   ├── core_api/              # REST API (Django Ninja)
│   ├── core_marketplace/
│   ├── core_permissions/      # Permissions framework
│   ├── core_audit/
│   ├── core_stats/
│   ├── core_config/
│   ├── core_dashboard/        # Dashboard framework
│   ├── core_pagebuilder/      # Web builder
│   │
│   ├── facturacion/           ✅ Essential — SRI invoices
│   ├── inventory/             ✅ Essential — stock
│   ├── sales/                 ✅ Essential — orders/quotes
│   ├── purchases/             ✅ Essential — PO
│   ├── notifications/         ✅ Essential — email/telegram
│   └── print_manager/         ✅ Essential — PDF
│
├── modules/                   # Vacío (solo plugins futuros via Marketplace)
├── erp_nexus/
│   ├── settings/base.py       # INSTALLED_APPS incluye los 17
│   └── modules_enabled.py     # Vacío
└── (otros archivos core)
```

**Nota:** `permissions`, `dashboard`, `web_builder` ya existen como
`core_permissions`, `core_dashboard`, `core_pagebuilder` (Tier 1).

---

## 🔄 Dependencies

**Phase 0.6 dependencies:**
- ✅ 0.6.2 (facturacion integrado) — DONE
- ✅ 0.6.3 (demo modules eliminados) — DONE

**Phase 1.x (Marketplace) dependencies:**
- ⏳ Phase 0.6 completo → requisito para Marketplace

---

## 📋 Acceptance Criteria

- [ ] `apps/` contiene 17 Django apps (11 core + 6 essential)
- [ ] `modules/` vacío (solo README.md, registry.json)
- [ ] Sin imports de `modules.facturacion_ec` (solo `apps.facturacion`)
- [ ] `modules_enabled.py` vacío (plug & play essential modules)
- [ ] Todos los essential modules en `INSTALLED_APPS`
- [ ] `pytest` pasa para cada app esencial
- [ ] `python manage.py migrate` aplica sin errores
- [ ] `python manage.py runserver` arranca
- [ ] API endpoints /api/v1/facturacion/ & /api/v1/inventory/ funcionan
- [ ] Graphify rebuild sin errores
- [ ] Documentación (ARCHITECTURE_HYBRID.md, MULTI_REPO_STRUCTURE.md) actualizada

---

## 🔗 References

- Architecture: `ARCHITECTURE_HYBRID.md`
- ADRs: `ADR/007-hybrid-architecture.md`, `ADR/008-communication-channels.md`
- Project Definition: `PROJECT_DEFINITION.md`
- Work Plan: `WORK_PLAN.md`
- Phase Spec: `.paul/phases/00-foundation/00-01-REPO-RESTRUCTURE.md`

---

**Estado Actual:** PLAN (0.6.2 y 0.6.3 ya APPLYed)
**Próxima acción:** Ejecutar Task 0.6.4 — Clean core settings
