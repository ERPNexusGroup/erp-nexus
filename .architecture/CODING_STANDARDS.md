# 📐 Reglas de Codificación — ERP Nexus

**Versión:** 1.0.0-alpha  
**Fecha:** 2026-05-10  
**Basado en:** PEP 8, Django Coding Style, Google Python Style Guide

---

## 🎯 Filosofía

1. **Simple sobre complejo** — Un módulo hace una cosa bien
2. **Explicitable sobre ingenioso** — Código que se explica solo
3. **Testeable por diseño** — Si no se puede testear, está mal diseñado
4. **Documentado inline** — Comentarios explican el `por qué`, no el `qué`
5. **Consistente sobre creativo** — Seguir convenciones establecidas

---

## 📝 Estilo General (Python)

### **Formato**
- **Indentación:** 4 espacios (NO tabs)
- **Línea máxima:** 100 caracteres (máximo 120 en casos excepcionales)
- **Codificación:** UTF-8
- **Final de línea:** `\n` (LF Unix)
- **Tipo de archivos:** `.py` → Python 3.12+ (type hints obligatorios)

### **Import Order (PEP 8)**
```python
# 1. Standard library
import os
import json
from datetime import datetime
from typing import Optional

# 2. Django core
from django.conf import settings
from django.db import models
from django.http import HttpResponse

# 3. Third-party
from ninja import Router, Schema
from rest_framework import serializers

# 4. Local (ERP Nexus)
from apps.core_companies.models import Company
from modules.facturacion_ec.services import generate_xml
```

### **Naming Conventions**

| Tipo | Convención | Ejemplo |
|------|------------|---------|
| Módulo/Package | `snake_case` | `facturacion_ec` |
| Clase | `PascalCase` | `InvoiceManager`, `XMLGenerator` |
| Función/Variable | `snake_case` | `generate_access_key`, `company_id` |
| Constante | `UPPER_SNAKE_CASE` | `MAX_INVOICES_PER_MONTH` |
| Privado (método) | `_leading_underscore` | `_validate_signature()` |
| Django Model | `PascalCase` | `Customer`, `InvoiceLine` |
| Django Field | `snake_case` | `identification_number` |
| URL name | `snake_case` | `facturacion_ec:list` |

---

## 🏗️ Estructura de Archivos

```
modules/
└── {module_name}/
    ├── __init__.py              # Vacío o importaciones públicas
    ├── __meta__.py              # Metadata (requerido)
    ├── apps.py                  # AppConfig
    ├── models.py                # Modelos Django
    ├── admin.py                 # Admin Django
    ├── urls.py                  # URLs del módulo
    ├── signals.py               # Django signals
    ├── services/                # Lógica de negocio (puro Python)
    │   ├── __init__.py
    │   └── {service}.py
    ├── api/                     # REST API
    │   ├── __init__.py
    │   └── routes.py
    ├── templates/{module}/      # HTML templates
    ├── static/{module}/         # CSS/JS/images
    ├── tests/                   # Pruebas
    │   ├── __init__.py
    │   ├── test_models.py
    │   ├── test_services.py
    │   └── test_api.py
    ├── migrations/              # Django migrations
    │   └── 0001_initial.py
    └── README.md                # Documentación
```

---

## 📐 Patrones de Código

### **Models**

```python
class Invoice(models.Model):
    """Factura electrónica emitida por una empresa."""

    # ─── Campos obligatorios ────────────────────────────────────────
    company = models.ForeignKey(
        "core_companies.Company",
        on_delete=models.CASCADE,
        related_name="invoices"
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="invoices_created"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # ─── Campos específicos ─────────────────────────────────────────
    number = models.CharField(max_length=20, unique=True)
    date = models.DateField()
    customer = models.ForeignKey("Customer", on_delete=models.PROTECT)
    subtotal = models.DecimalField(max_digits=12, decimal_places=2)
    tax_total = models.DecimalField(max_digits=12, decimal_places=2)
    total = models.DecimalField(max_digits=12, decimal_places=2)

    # ─── Estado SRI ─────────────────────────────────────────────────
    sri_status = models.CharField(
        max_length=20,
        choices=[
            ("draft", "Borrador"),
            ("pending", "Pendiente envío"),
            ("sent", "Enviado"),
            ("accepted", "Aceptado"),
            ("rejected", "Rechazado"),
        ],
        default="draft"
    )
    ambiente = models.IntegerField(
        choices=[(1, "Pruebas"), (2, "Producción")],
        default=1
    )
    access_key = models.CharField(max_length=50, unique=True, blank=True)
    xml_content = models.TextField(blank=True)

    # ─── Meta ───────────────────────────────────────────────────────
    class Meta:
        ordering = ["-date", "-id"]
        unique_together = [("company", "number")]

    def __str__(self):
        return f"{self.number} — {self.customer.name}"

    # ─── Métodos de negocio ────────────────────────────────────────
    def calculate_totals(self):
        """Calcula subtotal, impuestos y total desde líneas."""
        self.subtotal = sum(l.subtotal for l in self.lines.all())
        self.tax_total = sum(l.tax_amount for l in self.lines.all())
        self.total = self.subtotal + self.tax_total

    @property
    def is_authorized(self):
        """True si la factura está aceptada por SRI."""
        return self.sri_status == "accepted"
```

