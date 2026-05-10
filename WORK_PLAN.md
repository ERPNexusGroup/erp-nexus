# 📈 Roadmap — ERP Nexus Ecosystem

**Versión:** 1.0.0-alpha  
**Fecha:** 2026-05-10  
**Estrategia:** Multi-Repo Architecture

---

## 🎯 Filosofía del Roadmap

ERP Nexus no es un solo proyecto. Es un **ecosistema** de repos independientes:

```
ERP Nexus Ecosystem
├── erp-nexus/          ← Core Framework (este roadmap)
├── facturacion_ec/     ← Módulo Ecuador (roadmap separado)
├── inventory/          ← Módulo Inventario (roadmap separado)
├── sdk-nexus/          ← SDK (roadmap separado)
├── nexus-cli/          ← CLI (roadmap separado)
└── nexus-marketplace/  ← Marketplace (roadmap separado)
```

**Este roadmap cubre SOLO el CORE (`erp-nexus/`).**

---

## 📊 Timeline Core (erp-nexus repo)

```
Año 2026
Mes:  5    6    7    8    9    10   11   12
      ────────────────────────────────────────────
v0.5.0  ████
v0.6.0      ████████████
v0.7.0              ████████████
v0.8.0                      ████████████
v0.9.0                              ████████████
v1.0.0                                    ████████████
      ────────────────────────────────────────────
      May  Jun  Jul  Aug  Sep  Oct  Nov  Dec
```

---

## 🏆 Milestones — Core Framework

### **M0 — Foundation (v0.5.0)** ✅ COMPLETADO
**Semana:** 1 (2026-05-04)  
**Estado:** ✅ Done

**Entregables:**
- [x] 11 core Django apps
- [x] Multi-tenant middleware (`ActiveCompanyMiddleware`)
- [x] ModuleRegistry básico
- [x] Event Bus (`core_events`)
- [x] API layer (Django Ninja)
- [x] Audit log system
- [x] Dashboard admin
- [x] Settings base (dev/prod)
- [x] Docker Compose stack

---

### **M0.5 — Graphify Integration (v0.5.x)** 🔄 IN PROGRESS
**Semana:** 3 (2026-05-10)  
**Estado:** 🔄 En progreso

**Objetivo:** Integrar knowledge graph para navigation y analysis.

**Fases:**
- **P0.5.1** — Graphify analysis completado ✅
  - 1,875 nodos, 2,300 edges, 209 comunidades
  - 5 nodos aislados críticos (validator.py)
- **P0.5.2** — Graph Unify (integrar validator) ⏸️ Pausado hasta restructure
  - Integrar validator en API endpoints
  - Verificar EventBus usage
  - Regenerar grafo

**Bloqueado por:** Phase 0.6 (repo restructure) debe ir primero.

---

### **M0.6 — Multi-Repo Restructure (v0.6.0)** 🔥 NEXT
**Semanas:** 4-5 (2026-05-17 → 2026-05-31)  
**Estado:** ⏳ Planificado

**Objetivo:** Separar core de módulos. Extraer facturacion_ec a repo propio.

**Fases:**
- **Phase 0.6.1** — Plan (✅ completado)
- **Phase 0.6.2** — Extract facturacion_ec → `repos/facturacion_ec/`
- **Phase 0.6.3** — Remove demo modules (accounting_basic, inventory_basic)
- **Phase 0.6.4** — Clean core settings
- **Phase 0.6.5** — Eliminate static `modules_enabled.py`
- **Phase 0.6.6** — Reorganize workspace
- **Phase 0.6.7** — Update docs
- **Phase 0.6.8** — Update PAUL
- **Phase 0.6.9** — Validate everything

**Deliverables:**
- `erp-nexus/` → Solo core (11 apps)
- `facturacion_ec/` → Repo independiente en `repos/`
- `MULTI_REPO_STRUCTURE.md` — Guía completa
- Tests core pasan sin modules/ locales

**Riesgos:**
- ⚠️ Pérdida de historial git (mitigar con `git subtree split`)
- ⚠️ Dependencias rotas (validar imports)
- ⚠️ Despliegue interrumpido (rollback plan)

---

### **M1 — Marketplace Engine Complete (v0.7.0)**
**Semanas:** 6-7 (2026-06-07 → 2026-06-21)  
**Estado:** 📋 Planeado

**Objetivo:** Sistema de marketplace funcional para instalar/desinstalar módulos.

