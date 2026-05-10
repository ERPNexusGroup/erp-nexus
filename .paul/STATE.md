# PAUL State — ERP Nexus Core (Hybrid Architecture)

**Project:** ERP Nexus Core (Framework + Essential Modules)
**Architecture:** Hybrid — Essential modules in core, Optional modules as plugins
**Current Phase:** 1.1 — Marketplace Foundation (PLAN)
**Loop Position:** PLAN → APPLY → UNIFY
**Last Completed:** Phase 0.6 — Hybrid Restructure (2026-05-10)
**Next Milestone:** M2 — Marketplace & Plugin System

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

## 📋 Phase 1.1 — Marketplace Foundation (PLAN)

**Objetivo:** Implementar sistema de Marketplace para plugins opcionales.

**Context:** Phase 0.6 integró essential modules. Phase 1.1 agrega capacidad de instalar módulos **opcionales** (hr, crm, accounting_adv, project_mgmt, pos, ecommerce) desde repos externos.

### Tasks

| Task | Descripción | Estimación | Estado |
|------|-------------|------------|--------|
| 1.1.1 | Extender ModuleCatalogItem metadata | 1h | ⬜ |
| 1.1.2 | Auto-Discover GitHub Organization | 2h | ⬜ |
| 1.1.3 | Install/Uninstall management commands | 1.5h | ⬜ |
| 1.1.4 | Dynamic App Loading (modules_enabled.py reload) | 1h | ⬜ |
| 1.1.5 | Admin UI — Marketplace tab | 1h | ⬜ |
| 1.1.6 | API Endpoints (catalog, install, uninstall) | 1h | ⬜ |
| 1.1.7 | Validation & Security (__meta__.py schema, checksum) | 1.5h | ⬜ |

**Total:** ~9h

---

## 🔄 Phase 1.1 — Detalle por Task

### **1.1.1 — Extend ModuleCatalogItem**

`apps/core_marketplace/models.py` exists. Añadir:

```python
class ModuleCatalogItem(models.Model):
    # existing fields...
    module_type = models.CharField(choices=[
        ('essential', 'Essential (core)'),
        ('optional', 'Optional Plugin'),
        ('plugin', 'Third-party Plugin'),
    ], default='optional')
    min_erp_version = models.CharField()  # "0.6.0"
    max_erp_version = models.CharField(null=True, blank=True)
    python_dependencies = models.JSONField(default=dict)  # {"packages": ["celery"]}
    system_dependencies = models.JSONField(default=dict)  # {"bin": ["wkhtmltopdf"]}
    documentation_url = models.URLField(blank=True)
```

**Commit:** `feat(marketplace): extend catalog metadata`

---

### **1.1.2 — Auto-Discover GitHub Organization**

```bash
python manage.py scan_github_org ERPNexus
```

**Implementación:**
- Usar GitHub API: `GET /orgs/ERPNexus/repos`
- Filtrar repos con `__meta__.py` en root
- Parsear `__meta__.py` (AST) → extraer technical_name, version, dependencies
- Crear/actualizar ModuleCatalogItem
- Task periódica: `python manage.py refresh_marketplace_catalog` (Celery beat)

**Commit:** `feat(marketplace): auto-discover modules from GitHub org`

---

### **1.1.3 — Install/Uninstall Commands**

```bash
# Install
python manage.py module_install hr
# → clone https://github.com/ERPNexus/hr.git → modules/hr/
# → EnabledModule.objects.create(technical_name='hr', django_app='hr', status='active')
# → write_modules_enabled()

# Uninstall
python manage.py module_uninstall hr
# → EnabledModule.status = 'inactive'
# → eliminar directorio modules/hr/ (opcional: keep_data=True)
# → write_modules_enabled()
```

**Commit:** `feat(marketplace): install/uninstall management commands`

---

### **1.1.4 — Dynamic App Loading**

Actualmente `modules_enabled.py` se lee al startup. Mejorar:

```python
# erp_nexus/apps.py
class ERPConfig(AppConfig):
    def ready(self):
        # Watch modules_enabled.py modification time
        # Si cambia, recargar apps dinámicamente (requiere restart o reload)
        pass
```

**Para desarrollo:** Auto-reload cuando modules_enabled.py cambia (StatReloader).
**Para producción:** Restart automático via systemd o Docker.

**Commit:** `feat(marketplace): dynamic module reload on config change`

---

### **1.1.5 — Admin UI**

Extender `core_marketplace/admin.py`:

- ModuleCatalogItemAdmin: list + install button (action)
- EnabledModuleAdmin: list + uninstall button
- Warning: module not compatible with current ERP version

**Commit:** `feat(marketplace): admin UI for catalog and installed modules`

---

### **1.1.6 — API Endpoints**

`apps/core_api/api.py` → new router:

```python
router = Router(tags=["Marketplace"])
@router.get("/catalog/")
@router.post("/{name}/install/")
@router.post("/{name}/uninstall/")
@router.get("/installed/")
```

**Commit:** `feat(marketplace): REST API endpoints`

---

### **1.1.7 — Validation & Security**

**Validaciones antes de install:**
1. `__meta__.py` existe y es parseable (AST)
2. Schema: required fields (technical_name, version, dependencies)
3. Checksum SHA256 del repo commit (verify integrity)
4. Sandbox check: no puede sobrescribir `erp_nexus/` o `apps/` (solo modules/)

**Commit:** `feat(marketplace): security validation for plugin installation`

---

## 📋 Acceptance Criteria Phase 1.1

- [ ] ModuleCatalogItem extendido con todos los campos metadata
- [ ] `scan_github_org ERPNexus` lista 6+ plugins (hr, crm, …)
- [ ] `module_install hr` clona y registra correctamente
- [ ] `module_uninstall hr` desinstala limpiamente
- [ ] modules_enabled.py se actualiza automáticamente
- [ ] Admin UI tiene pestaña Marketplace funcional
- [ ] API endpoints: GET/POST trabajan con auth
- [ ] Validación rechaza __meta__.py malformados
- [ ] Tests: `pytest apps/core_marketplace/tests/` pasan

---

## 🔗 Dependencies

✅ Phase 0.6 — Hybrid Restructure COMPLETED
🆕 core_marketplace app exists (Phase M0)

---

## 🎯 Phase 1.1 Deliverable

**Marketplace v0.1.0 funcional:**
- Admin puede instalar hr desde GitHub
- Sistema valida __meta__.py
- modules_enabled.py dinámico
- API + Admin UI operativos

---

**Estado:** 📋 PLANEADO — Esperando APPLY
