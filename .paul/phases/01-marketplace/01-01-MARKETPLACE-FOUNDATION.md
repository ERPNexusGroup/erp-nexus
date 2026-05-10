# PAUL Phase 1.1 — Marketplace Foundation

**Objetivo:** Implementar el sistema de Marketplace para plugins opcionales.

## Context

Phase 0.6 creó 6 essential modules integrados. Phase 1.x agrega la capacidad de instalar módulos **opcionales** desde repositorios externos GitHub.

**Flujo de Marketplace:**
1. Admin ve catálogo de módulos disponibles (ModuleCatalog)
2. Admin selecciona módulo → instala (clona a modules/)
3. Sistema registra EnabledModule y escribe modules_enabled.py
4. Django restart → carga app adicional
5. Admin puede desinstalar (elimina de modules/)

---

## Architecture

### **Module Catalog (Core Marketplace App)**

`apps/core_marketplace/` ya existe. Extender:

```python
# apps/core_marketplace/models.py (existente)
class ModuleCatalogItem(models.Model):
    technical_name = models.CharField(unique=True)  # 'hr'
    display_name = models.CharField()               # 'Recursos Humanos'
    repo_url = models.URLField()                    # GitHub URL
    version = models.CharField()                    # '0.1.0'
    is_essential = models.BooleanField(default=False)
    # ... existing fields

class EnabledModule(models.Model):
    technical_name = models.CharField(unique=True)
    django_app = models.CharField()  # 'hr' o 'apps.hr' (essential)
    status = models.CharField()      # active/inactive
    installed_at = models.DateTimeField()
```

**Cambio clave:** Essential modules NO pasan por Marketplace. Se activan directamente en `INSTALLED_APPS`.

---

### **Installation Flow**

```bash
# 1. Admin agrega ModuleCatalogItem (manual o auto-detect GitHub)
POST /api/v1/marketplace/catalog/
{
  "technical_name": "hr",
  "display_name": "Recursos Humanos",
  "repo_url": "https://github.com/ERPNexus/hr",
  "version": "0.1.0"
}

# 2. Admin instala módulo
POST /api/v1/marketplace/hr/install/
# → Clona repo a modules/hr/
# → Crea EnabledModule(status='active')
# → write_modules_enabled() actualiza modules_enabled.py

# 3. Reiniciar Django (auto o manual)
# → modules_enabled.py contiene 'hr'
# → INSTALLED_APPS extiende con 'hr'
```

---

## Tasks Phase 1.1

### **1.1.1 — Extender ModuleCatalogItem**

- [ ] Añadir campo `module_type` choices: `essential` | `optional` | `plugin`
- [ ] Añadir `min_erp_version`, `max_erp_version`
- [ ] Añadir `python_dependencies` (JSON field: {"packages": ["django-celery-beat"]})
- [ ] Añadir `system_dependencies` (JSON: {"bin": ["wkhtmltopdf"]})
- [ ] Añadir `documentation_url`
- [ ] Commit: `feat(marketplace): extend ModuleCatalogItem metadata`

### **1.1.2 — Auto-Discover GitHub Organization**

- [ ] Management command: `scan_github_org ERPNexus`
  - Lista repos públicos de la org que tengan `__meta__.py`
  - Auto-crea ModuleCatalogItem entries
- [ ] Task periódica (Celery beat): actualizar catálogo nightly
- [ ] Commit: `feat(marketplace): auto-discover modules from GitHub org`

### **1.1.3 — Install/Uninstall Management Commands**

- [ ] `python manage.py module_install <technical_name>`
  - Valida ModuleCatalogItem existe
  - Clona a `modules/<technical_name>/`
  - Crea/actualiza EnabledModule(status='active')
  - Llama `write_modules_enabled()`
  - Retorna success/failure
- [ ] `python manage.py module_uninstall <technical_name>`
  - Marca EnabledModule como inactive
  - Elimina directorio `modules/<technical_name>/` (opcional: keep_data)
  - Regenera modules_enabled.py
- [ ] Commit: `feat(marketplace): install/uninstall commands`

### **1.1.4 — Dynamic App Loading (modules_enabled.py)**

**Actual:** `modules_enabled.py` estático leído al startup.

**Mejorar:** Watcher que recarga automáticamente si modules_enabled.py cambia.

```python
# erp_nexus/apps.py (AppConfig)
class ERPConfig(AppConfig):
    def ready(self):
        from django.conf import settings
        import importlib
        # Reload modules_enabled si timestamp cambió
        # Extender INSTALLED_APPS dinámicamente
```

**Tarea:** Implementar `AppConfig.ready()` reload de modules_enabled.
- [ ] Commit: `feat(marketplace): dynamic module reload on modules_enabled change`

---

### **1.1.5 — Admin UI — Marketplace Tab**

- [ ] Extender Django admin:
  - ModuleCatalog list + install button
  - EnabledModule list + uninstall button
  - Version check warnings
- [ ] Commit: `feat(marketplace): admin UI for module catalog`

---

### **1.1.6 — API Endpoints**

- [ ] `GET /api/v1/marketplace/catalog/` — Lista módulos disponibles
- [ ] `POST /api/v1/marketpace/{name}/install/` — Instalar
- [ ] `POST /api/v1/marketpace/{name}/uninstall/` — Desinstalar
- [ ] `GET /api/v1/marketplace/installed/` — Lista módulos instalados
- [ ] Commit: `feat(marketplace): REST API endpoints`

---

### **1.1.7 — Validation & Security**

- [ ] Validar `__meta__.py` del plugin (schema validation)
- [ ] Checksum SHA256 del repo (verify integrity)
- [ ] Sandbox: módulo no puede sobrescribir core apps
- [ ] Commit: `feat(marketplace): security validation for plugins`

---

## Acceptance Criteria

- [ ] `ModuleCatalogItem` extendido con metadata completa
- [ ] `scan_github_org` command lista módulos de ERPNexus GitHub org
- [ ] `module_install hr` clona y registra correctamente
- [ ] `module_uninstall hr` desinstala limpiamente
- [ ] modules_enabled.py se actualiza dinámicamente
- [ ] Admin UI muestra Marketplace tab
- [ ] API endpoints funcionan (401 protected)
- [ ] Validación de `__meta__.py` previene plugins malformados

---

## Dependencies

- ✅ Phase 0.6 (Hybrid Restructure) — COMPLETADO
- 🆕 Core marketplace app existente (core_marketplace)

---

## Timeline Estimation

**Total:** ~8h
- 1.1.1 — 1h
- 1.1.2 — 2h (GitHub API + clone logic)
- 1.1.3 — 1.5h (commands)
- 1.1.4 — 1h (dynamic loading)
- 1.1.5 — 1h (admin UI)
- 1.1.6 — 1h (API endpoints)
- 1.1.7 — 1.5h (validation + security)

---

## Risks

| Riesgo | Mitigación |
|--------|------------|
| Plugin sobrescribe core files | Check: `/modules/<name>/` no puede contener `../erp_nexus/` paths |
| __meta__.py malformado | Schema validation Pydantic antes de install |
| GitHub rate limit | Cache respuestas, exponential backoff |
| modules_enabled.py corrupto | Backup antes de write, validate Python syntax |

---

**Estado:** 📋 PLANEADO — Esperando confirmación para APPLY
