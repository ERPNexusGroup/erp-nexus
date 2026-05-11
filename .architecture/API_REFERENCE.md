# 📡 API Reference — ERP Nexus

**Versión API:** v1  
**Base URL:** `/api/v1/`  
**Formato:** JSON  
**Auth:** JWT (Bearer token) o Session Auth (admin)

---

## 🔐 Autenticación

### **Session Auth (_admin panel_)**

```python
# Acceso desde Django admin o browser
# Session cookie automática
GET /api/v1/modules/
```

### **JWT Token (_API externa_)**

```bash
# 1. Obtener token
POST /api/v1/auth/token/
Content-Type: application/json

{
  "username": "admin@local",
  "password": "tu-contraseña"
}

# Respuesta:
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGciOi...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOi..."
}
```

```bash
# 2. Usar token
GET /api/v1/modules/
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOi...
```

---

## 🏠 Core Endpoints

### **Health Check**

```http
GET /api/health
```

**Respuesta:**
```json
{
  "status": "ok",
  "version": "0.5.0",
  "database": "ok",
  "cache": "ok"
}
```

---

### **Modules (Marketplace)**

#### Listar módulos

```http
GET /api/v1/modules/
```

**Respuesta:**
```json
[
  {
    "technical_name": "facturacion",
    "name": "Facturación Ecuador",
    "version": "0.1.0",
    "active": true,
    "installed_at": "2026-05-10T10:00:00Z"
  }
]
```

#### Detalle de módulo

```http
GET /api/v1/modules/{technical_name}/
```

**Respuesta:**
```json
{
  "technical_name": "facturacion",
  "name": "Facturación Ecuador",
  "version": "0.1.0",
  "description": "Facturación electrónica SRI Ecuador",
  "active": true,
  "settings": {
    "FACTURACION_EC_AMBIENTE": 1,
    "FACTURACION_EC_AUTO_SEND": false
  }
}
```

#### Habilitar/deshabilitar módulo

```http
POST /api/v1/modules/{technical_name}/enable/
POST /api/v1/modules/{technical_name}/disable/
```

**Respuesta:**
```json
{
  "status": "ok",
  "active": true
}
```

---

### **Events (Event Bus)**

#### Listar eventos

```http
GET /api/v1/events/?limit=50&offset=0
```

**Respuesta:**
```json
{
  "count": 150,
  "results": [
    {
      "id": 1,
      "event_type": "invoice.created",
      "source": "facturacion",
      "payload": {
        "invoice_id": 42,
        "total": "150.00"
      },
      "created_at": "2026-05-10T12:00:00Z",
      "processed": true
    }
  ]
}
```

#### Emitir evento (debug)

```http
POST /api/v1/events/emit/
Content-Type: application/json

{
  "event_type": "test.event",
  "source": "manual",
  "payload": {"foo": "bar"}
}
```

#### Estadísticas de eventos

```http
GET /api/v1/events/stats/
```

**Respuesta:**
```json
{
  "total_events": 1240,
  "pending": 0,
  "failed": 3,
  "by_type": {
    "invoice.created": 500,
    "payment.received": 400,
    "customer.created": 340
  }
}
```

---

## 🧾 Módulo facturacion

### **Invoices (Facturas)**

#### Listar facturas

```http
GET /api/v1/facturacion/invoices/?status=pending&limit=20
```

**Query params:**
- `status` — `draft` | `pending` | `sent` | `accepted` | `rejected`
- `date_from` — fecha inicio (YYYY-MM-DD)
- `date_to` — fecha fin (YYYY-MM-DD)
- `customer_id` — filtrar por cliente
- `limit` — máximo 100
- `offset` — paginación

**Respuesta:**
```json
[
  {
    "id": 1,
    "number": "001-001-000000042",
    "date": "2026-05-10",
    "customer": {
      "id": 5,
      "name": "Cliente Demo",
      "identification": "1791234567001"
    },
    "subtotal": "200.00",
    "tax_total": "24.00",
    "total": "224.00",
    "sri_status": "pending",
    "ambiente": 1,
    "access_key": "2026051000001000000000000423456789"
  }
]
```

#### Crear factura

```http
POST /api/v1/facturacion/invoices/
Content-Type: application/json

{
  "customer_id": 5,
  "date": "2026-05-10",
  "lines": [
    {
      "product_id": 1,
      "quantity": 2,
      "unit_price": 100.00,
      "tax_percent": 12
    },
    {
      "product_id": 2,
      "quantity": 1,
      "unit_price": 50.00,
      "tax_percent": 0
    }
  ]
}
```

**Respuesta (201 Created):**
```json
{
  "id": 42,
  "number": "001-001-000000042",
  "access_key": "2026051000001000000000000423456789",
  "total": "224.00",
  "sri_status": "pending"
}
```

**Errores:**
```json
{
  "error": "Cliente no encontrado"
}  // 404

{
  "error": "Stock insuficiente para producto X"
}  // 400
```

#### Detalle factura

