# 🏗️ Arquitectura de Software — ERP Nexus

**Versión:** 1.0.0-alpha  
**Fecha:** 2026-05-10  
**Tipo:** Plugin-based Modular Architecture

---

## 🎯 Principio Fundamental

**ERP Nexus Core es EL FRAMEWORK. Los módulos son PLUGINS.**

```
┌─────────────────────────────────────────────┐
│         ERP Nexus Ecosystem                 │
├─────────────────────────────────────────────┤
│                                             │
│  ┌──────────────┐      ┌──────────────┐   │
│  │  CORE        │      │  PLUGINS     │   │
│  │  (Framework) │◄────►│  (Módulos)   │   │
│  └──────────────┘      └──────────────┘   │
│         │                      │           │
│         │  APIs + Events       │           │
│         └──────────┬───────────┘           │
│                    ▼                       │
│          Running ERP Instance              │
│  (Core + Plugins activos)                  │
│                                             │
└─────────────────────────────────────────────┘
```

**Core responsibilities:**
- ✅ Framework Django (settings, middleware, routing)
- ✅ Multi-tenant (Company isolation)
- ✅ Module Registry (catálogo + instalación)
- ✅ Event Bus (comunicación entre módulos)
- ✅ API Layer (exponer endpoints)
- ✅ Admin Panel (gestionar módulos)

**Plugin responsibilities:**
- ✅ Models (propios, en su namespace)
- ✅ Business logic (servicios)
- ✅ API endpoints (propios)
- ✅ Templates/Views (si necesitan UI)
- ✅ Admin (registran sus modelos)

---

## 🔌 Modelo de Plugins (Django Apps)

### **Cómo funciona:**

**1. Cada módulo es una Django App independiente:**
```python
# facturacion_ec/apps.py
from django.apps import AppConfig

class FacturacionEcConfig(AppConfig):
    name = "facturacion_ec"
    verbose_name = "Facturación Ecuador"

    def ready(self):
        # Registrar signals, inicializar
        pass
```

**2. Core los carga dinámicamente en INSTALLED_APPS:**
```python
# erp_nexus/settings/base.py (DYNAMIC)
INSTALLED_APPS = [
    # Core apps (SIEMPRE)
    "apps.core_users",
    "apps.core_companies",
    # ...
    # Apps from ModuleRegistry (INSTALLADAS)
]

def load_installed_modules():
    """Añade módulos instalados a INSTALLED_APPS."""
    from apps.core_marketplace.models import Module
    for module in Module.objects.filter(enabled=True):
        INSTALLED_APPS.append(module.technical_name)
```

**3. Module Registry en DB:**
```python
# apps/core_marketplace/models.py
class Module(models.Model):
    technical_name = models.CharField(unique=True)  # "facturacion_ec"
    version = models.CharField()
    enabled = models.BooleanField(default=True)
    installed_at = models.DateTimeField()
    module_path = models.CharField()  # "~/.erp-nexus/modules/facturacion_ec/"
```

**4. Installation flow:**
```bash
# Usuario ejecuta:
python manage.py install_module --git https://github.com/ERPNexus/facturacion_ec.git

# Lo que pasa:
1. Clona repo a ~/.erp-nexus/modules/facturacion_ec/
2. Valida __meta__.py (dependencias, compatibilidad)
3. Crea registro en DB (Module model)
4. Añade "facturacion_ec" a INSTALLED_APPS (en runtime)
5. Ejecuta: manage.py migrate facturacion_ec
6. Emite evento: module.installed
```

---

## 📦 Estructura de un Plugin/Módulo

```
facturacion_ec/                    # Repo Git independiente
│
├── facturacion_ec/                # Python package (Django app)
│   ├── __init__.py
│   ├── apps.py                    # AppConfig
│   ├── models.py                  # Modelos Django
│   ├── admin.py                   # Admin registration
│   ├── urls.py                    # URLs del módulo
│   ├── signals.py                 # Django signals
│   │
│   ├── api/                       # REST API endpoints
│   │   ├── __init__.py
│   │   └── routes.py
│   │
│   ├── services/                  # Lógica de negocio
│   │   ├── __init__.py
│   │   ├── xml_generator.py
│   │   ├── digital_signature.py
│   │   └── validator.py
│   │
│   ├── templates/facturacion_ec/  # HTML templates
│   ├── static/facturacion_ec/     # CSS/JS
│   ├── tests/                     # Unit/integration tests
│   ├── migrations/                # Django migrations
│   └── __meta__.py                # METADATA (requerido)
│
├── README.md                      # Documentación módulo
├── LICENSE                        # Licencia
├── pyproject.toml                 # Dependencias Python
├── requirements.txt
│
└── .github/
    └── workflows/
        └── ci.yml                 # CI del módulo
```

