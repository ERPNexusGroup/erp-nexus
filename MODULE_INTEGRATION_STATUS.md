# 📦 Estado de Integración de Módulos — ERP Nexus

**Última actualización:** 2026-05-10  
**Grafo version:** b97c55d8  
**Nodos aislados totales:** 61 (3% de 1,875)

---

## 📊 Tabla de Integración

| Módulo | Nodos Tot | Aislados | % Aislado | Estado | Acción Requerida |
|--------|-----------|----------|------------|--------|------------------|
| **core** apps (11) | ~1,600 | ~45 | 2.8% | ✅ Bueno | Ninguna |
| `facturacion_ec` | ~120 | 10 | **8.3%** | 🔴 Crítico | Integrar validator |
| `core_events` | ~50 | 6 | 12.0% | 🟡 Falso + | Documentar limitation |
| `accounting_basic` | ~60 | 2 | 3.3% | 🟢 Demo | Ninguna |
| `inventory_basic` | ~60 | 0 | 0% | ✅ Completo | — |
| `inventory` (future) | — | — | — | ⬜ Planeado | — |
| `sales` (future) | — | — | — | ⬜ Planeado | — |

---

## 🔴 Módulos con Problemas

### **facturacion_ec** — PRIORIDAD ALTA

**Problema:** `validator.py` tiene 5 funciones aisladas (no usadas).

**Detalle:**
| Archivo | Nodos aislados | Funciones |
|---------|----------------|-----------|
| `services/validator.py` | 5 | `validate_ruc`, `validate_cedula`, `validate_invoice_lines`, `validate_invoice_number`, `validate_invoice_totals` |

**Root cause:** El archivo se creó pero nunca se integró en los endpoints de la API.

**Fix requerido:** Modificar `modules/facturacion_ec/api/routes.py`:
```python
# En create_invoice:
from ..services.validator import (
    validate_ruc,
    validate_cedula,
    validate_invoice_totals,
    validate_invoice_number,
)

# Llamar validaciones antes de crear invoice
```

**Impacto de no fixear:**
- ❌ RUC inválidos se aceptan
- ❌ Cédulas inválidas se aceptan
- ❌ Totals mal calculados no se detectan
- ❌ Formato factura incorrecto

**Deadline:** Antes de v0.1.0 release

**Task PAUL:** `01-02-GRAPH-UNIFY` → Task 2

---

### **core_events** — PRIORIDAD MEDIA (FALSO POSITIVO)

**Problema reported:** 6 nodos aislados en `bus.py` (métodos).

**Realidad:**
EventBus **SÍ se usa** en:
- `apps/core_events/tasks.py` — `EventBus._process_sync()`
- `apps/core_api/v1/events.py` — `EventBus.emit()`
- `modules/accounting_basic/core/models.py` — `EventBus.emit()`
- `modules/inventory_basic/core/models.py` — `EventBus.emit()`

**¿Por qué aislados?** Graphify NO detecta:
1. Llamadas a métodos de clase con nombres dinámicos
2. Imports de `from apps.core_events.bus import EventBus` + `EventBus.emit()` (detecta import, no la llamada)
3. Docstrings generan nodos pero no edges a las llamadas

**Estado:** 🟡 **NO ES PROBLEMA REAL** — Códodo funcional.

**Acción:** Documentar como "Graphify limitation" en `GRAPH_HEALTH.md`. No requiere code changes.

---

## 🟢 Módulos Completamente Integrados

Estos módulos tienen **0 nodos aislados** o solo `__init__.py`:

| Módulo | Estado | Notas |
|--------|--------|-------|
| `inventory_basic` | ✅ | Demo funcional |
| `core_users` | ✅ | Base, bien integrado |
| `core_companies` | ✅ | Multi-tenant backbone |
| `core_permissions` | ✅ | Permissions system |
| `core_audit` | ✅ | Audit log working |
| `core_marketplace` | ✅ | Module registry |
| `core_api` | ✅ | REST API layer |
| `erp_nexus` core | ✅ | Settings, URLs, WSGI/ASGI |

---

## 🟡 Módulos Parciales / Oportunidades

### **core_stats** — 2 nodos aislados
- `Metric.increment()`, `Metric.get_stats()`
- **Estado:** Incompleto, no usado aún
- **Prioridad:** Baja (futuro)

### **accounting_basic** — 2 nodos aislados
- Métodos de `Account`/`JournalEntry` no usados
- **Estado:** Demo/plantilla, no core
- **Prioridad:** Baja

---

## 📈 Trayectoria de Integración

```
v0.5.0 (actual)
├── Nodos aislados: 61 (3%)
├── validator.py: ❌ NO integrado
└── EventBus: 🟡 Falso positivo (real usage OK)

v0.5.1 (post-validator fix)
├── Nodos aislados: ~56 (3% → 2.9%)
├── validator.py: ✅ Integrado
└── EventBus: 🟡 Documentado

v0.6.0 (futuro)
├── Nodos aislados: <30 (<1.6%)
└── Todos módulos core integrados
```

---

## 🎯 Cómo leer este reporte

**Columnas:**
- **Nodos Tot** — Nodos totales en el módulo (functions, classes, methods, files)
- **Aislados** — Nodos sin conexiones (imports, calls, references)
- **% Aislado** — Porcentaje de aislamiento (objetivo <5%)
- **Estado** — Salud del módulo:
  - ✅ **Bueno** — <5% aislados, o aislados esperados (__init__)
  - 🟡 **Par** — ...
  - 🔴 **Crítico** — Funcionalidad no integrada (>10% aislados o funciones no usadas)

**Acción Requerida:**
- **Fix required** — Código necesita cambios (integrar, eliminar, o documentar)
- **Document** — Escribir doc explicando por qué está aislado
- **None** — Saludable, no acción

---

## 📝 Notas

### Why Graphify Marka EventBus como Aislado?
Graphify extrae edges desde:
1. `import X` statements
2. `X.method()` calls parseadas estáticamente
3. Docstring references

EventBus se usa via:
```python
EventBus.emit("event.type", ...)  # Ya importado, llamada no rastreada bien
```

Esto es una **limitación known de Graphify** — no captura todas las llamadas dinámicas. El código funciona, el grafo sub-reporta connectivity.

### Why validator.py Totalmente Aislado?
Porquevalidator.py se creó pero **nunca se importó ni llamó** desde ningún endpoint. Es código muerto funcional.

### Fix validator no es trivial:
Requiere agregar validacions en API endpoints, lo que implica:
- Modificar `routes.py`
- Agregar imports
- Manejar errores (return 400)
- Tests de validación

Esto justifica un **PAUL task** (01-02 en cola).

---

## 📚 Referencias

- [`GRAPHIFY_IMPLEMENTATION_SUMMARY.md`](./GRAPHIFY_IMPLEMENTATION_SUMMARY.md) — Setup Graphify
- [`GRAPH_REPORT.md`](./graphify-out/GRAPH_REPORT.md) — Reporte completo generado
- [`graph.html`](./graphify-out/graph.html) — Visualización interactiva
- PAUL `.paul/phases/01-foundation/01-02-GRAPH-UNIFY.md` — Plan de unificación

---

**Mantenimiento:** Actualizar este archivo después de cada `graphify update .` o cambio significativo en integración de módulos.
