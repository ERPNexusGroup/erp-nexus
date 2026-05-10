# ADR-003: Multi-Company (Multi-Tenant) Strategy

**Estado:** ✅ Aceptado  
**Fecha:** 2026-05-10  
**Contexto:** Fase 0 — Diseño de aislamiento de datos  
**Decisores:** Walter Cun, ERP Nexus Team

---

## 📋 Contexto

ERP Nexus debe soportar **múltiples empresas** en una misma instalación:

- Empresa A → Ve solo sus clientes, facturas, productos
- Empresa B → Ve solo sus datos
- Admin super → Ve todas (opcional)

**Problema:** ¿Cómo aislar datos por empresa?

### **Opción A: Separate databases**

| Empresa | DB |
|---------|----|
| Empresa A | `erp_nexus_company_a` |
| Empresa B | `erp_nexus_company_b` |

**Pros:**
- Aislamiento total
- Backup/restore por empresa fácil
- Performance (índices por DB)

**Contras:**
- Migraciones múltiples (100 empresas = 100 DBs)
- Reporting agregado complejo (UNION ALL)
- Schema migrations por DB individually

### **Opción B: Row-level security (PostgreSQL RLS)**

**Pros:**
- Una sola DB
- Aislamiento a nivel DB

**Contras:**
- Solo PostgreSQL
- Complejo de configurar
- Django ORM no soporta RLS nativamente

### **Opción C: CompanyId en cada tabla (Elegido)**

Todos los modelos tienen `company = ForeignKey(Company)`.

```python
class Invoice(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    number = models.CharField(...)
    # ...
```

**Query:**
```python
Invoice.objects.filter(company=request.active_company)
```

---

## 🎯 Decisión

**Elegimos Opción C: CompanyId column + Middleware**

Cada modelo incluye `company` como ForeignKey obligatorio. Un middleware (`ActiveCompanyMiddleware`) setea `request.active_company` basado en:

1. **Header HTTP** `X-Company-ID` (para APIs)
2. **Subdominio** `companyA.erp.com` (futuro)
3. **Session** (para admin Django)

---

## 🏗️ Implementación

### **Company model:**

```python
# core_companies/models.py
class Company(models.Model):
    name = models.CharField(max_length=200)
    tax_id = models.CharField(max_length=20, unique=True)  # RUC
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name
```

### **Base model (abstract):**

```python
class CompanyBoundModel(models.Model):
    """Base para TODOS los modelos con company."""
    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name="%(class)ss"
    )

    class Meta:
        abstract = True
```

Uso:
```python
class Customer(CompanyBoundModel):
    name = models.CharField(...)
    # company heredado automáticamente
```

### **ActiveCompanyMiddleware:**

```python
# core_companies/middleware.py
class ActiveCompanyMiddleware:
    """Set request.active_company desde header/session/subdomain."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        company_id = self._resolve_company_id(request)
        if company_id:
            request.active_company = Company.objects.get(id=company_id)
        else:
            request.active_company = None

        response = self.get_response(request)
        return response

    def _resolve_company_id(self, request):
        # 1. Header X-Company-ID (API)
        company_id = request.headers.get("X-Company-ID")
        if company_id:
            return company_id

        # 2. Session (admin)
        if hasattr(request, "user") and request.user.is_authenticated:
            return request.session.get("active_company_id")

        # 3. Subdomain (futuro)
        # host = request.get_host().split(".")[0]
        # return Company.objects.filter(slug=host).first()

        return None
```

### **Middleware order:**

```python
# settings.py
MIDDLEWARE = [
    "django.contrib.sessions.middleware.SessionMiddleware",
    "apps.core_companies.middleware.ActiveCompanyMiddleware",  # ← Aquí
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    ...
]
```

**Importante:** `ActiveCompanyMiddleware` va DESPUÉS de `SessionMiddleware` y ANTES de `AuthenticationMiddleware` para tener `request.session` disponible pero después de auth para opcionalmente filtrar por user permissions.

---

## 🔐 QuerySet Managers

### **CompanyQuerySet:**

```python
class CompanyQuerySet(models.QuerySet):
    def for_company(self, company):
        return self.filter(company=company)

    def by_user(self, user):
        """Devuelve objetos que el user puede ver."""
        if user.is_superuser:
            return self.all()
        return self.filter(company=user.active_company)
```

Uso:
```python
# En lugar de: Invoice.objects.filter(company=request.active_company)
Invoice.objects.for_company(request.active_company)
```

---

## 🧪 Tests Multi-Company

```python
@pytest.mark.django_db
class TestMultiCompany:
    def test_isolation(self, company_factory):
        """Data de company A no es visible para B."""
        company_a = company_factory()
        company_b = company_factory()

        Invoice.objects.create(company=company_a, number="001-001-1")
        Invoice.objects.create(company=company_b, number="001-002-1")

        assert Invoice.objects.for_company(company_a).count() == 1
        assert Invoice.objects.for_company(company_b).count() == 1

    def test_cross_company_access_forbidden(self, api_client):
        """API no expone datos de otras companies."""
        company_a = company_factory()
        company_b = company_factory()

        inv = Invoice.objects.create(company=company_a, number="001-001-1")

        # Intentar acceder desde company_b
        api_client.active_company = company_b
        resp = api_client.get(f"/api/v1/facturacion_ec/invoices/{inv.id}/")
        assert resp.status_code == 404  # No encontrado para company_b
```

---

## ⚠️ Reglas de Oro

1. **TODOS los modelos** que tienen datos de negocio → heredan de `CompanyBoundModel` o tienen `company` FK
2. **TODAS las queries** → `.for_company(request.active_company)` o `filter(company=...)`
3. **Admin Django** → `get_queryset()` filtra por company
4. **API endpoints** → validan `request.active_company` existe
5. **Never** `Model.objects.all()` sin filter de company en código de producción

---

## 📊 Comparación con Otras Estrategias

| Estrategia | Costo DB | Query complexity | Multi-db | Django friendly |
|------------|----------|------------------|----------|-----------------|
| **CompanyId column** | ✅ Bajo (index) | ✅ `filter(company=...)` | ❌ No | ✅ Nativo |
| **Separate DBs** | ❌ Alto (N DBs) | ✅ `using('db_a')` | ✅ Sí | ⚠️ Router complejo |
| **PostgreSQL RLS** | ✅ Bajo | ✅ Sin filtro (RLS自动) | ❌ No | ❌ Django no soporta |
| **Schema per tenant** | ⚠️ Medio | ✅ `search_path` | ❌ No | ⚠️ Django no soporta |

---

## 🚨 Problemas y Soluciones

| Problema | Solución |
|----------|----------|
| `company` es NULL en datos legacy | Migration para populate + NOT NULL constraint |
| Superuser ve todas las companies | QuerySet manager `by_user(user)` |
| Cross-company leak | Code review + test obligatorio para cada query |
| Company delete → orphan data | `on_delete=CASCADE` en todos los FKs |

---

## 📈 Escalabilidad

**1000 empresas × 1M facturas c/u = 1B rows**

Índices requeridos:
```sql
CREATE INDEX idx_invoice_company_date ON facturacion_ec_invoice(company_id, date);
CREATE INDEX idx_customer_company_id ON facturacion_ec_customer(company_id);
```

**Particionado por company_id** (PostgreSQL):
```sql
CREATE TABLE invoice_company_1 PARTITION OF invoice FOR VALUES WITH (MODULUS 10, REMAINDER 1);
```

---

**Siguiente ADR:** ADR-004 — Marketplace Module Installation Flow
