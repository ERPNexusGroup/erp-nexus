# PAUL State — ERP Nexus Core (Hybrid Architecture)

**Project:** ERP Nexus Core (Framework + Essential Modules)
**Architecture:** Hybrid — Essential modules in core, Optional modules as plugins
**Current Phases:**
  • Phase M5-A.2 — Commission Calculator Service (APPLIED — COMPLETE)
  • Phase M5-A.3 — Bank Integration Layer (IN PROGRESS)
  • Phase M5 — Feature Extensions (multi-tenant, analytics, API v2, Sentry — PLANNED)
**Loop Position:** APPLY COMPLETE (0.6 / 0.6.2 / 1.1 / 1.2 / 1.3 / 1.4 / 2.1 / 2.2 / 2.3 / M4)
**Last Completed:** Phase M5-A.2 — Commission Calculator + Signals (2026-05-13) ✅
****Current Milestone:** M5 — Feature Extensions (Phase M5-A.2 COMPLETE | M5-A.3 IN PROGRESS)
**Branch:** `main`

## ✅ Phase 0.6 — Hybrid Restructure (COMPLETED)

**Status:** ✅ ALL 9 TASKS DONE

| Task | Descripción | Estado |
|------|-------------|--------|
| 0.6.1 | Definir arquitectura híbrida | ✅ |
| 0.6.2 | Mover `facturacion_ec/` → `apps/facturacion/` | ✅ |
| 0.6.3 | Eliminar módulos demo | ✅ |
| 0.6.4 | Clean core settings | ✅ |
| 0.6.5 | Crear `apps/inventory/` | ✅ |
| 0.6.6 | Crear sales, purchases, notifications, print_manager | ✅ |
| 0.6.7 | Update documentation | ✅ |
| 0.6.8 | Rebuild graph + finalize state | ✅ |
| 0.6.9 | Validation | ✅ |

**Result:** 17 Django apps (11 core + 6 essential). ERP funcional out-of-the-box.

---

## ✅ Phase M5-A.1 — Payout Automation — Models + Migrations (APPLIED — COMPLETE)

**Fecha:** 2026-05-13
**Estado:** ✅ APPLIED + UNIFY COMPLETE
**Skill:** coding-agent
**Commits:** `feat(payout): models + migrations + admin`

**Objetivo:** Schema de datos para payout automation (5 modelos).

**Entregables:**
- [x] App `payouts` creada (`apps/payouts/`) y registrada en INSTALLED_APPS
- [x] 5 modelos implementados: BankAccount, CommissionRule, Payout, PayoutItem, PayoutConfig
- [x] Admin registration funcional (list_display, filters, inlines, actions)
- [x] Migración `0001_initial.py` generada y aplicada
- [x] Tests: 32 model tests passing ✅
- [x] Django check: 0 issues ✅

**Detalles modelos:**
- `BankAccount`: 8 bancos ecuatorianos + tipos cuenta + holder + RUT
- `CommissionRule`: módulo (sales/purchases/marketplace), tipo (percentage/fixed), umbrales min/max
- `Payout`: reference único (PAY-YYYYMMDD-NNNN), status workflow (6 estados), FK company + bank_account
- `PayoutItem`: FK a Order/PurchaseOrder nullable, cálculo neto = gross - retention
- `PayoutConfig`: OneToOne Company, auto_approve, retention_rate, payout_schedule, notify_emails

**Testing:** 32 tests (model validation, __str__, ordering, JSONField, constraints)

---

## ✅ Phase M5-A.2 — Commission Calculator Service + Signals (APPLIED — COMPLETE)

**Fecha:** 2026-05-13
**Estado:** ✅ APPLIED + UNIFY COMPLETE
**Skill:** coding-agent
**Commits:** `feat(payout): commission calculator service + signals + management command` (0a1a25f)

**Objetivo:** Servicio de cálculo de comisiones + signals automáticos + command.

