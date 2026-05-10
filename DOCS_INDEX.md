# 📚 Documentación ERP Nexus — Índice Maestro

**Última actualización:** 2026-05-10  
**Versión:** 0.5.0-alpha

---

## 🎯 Empezar Aquí

| Si eres… | Lee esto |
|-----------|----------|
| **Nuevo usuario** | `README.md` → `INSTALL.md` |
| **Developer de módulos** | `DEVELOPMENT.md` → `MODULE_SPEC.md` |
| **Contribuyente** | `CONTRIBUTING.md` → `CODING_STANDARDS.md` |
| **DevOps** | `docker-compose.yml` → `INSTALL.md#opción-docker` |
| **Tech Lead** | `ARCHITECTURE.md` → ADRs |

---

## 📄 Documentos por Categoría

### **🏗️ Visión y Arquitectura**

| Documento | Propósito | Enlace |
|-----------|-----------|--------|
| `PROJECT_DEFINITION.md` | Definición del proyecto, objetivos, stack, modelo negocio | [Ver](./PROJECT_DEFINITION.md) |
| `ARCHITECTURE.md` | Diseño técnico profundo, diagramas, decisiones | [Ver](./ARCHITECTURE.md) |
| `REQUIREMENTS.md` | Requisitos funcionales y no-funcionales | [Ver](./REQUIREMENTS.md) |
| `ADR/` | Architecture Decision Records (decisiones técnicas) | [Ver ADRs](./ADR/) |

---

### **📖 Guías de Desarrollo**

| Documento | Propósito | Enlace |
|-----------|-----------|--------|
| `DEVELOPMENT.md` | Guía completa para desarrolladores de módulos | [Ver](./DEVELOPMENT.md) |
| `MODULE_SPEC.md` | Especificación técnica de módulos (contrato) | [Ver](./MODULE_SPEC.md) |
| `CODING_STANDARDS.md` | Reglas de codificación (PEP8, Django style) | [Ver](./CODING_STANDARDS.md) |
| `CONTRIBUTING.md` | Cómo contribuir, git flow, PR checklist | [Ver](./CONTRIBUTING.md) |

---

### **🚀 Instalación y Deploy**

| Documento | Propósito | Enlace |
|-----------|-----------|--------|
| `README.md` | Página principal, quickstart, stack | [Ver](./README.md) |
| `INSTALL.md` | Instalación paso a paso (local + Docker) | [Ver](./INSTALL.md) |
| `docker-compose.yml` | Stack Docker completo (ERP + DB + Redis) | [Ver](./docker-compose.yml) |
| `Makefile` | Comandos shortcuts (make dev, make test, …) | [Ver](./Makefile) |

---

### **🔌 API y Referencia**

| Documento | Propósito | Enlace |
|-----------|-----------|--------|
| `API_REFERENCE.md` | Documentación completa REST API v1 | [Ver](./API_REFERENCE.md) |
| `/api/v1/docs/` | Swagger UI (auto-generado) | *server 실행 시* |
| `/api/v1/schema/` | OpenAPI JSON schema | *server 실행 시* |

---

### **📈 Roadmap y Progreso**

| Documento | Propósito | Enlace |
|-----------|-----------|--------|
| `WORK_PLAN.md` | Roadmap 12 semanas, hitos, timeline | [Ver](./WORK_PLAN.md) |
| `CHANGELOG.md` | Historial de releases y cambios | [Ver](./CHANGELOG.md) |
| `ACTIVE_PROJECTS.md` | Proyectos activos del equipo | [Ver](./ACTIVE_PROJECTS.md) |

---

### **🛠️ Configuración y Herramientas**

| Archivo | Propósito |
|---------|-----------|
| `pyproject.toml` | Config: black, isort, ruff, mypy, pytest, coverage |
| `.pre-commit-config.yaml` | Hooks pre-commit automáticos |
| `.env.example` | Variables de entorno de ejemplo |
| `Makefile` | Comandos `make dev`, `make test`, `make lint` |
| `setup-dev.sh` | Setup automático primera vez |
| `docker/Dockerfile` | Build multi-stage para producción |

---

### **📦 Plantillas**

| Plantilla | Propósito |
|-----------|-----------|
| `_template_module/` | Boilerplate completo para nuevo módulo |
| `modules/README.md` | Cómo crear/instalar módulos |

---

## 🗺️ Estructura de Archivos

```
erp-nexus/
├── README.md                    # Página principal
├── PROJECT_DEFINITION.md        # ¿Qué es ERP Nexus?
├── ARCHITECTURE.md              # Diseño técnico
├── CODING_STANDARDS.md          # Reglas de código
├── DEVELOPMENT.md               # Guía para desarrolladores
├── INSTALL.md                   # Instalación
├── API_REFERENCE.md             # Documentación API
├── REQUIREMENTS.md              # Requisitos
├── MODULE_SPEC.md               # Especificación módulos
├── WORK_PLAN.md                 # Roadmap
├── CHANGELOG.md                 # Historial versions
├── CONTRIBUTING.md              # Cómo contribuir
├── ACTIVE_PROJECTS.md           # Proyectos actuales
│
├── ADR/                         # Decisiones arquitectónicas
│   ├── 001-modular-architecture.md
│   ├── 002-event-bus.md
│   ├── 003-multi-company.md
│   ├── 004-marketplace.md
│   └── 005-api-framework.md
│
├── _template_module/            # Plantilla de módulo
│   ├── __meta__.py
│   ├── apps.py
│   ├── models.py
│   ├── admin.py
│   ├── api/routes.py
│   ├── services/
│   └── tests/
│
├── modules/                     # Módulos en desarrollo
│   └── facturacion_ec/          # Módulo facturación Ecuador
│       ├── models.py
│       ├── api/routes.py
│       ├── services/
│       └── tests/
│
├── apps/                        # Django core apps
│   ├── core_api/
│   ├── core_companies/
│   ├── core_events/
│   └── ...
│
├── docker/
│   └── Dockerfile               # Multi-stage build
├── docker-compose.yml           # Stack completo
├── scripts/
│   └── init-db.sql              # DB initialization
│
├── pyproject.toml               # Herramientas calidad código
├── .pre-commit-config.yaml      # Pre-commit hooks
├── .env.example                 # Variables entorno
├── Makefile                     # Comandos shortcuts
└── setup-dev.sh                 # Setup rápido
```

---

## 📖 Leer en Orden Recomendado

**Primera vez:**

1. `README.md` — Overview rápido (5 min)
2. `PROJECT_DEFINITION.md` — Entender el proyecto (10 min)
3. `ARCHITECTURE.md` — Diseño técnico (15 min)
4. `INSTALL.md` — Instalar localmente (10 min)
5. `DEVELOPMENT.md` — Empezar a desarrollar (20 min)

**Para contribuir:**

1. `CONTRIBUTING.md`
2. `CODING_STANDARDS.md`
3. `ADR/` — Leer ADRs relevantes
4. `MODULE_SPEC.md`

**Para usar API:**

1. `INSTALL.md` → Levantar server
2. `API_REFERENCE.md` → Referencia endpoints
3. `/api/v1/docs/` → Swagger interactivo

---

## 🔄 Documentación Viva

Este proyecto cree en **documentación viva**:

- `README.md` — Se actualiza con cada release
- `CHANGELOG.md` — Cada commit documentado
- `API_REFERENCE.md` — Auto-generado desde docstrings (futuro)
- ADRs — Evolucionan con decisiones

**¿Encontraste un docs error?** → Abre un Issue o PR.

---

**¿Listo para empezar?** → `INSTALL.md` → ¡Manos a la obra!
