# 📋 Definición del Proyecto — ERP Nexus Core

**Proyecto:** ERP Nexus Core (Framework + Essential Modules)  
**Versión:** 1.0.0-alpha  
**Fecha de creación:** 2026-05-10  
**Estado:** En desarrollo activo — Fase 0.6 (Restructure)  
**Licencia:** MIT  
**Mantenedor:** ERP Nexus Team  
**URL:** `github.com/ERPNexus/erp-nexus`

---

## 🎯 ¿Qué es ERP Nexus?

**ERP Nexus** es un **sistema ERP completo** para pequeñas y medianas empresas ecuatorianas.

No es solo un framework — es un **ERP funcional** que incluye:

1. **Facturación electrónica** (SRI Ecuador) — ✅ Incluido
2. **Inventario** — ✅ Incluido
3. **Ventas** — ✅ Incluido
4. **Compras** — ✅ Incluido
5. **Notificaciones** (email, Telegram) — ✅ Incluido
6. **Dashboard** — ✅ Incluido
7. **Permisos y roles** — ✅ Incluido
8. **Impresión de documentos** — ✅ Incluido

**Extensible** mediante plugins opcionales:
- HR (recursos humanos)
- CRM (customer relationship)
- Contabilidad avanzada
- Gestión de proyectos
- POS (punto de venta)
- E-commerce

---

## 🏗 Filosofía: Hybrid Architecture

### **Core + Essential Modules + Optional Extensions**

```
ERP Nexus Core (este repo):
├── Framework (11 Django apps)      ← Siempre presente
│   ├── core_users
│   ├── core_companies
│   ├── core_events
│   ├── core_api
│   ├── core_marketplace
│   └── ...
│
├── Essential Business Modules      ← Integrated (no desinstalables)
│   ├── facturacion/                (SRI Ecuador)
│   ├── inventory/                  (gestión stock)
│   ├── sales/                      (cotizaciones, órdenes)
│   ├── purchases/                  (compras, proveedores)
│   ├── notifications/              (email, Telegram)
│   ├── permissions/                (roles, permisos)
│   ├── dashboard/                  (home, KPIs)
│   └── print_manager/              (PDF generation)
│
└── Plugin System                 ← Para extensiones opcionales
    └── (hr, crm, projects, pos, ...)  ← Repos separados
```

**¿Por qué híbrido?**
- **ERP debe ser usable desde el inicio** — Pequeña empresa necesita facturar y controlar inventario YA
- **No queremos plugin hell** — No obligar al usuario a instalar 5 plugins para lo básico
- **Pero queremos extensibilidad** — HR, CRM, projects son para empresas grandes

**Analogía:** Odoo model (core modules + optional apps)

---

## 📦 Qué INCLUYE este Repositorio

### **Framework (11 core Django apps):**

| App | Propósito |
|-----|-----------|
| `core_users` | Usuarios + autenticación |
| `core_companies` | Multi-company (aislamiento de datos) |
| `core_events` | Event Bus (comunicación entre módulos) |
| `core_api` | REST API (Django Ninja) |
| `core_marketplace` | Catálogo e instalador de plugins |
| `core_permissions` | Permisos granulares (base) |
| `core_audit` | Audit log |
| `core_stats` | Métricas y analytics |
| `core_config` | Configuraciones globales |
| `core_dashboard` | Dashboard framework |
| `tba_core` | TBA |

### **Essential Business Modules (8 módulos integrados):**

| Módulo | Directorio | Función |
|--------|-----------|---------|
| Facturación | `apps/facturacion/` | Facturación electrónica SRI (XML, firma digital) |
| Inventario | `apps/inventory/` | Gestión de stock, bodegas, movimientos |
| Ventas | `apps/sales/` | Cotizaciones, órdenes, clientes |
| Compras | `apps/purchases/` | Órdenes de compra, proveedores |
| Notificaciones | `apps/notifications/` | Emails, Telegram, SMS |
| Permisos | `apps/permissions/` | Roles extendidos, permisos por módulo |
| Dashboard | `apps/dashboard/` | Widgets, KPIs, gráficos |
| Print Manager | `apps/print_manager/` | Generación PDF, impresión |

---

## 🔌 Módulos que NO van aquí (plugins separados)

Estos módulos vivirán en sus propios repositorios y se instalarán via Marketplace:

| Plugin | Repo destino | Razón |
|--------|--------------|-------|
| HR (recursos humanos) | `hr/` | No todos tienen empleados |
| Contabilidad avanzada | `accounting_adv/` | Especializado, para contadores |
| CRM | `crm/` | Ventas complejas, no todos lo necesitan |
| Gestión de proyectos | `project_mgmt/` | Consultoras, desarrollo |
| POS (punto de venta) | `pos/` | Solo retail/physical stores |
| E-commerce | `ecommerce/` | Vendedores online |
| App móvil | `mobile_app/` | Extensión móvil |
| Asistente IA | `ai_assistant/` | Futuro, experimental |

---

## 🚀 Cómo se Usa

### **Instalación Básica (solo core):**
```bash
# 1. Clonar core (trae todos los módulos esenciales)
git clone https://github.com/ERPNexus/erp-nexus.git
cd erp-nexus
uv sync

# 2. Configurar variables de entorno
cp .env.example .env
# Editar .env (DB, SECRET_KEY, etc.)

# 3. Migrar base de datos (crea tablas de TODOS los módulos esenciales)
python manage.py migrate

# 4. Crear superusuario
python manage.py createsuperuser

# 5. Ejecutar
python manage.py runserver
# → http://localhost:8000/admin
# → ERP completo funcionando (facturación, inventario, ventas, …)
```