**`__meta__.py` (contrato plugin):**
```python
MODULE_META = {
    "technical_name": "facturacion_ec",
    "name": "Facturación Electrónica Ecuador",
    "version": "0.1.0",
    "description": "Facturación electrónica para SRI Ecuador",
    "author": "ERP Nexus Team",
    "license": "MIT",

    # Dependencias (otros módulos que necesita)
    "depends": [
        "core_companies>=0.5.0",
        "core_events>=0.5.0",
    ],

    # Compatibilidad ERP Nexus Core
    "min_erp_version": "0.5.0",
    "max_erp_version": "0.9.0",

    # Configuración default del módulo
    "settings": {
        "FACTURACION_EC_AMBIENTE": 1,  # 1=pruebas, 2=producción
        "FACTURACION_EC_AUTO_SEND": False,
    },

    # UI
    "icon": "fa-file-invoice",
    "menu_category": "Contabilidad",
    "menu_order": 10,

    # URLs
    "repo": "https://github.com/ERPNexus/facturacion_ec",
    "docs_url": "https://docs.erpnexus.ec/facturacion_ec",
}
```

---

## 🔄 Cómo los Plugins se Conectan al Core

### **Pattern 1: Event Bus (Recomendado)**
```python
# facturacion_ec/invoice_service.py
from apps.core_events.bus import EventBus

def create_invoice(...):
    invoice = Invoice.objects.create(...)
    EventBus.emit(
        event_type="invoice.created",
        source="facturacion_ec",
        payload={
            "invoice_id": invoice.id,
            "total": str(invoice.total),
            "company_id": invoice.company_id,
        }
    )
    return invoice
```

```python
# inventory/handlers.py (módulo separado)
from apps.core_events.bus import EventBus

def on_invoice_created(payload):
    # Actualizar stock automáticamente
    invoice_id = payload["invoice_id"]
    # ... lógica inventory

EventBus.subscribe(
    event_type="invoice.created",
    subscriber_module="inventory",
    handler_path="inventory.handlers.on_invoice_created"
)
```

**Ventaja:** Ningún plugin importa directamente a otro. Acoplamiento débil.

---

### **Pattern 2: API Calls**
```python
# inventory quiere datos de facturacion_ec
import requests

def get_invoice_total(invoice_id):
    resp = requests.get(
        f"http://localhost:8000/api/v1/facturacion_ec/invoices/{invoice_id}/"
    )
    return resp.json()["total"]
```

**Ventaja:** Independencia total (HTTP)
**Desventaja:** Overhead de red, autenticación

---

### **Pattern 3: Shared Core Models**
```python
# facturacion_ec/models.py
from apps.core_companies.models import Company  # ✅ Core modelo

class Invoice(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    # ...
```

**Todos los plugins pueden importar:** `apps.core_*` (core framework)

---

## 🔒 Aislamiento y Seguridad

### **Multi-Company en Plugins:**
```python
# TODOS los modelos de plugin DEBEN tener company FK
class Invoice(models.Model):
    company = models.ForeignKey(  # ✅ OBLIGATORIO
        "core_companies.Company",
        on_delete=models.CASCADE
    )
    # ...
```

### **Queries siempre filtradas:**
```python
# ❌ MAL — expone datos de todas las empresas
Invoice.objects.all()

# ✅ BIEN — filtra por company activa
from apps.core_companies.middleware import get_current_company
company = get_current_company()
Invoice.objects.filter(company=company)
```

### **Admin por Company:**
```python
# admin.py
class InvoiceAdmin(admin.ModelAdmin):
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(company=request.active_company)
```

---

## 🗂️ Estructura Final del Repositorio

### **Opción A: Monorepo (NO recomendado)**
```
erp-nexus/
├── core/              # Framework (11 apps)
├── modules/
│   ├── facturacion_ec/  # Plugin 1
│   ├── inventory/       # Plugin 2
│   └── sales/           # Plugin 3
```
**Problema:** No hay verdadera separación. Actualizar un plugin requiere deploy completo.

---

### **Opción B: Multi-Repo (RECOMENDADO) ✅**
```
Organización GitHub: ERPNexus/
├── erp-nexus/              # CORE (framework only)
│   ├── apps/              # 11 core Django apps
│   ├── erp_nexus/
│   ├── docker/
│   └── README.md          # Solo core docs
│
├── facturacion_ec/         # PLUGIN (repo separado)
│   ├── facturacion_ec/
│   ├── tests/
│   └── README.md
│
├── inventory/              # PLUGIN (repo separado)
├── sales/                  # PLUGIN (repo separado)
│
├── sdk-nexus/              # SDK para crear plugins
└── nexus-cli/              # CLI tool
```

