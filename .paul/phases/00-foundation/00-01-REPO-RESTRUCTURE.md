---
phase: 0.6
plan: repo-restructure
type: execute
autonomous: false
---

<objective>
Restructurar el proyecto actual separando el CORE de módulos independientes.

**Why:** El código actual mezcla:
- CORE framework (11 apps, middleware, marketplace engine)
- Módulos específicos (facturacion_ec, accounting_basic, inventory_basic)
- Templates y ejemplos

Esto viola el principio de modularidad. Necesitamos:
1. ERP Nexus CORE — solo framework (11 apps + marketplace engine)
2. facturacion_ec — repo separado (módulo independiente)
3. Limpiar módulos demo/ejemplo del core

**Output:**
- `repos/erp-nexus/` → Solo core (11 apps + marketplace)
- `repos/facturacion_ec/` → Módulo extraído (nuevo repo)
- `repos/` → Directorio con todos los proyectos independientes
- Marketplace configurado para instalar módulos desde GitHub
</objective>

<context>
## Estado Actual (INCORRECTO)

```
repos/erp-nexus/
├── apps/                    # 11 core apps ✅ (debería quedarse)
├── modules/                 # ❌ MÓDULOS AQUÍ NO VAN
│   ├── facturacion_ec/      # Debe ser repo separado
│   ├── accounting_basic/    # Demo, debe salir
│   ├── inventory_basic/     # Demo, debe salir
│   └── demo_flow/           # Demo, debe salir
├── modules_enabled.py       # ❌ Debe generarse desde Marketplace
├── erp_nexus/settings.py    # ✅ Core (quedarse)
└── manage.py                # ✅ Core (quedarse)
```

**Problema:** 
- Core contiene módulos — no es modular
- `modules_enabled.py` manual — debería ser auto-generado
- No hay separación clara: core vs módulos

## Estado Deseado (CORRECTO)

```
repos/
├── erp-nexus/               # CORE ONLY
│   ├── apps/               # 11 core Django apps
│   ├── erp_nexus/
│   │   ├── settings/
│   │   ├── urls.py
│   │   └── modules_enabled.py  # AUTO-GENERADO
│   ├── docker/
│   ├── pyproject.toml
│   └── .paul/              # PAUL para core
│
├── facturacion_ec/          # MÓDULO INDEPENDIENTE (repo propio)
│   ├── facturacion_ec/
│   │   ├── models.py
│   │   ├── api/
│   │   ├── services/
│   │   └── __meta__.py
│   ├── tests/
│   ├── README.md
│   └── .paul/              # PAUL para módulo
│
├── sdk-nexus/              # SDK (crear módulos)
├── nexus-cli/              # CLI tool
└── nexus-marketplace/      # Marketplace server
```

## Cambios Requeridos

### 1. Extraer facturacion_ec a repo separado
- Crear `repos/facturacion_ec/` (nuevo git repo)
- Mover TODO el código de `modules/facturacion_ec/` allí
- Mantener historial git (filter-branch o subtree split)
- Actualizar `erp-nexus/` para que NO contenga facturacion_ec

### 2. Eliminar módulos demo del core
- `modules/accounting_basic/` → eliminar
- `modules/inventory_basic/` → eliminar  
- `modules/demo_flow/` → eliminar
- `config/facturacion_ec_settings_example.py` → eliminar

### 3. Limpiar references a modules/ en core
- Buscar imports de `modules.*` en core
- Reemplazar con `apps.*` (core) o eliminar
- Actualizar `INSTALLED_APPS` si hay referencias

### 4. ModuleRegistry → auto-generate from marketplace
- `modules_enabled.py` debe generarse dinámicamente
- Leer de DB (Module model) en runtime
- No archivo estático

### 5. Actualizar documentation
- Actualizar `WORK_PLAN.md` — separar phases por repo
- Actualizar `DOCS_INDEX.md` — estructura multi-repo
- Crear `MULTI_REPO_STRUCTURE.md` — guía de organization

## Complejidad

