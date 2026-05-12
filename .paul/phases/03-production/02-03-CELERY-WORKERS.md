# M3 Phase 2.3 — Celery Workers (Async Tasks)

**Fecha:** 2026-05-11
**Estado:** PLAN PENDING → APPLY NEXT
**Estimado:** 6h

## Objetivo
Sistema de colas asíncronas con Celery + Redis para:
- SRI auto-send (facturación electrónica Ecuador)
- Notificaciones push/email
- Reportes pesados (PDF, Excel generación)
- Webhooks de integración (GitHub, proveedores)
- Tareas periódicas (crontab-style) — backups, sync

## Entregables

### 1. Configuración Celery (`erp_nexus/celery.py`)
```python
import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'erp_nexus.settings')

app = Celery('erp_nexus')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()
```

### 2. Settings Celery (`erp_nexus/settings/development.py` + prod)
```python
# Redis como broker y result backend
CELERY_BROKER_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
CELERY_RESULT_BACKEND = CELERY_BROKER_URL
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TASK_TRACK_STARTED = True
CELERY_TASK_TIME_LIMIT = 300  # 5 minutos max por tarea
CELERY_WORKER_MAX_TASKS_PER_CHILD = 1000  # prevent memory leaks

# Colas (queues) por tipo de tarea
CELERY_TASK_QUEUES = {
    'default': {'exchange': 'default', 'routing_key': 'default'},
    'sri': {'exchange': 'sri', 'routing_key': 'sri.#', 'priority': 0},
    'notifications': {'exchange': 'notifications', 'routing_key': 'notifications.#', 'priority': 1},
    'reports': {'exchange': 'reports', 'routing_key': 'reports.#', 'priority': 5},
    'webhooks': {'exchange': 'webhooks', 'routing_key': 'webhooks.#', 'priority': 3},
}
CELERY_TASK_DEFAULT_QUEUE = 'default'
CELERY_TASK_DEFAULT_EXCHANGE = 'default'
CELERY_TASK_DEFAULT_ROUTING_KEY = 'default'
```

### 3. Tareas Base (`apps/core_notifications/tasks.py` o `apps/core_marketplace/tasks.py`)
```python
from celery import shared_task
from django.core.mail import send_mail

@shared_task(queue='notifications', bind=True, max_retries=3)
def send_email_task(self, subject, message, recipient_list):
    """Tarea asíncrona para envío de emails."""
    try:
        send_mail(subject, message, None, recipient_list, fail_silently=False)
    except Exception as exc:
        raise self.retry(exc=exc, countdown=60)

@shared_task(queue='sri', bind=True, max_retries=3)
def send_invoice_to_sri_task(self, invoice_id):
    """Auto-envía factura al SRI (Ecuador)."""
    from apps.facturacion.models import Invoice
    invoice = Invoice.objects.get(id=invoice_id)
    # Lógica de envío a SRI...
    invoice.sri_status = 'sent'
    invoice.save()
```

### 4. Docker Compose — Agregar Worker Service
```yaml
  worker:
    build:
      context: .
      dockerfile: Dockerfile.prod
    command: celery -A erp_nexus worker --loglevel=info --queues=default,sri,notifications,reports,webhooks
    depends_on:
      - db
      - redis
      - web
    env_file:
      - .env.prod
    volumes:
      - logs:/app/logs
    networks:
      - erp_nexus_net
    restart: unless-stopped

  beat:
    build:
      context: .
      dockerfile: Dockerfile.prod
    command: celery -A erp_nexus beat --loglevel=info
    depends_on:
      - db
      - redis
      - worker
    env_file:
      - .env.prod
    volumes:
      - logs:/app/logs
    networks:
      - erp_nexus_net
    restart: unless-stopped
```

### 5. Django Admin — Celery Task Monitor
- Modelo `AsyncTask` (log de tareas, status, resultado)
- Admin view para ver tareas en cola, failures
- Botón "Retry failed"

### 6. Monitoreo Básico
- Flower (opcional) o simple endpoint `/celery/stats/`
- Logs de worker en `/app/logs/worker.log`

### 7. Tests
- Test que tareas encolan correctamente
- Test retry mechanism
- Test queue priorities

## Tareas

| # | Tarea | Estimado | Estado |
|---|-------|----------|--------|
| 2.3.1 | Crear `erp_nexus/celery.py` + settings | 1h | ⏳ |
| 2.3.2 | Agregar `celery` y `redis` a `pyproject.toml` | 0.5h | ⏳ |
| 2.3.3 | Definir colas (queues) y prioridades | 0.5h | ⏳ |
| 2.3.4 | Crear tareas base (notifications, sri, reports) | 2h | ⏳ |
| 2.3.5 | Docker-compose: servicios `worker` y `beat` | 1h | ⏳ |
| 2.3.6 | Admin UI para monitoreo de tareas | 1.5h | ⏳ |
| 2.3.7 | Tests de integración Celery | 1.5h | ⏳ |
| 2.3.8 | Documentación (`docs/CELERY.md`) | 0.5h | ⏳ |

**Total:** ~8h

## Criterios de Éxito
- [ ] Worker `celery` arranca y consume colas
- [ ] Tareas encoladas desde Django se ejecutan
- [ ] SRI auto-send funciona asíncronamente
- [ ] Retries en fallos (max 3)
- [ ] Beat schedule para tareas periódicas (backup diario)
- [ ] Logs de worker accesibles
- [ ] Admin puede ver estado de tareas

## Dependencias
- Phase 2.1 (Docker) ✅
- Phase 2.2 (Redis configurado) ✅
- Django apps: facturacion, notifications, core_marketplace

## Riesgos
- Deadlocks en DB: usar `transaction.on_commit` para encolar tareas post-commit
- Memory leaks en workers: `max_tasks_per_child`
- Tareas largas bloqueando cola: prioridades por queue

## Notas
- Usar `celery -A erp_nexus worker --pool=solo` en desarrollo (evita prefork issues en WSL)
- En producción: `--pool=threads` o `prefork` según carga
- Flower para UI: `celery -A erp_nexus flower` (port 5555)
