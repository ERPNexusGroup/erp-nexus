# Changelog

All notable changes to ERP Nexus will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/),
and this project adheres to [Semantic Versioning](https://semver.org/).

## [0.2.0] — 2026-04-01

### Added
- **Core Events (Event Bus)**: EventLog, EventSubscription models, EventBus API
- **Django Ninja API**: /api/health, /api/modules/, /api/events/ with OpenAPI docs
- **Settings split**: base.py, development.py, production.py
- **Management commands**: install_module, uninstall_module, module (list/info/sync), catalog
- Celery tasks for async event processing
- 14 new tests (events + API)

### Changed
- Settings: single file → split base/dev/production
- urls.py: added /api/ routes for Django Ninja
- pyproject.toml: v0.2.0, added django-ninja, uvicorn, ruff, pytest-django
- Auth password validators enabled in base settings

## [0.1.0] — 2026-03-12

### Added
- Initial Django project structure
- Core apps: users, groups, companies, permissions, dashboard, marketplace
- Superadmin bootstrap command
- sync_modules, enable_module, disable_module management commands
- ModuleCatalogItem and EnabledModule models
- Manifest parsing with AST (safe, no code execution)
- Initial migrations for all core apps

[Unreleased]: https://github.com/ERPNexusGroup/erp-nexus/compare/v0.1.0...dev
[0.1.0]: https://github.com/ERPNexusGroup/erp-nexus/releases/tag/v0.1.0
