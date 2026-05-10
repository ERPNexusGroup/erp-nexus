# Phase 0.6 — Repository Restructure (Hybrid Model)

**Objective:** Reorganize `erp-nexus/` para Hybrid Architecture
**Status:** PLANNED
**Estimated:** 9h

---

## Context

ERP Nexus adopta **Hybrid Architecture**:
- **Essential modules** (facturacion, inventory, sales, purchases, notifications, permissions, dashboard, print_manager) → Integrated in core (`apps/`)
- **Optional modules** (hr, crm, projects, …) → External plugins via Marketplace

Actualmente `facturacion_ec/` está en `modules/` como si fuera un plugin aparte.
Debe moverse a `apps/facturacion/` como essential module integrado.

---

## Tasks

### **0.6.1 — Plan ✅ DONE**
- [x] Define hybrid architecture
- [x] Creates ADR-007
- [x] Updates docs (PROJECT_DEFINITION, WORK_PLAN, STATE)

---

### **0.6.2 — Mover facturacion_ec a apps/facturacion/**

**Estimated:** 2h

**Steps:**
1. Verificar current state de `modules/facturacion_ec/`
2. Rename package: `facturacion_ec` → `facturacion`
   - `facturacion_ec/__init__.py` → `facturacion/__init__.py`
   - `facturacion_ec/apps.py` → rename class a `FacturacionConfig`
   - Update `name = "facturacion_ec"` → `name = "facturacion"`
3. Mover directorio:
   ```bash
   mv modules/facturacion_ec/facturacion_ec/ apps/facturacion/
   ```
4. Eliminar directorio vacío `modules/facturacion_ec/`
5. Actualizar imports en core:
   - Buscar: `from modules.facturacion_ec`
   - Reemplazar: `from apps.facturacion`
6. Actualizar `INSTALLED_APPS` en settings (si no está autodiscover)
7. Commit: `refactor(modules): integrate facturacion_ec as essential module`

**Validation:**
- [ ] Django finds `facturacion` app
- [ ] migrate facturacion funciona
- [ ] No import errors en `manage.py check`

---

### **0.6.3 — Eliminar módulos demo**

**Estimated:** 30min

**Modules a eliminar:**
- `accounting_basic/`
- `inventory_basic/`
- `demo_flow/`

**Steps:**
1. Eliminar directorios
2. Eliminar referencias en docs
3. Commit: `chore: remove demo modules (essential modules replace them)`

**Validation:**
- [ ] `grep -r "accounting_basic" repos/erp-nexus/` → 0 results
- [ ] `grep -r "inventory_basic"` → 0 results
- [ ] `grep -r "demo_flow"` → 0 results

---

### **0.6.4 — Clean core settings**

**Estimated:** 1h

**Steps:**
1. Eliminar referencias a `modules/` en settings
2. Asegurar `INSTALLED_APPS` solo contiene `apps.` y `core_` apps
3. Verificar `PYTHONPATH` no incluye `modules/`
4. Commit: `refactor(settings): clean modules references for hybrid model`

**Validation:**
- [ ] `grep -r "modules/" erp_nexus/settings/` → 0 results
- [ ] `manage.py check` sin warnings

---

### **0.6.5 — Eliminar modules_enabled.py estático**

**Estimated:** 30min

**Contexto:** `erp_nexus/modules_enabled.py` existe y es estático. Con essential modules integrados, este archivo es innecesario (plugins opcionales se manejan via DB).

**Steps:**
1. Verificar que ningún código importa `modules_enabled`
2. Eliminar archivo
3. Remover referencias en settings/urls
4. Commit: `refactor: remove static modules_enabled.py (use DB + Marketplace)`

**Validation:**
- [ ] Archivo eliminado
- [ ] No imports rotos

---

### **0.6.6 — Reorganizar workspace**

**Estimated:** 1h

**Steps:**
1. Verificar estructura `apps/` (19 apps esperadas)
2. Mover cualquier essential module restante de `modules/` → `apps/`
3. Asegurar naming consistente: `facturacion`, `inventory`, `sales`, `purchases`, `notifications`, `permissions`, `dashboard`, `print_manager`
4. Commit: `chore(workspace): reorganize for hybrid architecture`

**Validation:**
- [ ] `ls apps/` muestra 19 apps
- [ ] No hay `modules/` con código (sino plugins futuros)

---

### **0.6.7 — Actualizar documentación**

**Estimated:** 2h

**Documents to update/create:**
- [x] ARCHITECTURE_HYBRID.md ✅
- [x] ADR/007-hybrid-architecture.md ✅
- [x] PROJECT_DEFINITION.md ✅
- [x] WORK_PLAN.md ✅
- [ ] DOCS_INDEX.md — reordenar para arquitectura híbrida
- [ ] README.md — actualizar scope (essential modules in core)
- [ ] INSTALL.md — simplificar (ya no hay que instalar plugins básicos)
- [ ] DEVELOPMENT.md — guía para desarrollar essential modules
- [ ] MODULE_SPEC.md — dos secciones: Essential vs Optional
- [ ] CONTRIBUTING.md — actualizar git flow

**Commit:** `docs: update for hybrid architecture model`

---

### **0.6.8 — Actualizar PAUL**

**Estimated:** 30min

**Steps:**
- [x] STATE.md actualizado ✅
- [ ] Asegurar que futurasPhases (M1, M2, …) reflejan hybrid model
- [ ] Añadir milestone M0.5 (Essential Modules Integration)
- [ ] Actualizar acceptance criteria

**Commit:** `chore(paul): update state for hybrid architecture`

---

### **0.6.9 — Validación final**

**Estimated:** 1h

**Checklist:**
- [ ] `python manage.py check` — sin errors
- [ ] `pytest apps/` — tests core pasan
- [ ] `python manage.py migrate` — crea tablas de todos los 8 essential modules
- [ ] `python manage.py runserver` — arranca sin errores
- [ ] Graphify rebuild: `graphify update .`
- [ ] `git status` — limpio, sin archivos huérfanos
- [ ] Docs index (DOCS_INDEX.md) apunta a ARCHITECTURE_HYBRID.md

---

## Rollback Plan

**Si algo falla:**
```bash
# En erp-nexus
git reset --hard HEAD~1  # Revertir commit de move
# Los facts vuelven a modules/facturacion_ec/
```

**Si essential modules no funcionan:**
- Considerar extraer a plugins (perder hybrid model)
- Pero esenciales deben vivir en core para MVP

---

## Deliverables

- [x] ADR-007 (hybrid architecture decision)
- [x] ARCHITECTURE_HYBRID.md
- [x] Updated PROJECT_DEFINITION.md
- [x] Updated WORK_PLAN.md
- [x] Updated PAUL STATE
- [ ] Phase 0.6.2 completado (facturacion en apps/)
- [ ] Phase 0.6.3+ completados
- [ ] All tests passing

---

## Notes

**Diff from original Phase 0.6 (plugin-only):**
- **Old:** Extract `facturacion_ec/` → separate repo
- **New:** Move `facturacion_ec/` → `apps/facturacion/` (stay in core)

**Rationale:** Essential business modules should be in core for out-of-the-box ERP experience.

**Rename:** `facturacion_ec` → `facturacion` (simpler, consistent with inventory/sales).