**Entregables:**
- [x] Modelo `CommissionRecord` (FK Order/PurchaseOrder, status workflow, indexes)
- [x] `CommissionCalculator` service (`services.py`) — gross/net/retention logic, min/max thresholds
- [x] Signal `post_save` en Order (status='completed') → auto-create CommissionRecord
- [x] Management command `calculate_commissions` (--date, --dry-run)
- [x] `get_pending_commissions(company, start_date, end_date)` — date/datetime flexible
- [x] Bulk helpers: `bulk_create_from_orders`, `bulk_create_from_purchase_orders`
- [x] Tests: 48 tests passing (models + services)
- [x] Django check: 0 issues ✅

**Tests detalle:**
- CommissionRecord model tests (12)
- CommissionCalculator unit tests (25)
- Signal integration tests (8)
- Management command tests (3)

**Fixed:** `created_at` default changed from `auto_now_add=True` to `default=timezone.now` para permitir assignment en tests.

---

## 🔄 Phase M5-A.3 — Bank Integration Layer (IN PROGRESS)

**Fecha:** 2026-05-13
**Estado:** ✅ APPLIED + UNIFY COMPLETE
**Duración:** ~3h
**Commits:** `feat(pagebuilder): API REST + public views + renderer`

**Objetivo:** Completar módulo core_pagebuilder con API REST extendida + servicio de renderizado + frontend.

**Entregables (9 tasks — 8/9 implementados, 1 documentación opcional):**
- [x] 0.6.2.1 — Serializers + API Foundation (`serializers.py`, extensión `apps/core_api/v1/pages.py`)
- [x] 0.6.2.2 — Layout Validation Schema (`validators.py` con JSON schema + pydantic)
- [x] 0.6.2.3 — Render Service (`renderer.py` — `PageRenderer` con `mark_safe`, templates inline)
- [x] 0.6.2.4 — Template Views + Public URLs (`views_public.py`, `urls_public.py`)
- [x] 0.6.2.5 — Frontend Components Library (`page-builder.css`, `page_detail.html`, `base.html`)
- [x] 0.6.2.6 — Management Commands (`create_demo_pages`, `publish_all` — páginas demo creadas)
- [x] 0.6.2.7 — Manual verification (HTML pages 200 ✅, JSON render endpoint 200 ✅, API endpoints funcionales ✅)
- [ ] 0.6.2.8 — Documentation (OPCIONAL — funcionalidad ya documentada en código)
- [x] 0.6.2.9 — Integration & Polish (admin preview button, 3 demo pages: home/about/contact)

**Rutas verificadas:**
- `GET  /pages/home/`       → HTML público (200)
- `GET  /pages/about/`      → HTML público (200)
- `GET  /pages/contact/`    → HTML público (200)
- `GET  /pages/<slug>/render/` → JSON con HTML renderizado (200)
- `GET  /api/v1/pages/`     → API protegida JWT (401 esperado)

**Demo pages creadas:**
- Home: `Inicio` (bienvenida + columnas 3 + CTA)
- About: `Acerca de` (hero image + texto)
- Contact: `Contacto` (formulario HTML)

---

## 🔹 Phase 1.1 — Marketplace Foundation (APPLIED — COMPLETE)

**Status:** ✅ ALL 7 TASKS DONE

| Task | Descripción | Estado |
|------|-------------|--------|
| 1.1.1 | Extender ModuleCatalogItem metadata | ✅ |
| 1.1.2 | Auto-Discover GitHub Organization (scan_github_org) | ✅ |
| 1.1.3 | Install/Uninstall management commands | ✅ |
| 1.1.4 | Dynamic App Loading (modules_enabled.py watcher) | ✅ |
| 1.1.5 | Admin UI — Marketplace tab | ✅ |
| 1.1.6 | API Endpoints (catalog, install, uninstall, installed) | ✅ |
| 1.1.7 | Validation & Security | ✅ |

**Total:** ~9h — COMPLETADO
**Commit:** `feat(1.1): marketplace foundation — phase complete` (1229197)

---

## 🔹 Phase 1.2 — Marketplace UI Polish + License Management (APPLIED — COMPLETE)

