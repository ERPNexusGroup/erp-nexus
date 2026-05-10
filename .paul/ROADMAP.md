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

**Phases:**
- **Phase 0.6.1** — Hybrid Architecture definida ✅
- **Phase 0.6.2** — facturacion_ec → apps/facturacion ✅
- **Phase 0.6.3** — Eliminar demo modules ✅
- **Phase 0.6.4** — Clean core settings ✅
- **Phase 0.6.5** — Crear apps/inventory ✅
- **Phase 0.6.6** — Crear sales, purchases, notifications, print_manager ✅
- **Phase 0.6.7** — Docs actualizadas ✅
- **Phase 0.6.8** — Graph rebuild ✅
- **Phase 0.6.9** — Validation ✅

**Outcome:** ERP Nexus funcional out-of-the-box con:
- Facturación SRI ✅
- Inventario ✅
- Ventas ✅
- Compras ✅
- Notificaciones ✅
- Print Manager ✅

**Total:** 17 Django apps (11 core + 6 essential)

---

### **M2 — Marketplace & Plugin System** 📋 PLANNED
**Target:** Semana 4-5
**Status:** ⏳ Next Up

**Objective:** Sistema de marketplace para módulos opcionales.

**Phases:**
- **Phase 1.1** — Marketplace Foundation (catalog, install/uninstall) — ⬜ PLAN
- **Phase 1.2** — Admin UI + REST API — ⬜ PLAN
- **Phase 1.3** — GitHub auto-discovery — ⬜ PLAN
- **Phase 1.4** — Version management + dependencies — ⬜ PLAN

**Success:** Admin puede instalar `hr`, `crm`, `accounting_adv` desde GitHub con un click.

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

**Sprint:** M1 (Hybrid Restructure) — COMPLETADO ✅

**Upcoming Sprint:** M2 (Marketplace) — Inicio inmediato

---

## 🔮 Future Vision (M5+)

- **M5 — AI Integration:** OCR para facturas, predictive inventory
- **M6 — E-commerce Sync:** WooCommerce/Shopify connectors
- **M7 — Accounting:** Integration with local accounting software (Ecuador)
- **M8 — POS Module:** Point of Sale for retail

---

**Last milestone completion:** M0, M1 ✅
**Current milestone:** M2 (Marketplace) — NEXT
**Estimated velocity:** 2-3 phases/semana
