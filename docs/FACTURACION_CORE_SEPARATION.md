# Arquitectura de Facturación — Separación Core/SRI

## Visión General

La separación sigue el principio de **dependencia inversa**: el plugin SRI Ecuador depende del core local, nunca al revés.

```
┌──────────────────────────────────────────────────────────┐
│  modules/facturacion_ec (Plugin SRI Ecuador)            │
│  • InvoiceSRIExtension (OneToOne → facturacion.Invoice) │
│  • Catálogos SRI (SriTipoComprobante, SriAmbiente, ...) │
│  • Servicios SRI (XML, firma digital, cliente SOAP)     │
│  • API endpoints SRI-specific (/facturacion_ec/)        │
└───────────────▲──────────────────────▲──────────────────┘
                │ uses                  │ depends on
                │ string ref            │ OneToOne FK
                │                       │
┌───────────────▼──────────────────────▼──────────────────┐
│  apps/facturacion (Core Local — agnóstico de SRI)      │
│  • Customer (con related_name 'facturacion_customers') │
│  • Invoice (con related_name 'facturacion_invoices')   │
│  • InvoiceLine (con related_name 'facturacion_lines')  │
│  • Signals: auto-numbering Invoice, Quote sequencer   │
│  • API core: /api/v1/facturacion/ (customers, invoices)│
│  • Admin core integrado                                │
└──────────────────────────────────────────────────────────┘
```

## Separación de Capas

### Capa 1: Core Local (`apps.facturacion`)

**Responsabilidad:** Gestionar el ciclo de vida de documentos tributarios de forma genérica (sin knowing SRI Ecuador).

**Modelos:**
- `Customer`: datos fiscales del cliente (RUC, cédula, razón social)
- `Invoice`: encabezado factura (number, date, totals, status)
- `InvoiceLine`: líneas detalle (product, quantity, prices, taxes)

**Características:**
- No conoce XML, firma digital, claves de acceso SRI
- `related_name`s únicos: `facturacion_customers`, `facturacion_invoices`, `facturacion_lines`
- Signals: `auto_number_invoice` (genera número secuencial), `calculate_invoice_totals` (recalcula totals)
- API REST con Django Ninja: create/list/retrieve customers e invoices

### Capa 2: Plugin SRI (`modules.facturacion_ec`)

**Responsabilidad:** Extender el core con capacidades específicas del SRI Ecuador.

**Modelos:**
- `InvoiceSRIExtension`: extensión OneToOne a `facturacion.Invoice`
  - `ambiente` (1=Pruebas, 2=Producción)
  - `tipo_comprobante` → `SriTipoComprobante`
  - `access_key` (clave acceso SRI 49 dígitos)
  - `sri_status` (draft, pending, sent, accepted, rejected, cancelled)
  - `xml_content`, `sri_xml_autorizado`, `sri_message`
- `SriTipoComprobante`: catálogo (01=Factura, 04=Nota de crédito, ...)
- `SriAmbiente`: ambiente SRI (1, 2)
- `SriImpuesto`: catálogo impuestos (IVA 12%, ICE, ...)
- `SRISendLog`: log de envíos (request/response XML, código respuesta)
- `CompanyLicense`: licencia por compañía (límite facturas/mes)

**Servicios:**
- `xml_generator.py`: genera XML factura según XSD SRI
- `digital_signature.py`: firma XML con certificado `.p12`
- `sri_client.py`: cliente SOAP para envío/recepción SRI
- `code_unique.py`: generador claves acceso (49 dígitos)
- `validator.py`: validación previa XSD/RUC
- `facturation_integration.py`: orquestador `send_invoice_to_sri(invoice_id)`

**API:**
- `GET /api/v1/facturacion_ec/invoices/` — listar extensiones SRI
- `POST /api/v1/facturacion_ec/invoices/{id}/send_to_sri/` — enviar factura
- `GET /api/v1/facturacion_ec/invoices/{id}/status/` — consultar estado
- `GET /api/v1/facturacion_ec/invoices/{id}/xml` — descargar XML firmado
- `POST /api/v1/facturacion_ec/invoices/{id}/resend` — reenviar rechazada

## Relaciones y Dependencias

### Diagrama de Dependency Graph

```
core_companies.Company
         │
         ├───► facturacion.Customer (FK company, related_name='facturacion_customers')
         │
         ├───► inventory.Product (FK company, omitido)
         │
         └───► facturacion.Invoice
                 ├─── FK customer → facturacion.Customer
                 │        (related_name='facturacion_invoices')
                 ├─── FK created_by → auth.User
                 │        (related_name='facturas_created_facturacion')
                 ├─── OneToOne ← facturacion_ec.InvoiceSRIExtension
                 │        (model='facturacion.Invoice', related_name='sri_extension')
                 └───► facturacion.InvoiceLine (FK invoice)
                          (related_name='facturacion_lines')
                          └─── FK product → inventory.Product
                                   (related_name='facturacion_invoice_lines')
```

