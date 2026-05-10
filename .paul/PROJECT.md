# ERP Nexus — PAUL Project Context

**Why this project exists:**  
ERP Nexus nace de la necesidad de un ERP modular, instalable por módulos, que permita a empresas ecuatorianas (y latinoamérica) tener un sistema a medida sin el overhead de un ERP monolítico tradicional.

**What problem it solves:**
- Los ERP tradicionales son monolíticos: todo o nada
- Modificar un módulo requiere understanding de todo el codebase
- Actualizaciones = deploy completo (riesgoso)
- Módulos de terceros difíciles de integrar

**ERP Nexus solution:**
- Core mínimo (users, companies, permissions, marketplace)
- Módulos como plugins independientes
- Instala solo lo que necesitas
- Actualiza módulos individualmente
- Cualquier dev puede crear módulos

---

## 🎯 Project Value

**Para empresas:**
- Paga solo por módulos que usas
- Implementación incremental (empieza con facturación, luego inventario)
- Customizable sin romper actualizaciones

**Para desarrolladores:**
- Framework estructurado para construir ERP modules
- Marketplace para publicar/distribuir
- Standards claros (CODING_STANDARDS, MODULE_SPEC)
- Tests + CI/CD integrados

**Para el mercado:**
- Open source (MIT) — sin licencias caras
- Enfoque Ecuador (facturación SRI nativa)
- Expandible a Latinoamérica

---

## 🎯 Success Criteria

**v1.0.0 (12 semanas):**
- ✅ Core estable (11 apps, 0 bugs críticos)
- ✅ Módulo facturacion_ec completo (XML, firma, SRI)
- ✅ Módulo inventory funcional
- ✅ Módulo sales básico
- ✅ Docker stack funcionando
- ✅ Documentación completa
- ✅ 80% test coverage core

**v2.0 (Año 2):**
- 100+ empresas usando ERP Nexus
- 10+ módulos oficiales
- Marketplace community con 20+ módulos
- Frontend React SPA

---

## 🏗️ Current State (2026-05-10)

**Completed:**
- Core Django configurado (11 apps)
- Multi-tenant middleware
- ModuleRegistry básico
- facturacion_ec models + admin + API básica
- Documentación exhaustiva (14 documentos)
- ADRs (5 decisiones arquitectónicas)

**In Progress:**
- facturacion_ec services (XML, signature, SRI client)
- Multi-company validation en API endpoints
- Tests unitarios

**Not Started:**
- Extraer facturacion_ec a repo separado
- inventory module
- sales module
- Docker production build
- CI/CD pipeline

---

## 🧭 Graphify Context

**Knowledge Graph Stats:**
- 1,875 nodes · 2,300 edges · 209 communities
- Corpus: 240 files, ~50,619 words
- Extraction: 81% · Inferred: 19%

**Key Hubs:**
1. `JWTAuth` — Authentication backbone
2. `Product` — Inventory/product domain
3. `ModuleCatalogItem` — Marketplace engine
4. `Invoice` — Core billing entity
5. `EventBus` — Inter-module communication
6. `AuditLog` — Compliance/security

**Implications for Development:**
- Centralized auth (JWT) already designed — use it
- EventBus is the integration pattern — subscribe/publish
- All business entities must have `company` FK
- ModuleRegistry controls activation — respect it

---

## 📚 References

- [`WORK_PLAN.md`](../WORK_PLAN.md) — 12-week roadmap
- [`ARCHITECTURE.md`](../ARCHITECTURE.md) — Technical deep-dive
- [`CODING_STANDARDS.md`](../CODING_STANDARDS.md) — Code rules
- [`API_REFERENCE.md`](../API_REFERENCE.md) — API docs
- [`DOCS_INDEX.md`](../DOCS_INDEX.md) — All documentation index
- [Graph Report](../graphify-out/GRAPH_REPORT.md) — Full graph analysis
- [Graph HTML](../graphify-out/graph.html) — Interactive visualization

---

**PAUL PROJECT.md:** Initialized  
**Next:** Run `/paul:plan` to create executable plan for Phase 1
