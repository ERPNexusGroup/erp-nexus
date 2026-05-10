# 🏗️ Arquitectura — ERP Nexus

**Versión:** 1.0.0-alpha  
**Fecha:** 2026-05-10

---

## 📐 Diagrama de Arquitectura

```
┌─────────────────────────────────────────────────────────────────┐
│                    Clientes / Usuarios                          │
│  Admin Django │ API REST │ Módulos activos │ Dashboard          │
└─────────────────────────────┬───────────────────────────────────┘
                              │
┌─────────────────────────────▼───────────────────────────────────┐
│               ERP NEXUS CORE (erp-nexus/)                       │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ Django Framework + Configuración                          │  │
│  │  - settings.py (INSTALLED_APPS dinámico)                  │  │
│  │  - Middleware (ActiveCompanyMiddleware)                   │  │
│  │  - Context processors                                     │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐       │
│  │ Core Apps    │  │ Marketplace  │  │ API Layer    │       │
│  │ (11 apps)    │  │ Engine       │  │ (Django Ninja│       │
│  │              │  │              │  │  + Ninja)     │       │
│  └──────────────┘  └──────────────┘  └──────────────┘       │
│                                                               │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │ Module Registry (ModuleCatalogItem + EnabledModule)     │ │
│  │ - Catálogo de módulos disponibles                       │ │
│  │ - Registro de módulos instalados                        │ │
│  │ - Descarga/instalación automática                       │ │
│  └──────────────────────────────────────────────────────────┘ │
└─────────────────────────────┬───────────────────────────────────┘
                              │
         ┌────────────────────┼────────────────────┐
         │                    │                    │
┌────────▼────────┐  ┌────────▼────────┐  ┌────────▼────────┐
│ Módulos Externos│  │ Módulos Externos│  │ Módulos Externos│
│ (repos separados)│  │ (repos separados)│  │ (repos separados)│
│                  │  │                  │  │                  │
│ facturacion_ec/  │  │ inventory/       │  │ sales/           │
│ └── modules/     │  │ └── modules/     │  │ └── modules/     │
│     facturacion_ │  │     inventory/   │  │     sales/       │
│     ec/          │  │                  │  │                  │
│   (app Django)   │  │   (app Django)   │  │   (app Django)   │
└──────────────────┘  └──────────────────┘  └──────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                    Base de Datos (PostgreSQL)                   │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐              │
│  │   Core DB   │ │ Facturacion │ │  Inventory  │              │
│  │  (tablas    │ │   EC DB     │ │    DB       │              │
│  │  core_*)    │ │ (facturacion│ │ (inventory_  │              │
│  │             │ │  _ec_*)     │ │   *)        │              │
│  └─────────────┘ └─────────────┘ └─────────────┘              │
│                              │                                 │
│                  Aislamiento por company_id                    │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🧩 Componentes del Core

### **1. Django Framework**
- **Configuración centralizada** en `erp_nexus/settings.py`
- `INSTALLED_APPS` dinámico — se construye desde:
  1. Apps core (hardcoded)
  2. `modules_enabled.py` (generado automáticamente)
- **Middleware:**
  - `ActiveCompanyMiddleware` — establece `request.active_company`
  - `CompanyAwareMiddleware` — filtra queries por company_id

### **2. Core Apps (11 apps)**

| App | Propósito | Dependencias |
|-----|-----------|--------------|
| `core_auth` | Políticas de autenticación | — |
| `core_users` | UserProfile + empresa activa | core_auth |
| `core_companies` | Multi-empresa + Membership | core_users |
| `core_groups` | Grupos + permisos M2M | auth |
| `core_permissions` | Permisos base (código/descripción) | — |
| `core_marketplace` | Catálogo + instalador módulos | — |
| `core_dashboard` | Métricas + widgets | — |
| `core_currency` | Monedas + tasas cambio | — |
| `core_chart_of_accounts` | Plan de cuentas + asientos | — |
| `core_fiscal_year` | Años fiscales + períodos | — |
| `core_config` | Config key-value global/empresa | — |

### **3. Marketplace Engine**

```
ModuleCatalog (catálogo local/remoto)
    ↓ (download/install)
EnabledModule (registro módulo activo)
    ↓ (generate)
modules_enabled.py ← Se genera automáticamente
    ↓ (import)
settings.py → INSTALLED_APPS incluye módulo
    ↓ (migrate)
migrations/ del módulo → aplicadas
```

**Flujo de instalación:**
1. Admin registra módulo en `ModuleCatalogItem` (repo URL, versión)
2. `EnabledModule.objects.create(technical_name='facturacion_ec', ...)`
3. `write_modules_enabled()` genera `modules_enabled.py`:
   ```python
   MODULE_APPS = ["modules.facturacion_ec"]
   ```
4. Al siguiente restart, Django carga el módulo

### **4. API Layer (Django Ninja)**

```
/erp-nexus/apps/core_api/api.py
    ↓ add_router()
