# ADR-007: Hybrid Architecture — Essential Modules in Core + Optional Plugins

**Estado:** ✅ Aceptado (Walter Cun, 2026-05-10)  
**Fecha:** 2026-05-10  
**Contexto:** Fase 0.6 — Repository Structure  
**Decisores:** Walter Cun, ERP Nexus Team

---

## 📋 Contexto

Tras discusión, se clarifica que **ERP Nexus debe ser un ERP funcional desde el inicio**, no un mero framework que requiere instalar módulos básicos.

**El usuario explicitó:**
> "los modulos que va a tener el core que sera de facturacion, impresion, notificaciones, permisos y grupos, dashboard, compras y ventas, inventario"

Esto significa que los siguientes módulos son **esenciales** y deben venir integrados en el core:

- facturacion (facturación electrónica)
- impresion (print_manager)
- notificaciones
- permisos y grupos
- dashboard
- compras
- ventas
- inventario

---

## 🎯 Decisión

**Hybrid Architecture:**

### **Tier 1 — Essential Business Modules (integrated in core):**
Estos módulos vienen **pre-instalados** en `erp-nexus/apps/` y **no pueden desinstalarse**.

| Módulo | Ubicación | ¿Desinstalable? |
|--------|-----------|-----------------|
| `facturacion` | erp-nexus/apps/facturacion/ | ❌ NO |
| `inventory` | erp-nexus/apps/inventory/ | ❌ NO |
| `sales` | erp-nexus/apps/sales/ | ❌ NO |
| `purchases` | erp-nexus/apps/purchases/ | ❌ NO |
| `notifications` | erp-nexus/apps/notifications/ | ❌ NO |
| `permissions` | erp-nexus/apps/permissions/ | ❌ NO |
| `dashboard` | erp-nexus/apps/dashboard/ | ❌ NO |
| `print_manager` | erp-nexus/apps/print_manager/ | ❌ NO |

### **Tier 2 — Optional Extensions (plugins externos):**
Estos módulos son **extensiones** que se instalan via Marketplace:

| Plugin | Repo | ¿Desinstalable? |
|--------|------|-----------------|
| `hr` | github.com/ERPNexus/hr | ✅ SÍ |
| `accounting_adv` | github.com/ERPNexus/accounting_adv | ✅ SÍ |
| `crm` | github.com/ERPNexus/crm | ✅ SÍ |
| `project_mgmt` | github.com/ERPNexus/project_mgmt | ✅ SÍ |
| `pos` | github.com/ERPNexus/pos | ✅ SÍ |
| `ecommerce` | github.com/ERPNexus/ecommerce | ✅ SÍ |

---

## 🏗️ Estructura de Repos (Final)

```
ERPNexus/
│
├── erp-nexus/              ← CORE (framework + essential modules)
│   ├── apps/
│   │   ├── core_users/           # Framework
│   │   ├── core_companies/       # Framework
│   │   ├── core_events/          # Framework + EventBus
│   │   ├── core_api/             # Framework + REST
│   │   ├── core_marketplace/     # Framework + installer
│   │   │
│   │   ├── facturacion/          # Essential (integrated)
│   │   ├── inventory/            # Essential (integrated)
│   │   ├── sales/                # Essential (integrated)
│   │   ├── purchases/            # Essential (integrated)
│   │   ├── notifications/        # Essential (integrated)
│   │   ├── permissions/          # Essential (integrated)
│   │   ├── dashboard/            # Essential (integrated)
│   │   └── print_manager/        # Essential (integrated)
│   │
│   └── README.md (core only)
│
├── hr/                     ← Optional plugin
├── crm/                    ← Optional plugin
├── project_mgmt/           ← Optional plugin
├── sdk-nexus/              ← SDK
└── nexus-cli/              ← CLI
```

---

## 🔄 Modelo de Instalación

### **Small Business (solo core):**
```bash
git clone https://github.com/ERPNexus/erp-nexus.git
cd erp-nexus
uv sync
python manage.py migrate    # Crea TODAS las tablas (essential modules)
python manage.py runserver  # → ERP funcional completo
```

**Resultado:** ERP con facturación, inventario, ventas, compras, notificaciones, dashboard — sin instalar plugins.

---

### **Enterprise (core + extensions):**
```bash
# Core ya tiene lo esencial
python manage.py install_module --git https://github.com/ERPNexus/hr.git
python manage.py install_module --git https://github.com/ERPNexus/crm.git
```

---

## 📊 Criterios de Essential vs Optional

### **Essential (debe estar en core):**
| Criterio | Ejemplos que cumplen |
|----------|----------------------|
| Core business function | Facturación, inventario, ventas, compras |
| Needed by 80%+ users | Notificaciones, permisos, dashboard |
| Cannot be decoupled | Print manager (PDF generation) |
| Cross-cutting concern | Event bus framework (core_events) |

### **Optional (puede ser plugin):**
| Criterio | Ejemplos que cumplen |
|----------|----------------------|
| Industry-specific | HR (solo empresas con empleados), POS (retail) |
| Advanced features | Accounting_adv (contadores), AI assistant |
| Nice-to-have | Web builder, mobile app |
| Third-party integration | Stripe, Shopify connectors |

---

## ✅ Ventajas

1. **ERP funcional out-of-the-box** — No necesitas instalar plugins para lo básico
2. **Simple para PYMES** — Un solo comando, ERP completo
3. **Extensible para enterprises** — Plugins para necesidades avanzadas
4. **Menos fricción** — No hay "analysis paralysis" eligiendo módulos básicos
5. **Core es producto** — No solo framework vacío

---

## ⚠️ Trade-offs

| Trade-off | Impacto | Mitigación |
|-----------|---------|------------|
| Core más grande | ~60% del código (essential modules) | Bien organizado en `apps/` |
| No puedes desinstalar facturación | Algunos clientes podrían no facturar | Asumimos 95% necesitan facturación |
| Update core = update todos los módulos | Más testing | CI/CD robusto, compatible SemVer |

---

## 🔄 Cambios en Phase 0.6 Plan

### **Antes (plugin-only):**
- Extraer `facturacion_ec/` → `repos/facturacion_ec/` (repo separado)

### **Ahora (hybrid):**
- Mover `modules/facturacion_ec/` → `apps/facturacion/` (dentro del core)
- Rename package: `facturacion_ec` → `facturacion` (o mantener)
- Mismo para inventory, sales, purchases, notifications, permissions, dashboard, print_manager
- Eliminar solo módulos demo (accounting_basic, inventory_basic, demo_flow)
- NO extraer facturacion a repo separado
- NO crear plugin marketplace para essential modules

---

## 📋 Acceptance Criteria

- [ ] `erp-nexus/apps/` contiene 19 apps (11 core + 8 essential)
- [ ] No hay `modules/` directorio (o vacío)
- [ ] No hay intento de extraer essential modules a repos separados
- [ ] Facturacion, inventory, sales, purchases, notifications, permissions, dashboard, print_manager todos en core
- [ ] Documentación refleja hybrid model (ARCHITECTURE_HYBRID.md)
- [ ] PAUL STATE actualizado (scope: core + essential modules)
- [ ] Tests pasan con nueva estructura

---

## 🔗 Related

- `ARCHITECTURE_HYBRID.md` — Guía completa
- `PROJECT_DEFINITION.md` — Scope actualizado
- `WORK_PLAN.md` — Roadmap con essential modules en core
- `MODULE_SPEC.md` — Dos tipos: Essential vs Optional

---

**Consecuencia:** ERP Nexus es un **ERP completo desde el primer commit**, no un framework vacío.

**Comparación:** Como Odoo (core con modules integrados + extensible).
