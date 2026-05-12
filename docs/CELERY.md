# 🐘 Celery Workers — ERP Nexus

**Guía de tareas asíncronas con Celery + Redis**
**Versión:** 1.0.0
**Fecha:** 2026-05-11

---

## 📋 Visión General

Celery maneja tareas pesadas o de larga duración fuera del request/response HTTP:

| Queue | Prioridad | Casos de uso |
|-------|-----------|--------------|
| `sri` | 0 (alta) | Envío facturas SRI (Ecuador), time-sensitive |
| `notifications` | 1 | Emails, push notifications |
| `webhooks` | 3 | Integraciones externas (GitHub, proveedores) |
| `default` | 5 | Tareas generales |
| `reports` | 9 (baja) | Generación PDF/Excel (resource-heavy) |

---

## 🔧 Configuración

### Settings

```python
# erp_nexus/settings/base.py  (colas, serializers, timeouts)
# erp_nexus/settings/production.py (broker URL, eager=False)

CELERY_BROKER_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")
CELERY_RESULT_BACKEND = CELERY_BROKER_URL
CELERY_TASK_ALWAYS_EAGER = False  # production
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TASK_TIME_LIMIT = 300
CELERY_WORKER_MAX_TASKS_PER_CHILD = 1000
```

### Docker Compose Services

```yaml
services:
  worker:
    command: celery -A erp_nexus worker --loglevel=info --queues=default,sri,notifications,reports,webhooks
    depends_on: [db, redis, web]

  beat:
    command: celery -A erp_nexus beat --loglevel=info
    depends_on: [db, redis, worker]
```

---

## 📝 Escribiendo Tareas

### Tarea Básica

```python
from celery import shared_task

@shared_task(queue='default')
def my_task(x, y):
    return x + y

# Encolar
my_task.delay(2, 3)
```

### Tarea con Retry

```python
@shared_task(queue='notifications', bind=True, max_retries=3, default_retry_delay=60)
def send_email_task(self, subject, message, recipient_list):
    try:
        send_mail(subject, message, None, recipient_list)
    except Exception as exc:
        raise self.retry(exc=exc, countdown=60)
```

### Tarea con Argumentos Complejos

```python
@shared_task(queue='reports', bind=True, max_retries=2)
def generate_pdf_report(self, report_id: int, filters: dict):
    from apps.reports.models import Report
    report = Report.objects.get(id=report_id)
    # Generación pesada...
    report.pdf_path = generate_pdf(report, filters)
    report.save()
    return {"status": "done", "path": report.pdf_path}
```

---

## 🕐 Periodic Tasks (Celery Beat)

Define tareas programadas en `erp_nexus/celery.py` o `apps/core_notifications/tasks.py`:

```python
from celery.schedules import crontab

app.conf.beat_schedule = {
    'cleanup-sessions-every-midnight': {
        'task': 'apps.core_notifications.tasks.cleanup_old_sessions',
        'schedule': crontab(hour=0, minute=0),
    },
    'refresh-cache-every-hour': {
        'task': 'apps.core_marketplace.tasks.refresh_marketplace_cache',
        'schedule': crontab(minute=0),  # cada hora
    },
    'daily-backup': {
        'task': 'scripts.backup_dispatch',  # si decides encolar backup
        'schedule': crontab(hour=2, minute=0),  # 2 AM
    },
}
```

---

## 🧪 Testing Celery

En desarrollo (`development.py`), Celery corre en modo **eager** (síncrono, sin broker):

```python
CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True
```

Esto significa `my_task.delay()` ejecuta la función inmediatamente. No requiere worker en tests unitarios.

Para tests de integración con worker real, usa `celery_worker` fixture (pytest-celery) o levanta worker en Docker.

### Tests unitarios (mock)

```python
from unittest.mock import patch

@patch('apps.core_notifications.tasks.send_email_task.delay')
def test_trigger_email(mock_delay):
    # ... tu código que encola tarea
    mock_delay.assert_called_once()
```

---

## 📊 Monitoreo

### Logs

```bash
# Ver logs del worker
docker compose logs -f worker

# Ver logs de beat
docker compose logs -f beat
```

### Flower (UI opcional)

```bash
# Instalar flower: pip install flower
docker compose exec worker celery -A erp_nexus flower --port=5555
# Acceder: http://localhost:5555
```

### Métricas Básicas

```python
from celery import current_app
inspector = current_app.control.inspect()
active = inspector.active()      # tareas activas
scheduled = inspector.scheduled() # tareas programadas
```

---

## ⚠️ Buenas Prácticas

1. **Idempotencia:** Tareas deben ser seguras ante re-ejecución (retry)
2. **Timeout:** `CELERY_TASK_TIME_LIMIT=300` evita tareas colgadas
3. **Memory leaks:** `CELERY_WORKER_MAX_TASKS_PER_CHILD=1000` recarga worker
4. **Prioridades:** Usa colas separadas para no bloquear tareas urgentes
5. **DB transactions:** Encoder tareas **después** de `transaction.on_commit()` para evitar race conditions
6. **Result backend:** Solo guarda resultados si los necesitas; si no, usa `CELERY_TASK_IGNORE_RESULT=True`

---

## 🔄 Comandos Útiles

```bash
# Ver colas activas
celery -A erp_nexus inspect active

# Ver tareas programadas
celery -A erp_nexus inspect scheduled

# Revocar tarea (si está pendiente)
celery -A erp_nexus control revoke <task-id>

# Purge cola (¡cuidado!)
celery -A erp_nexus purge -f default
```

---

## 🐛 Troubleshooting

| Síntoma | Causa probable | Solución |
|---------|----------------|----------|
| Worker no arranca | Redis no disponible | `docker compose ps redis` |
| Tareas no se ejecutan | Queue mismatch | Verificar `--queues` en worker command |
| Memory leak | Max tasks per child muy alto | Bajar a `500` o `100` |
| Deadlock DB | Tarea dentro de transacción | Usar `transaction.on_commit(encolar_tarea)` |
| Retry infinito | Exception no manejada | Capturar excepciones específicas |

---

## 📚 Referencias

- [Celery Documentation](https://docs.celeryproject.org/)
- [Django + Celery Guide](https://docs.celeryproject.org/en/stable/django/first-steps-with-django.html)
- [Redis as Broker](https://docs.celeryproject.org/en/stable/getting-started/backends-and-brokers/redis.html)