### **Services**

```python
# services/xml_generator.py
from pathlib import Path
from jinja2 import Template, Environment, FileSystemLoader
from lxml import etree


class XMLGenerator:
    """Generador de XML para facturas electrónicas SRI.

    Atributos:
        invoice: Instancia de Invoice a generar XML
        template_path: Ruta a plantilla XSLT/Jinja2
    """

    XSD_PATH = Path(__file__).parent.parent / "schemas" / "factura.xsd"

    def __init__(self, invoice: "Invoice"):
        self.invoice = invoice

    def render(self) -> str:
        """Genera el XML firmado."""
        context = self._build_context()
        template = self._get_template()
        raw_xml = template.render(**context)
        return self._validate(raw_xml)

    def _build_context(self) -> dict:
        """Construye contexto para plantilla."""
        return {
            "invoice": self.invoice,
            "company": self.invoice.company,
            "customer": self.invoice.customer,
            "lines": self.invoice.lines.select_related("product"),
            "taxes": self._compute_taxes(),
        }

    def _get_template(self) -> Template:
        """Carga plantilla Jinja2."""
        env = Environment(loader=FileSystemLoader(
            Path(__file__).parent.parent / "templates" / "facturacion_ec"
        ))
        return env.get_template("factura.xml.j2")

    def _validate(self, xml: str) -> str:
        """Valida XML contra XSD SRI."""
        schema_doc = etree.parse(str(self.XSD_PATH))
        schema = etree.XMLSchema(schema_doc)
        doc = etree.fromstring(xml.encode("utf-8"))
        schema.assertValid(doc)
        return etree.tostring(doc, pretty_print=True).decode()
```

### **API Endpoints**

```python
# api/routes.py
from ninja import Router, Schema
from django.shortcuts import get_object_or_404

from ..models import Invoice
from ..services import XMLGenerator, send_to_sri

router = Router(tags=["Facturación"])


class InvoiceCreate(Schema):
    """Schema para creación de facturas."""
    customer_id: int
    lines: list[dict]
    date: str = None  # ISO date YYYY-MM-DD


@router.post("/", response={200: dict, 400: dict, 404: dict})
def create_invoice(request, data: InvoiceCreate):
    """Crea una nueva factura y la envía al SRI.

    Args:
        request: Request HTTP (contiene active_company)
        data: Datos de factura (customer, lines, date)

    Returns:
        200: {id, number, access_key, sri_status}
        400: {error: "mensaje"}
        404: {error: "Cliente no encontrado"}

    Note:
        - Si `FACTURACION_EC_AUTO_SEND=True`, intenta enviar a SRI
        - En caso de error de envío, retorna 200 con sri_status=pending
    """
    company = request.active_company

    # Validar customer existe en esta company
    try:
        customer = Customer.objects.get(
            id=data.customer_id,
            company=company
        )
    except Customer.DoesNotExist:
        return 404, {"error": "Cliente no encontrado"}

    # Crear factura
    invoice = Invoice.objects.create(
        company=company,
        customer=customer,
        date=datetime.strptime(data.date, "%Y-%m-%d").date()
        if data.date else timezone.now().date(),
        created_by=request.user,
    )

    # Crear líneas
    for line_data in data.lines:
        InvoiceLine.objects.create(invoice=invoice, **line_data)

    invoice.calculate_totals()
    invoice.save()

    # Generar XML + enviar a SRI (async ideal)
    try:
        result = send_to_sri(invoice.id)
        invoice.sri_status = "accepted" if result["ok"] else "rejected"
        invoice.save(update_fields=["sri_status"])
    except Exception as exc:
        # Log error pero no fallar creación
        logger.error(f"SRI send failed invoice={invoice.id}: {exc}")
        invoice.sri_status = "pending"

    return {
        "id": invoice.id,
        "number": invoice.number,
        "access_key": invoice.access_key,
        "sri_status": invoice.sri_status,
    }
```

