"""
Context processor optimizado para dashboard admin.

Usa cache para evitar queries pesadas en cada request.
Cache se invalida cada 5 minutos.
"""
import json
from datetime import timedelta

from django.core.cache import cache
from django.utils import timezone

CACHE_KEY = "admin_dashboard_metrics"
CACHE_TTL = 300  # 5 minutos


def admin_metrics(request):
    """Métricas para el dashboard admin (cached)."""

    # Solo cargar en el admin index
    if not request.path.startswith("/admin/") or request.path != "/admin/":
        return {}

    # Intentar cache
    cached = cache.get(CACHE_KEY)
    if cached:
        return cached

    # Calcular métricas
    from django.contrib.auth import get_user_model
    from apps.core_companies.models import Company, Membership
    from apps.core_marketplace.models import ModuleCatalogItem

    User = get_user_model()
    now = timezone.now()
    week_ago = now - timedelta(days=7)

    total_users = User.objects.count()
    new_users = User.objects.filter(date_joined__gte=week_ago).count()
    total_companies = Company.objects.count()
    active_modules = ModuleCatalogItem.objects.filter(is_active=True).count()
    inactive_modules = ModuleCatalogItem.objects.filter(is_active=False).count()

    companies = Company.objects.all().order_by("name")[:10]
    users_per_company = []
    for company in companies:
        users_per_company.append({
            "label": company.name,
            "value": Membership.objects.filter(company=company, status="active").count(),
        })

    charts = {
        "modules": {
            "labels": ["Activos", "Inactivos"],
            "values": [active_modules, inactive_modules],
        },
        "users_per_company": {
            "labels": [i["label"] for i in users_per_company],
            "values": [i["value"] for i in users_per_company],
        },
    }

    result = {
        "dashboard_cards": {
            "total_users": total_users,
            "new_users": new_users,
            "total_companies": total_companies,
            "active_modules": active_modules,
        },
        "dashboard_charts_json": json.dumps(charts),
    }

    # Guardar en cache
    cache.set(CACHE_KEY, result, CACHE_TTL)

    return result


def invalidate_dashboard_cache():
    """Invalidar cache del dashboard (llamar después de cambios)."""
    cache.delete(CACHE_KEY)
