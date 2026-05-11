# 🏗️ Arquitectura de Software — ERP Nexus (Hybrid Model)

**Versión:** 1.0.0-alpha  
**Fecha:** 2026-05-10  
**Tipo:** Hybrid Architecture (Core + Essential Modules + Optional Plugins)

---

## 🎯 Principio Fundamental

**ERP Nexus = ERP completo con módulos esenciales integrados + sistema de extensiones**

```
┌─────────────────────────────────────────────────────────┐
│          ERP Nexus Ecosystem                            │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  ┌───────────────────────────────────────────────────┐ │
│  │  CORE (erp-nexus repo)                           │ │
│  │  ───────────────────────────────────────────────  │ │
│  │  Framework Layer (11 apps)                       │ │
│  │    • core_users, core_companies, core_events,    │ │
│  │      core_api, core_marketplace, core_audit, …   │ │
│  │                                                  │ │
│  │  Essential Business Modules (integrated)         │ │
│  │    • facturacion   (facturación Ecuador)         │ │
│  │    • inventory     (inventario)                  │ │
│  │    • sales         (ventas)                      │ │
│  │    • purchases     (compras)                     │ │
│  │    • notifications (notificaciones)              │ │
│  │    • permissions   (permisos extendidos)         │ │
│  │    • dashboard     (dashboard principal)         │ │
│  │    • print_manager (impresión PDF)               │ │
│  └───────────────────────────────────────────────────┘ │
│                          │                             │
│                          │ Marketplace                 │
│                          ▼                             │
│  ┌───────────────────────────────────────────────────┐ │
│  │  Optional Plugins (instalables)                  │ │
│  │    • hr           (recursos humanos)             │ │
│  │    • accounting_adv (contabilidad avanzada)      │ │
│  │    • crm          (CRM)                          │ │
│  │    • project_mgmt (gestión proyectos)            │ │
│  │    • pos          (punto de venta)               │ │
│  │    • ecommerce    (tienda online)                │ │
│  └───────────────────────────────────────────────────┘ │
│                                                         │
│  Running ERP: Core + Optional Plugins activos          │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

---

## 📦 Organización de Repos

```
Organización GitHub: ERPNexus/
│
├── erp-nexus/              ← CORE (framework + essential modules) ⬅ ESTA REPO
│   ├── apps/
│   │   ├── core_users/           ✅ Framework
│   │   ├── core_companies/       ✅ Framework
│   │   ├── core_events/          ✅ Framework + EventBus
│   │   ├── core_api/             ✅ Framework + REST API
│   │   ├── core_marketplace/     ✅ Framework + installer
│   │   │
│   │   ├── facturacion/          🔴 ESSENTIAL — Integrated
│   │   ├── inventory/            🔴 ESSENTIAL — Integrated
│   │   ├── sales/                🔴 ESSENTIAL — Integrated
│   │   ├── purchases/            🔴 ESSENTIAL — Integrated
│   │   ├── notifications/        🔴 ESSENTIAL — Integrated
│   │   ├── permissions/          🔴 ESSENTIAL — Integrated
│   │   ├── dashboard/            🔴 ESSENTIAL — Integrated
│   │   └── print_manager/        🔴 ESSENTIAL — Integrated
│   │
│   ├── erp_nexus/
│   ├── docker/
│   ├── .paul/
│   └── README.md
│
├── hr/                     ← PLUGIN (optional)
├── accounting_adv/         ← PLUGIN (optional)
├── crm/                    ← PLUGIN (optional)
├── project_mgmt/           ← PLUGIN (optional)
├── pos/                    ← PLUGIN (optional)
├── sdk-nexus/              ← SDK (create plugins)
└── nexus-cli/              ← CLI tool
```

---

## 🔍 Essential vs Optional — Cuándo usar cada tipo

### **Essential Modules (en core):**
**Criterio:** ¿Es este módulo **crítico** para que unERP funcione como ERP?

| Módulo | ¿Essential? | Razón |
|--------|-------------|-------|
| Facturación | ✅ SÍ | Todo ERP debe facturar |
| Inventario | ✅ SÍ | Todo ERP necesita control de stock |
| Ventas | ✅ SÍ | Todo ERP maneja ventas/cotizaciones |
| Compras | ✅ SÍ | Todo ERP maneja compras/proveedores |
| Notificaciones | ✅ SÍ | Comunicación es core (emails, Telegram) |
| Permisos | ✅ SÍ | Seguridad y acceso |
| Dashboard | ✅ SÍ | Vista unificada del negocio |
| Print Manager | ✅ SÍ | Documentos PDF esenciales |
| Contabilidad | ⚠️ NO | Puede ser plugin (accounting_adv) |
| HR | ⚠️ NO | No todas las empresas tienen empleados |
| CRM | ⚠️ NO | Vertical de ventas complejas |
| POS | ⚠️ NO | Solo retail |

---

### **Optional Plugins (externos):**
**Criterio:** ¿Es este módulo **específico de industria** o **avanzado**?

| Plugin | Industria/Use-case |
|--------|-------------------|
| `hr` | Empresas con nómina, empleados |
| `accounting_adv` | Contadores, firms contables |
| `crm` | Empresas con pipeline de ventas complejo |
| `project_mgmt` | Consultoras, desarrollo de proyectos |
| `pos` | Retail, tiendas físicas |
| `ecommerce` | Vendedores online |
| `mobile_app` | Empresas que necesitan app móvil |
| `ai_assistant` | Tecnología avanzada (futuro) |

---

## 🔄 Modelo de Instalación

### **Escenario A — Pequeña empresa (solo核心):**
```bash
# 1. Clonar core (trae todo esencial)
git clone https://github.com/ERPNexus/erp-nexus.git
cd erp-nexus
uv sync
python manage.py migrate   # Crea tablas de todos los módulos esenciales
python manage.py runserver

