# PAUL Phase 1.3 — GitHub Auto-Discovery + Sync

**Fecha:** 2026-05-12
**Estado:** ✅ APPLIED + UNIFY COMPLETE
**Commit:** `feat(marketplace): GitHub auto-discovery + admin UI polish + default registry` (2f5977d)
**Loop:** PLAN → APPLY → UNIFY ✅

---

## Objetivo Alcanzado

Sistema completo de detección automática de módulos desde GitHub organization + sincronización de catálogo:

- Comando `refresh_catalog` escanea org (topic `erp-nexus-module` + `__meta__.py`) → upsert `ModuleCatalogItem`
- Admin UI: botón "Sync Now" en `ModuleRegistryAdmin` + acción Jazzmin "Sync selected"
- Auto-creación de `ModuleRegistry` default ("GitHub Official") si no existen registros activos
- Utility `parse_meta_file` (AST parser seguro reutilizable)
- Settings: `GITHUB_TOKEN` + `GITHUB_ORG` con rate-limit awareness
- Fix timezone en `refresh_catalog`
- 2 tests E2E新增 (default registry creation + dry-run behavior)
- Mock mejorado: `refresh_catalog` ejecuta real sin recursion

**Tests:** +2 → **19 E2E passing** (total marketplace suite)

---

## Architecture — Scan Pipeline

```
1. Configuration (ModuleRegistry con source_type='github', url='org-name')
   ↓
2. GitHub API fetch (GET /orgs/{org}/repos?type=all&per_page=100)
   ↓
3. Filter repos → has __meta__.py AND topic contains 'erp-nexus-module'
   ↓
4. For each repo: clone (shallow) → parse __meta__.py → extract metadata
   ↓
5. Upsert ModuleCatalogItem (por technical_name)
   ↓
6. Update ModuleRegistry.last_sync, cached_modules
```

---

## Files Changed (7)

| File | Cambios |
|------|---------|
| `apps/core_marketplace/admin.py` | `ModuleRegistryAdmin`: botón "Sync Now" (custom admin view) |
| `apps/core_marketplace/apps.py` | Señal `ready()` → auto-crea `ModuleRegistry` default si no hay registros activos |
| `apps/core_marketplace/management/commands/refresh_catalog.py` | Nuevo command: escanea registros GitHub, upsert catalog items, log estadísticas |
| `apps/core_marketplace/utils/module_loader.py` | `parse_meta_file()` extraído a función reutilizable (AST-safe) |
| `apps/core_marketplace/tests/conftest.py` | Mock `call_command` mejorado para permitir ejecución real de `refresh_catalog` |
| `apps/core_marketplace/tests/test_marketplace_license.py` | +2 tests: default registry auto-creation, dry-run behavior |
| `erp_nexus/settings.py` | `GITHUB_TOKEN`, `GITHUB_ORG` agregados; fix `timezone.now()` en refresh |

---

## Acceptance Criteria — Verificados ✅

- [x] `ModuleRegistry` funciona con `source_type='github'`
- [x] Command `refresh_catalog` escanea org y crea/actualiza `ModuleCatalogItem`
- [x] Filtrado por `__meta__.py` y topic `erp-nexus-module` funciona
- [x] Repos sin metadata se omiten (log warning informativo)
- [x] Auto-creación de registry default si no existe al iniciar Django
- [x] Admin: botón "Sync Now" en `ModuleRegistryAdmin` llama a `refresh_catalog`
- [x] Tests: 2 E2E pasando con mocks de GitHub API (total 19 tests)
- [x] Rate-limit handling (token authentication)
- [x] Shallow clone (`--depth=1`) para performance

---

## Commands Added

```bash
# Escanear todos los registros activos
uv run manage.py refresh_catalog --all

# Escanear solo el registry default
uv run manage.py refresh_catalog

# Escanear un registry específico
uv run manage.py refresh_catalog --registry="GitHub Official"

# Dry-run (sin guardar cambios)
uv run manage.py refresh_catalog --dry-run

# Desde admin: botón "Sync Now" en ModuleRegistry → ejecuta refresh_catalog
```

---

## Admin UI — Manual Sync

**Ubicación:** `ModuleRegistryAdmin` → botón "Sync Now" (acción personalizada)

**Flujo:**
1. Admin hace clic "Sync Now" en un registry
2. View admin ejecuta `call_command('refresh_catalog', registry_name=...)`
3. Mensaje success con estadísticas: `"X repos scanned, Y created, Z updated, W deactivated"`
4. Catálogo actualizado automáticamente

---

## Quality Checks

- ✅ `manage.py check` — sin errores
- ✅ `manage.py migrate` — todas las migraciones aplicadas
- ✅ `manage.py runserver` — arranca sin errores
- ✅ **19 E2E tests** passing (marketplace + license + GitHub sync + sidebar)

---

## Future Enhancements (Post-1.3)

- Webhook receiver para auto-refresh on push (GitHub webhook → Django view)
- Scheduled sync vía Celery beat (diario 03:00 AM)
- Multi-org scanning (múltiples GitHub organizations)
- Registry tipo 'git' (repos locales/privados sin GitHub)
- Registry tipo 'url' (JSON feed externo)

---

**Phase 1.3 signature:** Applied, Verified, UNIFY Complete ✅
**Integration:** GitHub Auto-discovery + Catalog Sync v1.0
**User impact:** Los administradores pueden sincronizar automáticamente el catálogo de módulos desde GitHub con un click; nuevos módulos aparecen inmediatamente en el marketplace.