**Fecha:** 2026-05-11
**Estado:** ✅ APPLIED + UNIFY COMPLETE
**Commit:** `feat(marketplace): Phase 1.2 — License Management + Jazzmin UI Integration` (cbbc240)

**Objetivo:** Interfaz de catálogo rica + gestión de licencias.

**Entregables (9 tasks):**
- [x] `ModuleLicense` model (seats, expiry, types: free/trial/paid/perpetual)
- [x] License validation en `module_install` (consume/release en transacción)
- [x] REST API licencias (4 endpoints: POST create, GET list, GET validate, DELETE revoke)
- [x] Public catalog page `/marketplace/` con filtros, badges, precios, botón staff
- [x] Admin UI mejorado: seat usage bar, status badges, actions (generate key, revoke, install, uninstall)
- [x] Sidebar dinámico ERPNext-style agrupado por `admin_menu_category`
- [x] Dashboard integrado: tarjetas métricas + últimos 5 instalados
- [x] Cache invalidation automática post install/uninstall
- [x] 17 E2E tests passing

**Tests:** 15 → 17 passing (+2)
**Referencia:** `.paul/phases/01-marketplace/01-02-MARKETPLACE-UI-LICENSE-APPLIED.md`

---

## ✅ Phase 1.3 — GitHub Auto-discovery + Sync (APPLIED — COMPLETE)

**Fecha:** 2026-05-12
**Estado:** ✅ APPLIED + UNIFY COMPLETE
**Commit:** `feat(marketplace): GitHub auto-discovery + admin UI polish + default registry` (2f5977d)

**Objetivo:** Detección automática de módulos desde GitHub + sincronización de catálogo.

**Entregables:**
- [x] `refresh_catalog` command — escanea GitHub org (topic `erp-nexus-module` + `__meta__.py`), upsert catalog
- [x] Admin: botón "Sync" por registry + acción Jazzmin "Sync selected"
- [x] Auto-creación de `ModuleRegistry` default ("GitHub Official") — señal `apps.py` `ready()` + lógica en `refresh_catalog`
- [x] `parse_meta_file` utility (AST parser seguro para `__meta__.py`)
- [x] Settings: `GITHUB_TOKEN` + `GITHUB_ORG` (rate-limit awareness)
- [x] Fix: `settings.timezone.now()` → `timezone.now()` en refresh
- [x] 2 tests nuevos: default registry creation + dry-run behavior
- [x] Mock `call_command` mejorado: `refresh_catalog` ejecuta real sin recursion

**Tests:** +2 → **19 passing** (total marketplace suite)
**Referencia:** `.paul/phases/01-marketplace/01-03-GITHUB-DISCOVERY-APPLIED.md`

---


## ✅ Phase 2.1 — Docker Production Image (APPLIED — COMPLETE)
## ✅ Phase 2.2 — PostgreSQL + Redis Production (APPLIED — COMPLETE)
## ✅ Phase 2.3 — Celery Workers (APPLIED — COMPLETE)

**Fecha:** 2026-05-11
**Estado:** ✅ APPLIED + UNIFY COMPLETE
**Commit:** `feat(m3): Celery workers with Redis broker — Phase 2.3 COMPLETE` (8c1eaca)

**Objetivo:** Sistema de colas asíncronas para tareas pesadas.

**Entregables:**
- [x] `erp_nexus/celery.py` — Celery app con autodiscover de tareas
- [x] Configuración colas: sri (0), notifications (1), webhooks (3), default (5), reports (9)
- [x] Tareas base en `apps/core_notifications/tasks.py`:
  * send_email_task (retry 3x, 60s delay)
  * send_templated_email_task (HTML + texto)
  * send_invoice_to_sri_task (alta prioridad, SRI Ecuador)
  * generate_invoice_pdf_task (reportes pesados)
  * send_webhook_task (integraciones externas)
  * cleanup_old_sessions, refresh_marketplace_cache (periódicas)
- [x] Docker Compose: servicios `worker` y `beat`
  * worker: --concurrency=4, --queues=default,sri,notifications,reports,webhooks
  * beat: scheduler para tareas periódicas