# → ERP funcional: facturación + inventario + ventas + compras + notificaciones + dashboard
```

**No necesita decidir** qué módulos instalar — vienen todos.

---

### **Escenario B — Empresa mediana (core + HR):**
```bash
# Core ya tiene lo esencial
# Agrega plugin HR
python manage.py install_module --git https://github.com/ERPNexus/hr.git
python manage.py migrate hr
```

---

### **Escenario C — Enterprise (todo):**
```bash
# Core con esenciales
# Agrega plugins avanzados
for plugin in hr accounting_adv crm project_mgmt pos ecommerce; do
    python manage.py install_module --git "https://github.com/ERPNexus/$plugin.git"
done
```

---

## 🎯 Cómo se Conectan los Módulos

### **Pattern 1 — Shared Core Models (dentro del core)**
```python
# Dentro de apps/facturacion/models.py
from apps.core_companies.models import Company  # ✅permitido (core)

class Invoice(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE)  # ✅
    client = models.ForeignKey("sales.Client", on_delete=models.PROTECT)  # ✅
```

**Regla:**
- ✅ Puedes importar `apps.core_*` (framework)
- ✅ Puedes importar otros `apps.{essential_module}` (porque están en el mismo codebase)
- ❌ NO puedes importar plugins externos (usar API/EventBus)

---

### **Pattern 2 — Event Bus (decoupled)**
```python
# facturacion/emite
from apps.core_events.bus import EventBus
EventBus.emit("invoice.created", {"invoice_id": 123})

