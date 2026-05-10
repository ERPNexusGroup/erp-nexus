# ADR-004: Marketplace Module Installation Flow

**Estado:** ✅ Aceptado  
**Fecha:** 2026-05-10  
**Contexto:** Fase 2 — Módulos externos  
**Decisores:** Walter Cun, ERP Nexus Team

---

## 📋 Contexto

El core ERP Nexus debe permitir **instalar módulos desde múltiples fuentes**:

1. Local directory (dev)
2. Git repository (GitHub/GitLab)
3. Paquete `.npkg` (Marketplace oficial)
4. PyPI (futuro)

¿Cómo hacemos el install?

---

## 🎯 Decisión

**Marketplace Engine con ModuleInstaller**

1. **Clonar/descargar** módulo a `~/.erp-nexus/modules/{technical_name}/`
2. **Validar** estructura (presence de `__meta__.py`, `apps.py`, `models.py`)
3. **Registrar** en DB (Module model)
4. **Agregar** a `INSTALLED_APPS` dinámicamente
5. **Ejecutar** `migrate` para el módulo
6. **Activar** (opcional, por defecto activado)

---

## 🏗️ Flujo de Instalación

### **Commando CLI:**

```bash
# Desde git
python manage.py install_module --git https://github.com/ERPNexus/facturacion_ec.git

# Desde directorio local
python manage.py install_module ./facturacion_ec

# Desde paquete .npkg
python manage.py install_module --package ./facturacion_ec-0.1.0.npkg
```

### **Pipeline:**

```
Usuario ejecuta install_module
   ↓
1. Downloader
   ├─ git clone → ~/.erp-nexus/tmp/facturacion_ec/
   └─ unzip .npkg → ~/.erp-nexus/tmp/facturacion_ec/
   ↓
2. Validator
   ├─ __meta__.py existe y parseable
   ├─ apps.py define AppConfig
   ├─ models.py importable
   ├─ dependencies satisfechas
   └─ version compatibility
   ↓
3. Installer
   ├─ Copia a ~/.erp-nexus/apps/facturacion/
   ├─ Crea/actualiza Module record en DB
   ├─ Añade a INSTALLED_APPS (runtime)
   ├─ Ejecuta: manage.py migrate facturacion_ec
   └─ Emite evento: module.installed
   ↓
4. Post-install (opcional)
   ├─ Carga fixtures (catalogs SRI)
   ├─ Crea default data
   └─ Registra webhooks (si los define)
```

---

## 📁 Estructura de Almacenamiento

```
~/.erp-nexus/
├── modules/                  # Módulos instalados
│   ├── facturacion_ec/
│   │   ├── __meta__.py
│   │   ├── __init__.py
│   │   ├── apps.py
│   │   ├── models.py
│   │   └── migrations/
│   └── inventory/
│       └── ...
├── downloads/                # .npkg descargados (cache)
├── tmp/                      # Clones temporales git
└── registry.db               # SQLite con metadata (si no usamos Django DB)
```

**Nota:** En producción, módulos se instalan una sola vez y viven en filesystem. No se actualizan automáticamente (update manual).

---

## 🔐 Validación de Módulos

### **ModuleValidator:**

```python
class ModuleValidator:
    REQUIRED_FILES = ["__meta__.py", "apps.py", "models.py"]

    def validate(self, path: Path) -> ValidationResult:
        errors = []

        # 1. Archivos requeridos
        for file in self.REQUIRED_FILES:
            if not (path / file).exists():
                errors.append(f"Missing required file: {file}")

        # 2. __meta__.py válido
        try:
            meta = import_module_meta(path)
            required_fields = ["technical_name", "name", "version", "dependencies"]
            for field in required_fields:
                if field not in meta:
                    errors.append(f"Missing field in __meta__.py: {field}")
        except Exception as exc:
            errors.append(f"Invalid __meta__.py: {exc}")

        # 3. Django AppConfig subclass
        try:
            app_config = self._get_app_config(path)
            if not issubclass(app_config, AppConfig):
                errors.append("apps.py must define AppConfig subclass")
        except Exception:
            errors.append("Cannot import AppConfig from apps.py")

        # 4. Models importable y con company FK
        try:
            models_module = import_module(f"{technical_name}.models")
            for model in apps.get_models():
                if not hasattr(model, "company"):
                    errors.append(f"Model {model.__name__} missing 'company' field")
        except Exception as exc:
            errors.append(f"Models import error: {exc}")

        return ValidationResult(valid=len(errors)==0, errors=errors)
```

---

## 🔄 Actualización (Upgrade)

```bash
# Upgrade a nueva versión
python manage.py upgrade_module facturacion_ec --package ./facturacion_ec-0.2.0.npkg

# Pipeline:
# 1. Validar nueva versión
# 2. Backup DB (migrations)
# 3. Backup filesystem (old version)
# 4. Reemplazar archivos
# 5. Ejecutar nuevas migraciones
# 6. Emitir module.upgraded evento
# 7. Cleanup backups (después de 24h si ok)
```

---

## 🗑️ Desinstalación

```bash
python manage.py uninstall_module facturacion_ec
```

**Acciones:**
1. Desactivar módulo (enable=False)
2. Eliminar registros en Module table (marcar como uninstalled, no borrar historial)
3. **NO eliminar** datos en DB (posiblemente necesarios para reportes históricos)
4. Eliminar archivos de `~/.erp-nexus/apps/facturacion/`

**Nota:** Data remains in DB pero becomes "orphaned". Futuramente: soft-delete cascade.

---

## 🧪 Instalador Tests

```python
def test_install_from_git():
    result = call_command("install_module", "--git", "https://github.com/...")
    assert result.success
    assert Module.objects.filter(technical_name="facturacion_ec").exists()

def test_install_invalid_module():
    result = call_command("install_module", "./invalid_module")
    assert not result.success
    assert "Missing __meta__.py" in result.stderr

def test_install_with_missing_dependency():
    # Module depends on core_users v0.6.0, we have 0.5.0
    result = call_command("install_module", "./needs_new_core")
    assert "dependency unsatisfied" in result.stderr
```

---

## 📦 Formato .npkg

`.npkg` = ZIP con estructura:

```
facturacion_ec-0.1.0.npkg
├── __meta__.py
├── apps.py
├── models.py
├── admin.py
├── urls.py
├── api/
│   └── routes.py
├── migrations/
│   └── 0001_initial.py
├── static/
├── templates/
├── README.md
└── MANIFEST.json
```

**MANIFEST.json:**
```json
{
  "technical_name": "facturacion_ec",
  "version": "0.1.0",
  "erp_version": ">=0.5.0",
  "hash_sha256": "...",
  "signature": "..."  # Opcional: firma digital del paquete
}
```

---

## 🔏 Seguridad

- **Solo admins** pueden instalar módulos
- **Validación mandatory** antes de activar
- **Hash verification** para .npkg descargados
- **No ejecutar code arbitrario** durante install (solo Django standard)
- **Audit log** — cada install/upgrade/uninstall registrado

---

## 📊 Registry/Marketplace API (futuro)

```http
GET /api/v1/marketplace/modules/
# Devuelve catálogo oficial ERPNexus

GET /api/v1/marketplace/apps/facturacion/
# Detalle + download url

POST /api/v1/marketplace/install/
{
  "technical_name": "facturacion_ec",
  "version": "0.1.0",
  "source": "official"
}
```

---

**Siguiente ADR:** ADR-005 — API Design (Django Ninja vs DRF)