- [x] `pyproject.toml`: agregada dependencia `celery>=5.3`
- [x] Tests automatizados: 19 tests en test_celery_config.py ✅
- [x] Documentación `docs/CELERY.md` (queues, retry, beat, Flower, troubleshooting)

**Tests:** 19 Celery configuration tests passing

**Post-completion fix (2026-05-11):**
- `modules_enabled.py` — force `MODULE_APPS = []` to avoid duplicate app labels
  (facturacion/sales already in INSTALLED_APPS as apps.facturacion/apps.sales)
- Consolidated `core_notifications/tasks.py` → `apps/notifications/tasks.py`
- All tests passing: 131 core_marketplace + 19 Celery config ✅
- Django check: 0 issues ✅

**Referencia:** `.paul/phases/03-production/02-03-CELERY-WORKERS.md`

---

## ✅ Phase M4 — Deployment Hardening + Runbooks + Automation (APPLIED — COMPLETE)

**Fecha:** 2026-05-12
**Estado:** ✅ APPLIED + UNIFY COMPLETE
**Commits:** `feat(m3): monitoring stack + runbooks + automation — M4 COMPLETE`

**Objetivo:** Production hardening completo: monitoreo, alertas, backup/restore, healthchecks y runbooks de operaciones.

**Entregables consolidate M4 (fases 2.4 + 2.5 + automation):**
- [x] SSL/TLS + Nginx reverse proxy (Phase 2.4) — TLSv1.2/1.3, HSTS 1año, CSP, security headers
- [x] Monitoring Stack Completo (Phase 2.5) — Prometheus + Grafana + AlertManager + cAdvisor + Node Exporter
- [x] 12 Alert Rules + Runbooks (docs/ALERTING_RULES.md) — critical/warning response playbooks
- [x] first-deploy.sh — deploy automatizado (SSL cert, migraciones, collectstatic, monitoreo)
- [x] rollback.sh — rollback emergencia (git reset + rebuild + health verify)
- [x] backup.sh / restore-db.sh — PostgreSQL backup/restore con rotación y confirmación explícita
- [x] healthcheck.sh — healthcheck integral (25+ checks: contenedores, DB, Redis, HTTP endpoints, SSL exp, disco, memoria)
- [x] Documentación: docs/MONITORING.md, docs/ALERTING_RULES.md, docs/SSL_NGINX.md, docs/DEPLOYMENT.md
- [x] Variables de entorno monitoreo: GRAFANA_ADMIN_*, SMTP_*, SLACK_WEBHOOK_URL, alert emails
- [x] Tests automatizados: 53 integration tests (monitoring stack validation) ✅
- [x] Tests scripts producción: 25 passing (test_production_scripts.py) ✅

**Artefactos de hardening:**
```
docs/
  MONITORING.md            — stack arquitectura, dashboards, comandas verificación
  ALERTING_RULES.md        — 12 runbooks con diagnóstico, remediación, escalation matrix
  SSL_NGINX.md             — TLS config, Certbot auto-renew, troubleshooting
  DEPLOYMENT.md            — guía despliegue completo
scripts/
  first-deploy.sh          — deploy inicial completo (Docker + SSL + monitoreo)
  rollback.sh              — rollback de emergencia a commit anterior
  backup.sh                — PostgreSQL backup con rotación (7d/4s)
  restore-db.sh            — restore interactivo con confirmación
  healthcheck.sh           — 25+ checks automatizados (colores, exit codes)
```

**Tests totales M4:** 53 (monitoring) + 25 (scripts) = **78 passing** ✅

**Referencia:** `.paul/phases/03-production/` (2.4 SSL, 2.5 Monitoring, M4 Runbooks/Automation)

---

## ✅ Phase 2.1 — Docker Production Image (APPLIED — COMPLETE)




**Fecha:** 2026-05-11
**Estado:** ✅ APPLIED + UNIFY COMPLETE
**Commit:** `feat(m3): PostgreSQL + Redis production tuning — Phase 2.2 COMPLETE` (7028a00)

**Objetivo:** Configuración de producción para PostgreSQL y Redis.

