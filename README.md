<div align="center">

# 🏢 ERP Nexus

**ERP modular open-source con enfoque en simplicidad extrema**

[![Python](https://img.shields.io/badge/python-3.11+-blue.svg)](https://python.org)
[![Django](https://img.shields.io/badge/django-5.0-green.svg)](https://djangoproject.com)
[![License](https://img.shields.io/badge/license-GPL--3.0-green.svg)](LICENSE)
[![Version](https://img.shields.io/badge/version-0.2.0-blue.svg)](CHANGELOG.md)

[Instalación rápida](#instalación-rápida) • [Arquitectura](#arquitectura) • [Módulos](#gestión-de-módulos) • [API](#api-rest) • [Eventos](#event-bus)

</div>

---

## ¿Qué es?

ERP Nexus es un ERP modular construido en Django. Arranca con un **core mínimo** y crece instalando módulos por el marketplace o manualmente.

### Principios

- **Core mínimo** — Solo lo esencial (users, groups, companies, permissions)
- **Módulos desacoplados** — Comunicación por eventos, no dependencias directas
- **CLI integrado** — Management commands como `manage.py install_module`
- **API moderna** — Django Ninja con OpenAPI auto-generado
- **Fácil de implementar** — De cero a ERP funcional en minutos

## Instalación rápida

```bash
# Opción A: Con nexus CLI (recomendado)
pip install nexus
nexus init mi-erp --with-docker
cd mi-erp

# Opción B: Manual
git clone https://github.com/ERPNexusGroup/erp-nexus.git
cd erp-nexus
git checkout dev

# Configurar
uv sync
cp .env.example .env

# Base de datos
uv run python manage.py migrate

# Superadmin
uv run python manage.py bootstrap_superadmin \
  --username admin \
  --email admin@local \
  --password changeme

# Arrancar
uv run python manage.py runserver
```

Abrir: `http://localhost:8000/admin`

## Arquitectura

```
erp-nexus/
├── erp_nexus/                  # Configuración Django
│   ├── settings/
│   │   ├── base.py             # Settings compartidas
│   │   ├── development.py      # Debug, SQLite, eager tasks
│   │   └── production.py       # PostgreSQL, Redis, Celery
│   ├── asgi.py                 # ASGI entry point
│   ├── wsgi.py                 # WSGI entry point
│   └── urls.py                 # /admin/ + /api/
│
├── apps/                       # Core apps (siempre presentes)
│   ├── core_users/             # Gestión de usuarios
│   ├── core_groups/            # Grupos y roles
│   ├── core_companies/         # Multi-empresa
│   ├── core_permissions/       # Sistema de permisos
│   ├── core_dashboard/         # Dashboard admin
│   ├── core_marketplace/       # Catálogo de módulos
│   ├── core_events/            # 🆕 Event Bus
│   │   ├── models.py           # EventLog, EventSubscription
│   │   ├── bus.py              # EventBus.emit/subscribe
│   │   └── management/         # install_module, etc.
│   └── core_api/               # 🆕 Django Ninja API
│       └── v1/                 # Versionada
│
├── modules/                    # Módulos instalados (externos)
│   ├── accounting_basic/       # Ejemplo: contabilidad
│   ├── invoicing/
│   └── inventory/
│
└── tests/                      # Tests del core
```

## Management Commands (CLI integrado)

### Gestión de módulos

```bash
# Instalar módulo
manage.py install_module ./mi_modulo                  # Desde directorio
manage.py install_module --git https://github.com/...  # Desde git
manage.py install_module --package modulo.npkg         # Desde paquete

# Desinstalar
manage.py uninstall_module mi_modulo

# Listar
manage.py module list

# Info detallada
manage.py module info mi_modulo

# Sincronizar filesystem ↔ DB
manage.py module sync
```

### Sistema

```bash
# Superadmin
manage.py bootstrap_superadmin --username admin --email admin@local --password pass

# Django estándar
manage.py migrate
manage.py runserver
manage.py createsuperuser
manage.py collectstatic
```

## Gestión de módulos

### Instalar un módulo

```bash
# 1. Desde directorio local
manage.py install_module ./accounting_basic

# 2. Desde repositorio git
manage.py install_module --git https://github.com/ERPNexusGroup/accounting-ec.git

# 3. Desde paquete .npkg/.zip
manage.py install_module --package accounting_basic-0.1.0.npkg
```

### Crear un módulo

Usa **SDK Nexus**:

```bash
pip install sdk-nexus
sdk-nexus create mi_modulo --type=module --domain=accounting
cd mi_modulo
# Desarrollar...
sdk-nexus validate ./
sdk-nexus package ./
manage.py install_module --package ./dist/mi_modulo-0.1.0.npkg
```

### Estructura de un módulo

```
mi_modulo/
├── __meta__.py           # Metadata (validada por SDK)
├── __init__.py
├── apps.py               # Django AppConfig
├── admin.py              # Admin registration
├── core/
│   └── models.py         # Modelos Django
├── events/
│   └── handlers.py       # Event handlers
├── api/
│   └── endpoints.py      # API endpoints (Django Ninja)
├── tests/
│   └── test_meta.py
└── migrations/
```

### __meta__.py

```python
technical_name = "mi_modulo"
display_name = "Mi Módulo"
component_type = "module"
package_type = "extension"
domain = "accounting"

python = ">=3.11"
erp_version = ">=0.2.0"

version = "0.1.0"
license = "MIT"
keywords = ["erp", "nexus", "accounting"]
description = "Descripción del módulo"

depends = []

registry_flags = {
    "models": True,
    "api": True,
    "workers": False,
    "tasks": False,
}
```

## API REST

Django Ninja con documentación auto-generada.

### Endpoints disponibles

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | `/api/health` | Health check |
| GET | `/api/modules/` | Lista módulos instalados |
| GET | `/api/modules/stats` | Estadísticas de módulos |
| GET | `/api/modules/{name}` | Detalle de módulo |
| GET | `/api/events/` | Historial de eventos |
| GET | `/api/events/stats` | Estadísticas del Event Bus |
| POST | `/api/events/emit` | Emitir evento (debug) |
| GET | `/api/docs` | Swagger UI |

### Ejemplo de respuesta

```json
// GET /api/modules/stats
{
  "total": 3,
  "active": 2,
  "inactive": 1
}

// GET /api/events/stats
{
  "total": 42,
  "pending": 0,
  "failed": 1
}
```

### API de módulos

Los módulos pueden exponer sus propios endpoints. Ver `accounting_basic/api/endpoints.py` como ejemplo.

## Event Bus

Comunicación desacoplada entre módulos mediante eventos.

### Emitir evento

```python
from apps.core_events.bus import EventBus

# Desde un módulo
EventBus.emit(
    event_type="invoice.created",
    source="invoicing",
    payload={"invoice_id": 42, "total": 1500.00},
)
```

### Suscribirse a evento

```python
from apps.core_events.bus import EventBus

# En el archivo events/handlers.py del módulo
def on_payment_received(payload: dict):
    invoice_id = payload["invoice_id"]
    # Procesar pago...

# Registrar suscripción
EventBus.subscribe(
    event_type="payment.received",
    subscriber_module="accounting",
    handler_path="accounting.events.handlers.on_payment_received",
)
```

### Ver eventos

```bash
# Por API
curl http://localhost:8000/api/events/

# Por admin Django
# Ir a /admin/core_events/eventlog/
```

### Estadísticas

```python
from apps.core_events.bus import EventBus

stats = EventBus.get_stats()
# {'total_events': 42, 'pending_events': 0, 'failed_events': 1, 'subscriptions': 5}
```

## Settings

### Desarrollo (default)

```bash
# settings/__init__.py importa development.py
uv run python manage.py runserver
```

- SQLite
- DEBUG = True
- Celery eager (sync)

### Producción

```bash
DJANGO_SETTINGS_MODULE=erp_nexus.settings.production
```

- PostgreSQL
- Redis (cache + Celery)
- Security headers
- HSTS, SSL redirect

### Variables de entorno

```bash
# Requeridas en producción
DJANGO_SECRET_KEY=...
DJANGO_ALLOWED_HOSTS=erp.miempresa.com

# Database
POSTGRES_DB=erp_nexus
POSTGRES_USER=erp_nexus
POSTGRES_PASSWORD=changeme

# Redis
REDIS_URL=redis://localhost:6379/0
```

## Stack técnico

| Componente | Tecnología |
|-----------|------------|
| Framework | Django 5.0 |
| API | Django Ninja |
| Admin UI | django-jazzmin |
| ASGI Server | Uvicorn + Gunicorn |
| Database | PostgreSQL |
| Cache | Redis |
| Tasks | Celery |
| Testing | pytest + pytest-django |
| Linting | Ruff |
| Package Manager | uv |

## Producción

### Con nexus CLI

```bash
nexus server setup --domain erp.miempresa.com
nexus server start
```

### Manual

```bash
# Gunicorn + Uvicorn
gunicorn erp_nexus.asgi:application \
  -w 4 \
  -k uvicorn.workers.UvicornWorker \
  --bind 127.0.0.1:8000

# Collect static
python manage.py collectstatic --noinput
```

### Docker

```yaml
# docker-compose.yml (generado por nexus init --with-docker)
services:
  web:
    build: .
    command: gunicorn erp_nexus.asgi:application -w 4 -k uvicorn.workers.UvicornWorker
    ports: ["8000:8000"]
  db:
    image: postgres:16-alpine
  redis:
    image: redis:7-alpine
```

## Ejemplo: accounting_basic

Módulo de ejemplo incluido con el repo. Demuestra el flujo completo:

```bash
# Ya instalado en modules/
manage.py module list
# accounting_basic 0.1.0 ✅ active

# Probar
python -c "
from accounting_basic.core.models import Account, JournalEntry
Account.objects.create(code='1.1.01', name='Caja', account_type='asset')
"
```

Ver [modules/accounting_basic/](modules/accounting_basic/) para el código fuente.

## Ecosistema ERP Nexus

```
┌─────────────────────────────────────────────────┐
│  sdk-nexus  →  Dev Toolkit                      │
│  sdk-nexus create/validate/package              │
├─────────────────────────────────────────────────┤
│  nexus (CLI)  →  Bootstrap/Deploy               │
│  nexus init / server / update                   │
├─────────────────────────────────────────────────┤
│  erp-nexus  →  ERP Core (este repo)             │
│  Django + API + Events + Management Commands    │
├─────────────────────────────────────────────────┤
│  Módulos  →  accounting, invoicing, inventory...│
│  Creados con SDK, instalados en ERP             │
└─────────────────────────────────────────────────┘
```

## Contribuir

Ver [CONTRIBUTING.md](CONTRIBUTING.md) para guías de contribución, git flow y convenciones.

## Licencia

GPL-3.0-or-later — Ver [LICENSE](LICENSE)
