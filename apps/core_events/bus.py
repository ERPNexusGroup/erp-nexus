"""
EventBus — API principal para emitir y suscribir eventos.

Uso:
    from apps.core_events.bus import EventBus

    # Emitir evento
    EventBus.emit("invoice.created", "invoicing", {"invoice_id": 123})

    # Suscribir handler
    EventBus.subscribe("invoice.created", "accounting", "accounting.events.on_invoice_created")
"""
import importlib
import logging
from typing import Callable, Optional

from django.utils import timezone

logger = logging.getLogger(__name__)

# Registro en memoria de handlers suscritos
_subscribers: dict[str, list[dict]] = {}


class EventBus:
    """
    Bus de eventos desacoplado para comunicación entre módulos.
    """

    @staticmethod
    def emit(
        event_type: str,
        source: str,
        payload: dict,
        async_process: bool = False,
    ) -> "EventLog":
        """
        Emite un evento al bus.

        Args:
            event_type: Tipo de evento ('invoice.created')
            source: Módulo que emite ('invoicing')
            payload: Datos del evento
            async_process: Si True, procesa via Celery (production)
        """
        from .models import EventLog

        event = EventLog.objects.create(
            event_type=event_type,
            source_module=source,
            payload=payload,
        )

        logger.info(f"Event emitted: {event_type} from {source}")

        if async_process:
            try:
                from .tasks import process_event
                process_event.delay(str(event.id))
            except Exception:
                # Fallback a sync si Celery no está disponible
                EventBus._process_sync(event)
        else:
            EventBus._process_sync(event)

        return event

    @staticmethod
    def _process_sync(event: "EventLog"):
        """Procesa un evento de forma síncrona."""
        from .models import EventSubscription

        # Buscar suscriptores en DB
        subscriptions = EventSubscription.objects.filter(
            event_type=event.event_type,
            active=True,
        )

        for sub in subscriptions:
            try:
                handler = _import_handler(sub.handler_path)
                if handler:
                    handler(event.payload)
                    logger.debug(f"Handler {sub.handler_path} processed {event.event_type}")
            except Exception as e:
                logger.error(f"Handler {sub.handler_path} failed for {event.event_type}: {e}")
                event.mark_failed(str(e))

        # Procesar handlers registrados en memoria
        handlers = _subscribers.get(event.event_type, [])
        for entry in handlers:
            try:
                entry["handler"](event.payload)
            except Exception as e:
                logger.error(f"Memory handler failed for {event.event_type}: {e}")

        event.mark_processed()

    @staticmethod
    def subscribe(
        event_type: str,
        subscriber_module: str,
        handler_path: str,
    ):
        """
        Suscribe un módulo a un tipo de evento.

        Args:
            event_type: Tipo de evento a escuchar
            subscriber_module: Nombre del módulo suscrito
            handler_path: Ruta al handler ('module.events.handle_event')
        """
        from .models import EventSubscription

        EventSubscription.objects.update_or_create(
            event_type=event_type,
            subscriber_module=subscriber_module,
            defaults={
                "handler_path": handler_path,
                "active": True,
            },
        )

    @staticmethod
    def subscribe_handler(event_type: str, handler: Callable):
        """
        Suscribe un handler directamente (en memoria, sin DB).
        Útil para handlers del core que siempre están activos.
        """
        if event_type not in _subscribers:
            _subscribers[event_type] = []
        _subscribers[event_type].append({"handler": handler})

    @staticmethod
    def get_event_history(
        event_type: Optional[str] = None,
        source: Optional[str] = None,
        limit: int = 100,
    ) -> list:
        """Obtiene historial de eventos con filtros opcionales."""
        from .models import EventLog

        qs = EventLog.objects.all()
        if event_type:
            qs = qs.filter(event_type=event_type)
        if source:
            qs = qs.filter(source_module=source)
        return list(qs[:limit])

    @staticmethod
    def get_stats() -> dict:
        """Estadísticas del bus de eventos."""
        from .models import EventLog, EventSubscription

        return {
            "total_events": EventLog.objects.count(),
            "pending_events": EventLog.objects.filter(processed=False).count(),
            "failed_events": EventLog.objects.filter(error_message__gt="").count(),
            "subscriptions": EventSubscription.objects.filter(active=True).count(),
        }


def _import_handler(handler_path: str) -> Optional[Callable]:
    """Importa un handler desde su ruta dotted path."""
    try:
        module_path, func_name = handler_path.rsplit(".", 1)
        module = importlib.import_module(module_path)
        return getattr(module, func_name)
    except (ValueError, ImportError, AttributeError) as e:
        logger.error(f"Cannot import handler {handler_path}: {e}")
        return None