---

## 🧪 Testing

### **Convenciones:**
- Archivos: `test_{module}.py`
- Clases: `Test{ClassName}` (ej: `TestInvoice`)
- Métodos: `test_{condition}` (ej: `test_create_requires_company`)
- Usar `pytest-django` fixtures

```python
# tests/test_models.py
import pytest
from modules.facturacion_ec.models import Customer, Invoice


@pytest.mark.django_db
class TestCustomer:
    @pytest.fixture
    def company(self, company_factory):
        return company_factory()

    def test_create_customer_requires_company(self, company):
        """Company es obligatorio."""
        cust = Customer.objects.create(
            company=company,
            identification_type="05",
            identification_number="1750234556",
            name="Test Customer"
        )
        assert cust.company == company

    def test_unique_together_identification(self, company):
        """RUC+type deben ser únicos por company."""
        Customer.objects.create(
            company=company,
            identification_type="05",
            identification_number="999",
            name="A"
        )
        with pytest.raises(IntegrityError):
            Customer.objects.create(
                company=company,
                identification_type="05",
                identification_number="999",
                name="B"
            )
```

---

## 🗄️ Database Migrations

### **Generar migraciones:**
```bash
# Dentro del módulo
cd modules/facturacion_ec
uv run python manage.py makemigrations facturacion_ec
```

### **Convenciones:**
- Nombre: `0001_initial.py`, `0002_add_field_x.py`
- Siempre incluir `dependencies` si depende de otra app
- NO modificar migraciones después de aplicarlas en producción
- NO hacer `migrate --fake` sin justificación

```python
# migrations/0002_invoice_access_key.py
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("facturacion_ec", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="invoice",
            name="access_key",
            field=models.CharField(
                max_length=50,
                unique=True,
                blank=True,
                help_text="Clave de acceso SRI (49 dígitos)"
            ),
        ),
        migrations.AddIndex(
            model_name="invoice",
            index=models.Index(fields=["company", "sri_status"]),
        ),
    ]
```

---

## 🔐 Seguridad

### **Validación Obligatoria:**
- ✅ Validar `request.active_company` en cada endpoint
- ✅ Sanitizar entradas (Django ORM previene SQLi)
- ✅ Validar `company_id` en cada query
- ✅ No exponer datos entre companies
- ✅ Logs de auditoría para cambios sensibles

### **Queries Peligrosas (⚠️ NO hacer):**
```python
# ❌ MAL — expone datos de otras companies
Invoice.objects.all()

# ✅ BIEN — filtra por company activa
Invoice.objects.filter(company=request.active_company)

# ❌ MAL — no valida ownership
customer = Customer.objects.get(id=customer_id)

# ✅ BIEN — valida company
customer = get_object_or_404(
    Customer,
    id=customer_id,
    company=request.active_company
)
```

---

## 📝 Commits

### **Convención: Conventional Commits**
```
tipo(scope): descripción breve

[demo]
feat(facturacion_ec): add XML generator with XSD validation
fix(invoice): correct tax calculation for zero-rated items
docs(api): add OpenAPI schema for invoice endpoints
test(services): add unit tests for digital signature
refactor(models): split Invoice into base/detail models
chore(deps): update django-ninja to 3.0
```

**Tipos:**
- `feat` — nueva funcionalidad
- `fix` — corrección de bug
- `docs` — cambios en documentación
- `test` — añadir/修正 pruebas
- `refactor` — refactorización sin cambios funcionales
- `chore` — tareas de mantenimiento (deps, CI, etc.)
- `style` — formato/ whitespace (no funcional)
- `perf` — mejora de rendimiento

---

## 🔄 Code Review Checklist

**Antes de PR:**
- [ ] Tests pasan (`pytest -q`)
- [ ] Linter OK (`ruff check .` o `flake8`)
- [ ] Type hints completos
- [ ] Docstrings en funciones/clases públicas
- [ ] No hay código muerto/comentado
- [ ] Migraciones generadas y funcionan
- [ ] README actualizado (si aplica)

