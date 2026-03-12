# PROYECTO: ERP NEXUS - FASE 1A (SDK Y HERRAMIENTAS)

## 🎯 OBJETIVO PRINCIPAL
Crear un SDK minimalista pero robusto que permita a un desarrollador Python crear, validar e instalar un módulo funcional en < 15 minutos, con garantía de rollback automático ante fallos.

## ⚙️ STACK TÉCNICO OBLIGATORIO
- Python 3.11+
- Gestor de paquetes: `uv` (no pip)
- Framework: Django 5.0 (solo para core futuro, NO para SDK)
- CLI: Click 8.1.7 + Rich 13.7.0
- Validación: Pydantic 2.6.0 + semantic-version 2.10.0
- Plantillas: cookiecutter 2.5.0 (solo para generar estructura)
- Testing: pytest (mínimo para validación)

## 🚫 RESTRICCIONES CRÍTICAS
1. NO usar frameworks frontend (React/Vue) en esta fase
2. NO dependencias complejas (máx 10 dependencias totales)
3. NO arquitectura microservicios (monolito modular Django-style)
4. Rollback 100% automático - cero datos huérfanos tras desinstalación
5. Tiempo instalación módulo < 30 segundos en hardware promedio

## 📂 ESTRUCTURA DE PROYECTO

erp-nexus/
├── .gitignore
├── pyproject.toml          # Configuración uv + dependencias
├── README.md               # Documentación inicial
├── cli/
│   ├── __init__.py
│   ├── main.py             # Punto de entrada CLI (click)
│   ├── commands/
│   │   ├── __init__.py
│   │   ├── creator.py      # Comando 'create'
│   │   ├── validator.py    # Comando 'validate'
│   │   ├── installer.py    # Comando 'install'
│   │   └── uninstaller.py  # Comando 'uninstall'
│   └── templates/
│       └── basic/          # Template mínimo funcional
│           ├── module.json.jinja
│           ├── models.py.jinja
│           ├── views.py.jinja
│           ├── urls.py.jinja
│           ├── __init__.py.jinja
│           └── README.md.jinja
├── core/
│   └── __init__.py
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
├── module_system/
│   ├── __init__.py
│   ├── contracts.py        # Protocolos Pydantic/typing
│   ├── validator.py        # Validador de módulos
│   └── installer.py        # Instalador transaccional
├── modules/                # Directorio destino de módulos (vacío inicialmente)
└── tests/
    ├── __init__.py
    └── test_cli.py         # Tests mínimos para CLI

## 🧪 Core Django (Bootstrap)
Proyecto base para comenzar el core del ERP con módulos esenciales:
autenticación, usuarios, permisos, grupos y marketplace.
