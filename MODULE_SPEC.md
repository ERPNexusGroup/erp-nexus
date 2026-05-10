# 📝 Especificación de Módulos — ERP Nexus

**Versión:** 1.0.0-alpha  
**Fecha:** 2026-05-10

---

## 📦 Qué es un Módulo

Un **módulo** es una app Django autocontenida que extiende ERP Nexus. Vive en su propio repositorio Git y se instala/desinstala dinámicamente a través del Marketplace.

---

## 🏗️ Estructura Obligatoria

```
{módulo}/
├── __meta__.py                    ✅ REQUERIDO
├── __init__.py                    ✅ REQUERIDO
├── apps.py                        ✅ REQUERIDO
├── models.py                      ✅ REQUERIDO
├── admin.py                       ✅ REQUERIDO
├── urls.py                        ✅ REQUERIDO
├── signals.py                     ⚠️  Recomendado
├── services/                      ✅ RECOMENDADO
│   ├── __init__.py
│   └── *.py
├── api/                           ✅ RECOMENDADO (si expone API)
│   └── routes.py
├── templates/{technical_name}/    ⚠️  Si usa templates
├── static/{technical_name}/       ⚠️  Si usa CSS/JS
├── tests/
│   ├── __init__.py
│   ├── test_models.py
│   ├── test_services.py
│   └── test_api.py
├── migrations/
│   ├── 0001_initial.py
│   └── ...
├── data/                          ⚠️  Si necesita seed data
│   ├── fixtures.json
│   └── ...
├── module.yaml                     ✅ RECOMENDADO (metadata alternativa)
└── README.md                      ✅ REQUERIDO
```

---

## 📋 `__meta__.py` — Metadata (OBLIGATORIO)

```python
# apps/facturacion/__meta__.py

MODULE_META = {
    # Identificación
    "name": "Facturación Electrónica Ecuador",
    "technical_name": "facturacion_ec",
    "version": "0.1.0",
    "description": "Emisión de facturas electrónicas SRI Ecuador (XML, firma digital, envío)",
    "summary": "Facturación electrónica para Ecuador",
    "author": "ERP Nexus Team",
    "author_email": "dev@erpnexus.ec",
    "repo": "https://github.com/ERPNexus/facturacion_ec",
    "license": "MIT",

    # Dependencias
    "dependencies": [
        "core_companies>=0.5.0",
        "core_users>=0.5.0",
    ],
    "optional_dependencies": [
        "core_chart_of_accounts>=0.5.0",  # Si necesita plan de cuentas
    ],

    # Compatibilidad ERP Nexus
    "min_erp_version": "0.5.0",
    "max_erp_version": "0.9.0",

    # Configuración
    "settings": {
        "FACTURACION_EC_ENVIRONMENT": "pruebas",  # pruebas|produccion
        "FACTURACION_EC_AUTO_SEND": True,         # envío automático
        "FACTURACION_EC_DAYS_DUE": 30,            # días vencimiento
    },

    # Licenciamiento (si aplica)
    "licensing": {
        "type": "tiered",  # free|paid|tiered
        "plans": ["free", "monthly_10", "yearly_100", "lifetime"],
        "free_tier": {
            "max_invoices_month": 10,
        },
    },

    # UI
    "icon": "fa-file-invoice-dollar",  # FontAwesome icon name
    "menu_category": "Contabilidad",    # Categoría en menú admin
    "menu_order": 10,                   # Orden en menú

    # URLs
    "docs_url": "https://erpnexus.facturacion_ec/docs",
    "support_url": "https://github.com/ERPNexus/facturacion_ec/issues",
}
```

---

## 🎯 `apps.py` — AppConfig

