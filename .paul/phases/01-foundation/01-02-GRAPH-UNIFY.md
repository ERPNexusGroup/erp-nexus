---
phase: 0.5
plan: graph-unify
type: execute
autonomous: true
---

<objective>
Unificar el grafo de conocimiento Graphify conectando nodos aislados y validando edges inferidos.

**Why:** El grafo actual tiene 61 nodos aislados (3%) y 434 edges inferidos con confianza 0.50-0.80 (18%). Necesitamos:
1. Conectar los nodos aislados CRÍTICOS (validator.py, bus.py métodos)
2. Validar que los edges inferidos sean correctos (o marcarlos como EXTRACTED)
3. Asegurar que todos los elementos codebles estengan conectados al grafo

**Output:**
- `validator.py` integrado y linkeado a API endpoints
- `bus.py` métodos correctamente referenciados
- Documentación actualizada que reference todos los components
- Graphify actualizado (0 nodos aislados críticos)
</objective>

<context>
## Estado Actual del Grafo (2026-05-10)

### Métricas
- Nodos: 1,875
- Edges: 2,300
  - EXTRACTED: 1,866 (81%)
  - INFERRED: 434 (18%) — confianza promedio 0.52
- Nodos aislados: 61 (3%)

### Nodos Aislados CRÍTICOS

#### 1. `apps/facturacion/services/validator.py` — 5 nodos aislados (TODO)
**Funciones aisladas:**
- `validate_ruc()` — Valida RUC (módulo 11)
- `validate_cedula()` — Valida cédula (módulo 10)
- `validate_invoice_lines()` — Valida líneas de factura
- `validate_invoice_number()` — Valida formato número
- `validate_invoice_totals()` — Valida subtotal+tax=total

**Problema:** Estas funciones existen pero NO se usan en ningún endpoint. El grafo las marca como aisladas porque no hay `import` o llamadas directas.

**Solución:** Integrar validators en `api/routes.py` (create_invoice endpoint).

#### 2. `apps/core_events/bus.py` — 6 nodos aislados (métodos documentados)
**Métodos aislados:**
- `emit()` — Emite evento
- `subscribe()` — Suscribe handler
- `subscribe_sync()` — Handler en memoria
- `get_history()` — Historial eventos
- `get_stats()` — Estadísticas

**Problema:** Son métodos de clase con docstrings pero no se ven llamadas en el codebase (o Graphify no las detectó).

**Verificar:** Buscar usos reales de `EventBus.` en el código.

#### 3. `apps/core_stats/models.py` — 2 nodos aislados
- `Metric.increment()` — Incrementa métrica
- `Metric.get_stats()` — Obtiene estadísticas

**Estado:** Módulo stats incompleto/integrado parcialmente. No crítico.

#### 4. `modules/accounting_basic/core/models.py` — 2 nodos aislados
- Métodos de Accounting que no se usan aún.

**Estado:** Módulo demo/plantilla. No crítico.

### Edges Inferidos (434, confianza 0.5-0.8)

**Todos son relación `'uses'`** — Principalmente:
- Test files → modelos (ej: `test_audit.py` → `AuditLog`)
- Models → otros modelos (FK relationships no explicitadas)
- Views → servicios

**Confianza 0.5-0.8 es normal para edges inferidos** (no extracted from explicit imports).

**NO SON PROBLEMA** — Son correctos pero no extraídos directamente. El score 0.52 promedio es aceptable.

### Files con __init__.py aislados (40+)
- apps/*/__init__.py
- modules/*/__init__.py

**ESTADO NORMAL** — `__init__.py` vacíos o con solo imports no generan edges. No es problema.

---

## Root Cause Analysis

### Nodos aislados = Funciones no referenciadas

**Causa principal:**
1. `validator.py` functions created but NOT called anywhere
2. `bus.py` methods quizás no tienen calls explícitas detectables
3. `__init__.py` vacíos — por diseño

