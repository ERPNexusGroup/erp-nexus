# 📈 Roadmap — ERP Nexus Core (Framework + Essential Modules)

**Versión:** 1.0.0-alpha  
**Fecha:** 2026-05-10  
**Estrategia:** Hybrid Architecture (Core + Essential Modules + Optional Plugins)

---

## 🎯 Filosofía del Roadmap

**ESTE ROADMAP CUBRE SOLO EL CORE (`erp-nexus/` repo).**

El core contiene:
- **Framework** (11 Django apps)
- **Essential Business Modules** (8 módulos integrados: facturacion, inventory, sales, purchases, notifications, permissions, dashboard, print_manager)

Los **plugins opcionales** (hr, crm, projects, pos, …) tienen sus propios roadmaps en sus repositorios.

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

## 🏆 Milestones — ERP Nexus Core

### **M0 — Foundation (v0.5.0)** ✅ COMPLETADO
**Semana:** 1 (2026-05-04)  
**Estado:** ✅ Done

**Entregables:**
- [x] 11 core Django apps (framework)
- [x] Multi-tenant middleware (`ActiveCompanyMiddleware`)
- [x] Event Bus básico (`core_events`)
- [x] API layer (Django Ninja)
- [x] Audit log system
- [x] Settings base (dev/prod)
- [x] Docker Compose stack
- [x] Documentación inicial (10+ archivos)

---

### **M0.5 — Essential Modules Integration (v0.5.x)** 🔄 EN PROGRESO
**Semana:** 3 (2026-05-10)  
**Estado:** 🔄 In Progress

**Objetivo:** Integrar los 8 módulos esenciales de negocio en el core.

**Módulos a integrar:**
1. `facturacion` — Facturación electrónica SRI Ecuador
2. `inventory` — Gestión de inventario
3. `sales` — Ventas y cotizaciones
4. `purchases` — Compras y proveedores
5. `notifications` — Notificaciones (email, Telegram)
6. `permissions` — Permisos extendidos
7. `dashboard` — Dashboard principal
8. `print_manager` — Impresión PDF

**Estado actual:**
- `facturacion_ec/` existe en `modules/` (a mover a `apps/facturacion/`)
- Resto de módulos: pendiente mover/crear

**Esta milestone incluye:**
- Mover módulos de `modules/` → `apps/`
- Rename packages (`facturacion_ec` → `facturacion`)
- Asegurar imports correctos (de `modules.` → `apps.`)
- Validar que todos los módulos esenciales están en core
- Tests de integración (módulo por módulo)

**Nota:** M0.5 es parte de Phase 0.6 (restructure).

---

### **M0.6 — Multi-Repo Cleanup (v0.6.0)** 🔄 PLANEADO
**Semanas:** 4-5 (2026-05-17 → 2026-05-31)  
**Estado:** 📋 Planeado

**Objetivo:** Limpiar core después de integración de essential modules.

**Fases (9 tasks):**
- Phase 0.6.1 — Plan ✅ (completado)
- Phase 0.6.2 — Mover `facturacion_ec/` → `apps/facturacion/` (en lugar de extraer)
- Phase 0.6.3 — Eliminar módulos demo (`accounting_basic`, `inventory_basic`, `demo_flow`)
- Phase 0.6.4 — Limpiar core settings (remover references a `modules/`)
- Phase 0.6.5 — Eliminar estático `modules_enabled.py` (dynamic loader)
- Phase 0.6.6 — Reorganizar workspace directory
- Phase 0.6.7 — Actualizar documentación (hybrid model)
- Phase 0.6.8 — Actualizar PAUL state
- Phase 0.6.9 — Validar todo (tests + lint + graph)

**Deliverables:**
- Core con 19 Django apps (11 framework + 8 essential)
- Sin `modules/` directorio
- Documentación híbrida completa
- Graphify actualizado (sin nodos aislados de essential modules)

---

### **M1 — Plugin System (v0.7.0)** 📋 PLANEADO
**Semanas:** 6-7 (2026-06-07 → 2026-06-21)  
**Estado:** 📋 Planeado

**Objetivo:** Sistema de plugins para extensiones opcionales (hr, crm, projects…).

**Fases:**
- Phase 1.1 — ModuleCatalog (catálogo DB para plugins opcionales)
- Phase 1.2 — ModuleInstaller (download + verify + install)
- Phase 1.3 — Plugin activation/deactivation UI
- Phase 1.4 — Update checks
- Phase 1.5 — License management

**Nota:** Esto es para plugins OPCIONALES. Los essential modules ya están en core.

**Success:** Instalar plugin `hr` desde GitHub.

---

### **M2 — SDK & CLI (v0.8.0)** 📋 PLANEADO
**Semanas:** 8-9 (2026-06-28 → 2026-07-12)  
**Estado:** 📋 Planeado

**Objetivo:** Herramientas para desarrolladores de plugins (externos).

**Fases:**
- Phase 2.1 — SDK (`sdk-nexus` repo)
- Phase 2.2 — CLI (`nexus-cli` repo)

---

### **M3 — Stable Core (v0.9.0)** 📋 PLANEADO
**Semanas:** 10-11 (2026-08-02 → 2026-08-15)  
**Estado:** 📋 Planeado

**Objetivo:** Core estable, bien documentado.

