# Changelog

All notable changes to ERP Nexus will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/),
and this project adheres to [Semantic Versioning](https://semver.org/).

## [Unreleased] — dev branch

### Changed
- README updated with new architecture (modular, event-driven, integrated CLI)
- Defined stack: Django Ninja, Celery, Redis, PostgreSQL
- Documented management commands for module lifecycle
- Documented marketplace and deployment flows

### Planned (Sprint 2+)
- Settings split (base/dev/production)
- Django Ninja API layer
- Core events app (EventBus)
- Celery integration
- Expanded management commands (from nexus CLI)
- Module dynamic loader
- Docker + docker-compose

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
