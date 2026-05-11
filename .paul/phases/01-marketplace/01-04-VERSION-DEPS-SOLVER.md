# PAUL Phase 1.4 — Version Management + Dependencies Solver

**Fecha:** 2026-05-12
**Estado:** 📋 PLAN — Esperando APPLY
**Sprint:** M2 Phase 1.4
**Estimated:** ~20h (2.5 días)
**Commit branch:** `feat/marketplace/version-deps-solver`

---

## Objetivo

Implementar gestión robusta de versiones y resolución de dependencias entre módulos del marketplace.

**Problema actual:**
- No hay validación de compatibilidad entre versiones de módulos
- No hay detección de conflictos (módulos incompatibles)
- Instalación de un módulo no resuelve automáticamente sus dependencias
- No hay upgrade path analysis (¿esta actualización es segura?)

**Solución Phase 1.4:**
- Modelos de constraints y dependencias
- Algoritmo de resolución (topological sort)
- UI de conflictos en admin (pre-flight warnings)
- Auto-instalación de dependencias (`--with-deps`)
- Upgrade safety checker (backward compatibility)

---

## Tasks Desglosados

### 1.4.1 — `ModuleVersionConstraint` Model (2h)

**Modelo:**
```python
class ModuleVersionConstraint(models.Model):
    module = ForeignKey(ModuleCatalogItem, related_name='version_constraints')
    constraint_type = CharField(max_length=20, choices=[
        ('equal', '='), ('approx_equal', '~'), ('caret', '^'),
        ('greater', '>'), ('greater_equal', '>='),
        ('less', '<'), ('less_equal', '<='),
    ])
    version = CharField(max_length=50)  # e.g. "1.2.3", ">=1.0.0", "^2.0.0"
    description = TextField(blank=True)  # "Requiere facturacion >=1.2.0"

    def is_satisfied_by(installed_version: str) -> bool:
        # Lógica semver: parse version + constraint → bool
```

**Migration:**
- Crear `apps/core_marketplace/migrations/0004_moduleversionconstraint.py`

**Tests unitarios:**
- `test_is_satisfied_by_equal()`
- `test_is_satisfied_by_caret()`
- `test_is_satisfied_by_range()`
- `test_invalid_semver_raises()`

---

### 1.4.2 — `ModuleDependency` Model (2h)

**Modelo:**
```python
class ModuleDependency(models.Model):
    module = ForeignKey(ModuleCatalogItem, related_name='dependencies')
    depends_on = ForeignKey(ModuleCatalogItem, related_name='dependents')
    version_constraint = ForeignKey(ModuleVersionConstraint, null=True, blank=True)
    required = BooleanField(default=True)  # True = hard requirement
    conflict = BooleanField(default=False)  # True = cannot coexist
    description = TextField(blank=True)

    class Meta:
        unique_together = [('module', 'depends_on')]
```

**Migration:**
- `apps/core_marketplace/migrations/0005_moduledependency.py`

**Admin:**
- `ModuleDependencyAdmin` inline en `ModuleCatalogItemAdmin`
- Mostrar árbol de dependencias (readonly) en detail view

---

### 1.4.3 — Semver Parser + Compatibility Checker (2h)

**Utility:** `apps/core_marketplace/utils/semver.py`

```python
def parse_version(v: str) -> Version:
    """Parse '1.2.3-alpha.1' → Version(major=1, minor=2, patch=3, pre='alpha.1')"""

def compare_versions(v1: str, v2: str) -> int:
    """Return -1 if v1<v2, 0 if equal, 1 if v1>v2"""

def satisfies_constraint(version: str, constraint: str) -> bool:
    """Check if version satisfies semver constraint ('^1.2.0', '>=1.0.0', '~1.2')"""

def highest_compatible_version(constraints: List[str], available: List[str]) -> Optional[str]:
    """Pick highest version that satisfies all constraints"""
```

