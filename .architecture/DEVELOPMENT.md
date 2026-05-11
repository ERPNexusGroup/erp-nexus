# 📖 Guía de Desarrollo — ERP Nexus

**Para desarrolladores que extienden el framework**

**Última actualización:** 2026-05-12

---

## 🎯 Visión de Desarrollo

ERP Nexus está diseñado para ser **extensible por terceros** sin modificar el core. Como desarrollador de módulos, tu trabajo es:

1. ✅ Crear un módulo independiente (repo propio)
2. ✅ Usar las APIs públicas del core
3. ✅ No tocar `erp_nexus/` (excepto para bugs)
4. ✅ Escribir tests para tu módulo
5. ✅ Documentar tu módulo

---

## 🏗️ Anatomía de un Módulo

### Estructura mínima (mínimo viable):

```python
mi_modulo/
├── __meta__.py              # Metadata (REQUERIDO)
├── apps.py                  # AppConfig (REQUERIDO)
├── models.py                # Modelos Django (REQUERIDO)
├── admin.py                 # Admin Django (REQUERIDO)
├── urls.py                  # URLs del módulo (REQUERIDO)
├── services/                # Lógica de negocio
│   ├── __init__.py
│   └── invoicing.py
├── tests/
│   ├── __init__.py
│   ├── test_models.py
│   └── test_services.py
└── README.md                # Documentación (REQUERIDO)
```

### Campo por campo de `__meta__.py`:

| Campo | Requerido | Descripción | Ejemplo |
|-------|-----------|-------------|---------|
| `technical_name` | ✅ Sí | slug único (minúsculas, sin guiones) | `"facturacion_ec"` |
| `name` | ✅ Sí | Nombre mostrado en UI | `"Facturación Ecuador"` |
| `version` | ✅ Sí | SemVer X.Y.Z | `"0.1.0"` |
| `description` | ✅ Sí | Descripción corta | `"Facturación electrónica SRI"` |
| `dependencies` | ✅ Sí | Módulos core requeridos | `["core_companies"]` |
| `min_erp_version` | ✅ Sí | Versión mínima ERP Nexus | `"0.5.0"` |
| `repo` | ✅ Sí | URL del repositorio | `"https://github.com/..."` |
| `license` | ✅ Sí | Licencia OSI | `"MIT"` |
| `python` | ⚠️ Opcional | Requisitos Python | `">=3.11"` |
| `settings` | ⚠️ Opcional | Config defaults | `{"DEBUG": false}` |

---

## 🔄 Ciclo de Vida del Módulo

```
1. Desarrollo
   └─> Escribir código + tests localmente

2. Validación
   └─> sdk-nexus validate ./

3. Empaquetado
   └─> sdk-nexus package ./mi_modulo/

4. Instalación
   └─> manage.py install_module --package ./dist/mi_modulo-0.1.0.npkg

5. Activación
   └─> enable en Marketplace UI o CLI

6. Uso en producción
   └─> Funciona con ERP Nexus

7. Actualización
   └─> manage.py upgrade_module mi_modulo --package ./dist/mi_modulo-0.2.0.npkg
```

---

## 📡 Event Bus — Comunicación Sin Acoplamiento

El **Event Bus** es el mechanism de comunicación entre módulos.

### Emitir eventos:

```python
from apps.core_events.bus import EventBus

class Invoice(models.Model):
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Notificar a otros módulos
        EventBus.emit(
            event_type="invoice.created",
            source="facturacion_ec",
            payload={
                "invoice_id": self.id,
                "number": self.number,
                "total": str(self.total),
                "company_id": self.company_id,
            },
            metadata={"ambiente": self.ambiente}
        )
```

### Suscribirse a eventos:

```python
# inventory/events/handlers.py
def reserve_stock_on_invoice(payload: dict):
    """Cuando se crea factura, reservar inventario."""
    from inventory.models import StockReservation
    invoice_id = payload["invoice_id"]
    # Lógica de reserva...
    StockReservation.objects.create(...)

# Registrar en inventory/__init__.py o signals.py
from apps.core_events.bus import EventBus
EventBus.subscribe(
    event_type="invoice.created",
    subscriber_module="inventory",
    handler_path="inventory.events.handlers.reserve_stock_on_invoice",
)
```

### Eventos predefinidos (core):

