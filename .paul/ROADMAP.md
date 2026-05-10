# ERP Nexus — Roadmap (PAUL)

**Version:** 1.0.0-alpha
**Last Updated:** 2026-05-10

---

## 🎯 Milestones

### **M0 — Core Foundation** ✅ COMPLETED
**Target:** Semana 1
**Status:** ✅ Done (2026-05-10)

**Deliverables:**
- [x] 11 core Django apps (framework)
- [x] Multi-tenant middleware
- [x] Settings base (dev + prod)
- [x] Docker stack (PostgreSQL + Redis)
- [x] Project documentation (15+ docs)

---

### **M1 — Hybrid Restructure — Essential Modules** ✅ COMPLETED
**Target:** Semana 2
**Status:** ✅ Done (2026-05-10)

**Objective:** Integrar módulos esenciales en core (no plugins).

**Phases (9 tasks):**

| Phase | Descripción | Estado |
|-------|-------------|--------|
| 0.6.1 | Definir arquitectura híbrida | ✅ |
| 0.6.2 | Mover `facturacion_ec/` → `apps/facturacion/` | ✅ |
| 0.6.3 | Eliminar módulos demo | ✅ |
| 0.6.4 | Clean core settings | ✅ |
| 0.6.5 | Crear `apps/inventory/` | ✅ |
| 0.6.6 | Crear sales, purchases, notifications, print_manager | ✅ |
| 0.6.7 | Update documentation | ✅ |
| 0.6.8 | Rebuild graph + finalize state | ✅ |
| 0.6.9 | Validation | ✅ |

**Outcome:** ERP Nexus funcional out-of-the-box con 6 business modules.

**Total:** 17 Django apps (11 core + 6 essential)

---

### **M2 — Marketplace & Plugin System** ✅ COMPLETED
**Target:** Semana 4-5
**Status:** ✅ Done (2026-05-10)

**Objective:** Sistema de marketplace funcional para instalar módulos.

**Phases:**
- **Phase 1.1** — Marketplace Foundation (catalog, install/uninstall, API, Admin UI) — ✅ DONE
- **Phase 1.2** — Marketplace UI + License management — ⬜ PLAN
- **Phase 1.3** — GitHub auto-discovery + sync — ⬜ PLAN
- **Phase 1.4** — Version management + dependencies solver — ⬜ PLAN

**Success:** Admin puede instalar `hr`, `crm`, `project_mgmt` desde GitHub con un click.

---

### **M3 — Production Ready** 📋 PLANNED
**Target:** Semana 6-7
**Status:** ⬜ Planned

**Objective:** Despliegue en producción.

**Phases:**
- **Phase 2.1** — Docker production image (multi-stage build)
- **Phase 2.2** — PostgreSQL + Redis (production config)
- **Phase 2.3** — Celery workers (async notifications, SRI auto-send)
- **Phase 2.4** — SSL + Nginx reverse proxy
- **Phase 2.5** — Monitoring (Prometheus + Grafana + Sentry)

**Success:** `docker compose up -d` levanta ERP completo en producción.

---

### **M4 — Advanced Features** 📋 Planned
**Target:** Semana 8-10
**Status:** ⬜ Planned

**Objective:** Features avanzadas.

**Phases:**
- **Phase 3.1** — GraphQL API (para frontend complejo)
- **Phase 3.2** — Mobile app API optimizada
- **Phase 3.3** — Multi-company enhancements
- **Phase 3.4** — Reporting engine (PDF reports, Excel export)

**Success:** ERP con API moderna y reporting avanzado.

---

## 📊 Current Sprint

**Sprint:** M2 (Marketplace Foundation 1.1) — ✅ COMPLETADO

**Upcoming Sprint:** M2 Phase 1.2 — Marketplace UI + License Management

---

## 🔮 Future Vision (M5+)

- **M5 — AI Integration:** OCR para facturas, predictive inventory
- **M6 — E-commerce Sync:** WooCommerce/Shopify connectors
- **M7 — Accounting:** Integration with local accounting software (Ecuador)
- **M8 — POS Module:** Point of Sale for retail

---

**Last milestone completion:** M0, M1, M2-1.1 ✅
**Current milestone:** M2 Phase 1.2 — NEXT
**Estimated velocity:** 2-3 phases/semana
