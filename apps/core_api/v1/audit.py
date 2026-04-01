"""
Router de audit — endpoints para consultar logs de auditoría.
Protegido con JWT Auth.
"""
from ninja import Router, Schema
from typing import Optional, List
from datetime import datetime

from apps.core_api.auth import JWTAuth
from apps.core_audit.models import AuditLog

router = Router(auth=JWTAuth())


class AuditLogOut(Schema):
    id: str
    username: str
    action: str
    resource_type: str
    resource_id: str
    description: str
    ip_address: Optional[str]
    company_name: str
    created_at: datetime


class AuditStats(Schema):
    total: int
    today: int
    last_7_days: int
    by_action: dict


@router.get("/", response=List[AuditLogOut])
def list_logs(
    request,
    action: str = None,
    user: str = None,
    resource_type: str = None,
    limit: int = 50,
):
    """Lista logs de auditoría con filtros opcionales."""
    qs = AuditLog.objects.all()

    if action:
        qs = qs.filter(action=action)
    if user:
        qs = qs.filter(username__icontains=user)
    if resource_type:
        qs = qs.filter(resource_type=resource_type)

    logs = qs[:limit]
    return [
        AuditLogOut(
            id=str(log.id),
            username=log.username,
            action=log.action,
            resource_type=log.resource_type,
            resource_id=log.resource_id,
            description=log.description,
            ip_address=log.ip_address,
            company_name=log.company_name,
            created_at=log.created_at,
        )
        for log in logs
    ]


@router.get("/stats", response=AuditStats)
def audit_stats(request):
    """Estadísticas de auditoría."""
    from django.utils import timezone
    from datetime import timedelta
    from django.db.models import Count

    now = timezone.now()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    week_ago = now - timedelta(days=7)

    qs = AuditLog.objects.all()

    by_action = dict(
        qs.filter(created_at__gte=week_ago)
        .values_list("action")
        .annotate(count=Count("id"))
        .values_list("action", "count")
    )

    return AuditStats(
        total=qs.count(),
        today=qs.filter(created_at__gte=today_start).count(),
        last_7_days=qs.filter(created_at__gte=week_ago).count(),
        by_action=by_action,
    )
