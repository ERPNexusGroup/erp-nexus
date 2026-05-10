# 📋 Definición del Proyecto — ERP Nexus

**Proyecto:** ERP Nexus Core (Framework)  
**Versión:** 1.0.0-alpha  
**Fecha de creación:** 2026-05-10  
**Estado:** En desarrollo activo — Fase 0.6 (Restructure)  
**Licencia:** MIT  
**Mantenedor:** ERP Nexus Team  
**URL:** `github.com/ERPNexus/erp-nexus`

---

## 🎯 ¿Qué es ERP Nexus Core?

**ERP Nexus Core** = **Framework Django minimalista** para construir sistemas ERP mediante **plugins**.

No es un ERP completo. Es el **andamiaje** que provee:

1. **Multi-tenant** — Múltiples empresas en una instancia
2. **Module Registry** — Catálogo e instalación de plugins
3. **Event Bus** — Comunicación entre plugins
4. **API Layer** — Django Ninja REST endpoints
5. **Admin Panel** — Gestión de plugins + datos

**Los plugins (módulos de negocio) se instalan por separado.**

---

## 🏗️ Filosofía: Core + Plugins

### **WordPress for ERP**

```
WordPress Core      = ERP Nexus Core
Plugins (WP)        = Módulos (facturacion_ec, inventory, sales)
Theme               = Frontend (futuro)
Marketplace         = Plugin directory
```

**Ejemplo de uso:**
```bash
# 1. Instalar core (framework)
git clone https://github.com/ERPNexus/erp-nexus.git
cd erp-nexus
uv sync
python manage.py migrate

# 2. Instalar solo plugins que necesitas
python manage.py install_module --git https://github.com/ERPNexus/facturacion_ec.git
# (facturacion_ec es un plugin que se conecta al core)

# 3. Listo — ERP con facturación únicamente
python manage.py runserver
```

---

## 📦 Qué INCLUYE el Core

### **Framework (11 Django Apps)**

| App | Propósito |
|-----|-----------|
| `core_users` | Usuarios + perfiles |
| `core_companies` | Multi-company (Company model, middleware) |
| `core_groups` | Grupos y roles |
| `core_permissions` | Permisos granulares |
| `core_marketplace` | Catálogo + instalador de plugins |
| `core_events` | Event Bus (pub/sub entre plugins) |
| `core_api` | REST API (Django Ninja) |
| `core_dashboard` | Dashboard admin |
| `core_audit` | Audit log |
| `core_stats` | Métricas |
| `core_config` | Configuraciones globales |

### **Infraestructura**
- Docker + docker-compose
- CI/CD base (GitHub Actions)
- Graphify integration (knowledge graph)
- Documentation framework

---

## 📦 Qué NO incluye el Core (Plugins Separados)

| Plugin | Repo | Función |
|--------|------|---------|
| `facturacion_ec` | `github.com/ERPNexus/facturacion_ec` | Facturación electrónica SRI Ecuador |
| `inventory` | `github.com/ERPNexus/inventory` | Gestión de inventarios |
| `sales` | `github.com/ERPNexus/sales` | Cotizaciones, órdenes, facturación |
| `accounting` | `github.com/ERPNexus/accounting` | Contabilidad |
| `hr` | `github.com/ERPNexus/hr` | Recursos humanos |

**Los plugins se instalan opcionalmente.**

---

## 🔌 Cómo Funciona un Plugin

### **1. Plugin es una Django App estándar**
```python
# facturacion_ec/apps.py
from django.apps import AppConfig

class FacturacionEcConfig(AppConfig):
    name = "facturacion_ec"
    verbose_name = "Facturación Ecuador"
```

### **2. Plugin define sus propios models**
```python
# facturacion_ec/models.py
from django.db import models
from apps.core_companies.models import Company  # Import core model

class Invoice(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE)  # ✅
    number = models.CharField(max_length=20)
    # ...
```

### **3. Plugin expone API endpoints**
```python
# facturacion_ec/api/routes.py
from ninja import Router

router = Router(tags=["Facturación"])

@router.post("/invoices/")
def create_invoice(request, data: InvoiceCreate):
    # Lógica del plugin
    return {"id": invoice.id}
```

### **4. Plugin se comunica via Event Bus**
```python
from apps.core_events.bus import EventBus

# Emitir evento (otros plugins pueden escuchar)
EventBus.emit("invoice.created", source="facturacion_ec", payload={...})
```

---

## 🔄 Cómo se Instala un Plugin

### **Pipeline de instalación:**
```
Admin ejecuta: install_module --git <url>
   ↓
1. Validar __meta__.py (deps, version)
   ↓
2. Clonar repo a ~/.erp-nexus/modules/{plugin}/
   ↓
3. Registrar en DB (Module model)
   ↓
4. Añadir a INSTALLED_APPS (runtime)
   ↓
5. Ejecutar migrate {plugin}
   ↓
✅ Plugin activo y funcionando
```

---

## 📁 Estructura Multi-Repo

```
Organización GitHub: ERPNexus/
├── erp-nexus/              ← CORE (framework only) ⬅ ESTA REPO
│   ├── apps/               # 11 core Django apps
│   ├── erp_nexus/
│   ├── docker/
│   ├── pyproject.toml
│   └── README.md           # Solo core docs
│
├── facturacion_ec/         ← PLUGIN (repo separado)
│   ├── facturacion_ec/
│   ├── tests/
│   ├── README.md
│   └── __meta__.py
│
├── inventory/              ← PLUGIN (futuro)
├── sales/                  ← PLUGIN (futuro)
├── sdk-nexus/              ← SDK para crear plugins
└── nexus-cli/              ← CLI tool
```

**Dependencias:**
```
facturacion_ec → erp-nexus >= 0.5.0
inventory      → erp-nexus >= 0.6.0
sales          → erp-nexus >= 0.7.0
```

---

## 🎯 Ventajas de Plugin Architecture

| Ventaja | Explicación |
|---------|-------------|
| **Modularidad real** | Core no contiene código de negocio |
| **Instalación selectiva** | Cliente instala solo lo que necesita |
| **Versionado independiente** | facturacion_ec v1.0 compatible con core v0.5+ |
| **Third-party friendly** | Cualquier developer puede crear plugin |
| **CI/CD aislado** | Cada plugin tiene su propio pipeline |
| **Deploy selectivo** | Actualizar solo plugin que cambió |

---

## ⚠️ Restricciones para Plugins

### **❌ NO deben:**
- Modificar `erp_nexus/settings.py`
- Importar otros plugins directamente (usar EventBus)
- Asumir `request.active_company` sin validar
- Hardcodear company IDs

### **✅ PUEDEN:**
- Importar `apps.core_*` (core framework)
- Emitir/Subscribirse a EventBus events
- Definir sus propios models, api, admin
- Tener dependencias pip propias

---

## 📚 Documentación

- `ARCHITECTURE_PLUGIN.md` — Arquitectura de plugins completa
- `MODULE_SPEC.md` — Contrato técnico de módulos (qué debe tener un plugin)
- `MULTI_REPO_STRUCTURE.md` — Organización de repos
- `DEVELOPMENT.md` — Cómo desarrollar plugins
- `API_REFERENCE.md` — APIs expuestas por core para plugins

---

**Arquitectura:** Core framework + Plugins independientes  
**Alcance Core:** Solo 11 apps + marketplace engine  
**Alcance Plugins:** Módulos de negocio (facturacion_ec, inventory, sales, ...)