**Ventajas:**
- ✅ Cada plugin versiona independientemente
- ✅ Core no contiene código de negocio
- ✅ Plugins pueden ser de terceros
- ✅ Marketplace: catálogo de plugins instalables
- ✅ Developer experience: clona solo lo que necesitas

---

## 📊 Modelo de Instalación

### **Escenario 1: Pequeño Negocio (solo facturación)**
```bash
# 1. Instalar core (framework)
git clone https://github.com/ERPNexus/erp-nexus.git
cd erp-nexus
uv sync
python manage.py migrate

# 2. Instalar solo plugin facturacion_ec
python manage.py install_module --git https://github.com/ERPNexus/facturacion_ec.git

# 3. Listo — ERP con facturación únicamente
python manage.py runserver
# → http://localhost:8000
```

**Resultado:** Solo facturación, sin inventory/sales overhead.

---

### **Escenario 2: Mediana Empresa (facturación + inventario)**
```bash
# Core + facturacion_ec + inventory
python manage.py install_module --git https://github.com/ERPNexus/facturacion_ec.git
python manage.py install_module --git https://github.com/ERPNexus/inventory.git
```

---

### **Escenario 3: Enterprise (todos los módulos)**
```bash
# Instalar todos los plugins oficiales
for plugin in facturacion_ec inventory sales accounting hr; do
    python manage.py install_module --git "https://github.com/ERPNexus/$plugin.git"
done
```

---

## 🔄 Marketplace Workflow

```
┌─────────────┐
│ Admin login │
└──────┬──────┘
       │
       ▼
┌─────────────────────┐
│   Marketplace UI    │  ← Ver catálogo de plugins
│   ( admin/          │     - facturacion_ec v0.1.0 [Install]
│     core_marketplace)│
└─────────┬───────────┘
          │ Click "Install"
          ▼
┌─────────────────────────┐
│  ModuleInstaller        │
│  1. Validate __meta__.py│
│  2. Clone to           │
│     ~/.erp-nexus/modules/│
│  3. Register in DB     │
│  4. Add to INSTALLED_APPS│
│  5. Run migrations     │
└─────────┬───────────────┘
          │
          ▼
┌─────────────────────┐
│   Plugin Active     │  ← Funcionando
│   - Models created  │
│   - URLs mounted    │
│   - Admin visible   │
└─────────────────────┘
```

---

## 🎯 Comparación con Otros Sistemas

| Sistema | Core | Módulos | Instalación |
|---------|------|---------|-------------|
| **WordPress** | WordPress core | Plugins (directorio wp-content/plugins/) | ZIP upload o repo |
| **Odoo** | Core + módulos built-in | Apps (separados, pero en mismo repo) | App Store |
| **ERP Nexus (nuestro)** | Framework minimalista | Plugins externos (Git repos) | `install_module --git <url>` |
| **Magento** | Core + modules/ | Composer packages | `composer require` |

**Ventaja ERP Nexus:** Cada plugin es repo independiente → versionado aislado, CI independiente.

---

## 📁 Dónde Vive el Código

### **En Desarrollo Local:**
```
/home/wcun/.openclaw/workspace/
├── repos/
│   ├── erp-nexus/           # Core (clonado)
│   ├── facturacion_ec/      # Plugin 1 (clonado)
│   ├── inventory/           # Plugin 2 (clonado)
│   └── sales/               # Plugin 3 (clonado)
│
├── .erp-nexus/              # Instancia runtime (datos, config)
│   ├── modules/             # Plugins instalados (symlinks/clones)
│   ├── media/
│   └── logs/
```

### **En Producción:**
```
/opt/erp-nexus/
├── core/                    # Core instalado (pip install erp-nexus)
├── modules/                 # Plugins instalados (~/.erp-nexus/modules/)
├── .env
└── docker-compose.yml
```

---

## 🚀 Developer Workflow

### **Desarrollar Core:**
```bash
cd repos/erp-nexus/
# Cambios en apps/core_*
pytest apps/core_marketplace/tests/
git commit -m "feat(core_marketplace): add plugin auto-update"
```

### **Desarrollar Plugin (facturacion_ec):**
```bash
cd repos/facturacion_ec/
# Independiente del core
pytest facturacion_ec/tests/
git tag -a v0.1.0
git push origin v0.1.0
# Publicar en GitHub (auto-aparece en Marketplace)
```