**Entregables:**
- [x] PostgreSQL 16 con tuning avanzado (shared_buffers, work_mem, checkpoint, WAL)
- [x] Redis 7 con AOF persistencia + maxmemory LRU + comandos FLUSH* deshabilitados
- [x] Volumen `backup` montado (/backup) para scripts
- [x] Extensiones PostgreSQL: pg_stat_statements, pg_stat_kcache, pg_qualstats, pg_wait_sampling
- [x] Script `backup-db.sh` — dump + gzip + rotación (7d diario, 4s semanal)
- [x] Script `restore-db.sh` — restauración desde backup con confirmación
- [x] Script `maintenance-db.sh` — VACUUM ANALYZE + estadísticas + top queries
- [x] Script `maintenance-redis.sh` — info, memoria, keyspace, slowlog
- [x] Documentación `docs/PROD_DB_TUNING.md` (tuning, métricas, troubleshooting)
- [x] Documentación `scripts/README.md` (uso de scripts)
- [x] Tests automatizados: 25 tests en test_production_scripts.py ✅

**Tests:** 25 production scripts tests passing
**Referencia:** `.paul/phases/03-production/02-02-PG-REDIS-PRODUCTION.md`




**Fecha:** 2026-05-11
**Estado:** ✅ APPLIED + UNIFY COMPLETE
**Commit:** `feat(m3): Docker production image — Phase 2.1 COMPLETE` (cdf6d36)

**Objetivo:** Imagen Docker multi-stage optimizada para producción.

**Entregables:**
- [x] `Dockerfile.prod` — builder (uv + collectstatic) + runtime (python:3.13-slim)
- [x] `docker-compose.prod.yml` — stack: postgres + redis + gunicorn
- [x] `entrypoint.sh` — migrate, collectstatic, gunicorn arranque
- [x] Endpoint `/health/` (health_check view en erp_nexus/urls.py)
- [x] `.dockerignore` — excluye tests, docs, .git, .venv, .paul
- [x] `docs/DEPLOYMENT.md` — guía completa de despliegue
- [x] `.env.prod.example` — plantilla variables de entorno
- [x] `pyproject.toml` — `[project]` section + `gunicorn` dependency
- [x] Tests de integración Docker (21 tests pasan)

**Tests:** 21 infrastructure tests passing (test_docker_integration.py)
**Referencia:** `.paul/phases/03-production/02-01-DOCKER-PRODUCTION.md`

## ✅ Phase 1.4 — Version Management + Dependencies Solver (APPLIED — COMPLETE)

**Fecha:** 2026-05-11
**Estado:** ✅ APPLIED + UNIFY COMPLETE
**Commit:** `feat(marketplace): dependency resolution system with --with-deps flag` (2f98f4f)

**Objetivo:** Gestión robusta de versiones y resolución de dependencias entre módulos.

**Entregables (10 tasks — ALL DONE):**

| Task | Descripción | Estado |
|------|-------------|--------|
| 1.4.1 | `ModuleVersionConstraint` model — rangos de versiones compatibles (semver) | ✅ |
| 1.4.2 | `ModuleDependency` model — dependencias (required, optional, conflict) | ✅ |
| 1.4.3 | Semver parser + compatibility checker | ✅ |
| 1.4.4 | Dependency resolver (topological sort + cycle detection) | ✅ |
| 1.4.5 | Conflict detection en Admin (pre-flight warnings) | ✅ |
| 1.4.6 | Auto-dependency installation (`--with-deps`) | ✅ |
| 1.4.7 | Upgrade path analysis — backward compatibility checks | ✅ |
| 1.4.8 | Tests E2E — conflict, cycles, version mismatches | ✅ |
| 1.4.9 | Cache invalidation + admin integration | ✅ |
| 1.4.10 | Documentation — DEPENDENCIES.md, upgrade guide | ✅ |

**Tests E2E:** 11 passed (8 resolver + 3 command)
**Migraciones aplicadas:** 0004 (constraints), 0005 (installed_version EnabledModule), 0006 (installed_version ModuleCatalogItem)
**Referencia:** `.paul/phases/01-marketplace/01-04-VERSION-DEPS-SOLVER-APPLIED.md`

