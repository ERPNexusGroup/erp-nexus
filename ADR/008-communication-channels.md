# ADR 008 — Comunicación: REST vs Event Bus vs GraphQL vs gRPC

**Fecha:** 2026-05-10  
**Estado:** Accepted  
**Autor:** Arquitecto ERP Nexus  
**Stakeholders:** Walter (product owner), dev team

---

## **Contexto**

ERP Nexus necesita definir **cómo se comunican** sus componentes internos (módulos) y externos (clientes, microservicios). Hay 4 mecanismos posibles:

1. **REST API** — Request/response síncrono
2. **Event Bus** — Pub/sub asíncrono (event-driven)
3. **GraphQL** — Single endpoint, cliente solicita exacto lo que necesita
4. **gRPC** — RPC binario de alto performance

Se debe definir **cuándo usar cada uno** para evitar mixed messages y sobre-ingeniería.

---

## **Decisión**

### **1. REST API — Pilar principal (90% de los casos)**

**Uso:** Cualquier operación que sea:
- CRUD estándar (create/read/update/delete)
- Peticiones desde frontend/web/mobile
- Integración con sistemas externos (clientes, proveedores)
- Operaciones síncronas que requieren respuesta inmediata

**Ejemplos:**
```http
POST   /api/v1/facturacion/invoices/           # Crear factura (directo)
GET    /api/v1/inventory/stock/                # Consultar stock
PATCH  /api/v1/sales/orders/123/               # Actualizar orden
DELETE /api/v1/purchases/orders/456/           # Cancelar OC
```

**HttpClient usage:**
```python
# modules que DEPENDEN de otros modules (acoplamiento directo):
facturacion → inventory (stock deduction al facturar)
sales → facturacion (generate invoice from order)
purchases → inventory (receive goods, add stock)
```

**Razón:** Simplicidad. REST es universal, cacheable, fácil de debug, bien documentado. Django Ninja lo provee out-of-the-box.

---

### **2. Event Bus — Comunicación loose-coupling (10% de casos)**

**Uso:** Cuando un módulo **emite un evento** y **múltiples módulos independientes** lo escuchan:

**Ejemplos:**
```python
# Facturación emite (no sabe quién escucha):
EventBus.publish("invoice.created", {
    "invoice_id": 123,
    "customer_id": 456,
    "total": 1500.00
})

# Inventory escucha (dependencia en tiempo de ejecución, no compile-time):
@EventBus.subscribe("invoice.created")
def deduct_stock(event):
    # Auto-deducir inventario
    pass

# Notifications escucha:
@EventBus.subscribe("invoice.created")
def send_invoice_email(event):
    # Enviar email al cliente
    pass

# Audit escucha:
@EventBus.subscribe("invoice.created")
def log_audit(event):
    # Registrar en audit log
    pass
```

**Ventajas:**
- ✅ **Loose coupling:** Facturación no necesita importar inventory, notifications, audit
- ✅ **Extensible:** Nuevos listeners se agregan sin modificar emisor
- ✅ **Async/Background:** Los listeners pueden ejecutar en colas (Celery)
- ✅ **Audit + Notifications** sin tocar código de negocio

**Desventajas:**
- ❌ Difícil de debug (flujo no lineal)
- ❌ No hay return value (fire-and-forget)

**Razón:** Para side-effects (notify, audit, analytics), no para operaciones core.

---

### **3. GraphQL — Capa de agregación para CLIENTES (futuro)**

**Uso:** Solamente cuando el **frontend cliente** (dashboard SPA, mobile app, desktop app) necesita:
- Múltiples recursos en una sola petición (ej: dashboard con KPI de facturación + inventario + ventas)
- Evitar N+1 REST calls
- Filtros dinámicos, paginación, campos específicos

**NO usar para:**
- ❌ Comunicación módulo → módulo (REST o Event Bus)
- ❌ Integraciones externas (REST más estándar)
- ❌ Simple CRUD (REST es más simple)

**Ejemplo (futuro):**
```graphql
query Dashboard($dateFrom: Date!, $dateTo: Date!) {
  invoices: facturacion_invoices(dateFrom: $dateFrom, dateTo: $dateTo) {
    totalCount
    totalAmount
    byStatus { label count }
  }
  inventory: inventory_items(lowStockOnly: true) {
    id name currentStock minStock
  }
  sales: sales_orders(status: "pending") {
    id customer total
  }
}
```

**Una llamada GraphQL** reemplaza **3-4 llamadas REST** separadas.

**Implementación:** Crear plugin `core_graphql` (separado del core). Solo activar cuando haya 2+ clientes frontend que lo justifiquen.