### **Instalar Plugin en Desarrollo:**
```bash
cd repos/erp-nexus
python manage.py install_module ../facturacion_ec/
```

---

## 🔄 Ciclo de Vida de un Plugin

```
1. CREATED     — Dev crea repo, define __meta__.py
2. DEVELOPMENT — Dev codifica, tests, tag v0.1.0
3. PUBLISHED   — GitHub release o publica en Marketplace
4. INSTALLED   — Admin de ERP Nexus instala desde Marketplace
5. ENABLED     — Plugin activo, funcionando
6. UPDATED     — Nueva versión disponible → upgrade
7. DISABLED    — Desactivado (sin eliminar datos)
8. UNINSTALLED — Eliminado (datos borrados o archivados)
```

---

## 📋 Checklist de Plugin Válido

Para que un directorio sea reconocido como plugin:

- [ ] Tiene `__meta__.py` con `MODULE_META` dict
- [ ] Tiene `apps.py` con `AppConfig` subclass
- [ ] Tiene `models.py` (aunque sea vacío)
- [ ] `__meta__.py` incluye:
  - `technical_name` (único)
  - `name` (mostrado)
  - `version` (SemVer)
  - `depends` (core modules necesarios)
  - `min_erp_version`
  - `repo` (URL)
- [ ] Models tienen `company = ForeignKey(Company)` si tienen datos
- [ ] No importa de otros plugins (solo core)
- [ ] Tiene tests (opcional pero recomendado)

---

## 🔍 Cómo el Core Detecta Plugins

**ModuleRegistry:**
```python
class ModuleRegistry:
    @staticmethod
    def discover_plugins():
        """Escanea directorios de plugins instalados."""
        plugin_dirs = [
            settings.BASE_DIR / "modules",  # ~/.erp-nexus/modules/
            settings.PLUGIN_DIRS,           # Directorios configurados
        ]
        for plugin_dir in plugin_dirs:
            for module_path in plugin_dir.iterdir():
                if (module_path / "__meta__.py").exists():
                    ModuleRegistry.register(module_path)

    @staticmethod
    def get_enabled_modules():
        """Retorna plugins activos para INSTALLED_APPS."""
        return [m.technical_name for m in Module.objects.filter(enabled=True)]
```

**Settings (dynamic):**
```python
# En runtime, al arrancar Django:
from apps.core_marketplace.registry import ModuleRegistry
ModuleRegistry.discover_plugins()
ModuleRegistry.load_to_settings()  # Añade a INSTALLED_APPS

django.setup()  # Carga todas las apps
```

---

## ✅ Ventajas de Esta Arquitectura

| Aspecto | Beneficio |
|---------|-----------|
| **Modularidad real** | Core sin knows about plugins. Plugins sin know about each other |
| **Plug & Play** | Instala/desinstala sin tocar core |
| **Versionado independiente** | Plugin v1.0 compatible con core v0.5+ |
| **Third-party friendly** | Cualquier dev puede crear plugin |
| **Core minimalista** | Solo lo esencial → fácil de mantener |
| **Testing aislado** | Tests de plugin no afectan core CI |

---

## ⚠️ Restricciones y Contratos

### **Plugins NO deben:**
- ❌ Modificar `erp_nexus/settings.py`
- ❌ Importar otros plugins directamente (usar EventBus)
- ❌ Asumir `request.active_company` sin validar
- ❌ Hardcodear IDs de company
- ❌ Crear modelos sin `company` FK (si son multi-tenant)

### **Plugins PUEDEN:**
- ✅ Importar `apps.core_*` (core framework)
- ✅ Emitir/Subscription a EventBus events
- ✅ Definir sus propios models, api, admin
- ✅ Tener sus propias dependencias pip (en `requirements.txt` del plugin)

---

## 📚 Documentación Relacionada

- `MODULE_SPEC.md` — Contrato técnico completo de plugins
- `DEVELOPMENT.md` — Cómo desarrollar plugins
- `MULTI_REPO_STRUCTURE.md` — Organización de repos
- `API_REFERENCE.md` — APIs que los plugins pueden usar

---

## 🎯 Conclusión

**ERP Nexus = WordPress for ERP**

- **Core** = WordPress (framework)
- **Plugins** = facturacion_ec, inventory, sales (extensiones)
- **Marketplace** = Directorio de plugins instalables
- **Developer** = Crea plugins, publica en GitHub, instala via Marketplace

**Tu repositorio actual `erp-nexus/` debe contener SOLO el CORE.**  
Los módulos (facturacion_ec, etc.) van en sus propios repos.

**¿Listo para reestructurar?** Vamos a ejecutar PAUL 0.6 para separar.