```http
GET /api/v1/facturacion/invoices/{id}/
```

**Respuesta:**
```json
{
  "id": 42,
  "number": "001-001-000000042",
  "date": "2026-05-10",
  "customer": {...},
  "lines": [
    {
      "id": 1,
      "product": {"id": 1, "name": "Producto A"},
      "quantity": 2,
      "unit_price": "100.00",
      "subtotal": "200.00",
      "tax_amount": "24.00"
    }
  ],
  "subtotal": "200.00",
  "tax_total": "24.00",
  "total": "224.00",
  "sri_status": "pending",
  "xml_content": null,
  "created_at": "2026-05-10T10:30:00Z"
}
```

#### Descargar XML

```http
GET /api/v1/facturacion/invoices/{id}/xml/
```

**Respuesta:**
```http
Content-Type: application/xml
Content-Disposition: attachment; filename="factura_001-001-000000042.xml"

<?xml version="1.0" encoding="UTF-8"?>
<factura ...>
  ...
</factura>
```

#### Enviar a SRI (manual)

```http
POST /api/v1/facturacion/invoices/{id}/send/
```

**Respuesta:**
```json
{
  "success": true,
  "sri_status": "accepted",
  "message": "Factura enviada y aceptada por SRI"
}
```

---

### **Customers (Clientes)**

#### Listar clientes

```http
GET /api/v1/facturacion/customers/?identification=1791234567001
```

**Respuesta:**
```json
[
  {
    "id": 5,
    "identification_type": "05",
    "identification_number": "1791234567001",
    "name": "Cliente Demo",
    "email": "cliente@demo.com",
    "phone": "0991234567",
    "address": "Calle Principal 123, Guayaquil"
  }
]
```

#### Crear cliente

```http
POST /api/v1/facturacion/customers/
Content-Type: application/json

{
  "identification_type": "05",
  "identification_number": "1791234567001",
  "name": "Walter Cun",
  "email": "walter@email.com",
  "phone": "0991234567",
  "address": "Guayaquil, Ecuador"
}
```

**Respuesta (201):**
```json
{
  "id": 6,
  "identification_number": "1791234567001",
  "name": "Walter Cun"
}
```

---

### **Products (Productos)**

```http
GET /api/v1/facturacion/products/

POST /api/v1/facturacion/products/
{
  "name": "Producto A",
  "sku": "PROD-001",
  "description": "Descripción",
  "unit_price": 100.00,
  "tax_percent": 12
}
```

---

## 🔢 Códigos SRI

### **Tipos de identificación:**

| Código | Descripción |
|--------|-------------|
| `05` | Cédula (ecuatoriano) |
| `06` | RUC |
| `04` | Pasaporte |
| `03` | RUC extranjero |

### **Tipos de comprobante:**

| Código | Descripción |
|--------|-------------|
| `01` | Factura |
| `04` | Nota de crédito |
| `05` | Nota de débito |
| `06` | Guía de remisión |

### **Ambiente SRI:**

| Código | Descripción |
|--------|-------------|
| `1` | Pruebas (sandbox) |
| `2` | Producción |

---

## 💡 Ejemplos de Uso

### **Python (requests):**

```python
import requests
from requests.auth import HTTPBasicAuth

BASE = "http://localhost:8000/api/v1"

# Auth
resp = requests.post(
    f"{BASE}/auth/token/",
    json={"username": "admin", "password": "admin123"}
)
token = resp.json()["access"]
headers = {"Authorization": f"Bearer {token}"}

# Crear factura
payload = {
    "customer_id": 5,
    "lines": [
        {"product_id": 1, "quantity": 2, "unit_price": 100}
    ]
}
resp = requests.post(
    f"{BASE}/facturacion/invoices/",
    json=payload,
    headers=headers
)
invoice = resp.json()
print(f"Factura {invoice['number']} creada")
```

### **cURL:**

```bash
# Login
TOKEN=$(curl -s -X POST http://localhost:8000/api/v1/auth/token/ \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin"}' | jq -r .access)

# Crear factura
curl -X POST http://localhost:8000/api/v1/facturacion/invoices/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"customer_id":5,"lines":[{"product_id":1,"quantity":2}]}'
```

### **JavaScript (fetch):**

```javascript
const BASE = "http://localhost:8000/api/v1";

async function login() {
  const resp = await fetch(`${BASE}/auth/token/`, {
    method: "POST",
    headers: {"Content-Type": "application/json"},
    body: JSON.stringify({username: "admin", password: "admin123"})
  });
  const data = await resp.json();
  return data.access;
}

async function createInvoice(token) {
  const resp = await fetch(`${BASE}/facturacion/invoices/`, {
    method: "POST",
    headers: {
      "Authorization": `Bearer ${token}`,
      "Content-Type": "application/json"
    },
    body: JSON.stringify({
      customer_id: 5,
      lines: [{product_id: 1, quantity: 2, unit_price: 100}]
    })
  });
  return resp.json();
}
```

---

