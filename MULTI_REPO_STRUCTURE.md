# 📁 Estructura Multi-Repo — ERP Nexus

**Versión:** 1.0.0-alpha  
**Fecha:** 2026-05-10  
**Estado:** En transición ( Phase 0.6 en curso )

---

## 🎯 Visión General

ERP Nexus usa **arquitectura multi-repo**:

| Repo | Propósito | Estado |
|------|-----------|--------|
| `erp-nexus/` | Core framework (este repo) | ✅ Activo |
| `facturacion_ec/` | Módulo facturación Ecuador | ⏳ En extracción |
| `inventory/` | Módulo inventario | 📋 Planeado |
| `sales/` | Módulo ventas/cotizaciones | 📋 Planeado |
| `sdk-nexus/` | SDK para crear módulos | 📋 Planeado |
| `nexus-cli/` | CLI tool (`nexus` command) | 📋 Planeado |
| `nexus-marketplace/` | Catálogo + API Marketplace | 📋 Planeado |

---

## 🏗️ Principios

### **1. Core Never Contains Modules**
El core (`erp-nexus/`) **NO contiene** código de módulos de negocio.
- ❌ NO `modules/facturacion_ec/` dentro de core
- ❌ NO `modules/inventory/` dentro de core
- ✅ Solo `apps/` (core framework) + `docker/` + `docs/`

### **2. Módulos son Repos Independientes**
Cada módulo es un repo Git separado:
```bash
gh repo clone ERPNexus/facturacion_ec
gh repo clone ERPNexus/inventory
```

### **3. Dependencia Unidireccional**
```
Módulo → Core (depende)
Core   → Nada (no depende de módulos)
```

** Manifesto **: Core es el "framework", módulos son "plugins".

---

## 📦 Estructura de un Módulo

```
facturacion_ec/                    # Repo independiente
├── facturacion_ec/
│   ├── __init__.py
│   ├── apps.py                   # AppConfig
│   ├── models.py                 # Modelos Django
│   ├── admin.py
│   ├── urls.py
│   ├── api/
│   │   └── routes.py             # API endpoints
│   ├── services/
│   │   ├── __init__.py
│   │   ├── xml_generator.py
│   │   ├── digital_signature.py
│   │   ├── sri_client.py
│   │   └── validator.py
│   ├── templates/
│   ├── static/
│   ├── tests/
│   ├── migrations/
│   └── __meta__.py               # Metadata (requerido)
│
├── .paul/                        # PAUL para el módulo
├── pyproject.toml                # Dependencias del módulo
├── requirements.txt
├── README.md                     # Docs del módulo
├── LICENSE                       # Licencia del módulo
└── .github/
    └── workflows/
        └── ci.yml                # tests del módulo
```

**`__meta__.py` contract:**
```python
MODULE_META = {
    "technical_name": "facturacion_ec",
    "name": "Facturación Ecuador",
    "version": "0.1.0",
    "description": "Facturación electrónica SRI Ecuador",
    "dependencies": ["core_companies>=0.5.0", "core_events>=0.5.0"],
    "min_erp_version": "0.5.0",
    "repo": "https://github.com/ERPNexus/facturacion_ec",
    "license": "MIT",
}
```

---

## 🔄 Instalación de Módulos

### **Desde línea de comandos:**
```bash
# En ERP Nexus Core instalado
python manage.py install_module --git https://github.com/ERPNexus/facturacion_ec.git

# O desde directorio local (dev)
python manage.py install_module ./facturacion_ec
```

### **Desde Marketplace UI:**
1. Admin login → Marketplace
2. Buscar módulo (facturacion_ec)
3. Click "Install"
4. Core clona a `~/.erp-nexus/modules/facturacion_ec/`
5. Registra en DB, activa

### **Pipeline de instalación:**
```
manage.py install_module
   ↓
1. Validate __meta__.py (dependencies, version)
   ↓
2. Download/Clone module
   ├─ git clone <repo_url> ~/.erp-nexus/modules/{name}/
   └─ OR copy from local directory
   ↓
3. Register in DB (Module model)
   ├─ technical_name, version, path
   └─ status = 'installed'
   ↓
4. Add to INSTALLED_APPS (runtime)
   └─ django.setup() reload
   ↓
5. Run migrations
   └─ python manage.py migrate {module}
   ↓
6. Emit event: module.installed
   └─ EventBus.emit('module.installed', ...)
   ↓
✅ Module ready
```