# inventory/escucha
from apps.core_events.bus import EventBus
EventBus.subscribe("invoice.created", "inventory", "handlers.update_stock")
```

**Uso:** Comunicación entre módulos (incluso entre essential y plugins).

---

### **Pattern 3 — REST API (cross-context)**
```python
# Plugin hr quiere datos de facturación
import requests
resp = requests.get("/api/v1/facturacion/invoices/123/")
```

**Uso:**
- De plugin → essential module
- De essential module → plugin
- External integrations

---

## 📁 Estructura de Directorios

```
erp-nexus/
├── apps/
│   ├── core_users/           # Framework: auth, usuarios
│   ├── core_companies/       # Framework: multi-company
│   ├── core_events/          # Framework: event bus
│   ├── core_api/             # Framework: REST endpoints
│   ├── core_marketplace/     # Framework: plugin manager
│   ├── core_permissions/     # Framework: permissions backend
│   ├── core_audit/           # Framework: audit log
│   ├── core_stats/           # Framework: metrics
│   ├── core_config/          # Framework: settings
│   │
│   ├── facturacion/          # Essential: SRI, XML, firma digital
│   │   ├── models.py
│   │   ├── api/routes.py
│   │   ├── services/
│   │   │   ├── xml_generator.py
│   │   │   ├── digital_signature.py
│   │   │   └── validator.py
│   │   └── admin.py
│   │
│   ├── inventory/            # Essential: stock, bodegas
│   │   ├── models.py (Product, Stock, Movement)
│   │   ├── api/routes.py
│   │   └── services/
│   │
│   ├── sales/                # Essential: cotizaciones, órdenes
│   │   ├── models.py (Quotation, Order)
│   │   ├── api/routes.py
│   │   └── services/
│   │
│   ├── purchases/            # Essential: órdenes de compra
│   │   ├── models.py (PurchaseOrder, Vendor)
│   │   └── ...
│   │
│   ├── notifications/        # Essential: email, Telegram
│   │   ├── backends/
│   │   │   ├── email.py
│   │   │   └── telegram.py
│   │   └── templates/
│   │
│   ├── permissions/          # Essential: roles, permisos
│   │   ├── models.py (Role, Permission)
│   │   └── middleware.py
│   │
│   ├── dashboard/            # Essential: home, widgets
│   │   ├── widgets/
│   │   └── api/routes.py
│   │
│   └── print_manager/        # Essential: PDF generation
│       ├── generators/
│       └── templates/
│
├── erp_nexus/
│   ├── settings/
│   ├── urls.py
│   └── asgi.py
│
├── docker/
├── tests/
├── .paul/
├── README.md
├── PROJECT_DEFINITION.md
├── ARCHITECTURE_HYBRID.md     # ⬅ ESTE DOCUMENTO
└── ADR/007-hybrid-architecture.md
```

---

## 📡 GraphQL vs REST vs gRPC — Decisión Estratégica

### **Fase 0.5-0.7 (MVP):**
| Tecnología | Estado | Uso |
|------------|--------|-----|
| **REST API** | ✅ Implementado (Django Ninja) | Todo lo expuesto a frontend/third-party |
| **Event Bus** | ✅ Implementado (Redis + signals) | Comunicación interna módulos |
| **GraphQL** | ⏸️ Pendiente | Evaluar en v0.8 si frontend heavy |
| **gRPC** | ⏸️ Pendiente | Evaluar en v1.0+ si microservices |

### **Razones:**
1. **REST es simple, universal** — sufficient para MVP
2. **EventBus para intra-module** — async, decoupled
3. **GraphQL** solo si el frontend necesita queries complejas (React/Vue SPA)
4. **gRPC** solo si en v2.0 separamos a microservices

---

## ⚠️ Restricciones y Contratos

### **Módulos Essential (en core):**
- ✅ Pueden importar `apps.core_*`
- ✅ Pueden importar otros `apps.{essential}` (porque están en el mismo repo)
- ✅ Deben tener `company = ForeignKey(Company)` para datos tenant
- ✅ Deben registrar signals en `apps.py` ready()
- ✅ Deben tener migrations propias

### **Plugins Opcionales (externos):**
- ✅ Pueden importar `apps.core_*` únicamente
- ❌ NO pueden importar módulos essential (usar EventBus o API)
- ❌ NO pueden modificar core settings
- ✅ Deben definir `__meta__.py` (para Marketplace)

---

## ✅ Ventajas del Modelo Híbrido

| Ventaja | Explicación |
|---------|-------------|
| **ERP funcional inmediatamente** | `git clone` → ERP completo lista |
| **Sin decisión de módulos básicos** | Pequeña empresa no elige: ya tiene fact+inv+sales |
| **Extensible para grandes** | Empresas grandes instalan plugins (hr, crm, …) |
| **Core más robusto** | No es solo framework, es producto usable |
| **Plugins aún disponibles** | Para verticales/extensiones específicas |
| **Menos fricción onboarding** | No 10 decisiones sobre qué instalar |

---

## 🔄 Cómo Cambia esto el Plan

### **Phase 0.6 (restructure) — Modificado:**

**Original (plugin-only):**
1. Extraer `facturacion_ec/` → repo separado ❌

**Nuevo (hybrid):**
1. **Mover** `modules/facturacion_ec/` → `apps/facturacion/` ✅
2. Rename package: `facturacion_ec` → `facturacion` (o mantener nombre)
3. Ajustar imports en core (si hay referencias)
4. Eliminar modules demo (accounting_basic, inventory, demo_flow)
5. Limpiar settings
6. Documentar hybrid architecture

**Resultado:**
```
Antes:
erp-nexus/modules/facturacion_ec/   (plugin separado)

Después:
erp-nexus/apps/facturacion/         (essential module integrated)
```

---

## 🎯 Módulos Base del Core (Lista Final)

**11 Framework Apps (core):**
1. core_users
2. core_companies
3. core_events
4. core_api
5. core_marketplace
6. core_permissions
7. core_audit
8. core_stats
9. core_config
10. core_dashboard

**8 Essential Business Modules (integrated):**
11. facturacion
12. inventory
13. sales
14. purchases
15. notifications
16. permissions (extiende core_permissions)
17. dashboard (extiende core_dashboard)
18. print_manager

**Total:** 18 apps en core (11 framework + 8 business)

---

## 🤔 Web Builder — ¿Core o Plugin?

**Web Builder** (constructor de páginas web):
- No es esencial para un ERP
- Es un add-on de marketing/website
- Puede ser plugin opcional

**Decisión:** Plugin opcional (futuro), NO en core v1.0.

---

## 📚 Documentación Relacionada

- `ADR/006-plugin-architecture.md` — Obsolescente (reemplaza por este)
- `ADR/007-hybrid-architecture.md` — **Nuevo ADR oficial**
- `ARCHITECTURE_HYBRID.md` — Este documento (arquitectura)
- `PROJECT_DEFINITION.md` — Scope actualizado
- `MODULE_SPEC.md` — Update con 2 tipos de módulos

---

## 🎯 Conclusión

**ERP Nexus es un ERP completo que incluye:**

1. **Framework robusto** (multi-tenant, events, API)
2. **Módulos esenciales de negocio** (facturación, inventario, ventas, compras, …)
3. **Sistema de extensiones** (plugins opcionales para necesidades avanzadas)

**No es** un framework vacío que requiere instalar 10 plugins para ser usable.

**Para un pequeño negocio:** `git clone erp-nexus` → ERP funcionando en 5 min.  
**Para una enterprise:** Core + plugins oficiales (hr, crm, projects).

---

**Siguiente paso:** Actualizar Phase 0.6 para mover `facturacion_ec/` → `apps/facturacion/` (en lugar de extraer).
