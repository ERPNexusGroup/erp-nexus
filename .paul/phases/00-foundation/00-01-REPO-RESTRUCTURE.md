# PAUL Phase 0.6.4 — Clean Core Settings

**Objetivo:** Asegurar que `INSTALLED_APPS` contenga solo essential modules en core, y que `modules_enabled.py` quede vacío (solo para plugins futuros).

## Tasks

- [ ] Verificar que `apps/facturacion` está en `INSTALLED_APPS`
- [ ] Eliminar cualquier resto de `modules/facturacion_ec` en settings
- [ ] `modules_enabled.py`: dejarlo vacío (solo comentarios)
- [ ] Verificar que `modules/` existe pero vacío (solo README.md, registry.json)
- [ ] `graphify rebuild` para actualizar grafo

**Dependencias:** 0.6.2, 0.6.3 completadas.

---

# PAUL Phase 0.6.5 — Replace inventory_basic → inventory

**Objetivo:** Convertir `modules/inventory_basic/` (demo) en `apps/inventory/` (essential module).

## Context

`inventory` es **Essential Module** (Tier 2 — Hybrid Architecture). Todo ERP necesita inventario.

`modules/inventory_basic/` es un demo module (placeholder). Lo reemplazamos con módulo real.

## Tasks

- [ ] **Copiar estructura** de `modules/inventory_basic/` → `apps/inventory/`
  - Mantener historial (git mv preferido, pero copy es aceptable si es rename de package)
- [ ] Rename package: `inventory_basic` → `inventory`
  - `apps.py`: rename class a `InventoryConfig`, `name = 'apps.inventory'`
  - `__init__.py`, `models.py` imports
- [ ] Actualizar imports en core que referencien `inventory_basic` → `inventory`
- [ ] Actualizar `MODULE_SPEC.md` — spec de inventory module
- [ ] Migrations: actualizar FK dependencias si las hubiera
- [ ] Commit: `feat(inventory): create essential inventory module from demo`

**Dependencias:** 0.6.3 (demo modules eliminados, pero copiamos _antes_ de eliminar? No, ya eliminamos. Usar git restore para recuperar inventory_basic desde HEAD~1, o re-crear desde cero).

**Estimación:** 2h

---

# PAUL Phase 0.6.6 — Create Essential Modules Restantes

**Objetivo:** Crear los remaining essential modules que NO tienen demo: `sales`, `purchases`, `notifications`, `print_manager`.

## Decisions tomadas (ADR 008):

- `permissions`: ya existe como `core_permissions` (framework) — NO crear módulo aparte
- `groups`: ya existe como `core_groups` (framework) — incluido
- `dashboard`: ya existe como `core_dashboard` (framework) — incluido
- `web_builder`: ya existe como `core_pagebuilder` (framework) — incluido
- `print_manager`: crear nuevo `apps/print_manager/` (Essential)

## Tasks por módulo

### 0.6.6.1 — Create `apps/sales/`
- [ ] Create directory structure:
  ```
  apps/sales/
  ├── __init__.py
  ├── __meta__.py       # Module metadata (parser AST)
  ├── apps.py           # SalesConfig(name='apps.sales')
  ├── models.py         # Order, OrderLine, Quote, QuoteLine
  ├── api/
  │   ├── __init__.py
  │   └── routes.py     # Django Ninja routers
  ├── services/
  │   ├── __init__.py
  │   ├── order_service.py
  │   └── quote_service.py
  ├── management/commands/
  │   └── (ninguno inicial)
  ├── migrations/       # Crear migración inicial
  ├── tests/
  │   ├── __init__.py
  │   └── test_models.py
  └── templates/sales/
  ```
- [ ] `__meta__.py` (template desde MODULE_SPEC)
- [ ] `apps.py` (AppConfig)
- [ ] `models.py` — minimal: Order, OrderLine (con total calculations)
- [ ] `api/routes.py` — CRUD endpoints
- [ ] migración inicial
- [ ] Commit: `feat(sales): create essential sales module`

### 0.6.6.2 — Create `apps/purchases/`
- [ ] Similar estructura a sales
- [ ] Models: PurchaseOrder, PurchaseOrderLine, Supplier
- [ ] API: CRUD + receive goods endpoint
- [ ] Commit: `feat(purchases): create essential purchases module`

