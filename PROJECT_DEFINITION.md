# 📋 Definición del Proyecto — ERP Nexus

**Proyecto:** ERP Nexus Core (Framework)  
**Versión:** 1.0.0-alpha  
**Fecha de creación:** 2026-05-10  
**Estado:** En desarrollo activo — Fase 0 (Restructure)  
**Licencia:** MIT  
**Mantenedor:** ERP Nexus Team  
**URL:** `github.com/ERPNexus/erp-nexus`

---

## 🎯 ¿Qué es ERP Nexus Core?

**ERP Nexus Core** es el **framework base** sobre el cual se construyen módulos ERP.

NO es un ERP completo. Es el **andamiaje** que permite:
- Multi-tenant (múltiples empresas en una instancia)
- Sistema de permisos granulares
- Marketplace engine (descargar/activar módulos)
- Event Bus (comunicación entre módulos)
- API REST (Django Ninja)
- Admin panel (Jazzmin)

---

## 🏗️ Arquitectura Multi-Repo

### **Principio: Un módulo = Un repositorio**

```
github.com/ERPNexus/
├── erp-nexus/              ← ESTE REPO (Core framework only)
│   ├── apps/               # 11 Django core apps
│   ├── erp_nexus/          # Settings, URLs, config
│   ├── docker/
│   ├── pyproject.toml
│   └── .paul/              # PAUL para core development
│
├── facturacion_ec/         ← Módulo independiente (OTRO repo)
│   ├── facturacion_ec/
│   │   ├── models.py
│   │   ├── api/
│   │   ├── services/
│   │   └── __meta__.py
│   ├── tests/
│   ├── README.md
│   └── .paul/              # PAUL para módulo
│
├── inventory/              ← Futuro módulo
├── sales/                  ← Futuro módulo
├── accounting/             ← Futuro módulo
│
├── sdk-nexus/              ← SDK para crear módulos
├── nexus-cli/              ← CLI tool (nexus command)
└── nexus-marketplace/      ← Marketplace server (catálogo)
```

---

## 🎯 Objetivos del Core

### **✅ SÍ incluye (Core):**
1. **Django base** — Config, middleware, settings
2. **Core apps (11):**
   - `core_users` — Usuarios + perfiles
   - `core_companies` — Multi-company (Company model)
   - `core_groups` — Grupos y roles
   - `core_permissions` — Permisos granulares
   - `core_marketplace` — Catálogo + ModuleRegistry
   - `core_events` — Event Bus (pub/sub)
   - `core_api` — API layer (Django Ninja)
   - `core_dashboard` — Dashboard admin
   - `core_audit` — Audit log
   - `core_stats` — Métricas
   - `core_config` — Configuraciones

3. **Marketplace Engine:**
   - ModuleRegistry (DB de módulos instalados)
   - ModuleInstaller (descarga/instala módulos)
   - ModuleValidator (valida estructura _meta_)
   - Activación/desactivación de módulos

4. **Infraestructura:**
   - Docker + docker-compose
   - CI/CD base (GitHub Actions)
   - Graphify integration (knowledge graph)
   - Documentation framework

### **❌ NO incluye (Core):**
1. **Módulos de negocio** — facturacion_ec, inventory, sales, etc.
2. **Certificados SRI** — Cada módulo los maneja
3. **Lógica específica de país** — Cada módulo local
4. **Frontend SPA** — v2.0 feature
5. ** SDK / CLI** — Repos separados

---

## 📦 Estructura Final (Core únicamente)

```
erp-nexus/                    # ERP Nexus Core (este repo)
├── apps/                     # 11 core Django apps
│   ├── core_auth/           # (renamed from core_users)
│   ├── core_companies/
│   ├── core_groups/
│   ├── core_permissions/
│   ├── core_marketplace/
│   ├── core_events/
│   ├── core_api/
│   ├── core_dashboard/
│   ├── core_audit/
│   ├── core_stats/
│   └── core_config/
│
├── erp_nexus/
│   ├── __init__.py
│   ├── settings/
│   │   ├── base.py          # Base settings (todos los módulos)
│   │   ├── development.py
│   │   └── production.py
│   ├── urls.py              # URLs core + API
│   ├── wsgi.py
│   ├── asgi.py
│   └── modules_registry.py  # Dinámico (DB-based), NO modules_enabled.py
│
├── docker/
│   ├── Dockerfile
│   └── docker-compose.yml   # Core + PostgreSQL + Redis
│
├── docs/                    # Documentación del core
├── tests/                   # Tests del core
├── scripts/                 # Scripts de mantenimiento
│
├── pyproject.toml           # Dependencias core
├── requirements.txt
├── Makefile
├── README.md                # Solo core documentation
├── ARCHITECTURE.md
├── CONTRIBUTING.md
├── WORK_PLAN.md             # Roadmap del core
└── .paul/                   # PAUL para core development
```

