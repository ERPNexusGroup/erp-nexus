# 📚 Documentación ERP Nexus — Índice Maestro

**Última actualización:** 2026-05-10  
**Versión:** 0.6.0-alpha (Plugin Architecture)

---

## 🎯 Empezar Aquí

| Si eres… | Lee esto |
|-----------|----------|
| **Nuevo usuario** | `README.md` → `INSTALL.md` |
| **Developer de plugins** | `ARCHITECTURE_PLUGIN.md` → `MODULE_SPEC.md` |
| **Contribuyente al core** | `CONTRIBUTING.md` → `CODING_STANDARDS.md` |
| **DevOps** | `docker-compose.yml` → `INSTALL.md#docker` |
| **Tech Lead / Arquitecto** | `ADR/` → Decisiones arquitectónicas |

---

## 📄 Documentos por Categoría

### **🏗️ Arquitectura (IMPORTANTE)**

| Documento | Propósito | Enlace |
|-----------|-----------|--------|
| `ARCHITECTURE_PLUGIN.md` | **Arquitectura principal**: Core + Plugins independientes | [Ver](./ARCHITECTURE_PLUGIN.md) |
| `PROJECT_DEFINITION.md` | Definición del proyecto, scope del core | [Ver](./PROJECT_DEFINITION.md) |
| `MULTI_REPO_STRUCTURE.md` | Guía completa multi-repo | [Ver](./MULTI_REPO_STRUCTURE.md) |
| `ADR/006-plugin-architecture.md` | ADR: Plugin-based architecture | [Ver](./ADR/006-plugin-architecture.md) |

**ADRs (Architecture Decision Records):**
- [ADR-001](./ADR/001-modular-architecture.md) — Modular architecture (monolito vs microservicios)
- [ADR-002](./ADR/002-event-bus.md) — Event Bus para comunicación
- [ADR-003](./ADR/003-multi-company.md) — Multi-company strategy
- [ADR-004](./ADR/004-marketplace.md) — Marketplace installation flow
- [ADR-005](./ADR/005-api-framework.md) — Django Ninja vs DRF
- [ADR-006](./ADR/006-plugin-architecture.md) — Plugin-based architecture ⭐

---

### **📖 Guías de Desarrollo**

| Documento | Propósito | Enlace |
|-----------|-----------|--------|
| `DEVELOPMENT.md` | Cómo desarrollar el **core** | [Ver](./DEVELOPMENT.md) |
| `MODULE_SPEC.md` | **Contrato técnico de plugins** (qué debe tener un plugin) | [Ver](./MODULE_SPEC.md) |
| `CODING_STANDARDS.md` | Reglas de codificación (PEP8, Django style) | [Ver](./CODING_STANDARDS.md) |
| `CONTRIBUTING.md` | Cómo contribuir, git flow, PR checklist | [Ver](./CONTRIBUTING.md) |

---

### **🚀 Instalación y Deploy**

| Documento | Propósito | Enlace |
|-----------|-----------|--------|
| `README.md` | Página principal, quickstart | [Ver](./README.md) |
| `INSTALL.md` | Instalación paso a paso (local + Docker) | [Ver](./INSTALL.md) |
| `docker-compose.yml` | Stack Docker completo | [Ver](./docker-compose.yml) |
| `Makefile` | Comandos shortcuts (`make dev`, `make test`) | [Ver](./Makefile) |

---

### **🔌 API y Referencia**

| Documento | Propósito | Enlace |
|-----------|-----------|--------|
| `API_REFERENCE.md` | Documentación REST API v1 (core endpoints) | [Ver](./API_REFERENCE.md) |
| `/api/v1/docs/` | Swagger UI (auto-generado, server running) | *en runtime* |
| `MODULE_SPEC.md` | Cómo construir plugins (APIs que pueden exponer) | [Ver](./MODULE_SPEC.md) |

---

### **📈 Roadmap y Progreso**

| Documento | Propósito | Enlace |
|-----------|-----------|--------|
| `WORK_PLAN.md` | Roadmap **core** (M0-M4) | [Ver](./WORK_PLAN.md) |
| `CHANGELOG.md` | Historial de releases | [Ver](./CHANGELOG.md) |
| `ACTIVE_PROJECTS.md` | Proyectos activos del workspace | [Ver](./ACTIVE_PROJECTS.md) |
| `GRAPH_HEALTH.md` | Salud del grafo Graphify | [Ver](./GRAPH_HEALTH.md) |
| `MODULE_INTEGRATION_STATUS.md` |Estado integración plugins | [Ver](./MODULE_INTEGRATION_STATUS.md) |

---

### **🛠️ Configuración y Herramientas**