**Tests:**
- `test_parse_version()` — casos normales, pre-release, build metadata
- `test_satisfies_constraint_caret()` — `^1.2.3` acepta `1.2.3`–`1.999.999`
- `test_satisfies_constraint_approx()` — `~1.2.3` acepta `1.2.3`–`1.2.999`
- `test_satisfies_constraint_range()` — `>=1.0.0 <2.0.0`

---

### 1.4.4 — Dependency Resolver Algorithm (3h)

**Service:** `apps/core_marketplace/services/resolver.py`

```python
class DependencyResolver:
    def resolve_install_plan(module_name: str, with_deps: bool = True) -> InstallPlan:
        """
        Returns:
            InstallPlan(
                to_install: List[ModuleCatalogItem],  # in order
                conflicts: List[Conflict],
                missing_deps: List[str],
                already_installed: List[EnabledModule],
            )
        """

    def topological_sort(modules: List[ModuleCatalogItem]) -> List[ModuleCatalogItem]:
        """Kahn's algorithm — detect cycles, raise CycleError"""

    def detect_conflicts(modules: List[ModuleCatalogItem]) -> List[Conflict]:
        """Find modules that cannot coexist (conflict=True)"""

    def check_upgrade_safety(target: ModuleCatalogItem, from_version: str) -> UpgradeCheck:
        """Return: SAFE | BREAKING | UNKNOWN"""
```

**Algoritmo:**
1. Obtener `ModuleDependency` del módulo target
2. Para cada dependencia `required=True`:递归 resolución (DFS)
3. Detectar ciclos → `CycleError` con path
4. Detectar conflicts → marcar_modules en conflicto
5. Generar `InstallPlan` con orden topológico
6. Calcular `UpgradeCheck` comparando semver (major version change = breaking)

**Tests:**
- `test_resolve_simple_chain()` — A→B→C resuelve [B, C] para instalar A
- `test_resolve_detects_cycle()` — A→B→A lanza `CycleError`
- `test_resolve_detects_conflict()` — A conflict with B → ambos en `conflicts` list
- `test_topological_sort_multiple()` — DAG complejo, orden correcto
- `test_upgrade_safety_major_bump()` — 1.x→2.x = BREAKING

---

### 1.4.5 — Conflict Detection UI en Admin (2h)

**Admin Enhancement:** `apps/core_marketplace/admin.py`

```python
class ModuleCatalogItemAdmin(admin.ModelAdmin):
    def install_view(self, request, module_id):
        # Pre-flight check BEFORE install
        plan = resolver.resolve_install_plan(module_name)
        if plan.conflicts:
            messages.error(request, f"Conflictos: {plan.conflicts}")
            return render('admin/install_conflicts.html', {'plan': plan})
        if plan.missing_deps:
            messages.warning(request, f"Deps faltantes: {plan.missing_deps}")
            # Offer: "Install with dependencies --with-deps"
        # Proceed install...
```

**Templates:**
- `templates/admin/install_conflicts.html` — tabla de conflictos, botones "Cancel" / "Force Install"
- `templates/admin/install_dependencies.html` — lista de deps pendientes, checkbox "Install dependencies"

**JavaScript:**
- Modal de confirmación con detalles before install
- "Show dependency tree" expandable

---

### 1.4.6 — Auto-Dependency Installation (2h)

**Command enhancement:** `module_install` command

```bash
# Install con todas las dependencias (required + optional)
uv run manage.py module_install sales --with-deps

# Install solo dependencias requeridas (hard requirements)
uv run manage.py module_install sales --with-deps=required

# Install sin tocar dependencias (default)
uv run manage.py module_install sales
```

**Implementation:**
1. `module_install` llama `resolver.resolve_install_plan(module_name, with_deps=flag)`
2. Si `with_deps=True`: instala en order topológico (deps primero)
3. Si conflicto: abort con mensaje claro + sugerencia `--force`
4. Log detallado: `"Installing dependencies: B, C..."`

