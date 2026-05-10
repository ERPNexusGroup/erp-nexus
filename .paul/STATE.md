# PAUL State — ERP Nexus Core (Hybrid Architecture)

**Project:** ERP Nexus Core (Framework + Essential Modules)  
**Architecture:** Hybrid — Essential modules in core, Optional modules as plugins  
**Phase:** 0.6 — Hybrid Restructure (Mover essential modules a apps/)  
**Loop Position:** PLAN → APPLY → UNIFY  
**Started:** 2026-05-10  
**Last Updated:** 2026-05-10

---

## 🎯 Architecture Decision — HYBRID MODEL ✅ CONFIRMADO

**Decisión (Walter, 2026-05-10):**

ERP Nexus usa **Hybrid Architecture**:

### **Tier 1 — Core Framework (always present):**
- `core_users`, `core_companies`, `core_events`, `core_api`, `core_marketplace`, `core_permissions`, `core_audit`, `core_stats`, `core_config`, `core_dashboard`

### **Tier 2 — Essential Business Modules (integrated, NOT plugins):**
- `facturacion` — Facturación SRI Ecuador
- `inventory` — Inventario/stock
- `sales` — Ventas/cotizaciones
- `purchases` — Compras/proveedores
- `notifications` — Email + Telegram
- `permissions` — Permisos extendidos
- `dashboard` — Dashboard principal
- `print_manager` — PDF generation

**Motivo:** ERP debe ser funcional "out-of-the-box" para PYMES. No tiene sentido hacer instalar facturación como plugin cuando todo ERP necesita facturar.

### **Tier 3 — Optional Plugins (externos, instalables):**
- `hr` — Recursos humanos (repo separado)
- `crm` — CRM (repo separado)
- `accounting_adv` — Contabilidad avanzada (repo separado)
- `project_mgmt` — Gestión de proyectos (repo separado)
- `pos` — Punto de venta (repo separado)
- `ecommerce` — Tienda online (repo separado)

---

## 📊 Current State (After Phase 0.6.2 — Task Complete)

```
repos/erp-nexus/
├── apps/                      # ✅ 11 core + facturacion (essential)
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
│   │
│   ├── facturacion/           ✅ MOVED from modules/facturacion_ec/
│   │   ├── models.py
│   │   ├── api/routes.py
│   │   ├── services/
│   │   └── ...
│   │
│   ├── inventory/             ⏳ Pendiente (ya existe en modules?)
│   ├── sales/                 ⏳ Pendiente
│   ├── purchases/             ⏳ Pendiente
│   ├── notifications/         ⏳ Pendiente
│   ├── permissions/           ⏳ Pendiente
│   ├── dashboard/             ⏳ Pendiente
│   └── print_manager/         ⏳ Pendiente
│
├── modules/                   # ❌ Vacío (a eliminar en 0.6.3)
│   ├── accounting_basic/      # Demo — eliminar
│   ├── inventory_basic/       # Demo — eliminar
│   └── demo_flow/             # Demo — eliminar
│
├── erp_nexus/
│   ├── settings.py           # ✅ Actualizado
│   ├── modules_enabled.py    # ✅ Actualizado a apps.facturacion
│   └── ...
│
├── docker/
├── .paul/
└── README.md
```

**Task 0.6.2 completada:**
- ✅ `facturacion_ec/` movido a `apps/facturacion/`
- ✅ Package rename: `facturacion_ec` → `facturacion`
- ✅ Imports actualizados en core (core_api, tests, management commands)
- ✅ Settings actualizados (modules_enabled.py, INSTALLED_APPS implícito)
- ✅ Docsactualizadas (INSTALL.md, DEVELOPMENT.md, CONTRIBUTING.md)

**Próximo:** Task 0.6.3 — Eliminar módulos demo

---

## 📋 Phase 0.6 — Hybrid Restructure (PLAN)

**Objetivo:** Reorganizar core para hybrid architecture (essential modules en `apps/`).

**Estado actual:** ✅ Task 0.6.2 COMPLETADA — facturacion movido a `apps/facturacion/`

### Tasks pendientes (8 tasks):

