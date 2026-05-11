# Changelog — ERP Nexus

Todas las changes notables serán documentadas aquí.

El formato está basado en [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
y este proyecto adhiere a [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

### 🚧 En Desarrollo (v0.6.0-dev)

#### **Added**
- Modular architecture con ModuleRegistry ([ADR-001](./ADR/001-modular-architecture.md))
- EventBus para comunicación desacoplada ([ADR-002](./ADR/002-event-bus.md))
- Multi-company middleware ([ADR-003](./ADR/003-multi-company.md))
- Marketplace Module Installation Flow ([ADR-004](./ADR/004-marketplace.md))
- Django Ninja API framework ([ADR-005](./ADR/005-api-framework.md))
- Plantilla de módulo `_template_module/` para desarrollo rápido
- Codificación de reglas en [`.architecture/CODING_STANDARDS.md`](.architecture/CODING_STANDARDS.md)
- Plan de trabajo detallado en [`.architecture/WORK_PLAN.md`](.architecture/WORK_PLAN.md)
- Guía de desarrollo [`.architecture/DEVELOPMENT.md`](.architecture/DEVELOPMENT.md)
- Guía de instalación [`.architecture/INSTALL.md`](.architecture/INSTALL.md)
- API Reference completa [`.architecture/API_REFERENCE.md`](.architecture/API_REFERENCE.md)
- ADRs (Architecture Decision Records) en `ADR/`
- Contributing guide [`.architecture/CONTRIBUTING.md`](.architecture/CONTRIBUTING.md)
- Management command `refresh_catalog` (GitHub org scan + upsert catalog)
- Auto-creación de ModuleRegistry default (GitHub Official) via signal + command fallback
- `parse_meta_file` utility (AST parser seguro para `__meta__.py`)
- Settings: GITHUB_TOKEN, GITHUB_ORG
- Admin improvements: ModuleRegistry sync button, ModuleLicense seat usage bar
- Fix: `settings.timezone.now()` → `timezone.now()` en refresh_catalog
- Tests: TestGitHubRegistry (2 tests) → **19 passing** total marketplace

#### **Fixed**
- Secuencial de facturas duplicado (todos tenían mismo número)
- `get_next_sequential` ordenaba por `-number` (string) en vez de por `-id`
- Import relativo mal en `code_unique.py` (`.models` → `..models`)
- API endpoints requerían `request.active_company` (no disponible sin auth)

#### **Changed**
- Migración de Gemini (agotado) a Gemma 4 31B en Career-Ops pipeline
- Refactor `facturacion_ec` para soporte multi-company
- Estructura de directorios: módulos en `modules/` (dev) y `~/.erp-nexus/modules/` (prod)

---

## [0.5.0] — 2026-05-04

### **Added**
- Sistema Career-Ops completo con OpenRouter Free Tier
- Dashboard web v3.3 con 5 pestañas y auto-refresh 15s
- API Flask mejorada con `distribucion_estados`
- Tracking IDs únicos por postulación
- Notificaciones Telegram diarias
- Integración OpenRouter (google/gemma-4-31b-it)
- Soporte múltiples modelos OpenRouter Free Tier

### **Migration**
- Gemini → Gemma 4 31B (cuota agotada)
- Flask → OpenRouter API directa

---

## [0.4.0] — 2026-05-03

### **Added**
- Dashboard web v3.2 mejorado
- Filtros por estado en timeline
- Gráficos de distribución salarial
- KPI cards animados
- Sync tabs con timeline filter

---

## [0.3.0] — 2026-05-01

### **Added**
- Pipeline automatizado de búsqueda de empleo
- Scoring IA con OpenRouter
- CV en markdown con perfil personalizado
- Crontab system (L-V 9AM, 2PM, 5PM)
- Logs estructurados en `logs/cron_*.log`

---

## [0.2.0] — 2026-04-30

### **Added**
- Sistema de evaluación de crédito
- Microservicios Quarkus + REST reactive
- Frontend React + TypeScript
- Validación cédula Módulo 10
- Documentación completa (README, ARCHITECTURE, DEVELOPMENT)

---

## [0.1.0] — 2026-04-15

### **Added**
- Proyecto inicial ERP Nexus
- Core Django configurado (11 apps)
- Multi-company middleware
- ActiveCompanyMiddleware
- ModuleRegistry basic
- Django Ninja API base

---

## Versionando

### **v0.x.y** — Pre-release
- `0.1.0` — Primera funcional working
- `0.2.0` — Features nuevas (backward-compatible)
- `0.2.1` — Bugfix

### **v1.0.0** — Primer estable
- API estable (no breaking changes)
- Documentación completa
- Test coverage >80%

---

## Tipos de Cambio

| Tipo | Ejemplo | Version bump |
|------|---------|--------------|
| **Added** | Nueva feature | `0.1.0` → `0.2.0` |
| **Changed** | Modificación existente (backward-compat) | `0.2.0` → `0.2.1` |
| **Deprecated** | Feature obsoleto (aún funciona) | `0.2.1` → `0.3.0` |
| **Removed** | Feature eliminado | `0.3.0` → `0.4.0` |
| **Fixed** | Bug fix | `0.4.0` → `0.4.1` |
| **Security** | Vulnerabilidad corregida | `0.4.1` → `0.4.2` |