---

## 🔍 Cómo Crear un Nuevo Módulo

### **Opción A: SDK (recomendado)**
```bash
# Instalar SDK (repo separado)
pip install sdk-nexus

# Crear módulo
sdk-nexus create facturacion_ec --type=module --country=EC
cd facturacion_ec
# → Estructura completa generada
```

### **Opción B: Copiar plantilla**
```bash
# Desde erp-nexus core (plantilla)
cp -r erp-nexus/_template_module/ facturacion_ec/
cd facturacion_ec
# Editar __meta__.py, models.py, etc.
```

### **Opción C: Manual desde cero**
```bash
mkdir facturacion_ec
touch __meta__.py apps.py models.py
# Seguir MODULE_SPEC.md
```

---

## 🔧 Desarrollo de Módulos (aislado del core)

```bash
# 1. Clonar módulo (su propio repo)
git clone https://github.com/ERPNexus/facturacion_ec.git
cd facturacion_ec

# 2. Instalar dependencias (core + paquetería)
cat > requirements.txt << EOF
erp-nexus @ git+https://github.com/ERPNexus/erp-nexus.git@v0.5.0
django-ninja
lxml
cryptography
EOF

uv sync

# 3. Desarrollo aislado (no afecta core)
# Editar services/, models/, tests/

# 4. Tests del módulo
uv run pytest facturacion_ec/tests/ -v

# 5. Commit y tag
git tag -a v0.1.0 -m "First release"
git push origin v0.1.0

# 6. Publicar (disponible en Marketplace)
# (auto-detecta desde GitHub releases o manual upload)
```

---

## 🤖 Dependencies Cross-Repo

**Módulo → Core** (permitido):
```python
# facturacion_ec/models.py
from apps.core_companies.models import Company  # ✅ Correcto
```

**Core → Módulo** (PROHIBIDO):
```python
# erp-nexus/apps/core_api/api.py
from modules.facturacion_ec.models import Invoice  # ❌ NUNCA
```

**Módulo → Módulo** (PROHIBIDO directo):
```python
# facturacion_ec → inventory (incorrecto)
from inventory.models import Product  # ❌

# ✅ Correcto: EventBus
from apps.core_events.bus import EventBus
EventBus.emit('invoice.created', payload={...})
# inventory se suscribe a 'invoice.created'
```

---

## 🏷️ Versionado SemVer (por repo)

```
erp-nexus/       v0.5.0 → v0.6.0 → v1.0.0
facturacion_ec/  v0.1.0 → v0.2.0 → v1.0.0
inventory/       v0.1.0 → ...
```

**Breaking changes:**
- Core v1.0.0 → rompe compatibilidad → módulos deben actualizarse
- Módulo v1.0.0 → rompe compatibilidad → core no se afecta

**Dependency declarations:**
```python
# __meta__.py
"dependencies": [
    "core_companies>=0.5.0",  # Mínima versión core
    "core_events>=0.5.0",
],
```

---

## 🛠️ Marketplace como Servicio

### **Architecture:**
```
nexus-marketplace/ (separate repo/service)
├── Catalog API  — GET /api/modules/
├── Search
├── Download stats
└── Quality badges

erp-nexus core:
├── ModuleRegistry — lee catálogo
├── ModuleInstaller — descarga e instala
└── Admin UI — muestra catálogo
```

**En v1.0:** Marketplace como simple DB table (ModuleCatalogItem) dentro del core.

**En v2.0:** Marketplace como servicio independiente (API centralizada).

---

## 🚀 Workflow: Contribuir a ERP Nexus Ecosystem

### **Para contribuir al CORE:**
```bash
# Fork erp-nexus
cd repos/erp-nexus/
# Desarrollar en apps/
# Tests: pytest apps/
# PR a: github.com/ERPNexus/erp-nexus
```

### **Para contribuir a un MÓDULO:**
```bash
# Fork facturacion_ec
cd repos/facturacion_ec/
# Desarrollar en facturacion_ec/
# Tests: pytest facturacion_ec/tests/
# PR a: github.com/ERPNexus/facturacion_ec
```