| Evento | Payload | Descripción |
|--------|---------|-------------|
| `invoice.created` | `{invoice_id, total, company_id}` | Factura creada |
| `invoice.sent` | `{invoice_id, access_key}` | Factura enviada a SRI |
| `payment.received` | `{invoice_id, amount, date}` | Pago recibido |
| `customer.created` | `{customer_id, identification}` | Cliente creado |

---

## 🔐 Multi-Company (Multi-Tenant)

**CADA consulta debe filtrar por `company` activa.**

```python
# ❌ MAL — expone datos de todas las empresas
Product.objects.all()
Customer.objects.filter(name="Walter")

# ✅ BIEN — filtra por company de la request
company = request.active_company
Product.objects.filter(company=company)
Customer.objects.filter(company=company, name="Walter")

# En modelos, siempre incluir company ForeignKey:
class Customer(models.Model):
    company = models.ForeignKey(
        "core_companies.Company",
        on_delete=models.CASCADE
    )
    name = models.CharField(...)
```

### En APIs:

```python
@router.get("/")
def list_items(request):
    company = request.active_company  # Vía middleware
    items = Item.objects.filter(company=company)
    return [...]
```

### En signals/background tasks:

```python
from apps.core_companies.models import Company

def process_for_company(company_id: int):
    company = Company.objects.get(id=company_id)
    # Procesar solo para esa company
```

---

## 🧪 Testing

### Estructura de tests:

```
tests/
├── conftest.py           # Fixtures globales
├── test_models.py        # Tests modelos
├── test_services.py      # Tests lógica
├── test_api.py           # Tests API endpoints
└── fixtures/
    ├── companies.json
    └── products.json
```

### Ejemplo `conftest.py`:

```python
import pytest
from modules.facturacion_ec.models import Customer


@pytest.fixture
def company(company_factory):
    """Company de prueba."""
    return company_factory(name="Mi Empresa Test")


@pytest.fixture
def customer(company):
    """Customer básico."""
    return Customer.objects.create(
        company=company,
        identification_type="05",
        identification_number="1791234567001",
        name="Cliente Test"
    )
```

### Ejecutar tests:

```bash
# Todos los tests del módulo
uv run pytest facturacion_ec/tests/ -v

# Solo unitarios
uv run pytest -m "not integration"

# Con cobertura
uv run pytest --cov=facturacion_ec --cov-report=html

# Un test específico
uv run pytest tests/test_services.py::test_generate_access_key -v
```

### Tests obligatorios por tipo:

| Tipo | Cobertura mínima |
|------|------------------|
| Models | 80% (validaciones, `save()`, properties) |
| Services | 90% (lógica pura, sin DB) |
| API endpoints | 70% (happy path + errores) |
| Signals | 50% (si hay lógica compleja) |

---

## 🐛 Debugging

### Logging estructurado:

```python
import logging
logger = logging.getLogger(__name__)

logger.debug("Datos: %s", data)           # Solo en DEBUG
logger.info("Factura %s creada", inv.id)  # Siempre
logger.warning("IVA negativo: %s", tax)   # Sospechoso
logger.error("Error SRI: %s", exc)        # Fallo
```

**Niveles:**
- `DEBUG` — Detalle (desarrollo)
- `INFO` — Eventos normales (creación, envío)
- `WARNING` — Algo inesperado pero manejable
- `ERROR` — Fallo en operación
- `CRITICAL` — Sistema abajo

### Django Debug Toolbar:

```bash
# Instalar en desarrollo
uv pip install django-debug-toolbar

# En settings/development.py
INSTALLED_APPS += ["debug_toolbar"]
MIDDLEWARE += ["debug_toolbar.middleware.DebugToolbarMiddleware"]
```

---

## 📦 Dependencias

### Declarar en `__meta__.py`:

```python
MODULE_META = {
    ...
    "dependencies": [
        "core_companies>=0.5.0",
        "core_users>=0.5.0",
    ],
    "python_packages": [
        "lxml>=4.9.0",
        "cryptography>=41.0.0",
    ],
}
```

### Instalación automática:

Cuando se instala tu módulo, ERP Nexus:
1. Lee `dependencies` (módulos core)
2. Instala `python_packages` con `uv pip install`
3. Aplica migraciones
4. Registra en Marketplace

---

## 🔄 Migraciones

### Crear migración:

```bash
# Dentro del módulo
uv run python manage.py makemigrations facturacion_ec

# Review
git diff apps/facturacion/migrations/

# Aplicar
uv run python manage.py migrate
```

### Migraciones de datos (data migrations):

```python
# migrations/0002_load_sri_catalogs.py
from django.db import migrations


def load_sri_catalogs(apps, schema_editor):
    SriTipoComprobante = apps.get_model("facturacion_ec", "SriTipoComprobante")
    SriTipoComprobante.objects.bulk_create([
        SriTipoComprobante(code="01", name="Factura"),
        SriTipoComprobante(code="04", name="Nota de Crédito"),
        SriTipoComprobante(code="05", name="Nota de Débito"),
    ])


class Migration(migrations.Migration):
    dependencies = [("facturacion_ec", "0001_initial")]
    operations = [migrations.RunPython(load_sri_catalogs)]
```

---

## 📚 Documentación

### README.md — Requerido:

```markdown
# Facturación Ecuador

Módulo de facturación electrónica para Ecuador (SRI).

## Instalación

```bash
manage.py install_module --git https://github.com/ERPNexus/facturacion_ec.git
```

## Configuración

```python
# settings.py
FACTURACION_EC_AMBIENTE = 1  # 1=Pruebas, 2=Producción
FACTURACION_EC_AUTO_SEND = True
```

## API

- `POST /api/v1/facturacion_ec/invoices/` — Crear factura
- `GET /api/v1/facturacion_ec/invoices/{id}/` — Detalle
- `GET /api/v1/facturacion_ec/xml/{id}/` — Descargar XML

## Licencia

MIT
```

### Docstrings:

```python
def generate_access_key(ruc: str, ambiente: int, ...) -> str:
    """Genera clave de acceso SRI (49 dígitos).

    Formato: AAAAMMDD + estab(2) + ptoEmi(3) + sec(9) + random(8)

    Args:
        ruc: RUC empresa (13 dígitos)
        ambiente: 1=Pruebas, 2=Producción

    Returns:
        Clave acceso SRI (49 dígitos)

    Raises:
        ValueError: Si RUC inválido
    """
```

---

## 🔐 Seguridad

### Validación obligatoria:

```python
# ❌ NUNCA
invoice = Invoice.objects.get(id=invoice_id)

# ✅ SIEMPRE
invoice = get_object_or_404(
    Invoice,
    id=invoice_id,
    company=request.active_company  # Filtra por company
)
```

### Sanitización:

```python
# Validar inputs
from django.core.validators import validate_integer

def validate_ruc(ruc: str):
    if len(ruc) != 13:
        raise ValidationError("RUC debe tener 13 dígitos")
    if not ruc.isdigit():
        raise ValidationError("RUC solo dígitos")
```

---

## 🔗 GitHub Auto-discovery & Publishing

### Publicar un módulo en GitHub (para Marketplace)

1. **Repositorio en GitHub** (orgconfigurada en `GITHUB_ORG`):
   - Nombre: `<technical_name>` (ej: `facturacion_ec`)
   - Topic: `erp-nexus-module` (requerido para ser discoverable)
   - `__meta__.py` en raíz del repo (ver `MODULE_SPEC.md`)
   - Tags SemVer: `v0.1.0`, `v0.2.0`, etc.

2. **Settings del Core** (`erp_nexus/settings.py`):
   ```python
   GITHUB_ORG = os.getenv("GITHUB_ORG", "ERPNexusGroup")
   GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")  # opcional
   ```
   - Sin token: rate limit 60 requests/hora (anónimo)
   - Con token: 5000 requests/hora

3. **Sincronizar catálogo** (desde admin o CLI):
   ```bash
   # CLI
   python manage.py refresh_catalog [--dry-run]

   # Admin Django → core_marketplace → ModuleRegistry → Sync button
   ```
   El comando:
   - Lista repos de la org con topic `erp-nexus-module`
   - Para cada repo: valida `__meta__.py` (HEAD a raw.githubusercontent.com/.../__meta__.py)
   - Parsea metadata con `parse_meta_file()` (AST-based, seguro)
   - Crea/actualiza `ModuleCatalogItem`