**Flag `--force`:**
- Ignora conflicts (pero still instala deps requeridas)
- Útil para development/testing

---

### 1.4.7 — Upgrade Path Analysis (2h)

**Service extension:** `resolver.check_upgrade_safety(target, from_version)`

```python
class UpgradeCheck:
    status: Literal['SAFE', 'BREAKING_MAJOR', 'BREAKING_MINOR', 'UNKNOWN']
    breaking_changes: List[str]
    recommended: bool

def check_upgrade_safety(module_name, target_version, current_version) -> UpgradeCheck:
    """
    Compare current_version vs target_version:
    - Major bump (1.x → 2.x) = BREAKING (unless explicitly marked compatible)
    - Minor bump (1.2 → 1.3) = SAFE (backward compatible by semver)
    - Patch bump (1.2.3 → 1.2.4) = SAFE
    """
```

**Admin UI:**
- En `module_install` (upgrade mode): mostrar advertencia si `BREAKING`
- Botón "View breaking changes" → enlaza a release notes (si existen en `__meta__.py`)

---

### 1.4.8 — Tests E2E (3h)

**File:** `apps/core_marketplace/tests/test_dependencies.py`

**Test cases:**

1. `test_install_with_missing_dependency_fails()` — A requiere B no instalado → error
2. `test_install_with_deps_autoinstalls()` — `--with-deps` instala B automáticamente
3. `test_conflict_detection_two_modules()` — A y B en conflicto → mensaje claro
4. `test_circular_dependency_detected()` — A→B→A → `CycleError`
5. `test_upgrade_safe_minor_bump()` — 1.2.0→1.3.0 = SAFE
6. `test_upgrade_breaking_major_bump()` — 1.x→2.x = BREAKING con warning
7. `test_version_constraint_satisfied()` — `^1.2.0` acepta `1.2.3`, rechaza `2.0.0`
8. `test_dependency_resolution_order()` — DAG → order topológico correcto

**Fixtures:**
- Mock modules con `__meta__.py` que declaran dependencies
- `ModuleCatalogItem` + `ModuleDependency`工厂
- `EnabledModule` fake para simulating installed state

---

### 1.4.9 — Cache + Admin Integration (1h)

**Cache keys:**
- `dependencies:{module_name}` — dependency tree cache (5min)
- `resolve_plan:{module_name}:{with_deps}` — install plan cache

**Invalidation triggers:**
- `module_install` → limpiar cache de dependencias de TODOS los módulos
- `module_uninstall` → igual
- `ModuleDependency` save/delete → limpiar cache específico

**Context processor update:**
- `core_dashboard.context_processors` → `dependency_graph()` (optional, opcional para dashboard)

---

### 1.4.10 — Documentation (1h)

**Archivos:**

1. `DEPENDENCIES.md` — Guía completa:
   - Cómo declarar dependencias en `__meta__.py`
   - Formatos de constraint semver (`^`, `~`, `=`, `>=`, `<=`)
   - Ejemplos de conflictos y resoluciones
   - Upgrade guide (how to bump major version safely)

2. `MODULE_SPEC.md` update — Sección "Dependencies":
   ```yaml
   dependencies:
     - module: facturacion
       version: "^1.0.0"
       required: true
     - module: inventory
       version: "~1.2.0"
       required: false
   conflicts:
     - module: old_inventory
       reason: "Reemplazado por inventory v2"
   ```

3. `docs/marketplace/dependency-resolution.md` — Diagrama de flujo algorithm

4. `UPGRADE.md` — Guía de actualización segura de módulos

---

## Deliverables Finales Phase 1.4

**Models:**
- `ModuleVersionConstraint` (con `is_satisfied_by()` method)
- `ModuleDependency` (con `required` + `conflict` flags)

**Services:**
- `DependencyResolver` (topological sort + cycle detection + conflict detection)
- `SemverParser` (standalone utility)

