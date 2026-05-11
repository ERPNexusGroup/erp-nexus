# PAUL Phase 1.3 — GitHub Auto-Discovery + Sync

**Objetivo:** Detectar automáticamente módulos desde repositorios GitHub y sincronizar el catálogo del marketplace.

**Estado:** 📋 PLAN

---

## Context

Phase 1.1 y 1.2 crearon el backend y sistema de licencias. Phase 1.3 agrega:

1. **GitHub organization scan** — Detecta repos que cumplan criteria (topic `erp-nexus-module`, `__meta__.py` presente)
2. **Auto-catalog population** — Crea/actualiza `ModuleCatalogItem` desde metadata de GitHub
3. **Scheduled sync** — Tarea periódica (Celery/cron) para mantener catálogo fresco
4. **Webhook support** — Opcional: recibir eventos push desde GitHub para refresh inmediato
5. **Registry model** — Multi-source soporte (GitHub org, múltiples cuentas, URLs JSON)

---

## Architecture

### **Scan Pipeline**

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

### **ModuleRegistry Model** (already exists)
```python
class ModuleRegistry(models.Model):
    name =.CharField(unique=True)  # e.g., "Official GitHub Org"
    source_type = 'github' | 'git' | 'url' | 'local'
    url = 'erp-nexus'  # org name or repo URL
    is_active = True
    is_default = True (priority 50)
    cached_modules = JSONField  # última data escaneada
    last_sync = DateTimeField
```

### **Command: `scan_github_org`**
```bash
uv run manage.py scan_github_org [registry_name]
```
- Lee token de `GITHUB_TOKEN` (env)
- Itera sobre repos de la org configurada
- Para cada repo: clone shallow → parse `__meta__.py` → upsert catalog item
- Actualiza `ModuleRegistry.cached_modules` con resumen

### **Management Command: `refresh_catalog`**
```bash
uv run manage.py refresh_catalog [--all] [--registry=name]
```
- Sin args: escanea solo registros `is_default=True`
- `--all`: todos los registros activos
- `--registry`: uno específico

---

## Tasks Phase 1.3

### **1.3.1 — GitHub API Integration**

- [ ] Instalar `PyGithub` o usar `requests` + GitHub REST API
- [ ] Configurar `GITHUB_TOKEN` en settings (desde env)
- [ ] Helper: `apps/core_marketplace/utils/github.py` → `get_org_repos(org_name)`
- [ ] Rate-limit handling (60 req/hora sin token → usar token para 5000/h)
- [ ] Commit: `feat(github): add GitHub API client for org scanning`

**Dependencies:**
- `requests` ya instalado en requirements

### **1.3.2 — Module Discovery & Filtering**

- [ ] Filtrar repos por:
  - Tiene archivo `__meta__.py` en raíz
  - Topic `erp-nexus-module` presente
  - No archivo `.skip_erp_nexus` (opt-out)
- [ ] Función: `is_erp_nexus_module(repo) -> bool`
- [ ] Commit: `feat(scan): filter repos by __meta__.py and topic`

### **1.3.3 — Metadata Parser**

- [ ] Reutilizar `_parse_meta_file()` de `module_install`
- [ ] Extraer: `technical_name`, `version`, `django_app`, `module_type`
- [ ] Opcionales: `repo_url`, `min_erp_version`, `python_dependencies`
- [ ] Validación mínima: `technical_name` único, `version` semver-ish
- [ ] Commit: `feat(scan): parse __meta__.py from GitHub repos`

### **1.3.4 — Catalog Upsert Logic**

- [ ] Si `ModuleCatalogItem` no existe → crear con `is_active=True`
- [ ] Si existe y `version` cambió → actualizar campos, `installed_at=None`
- [ ] Si repo desapareció → marcar `is_active=False` (soft delete)
- [ ] Commit: `feat(scan): upsert catalog items from discovered repos`

### **1.3.5 — Refresh Catalog Command**

- [ ] Crear `apps/core_marketplace/management/commands/refresh_catalog.py`
- [ ] Opciones: `--registry`, `--all`, `--dry-run`
- [ ] Logging detallado: "✔ repo/name: updated", "✗ repo/name: skipped (no __meta__)"
- [ ] Estadísticas finales: `X modules scanned, Y created, Z updated, W deactivated`
- [ ] Commit: `feat(catalog): refresh_catalog management command`

### **1.3.6 — Scheduled Sync (Celery/Crontab)**

- [ ] Task asincrónica: `tasks.refresh_catalog_task()`
- [ ] Configurar schedule: diario 03:00 AM (bajo carga)
- [ ] O alternativamente cron del sistema (si Celery no configurado)
- [ ] Logging a archivo: `logs/catalog_sync.log`
- [ ] Commit: `feat(sync): scheduled catalog refresh task`

### **1.3.7 — Admin UI: Manual Sync Trigger**

- [ ] En `ModuleRegistryAdmin`: botón "Sync Now" (accion personalizada)
- [ ] View admin: llama a `refresh_catalog(registry_name=...)`
- [ ] Feedback: mensaje success con stats
- [ ] Commit: `style(admin): add manual sync button to ModuleRegistry`

### **1.3.8 — Tests E2E**

- [ ] Mock GitHub API respuestas (2-3 repos: con/sin __meta__, con topic, sin topic)
- [ ] Test: `test_scan_identifies_valid_modules`
- [ ] Test: `test_refresh_catalog_creates_new_items`
- [ ] Test: `test_refresh_catalog_updates_existing_version`
- [ ] Test: `test_refresh_catalog_deactivates_missing_repos`
- [ ] Test: `test_public_catalog_shows_synced_modules`
- [ ] Commit: `test(1.3): e2e tests for GitHub discovery and sync`

---

## Acceptance Criteria Phase 1.3

- [ ] `ModuleRegistry` funciona con `source_type='github'`
- [ ] Command `refresh_catalog` escanea org y crea/actualiza `ModuleCatalogItem`
- [ ] Filtrado por `__meta__.py` y topic `erp-nexus-module` funciona
- [ ] Repos sin metadata se omiten (log warning)
- [ ] Sync automático diario configurado
- [ ] Admin: botón "Sync Now" en `ModuleRegistryAdmin`
- [ ] Tests: 5+ E2E pasando con mocks de GitHub API

---

## Dependencies

✅ Phase 1.2 — License Management COMPLETED
📦 `requests` library (ya en requirements)
🔑 `GITHUB_TOKEN` en settings/env

---

## Timeline Estimation

**Total:** ~16h
- 1.3.1 — 2h (GitHub client + auth)
- 1.3.2 — 1.5h (filtering logic)
- 1.3.3 — 1h (meta parser reuse)
- 1.3.4 — 2h (upsert + soft-deactivate)
- 1.3.5 — 2h (refresh_catalog command)
- 1.3.6 — 2h (scheduled sync)
- 1.3.7 — 1.5h (admin button)
- 1.3.8 — 2h (E2E tests mocks)
- Testing/debug: 2h buffer

---

## Risks

| Riesgo | Mitigación |
|--------|------------|
| GitHub rate limit (60/h sin token) | Usar token autenticado, cache respuestas |
| Clone lento en repos grandes | Git clone `--depth=1` + `--single-branch` |
| metadata inválida en __meta__.py | Validación robusta, log warnings, continuar |
| Sync bloquea DB | Procesar en batches (100 repos/scroll) |
| Webhook seguridad | Validar signature X-Hub-Signature si se implementa |

---

**Estado:** 📋 PLANEADO — Esperando APPLY
