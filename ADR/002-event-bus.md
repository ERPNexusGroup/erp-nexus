# ADR-002: Event Bus como Medio de Comunicación Entre Módulos

**Estado:** ✅ Aceptado  
**Fecha:** 2026-05-10  
**Contexto:** Fase 0 — Diseño de acoplamiento  
**Decisores:** Walter Cun, ERP Nexus Team

---

## 📋 Contexto

Los módulos de ERP Nexus deben estar **desacoplados**. Si `facturacion_ec` crea una factura, `inventory` debe actualizar stock. ¿Cómo lo hacemos?

**Opción A: Imports directos**  
```python
# facturacion_ec/views.py
from inventory.models import Product
Product.update_stock(...)  # ❌ Acoplamiento fuerte
```

**Opción B: Django Signals**  
```python
invoice_created.send(sender=..., invoice=inv)
# inventory escucha signal
@receiver(invoice_created)
def update_stock(sender, invoice, **kw): ...
```

**Opción C: Event Bus propio**  
```python
EventBus.emit("invoice.created", payload={...})
# inventory subscribe en su init
```

---

## 🎯 Decisión

**Elegimos Opción C: Event Bus propio (basado en Django signals internamente)**

Implementamos `apps.core_events.bus.EventBus` como wrapper de Django signals, con:

1. **Persistencia:** Eventos guardados en DB (`EventLog`)
2. **Retry automático:** Si handler falla, se reintenta
3. **Suscripciones declarativas:** Configurable vía `__meta__.py` o settings
4. **Dashboard:** Ver eventos en admin o API

---

## 🏗️ Diseño

### **EventLog model:**

```python
class EventLog(models.Model):
    event_type = models.CharField(max_length=100)
    source = models.CharField(max_length=50)  # Módulo emisor
    payload = models.JSONField()
    metadata = models.JSONField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    processed = models.BooleanField(default=False)
    error_message = models.TextField(blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["event_type", "-created_at"]),
            models.Index(fields=["processed"]),
        ]
```

### **EventBus API:**

```python
class EventBus:
    @staticmethod
    def emit(event_type: str, source: str, payload: dict, metadata: dict = None):
        """Emitir evento (async o sync)."""
        # 1. Guardar en EventLog
        event = EventLog.objects.create(...)

        # 2. Buscar suscripciones activas
        subs = EventSubscription.objects.filter(event_type=event_type, active=True)

        # 3. Ejecutar handlers (sync o async via Celery)
        for sub in subs:
            try:
                sub.invoke(payload)
                event.processed = True
            except Exception as exc:
                logger.error(f"Handler failed: {exc}")

    @staticmethod
    def subscribe(event_type: str, subscriber_module: str, handler_path: str):
        """Registrar suscripción."""
        EventSubscription.objects.get_or_create(
            event_type=event_type,
            subscriber_module=subscriber_module,
            defaults={"handler_path": handler_path, "active": True}
        )
```

---

## 📡 Eventos Predefinidos

### **Facturación (`facturacion_ec` emite):**

| Evento | Payload | Quién escucha |
|--------|---------|---------------|
| `invoice.created` | `{invoice_id, total, company_id}` | `inventory` (reservar stock), `accounting` (crear asiento) |
| `invoice.sent` | `{invoice_id, access_key}` | `email` (enviar copia) |
| `invoice.accepted` | `{invoice_id, authorization_date}` | `accounting` (contabilizar) |
| `invoice.rejected` | `{invoice_id, errors}` | `notifications` (alertar usuario) |

### **Inventario (`inventory` emite):**

| Evento | Payload | Quién escucha |
|--------|---------|---------------|
| `stock.movement` | `{product_id, delta, reason}` | `facturacion_ec` (validar stock antes facturar) |
| `stock.critical` | `{product_id, current_stock}` | `notifications` (alertar reabastecimiento) |

---

## ✅ Ventajas

| Ventaja | Explicación |
|---------|-------------|
| **Desacoplado** | Módulo A no conoce Módulo B |
| **Extensible** | Cualquiera puede subscribirse |
| **Auditable** | EventLog → trazabilidad completa |
| **Recoverable** | Si handler falla, se reintenta |
| **Observable** | Dashboard de eventos en tiempo real |

---

## ⚠️ Trade-offs

| Trade-off | Decisión |
|-----------|----------|
| **Latencia** | Sync por defecto. Async (Celery) opcional |
| **Complexity** | EventLog + retry logic añade código |
| **Ordering** | Events per type se procesan FIFO |
| **Idempotency** | Handlers deben ser idempotentes |

---

## 🔄 Comparación con Alternativas

| Aspecto | Event Bus (elegido) | Django Signals | Direct Imports |
|---------|-------------------|----------------|----------------|
| Decoupling | ✅ Alto | ✅ Alto | ❌ Bajo |
| Persistencia | ✅ Sí | ❌ No | ❌ No |
| Retry | ✅ Sí | ❌ No | ❌ No |
| Visibility | ✅ Dashboard | ❌ No | ❌ No |
| Simplicidad | ⚠️ Media | ✅ Alta | ✅ Alta |

**Conclusión:** Event Bus es el balance correcto entre poder y simplicidad.

---

## 🧪 Requisitos No-Funcionales

- **Performance:** < 5ms por emit (sync, sin celery)
- **Throughput:** 1000 eventos/segundo (suficiente para 100 facturas/seg)
- **Durability:** Eventos persistidos (si celery worker cae, no se pierden)
- **Duplicados:** Handler debe ser idempotente (no asumir exactly-once)

---

## 📝 Ejemplo Práctico

```python
# facturacion_ec/services/invoice_service.py
def create_invoice(...):
    invoice = Invoice.objects.create(...)

    # 1. Emitir evento
    EventBus.emit(
        event_type="invoice.created",
        source="facturacion_ec",
        payload={
            "invoice_id": invoice.id,
            "company_id": invoice.company_id,
            "total": str(invoice.total),
        }
    )

    return invoice
```

```python
# inventory/events/handlers.py
def on_invoice_created(payload: dict):
    """Cuando se crea factura, verificar stock."""
    from inventory.models import StockMovement

    invoice_id = payload["invoice_id"]
    # Buscar líneas de la factura
    lines = InvoiceLine.objects.filter(invoice_id=invoice_id)
    for line in lines:
        StockMovement.objects.create(
            product=line.product,
            delta=-line.quantity,
            reason=f"Factura {invoice_id}"
        )

# En inventory/__init__.py o signals.py
EventBus.subscribe(
    event_type="invoice.created",
    subscriber_module="inventory",
    handler_path="inventory.events.handlers.on_invoice_created"
)
```

---

## 🔮 Futuro

**v1.1:** Async events via Celery  
**v1.2:** Event schemas (JSON Schema validation)  
**v1.3:** Webhooks externos (POST a URLs externas)

---

**Siguiente:** ADR-003 — Multi-Company Strategy