**Commands:**
- `module_install --with-deps` (auto-install dependencies)
- `check_dependencies <module>` (CLI: show dependency tree)
- `resolve_dependencies <module>` (CLI: show install plan)

**Admin UI:**
- Pre-flight check en `module_install` view
- Conflict/dependency warning pages
- Inline editing de dependencias en `ModuleCatalogItemAdmin`

**API:**
- `GET /api/v1/marketplace/dependencies/{module}` — devuelve dependency tree JSON
- `POST /api/v1/marketplace/validate-install/{module}` — pre-flight validation (returns conflicts/missing)

**Tests:**
- 8+ unit tests (semver parser, constraint checker)
- 8+ E2E tests (install flow con/without deps, conflicts, cycles, upgrades)

**Docs:**
- `DEPENDENCIES.md`
- `MODULE_SPEC.md` updated
- `docs/marketplace/dependency-resolution.md`
- `UPGRADE.md`

**Quality:**
- ✅ `manage.py check` — 0 issues
- ✅ Migrations aplicadas limpias
- ✅ 27 E2E tests passing total (19 existing + 8 new)

---

## Acceptance Criteria Phase 1.4

- [ ] `ModuleVersionConstraint` model + admin + migrations aplicadas
- [ ] `ModuleDependency` model + admin inline + migrations aplicadas
- [ ] Semver parser satisface constraints (`^`, `~`, `=`, `>=`, `<=`)
- [ ] `DependencyResolver` detecta ciclos y conflictos
- [ ] `module_install --with-deps` instala dependencias automáticamente en orden correcto
- [ ] Admin muestra pre-flight warnings antes de install (conflicts + missing deps)
- [ ] `module_install` rechaza install si conflictos no resueltos (a menos que `--force`)
- [ ] Upgrade analysis detecta breaking changes (major version bump)
- [ ] 8+ tests E2E pasando (dependencies, conflicts, cycles, upgrades)
- [ ] Documentación completa (DEPENDENCIES.md, MODULE_SPEC.md upgrade)
- [ ] Total tests: **27 E2E passing**

---

## Timeline Estimado

| Day | Tasks | Outcome |
|-----|-------|---------|
| D1 | 1.4.1 + 1.4.2 (models + migrations) | DB schema listo |
| D2 | 1.4.3 (semver parser) + unit tests | Parser validado |
| D3 | 1.4.4 (resolver algorithm) + tests | Resolución funcional |
| D4 | 1.4.5 (admin UI) + 1.4.6 (auto-deps) | Admin warnings + --with-deps |
| D5 | 1.4.7 (upgrade analysis) + 1.4.9 (cache) | Upgrade safety + cache |
| D6 | 1.4.8 (E2E tests) + bugfixes | 8 tests新 added |
| D7 | 1.4.10 (docs) + final polish + unify | Docs + PAUL complete |

**Total:** 5-7 días hábiles

---

## Risks & Mitigations

| Riesgo | Mitigación |
|--------|------------|
| Ciclos complejos en dependencias | Validación en `save()` de `ModuleDependency` (prevent cycle on create) |
| Semver edge cases (pre-release, build metadata) | Usar librería `packaging` (ya en requirements) para parsing robusto |
| Performance: resolver en tiempo real puede ser lento con muchos módulos | Cache de `InstallPlan` por module_name (5min TTL) |
| `module_install` se vuelve muy complejo | Separar lógica a `DependencyResolver` service (single responsibility) |
| Admin UI se satura con opciones | Agrupar en collapsible panels ("Dependencies", "Conflicts", "Upgrade Analysis") |

---

## Dependencies

✅ Phase 1.3 — GitHub Auto-discovery COMPLETED
📦 `packaging` library ( instalado en requirements )
🔧 `ModuleCatalogItem`, `EnabledModule` models existentes

---

**Phase 1.3 signature:** Applied, Verified, UNIFY Complete ✅
**Phase 1.4 signature:** PLAN READY → Esperando APPLY