| Archivo | Propósito |
|---------|-----------|
| `pyproject.toml` | Black, isort, ruff, mypy, pytest config |
| `.pre-commit-config.yaml` | Pre-commit hooks automáticos |
| `.env.example` | Variables de entorno ejemplo |
| `Makefile` | Comandos desarrollo |
| `setup-dev.sh` | Setup automatizado primera vez |
| `docker/Dockerfile` | Multi-stage build producción |

---

### **📦 Plantillas**

| Plantilla | Propósito |
|-----------|-----------|
| `_template_module/` | Boilerplate para plugins (Django app) |
| `ARCHITECTURE_PLUGIN.md` | Template de arquitectura para plugins |

---

## 🗺️ Estructura de Archivos (Core Únicamente)

```
erp-nexus/                    # ERP Nexus Core (framework)
├── README.md                 # Página principal (core only)
├── PROJECT_DEFINITION.md     # Qué es ERP Nexus Core
├── ARCHITECTURE_PLUGIN.md    # ⭐ Arquitectura de plugins
├── MULTI_REPO_STRUCTURE.md   # Estructura multi-repo
├── DEVELOPMENT.md            # Desarrollo del core
├── MODULE_SPEC.md            # Cómo construir plugins
├── INSTALL.md                # Instalación core
├── API_REFERENCE.md          # API core
├── WORK_PLAN.md              # Roadmap core
├── CODING_STANDARDS.md       # Reglas código
├── CONTRIBUTING.md           # Cómo contribuir
├── GRAPH_HEALTH.md           # Graphify status
├── MODULE_INTEGRATION_STATUS.md # Estado plugins
│
├── apps/                     # 11 core Django apps
│   ├── core_users/
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
│   ├── settings/
│   ├── urls.py
│   ├── wsgi.py
│   └── asgi.py
│
├── docker/
├── docs/
├── tests/
├── scripts/
├── pyproject.toml
├── .paul/                    # PAUL para core development
└── ADR/                      # Architecture Decision Records
```

---

## 📖 Leer en Orden Recomendado

**Primera vez (nuevo usuario):**
1. `README.md` — Overview (5 min)
2. `PROJECT_DEFINITION.md` — Scope del core (5 min)
3. `ARCHITECTURE_PLUGIN.md` — Cómo funcionan los plugins (10 min)
4. `INSTALL.md` — Instalar (10 min)

**Para desarrollar el core:**
1. `DEVELOPMENT.md`
2. `CODING_STANDARDS.md`
3. `ADR/` — Decisiones arquitectónicas
4. `API_REFERENCE.md`

**Para crear un plugin (módulo de negocio):**
1. `ARCHITECTURE_PLUGIN.md` — Entender modelo plugin
2. `MODULE_SPEC.md` — Contrato técnico
3. `MULTI_REPO_STRUCTURE.md` — Dónde vive el código
4. `_template_module/` — Plantilla de referencia

---

## 🔄 Cambios vs Versión Anterior

**v0.5.x → v0.6.0:**
- ✅ **Nuevo:** Plugin Architecture definido formalmente
- ✅ **Nuevo:** Multi-repo structure documentado
- ✅ **Nuevo:** ADR-006 (plugin-based architecture)
- ✅ **Actualizado:** WORK_PLAN.md (roadmap por componente)
- ✅ **Actualizado:** PROJECT_DEFINITION.md (scope clarificado)

**Core vs Plugins:**
- **Antes:** Todo mezclado en `erp-nexus/` (core + módulos)
- **Ahora:** Core solo + plugins en repos separados

---

## 💡 Conceptos Clave

### **Plugin = Django App independiente**
- Instalable/desinstalable en caliente
- Versionado independiente
- Depende del core (no al revés)
- Ejemplo: `facturacion_ec` es un plugin

### **Core = Framework**
- NO contiene plugins de negocio
- Expone APIs, EventBus, ModuleRegistry
- Proporciona base para plugins

### **Marketplace**
- Catálogo de plugins disponibles
- `install_module --git <url>` los instala
- Admin UI para gestionar

### **Multi-Repo**
- `erp-nexus/` — Core
- `facturacion_ec/` — Plugin 1
- `inventory/` — Plugin 2
- `sdk-nexus/` — SDK
- `nexus-cli/` — CLI

---

## 📞 Canales

- **Core Issues:** `github.com/ERPNexus/erp-nexus/issues`
- **Plugin Issues:** Respectivo repo (facturacion_ec/issues, …)
- **Discussions:** `github.com/ERPNexus/.github/discussions`

---

**¿Listo?** → Empieza con `README.md` → `INSTALL.md` → `ARCHITECTURE_PLUGIN.md`