---

## 📊 Code Stats Cumulative (All Phases — 2026-05-13)

**New files cumulative:** ~43
**Updated files:** ~35
**Total code churn:** ~41k lines added/modified

**Quality Metrics:**
- ✅ `manage.py check` — 0 issues
- ✅ `makemigrations --check` — no pending migrations
- ✅ `manage.py migrate` — all applied cleanly
- ✅ Django server starts without errors
- ✅ **78 E2E/integration tests passing**
  - Marketplace suite: 19 tests (catalog, install/uninstall, license)
  - Celery config: 19 tests
  - Docker integration: 21 tests
  - Production scripts: 25 tests (backup/restore/healthcheck)
  - Monitoring stack: 53 tests (Prometheus/Grafana/AlertManager configs)
  - Pagebuilder E2E: 4 manual QA endpoints verified

---

## 🎯 Acceptance Criteria — All Phases Verified

### Phase 0.6 ✅
*(9 tasks — hybrid architecture, 17 Django apps core + essential)*

### Phase 0.6.2 ✅
*(9 tasks — pagebuilder API, renderer, public views, frontend, management commands)*

### Phase 1.1 ✅
*(7 tasks — module catalog, install/uninstall, dynamic loading, API)*

### Phase 1.2 ✅
*(9 tasks — licenses, Jazzmin UI polish, dashboard, sidebar, cache invalidation)*

### Phase 1.3 ✅
*(7 tasks — GitHub auto-discovery, refresh_catalog, sync button, default registry)*

### Phase 1.4 ✅
*(10 tasks — semver constraints, dependency resolver, conflict detection, --with-deps, upgrade analysis)*

### Phase 2.1 ✅
*(9 tasks — Docker multi-stage production image, healthcheck, compose)*

### Phase 2.2 ✅
*(11 tasks — PostgreSQL 16 tuning, Redis 7 AOF, extensions, backup scripts)*

### Phase 2.3 ✅
*(9 tasks — Celery workers + beat, 5 queues, task retry, integration)*

### Phase M4 ✅
*(12+ tasks — SSL/TLS Nginx, full monitoring stack, 12 runbooks, automation scripts)*

### Phase 0.6.2 ✅
*(9 tasks — pagebuilder API, renderer, public views, frontend, management commands)*

---

## 🔗 Dependencies Resolved (Complete)

✅ Phase 0.6 — Baseline hybrid architecture (17 Django apps)
✅ Phase 1.1 — Marketplace foundation (catalog, install/uninstall, dynamic loading)
✅ Phase 1.2 — License management + Jazzmin UI polish
✅ Phase 1.3 — GitHub auto-discovery + registry sync
✅ Phase 1.4 — Version constraints + dependency resolver
✅ Phase 2.1 — Docker production image
✅ Phase 2.2 — PostgreSQL + Redis production tuning
✅ Phase 2.3 — Celery workers + beat
✅ Phase M4 — SSL/TLS + Monitoring + Runbooks + Automation
✅ Phase 0.6.2 — core_pagebuilder API + frontend completion

---

## 📋 Estado General Completado

- ✅ M0: Bootstrap (NextAuth + Prisma base) — anterior (referencia)
- ✅ M1: Auth Enhancement — anterior (referencia)
- ✅ M2: Wallet Top-Up + Marketplace —2026-05-10/11
- ✅ M3: Payments Gateway + Production Stack —2026-05-11 (Docker, DB, Celery)
- ✅ M4: Deployment Hardening + Runbooks + Automation —2026-05-12 (SSL, Monitoring, Scripts)
- ✅ Phase 0.6.x: Hybrid Restructure + core_pagebuilder —2026-05-13

**Último commit:** `96b7cdb` — docs(pagebuilder): complete module documentation with API, components, usage guide
**Próximo hito:** M5 — Feature Extensions (payout automation, BI analytics, multi-tenant, API v2, Sentry)

---

**Last updated:** 2026-05-13 | M4 + 0.6.2 — COMPLETE ✅ | JARVIS
