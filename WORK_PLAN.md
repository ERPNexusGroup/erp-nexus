# 📈 Roadmap — ERP Nexus Core (Framework Only)

**Versión:** 1.0.0-alpha  
**Fecha:** 2026-05-10  
**Estrategia:** Plugin-based Architecture (Core + Módulos Independientes)

---

## 🎯 Filosofía del Roadmap

**ESTE ROADMAP CUBRE SOLO EL CORE (`erp-nexus/` repo).**

Los plugins (facturacion_ec, inventory, sales) tienen sus propios roadmaps en sus repositorios.

```
ERP Nexus Ecosystem Roadmaps:
├── erp-nexus/          ← ESTE DOCUMENTO (Core framework)
├── facturacion_ec/     ← Roadmap separado (módulo Ecuador)
├── inventory/          ← Roadmap separado (futuro)
└── sdk-nexus/          ← Roadmap separado (SDK)
```

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
- [x] Event Bus básico (`core_events`)
- [x] API layer (Django Ninja)
- [x] Audit log system
- [x] Settings base (dev/prod)
- [x] Docker Compose stack
- [x] Documentación inicial (14 archivos)

---

### **M0.5 — Graphify Integration (v0.5.x)** 🔄 PAUSADO
**Semana:** 3 (2026-05-10)  
**Estado:** ⏸️ Pausado hasta completar M0.6

**Objetivo:** Integrar knowledge graph para navegación y análisis.

**Hallazgos:**
- 1,875 nodos · 2,300 edges (81% extraídos, 18% inferidos)
- 61 nodos aislados (3%)
- **Crítico:** `validator.py` (5 nodos) — funciones no usadas
- **Falso positivo:** `bus.py` (6 nodos) — EventBus sí se usa

**Bloqueado por:** M0.6 (restructure) debe ir primero.

**Post-M0.6:** Re-evaluar grafo (facturacion_ec ya no en core).

---

### **M0.6 — Multi-Repo Restructure (v0.6.0)** 🔥 PRÓXIMO
**Semanas:** 4-5 (2026-05-17 → 2026-05-31)  
**Estado:** 📋 Planificado (PLAN completado)

**Objetivo:** Separar core de módulos. Extraer `facturacion_ec` a repo propio.

**Fases (9 tasks):**
- Phase 0.6.1 — Plan ✅ (completado)
- Phase 0.6.2 — Extract `facturacion_ec/` → `repos/facturacion_ec/`
- Phase 0.6.3 — Remove demo modules (`accounting_basic`, `inventory_basic`, `demo_flow`)
- Phase 0.6.4 — Clean core settings
- Phase 0.6.5 — Eliminate static `modules_enabled.py`
- Phase 0.6.6 — Reorganize workspace
- Phase 0.6.7 — Update docs
- Phase 0.6.8 — Update PAUL
- Phase 0.6.9 — Validate everything

**Deliverables:**
- `erp-nexus/` → Solo core (11 apps)
- `facturacion_ec/` → Repo independiente
- `MULTI_REPO_STRUCTURE.md` — Guía completa
- Tests core pasan sin modules/ locales

**Riesgos:**
- ⚠️ Pérdida de historial git (usar `git subtree split`)
- ⚠️ Dependencias rotas (validar imports)

**Documentación:**
- [`MULTI_REPO_STRUCTURE.md`](./MULTI_REPO_STRUCTURE.md)
- PAUL Phase `00-01-REPO-RESTRUCTURE.md`

---

### **M1 — Marketplace Engine (v0.7.0)** 📋 PLANEADO
**Semanas:** 6-7 (2026-06-07 → 2026-06-21)  
**Estado:** 📋 Planeado

**Objetivo:** Sistema completo de marketplace para instalar/desinstalar plugins.

**Fases:**
- Phase 1.1 — ModuleCatalog (catálogo DB)
- Phase 1.2 — ModuleInstaller mejorado (download + verify + install)
- Phase 1.3 — Module activation/deactivation UI
- Phase 1.4 — Update checks
- Phase 1.5 — License management (free/paid)

**Deliverables:**
- Admin UI: Marketplace catalogo
- CLI: `python manage.py install_module --git <url>`
- DB: `ModuleCatalogItem`, `Module` models
- Auto-discovery: GitHub repos con `__meta__.py`

**Success:** Instalar `facturacion_ec` desde GitHub oficial.

---

### **M2 — SDK & CLI (v0.8.0)** 📋 PLANEADO
**Semanas:** 8-9 (2026-06-28 → 2026-07-12)  
**Estado:** 📋 Planeado

**Objetivo:** Herramientas para desarrolladores de plugins.

**Fases:**
- Phase 2.1 — SDK (`sdk-nexus` repo)
  - `sdk-nexus create` — scaffolding
  - `sdk-nexus validate` — validación
  - `sdk-nexus package` — empaquetar .npkg