**Implicación:**
- Código muerto (validator no se usa) → Dead weight
- O funcionalidad no integrada → Incomplete implementation

### Solución

**Para validator.py (URGENTE):**
- Agregar validaciones en `api/routes.py` create_invoice endpoint
- Esto linkea las funciones al grafo automáticamente

**Para bus.py (VERIFICAR):**
- Buscar usos reales de `EventBus.emit()` y `EventBus.subscribe()`
- Si hay usage, el grafo debería haberlo detectado
- Si NO hay usage, el código está muerto (eliminar o documentar)

**Para otros aislados:**
-Son aceptables (`__init__.py`, módulos demo no usados)
</context>

<skills>
# Conocimiento requerido
- Graphify usage patterns
- Graph node-linking (how edges form from code)
- Django/Python import analysis
- Code coverage analysis

# Habilidades existentes
- Ya tenemos el grafo generado
- Podemos re-ejecutar `graphify update .` después de cambios
</skills>

<acceptance_criteria>
# Acceptance Criteria

## Functional
1. **Validator integration**
   - [ ] `validate_ruc()` llamado desde create_invoice endpoint
   - [ ] `validate_cedula()` llamado al crear/actualizar Customer
   - [ ] `validate_invoice_totals()` llamado antes de save Invoice
   - [ ] `validate_invoice_number()` llamado en Invoice.save()

2. **EventBus usage verification**
   - [ ] Buscar todos los `EventBus.emit()` en codebase
   - [ ] Si hay 0 usos, marcar como código muerto (DECISION: eliminar o mantener)
   - [ ] Si hay usos, verificar por qué graphify no los linkeó

3. **Graphify regenerado**
   - [ ] Ejecutar `graphify update .`
   - [ ] Nodos aislados de validator.py → 0
   - [ ] Nodos aislados de bus.py métodos → conectados (si hay usage)

## Quality
- [ ] Cobertura tests de validator >80%
- [ ] Linter OK en services/validator.py
- [ ] Actualizar DOCS_INDEX.md con sección "Graph Health"

## Documentation
- [ ] `GRAPH_HEALTH.md` — Reporte estado grafo, acciones tomadas
- [ ] `MODULE_INTEGRATION_STATUS.md` — Estado integración módulos
</verification>

## Manual Verification
1. Revisar código: ¿validator.py se usa en endpoints?
2. Si NO se usa: Agregar llamadas
3. Re-ejecutar graphify update
4. Comparar nodos aislados antes/después
5. Documentar en GRAPH_HEALTH.md
</verification>

<boundaries>
# Scope

## In Scope (THIS PLAN)
- ✅ Integrar validator.py en API endpoints
- ✅ Verificar usos EventBus
- ✅ Regenerar grafo y medir mejora
- ✅ Documentar estado

## Out of Scope (future phases)
- ❌ Eliminar código muerto (decisión posterior)
- ❌ Refactor complete bus.py (solo verificación)
- ❌ Eliminar módulos demo no usados
- ❌ Arreglar todos los edges inferidos (confianza 0.5-0.8 es aceptable)

## Constraints
- No modificar core Graphify (is a tool, not part of ERP)
- Solo modificar ERP Nexus code para integrar validator
- Mantener tests existentes funcionando
</boundaries>

<tasks>
## Task 0.5.1 — Audit Current Graph State

**Type:** auto  
**Estimate:** 30 min

```yaml
action: ANALYZE
description: >
  Analizar grafo actual y分类 nodos aislados por criticidad.
  1. Listar TODOS los nodos aislados con detalles (file, category, label)
  2. Identificar cuáles son CRÍTICOS vs aceptables
  3. Documentar hallazgos en GRAPH_HEALTH.md
```

**Output:** `GRAPH_HEALTH.md` con:
- Tabla de nodos aislados por archivo
- Criticidad (CRÍTICO/IMPORTANTE/BAJO)
- Recomendaciones por cada uno

---

## Task 0.5.2 — Integrate Validator into API

**Type:** auto  
**Estimate:** 2 hours