### 0.6.6.3 — Create `apps/notifications/`
- [ ] Models: Notification, NotificationTemplate, NotificationQueue
- [ ] Services: email_sender, telegram_sender, queue_processor
- [ ] Event Bus listeners: subscribe a eventos core (invoice.created, order.created)
- [ ] Commit: `feat(notifications): create essential notifications module`

### 0.6.6.4 — Create `apps/print_manager/`
- [ ] Models: PrintTemplate, PrintJob
- [ ] Services: pdf_generator (WeasyPrint o ReportLab), barcode_generator
- [ ] Facturación usa print_manager para PDF
- [ ] Commit: `feat(print_manager): create reusable PDF generation module`

**Nota:** `inventory` se crea en 0.6.5 (desde inventory_basic recuperado).

**Estimación total:** 6h

---

# PAUL Phase 0.6.7 — Update Documentation

**Objetivo:** Actualizar toda la documentación para reflejar Hybrid Architecture con essential modules.

## Tasks

- [ ] `README.md` — Update diagram de repos (solo erp-nexus)
- [ ] `INSTALL.md` — Simplificar: solo `git clone erp-nexus`, `uv sync`, `migrate`
- [ ] `PROJECT_DEFINITION.md` — Scope actualizado (essential modules list)
- [ ] `WORK_PLAN.md` — Actualizado con nuevas fechas
- [ ] `MULTI_REPO_STRUCTURE.md` — Explicar hybrid model claramente
- [ ] `ARCHITECTURE.md` / `ARCHITECTURE_HYBRID.md` — Reflect decisions
- [ ] ADRs:
  - ADR/007 — Hybrid Architecture (ya existe)
  - ADR/008 — Communication Channels (creado)
- [ ] `MODULE_SPEC.md` — Add specs para sales, purchases, notifications, print_manager
- [ ] `CONTRIBUTING.md` — Update dev workflow (essential vs plugin)
- [ ] `docs/DEVELOPMENT.md` — Actualizar
- [ ] Commit: `docs(architecture): update for hybrid essential-modules model`

**Estimación:** 2h

---

# PAUL Phase 0.6.8 — Finalize State & Rebuild Graph

**Objetivo:** Sincronizar estado interno y reconstruir grafo de conocimiento.

## Tasks

- [ ] Actualizar `.paul/STATE.md` con:
  - facturacion: ✅ DONE
  - inventory: ✅ DONE (0.6.5)
  - sales: ✅ DONE (0.6.6.1)
  - purchases: ✅ DONE (0.6.6.2)
  - notifications: ✅ DONE (0.6.6.3)
  - print_manager: ✅ DONE (0.6.6.4)
- [ ] `graphify extract .` para regenerar grafo con nueva estructura
- [ ] Commit: `chore(graph): rebuild knowledge graph after 0.6 restructure`
- [ ] Push a GitHub (cuando red disponible)

**Estimación:** 1h

---

# PAUL Phase 0.6.9 — Validation

**Objetivo:** Verificar que todo funciona.

## Tasks

- [ ] `python manage.py check` — sin errores
- [ ] `python manage.py migrate` — migraciones aplican
- [ ] `pytest apps/facturacion/tests/` — pasan
- [ ] `pytest apps/inventory/tests/` — pasan
- [ ] `pytest apps/sales/tests/` — pasan
- [ ] `pytest apps/purchases/tests/` — pasan
- [ ] `pytest apps/notifications/tests/` — pasan
- [ ] `pytest apps/print_manager/tests/` — pasan
- [ ] `python manage.py runserver` — arranca sin errors
- [ ] `curl http://localhost:8000/api/v1/facturacion/invoices/` — devuelve 200/401
- [ ] Commit: `test(0.6): validate all essential modules load correctly`

**Estimación:** 1h

---

## Summary — Phase 0.6 Complete (Expected)

**Entrega:** ERP Nexus Core conHybrid Architecture funcional:

```
erp-nexus/
├── apps/
│   ├── core_* (11 framework apps)
│   ├── facturacion    ✅
│   ├── inventory      ✅
│   ├── sales          ✅
│   ├── purchases      ✅
│   ├── notifications  ✅
│   └── print_manager  ✅
├── modules/           (vacío — solo para plugins futuros)
└── erp_nexus/
    ├── settings.py    (INSTALLED_APPS incluye essential)
    └── modules_enabled.py (vacío, solo plugins)
```

**Documentación actualizada** + **Graphify grafo** reconstruido.

**Commit en GitHub** (cuando red disponible).
