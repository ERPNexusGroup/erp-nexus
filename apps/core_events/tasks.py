"""
Tareas Celery para procesamiento async de eventos.
Solo se usan en production cuando Celery está activo.
"""
import logging

logger = logging.getLogger(__name__)

try:
    from celery import shared_task

    @shared_task(bind=True, max_retries=3)
    def process_event(self, event_id: str):
        """Procesa un evento de forma asíncrona."""
        from .models import EventLog
        from .bus import EventBus

        try:
            event = EventLog.objects.get(id=event_id)
            EventBus._process_sync(event)
        except EventLog.DoesNotExist:
            logger.warning(f"Event {event_id} not found")
        except Exception as exc:
            logger.error(f"Error processing event {event_id}: {exc}")
            self.retry(countdown=60, exc=exc)

except ImportError:
    # Celery no instalado — las tasks no existen
    pass
