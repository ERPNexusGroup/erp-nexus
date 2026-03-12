# PROYECTO: ERP NEXUS - CORE

## 🎯 OBJETIVO PRINCIPAL
Construir el core del ERP basado en Django con módulos esenciales: autenticación, usuarios, permisos, grupos y marketplace.

## ⚙️ STACK TÉCNICO
- Python 3.11+
- Gestor de paquetes: `uv` (no pip)
- Framework: Django 5.0
- Validación: Pydantic + semantic-version
- Testing: pytest

## 🚫 RESTRICCIONES CRÍTICAS
1. NO usar frameworks frontend (React/Vue) en esta fase
2. NO arquitectura microservicios (monolito modular Django-style)
3. Enfocar en core funcional y extensible

## 📂 ESTRUCTURA DE PROYECTO

erp-nexus/
├── .gitignore
├── pyproject.toml          # Configuración uv + dependencias
├── README.md               # Documentación inicial
├── erp_nexus/              # Proyecto Django (core)
│   ├── __init__.py
│   ├── settings.py
│   ├── urls.py
│   ├── asgi.py
│   └── wsgi.py
├── apps/                   # Apps base del core
│   ├── core_auth/
│   ├── core_users/
│   ├── core_permissions/
│   ├── core_groups/
│   └── core_marketplace/
├── modules/                # Directorio destino de módulos (vacío inicialmente)
└── tests/
    ├── __init__.py
    └── test_core_models.py # Tests mínimos de core

## 🧪 Core Django (Bootstrap)
Proyecto base para comenzar el core del ERP con módulos esenciales:
autenticación, usuarios, permisos, grupos y marketplace.

## 👤 Superadmin (arranque inicial)
Puedes usar el comando estándar de Django:
```bash
uv run python manage.py createsuperuser
```

O el comando bootstrap (no interactivo):
```bash
uv run python manage.py bootstrap_superadmin --username admin --email admin@local --password 123456
```

Luego, en el panel administrativo puedes crear usuarios, grupos y permisos.

## 🧩 Sincronizar módulos instalados
El ERP es el source of truth del catálogo interno. Después de instalar módulos con el CLI,
ejecuta el sync para registrar/actualizar en la base de datos:

```bash
uv run python manage.py sync_modules
```

El comando escanea `modules/`, valida cada `__meta__.py` con AST seguro y actualiza
el modelo `ModuleCatalogItem`. Los módulos removidos del filesystem quedan marcados
como `inactive`.