**Checklist:**
- [ ] Test coverage >70%
- [ ] CI/CD funcionando (GitHub Actions)
- [ ] Docs 100% (INSTALL, DEVELOPMENT, API_REFERENCE, MODULE_SPEC)
- [ ] Todos los módulos esenciales estables
- [ ] Plugin system probado con 2+ plugins oficiales

---

### **M4 — v1.0.0 Stable (v1.0.0)** 🎯 FINAL
**Semana:** 12 (2026-08-16)  
**Estado:** 📋 Planeado

**Objetivo:** Release estable para adopción inicial.

**Checklist:**
- [ ] Core sin bugs críticos (0 P0)
- [ ] Test coverage >80%
- [ ] Módulos esenciales completos (facturacion, inventory, sales, purchases)
- [ ] Notifications (email + Telegram) funcionando
- [ ] Dashboard con widgets útiles
- [ ] Print manager (PDF) operativo
- [ ] Permissions system robusto
- [ ] CI/CD completo + deploy automation
- [ ] Docs 100% (todo en español/inglés)
- [ ] 2+ plugins oficiales disponibles (hr, crm)
- [ ] Demo desplegada (demo.erpnexus.ec)
- [ ] CHANGELOG completo
- [ ] SemVer asegurado

---

## 📊 Essential Modules — Roadmap Separado

### **facturacion (v0.5 → v1.0):**
- v0.5 — Models + Admin (SRI basics) ✅
- v0.6 — Services (XML, digital signature, validator) 🔄
- v0.7 — API completion (endpoints REST)
- v0.8 — UI templates (factura forms, list)
- v0.9 — Testing SRI (certificados de prueba)
- v1.0 — Production ready (firma digital, ambiente producción)

### **inventory (v0.5 → v1.0):**
- v0.5 — Models (Product, Stock, Movement) ✅
- v0.6 — Warehouse management (bodegas) 🔄
- v0.7 — Stock adjustments, transfers
- v0.8 — Barcode/QR support
- v0.9 — Low stock alerts
- v1.0 — Full featured (multi-warehouse, batches)

### **sales (v0.5 → v1.0):**
- v0.5 — Models (Quotation, Order, Client) ✅
- v0.6 — Quotation → Order flow 🔄
- v0.7 — Invoice generation (enlaza con facturacion)
- v0.8 — Payment tracking
- v0.9 — Sales reports
- v1.0 — Complete sales cycle

### **purchases (v0.5 → v1.0):**
- v0.5 — Models (PurchaseOrder, Vendor) ✅
- v0.6 — PO approval workflow 🔄
- v0.7 — Receiving goods (inventory integration)
- v0.8 — Vendor management
- v0.9 — Purchase analytics
- v1.0 — Full purchase cycle

---

## 🔄 Dependencies entre Módulos

```
facturacion       → core_events (emite eventos)
facturacion       → core_companies (usa Company model)
inventory         ← facturacion (escucha eventos invoice.created)
sales             → facturacion (genera facturas desde órdenes)
sales             → inventory (reserva stock)
purchases         → inventory (ingreso de stock)
notifications     ← todos (escucha eventos de todos)
dashboard         ← todos (consulta stats de todos)
```

---

## 📊 Métricas de Progreso (Core)

| Métrica | v0.5.0 (actual) | v0.6.0 Target | v0.9.0 Target | v1.0.0 Target |
|---------|-----------------|---------------|---------------|---------------|
| Django apps | 11 (solo framework) | 19 (11+8) | 19 | 19 |
| Essential modules | 0 | 8 (100%) | 8 (100%) | 8 (100%) |
| Test coverage | ~15% | >40% | >70% | >80% |
| Nodos aislados Graphify | 61 | <20 | <10 | <5 |
| Docs completas | 60% | 80% | 95% | 100% |
| CI/CD | No | GitHub Actions | ✅ | ✅ |
| API endpoints | 20+ | 50+ | 80+ | 100+ |
| Plugin system | No | ✅ Basic | ✅ Advanced | ✅ Stable |

---

## 🚨 Bloqueos y Riesgos

| Riesgo | Probabilidad | Impacto | Mitigación |
|--------|--------------|---------|------------|
| **Essential modules no caben en core** | Baja | Alto | Mover a plugins si es necesario (perder hybrid model) |
| **Core se vuelve monolito pesado** | Media | Medio | Modular design (cada essential module es app independiente) |
| **Plugins opcionales no se adoptan** | Media | Bajo | Core ya es ERP completo (plugins son bonus) |
| **Essential modules retrasan v1.0** | Media | Alto | Parallel development (multi-app) |

---

## 💡 Decisiones Pendientes

1. **¿Web builder en core o plugin?**
   - A: En core (pero no es essential) → plugin recomendado
   - Pendiente: Decisión para v1.0

2. **¿GraphQL en v0.8 o v1.0?**
   - Evaluar según frontend complexity

3. **¿gRPC en v2.0?**
   - Solo si separamos microservices

---

## 📞 Canales

- **Core Issues:** `github.com/ERPNexus/erp-nexus/issues`
- **Plugin Issues:** Respectivo repo (hr/issues, …)
- **Discussions:** `github.com/ERPNexus/.github/discussions`

---

**Última actualización:** 2026-05-10 — ARCHITECTURE_HYBRID adoptada, M0.5 en progreso
