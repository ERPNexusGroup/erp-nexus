# ADR-005: API Framework — Django Ninja vs Django REST Framework

**Estado:** ✅ Aceptado  
**Fecha:** 2026-05-10  
**Contexto:** Fase 1 — API endpoints  
**Decisores:** Walter Cun, ERP Nexus Team

---

## 📋 Contexto

ERP Nexus necesita exponer una API REST moderna:

- OpenAPI/Swagger auto-generado
- Type hints / Pydantic-like validation
- Async support (futuro)
- Simple de usar para devs de módulos

### **Opción A: Django REST Framework (DRF)**

**Pros:**
- Maduro, ampliamente usado
- Viewsets, routers, serializers
- Buen admin integration

**Contras:**
- Verboso (serializers duplican models)
- No nativo type hints
- OpenAPI requiere drf-spectacular
- Serializers = boilerplate

### **Opción B: Django Ninja (Elegido)**

**Pros:**
- Pydantic-like schemas (type hints nativos)
- OpenAPI auto-generado (mejor que DRF)
- Async/await listo
- No serializers (usa models directamente o Schemas)
- Más rápido (menos capas)

**Contras:**
- Menos maduro (pero estable)
- Menos plugins/community que DRF

---

## 🎯 Decisión

**Elegimos Django Ninja**

```python
# API endpoint con Django Ninja
from ninja import Router, Schema

router = Router()

class InvoiceCreate(Schema):
    customer_id: int
    date: date
    lines: list[InvoiceLineIn]

@router.post("/invoices/")
def create_invoice(request, data: InvoiceCreate):
    # data tipado automáticamente
    company = request.active_company
    invoice = Invoice.objects.create(
        company=company,
        customer_id=data.customer_id,
        ...
    )
    return {"id": invoice.id, "number": invoice.number}
```

---

## 🏗️ Estructura API

```
apps/facturacion/
├── api/
│   ├── __init__.py
│   └── routes.py       # Router con endpoints
└── models.py           # Modelos Django (usados en schemas)
```

**Router registration:**

```python
# facturacion_ec/api/__init__.py
from .routes import router as facturacion_router

# Export para incluir en API principal
router = facturacion_router
```

```python
# apps/core_api/v1/__init__.py
from modules.facturacion_ec.api import router as facturacion_router

api_router = APIRouter()
api_router.add_router("/facturacion_ec/", facturacion_router)
```

---

## 📚 Schemas con Type Hints

```python
from datetime import date
from decimal import Decimal
from ninja import Schema
from typing import Optional, List


class InvoiceLineIn(Schema):
    """Schema para crear línea de factura."""
    product_id: int
    quantity: int
    unit_price: Decimal
    tax_percent: Decimal = Decimal("0.12")


class InvoiceOut(Schema):
    """Schema respuesta factura."""
    id: int
    number: str
    date: date
    customer: "CustomerMini"  # Forward ref
    total: Decimal
    sri_status: str

    class Config:
        from_attributes = True  # Usa model.__dict__ (como ORM mode)


class CustomerMini(Schema):
    id: int
    name: str
    identification: str
```

---

## 🔄 Comparación DRF vs Ninja

### **Serializer (DRF):**

```python
class InvoiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Invoice
        fields = ["id", "number", "total"]

    def create(self, validated_data):
        company = self.context["request"].active_company
        return Invoice.objects.create(company=company, **validated_data)
```

### **Schema + View (Ninja):**

```python
class InvoiceCreate(Schema):
    customer_id: int

@router.post("/")
def create_invoice(request, data: InvoiceCreate):
    company = request.active_company
    invoice = Invoice.objects.create(
        company=company,
        customer_id=data.customer_id
    )
    return {"id": invoice.id}
```

**Ahorro:** ~50% menos código por endpoint.

---

## 🧪 Testing APIs

```python
from ninja.testing import TestClient

def test_create_invoice(api_client, company, customer):
    payload = {
        "customer_id": customer.id,
        "lines": [
            {"product_id": 1, "quantity": 2, "unit_price": 100}
        ]
    }
    response = api_client.post("/facturacion_ec/invoices/", payload)
    assert response.status_code == 200
    assert response.json()["id"] is not None
```

---

## 📖 OpenAPI Docs

**Auto-generado:**
- http://localhost:8000/api/v1/docs/ — Swagger UI
- http://localhost:8000/api/v1/schema/ — OpenAPI JSON

**Customizar:**

```python
# erp_nexus/api/v1/__init__.py
from ninja import NinjaAPI

api = NinjaAPI(
    title="ERP Nexus API",
    version="1.0.0",
    description="API REST para ERP Nexus",
    docs_url="/docs/",
)

# Añadir routers
api.add_router("/facturacion_ec/", facturacion_router)
```

---

## ⚠️ Límites de Django Ninja

| Límite | Solución |
|--------|----------|
| File uploads | Usar `File` type + `request.FILES` |
| Bulk operations | Crear endpoint específico |
| Custom validators | Usar `@validator` en Schema o `def clean()` |
| Nested writes | `Schema` con `create()` custom |

---

## 🔮 Futuro

**v1.x:** Migrar todo a Django Ninja (actualmente híbrido DRF+Ninja)  
**v2.0:** Considerar FastAPI si need extreme performance (pero perderíamos Django ORM)

---

**Documentación:** https://django-ninja.rest-framework.com/
