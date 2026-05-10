"""
API endpoints para el módulo notifications.
"""
from ninja import Router
from django.db import transaction

from ..models import Notification, NotificationTemplate, NotificationQueue

router = Router(tags=["Notificaciones"])


@router.get("/inbox/")
def list_inbox(request):
    """Notificaciones del usuario actual."""
    user = request.user
    notifications = Notification.objects.filter(user=user).order_by("-created_at")[:50]
    return [
        {
            "id": n.id,
            "type": n.notification_type,
            "title": n.title,
            "message": n.message,
            "is_read": n.is_read,
            "created_at": n.created_at,
        }
        for n in notifications
    ]


@router.post("/inbox/{nid}/read/")
def mark_read(request, nid: int):
    """Marca notificación como leída."""
    Notification.objects.filter(id=nid, user=request.user).update(is_read=True)
    return {"status": "ok"}


@router.post("/send/")
def queue_notification(request):
    """
    Encola una notificación para envío asincrónico.
    Body: { "type": "email"|"telegram", "recipient": "...", "title": "...", "message": "...", "template": "name" }
    """
    data = request.json
    item = NotificationQueue.objects.create(
        notification_type=data["type"],
        recipient=data["recipient"],
        title=data.get("title", ""),
        message=data["message"],
        template_id=data.get("template"),
        context=data.get("context", {}),
    )
    return {"queue_id": item.id, "status": "queued"}


@router.get("/templates/")
def list_templates(request):
    """Lista plantillas disponibles."""
    templates = NotificationTemplate.objects.all()
    return [
        {
            "id": t.id,
            "name": t.name,
            "type": t.notification_type,
            "subject": t.subject,
        }
        for t in templates
    ]