**Fases:**
- **Phase 1.1** — ModuleCatalog (catálogo DB de módulos disponibles)
- **Phase 1.2** — ModuleInstaller mejorado (download + verify + install)
- **Phase 1.3** — Module activation/deactivation UI
- **Phase 1.4** — Update checks (notify module updates)
- **Phase 1.5** — License management (free/paid tiers)

**Deliverables:**
- Admin UI: Marketplace → Catalogo → Install
- CLI: `python manage.py install_module --git <url>`
- DB schema: `core_marketplace_ModuleCatalogItem`, `Module`
- Auto-discovery: GitHub repos con `__meta__.py`

**Success criteria:**
- Instalar `facturacion_ec` desde GitHub oficial
- Desinstalar sin romper dependencias
- Actualizar módulo a nueva versión

---

### **M2 — SDK & CLI (v0.8.0)**
**Semanas:** 8-9 (2026-06-28 → 2026-07-12)  
**Estado:** 📋 Planeado

**Objetivo:** Herramientas para desarrolladores de módulos.

**Fases:**
- **Phase 2.1** — SDK (`sdk-nexus` repo)
  - `sdk-nexus create` — scaffolding
  - `sdk-nexus validate` — validación estructura
  - `sdk-nexus package` — empaquetar .npkg
- **Phase 2.2** — CLI (`nexus-cli` repo)
  - `nexus install <module>`
  - `nexus list`
  - `nexus update`
  - `nexus marketplace search`

**Deliverables:**
- `sdk-nexus` PyPI package
- `nexus-cli` binary (PyInstaller o Go)
- Guías de desarrollo

---

### **M3 — Facturacion_ec Stable (v0.9.0)** 📦 Módulo
**Semanas:** 10-12 (2026-07-19 → 2026-08-09)  
**Estado:** 📋 Planeado (en su propio repo)

**Nota:** Este milestone es PARA EL MÓDULO `facturacion_ec`, NO del core.
Ver `facturacion_ec/ROADMAP.md` para detalle.

**Módulo facturacion_ec milestones:**
- M1: Services layer (XML, signature, SRI) — Semanas 2-4
- M2: API completion + integration — Semanas 5-6
- M3: Tests + validation — Semana 7
- M4: Extract to separate repo — Semana 8 (ya hecho por core Phase 0.6)
- M5: Stable release v1.0.0 — Semana 12

---

### **M4 — Core v1.0.0 Release (v1.0.0)** 🎯 FINAL
**Semana:** 12 (2026-08-16)  
**Estado:** 📋 Planeado

**Objetivo:** Core estable, documentado, con módulos oficiales.

**Checklist:**
- [ ] Core sin bugs críticos (0 P0)
- [ ] Test coverage >80%
- [ ] CI/CD funcionando (GitHub Actions)
- [ ] Documentación completa (INSTALL, DEVELOPMENT, API_REFERENCE)
- [ ] Al menos 2 módulos oficiales publicados (facturacion_ec + inventory)
- [ ] Demo desplegada en Railway/Render
- [ ] GitHub Discussions + Issues templates
- [ ] CHANGELOG completo
- [ ] SemVer asegurado (no breaking changes post-1.0)

**Entregable:** Release v1.0.0 en GitHub → Adopción inicial.

---

## 📋 Cross-Repo Dependencies

```
Phase 0.6 (este phase)  → erp-nexus core
                            └── Extrae facturacion_ec → nuevo repo

Phase 1.1 (services)     → facturacion_ec repo (su propio PAUL)
                            Depende de: erp-nexus >= 0.6.0

Phase 2.1 (SDK)          → sdk-nexus repo
                            Depende de: erp-nexus >= 0.7.0

Phase 3.1 (inventory)    → inventory repo
                            Depende de: erp-nexus >= 0.7.0
```

**Matrix de compatibilidad (futuro):**

| Core \ Módulo | facturacion_ec v0.1 | facturacion_ec v0.2 | inventory v0.1 |
|---------------|--------------------|--------------------|----------------|
| v0.5.x        | ✅                 | ❌                 | ❌             |
| v0.6.x        | ✅                 | ⚠️ beta            | ❌             |
| v0.7.x        | ✅                 | ✅                 | ✅             |
| v1.0.x        | ✅                 | ✅                 | ✅             |

---

## 📊 Métricas de Progreso (Core)