---

## 🔄 Flujo de Trabajo Multi-Repo

### **1. Desarrollar Core (este repo)**
```bash
cd repos/erp-nexus/
uv run pytest apps/core_marketplace/tests/
uv run python manage.py check
# Commits a erp-nexus repo
```

### **2. Desarrollar Módulo (facturacion_ec repo)**
```bash
cd repos/facturacion_ec/
# Desarrollar independientemente
# Depende de erp-nexus core (requirements: erp-nexus @ git+https://...)
```

### **3. Instalar Módulo en Core**
```bash
# En ERP Nexus core ejecutar:
uv run python manage.py install_module --git https://github.com/ERPNexus/facturacion_ec.git

# El Marketplace:
# 1. Lee __meta__.py del módulo
# 2. Valida dependencies (core version)
# 3. Clona a ~/.erp-nexus/modules/facturacion_ec/
# 4. Registra en DB (Module model)
# 5. Añade a INSTALLED_APPS dinámicamente
# 6. Ejecuta migrate
```

---

## 📊 Dependencias entre Repos

### **Core → No depende de módulos**
```
erp-nexus (core)
├── Django (pip)
├── PostgreSQL driver (psycopg)
├── Redis (django-redis)
└── NO dependencias de modules/*
```

### **Módulo → Depende de Core**
```
facturacion_ec/
├── Depends: erp-nexus >= 0.5.0
├── Uses: from apps.core_companies.models import Company
├── Uses: from apps.core_events.bus import EventBus
└── NO modifica core
```

**En requirements.txt del módulo:**
```txt
erp-nexus @ git+https://github.com/ERPNexus/erp-nexus.git@v0.5.0
django-ninja
lxml
cryptography
```

---

## 🚀 Marketplace Design

### **Marketplace como Catálogo (DB-based)**

```python
# apps/core_marketplace/models.py
class ModuleCatalogItem(models.Model):
    """Catálogo de módulos disponibles (no instalados)."""
    technical_name = models.CharField(unique=True)
    display_name = models.CharField()
    description = models.TextField()
    repository_url = models.URLField()  # GitHub repo
    latest_version = models.CharField()
    is_official = models.BooleanField()
    author = models.CharField()
    download_count = models.IntegerField(default=0)
    # metadata: dependencies, settings_form, screenshots

class Module(models.Model):
    """Módulo instalado en esta instancia."""
    catalog_item = models.ForeignKey(ModuleCatalogItem)
    version = models.CharField()
    installed_at = models.DateTimeField()
    enabled = models.BooleanField(default=True)
    module_path = models.CharField()  # ~/.erp-nexus/modules/{name}/
```

**Flujo:**
1. Admin ve catálogo en `/admin/core_marketplace/`
2. Click "Install" → `ModuleRegistry.install_from_git(url)`
3. Clona a `~/.erp-nexus/modules/{name}/`
4. Valida `__meta__.py`
5. Registra en DB → `Module.objects.create(...)`
6. Añade a `INSTALLED_APPS` runtime
7. Ejecuta `migrate {module}`

---

## 🔄 Workflows

### **Core Development:**
```bash
# 1. Cambios en core (erp-nexus repo)
git commit -m "feat(core_marketplace): add module auto-update"

# 2. Tag release
git tag -a v0.5.0 -m "Core 0.5.0"
git push origin v0.5.0

# 3. Módulos dependen de "erp-nexus >= 0.5.0"
```

### **Module Development:**
```bash
# 1. Crear módulo (facturacion_ec repo independiente)
sdk-nexus create facturacion_ec --type=module --country=EC

# 2. Desarrollar módulo (en su propio repo)
cd repos/facturacion_ec/
git commit -m "feat(xml): add XSD validation"

# 3. Tag release
git tag -a v0.1.0 -m "First release"
git push origin v0.1.0

# 4. Publicar en Marketplace
# (auto-detecta desde GitHub releases o manual upload)
```