⚠️ **ALTA COMPLEJIDAD** — Cambios estructurales profundos:
- Historial git (mantener commits de facturacion_ec)
- Dependencias cross-repo (facturacion_ec depende de core apps)
- CI/CD para múltiples repos
- Submodule vs subtree decision

## Alternatives Considered

### Alt A: Monorepo (TODO en un repo) — ACTUALMENTE
**Pros:** Simple, un solo CI, un solo deploy
**Cons:** No hay true modularity, difícil separar módulos, coupling alto

### Alt B: Multi-repo (cada módulo repo independiente) — ELEGIDO
**Pros:** True isolation, cada módulo versiona independiente, clara separación
**Cons:** Más repos, CI más complejo, dependencias cross-repo

### Alt C: Hybrid (core repo + modules/ subtree)
**Pros:** Core standalone, módulos como subtrees
**Cons:** Complejo de mantener, git subtree overhead

**Decisión:** Multi-repo puro (Alt B) — Mayor claridad, mejor para contributions externas.
</context>

<skills>
# Git expertice
- git subtree split (extraer directorio a repo separado manteniendo historial)
- git filter-branch (rewrite history)
- Submodule management (si usamos submodules)

# Django modularization
- Django app config (AppConfig)
- Dynamic INSTALLED_APPS
- ModuleRegistry pattern

# Project organization
- Multi-repo strategies
- Dependency management (requirements con paths)
</skills>

<acceptance_criteria>
# Acceptance Criteria

## Git Structure
- [ ] `repos/` directory exists with independent repos
- [ ] `erp-nexus/` es SOLO core (11 apps + marketplace engine)
- [ ] `facturacion_ec/` es repo independiente con su propio historial
- [ ] `accounting_basic/`, `inventory_basic/`, `demo_flow/` removidos del core
- [ ] `.gitmodules` (si usamos submodules) o documentación de dependencias

## Code Separation
- [ ] Ningún `modules/` directorio en erp-nexus core
- [ ] `INSTALLED_APPS` en core NO referencia módulos externos
- [ ] `modules_enabled.py` es generado dinámicamente (no estático)
- [ ] Core apps no importan de `modules.*`

## Documentation
- [ ] `MULTI_REPO_STRUCTURE.md` creado
- [ ] `WORK_PLAN.md` actualizado (roadmap por repo)
- [ ] `CONTRIBUTING.md` actualizado (cómo contribuir a cada repo)
- [ ] `README.md` core actualizado (solo core scope)
- [ ] `INSTALL.md` actualizado (instalación modular)

## Testing
- [ ] Tests core pasan (pytest erp-nexus/)
- [ ] facturacion_ec tests pasan en su repo (si se move con tests)

## CI/CD
- [ ] GitHub Actions configurado para erp-nexus (core)
- [ ] GitHub Actions configurado para facturacion_ec (módulo)
- [ ] Workflow de dependencia: facturacion_ec CI depende de core estable
</acceptance_criteria>

<boundaries>
# Scope

## IN SCOPE (ESTE PLAN)
- ✅ Mover facturacion_ec a repo separado
- ✅ Eliminar módulos demo (accounting_basic, inventory_basic, demo_flow)
- ✅ Limpiar core de referencias a modules/
- ✅ Documentar nueva estructura multi-repo
- ✅ Configurar git (subtree split o manual copy)

## OUT OF SCOPE (FUTURO)
- ❌ Crear facturacion_ec repo en GitHub (solo local por ahora)
- ❌ Configurar CI/CD para cada repo (solo estructura local)
- ❌ SDK/CLI/Marketplace (fases 2-3 del roadmap)
- ❌ Extraer inventory/sales (futuro, ahora solo facturacion_ec)

## Decisions Pendientes
1. **¿git subtree o manual copy?**
   - subtree: mantiene historial, más complejo
   - manual copy: simple, pierde historial (pero ok para v0.1.0)
   - Recomendación: manual copy (facturacion_ec joven, historial corto)

2. **¿Marketplace como DB o como Git clone?**
   - DB: registry de módulos (name, version, git_url)
   - Installer: clona git_url a ~/.erp-nexus/modules/
   - Elegido: DB registry + git clone