**Durante PR:**
- [ ] Lógica clara y simple
- [ ] Manejo de errores apropiado
- [ ] Performance considerada (N+1 queries)
- [ ] Seguridad: validación company, permisos
- [ ] Backward compatible (si es módulo estable)

---

## 📚 Documentación

### **Docstrings (Google Style)**
```python
def generate_access_key(ruc: str, ambiente: int, establishment_code: str,
                        emission_point: str, sequential: str,
                        date: Optional[datetime] = None) -> str:
    """Genera la clave de acceso única del SRI (49 dígitos).

    Formato SRI Ecuador:
        AAAAMMDD + 2d estab + 3d ptoEmi + 15d secuencial + 9d random+verificador

    Args:
        ruc: RUC de la empresa (13 dígitos, no se usa en clave pero es parte del contexto)
        ambiente: 1=Pruebas, 2=Producción
        establishment_code: Código establecimiento (2 dígitos)
        emission_point: Código punto emisión (3 dígitos)
        sequential: Número secuencial (9 dígitos)
        date: Fecha emisión (default: hoy)

    Returns:
        Clave de acceso de hasta 49 dígitos

    Raises:
        ValueError: Si los parámetros tienen formato inválido
    """
```

---

## 🚫 Anti-Patrones (NO hacer)

| Anti-patrón | Por qué es malo | Alternativa |
|-------------|----------------|-------------|
| `from django.conf import settings` + `settings.DEBUG` scattered | Hard to test/mocks | Inyectar settings o usar factory |
| `print()` para logging | No estructurado, no levels | `import logging; logger = logging.getLogger(__name__)` |
| `queryset = Model.objects.all()` sin filter por company | Data leak | Siempre filtrar por `request.active_company` |
| `try: ... except: pass` | Silencia errores reales | Loggear excepción o re-raise |
| `if settings.DEBUG: ... else: ...` en producción | Código condicional por ambiente | Usar settings diferentes |
| Hardcodear strings (ej: "01") | Typos no detectados | Usar `choices` o constants |

---

## 🔧 Herramientas de Calidad

```bash
# Formato (Black)
uv pip install black isort
black apps/facturacion/
isort apps/facturacion/

# Linting (Ruff) — rápido y moderno
uv pip install ruff
ruff check . --fix

# Type checking (mypy)
uv pip install mypy
mypy apps/facturacion/

# Tests
uv run pytest apps/facturacion/tests/ -v --cov

# Security
uv pip install bandit
bandit -r apps/facturacion/
```

**.pre-commit-config.yaml** (opcional):
```yaml
repos:
  - repo: https://github.com/psf/black
    rev: 24.4.2
    hooks:
      - id: black
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.4.7
    hooks:
      - id: ruff
        args: [--fix]
```

---

## 📊 Métricas de Calidad

| Métrica | Mínimo | Ideal |
|---------|--------|-------|
| Cobertura tests | 70% | 90% |
| Linter issues | 0 | 0 |
| Type errors (mypy) | 0 | 0 |
| Complexity (radon) | <10 | <5 |
| Doc coverage | 60% | 100% |

---

## 🔄 Workflow de Desarrollo

```bash
# 1. Crear branch
git checkout -b feat/factura-email

# 2. Desarrollo
# - Escribir código
# - Escribir tests primero (TDD)
# - Documentar docstrings

# 3. Validación local
uv run pytest facturacion_ec/tests/ -v
ruff check facturacion_ec/
mypy facturacion_ec/

# 4. Commit (conventional commit)
git add .
git commit -m "feat(facturacion_ec): add email notification on invoice approval"

# 5. PR → CI ejecuta: tests + lint + typecheck
```

---

## 📖 Referencias

- [PEP 8 — Style Guide for Python Code](https://peps.python.org/pep-0008/)
- [Django Coding Style](https://docs.djangoproject.com/en/dev/internals/contributing/writing-code/coding-style/)
- [Google Python Style Guide](https://google.github.io/styleguide/pyguide.html)
- [Conventional Commits](https://www.conventionalcommits.org/)

---

**Aprobación:** Todo código nuevo debe cumplir estas reglas. PRs que no cumplan serán bloqueados en CI.