```yaml
file: apps/facturacion/api/routes.py
action: MODIFY
changes:
  - Import validator functions:
      from ..services.validator import (
          validate_ruc,
          validate_cedula,
          validate_invoice_totals,
          validate_invoice_number,
      )
  - En create_invoice endpoint:
      # Antes de crear factura:
      is_valid, error = validate_ruc(invoice.company.tax_id)
      if not is_valid:
          return 400, {"error": f"RUC inválido: {error}"}
      
      is_valid, error = validate_cedula(customer.identification_number)
      if not is_valid:
          return 400, {"error": f"Cédula inválida: {error}"}
      
      # Después de calcular totals:
      is_valid, error = validate_invoice_totals(invoice)
      if not is_valid:
          return 400, {"error": error}
```

**Tests:** Agregar pruebas que fallen si validation no se ejecuta.

---

## Task 0.5.3 — Verify EventBus Usage

**Type:** auto  
**Estimate:** 1 hour

```yaml
action: GLOBAL_SEARCH
pattern: "EventBus\."
files: ["**/*.py"]
exclude: ["tests/**", "**/__init__.py"]
```

**Acciones:**
1. Buscar todos los `EventBus.` en el codebase (excluyendo tests/__init__)
2. Contar:
   - `EventBus.emit()` calls
   - `EventBus.subscribe()` calls
3. Si CERO usos reales → DECISION: ¿eliminar o mantener documentado?
4. Si hay usos → investigar por qué Graphify no linkeó estos edges

**Output:** `EVENTBUS_USAGE.md` con hallazgos.

---

## Task 0.5.4 — Regenerate Graphify

**Type:** auto  
**Estimate:** 5 min

```yaml
command: |
  cd /home/wcun/.openclaw/workspace/repos/erp-nexus
  graphify update .
  # O si no hay CLI:
  # El hook post-commit ya lo hace automáticamente
```

**Verificar:**
```bash
# Comparar nodos aislados antes/después
grep -c "nodos aislados" graphify-out/GRAPH_REPORT.md
# Debería bajar de 61 a ~55 (eliminar 5 de validator)
```

---

## Task 0.5.5 — Update Documentation

**Type:** auto  
**Estimate:** 30 min

```yaml
files:
  - GRAPH_HEALTH.md (nuevo)
  - MODULE_INTEGRATION_STATUS.md (nuevo)
  - DOCS_INDEX.md (actualizar sección Graphify)
```

**Contenido GRAPH_HEALTH.md:**
- Estado actual (antes/después)
- Nodos aislados críticos tratados
- Edges inferidos aceptables
- Próximos pasos para limpiar grafo
</tasks>

<boundaries>
# Integridad del grafo

## Lo que NO vamos a hacer en esta fase
- No vamos a eliminar código (solo integrar)
- No vamos a modificar estructura de carpetas
- No vamos a re-escribir módulos existentes
- No vamos a crear nuevos tests (solo verificar)

## Lo que SÍ vamos a hacer
- ✅ Integrar validator en API (conectar nodos)
- ✅ Documentar estado grafo
- ✅ Re-generar graphify
- ✅ Tomar decisiones sobre EventBus (usar/eliminar)
</boundaries>

<verification>
## Checkpost-Integration

1. ¿Validator functions llamadas desde API?
   - grep -r "validate_" apps/facturacion/api/
   - Debería encontrar 4 llamadas

2. ¿Graphify regenerado?
   - graphify-out/GRAPH_REPORT.md actualizado (timestamp reciente)

3. ¿Diferencia en nodos aislados?
   - Antes: 61
   - Después: ~55 o menos

4. ¿Documentación actualizada?
   - GRAPH_HEALTH.md existe
   - MODULE_INTEGRATION_STATUS.md existe
</verification>

<skills-loaded>
# Herramientas a usar
- grep/buscar en codebase
- graphify CLI (update)
- Markdown writing
- Code editing (agregar validaciones)
</skills-loaded>