**Notas:**
- `InvoiceSRIExtension` usa referencia string `'facturacion.Invoice'` → evita import circular
- `facturacion` no importa nada de `facturacion_ec`
- `sales` puede importar `facturacion.Customer` sin problemas

### Esquema de Tablas (DDL simplificado)

```sql
-- Core facturación
CREATE TABLE facturacion_customer (
    id BIGSERIAL PRIMARY KEY,
    company_id INTEGER NOT NULL REFERENCES core_companies_company(id),
    identification_type CHAR(5) DEFAULT '05',
    identification_number VARCHAR(20) NOT NULL,
    name VARCHAR(200) NOT NULL,
    email VARCHAR(254), phone VARCHAR(50),
    address TEXT,
    razon_social VARCHAR(200),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(company_id, identification_type, identification_number),
    INDEX idx_fact_customer_ident(identification_number),
    INDEX idx_fact_customer_co_active(company_id, is_active)
);

CREATE TABLE facturacion_invoice (
    id BIGSERIAL PRIMARY KEY,
    company_id INTEGER NOT NULL REFERENCES core_companies_company(id),
    customer_id INTEGER NOT NULL REFERENCES facturacion_customer(id),
    created_by_id INTEGER NOT NULL REFERENCES auth_user(id),
    number VARCHAR(30) UNIQUE,
    date DATE DEFAULT CURRENT_DATE,
    subtotal NUMERIC(15,2) DEFAULT 0,
    tax_total NUMERIC(15,2) DEFAULT 0,
    total NUMERIC(15,2) DEFAULT 0,
    status VARCHAR(20) DEFAULT 'draft',
    notes TEXT DEFAULT '',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    INDEX idx_fact_invoice_co_date(company_id, date),
    INDEX idx_fact_invoice_status(status)
);

CREATE TABLE facturacion_invoiceline (
    id BIGSERIAL PRIMARY KEY,
    invoice_id INTEGER NOT NULL REFERENCES facturacion_invoice(id) ON DELETE CASCADE,
    product_id INTEGER NOT NULL REFERENCES inventory_product(id),
    description VARCHAR(200),
    quantity NUMERIC(10,4) DEFAULT 1,
    unit_price NUMERIC(10,2),
    unit_discount NUMERIC(10,2) DEFAULT 0,
    subtotal NUMERIC(12,2),
    tax_rate NUMERIC(5,2) DEFAULT 12.00,
    tax_amount NUMERIC(12,2) DEFAULT 0,
    discount NUMERIC(12,2) DEFAULT 0,
    total NUMERIC(12,2),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    INDEX idx_fact_line_invoice(invoice_id)
);

-- Plugin SRI Ecuador
CREATE TABLE facturacion_ec_invoicesriextension (
    id BIGSERIAL PRIMARY KEY,
    invoice_id INTEGER UNIQUE NOT NULL REFERENCES facturacion_invoice(id) ON DELETE CASCADE,
    ambiente INTEGER DEFAULT 1,
    tipocomprobante_id INTEGER NULL REFERENCES facturacion_ec_sritipocomprobante(id),
    access_key VARCHAR(50) UNIQUE,
    sri_status VARCHAR(20) DEFAULT 'pending',
    sri_message TEXT,
    sri_xml_autorizado TEXT,
    sri_authorization_date TIMESTAMP WITH TIME ZONE,
    xml_content TEXT,
    xml_original_hash VARCHAR(128),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    INDEX facturacion_sri_sta_992769_idx(sri_status),
    INDEX facturacion_access__17b2dc_idx(access_key)
);

CREATE TABLE facturacion_ec_sritisendlog (
    id BIGSERIAL PRIMARY KEY,
    invoice_extension_id INTEGER NOT NULL REFERENCES facturacion_ec_invoicesriextension(id) ON DELETE CASCADE,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    endpoint VARCHAR(200),
    request_xml TEXT,
    response_xml TEXT,
    response_code VARCHAR(20),
    success BOOLEAN DEFAULT FALSE,
    error_message TEXT,
    INDEX (invoice_extension_id)
);

CREATE TABLE facturacion_ec_companylicense (
    id BIGSERIAL PRIMARY KEY,
    company_id INTEGER NOT NULL REFERENCES core_companies_company(id),
    license_type_id INTEGER NOT NULL REFERENCES facturacion_ec_sritipocomprobante(id),
    activated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE,
    is_active BOOLEAN DEFAULT TRUE,
    is_trial BOOLEAN DEFAULT FALSE,
    invoices_this_month INTEGER DEFAULT 0,
    current_month_year VARCHAR(7),
    UNIQUE(company_id, license_type_id),
    INDEX facturacion_company_716ecd_idx(company_id, is_active)
);
```