```python
# apps/facturacion/apps.py

from django.apps import AppConfig
from django.db.models.signals import post_migrate


class FacturacionEcConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'modules.facturacion_ec'
    verbose_name = "Facturación Electrónica Ecuador"

    def ready(self):
        """
        Señales y hooks que se ejecutan al cargar la app.
        Importar signals aquí para que se registren.
        """
        # Importar signals
        import modules.facturacion_ec.signals  # noqa: F401

        # Hook post-migrate para seed data
        post_migrate.connect(self.seed_initial_data, sender=self)

    def seed_initial_data(self, **kwargs):
        """Crear datos iniciales (catálogos SRI) si no existen."""
        from django.conf import settings
        if not settings.DEBUG:
            # Solo seed en desarrollo
            return

        from .models import SriAmbiente, SriTipoComprobante, SriImpuesto

        # Ambientes SRI (1=pruebas, 2=producción)
        SriAmbiente.objects.get_or_create(
            code=1, defaults={"name": "Pruebas"}
        )
        SriAmbiente.objects.get_or_create(
            code=2, defaults={"name": "Producción"}
        )

        # Tipos de comprobante
        SriTipoComprobante.objects.get_or_create(
            code="01",
            defaults={
                "name": "Factura",
                "description": "Factura de venta"
            }
        )
        # ... más seed data
```

---

## 📐 `models.py` — Modelos Django

### **Convenciones:**
1. Todos los modelos deben tener `company = ForeignKey(Company)` como primer campo
2. Usar `CompanyManager` para queries automáticas por company
3. `created_by`, `created_at`, `updated_at` en todos los modelos
4. `is_active` para borrado lógico (excepto documentos legales)

```python
# Ejemplo: Customer
from django.db import models
from apps.core_companies.models import Company


class CustomerManager(models.Manager):
    """Manager que filtra automáticamente por company."""
    def get_queryset(self):
        from django.conf import settings
        if settings.DEBUG:
            return super().get_queryset()
        return super().get_queryset().filter(company=self.request.active_company)


class Customer(models.Model):
    """Cliente/Emisor/Receptor de facturas."""
    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name="customers"
    )
    identification_type = models.CharField(
        max_length=2,
        choices=[("04", "RUC"), ("05", "Cédula"), ("06", "Pasaporte")]
    )
    identification_number = models.CharField(max_length=20)
    name = models.CharField(max_length=200)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=50, blank=True)
    address = models.TextField(blank=True)
    razon_social = models.CharField(max_length=200, blank=True)
    is_active = models.BooleanField(default=True)

    created_by = models.ForeignKey(
        "users.User",
        on_delete=models.SET_NULL,
        null=True,
        related_name="customers_created"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = CustomerManager()

    class Meta:
        unique_together = ("company", "identification_type", "identification_number")
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} ({self.identification_number})"
```

---

## 🔗 `services/` — Lógica de Negocio

Separar lógica de negocio de views/models. Cada servicio es un módulo Python puro.

```python
# services/xml_generator.py
from jinja2 import Template
from lxml import etree


class XMLGenerator:
    """Genera XML para facturas electrónicas SRI Ecuador."""

    XSD_SCHEMA = "schemas/factura_v1.0.xsd"

    def __init__(self, invoice):
        self.invoice = invoice

    def render(self) -> str:
        """Genera XML firmado."""
        context = self._build_context()
        template = self._load_template()
        xml_raw = template.render(**context)
        return self._validate_and_format(xml_raw)

    def _build_context(self):
        return {
            "invoice": self.invoice,
            "company": self.invoice.company,
            "customer": self.invoice.customer,
            "lines": self.invoice.lines.all(),
            "taxes": self._calculate_taxes(),
        }

    def _load_template(self):
        from pathlib import Path
        template_path = Path(__file__).parent.parent / "templates" / "factura.xml"
        return Template(template_path.read_text())

    def _validate_and_format(self, xml: str) -> str:
        # Validar contra XSD
        # Formatear (pretty print)
        return xml
```

---

## 🌐 `api/routes.py` — REST API (Django Ninja)

