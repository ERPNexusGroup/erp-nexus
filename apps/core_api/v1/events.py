"""
Router de eventos — endpoints para el Event Bus.
Protegido con JWT Auth.
"""
from ninja import Router, Schema
from typing import Optional
from datetime import datetime

from apps.core_events.models import EventLog
from apps.core_api.auth import JWTAuth

router = Router(auth=JWTAuth())


class EventOut(Schema):
    id: str
    event_type: str
    source_module: str
    payload: dict
    processed: bool
    processed_at: Optional[datetime]
    error_message: str
    created_at: datetime

    @staticmethod
    def resolve_id(obj):
        return str(obj.id)


class EventStats(Schema):
    total: int
    pending: int
    failed: int


class EmitRequest(Schema):
    event_type: str
    source: str
    payload: dict = {}


class EmitResponse(Schema):
    id: str
    event_type: str
    processed: bool

    @staticmethod
    def resolve_id(obj):
        return str(obj.id)


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


@router.post("/emit", response=EmitResponse)
def emit_event(request, data: EmitRequest):
    """Emite un evento al bus."""
    from apps.core_events.bus import EventBus
    event = EventBus.emit(data.event_type, data.source, data.payload)
    return event
