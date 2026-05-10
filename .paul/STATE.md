# PAUL State — ERP Nexus Core

**Project:** ERP Nexus Core (Framework)  
**Phase:** 0.6 — Repository Restructure  
**Loop Position:** PLAN → APPLY → UNIFY  
**Started:** 2026-05-10  
**Last Updated:** 2026-05-10

---

## 📊 Current Loop Status

```
┌─────────────────────────────────────────────┐
│  PLAN  │  APPLY  │  UNIFY                    │
│  ✅    │  ⬜     │  ⬜                       │
└─────────────────────────────────────────────┘
```

**Current Phase:** 0.6 — Repository Restructure (Multi-Repo Separation)  
**Current Position:** PLAN (Phase 0.6 defined, awaiting approval)  
**Next Action:** Execute PLAN 0.6.2 — Extract facturacion_ec to separate repo

---

## 🎯 Project Context — SCOPE CLARIFICATION

### **IMPORTANTE: Qué es ERP Nexus Core**

**ERP Nexus Core** = **Framework solamente**. NO incluye módulos de negocio.

**SCOPE DEL CORE:**
✅ 11 Django core apps (auth, companies, marketplace, events, api, etc.)  
✅ Multi-tenant middleware  
✅ ModuleRegistry + ModuleInstaller  
✅ Event Bus (comunicación entre módulos)  
✅ REST API layer (Django Ninja)  
✅ Admin panel + Dashboard  
✅ Docker + deployment tooling  
✅ Documentation framework  

**OUT OF SCOPE (se van a otros repos):**
❌ facturacion_ec → `github.com/ERPNexus/facturacion_ec`  
❌ inventory → `github.com/ERPNexus/inventory` (futuro)  
❌ sales → `github.com/ERPNexus/sales` (futuro)  
❌ SDK/CLI/Marketplace server → repos separados

---

## 📋 Arquitectura Multi-Repo (DECIDIDA)

```
Organización GitHub ERPNexus:
┌──────────────────────────────────────────────────┐
│  erp-nexus/           ← ESTE REPO (CORE)          │
│  facturacion_ec/      ← MÓDULO (repo separado)    │
│  inventory/           ← MÓDULO (repo separado)    │
│  sales/               ← MÓDULO (repo separado)    │
│  sdk-nexus/           ← SDK (repo separado)       │
│  nexus-cli/           ← CLI (repo separado)       │
│  nexus-marketplace/   ← Marketplace server        │
└──────────────────────────────────────────────────┘
```

**Dependencias:**
```
facturacion_ec → erp-nexus >= 0.5.0
inventory      → erp-nexus >= 0.6.0
sales          → erp-nexus >= 0.7.0
```

**Marketplace flow:**
1. Module developer publica módulo en GitHub
2. Admin instala desde Marketplace: `manage.py install_module --git <url>`
3. ModuleInstaller clona a `~/.erp-nexus/modules/{name}/`
4. Core carga módulo dinámicamente

---

## 🎯 Phase 0.6 — Repository Restructure

**Objetivo:** Separar core de módulos. Dejar `erp-nexus/` como SOLO framework.

### Tasks (9 tasks):

| Task | Descripción | Estado | Estimación |
|------|-------------|--------|------------|
| 0.6.1 | Plan restructure | ✅ DONE | PLAN |
| 0.6.2 | Extract facturacion_ec to separate repo | ⬜ Pending | 2h |
| 0.6.3 | Remove demo modules (accounting_basic, etc.) | ⬜ Pending | 30min |
| 0.6.4 | Update core settings (limpiar modules/) | ⬜ Pending | 1h |
| 0.6.5 | Remove static modules_enabled.py | ⬜ Pending | 30min |
| 0.6.6 | Reorganize workspace directory | ⬜ Pending | 1h |
| 0.6.7 | Update documentation | ⬜ Pending | 2h |
| 0.6.8 | Update PAUL for multi-repo | ⬜ Pending | 30min |
| 0.6.9 | Validate everything works | ⬜ Pending | 1h |

**Total estimado:** ~9 horas

---

## 📊 State Before Phase 0.6

```
repos/erp-nexus/
├── apps/                      # Core ✅
├── modules/                   # ❌ Contiene módulos (mal)
│   ├── facturacion_ec/        # Debería estar en repo separado
│   ├── accounting_basic/      # Demo — eliminar
│   └── inventory_basic/       # Demo — eliminar
├── erp_nexus/modules_enabled.py  # ❌ Estático, debería ser dinámico
└── manage.py                  # Core ✅
```