## Decisions Técnicas

### 1. `related_name` Prefijados

**Problema:** Django no permite `related_name` duplicados en el proyecto. Si `sales` y `facturacion_ec` ambos definen `related_name='invoices'` en un FK a `Customer`, colisiona.

**Solución:** Prefijo por app:
- `facturacion.Customer.company` → `related_name='facturacion_customers'`
- `facturacion.Invoice.company` → `related_name='facturacion_invoices'`
- `facturacion.Invoice.customer` → `related_name='facturacion_invoices'`
- `facturacion.Invoice.created_by` → `related_name='facturas_created_facturacion'`
- `facturacion.InvoiceLine.invoice` → `related_name='facturacion_lines'`
- `facturacion.InvoiceLine.product` → `related_name='facturacion_invoice_lines'`
- `facturacion_ec.InvoiceSRIExtension.invoice` → `related_name='sri_extension'` (único en plugin)

### 2. String References para Evitar Import Circular

`facturacion_ec/models.py` usa:
```python
invoice = models.OneToOneField(
    'facturacion.Invoice',  # ← string reference
    on_delete=models.CASCADE,
    related_name='sri_extension'
)
```

Esto permite que `facturacion_ec` se importe sin necesidad de importar `facturacion.models` (que a su vez puede importar `facturacion_ec` indirectamente).

### 3. Dependencias de Migraciones

```
core_companies.0001_initial
facturacion.0001_initial
    └── facturacion_ec.0001_initial (depende de ambas)
sales.0001_initial
    └── facturacion.0001_initial  (ya actualizado)
```

### 4. API con Django Ninja

El core facturación expone su propia API REST independiente (`apps/facturacion/api/routes.py`), integrada en `apps/core_api/v1/facturacion.py` y montada en `/api/v1/facturacion/`.

El plugin SRI expone su API en `modules/facturacion_ec/api/routes.py`, integrado en `apps/core_api/v1/facturacion_ec.py` y montado en `/api/v1/facturacion_ec/`.

### 5. Signals Conservados

- `facturacion.signals.auto_number_invoice`: asigna `Invoice.number` secuencial (ej: 001-001-000000042) al crear factura.
- `facturacion.signals.calculate_invoice_totals`: recalcula `subtotal`, `tax_total`, `total` al save de Invoice o InvoiceLine.

## Rollout & Migración de Datos

### Comando `migrate_facturacion_ec_data`

Copiado a `facturacion_ec/management/commands/migrate_facturacion_ec_data.py`. Lee datos legacy (si existen en el esquema antiguo) y los migra a las nuevas tablas core + extensión.

**Uso:**
```bash
# Dry-run: solo reportar
uv run python manage.py migrate_facturacion_ec_data --dry-run

# Migración real para compañía específica
uv run python manage.py migrate_facturacion_ec_data --company-id 1 --batch-size 100

# Migrar todas las compañías
uv run python manage.py migrate_facturacion_ec_data --all
```

### Validación Post-Migración

```bash
# Contar facturas por compañía
uv run python manage.py shell -c "
from apps.facturacion.models import Invoice
from modules.facturacion_ec.models import InvoiceSRIExtension
print('Facturas core:', Invoice.objects.count())
print('Facturas con extensión SRI:', InvoiceSRIExtension.objects.count())
assert Invoice.objects.count() == InvoiceSRIExtension.objects.count(), '¡Faltan extensiones!'
"
```

## Troubleshooting

| Síntoma | Causa probable | Solución |
|---------|---------------|----------|
| `ImportError: cannot import name 'facturacion' from partially initialized module` | Import circular | Usar `apps.get_model('facturacion', 'Invoice')` o string references |
| `related_name collision: Reverse accessor for 'facturacion.Invoice.company' clashes` | `related_name` duplicado | Prefijar con nombre de app (facturacion_) |
| `ValueError: Indexes passed to ModelState require a name` | Índices sin nombre en migración | Agregar `name='idx_<app>_<fields>'` en `models.Index` |
| `LookupError: App 'facturacion_ec' not installed` | `facturacion_ec` no en INSTALLED_APPS | Agregar a `erp_nexus/modules_enabled.py` → `MODULE_APPS` |

## Referencias

- `apps/facturacion/models.py` — modelos core
- `modules/facturacion_ec/models.py` — modelos plugin
- `apps/core_api/v1/facturacion.py` — API core
- `modules/facturacion_ec/api/routes.py` — API plugin
- `PLAN_FACTURACION_CORE_SEPARATION.md` — plan detallado