### **Installation (User):**
```bash
# En ERP Nexus core instalado:
python manage.py install_module --git https://github.com/ERPNexus/facturacion_ec.git

# O desde catálogo:
# Admin → Marketplace → facturacion_ec → Install
```

---

## 📁 Estructura de Directorios Final (Workspace Local)

```
/home/wcun/.openclaw/workspace/
├── repos/
│   ├── erp-nexus/              # CORE (este repo actual)
│   ├── facturacion_ec/         # Módulo Ecuador (próximamente)
│   ├── inventory/              # Futuro
│   ├── sales/                  # Futuro
│   ├── sdk-nexus/              # SDK (crear)
│   ├── nexus-cli/              # CLI (crear)
│   └── nexus-marketplace/      # Marketplace server (crear)
│
├── .erp-nexus/                 # Datos de instancia ERP (en producción)
│   ├── modules/                # Módulos instalados (symlinks/clones)
│   ├── media/
│   └── logs/
│
├── career-ops/                 # Otro proyecto (no ERP Nexus)
└── credit-evaluation/          # Proyecto completado
```

---

## 🎯 Ventajas de Multi-Repo

| Ventaja | Explicación |
|---------|-------------|
| **Separación clara** | Core nunca contiene módulos de negocio |
| **Versionado independiente** | facturacion_ec v0.1.0 → v0.2.0 sin tocar core |
| **Contribuciones aisladas** | Devs de facturacion_ec no necesitan/core acceso |
| **Testing aislado** | Tests de módulo no corren en CI de core |
| **Deploy selectivo** | Actualizar solo módulo que cambió |
| **Licenciamiento diferenciado** | Core MIT, módulos pueden ser paid |

---

## ⚠️ Complejidades y Soluciones

| Problema | Solución |
|----------|----------|
| **Dependencia circular** | Core NO depende de módulos. Módulos dependen de core API estable |
| **Core cambio rompe módulos** | SemVer estricto: core v0.x → breaking changes → v1.0 |
| **CI/CD múltiple** | GitHub Actions matrix: test contra múltiples core versions |
| **Developer setup** | `sdk-nexus bootstrap` — clona todos los repos necesarios |
| **Marketplace discovery** | DB central (nexus-marketplace) con catalog de todos los módulos |

---

## 📈 Roadmap de Repos

### **Fase Actual (0.5.0) — Core Foundation**
- [x] Core apps 11
- [x] Multi-tenant middleware
- [x] Marketplace engine básico
- [ ] **Extraer facturacion_ec** → repo separado
- [ ] Eliminar módulos demo del core

### **Fase 0.6.0 — Multi-Repo Structure**
- [ ] Crear `facturacion_ec/` repo
- [ ] Crear `sdk-nexus/` repo
- [ ] Crear `nexus-cli/` repo
- [ ] Crear `nexus-marketplace/` repo
- [ ] Documentar multi-repo en `MULTI_REPO_STRUCTURE.md`

### **Fase 1.0.0 — Core Stable**
- [ ] Core sin módulos de ejemplo
- [ ] ModuleRegistry completo
- [ ] Marketplace UI funcional
- [ ] Mínimo 2 módulos oficiales instalables (facturacion_ec + inventory)

---

## 📚 Documentación Relacionada

- `ARCHITECTURE.md` — Diseño técnico del core
- `MODULE_SPEC.md` — Cómo construir módulos (para facturacion_ec repo)
- `DEVELOPMENT.md` — Desarrollo del core
- `MULTI_REPO_STRUCTURE.md` — Guía completa de organización multi-repo (próximo)
- `MARKETPLACE_GUIDE.md` — Cómo publicar módulos (próximo)

---

## 🔗 Referencias Externas

- **Git Subtree vs Submodule:** https://www.atlassian.com/git/tutorials/git-subtree
- **Django App Modularization:** https://docs.djangoproject.com/en/dev/ref/applications/
- **Plugin Architectures:** https://en.wikipedia.org/wiki/Plugin_architecture

---

**Nota:** Este documento define el **alcance del core ERP Nexus**. Cada módulo (facturacion_ec, inventory, sales) tiene su propio repositorio y documentación independiente.