</boundaries>

<tasks>
## Task 0.6.1 — Plan Restructure (DONE — este PLAN)
**Type:** checkpoint:decision  
**Estimate:** Complete

---

## Task 0.6.2 — Extract facturacion_ec to Separate Repo

**Type:** auto  
**Estimate:** 2 hours

```yaml
action: GIT_OPERATION
description: >
  Extraer modules/facturacion_ec/ a repos/facturacion_ec/ manteniendo historial.
  
  Opción A (subtree split — mantiene historial):
  git subtree split --prefix=modules/facturacion_ec -b facturacion_ec-split
  git clone --depth=1 . repos/facturacion_ec
  (en facturacion_ec) git checkout facturacion_ec-split
  
  Opción B (manual copy — más simple, pierde historial):
  mkdir -p repos/facturacion_ec
  cp -r modules/facturacion_ec/* repos/facturacion_ec/
  (en facturacion_ec) git init; git add .; git commit -m "Initial import"
  
  RECOMENDADO: Opción B (facturacion_ec es joven, 1 semana de commits)
```

**Verificar:**
- [ ] `repos/facturacion_ec/` existe
- [ ] Tiene su propio `git init` (separado de erp-nexus)
- [ ] Archivos copiados correctamente (models, api, services, tests)
- [ ] `.gitignore` apropiado para módulo

---

## Task 0.6.3 — Remove Demo Modules from Core

**Type:** auto  
**Estimate:** 30 min

```yaml
action: DELETE_DIRECTORIES
description: >
  Eliminar módulos demo del core (no forman parte del framework):
  
  rm -rf modules/accounting_basic/
  rm -rf modules/inventory_basic/
  rm -rf modules/demo_flow/
  rm -f config/facturacion_ec_settings_example.py
```

**NOTA:** Asegurar que no haya imports de estos módulos en core antes de borrar.

```bash
# Verificar imports
grep -r "accounting_basic" --include="*.py" apps/ erp_nexus/ || echo "OK — no refs"
grep -r "inventory_basic" --include="*.py" apps/ erp_nexus/ || echo "OK — no refs"
```

---

## Task 0.6.4 — Update Core Settings

**Type:** auto  
**Estimate:** 1 hour

```yaml
file: erp_nexus/settings/base.py
action: MODIFY
changes:
  - Remove modules/ from INSTALLED_APPS si están allí
  - Asegurar que INSTALLED_APPS solo contiene:
      'apps.core_*'  # 11 core apps
      'django.contrib.*'  # Django contrib
  - Eliminar references a modules_enabled.py si está hardcoded
  - Configurar dynamic module loading from DB (future)
```

**Verificar:**
```bash
uv run python manage.py check --deploy
```

---

## Task 0.6.5 — Remove modules_enabled.py Static File

**Type:** auto  
**Estimate:** 30 min

```yaml
file: erp_nexus/modules_enabled.py
action: DELETE_OR_REFACTOR
description: >
  modules_enabled.py es estático — eliminar o convertir en función
  que lee de ModuleRegistry (DB).
  
  Si se elimina:
  1. Buscar imports de modules_enabled en codebase
  2. Reemplazar con:
     from apps.core_marketplace.registry import get_enabled_modules
     enabled = get_enabled_modules()
  
  3. Eliminar archivo modules_enabled.py
```

**Verificar imports:**
```bash
grep -r "modules_enabled" --include="*.py" .
```

---

## Task 0.6.6 — Reorganize Workspace Directory

**Type:** auto  
**Estimate:** 1 hour

```yaml
action: MOVE_DIRECTORIES
description: >
  Mover facturacion_ec a repos/ y reestructurar:
  
  mkdir -p repos/facturacion_ec
  # Mover (ya hecho en Task 0.6.2)
  
  # Actualizar estructura:
  repos/
  ├── erp-nexus/       (core — ya existe)
  ├── facturacion_ec/  (módulo extraído)
  ├── inventory/       (crear luego)
  └── sales/           (crear luego)
```