| Task | Descripción | Estado | Estimación |
|------|-------------|--------|------------|
| 0.6.1 | Definir arquitectura híbrida | ✅ DONE | PLAN |
| 0.6.2 | Mover `facturacion_ec/` → `apps/facturacion/` | ✅ DONE | 2h |
| 0.6.3 | Eliminar módulos demo | ⬜ Pending | 30min |
| 0.6.4 | Clean core settings | ⬜ Pending | 1h |
| 0.6.5 | Eliminar estático modules_enabled.py | ⬜ Pending | 30min |
| 0.6.6 | Reorganizar workspace | ⬜ Pending | 1h |
| 0.6.7 | Actualizar documentación | ⬜ Pending | 2h |
| 0.6.8 | Actualizar PAUL | ⬜ Pending | 30min |
| 0.6.9 | Validar todo | ⬜ Pending | 1h |

**Total:** ~9 horas

---

## 🗺️ Phase 0.6.2 — Detalle (Mover facturacion_ec → apps/facturacion/)

### **Before:**
```
modules/facturacion_ec/
├── facturacion_ec/
│   ├── models.py
│   ├── api/routes.py
│   └── services/
```

### **After:**
```
apps/facturacion/
├── __init__.py
├── apps.py              (AppConfig — rename: FacturacionConfig)
├── models.py
├── admin.py
├── api/
│   └── routes.py
├── services/
├── migrations/
└── tests/
```

**Cambios:**
1. Mover directorio: `modules/facturacion_ec/facturacion_ec/` → `apps/facturacion/`
2. Rename package: `facturacion_ec` → `facturacion` (en apps.py, imports)
3. Actualizar imports rotos en core (de `modules.facturacion_ec` → `apps.facturacion`)
4. Añadir a `INSTALLED_APPS` en settings (como los otros core apps)

---

## 📈 Expected State After Phase 0.6

```
repos/erp-nexus/
├── apps/                      # 19 Django apps (11 core + 8 essential)
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
│   │
│   ├── facturacion/           ✅ Moved from modules/
│   ├── inventory/             ✅ (ya existe o por crear)
│   ├── sales/                 ✅ (ya existe o por crear)
│   ├── purchases/             ✅ (ya existe o por crear)
│   ├── notifications/         ✅ (ya existe o por crear)
│   ├── permissions/           ✅ (ya existe o por crear)
│   ├── dashboard/             ✅ (ya existe o por crear)
│   └── print_manager/         ✅ (ya existe o por crear)
│
├── erp_nexus/
│   ├── settings/
│   │   ├── base.py           # INSTALLED_APPS con los 19 apps
│   │   └── ...
│   ├── urls.py
│   └── ...
│
├── docker/
├── .paul/
├── README.md
└── (sin modules/ directory)
```

---

## 🔄 Dependencies

**Phase 0.6 dependencies:**
- ❌ Ninguno — es foundation

**Phase 1.1 (Marketplace) dependencies:**
- ✅ Phase 0.6 completado

---

## 📋 Acceptance Criteria

- [ ] `erp-nexus/apps/` contiene 19 Django apps
- [ ] No existe `modules/` directorio (o solo plugins externos futuros)
- [ ] `facturacion_ec/` movido a `apps/facturacion/` (rename package)
- [ ] Todos los essential modules registrados en `INSTALLED_APPS`
- [ ] No imports rotos (`grep -r "modules.facturacion"` → 0 results)
- [ ] `modules_enabled.py` eliminado o convertido a dinámico
- [ ] Tests core pasan (pytest apps/)
- [ ] Graphify rebuild sin errores
- [ ] Documentación ARCHITECTURE_HYBRID.md actualizada

---

## 🔗 References

- Architecture: `ARCHITECTURE_HYBRID.md`
- ADR: `ADR/007-hybrid-architecture.md`
- Project Definition: `PROJECT_DEFINITION.md`
- Work Plan: `WORK_PLAN.md`
- Phase Plan: `.paul/phases/00-foundation/00-01-REPO-RESTRUCTURE.md`

---

**Estado Actual:** PLAN completado, esperando APPLY  
**Próxima acción:** Ejecutar Phase 0.6.2 (mover facturacion_ec → apps/facturacion/)

**Nota:** Ya no se extraerá facturacion_ec a repo separado (era enfoque plugin-only). Ahora es hybrid con essential modules en core.