- Phase 2.2 — CLI (`nexus-cli` repo)
  - `nexus install <plugin>`
  - `nexus list`
  - `nexus marketplace search`

**Deliverables:**
- `sdk-nexus` PyPI package
- `nexus-cli` binary
- Developer guides

---

### **M3 — Core v1.0.0 Stable (v1.0.0)** 🎯 FINAL
**Semana:** 12 (2026-08-16)  
**Estado:** 📋 Planeado

**Objetivo:** Core estable, documentado, con plugins oficiales.

**Checklist:**
- [ ] Core sin bugs críticos (0 P0)
- [ ] Test coverage >80%
- [ ] CI/CD funcionando (GitHub Actions)
- [ ] Docs 100% (INSTALL, DEVELOPMENT, API_REFERENCE)
- [ ] Module system completo (install/upgrade/uninstall)
- [ ] Al menos 2 plugins oficiales disponibles (facturacion_ec + inventory)
- [ ] Demo desplegada
- [ ] CHANGELOG completo
- [ ] SemVer asegurado

**Entregable:** Release v1.0.0 — Adopción inicial.

---

## 📋 Facturacion_ec Plugin — Milestone Separado

**IMPORTANTE:** `facturacion_ec` tiene su propio roadmap (en su repositorio).

**Sin embargo, coordenadas temporales:**

| Fase | Plugin facturacion_ec | Core dependency |
|------|----------------------|----------------|
| P0 — Setup | v0.5.0 — Models + Admin | Core v0.5.0 ✅ |
| P1 — Services | v0.6.0 — XML, Signature, SRI | Core v0.5.0 ✅ |
| P2 — Integration | v0.7.0 — API completion | Core v0.6.0 |
| P3 — Stable | v1.0.0 — Release | Core v0.7.0 |

**Cuando core lanza v0.6.0 (restructure), facturacion_ec se extrae a repo separado** y continúa su desarrollo en paralelo.

---

## 🔄 Dependencies entre Core y Plugins

```
Core erp-nexus v0.5.x  ───→ Compatible con plugins v0.5.x
Core erp-nexus v0.6.x  ───→ Requiere plugins >= 0.6.0
Core erp-nexus v1.0.0  ───→ Compatible con plugins v1.0.0
```

**Matrix de compatibilidad:**

| Core \ Plugin | facturacion_ec v0.5 | facturacion_ec v0.6 | inventory v0.1 |
|---------------|--------------------|--------------------|---------------|
| v0.5.x        | ✅                 | ❌                 | ❌            |
| v0.6.x        | ✅                 | ⚠️ beta            | ❌            |
| v0.7.x        | ✅                 | ✅                 | ✅            |
| v1.0.x        | ✅                 | ✅                 | ✅            |

---

## 📊 Métricas de Progreso (Core)

| Métrica | v0.5.0 (actual) | v0.6.0 Target | v1.0.0 Target |
|---------|-----------------|---------------|---------------|
| Core apps | 11 | 11 | 11 |
| Test coverage | ~20% | >50% | >80% |
| Nodos aislados Graphify | 61 (3%) | <30 (<2%) | <10 (<1%) |
| Plugins extraídos | 0 | 1 (facturacion_ec) | 3+ |
| Docs completas | 70% | 80% | 100% |
| CI/CD | No | GitHub Actions | ✅ |
| Docker image size | — | <200MB | <150MB |

---

## 🚨 Bloqueos y Riesgos

| Riesgo | Probabilidad | Impacto | Mitigación |
|--------|--------------|---------|------------|
| **Plugin extraction falla** | Media | Alto | Backup, `git subtree split`, rollback plan |
| **Core change rompe plugins** | Media | Alto | SemVer, deprecation warnings, 2-cycle policy |
| **Plugins no se adoptan** | Baja | Medio | Docs excelentes, ejemplos, sdk-nexus fácil |
| **Community lenta** | Media | Bajo | Open source + buen onboarding |

---

## 💡 Decisiones Pendientes

1. **¿Marketplace como servicio cloud o self-hosted?**
   - A: Central (marketplace.erpnexus.ec) — más control
   - B: Self-hosted (cada instancia su catálogo) — más descentralizado
   - Pendiente para v0.7.x

2. **¿Plugin packages (.npkg) o Git clones?**
   - .npkg: signed, versioned, distributable
   - Git clone: simple
   - Decisión en v0.8.x (SDK)

3. **¿Core monolith o microservices?**
   - Actual: monolith (Django)
   - Futuro: ¿Separar Event Bus, ModuleRegistry en microservices?
   - Evaluar en v2.0

---

## 📞 Canales

- **Core issues:** `github.com/ERPNexus/erp-nexus/issues`
- **Plugin issues:** Respectivo repo (facturacion_ec/issues, …)
- **Discussions:** `github.com/ERPNexus/.github/discussions`

---

**Última actualización:** 2026-05-10 — Phase 0.6 plan completado, esperando ejecución