---

### **4. gRPC — Solo para microservicios externos (futuro lejano)**

**Uso:** Cuando ERP Nexus se descompone en **microservicios independientes** (cada módulo como servicio separado):

```
┌─────────────┐         gRPC         ┌─────────────┐
│  Frontend   │◄─────────────────────►│ API Gateway │
└─────────────┘                       └──────▲──────┘
                                            │ REST
                                 ┌──────────┴──────────┐
                                 │                     │
                    ┌────────────▼─────┐   ┌─────────▼──────┐
                    │  Facturación Srv │   │ Inventory Srv  │
                    │   (gRPC:50051)   │   │  (gRPC:50052)  │
                    └──────────────────┘   └────────────────┘
```

**NO usar para:**
- ❌ Módulos dentro del mismo repo (usar REST directo o Event Bus)
- ❌ Frontend/mobile (GraphQL o REST)
- ❌ Integraciones simples (REST)

**Razón:** gRPC requiere contrato `.proto`, codegen, balanceo de carga, service mesh. Overkill para monorepo.

---

## **Consecuencias**

### **Estructura de comunicación:**

```
┌─────────────────────────────────────────────────────────────┐
│                    ERP Nexus (Monorepo)                    │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Facturación ──REST──► Inventario  (dependencia directa)  │
│         │                                          │       │
│         │ Event Bus                                │ REST  │
│         ▼                                          ▼       │
│    Notifications                              Frontend      │
│         │                                          │       │
│         └──────────Event Bus──────────────────────┘       │
│                                                             │
│  [Frontend] ──REST/GraphQL──► API Layer (Django Ninja)    │
│                                                             │
│  [Mobile/Desktop] ──gRPC────► External Microservices ◄───┐│
│                              (futuro, si split)           ││
└─────────────────────────────────────────────────────────────┘│
                                                              │
  [External Systems] ──REST──► REST API (estándar) ◄─────────┘
```

### **Regla de oro:**

| ¿Quién habla con quién? | Mecanismo | Razón |
|--------------------------|-----------|-------|
| Módulo A → Módulo B (dependencia directa) | REST call | Synchronous, needs result |
| Módulo A → "alguien escucha" (side-effect) | Event Bus | Loose coupling, async |
| Frontend/API client → ERP | REST (hoy) / GraphQL (futuro) | Cliente consume datos |
| ERP → Microservicio externo | gRPC | High-throughput, binary protocol |
| Microservicio externo → ERP | REST/Webhook | External systems usually REST |

---

## **Alternativas Consideradas**

### **A. GraphQL para todo (rejected)**
GraphQL para módulo→módulo sería sobrekill. Cada módulo tendría que exponer schema GraphQL. Complejidad innecesaria. REST es suficiente para CRUD interno.

### **B. Event Bus para todo (rejected)**
Todo vía eventos haría el sistema imposible de debug. No habría return values. Operaciones transaccionales (facturar + descontar stock) necesitan acoplamiento.

### **C. gRPC para módulos internos (rejected)**
gRPC dentro de monorepo es innecesario. No hay need de protocolos binarios cuando están en mismo proceso/DB.

---

## **Riesgos**

| Riesgo | Mitigación |
|--------|------------|
| Overuse de Event Bus (todo via eventos) | Code review: ¿Este evento necesita consumidores múltiples? Si no, usa REST |
| Underuse de Event Bus (módulos acoplados) | Linter rule: No imports cross-module directos (excepto facturacion→inventory que es dependencia secuencial válida) |
| GraphQL implementado demasiado temprano | Solo considerar cuando frontend complejo lo justifique (2+ pantallas con N+1 problem) |
| gRPC implementado por "es más rápido" | No implementar hasta split a microservicios (no planeado) |

---

## **Timeline de Implementación**

| Fase | Canales activos |
|------|-----------------|
| **0.6 — 1.0 (MVP)** | REST + Event Bus (solo para audit/notifications) |
| **1.1 — 1.5 (Growth)** | REST + Event Bus (ampliado aInventory, Sales) |
| **2.0+ (Scale)** | Evaluar GraphQL si Frontend complejo lo requiere |
| **Futuro (split)** | Evaluar gRPC si microservicios (no planeado) |

---

## **Related**

- `ADR/007-hybrid-architecture.md` — Hybrid repo structure
- `ARCHITECTURE_HYBRID.md` — Guía arquitectónica
- `MODULE_SPEC.md` — Contratos entre módulos (REST endpoints)
- `docs/DEVELOPMENT.md` — Código de experiencia