## 📦 Inventory API

**Base:** `/api/v1/inventory/`

### GET /api/v1/inventory/products/
Lista todos los productos.

**Respuesta:**
```json
[
  {
    "id": 1,
    "sku": "PROD-001",
    "name": "Producto A",
    "category": "Electrónica",
    "stock_quantity": 50.0,
    "unit_price": "100.00",
    "is_low_stock": false
  }
]
```

### GET /api/v1/inventory/stock-movements/
Lista movimientos de inventario.

### POST /api/v1/inventory/stock-movements/
Registra movimiento (entrada/salida/ajuste). Automáticamente actualiza stock del producto.

---

## 🛒 Sales API

**Base:** `/api/v1/sales/`

### Quotes

`GET /api/v1/sales/quotes/` — Lista cotizaciones
`GET /api/v1/sales/quotes/{id}/` — Detalle con líneas
`POST /api/v1/sales/quotes/` — Crear cotización
```json
{
  "quote_number": "Q-001",
  "customer_id": 5,
  "expiry_date": "2026-05-20",
  "lines": [
    {"product_id": 1, "quantity": 2, "unit_price": 100}
  ]
}
```
`POST /api/v1/sales/quotes/{id}/accept/` — Aceptar cotización
`POST /api/v1/sales/quotes/{id}/reject/` — Rechazar cotización

### Orders

`GET /api/v1/sales/orders/` — Lista órdenes
`POST /api/v1/sales/orders/` — Crear orden
`POST /api/v1/sales/orders/{id}/confirm/` — Confirmar (verifica stock, reserva)
`POST /api/v1/sales/orders/{id}/invoice/` — Convertir orden en factura (llama a facturacion)

---

## 🛒 Purchases API

**Base:** `/api/v1/purchases/`

### Suppliers

`GET /api/v1/purchases/suppliers/` — Lista proveedores

### Purchase Orders

`GET /api/v1/purchases/purchase-orders/` — Lista OC
`POST /api/v1/purchases/purchase-orders/` — Crear OC
```json
{
  "po_number": "PO-001",
  "supplier_id": 3,
  "expected_delivery": "2026-05-25",
  "lines": [
    {"product_id": 1, "quantity_ordered": 100, "unit_price": 80}
  ]
}
```
`POST /api/v1/purchases/purchase-orders/{id}/send/` — Marcar como enviada
`POST /api/v1/purchases/purchase-orders/{id}/receive/` — Registrar recepción
```json
{ "lines": [{"line_id": 1, "quantity_received": 50}] }
```
Actualiza stock en inventory automaticamente.

---

## 🔔 Notifications API

**Base:** `/api/v1/notifications/`

### Inbox (usuario actual)

`GET /api/v1/notifications/inbox/` — Notificaciones no leídas
`POST /api/v1/notifications/inbox/{nid}/read/` — Marcar como leída

### Queue

`POST /api/v1/notifications/send/` — Encolar notificación
```json
{
  "type": "email",
  "recipient": "cliente@example.com",
  "title": "Factura creada",
  "message": "Su factura #001-001-000000001 está lista",
  "template": "invoice_created"
}
```
`GET /api/v1/notifications/templates/` — Lista plantillas disponibles

---

## 🖨️ Print Manager API

**Base:** `/api/v1/print/`

`GET /api/v1/print/templates/` — Plantillas activas
`POST /api/v1/print/render/` — Renderizar PDF (genera PrintJob)
```json
{
  "template_key": "invoice",
  "context": {
    "invoice": {"number": "001-001", "total": 224},
    "company": {"name": "Mi Empresa"}
  },
  "filename": "factura_001.pdf"
}
```
`GET /api/v1/print/jobs/{id}/` — Consultar estado del job

---

## 🐛 Códigos de Error

| Código | Descripción |
|--------|-------------|
| `400` | Bad Request — datos inválidos |
| `401` | Unauthorized — token inválido/missing |
| `403` | Forbidden — sin permisos |
| `404` | Not Found |
| `409` | Conflict — duplicado (ej: número factura) |
| `422` | Validation Error — validación de negocio fallida |
| `500` | Internal Server Error |

---

## 📊 Paginación

```http
GET /api/v1/facturacion/invoices/?limit=20&offset=40
```

**Respuesta:**
```json
{
  "count": 150,
  "next": "http://localhost:8000/api/v1/facturacion/invoices/?limit=20&offset=60",
  "previous": "http://localhost:8000/api/v1/facturacion/invoices/?limit=20&offset=20",
  "results": [...]
}
```

---

## 🔄 Webhooks (futuro)

```http
POST /api/v1/webhooks/invoice/
```

**Payload:**
```json
{
  "event": "invoice.created",
  "timestamp": "2026-05-10T12:00:00Z",
  "data": {
    "invoice_id": 42,
    "total": 224.00
  }
}
```

---

**API completa documentada en:** `/api/v1/docs/` (Swagger UI)  
**Ejecutando server:** http://localhost:8000