**Problema:** Core y módulos mezclados en un solo repo → No hay true modularity.

---

## 📈 State After Phase 0.6 (OBJETIVO)

```
repos/
├── erp-nexus/                 # CORE ONLY
│   ├── apps/                  # 11 core apps
│   ├── erp_nexus/
│   ├── docker/
│   ├── pyproject.toml
│   ├── .paul/                 # PAUL para core
│   └── README.md              # Solo core docs
│
├── facturacion_ec/            # MÓDULO INDEPENDIENTE (nuevo repo)
│   ├── facturacion_ec/
│   ├── tests/
│   ├── README.md              # Docs del módulo
│   └── .paul/                 # PAUL para módulo (futuro)
│
└── (otros módulos futuros)
```

**Resultado:**
- ✅ Core limpio, sin código de módulos
- ✅ Cada módulo en su repo
- ✅ Marketplace puede instalar desde Git URLs
- ✅ Versionado independiente

---

## 🔄 Dependencies and Blockers

### **Dependencies:**
- Phase 0.6 NO depende de nada (foundation)
- Phase 1.1 (services) depende de Phase 0.6 completado

### **Blockers:**
- ❌ No borrar facturacion_ec hasta tener repo separado (Task 0.6.2 first)
- ❌ No modificar settings hasta limpiar imports (Task 0.6.4)
- ❌ No eliminar modules_enabled.py hasta tener dynamic loader (Task 0.6.5)

---

## 📋 Acceptance Criteria (Summary)

- [ ] `repos/facturacion_ec/` existe como directorio Git independiente
- [ ] `repos/erp-nexus/modules/` NO existe (vacío o eliminado)
- [ ] Demo modules removidos (`accounting_basic`, `inventory_basic`, `demo_flow`)
- [ ] `modules_enabled.py` eliminado o convertido a dinámico
- [ ] Ningún `from modules.` import en core apps
- [ ] Tests core pasan sin modules/
- [ ] Documentación actualizada (MULTI_REPO_STRUCTURE.md)
- [ ] PAUL STATE actualizado (scope clarificado)

---

## 🗺️ Roadmap Impact

**Esta phase reestructura el proyecto completo.**

**Antes (monorepo):**
```
erp-nexus/
├── core + facturacion_ec + accounting_basic + ...
```

**Después (multi-repo):**
```
repos/
├── erp-nexus/        (core framework)
├── facturacion_ec/   (módulo Ecuador)
├── inventory/        (futuro)
└── sdk-nexus/        (futuro)
```

**WORK_PLAN.md** actualizado:
- M0: Core Foundation ✅ (ya)
- M0.5: Graph Unify ⏸️ (pausado hasta restructure)
- M1: facturacion_ec complete → **AHORA ES REPO SEPARADO**
- M2: Marketplace engine → **EN CORE**
- M3: inventory module → **REPO SEPARADO**

---

## 📝 Notes

**Why multi-repo now?**
Porque el usuario explicitó: "el modulo de facturacion_ec debe ser una extension del modulo de facturacion_core y debe estar aparte en otro repositorio".

**Riesgo principal:**
- Pérdida de historial git de facturacion_ec si hacemos copy (no subtree)
- Solución: Usar `git subtree split` para mantener historial

**Git strategy:**
```bash
# En erp-nexus:
git subtree split --prefix=modules/facturacion_ec -b facturacion_ec-split

# Crear nuevo repo
mkdir ../facturacion_ec
cd ../facturacion_ec
git init
git pull /home/wcun/.openclaw/workspace/repos/erp-nexus facturacion_ec-split
# Ahora tiene historial completo
```

---

## 🔗 References

- PAUL Phase: `00-01-REPO-RESTRUCTURE.md`
- Graph Health: `GRAPH_HEALTH.md` (validator integration pendiente)
- Module Spec: `MODULE_SPEC.md` (para facturacion_ec repo)
- Multi-Repo Guide: `MULTI_REPO_STRUCTURE.md` (crear en Task 0.6.7)

---

**Estado:** PLAN completado, esperando ejecución (/paul:apply)  
**Prioridad:** 🔴 CRÍTICO — Debe hacerse antes de continuar con facturacion_ec development
