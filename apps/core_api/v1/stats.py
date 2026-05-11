"""
Router de estadísticas — métricas de instalación y uso.
"""
from ninja import Router, Schema
from typing import Dict, List, Any

from apps.core_api.auth import JWTAuth
from apps.core_stats.models import UsageMetric, Installation

router = Router(auth=JWTAuth())


class DashboardStats(Schema):
    total_users: int
    total_companies: int
    total_modules: int
    active_modules: int
    api_requests_today: int
    logins_today: int


class UsageStats(Schema):
    metrics: Dict[str, List[Dict[str, Any]]]


@router.get("/dashboard", response=DashboardStats)
def dashboard(request):
    """Estadísticas principales del dashboard."""
    from django.contrib.auth import get_user_model
    from apps.core_companies.models import Company
    from apps.core_marketplace.models import ModuleCatalogItem
    from django.utils import timezone

    User = get_user_model()
    today = timezone.now().date()

    return DashboardStats(
        total_users=User.objects.count(),
        total_companies=Company.objects.count(),
        total_modules=ModuleCatalogItem.objects.count(),
        active_modules=ModuleCatalogItem.objects.filter(is_active=True).count(),
        api_requests_today=UsageMetric.objects.filter(
            date=today, metric_type="api_requests"
        ).values_list("value", flat=True).first() or 0,
        logins_today=UsageMetric.objects.filter(
            date=today, metric_type="logins"
        ).values_list("value", flat=True).first() or 0,
    )


@router.get("/usage", response=UsageStats)
def usage(request, days: int = 30):
    """Métricas de uso de los últimos N días."""
    return UsageStats(metrics=UsageMetric.get_daily_stats(days=days))


@router.get("/system")
def system_info(request):
    """Información del sistema."""
    import sys
    from django.conf import settings

    return {
        "python_version": sys.version,
        "django_version": getattr(__import__("django"), "VERSION", (0, 0, 0)),
        "debug": settings.DEBUG,
        "database": settings.DATABASES["default"]["ENGINE"].split(".")[-1],
        "installed_apps": len(settings.INSTALLED_APPS),
        "modules_dir": str(getattr(settings, "MODULES_DIR", "")),
    }
