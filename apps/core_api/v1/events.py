"""
Router de eventos — endpoints para el Event Bus.
"""
from ninja import Router, Schema
from typing import Optional
from datetime import datetime

from apps.core_events.models import EventLog

router = Router()


class EventOut(Schema):
    id: str
    event_type: str
    source_module: str
    payload: dict
    processed: bool
    processed_at: Optional[datetime]
    error_message: str
    created_at: datetime


class EventStats(Schema):
    total: int
    pending: int
    failed: int


@router.get("/", response=list[EventOut])
def list_events(request, event_type: str = None, limit: int = 50):
    """Lista eventos del Event Bus."""
    qs = EventLog.objects.all()
    if event_type:
        qs = qs.filter(event_type=event_type)
    return list(qs[:limit])


@router.get("/stats", response=EventStats)
def event_stats(request):
    """Estadísticas del Event Bus."""
    qs = EventLog.objects.all()
    return {
        "total": qs.count(),
        "pending": qs.filter(processed=False).count(),
        "failed": qs.filter(error_message__gt="").count(),
    }


@router.post("/emit", response=EventOut)
def emit_event(request, event_type: str, source: str, payload: dict = None):
    """Emite un evento al bus (para testing/debugging)."""
    from apps.core_events.bus import EventBus
    event = EventBus.emit(event_type, source, payload or {})
    return event