4. **Instalar desde Admin**
   - Admin → Core Marketplace → Module Catalog
   - Click "Install" → ejecuta `module_install` command
   - Plugin se clona a `~/.erp-nexus/modules/` y se registra en DB
   - `apps.py:ready()` → `ModuleRegistry.discover_plugins()` lo añade a INSTALLED_APPS
   -Migraciones aplicadas → módulo activo

### Default Registry (auto-creación)
Si no existe ningún `ModuleRegistry` activo:
- `refresh_catalog` crea automáticamente "GitHub Official" (is_default=True)
- Signal `apps.py` `ready()` también lo crea al iniciar Django
- `url = GITHUB_ORG` (fallback a `ERPNexusGroup`)

### Admin UI Mejorado
- **ModuleRegistryAdmin**: botón "Sync" por fila + acción "Sync selected" (Jazzmin)
- **ModuleCatalogItemAdmin**: botones "Install" / "Reinstall" en columna Actions
- **ModuleLicenseAdmin**: barra visual de uso de asientos, badge valid/invalid, generate/revoke keys
- **Dashboard**: métricas de módulos instalados + últimos 5
- **Sidebar**: agrupación por `admin_menu_category` (ERPNext-style)

### parse_meta_file
Ubicación: `apps/core_marketplace/utils/module_loader.py`
Parsea `__meta__.py` via AST (solo literales, seguro). Usado por:
- `refresh_catalog._sync_github()`
- `module_install` (validación local)

---

## 🚀 Deploy y Release

### Versionado SemVer:

```
0.1.0  — Primera release (funcionalidad básica)
0.1.1  — Bugfix sin features nuevos
0.2.0  — Nueva feature (backward-compatible)
1.0.0  — API estable (no breaking changes después)
```

### Checklist pre-release:

- [ ] Tests pasan (>80% cobertura)
- [ ] Linter limpio (`ruff check .`)
- [ ] Type hints OK (`mypy .`)
- [ ] `__meta__.py` version bumped
- [ ] CHANGELOG.md actualizado
- [ ] README actualizado
- [ ] No hay secrets en el código

### Publicar en Marketplace:

```bash
# 1. Tag en git
git tag -a v0.1.0 -m "Release v0.1.0 — Facturación básica"
git push origin v0.1.0

# 2. GitHub Release (automático con CI/CD futuro)
# 3. Marketplace se actualiza via webhook
```

---

## 🏗️ Ejemplo Completo: Módulo `subscriptions`

```python
# __meta__.py
MODULE_META = {
    "technical_name": "subscriptions",
    "name": "Suscripciones",
    "version": "0.1.0",
    "dependencies": ["core_companies", "core_users"],
    "min_erp_version": "0.5.0",
}

# models.py
class Subscription(CompanyBoundModel):
    customer = models.ForeignKey("Customer", on_delete=models.CASCADE)
    plan = models.CharField(max_length=50)
    start_date = models.DateField()
    end_date = models.DateField()
    is_active = models.BooleanField(default=True)

    @property
    def is_valid(self):
        return self.is_active and self.end_date >= timezone.now().date()

# services/billing.py
def generate_monthly_invoice(subscription: Subscription):
    """Genera factura mensual de suscripción."""
    company = subscription.company
    # Lógica...
    EventBus.emit("subscription.billed", ...)

# api/routes.py
@router.post("/subscriptions/")
def create_subscription(request, data: SubscriptionIn):
    subscription = Subscription.objects.create(
        company=request.active_company,
        **data.dict()
    )
    return {"id": subscription.id}
```

---

## 🐛 Problemas Comunes

| Problema | Solución |
|----------|----------|
| Migración conflictiva | `.venv/bin/python manage.py makemigrations --merge` |
| Company no disponible en signal | Usar `apps.get_model` + filtrar por company |
| Evento no llega | Verificar `EventBus.subscribe` cargado en `apps.py:ready()` |
| Módulo no se activa | Revisar `__meta__.py` + dependencias |
| Tests fallan | Usar `pytest -vv` para debug, `--pdb` para traceback |

---

## 📞 Recursos

- **API Core Reference:** `/api/v1/docs/` (cuando el server corre)
- **Event Catalog:** `apps/core_events/models.py` — Lista eventos
- **Settings defaults:** `erp_nexus/settings/base.py`
- **Marketplace UI:** `/admin/core_marketplace/` (admin Django)

---

**¿Todo claro?** → Ve a `MODULE_SPEC.md` para especificación técnica detallada.
