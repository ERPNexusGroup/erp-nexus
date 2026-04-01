# ERP Nexus — Core del ERP Modular Open Source

ERP modular minimalista en Django. Arranca con lo mínimo y crece instalando módulos.

## ¿Qué es?

Un ERP construido en Django que:
- Arranca solo con el core mínimo (users, groups, companies, permissions, dashboard)
- Se amplía instalando módulos (accounting, invoicing, inventory, etc.)
- Los módulos se comunican por eventos (no dependencias directas)
- Tiene su CLI integrado como Django management commands

## Stack

- Python 3.11+
- Django 5.x
- Django Ninja (API)
- PostgreSQL
- Redis (cache + events)
- Celery (background tasks)
- django-jazzmin (admin UI)

## Instalación rápida

```bash
# Clonar y configurar
git clone https://github.com/ERPNexusGroup/erp-nexus.git
cd erp-nexus
git checkout dev
uv sync

# Base de datos
uv run python manage.py migrate

# Superadmin
uv run python manage.py bootstrap_superadmin --username admin --email admin@local --password changeme

# Arrancar
uv run python manage.py runserver
```

## Management Commands (CLI integrado)

```bash
# Gestión de módulos
python manage.py install_module ./mi_modulo        # Instalar desde directorio
python manage.py install_module --git URL          # Instalar desde git
python manage.py install_module --package file.zip # Instalar desde paquete
python manage.py uninstall_module mi_modulo        # Desinstalar
python manage.py update_module mi_modulo           # Actualizar
python manage.py module list                       # Listar instalados
python manage.py module info mi_modulo             # Info detallada
python manage.py sync_modules                      # Sincronizar filesystem ↔ DB

# Marketplace
python manage.py catalog search --category accounting
python manage.py catalog install mi_modulo

# Arranque
python manage.py bootstrap_superadmin --username admin --email admin@local --password pass
```

## Estructura del proyecto

```
erp-nexus/
├── erp_nexus/              # Settings Django
│   ├── settings/
│   │   ├── base.py
│   │   ├── development.py
│   │   └── production.py
│   ├── asgi.py
│   ├── wsgi.py
│   └── urls.py
├── apps/                   # Core apps (siempre presentes)
│   ├── core_users/
│   ├── core_groups/
│   ├── core_companies/
│   ├── core_permissions/
│   ├── core_dashboard/
│   ├── core_marketplace/
│   ├── core_events/        # Event Bus entre módulos
│   └── core_api/           # Django Ninja API
├── modules/                # Módulos instalados (externos)
├── management/commands/    # CLI integrado
└── tests/
```

## Crear módulos

Usa el SDK Nexus para crear módulos compatibles:

```bash
pip install sdk-nexus
sdk-nexus create hotel_reservations --type=module
# ... desarrolla tu módulo ...
sdk-nexus validate ./hotel_reservations
# Luego instálalo en el ERP:
python manage.py install_module ./hotel_reservations
```

## Despliegue

```bash
# Configurar servidor de producción
nexus server setup --env production
nexus server start

# O manualmente:
gunicorn erp_nexus.asgi:application -w 4 -k uvicorn.workers.UvicornWorker
```

## Licencia

GPL-3.0-or-later