```python
# api/routes.py
from ninja import Router, Schema
from django.shortcuts import get_object_or_404

from ..models import Invoice, Customer
from ..services import generate_xml, send_to_sri

router = Router(tags=["Facturación Electrónica"])


# ─── SCHEMAS ──────────────────────────────────────────────────────────

class CustomerIn(Schema):
    identification_type: str
    identification_number: str
    name: str
    email: str = ""
    phone: str = ""
    address: str = ""


class InvoiceLineIn(Schema):
    product_code: str
    quantity: float
    unit_price: float
    discount: float = 0


class InvoiceCreate(Schema):
    customer: CustomerIn
    lines: list[InvoiceLineIn]
    date: str = None  # ISO date YYYY-MM-DD


class InvoiceOut(Schema):
    id: int
    number: str
    date: str
    customer_name: str
    total: float
    sri_status: str


# ─── ENDPOINTS ────────────────────────────────────────────────────────

@router.get("/", response=list[InvoiceOut])
def list_invoices(request, status: str = None):
    """Lista facturas de la empresa activa."""
    company = request.active_company
    qs = Invoice.objects.filter(company=company)
    if status:
        qs = qs.filter(sri_status=status)
    return qs.order_by("-date")[:100]


@router.post("/")
def create_invoice(request, data: InvoiceCreate):
    """Crea factura y la envía al SRI (async opcional)."""
    company = request.active_company

    # 1. Crear/obtener customer
    customer, _ = Customer.objects.get_or_create(
        company=company,
        identification_number=data.customer.identification_number,
        defaults={...}
    )

    # 2. Crear factura
    invoice = Invoice.objects.create(...)

    # 3. Enviar a SRI (async ideal)
    # from .tasks import send_invoice_async
    # send_invoice_async.delay(invoice.id)

    return {"id": invoice.id, "number": invoice.number}
```

---

## 🔄 `signals.py` — Hooks

```python
# signals.py
from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver

from .models import Invoice, SRISendLog


@receiver(post_save, sender=Invoice)
def invoice_post_save(sender, instance, created, **kwargs):
    """Hook post-guardado de factura."""
    if created:
        # Auto-enviar a SRI si está configurado
        from django.conf import settings
        if getattr(settings, "FACTURACION_EC_AUTO_SEND", False):
            send_invoice_to_sri(instance.id)


@receiver(pre_delete, sender=Invoice)
def invoice_pre_delete(sender, instance, **kwargs):
    """No permitir borrar facturas autorizadas."""
    if instance.sri_status == "accepted":
        raise Exception("No se puede eliminar factura autorizada por SRI")
```

---

## 🧪 `tests/` — Pruebas

```python
# tests/test_models.py
import pytest
from django.conf import settings

from modules.facturacion_ec.models import Customer, Invoice


@pytest.mark.django_db
class TestCustomer:
    def test_create_customer_requires_company(self, company):
        """Company es obligatorio."""
        cust = Customer.objects.create(
            company=company,
            identification_number="1750234556",
            name="Cliente Test",
            identification_type="05"
        )
        assert cust.company == company


# tests/test_api.py
from ninja.testing import TestClient

from modules.facturacion_ec.api.routes import router

client = TestClient(router)


def test_create_invoice(company, customer, product, api_request):
    request = api_request(company=company)
    payload = {
        "customer": {
            "identification_type": "05",
            "identification_number": "1750234557",
            "name": "Nuevo Cliente"
        },
        "lines": [
            {"product_code": product.code, "quantity": 2, "unit_price": 100}
        ]
    }
    response = client.post("/", payload, request=request)
    assert response.status_code == 200
    assert response["sri_status"] == "pending"
```

---

## 📖 `README.md` — Documentación

```markdown
# Facturación Electrónica Ecuador

Módulo ERP Nexus para emisión de facturas electrónicas SRI Ecuador.

## Instalación

```bash
# Desde el marketplace de ERP Nexus
POST /api/v1/modules/
{
  "technical_name": "facturacion_ec",
  "repo": "https://github.com/ERPNexus/facturacion_ec",
  "version": "0.1.0"
}
```

## Configuración

```python
# settings.py o .env
FACTURACION_EC_ENVIRONMENT = "pruebas"  # pruebas|produccion
FACTURACION_EC_CERT_PATH = "/path/to/cert.p12"
FACTURACION_EC_CERT_PASSWORD = "password"
FACTURACION_EC_AUTO_SEND = True
```

## API Endpoints

| Endpoint | Método | Descripción |
|----------|--------|-------------|
| `/api/v1/facturacion_ec/` | GET | Lista facturas |
| `/api/v1/facturacion_ec/` | POST | Crea factura |
| `/api/v1/facturacion_ec/{id}/` | GET | Detalle factura |
| `/api/v1/facturacion_ec/{id}/xml` | GET | Descarga XML |
| `/api/v1/facturacion_ec/customers/` | GET | Buscar clientes |

## Licencia

MIT — Ver LICENSE
```