### **Para crear NUEVO MÓDULO:**
```bash
# 1. Crear repo en GitHub (ERPNexus org)
gh repo create mi_nuevo_modulo --public

# 2. Clonar y estructurar
git clone git@github.com:ERPNexus/mi_nuevo_modulo.git
cd mi_nuevo_modulo
sdk-nexus create . --type=module --domain=custom

# 3. Desarrollar, testear, tag
git tag -a v0.1.0
git push --tags

# 4. Registrar en Marketplace (admin de algún ERP Nexus)
# O auto-registro via webhook (futuro)
```

---

## 📚 Documentación por Repo

| Repo | Documentación Principal |
|------|------------------------|
| `erp-nexus/` | README.md, DEVELOPMENT.md, API_REFERENCE.md |
| `facturacion_ec/` | README.md (module-specific), SRI_SPEC.md |
| `inventory/` | README.md (inventory ops) |
| `sdk-nexus/` | SDK Reference |
| `nexus-cli/` | CLI Reference |
| `nexus-marketplace/` | Marketplace API |

**Cada repo es autónomo en docs.** Solo el core tiene DOCS_INDEX.md global.

---

## 🐛 Troubleshooting Multi-Repo

### **"Module not found" error**
```bash
# Módulo no instalado
python manage.py install_module --git <url>

# O si está en desarrollo:
python manage.py install_module ./ruta/al/modulo
```

### **"Dependency unsatisfied"**
```bash
# Core version muy antigua para módulo
# Actualizar core:
cd erp-nexus/
git pull origin main
uv sync
```

### **Cross-module imports fallan**
```python
# ❌ MAL (acoplamiento fuerte)
from inventory.models import Product

# ✅ BIEN (EventBus)
EventBus.emit('invoice.created', ...)
# inventory se subscribe
```

---

## 📊 Comparación: Monorepo vs Multi-Repo

| Aspecto | Monorepo (ANTES) | Multi-Repo (AHORA) |
|---------|------------------|--------------------|
| **Estructura** | Todo en `erp-nexus/` | Cada componente repo separado |
| **Módulos** | Dentro core (`modules/`) | Repos independientes |
| **Versionado** | Único (core + módulos) | Independiente por repo |
| **CI/CD** | Un pipeline | Multiples pipelines |
| **Deploy** | Todo o nada | Selectivo por módulo |
| **Developer** | Solo core devs | Core devs + Module devs separados |
| **Marketplace** | Imposible (no hay catálogo) | Natural (GitHub repos) |
| **Adopción externa** | Baja (core grande) | Alta (solo módulos que necesitas) |

**Decisión:** Multi-repo → Mejor escalabilidad, comunidad, modularidad real.

---

## 📋 Checklist de Migración (Phase 0.6)

**Antes de ejecutar:**
- [ ] Backup completo (`git status` limpio)
- [ ] Commits locales pusheados
- [ ] Documentación actualizada (este archivo)

**Durante ejecución:**
- [ ] Task 0.6.2: facturacion_ec extraído a `repos/facturacion_ec/`
- [ ] Task 0.6.3: Demo modules eliminados
- [ ] Task 0.6.4: Settings core limpios
- [ ] Task 0.6.5: modules_enabled.py removido
- [ ] Task 0.6.6: Directorios reorganizados
- [ ] Task 0.6.7: Docs actualizados
- [ ] Task 0.6.8: PAUL state actualizado
- [ ] Task 0.6.9: Tests pasan

**Después:**
- [ ] `git push` todos los cambios
- [ ] Verificar `manage.py runserver` funciona
- [ ] Verificar `manage.py check` sin errores
- [ ] Graphify update (opcional)

---

## 🔮 Futuro (v2.0+)

- **nexus-marketplace** como servicio cloud (SaaS)
- **sdk-nexus** como PyPI package (`pip install sdk-nexus`)
- **nexus-cli** como binary (`brew install nexus-cli`)
- **Core** ultraligero (50MB Docker image)
- **Módulos** como Docker containers (futuro lejano)

---

## 📖 Referencias

- `PAUL/STATE.md` — Estado actual del proyecto
- `PAUL/ROADMAP.md` — Roadmap por fase
- `MODULE_SPEC.md` — Especificación técnica de módulos
- `DEVELOPMENT.md` — Cómo desarrollar el core
- `MULTI_REPO_GUIDE.md` — (este archivo)

---

**¿Listos para reestructurar?** → Ejecutar `/paul:apply` Phase 0.6
