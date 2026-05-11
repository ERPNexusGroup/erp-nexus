<div align="center">

# 🏢 ERP Nexus

**ERP modular open-source con enfoque en simplicidad extrema**

[![Python](https://img.shields.io/badge/python-3.12+-blue.svg)](https://python.org)
[![Django](https://img.shields.io/badge/django-5.0-green.svg)](https://djangoproject.com)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Version](https://img.shields.io/badge/version-0.5.0-blue.svg)](CHANGELOG.md)

[Instalación rápida](#instalación-rápida) • [Arquitectura](#arquitectura) • [Documentación](#documentación) • [Módulos](#módulos) • [API](#api-rest)

</div>

---

## 🚀 ¿Qué es?

**ERP Nexus** es un framework Django modular para construir ERP desde bloques independientes.

Instala solo los módulos que necesitas, actualízalos por separado, y crea tus propios módulos sin tocar el core.

### 🎯 Principios

- ✅ **Core mínimo** — Solo lo esencial (users, companies, permissions, marketplace)
- ✅ **Módulos desacoplados** — Comunicación por Event Bus, no imports directos
- ✅ **Marketplace integrado** — Descargar/activar módulos desde UI o CLI
- ✅ **Multi-tenant nativo** — Una instancia, múltiples empresas (data isolation)
- ✅ **API-first** — Todo exponible vía REST (Django Ninja + OpenAPI)
- ✅ **Open Source** — MIT License, comunidad abierta

---

## 📦 Instalación Rápida

```bash
# 1. Clonar
git clone https://github.com/ERPNexus/erp-nexus.git
cd erp-nexus

# 2. Instalar deps con uv (ultra-rápido)
uv sync
source .venv/bin/activate  # o .venv\Scripts\activate en Windows

# 3. Migraciones + superadmin
uv run python manage.py migrate
uv run python manage.py bootstrap_superadmin \
  --username admin \
  --email admin@local \
  --password admin123

# 4. Levantar servidor
uv run python manage.py runserver
```

**Abrir:** http://localhost:8000/admin

---

## 🐳 Docker Compose (Recomendado)

```bash
# Levantar todo (PostgreSQL + Redis + ERP Nexus)
docker-compose up -d

# Migraciones
docker-compose exec web uv run python manage.py migrate
docker-compose exec web uv run python manage.py bootstrap_superadmin \
  --username admin \
  --email admin@local \
  --password admin123

# Acceder
open http://localhost:8000/admin
```

---

## 🏗️ Arquitectura

```
┌─────────────────────────────────────────────────────────────┐
│                    CLIENTE (Empresa)                        │
│    Usa solo los módulos que necesita: facturación + stock   │
└───────────────────────────┬─────────────────────────────────┘
                            │
┌───────────────────────────▼─────────────────────────────────┐
│              ERP NEXUS CORE (Framework)                      │
│  ┌────────────────────────────────────────────────────────┐ │
│  │ Django + Multi-tenant + Marketplace + Event Bus       │ │
│  │  - Core apps: users, companies, permissions, events   │ │
│  │  - ModuleRegistry: catálogo + instalador              │ │
│  └────────────────────────────────────────────────────────┘ │
└───────────────────────────┬─────────────────────────────────┘
                            │
         ┌───────────────────┼───────────────────┐
         │                   │                   │
┌────────▼────────┐  ┌──────▼──────┐  ┌────────▼────────┐
│  facturacion_ec │  │  inventory  │  │     sales       │
│   (repo git)    │  │  (repo git) │  │  (repo git)     │
└──────────────────┘  └─────────────┘  └─────────────────┘
```

**Características clave:**
- Cada módulo es **independiente** (repo separado)
- **Event Bus** — Comunicación sin acoplamiento
- **Company-bound** — Todos los datos tienen `company_id`
- **Marketplace** — Instala/desinstala módulos en caliente

---

## 📚 Documentación

| Documento | Descripción |
|-----------|-------------|
| [`README.md`](README.md) | Este archivo — introducción |
| [`INSTALL.md`](.architecture/INSTALL.md) | Guía de instalación paso a paso |
| [`DEVELOPMENT.md`](.architecture/DEVELOPMENT.md) | Cómo desarrollar módulos |
| [`CODING_STANDARDS.md`](.architecture/CODING_STANDARDS.md) | Reglas de codificación |
| [`CONTRIBUTING.md`](.architecture/CONTRIBUTING.md) | Cómo contribuir |
| [`ARCHITECTURE.md`](.architecture/ARCHITECTURE.md) | Diseño técnico profundo |
| [`MODULE_SPEC.md`](.architecture/MODULE_SPEC.md) | Cómo construir módulos |
| [`WORK_PLAN.md`](.architecture/WORK_PLAN.md) | Roadmap y hitos |
| [`API_REFERENCE.md`](.architecture/API_REFERENCE.md) | API REST completa |
| [`CHANGELOG.md`](CHANGELOG.md) | Historial de releases |

### **Decisiones Arquitectónicas (ADRs)**

- [ADR-001: Modular Architecture](./ADR/001-modular-architecture.md)
- [ADR-002: Event Bus](./ADR/002-event-bus.md)
- [ADR-003: Multi-Company Strategy](./ADR/003-multi-company.md)
- [ADR-004: Marketplace Installation](./ADR/004-marketplace.md)
- [ADR-005: API Framework (Django Ninja)](./ADR/005-api-framework.md)

---

## 🔧 Management Commands

```bash
# Módulos
uv run python manage.py module list                    # Listar instalados
uv run python manage.py install_module ./mi_modulo     # Instalar desde dir
uv run python manage.py install_module --git <url>     # Instalar desde git
uv run python manage.py uninstall_module facturacion_ec
uv run python manage.py module enable facturacion_ec
uv run python manage.py module disable inventory

# Sistema
uv run python manage.py migrate                         # Migraciones
uv run python manage.py bootstrap_superadmin ...        # Crear admin
uv run python manage.py loaddata fixtures.json         # Cargar datos
```

---

## 📡 API Endpoints

| Endpoint | Método | Descripción |
|----------|--------|-------------|
| `/api/health` | GET | Health check |
| `/api/modules/` | GET | Listar módulos instalados |
| `/api/modules/{name}/` | GET | Detalle de módulo |
| `/api/events/` | GET | Historial Event Bus |
| `/api/events/stats` | GET | Estadísticas eventos |
| `/api/v1/docs/` | GET | Swagger UI (OpenAPI) |
| `/api/v1/schema/` | GET | OpenAPI JSON |

**Módulo `facturacion_ec`:**
- `GET /api/v1/facturacion_ec/invoices/`
- `POST /api/v1/facturacion_ec/invoices/`
- `GET /api/v1/facturacion_ec/invoices/{id}/`
- `GET /api/v1/facturacion_ec/invoices/{id}/xml/`
- `GET /api/v1/facturacion_ec/customers/`
- `POST /api/v1/facturacion_ec/customers/`

Ver [`.architecture/API_REFERENCE.md`](.architecture/API_REFERENCE.md) para detalles.

---

## 🧩 Módulos Oficiales

| Módulo | Estado | Descripción |
|--------|--------|-------------|
| **facturacion_ec** | ✅ v0.1.0 | Facturación electrónica SRI Ecuador |
| **inventory** | 🚧 En desarrollo | Gestión de inventarios y stock |
| **sales** | 📋 Planeado | Cotizaciones, órdenes, facturación |
| **accounting** | 💡 Futuro | Contabilidad básica |

---

## 🛠️ Stack Tecnológico

| Capa | Tecnología |
|------|------------|
| **Framework** | Django 5.0 + Python 3.12 |
| **API** | Django Ninja (OpenAPI auto) |
| **Database** | PostgreSQL 15+ |
| **Cache** | Redis |
| **Async Tasks** | Celery + Redis (futuro) |
| **Auth** | Django JWT (simplejwt) |
| **Admin UI** | Jazzmin theme |
| **Package Manager** | `uv` (ultra-rápido) |
| **Tests** | pytest + pytest-django |
| **Linting** | Ruff + mypy |
| **CI/CD** | GitHub Actions (futuro) |
| **Docker** | Docker + docker-compose |

---

## 🌱 Crear un Módulo Nuevo

### Con SDK (recomendado):

```bash
# Instalar SDK
uv pip install sdk-nexus

# Crear módulo
sdk-nexus create mi_modulo --type=module --domain=accounting

# Validar
sdk-nexus validate ./mi_modulo

# Empaquetar
sdk-nexus package ./mi_modulo

# Instalar
python manage.py install_module --package ./dist/mi_modulo-0.1.0.npkg
```

### Manual (copiar plantilla):

```bash
cp -r _template_module/ mi_nuevo_modulo/
cd mi_nuevo_modulo
# Editar __meta__.py, models.py, etc.
```

---

## 🧪 Testing

```bash
# Todos los tests
uv run pytest

# Módulo específico
uv run pytest facturacion_ec/tests/ -v

# Con cobertura
uv run pytest --cov=facturacion_ec --cov-report=html

# Linting
ruff check .
mypy .
```

---

## 🤝 Contribuir

¡Contribuciones bienvenidas! Por favor lee [`.architecture/CONTRIBUTING.md`](.architecture/CONTRIBUTING.md) antes de enviar PR.

1. Fork el repo
2. Crear branch: `git checkout -b feat/mi-feature`
3. Commit siguiendo [Conventional Commits](#-commits)
4. Push y abrir PR a `dev`

---

## 📄 License

MIT License — Ver [`LICENSE`](LICENSE)

---

## 📞 Contacto

- **Issues:** [GitHub Issues](https://github.com/ERPNexus/erp-nexus/issues)
- **Discussions:** [GitHub Discussions](https://github.com/ERPNexus/erp-nexus/discussions)
- **Email:** dev@erpnexus.ec
- **Website:** erpnexus.ec (futuro)

---

<div align="center">
Made with ❤️ by ERP Nexus Team
</div>