---

## 📦 `module.yaml` — Metadata Alternativa

Para instaladores que usan YAML:

```yaml
name: Facturación Electrónica Ecuador
technical_name: facturacion_ec
version: 0.1.0
description: Módulo para facturación electrónica SRI Ecuador
repo: https://github.com/ERPNexus/facturacion_ec
license: MIT
dependencies:
  - core_companies >= 0.5.0
  - core_users >= 0.5.0
min_erp_version: 0.5.0
settings:
  FACTURACION_EC_ENVIRONMENT: pruebas
  FACTURACION_EC_AUTO_SEND: true
```

---

## 🔐 Reglas de Integración con el Core

### **NO hacer:**
- ❌ Modificar `erp_nexus/settings.py` desde el módulo
- ❌ Importar modelos core hardcodeados (usar get_model)
- ❌ Asumir que hay empresa activa sin verificar
- ❌ Hacer migrations a mano (dejar que Django las genere)
- ❌ Agregar URLs sin registrar en `urls.py` del módulo

### **SÍ hacer:**
- ✅ Usar `django.conf.settings` para config
- ✅ Usar `apps.get_model()` para modelos core (si son dinámicos)
- ✅ Verificar `request.active_company` en cada endpoint
- ✅ Dejar que `makemigrations` detecte cambios
- ✅ Registrar urls en `modules/{module}/urls.py`

---

## 📦 Empaquetado y Distribución

El módulo se distribuye como **repositorio Git**:

```
https://github.com/ERPNexus/facturacion_ec/
├── .git/
├── modules/
│   └── facturacion_ec/     ← Código fuente
├── requirements.txt         ← Dependencias Python extra
├── pyproject.toml          ← Config build (opcional)
└── README.md
```

**Instalación ERP Nexus:**
1. Clona repo a `~/.erp-nexus/apps/facturacion/`
2. Agrega `modules.facturacion_ec` a `INSTALLED_APPS`
3. Ejecuta `python manage.py migrate facturacion_ec`
4. Registra en `ModuleCatalogItem`

---

## 🔄 Ciclo de Vida de un Módulo

```
┌─────────────┐
│   Creación  │  Nuevo módulo
└──────┬──────┘
       │
┌──────▼──────┐
│  Desarrollo │  En repo Git, siguiendo estándares
└──────┬──────┘
       │
┌──────▼──────┐
│  Release vX │  Tag en Git + changelog
└──────┬──────┘
       │
┌──────▼──────┐
│  Publicar   │  Agregar a catálogo Marketplace
│  en Catálogo│
└──────┬──────┘
       │
┌──────▼──────┐
│ Instalar    │  Cliente instala desde marketplace
└──────┬──────┘
       │
┌──────▼──────┐
│  Ejecución  │  Migraciones aplicadas, módulo activo
└──────┬──────┘
       │
┌──────▼──────┐
│  Update     │  Nueva versión disponible
└──────┬──────┘
       │
┌──────▼──────┐
│  Desinstalar│  Eliminar datos (o archivar)
└─────────────┘
```

---

## 📊 Checklist de Aprobación de Módulo

Para que un módulo sea aceptado en el Marketplace oficial:

- [ ] Tiene `__meta__.py` con todos los campos requeridos
- [ ] Cubre al menos 1 dominio de negocio claro
- [ ] Tests unitarios >70% cobertura
- [ ] API REST documentada (Django Ninja autodoc)
- [ ] Admin Django configurado
- [ ] Migraciones funcionan en BD limpia
- [ ] No modifica core ERP Nexus
- [ ] Dependencias declaradas correctamente
- [ ] README completo con instalación/config
- [ ] License OSI aprobada (MIT, Apache 2.0, BSD-3)

---

**Documentos relacionados:**
- `ARCHITECTURE.md` — Arquitectura general
- `CODING_STANDARDS.md` — Reglas de código
- `REQUIREMENTS.md` — Requisitos funcionales