**Resultado:** Tienes un ERP funcional completo sin instalar plugins adicionales.

---

### **Instalación con Extensiones:**
```bash
# Core ya instalado con módulos esenciales

# Instalar plugin HR
python manage.py install_module --git https://github.com/ERPNexus/hr.git
python manage.py migrate hr

# Instalar plugin CRM
python manage.py install_module --git https://github.com/ERPNexus/crm.git
python manage.py migrate crm
```

---

## 🔗 Cómo se Conectan los Módulos

### **1. Shared Core Models (dentro del core)**
```python
# apps/facturacion/models.py
from apps.core_companies.models import Company  # ✅ Framework

class Invoice(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE)  # ✅

from apps.sales.models import Order  # ✅ Essential module (en mismo codebase)
```

**Regla:**
- ✅ Puedes importar `apps.core_*` (framework)
- ✅ Puedes importar otros `apps.{essential}` (porque están en el mismo repo)
- ❌ No importar plugins externos (usar EventBus o API)

---

### **2. Event Bus (para decoupling):**
```python
# apps/facturacion/services/invoice_service.py
from apps.core_events.bus import EventBus

def create_invoice(...):
    invoice = Invoice.objects.create(...)
    EventBus.emit(
        event_type="invoice.created",
        source="facturacion",
        payload={"invoice_id": invoice.id, "total": str(invoice.total)}
    )
    return invoice
```

```python
# apps/inventory/handlers.py (escucha sin import directo)
from apps.core_events.bus import EventBus

def on_invoice_created(payload):
    # Actualizar stock
    invoice_id = payload["invoice_id"]
    # ...

EventBus.subscribe(
    event_type="invoice.created",
    subscriber_module="inventory",
    handler_path="inventory.handlers.on_invoice_created"
)
```

---

### **3. REST API (cross-context):**
```python
# Plugin hr consulta datos de facturación
import requests
resp = requests.get("/api/v1/facturacion/invoices/123/")
```

---

## 📡 GraphQL vs REST vs gRPC

### **Fase actual (v0.5-0.7):**
- ✅ **REST API** (Django Ninja) — todo lo público
- ✅ **Event Bus interno** (Redis + Django signals) — comunicación módulos
- ⏸️ **GraphQL** — evaluar en v0.8 (frontend SPA heavy)
- ⏸️ **gRPC** — evaluar en v1.0+ (microservices separados)

---

## 🎯 Comparación: Hybrid vs Plugin-Only

| Aspecto | Plugin-Only | Hybrid (ACTUAL) |
|---------|-------------|-----------------|
| Core contiene facturación | ❌ No | ✅ Sí |
| Core contiene inventario | ❌ No | ✅ Sí |
| Primera instalación | `git clone + install 5 plugins` | `git clone` únicamente |
| Para PYMES | Muy fricción (decidir plugins) | Cero fricción (todo incluido) |
| Extensibilidad | Todo es plugin | Essential in core + optional plugins |
| Similar a | WordPress | Odoo |

---

## 🏆 Ventajas del Modelo Híbrido

1. **ERP funcional desde el minuto 1** — Sin decisiones técnicas para el usuario
2. **Simple para el 80%** — Pequeñas empresas no necesitan plugins extra
3. **Extensible para el 20%** — Grandes empresas agregan HR, CRM, projects
4. **Core tiene valor** — No es solo framework vacío
5. **Menos mantenimiento** — Essential modules en mismo repo + tests unificados

---

## 🔄 Qué Módulos Van Dónde (Checklist)

### **En core (erp-nexus/apps/):**
- [x] facturacion — ✅ Facturación electrónica Ecuador
- [x] inventory — ✅ Gestión de inventario
- [ ] sales — ⏳ Pendiente mover
- [ ] purchases — ⏳ Pendiente mover
- [ ] notifications — ⏳ Pendiente mover
- [ ] permissions — ⏳ Pendiente mover
- [ ] dashboard — ⏳ Pendiente mover
- [ ] print_manager — ⏳ Pendiente mover

### **En plugins externos (futuro):**
- [ ] hr — Recursos humanos
- [ ] accounting_adv — Contabilidad avanzada
- [ ] crm — CRM
- [ ] project_mgmt — Gestión proyectos
- [ ] pos — Punto de venta
- [ ] ecommerce — Tienda online

---

## 📚 Documentación

- `ARCHITECTURE_HYBRID.md` — Guía arquitectónica completa
- `ADR/007-hybrid-architecture.md` — ADR oficial
- `PROJECT_DEFINITION.md` — Este documento
- `MODULE_SPEC.md` — Dos tipos de módulos (Essential vs Optional)
- `WORK_PLAN.md` — Roadmap con essential modules en core

---

## 🎯 Conclusión

**ERP Nexus = ERP completo listo-para-usar + sistema de extensiones**

**Core (erp-nexus/)** = Framework + 8 módulos esenciales de negocio  
**Plugins (otros repos)** = Extensiones especializadas (HR, CRM, …)

**Para Walter:** Pequeña empresa → solo core. Mediana/grande → core + plugins selectivos.

---

**Aprobado por:** Walter Cun  
**Fecha:** 2026-05-10
