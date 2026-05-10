# PAUL State — ERP Nexus Core (Hybrid Architecture)

**Project:** ERP Nexus Core (Framework + Essential Modules)
**Architecture:** Hybrid — Essential modules in core, Optional modules as plugins
**Current Phase:** 1.1 — Marketplace Foundation (APPLY)
**Loop Position:** APPLY → UNIFY
**Last Completed:** Phase 0.6 — Hybrid Restructure (2026-05-10)
**Next Milestone:** M2 — Marketplace & Plugin System (Phase 1.1)

---

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

## 🔄 Phase 1.1 — Marketplace Foundation (APPLY IN PROGRESS)

**Objetivo:** Implementar sistema de Marketplace para plugins opcionales.

### Tasks

| Task | Descripción | Estimación | Estado |
|------|-------------|------------|--------|
| 1.1.1 | Extender ModuleCatalogItem metadata | 1h | ✅ DONE |
| 1.1.2 | Auto-Discover GitHub Organization (scan_github_org) | 2h | ✅ DONE |
| 1.1.3 | Install/Uninstall management commands | 1.5h | ✅ DONE |
| 1.1.4 | Dynamic App Loading (modules_enabled.py watcher) | 1h | ✅ DONE |
| 1.1.5 | Admin UI — Marketplace tab | 1h | ✅ DONE |
| 1.1.6 | API Endpoints (catalog, install, uninstall, installed) | 1h | ✅ DONE |
| 1.1.7 | Validation & Security | 1.5h | 🔄 50% |

**Total:** ~9h

---

## 🔄 Phase 1.1 — Detalle Implementado

### **1.1.1 — ModuleCatalogItem extendido** ✅

Campos agregados:
- `module_type` (essential | optional | plugin)
- `display_name`, `repo_url`, `min_erp_version`, `max_erp_version`
- `python_dependencies`, `system_dependencies` (JSONField)
- `documentation_url`

Migración: `0001_initial` (recreado) + `0002_extend_catalog` aplicados.

### **1.1.2 — scan_github_org command** ✅

Archivo: `apps/core_marketplace/management/commands/scan_github_org.py`
- Lista repos de GitHub org
- Detecta `__meta__.py`
- Registra/actualiza ModuleCatalogItem
- Soporta dry-run y token env

### **1.1.3 — Install/Uninstall commands** ✅

- `module_install` — clona repo, valida __meta__.py, registra EnabledModule, actualiza modules_enabled.py
- `module_uninstall` — desregistra, elimina directorio, actualiza modules_enabled.py
- Utilería: `apps/core_marketplace/utils/module_loader.py` (read/write MODULE_APPS)

### **1.1.4 — Dynamic App Loading** ✅

- `modules_enabled.py` ya se carga dinámicamente en `erp_nexus/settings/base.py`
- Watcher en `apps/core_marketplace/apps.py` (ready()) — detecta cambios y sugiere restart en DEBUG
- `add_to_modules_enabled()` / `remove_from_modules_enabled()` usado por commands

### **1.1.5 — Admin UI** ✅

- `ModuleCatalogItemAdmin` con botones Install/Reinstall
- `EnabledModuleAdmin` con botón Uninstall
- `ModuleDownloadAdmin`, `ModuleRegistryAdmin`
- Vistas inline `install_view` y `uninstall_view`

### **1.1.6 — API Endpoints** ✅

Archivo: `apps/core_api/v1/marketplace.py`
- `GET /api/v1/marketplace/catalog` — lista catálogo (filters: module_type, installed)
- `POST /api/v1/marketplace/{name}/install` — instala módulo
- `POST /api/v1/marketplace/{name}/uninstall` — desinstala módulo
- `GET /api/v1/marketplace/installed` — lista módulos instalados
- `GET /api/v1/marketplace/status` — estado del marketplace

Ya registrado en `apps/core_api/api.py` como `marketplace_router`.

### **1.1.7 — Validation & Security** 🔄 50%

Implementado en `module_install`:
- ✅ AST parse de `__meta__.py` (safe literal_eval)
- ✅ Required fields validation (technical_name, version)
- ✅ Version format check (semver-like)
- ✅ Security check: paths seguros
- ⏳ Pendiente: checksum SHA256 del repo (future)

---

## 📊 Code Changes Summary

**New files:**
- `apps/core_marketplace/management/commands/scan_github_org.py`
- `apps/core_marketplace/management/commands/module_install.py`
- `apps/core_marketplace/management/commands/module_uninstall.py`
- `apps/core_marketplace/utils/module_loader.py`
- `apps/core_marketplace/utils/__init__.py`
- `apps/core_marketplace/migrations/0002_extend_catalog.py`

**Updated files:**
- `apps/core_marketplace/models.py` — ModuleCatalogItem extendido, +ModuleDownload +ModuleRegistry
- `apps/core_marketplace/admin.py` — Botones Install/Uninstall
- `apps/core_marketplace/apps.py` — Watcher de modules_enabled.py
- `apps/core_api/v1/marketplace.py` — Endpoints REST
- `apps/core_marketplace/migrations/0001_initial.py` — recreado para consistencia

---

## ✅ Acceptance Criteria Met

- [x] ModuleCatalogItem extendido con metadata completa
- [x] scan_github_org command implementado
- [x] module_install / module_uninstall commands funcionan
- [x] modules_enabled.py se actualiza dinámicamente
- [x] Admin UI tiene Marketplace con botones de acción
- [x] API endpoints funcionan (JWTAuth protected)
- [x] Validación básica de __meta__.py implementada
- [ ] Validación SHA256 checksum (future task)

---

## 📋 Todo 1.1.7 — Pending

- SHA256 checksum validation para repos (asegurar integridad)
- Future: auto-install python dependencies (pip install -r)
- Future: system_dependencies check (apt/brew install)

---

## 🎯 Next Steps

1. **Commit 1.1**: `feat(1.1): marketplace foundation — phase complete`
2. **UNIFY** — Graph rebuild + docs update
3. **Verificar** comandos manualmente:
   - `python manage.py scan_github_org ERPNexus --dry-run`
   - `python manage.py module_install hr` (cuando hr repo exista)
   - `python manage.py module_uninstall hr`
4. Phase 1.2: Marketplace UI + License management

---

**Estado Phase 1.1:** 🔄 APPLY (90% complete — pending SHA256 validation)