/api/v1/
├── /health              → core_api.health
├── /auth/               → core_api.v1.auth
├── /users/              → core_api.v1.users
├── /modules/            → core_api.v1.modules (marketplace)
├── /facturacion_ec/     → modules.facturacion_ec.api.routes
├── /inventory/          → modules.inventory.api.routes
└── ...
```

---

## 📦 Estructura de un Módulo

```
facturacion_ec/                    (repo separado)
├── __meta__.py                    # Metadata (requerido)
├── __init__.py
├── apps.py                        # AppConfig (requerido)
├── models.py                      # Modelos Django (requerido)
├── admin.py                       # Admin (requerido)
├── urls.py                        # URLs del módulo
├── signals.py                     # Django signals (opcional)
├── services/                      # Lógica de negocio (independiente)
│   ├── __init__.py
│   ├── xml_generator.py
│   ├── digital_signature.py
│   └── sri_client.py
├── api/
│   └── routes.py                  # REST endpoints (Django Ninja)
├── templates/facturacion_ec/      # Templates HTML
├── static/facturacion_ec/         # CSS/JS
├── tests/                         # Pruebas unitarias
├── migrations/                    # Migraciones Django
└── README.md                      # Documentación
```

**`__meta__.py` (estándar obligatorio):**
```python
MODULE_META = {
    "name": "Facturación Electrónica Ecuador",
    "technical_name": "facturacion_ec",
    "version": "0.1.0",
    "description": "Módulo para emisión de facturas electrónicas SRI Ecuador",
    "dependencies": ["core_companies", "core_users"],
    "author": "ERP Nexus Team",
    "repo": "https://github.com/ERPNexus/facturacion_ec",
    "license": "MIT",
    "min_erp_version": "0.5.0",
    "max_erp_version": "0.9.0",
}
```

---

## 🔄 Flujo de Instalación de Módulos

```
┌──────────────────────────────────────────────────────────────────┐
│ 1. Admin registra módulo en catálogo                             │
│    POST /api/v1/modules/                                         │
│    { technical_name, repo_url, version, enabled: false }        │
└───────────────────────┬──────────────────────────────────────────┘
                        │
┌───────────────────────▼──────────────────────────────────────────┐
│ 2. EnabledModule creado (status='pending_install')              │
│    - Se registra en BD                                          │
│    - No se instala aún                                          │
└───────────────────────┬──────────────────────────────────────────┘
                        │
┌───────────────────────▼──────────────────────────────────────────┐
│ 3. Admin activa módulo                                          │
│    POST /api/v1/modules/{name}/activate                         │
└───────────────────────┬──────────────────────────────────────────┘
                        │
┌───────────────────────▼──────────────────────────────────────────┐
│ 4. Sistema descarga e instala                                   │
│    a. Clona repo a ~/.erp-nexus/modules/{technical_name}/      │
│    b. Ejecuta manage.py check                                   │
│    c. Ejecuta manage.py makemigrations                          │
│    d. Ejecuta manage.py migrate                                 │
│    e. Copia migrations a repo migrations/                       │
│    f. Actualiza modules_enabled.py                              │
└───────────────────────┬──────────────────────────────────────────┘
                        │
┌───────────────────────▼──────────────────────────────────────────┐
│ 5. Módulo activo                                                │
│    - App agregada a INSTALLED_APPS                              │
│    - URLs incluidas en routing principal                       │
│    - Signals conectados                                         │
│    - Admin registrado                                           │
└──────────────────────────────────────────────────────────────────┘
```

---

## 🔐 Seguridad y Aislamiento

### **Multi-Tenant por company_id**
- Todas las queries filtran por `company_id`
- `request.active_company` seteado por middleware
- Filtro global obligatorio en todos los modelos con `CompanyMixin`

### **Permisos**
- `core_permissions.Permission` — catálogo de permisos (código único)
- `core_groups.Group` — agrupa permisos
- `core_companies.Membership` — usuario + empresa + rol
- Check de permisos en cada endpoint/api view

### **Audit Log**
- `core_audit.AuditLog` — registra cambios críticos
- Campos: `user`, `action`, `resource_type`, `resource_id`, `before/after`

---

## 📊 Base de Datos

### **Esquema por módulo:**
```
core_*              → Tablas del core
facturacion_ec_*    → Tablas del módulo facturación
inventory_*         → Tablas del módulo inventario (futuro)
sales_*             → Tablas del módulo ventas (futuro)
```

### **Convención de nombres:**
- `core_` — apps core
- `{technical_name}_` — módulos instalados
- Todos los modelos con `company = ForeignKey(Company)` obligatorio

---

## 🚀 Despliegue

### **Desarrollo:**
```bash
docker-compose up -d
# PostgreSQL + Redis + Django
```

### **Producción:**
```bash
# 1. PostgreSQL (RDS/CloudSQL o managed)
# 2. Django + Gunicorn + Nginx
# 3. Redis (cache/sessions)
# 4. Celery workers (opcional)
```

---

## 📚 Decisiones Técnicas

| Decisión | Opción Elegida | Rationale |
|----------|---------------|-----------|
| Framework | Django 5.x | Madurez, ecosistema, ORM |
| API | Django Ninja | FastAPI-like, OpenAPI auto |
| Frontend admin | Jazzmin | Theme moderno, personalizable |
| DB | PostgreSQL | ACID, JSONField, maduro |
| Módulos | Apps Django separadas | Aislamiento, versionado, independencia |
| Instalación | Git clone + migrate | Simple, verificable |
| Config | Key-Value store | Flexible por módulo/empresa |

---

## 🔮 Roadmap Técnico

| Versión | Meta |
|---------|------|
| v0.1.x | Core + Marketplace + 1 módulo demo |
| v0.2.x | Sistema licenciamiento + pagos (Stripe) |
| v0.3.x | Múltiples módulos oficiales |
| v0.4.x | Frontend público (React/Vue) |
| v1.0.0 | Release estable |

---

**Documentos relacionados:**
- `REQUIREMENTS.md` — Requisitos funcionales/no-funcionales
- `CODING_STANDARDS.md` — Reglas de codificación
- `MODULE_SPEC.md` — Especificación módulos
- `WORK_PLAN.md` — Roadmap temporal