| Métrica | Actual (v0.5.0) | v0.6.0 Target | v1.0.0 Target |
|---------|----------------|---------------|---------------|
| Apps core | 11 | 11 | 11 |
| Test coverage | ~20% | >50% | >80% |
| Nodos aislados Graphify | 61 (3%) | <30 (<2%) | <10 (<1%) |
| Módulos extraídos | 0 | 1 (facturacion_ec) | 3+ |
| Docs completas | 70% | 80% | 100% |
| CI/CD | No | GitHub Actions | GitHub Actions |
| Docker image size | — | <200MB | <150MB |

---

## 🔄 Workflow Semanal (Core Devs)

```
Lunes
├── Revisar PAUL progress (.paul/STATE.md)
├── Sprint planning (qué tasks esta semana)
└── Actualizar ROADMAP si hay bloqueos

Martes-Jueves
├── Desarrollo focused
├── Commits diarios (conventional commits)
├── Tests locales (pytest -xvs)
└── Graphify update (si cambios grandes)

Viernes
├── PR review (si hay colaboradores)
├── Actualizar WORK_PLAN.md con progreso
├── Documentar decisiones (ADR/)
└── PAUL unify (cerrar loops phases)
```

---

## 📈 Release Cadence

```
v0.5.x  — Foundation (actual)
   ├── Bug fixes
   └── Pequeñas features

v0.6.x  — Multi-repo restructure
   ├── Breaking change: modules fuera del core
   └── Migration guide

v0.7.x  — Marketplace completo
   ├── Install/Uninstall modules
   └── Module lifecycle

v0.8.x  — SDK + CLI
   ├── Developer tooling
   └── Boilerplate generation

v0.9.x  — Stability + polish
   ├── Bugfixing
   ├── Test coverage >80%
   └── Performance optimization

v1.0.0 — Stable release
   ├── No breaking changes desde v0.9.x
   ├── Docs 100%
   └── Production-ready
```

---

## 🚨 Bloqueos y Riesgos

| Riesgo | Probabilidad | Impacto | Mitigación |
|--------|--------------|---------|------------|
| **facturacion_ec extraction falla** | Media | Alto | Backup, rollback plan, git subtree |
| **Módulos dependen de core APIs que cambian** | Media | Alto | SemVer, deprecation warnings, 2-cycle policy |
| **Marketplace no adoptado** | Baja | Medio | Docs claros, ejemplos, sdk-nexus facilita |
| **Community no contribuye** | Media | Bajo | Open source + buen onboarding |
| **Performance en multi-tenant** | Media | Alto | Index DB, query optimization early |

---

## 💡 Decisiones Pendientes

1. **¿Marketplace como servicio cloud o self-hosted?**
   - Opción A: Marketplace central (marketplace.erpnexus.ec) — más control
   - Opción B: Self-hosted (cada instancia tiene su catálogo local) — más descentralizado
   - **Pendiente:** Decidir para v1.0

2. **¿Module packages (.npkg) o Git clones directos?**
   - .npkg: signed, versioned, distributable
   - Git clone: simple, sin empaquetado
   - **Pendiente:** Implementar .npkg en v0.8.x

3. **¿Core monolith o microservices?**
   - Actual: monolith (Django)
   - Futuro: Separar Event Bus, ModuleRegistry en services?
   - **Pendiente:** Evaluar en v2.0

---

## 📞 Contacto y Canales

- **Core Issues:** `github.com/ERPNexus/erp-nexus/issues`
- **Módulo Issues:** Respectivo repo (facturacion_ec/issues, etc.)
- **Discussions:** `github.com/ERPNexus/.github/discussions`
- **Telegram:** @erpnexus_support (futuro)

---

## 🗺️ Visual Timeline

```
2026-05-10  [M0.5] Graphify integration
2026-05-17  [M0.6] Multi-repo restructure ─┐
2026-06-07  [M1]   Marketplace engine      │ Core releases
2026-06-28  [M2]   SDK + CLI               │ (cada 2-3 semanas)
2026-07-19  [M3]   facturacion_ec v1.0     │  ──────────────
2026-08-16  [M4]   Core v1.0.0 release     ┘
                ↑
                │  Módulo facturacion_ec paralelo
                └── Su propio roadmap (facturacion_ec/ROADMAP.md)
```

---

**Última actualización:** 2026-05-10 — Phase 0.6 plan completado