**Actualizar `.gitignore` de erp-nexus:**
- Ignorar `repos/*/` excepto `repos/erp-nexus/` (el core)

---

## Task 0.6.7 — Documentation Updates

**Type:** auto  
**Estimate:** 2 hours

```yaml
files:
  - README.md: Actualizar — solo core scope, sin módulos
  - INSTALL.md: Separar secciones (Core installation vs Module installation)
  - WORK_PLAN.md: Roadmap por repo (core roadmap vs module roadmaps)
  - CONTRIBUTING.md: Cómo contribuir a core vs módulos
  - DOCS_INDEX.md: Agregar sección "Multi-Repo Structure"
  - MULTI_REPO_STRUCTURE.md: NUEVO — guía completa de organización
```

**MULTI_REPO_STRUCTURE.md** debe contener:
- Por qué multi-repo
- Cómo agregar nuevo módulo (crear repo, registrar en marketplace)
- Dependencias entre repos (facturacion_ec → erp-nexus core)
- CI/CD strategy (cada repo independiente)
- Versioning (SemVer por módulo)

---

## Task 0.6.8 — Update PAUL for Multi-Repo

**Type:** auto  
**Estimate:** 30 min

```yaml
files:
  - .paul/PROJECT.md: Actualizar scope (solo core)
  - .paul/ROADMAP.md:  Dividir milestones por repo
    M1-M6 para erp-nexus core
    M1'-M3' para facturacion_ec (separado)
  
  # Nuevo project Context:
  "ERP Nexus Core": Framework only
  "facturacion_ec": Independent module (own PAUL soon)
```

**Nota:** facturacion_ec necesitará su propio `.paul/` una vez sea repo separado.

---

## Task 0.6.9 — Validate Everything Works

**Type:** auto  
**Estimate:** 1 hour

```yaml
checks:
  - manage.py check --deploy
  - manage.py migrate  # migrations core solo
  - manage.py runserver  # Arranca sin modules/
  - pytest apps/  # Tests core pasan
  - pytest modules/  # Debería fallar (modules ya no existe) — esperado
```

**Éxito criteria:**
- ✅ ERP Nexus core arranca sin `modules/` directorio
- ✅ Todas las core apps funcionan
- ✅ No hay imports de modules.* en core
- ✅ facturacion_ec代码 en repos/facturacion_ec/ intacto
- ✅ Git history de erp-nexus core limpio (sin facturacion_ec commits)
</tasks>

<boundaries>
# NO HACER

## Explicado
- ❌ No configurar CI/CD (solo estructura local)
- ❌ No crear GitHub repos (solo local directories)
- ❌ No migrar database (datos se pierden, es reestructuración code-only)
- ❌ No crear SDK/CLI/Marketplace en esta fase (solo facturacion_ec extraction)

## Si surgen problemas
- Si algo se rompe: rollback con git
- Hacer commit después de cada task
- Documentar decisions en ADR-006 (repo structure)
</boundaries>

<verification>
## Post-Restructure Verification

1. **Structure check**
   ```bash
   ls repos/
   # Should show: erp-nexus/ facturacion_ec/
   ls erp-nexus/modules/  # Should NOT exist or be empty
   ```

2. **Import check**
   ```bash
   grep -r "from modules." erp-nexus/ --include="*.py"
   # Should return nothing
   ```

3. **Django check**
   ```bash
   cd repos/erp-nexus
   uv run python manage.py check
   # Should pass (no AppNotRegistered errors)
   ```

4. **Git status**
   ```bash
   cd repos/erp-nexus
   git log --oneline --graph --all | head -20
   # Should show clean history without facturacion_ec noise
   ```

5. **Graphify update**
   ```bash
   cd repos/erp-nexus
   graphify update .
   # Nodos aislados deberían bajar (facturacion_ec ya no en core)
   ```
</verification>

<skills-loaded>
# Tools activated
- Git (subtree/split, filter-branch)
- File operations (mv, cp, rm)
- Django settings management
- Documentation writing
</skills-loaded>
