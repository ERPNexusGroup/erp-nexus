"""
Context processor para dashboard + menú lateral dinámico ERPNext.

- Solo ejecuta para usuarios staff.
- Solo carga queries DB en URLs /admin/.
- Invalida cache automáticamente al instalar/desinstalar módulos.
"""
import json
from datetime import timedelta
from collections import defaultdict

from django.conf import settings
from django.core.cache import cache
from django.utils import timezone

CACHE_TTL = 300  # 5 minutos


def admin_metrics(request):
    """Context processor principal — solo páginas del admin."""

    # Guards: solo staff en URLs del admin
    if not request.user.is_staff or not request.path.startswith('/admin/'):
        return {}

    # ─── Menú lateral dinámico (disponible en TODAS las páginas admin) ─
    jazzmin_apps_cache_key = "jazzmin_side_menu_apps"
    jazzmin_apps = cache.get(jazzmin_apps_cache_key)

    if jazzmin_apps is None:
        jazzmin_apps = []
        from apps.core_marketplace.models import EnabledModule, ModuleCatalogItem

        enabled_qs = EnabledModule.objects.filter(status='active')
        tech_names = list(enabled_qs.values_list('technical_name', flat=True))
        catalog_map = {
            item.technical_name: item
            for item in ModuleCatalogItem.objects.filter(technical_name__in=tech_names)
        }

        by_category = defaultdict(list)
        for enabled in enabled_qs:
            cat = 'Aplicaciones'
            catalog_item = catalog_map.get(enabled.technical_name)
            if catalog_item:
                cat = catalog_item.admin_menu_category or 'Aplicaciones'
            by_category[cat].append((enabled, catalog_item))

        category_icons = {
            'Aplicaciones': 'fas fa-th-large',
            'Ventas': 'fas fa-shopping-cart',
            'Inventario': 'fas fa-warehouse',
            'Contabilidad': 'fas fa-chart-line',
            'Recursos Humanos': 'fas fa-users',
            'CRM': 'fas fa-handshake',
            'Manufactura': 'fas fa-industry',
            'Proyectos': 'fas fa-tasks',
            'Sitio Web': 'fas fa-globe',
        }

        for category in sorted(by_category.keys()):
            items = sorted(by_category[category], key=lambda x: x[0].technical_name)
            first_enabled, first_catalog = items[0] if items else (None, None)
            label = (first_catalog.display_name or first_catalog.technical_name) if first_catalog else category

            jazzmin_apps.append({
                'label': category,
                'icon': category_icons.get(category, 'fas fa-cube'),
                'url': None,
                'models': [
                    {
                        'name': catalog.display_name if catalog else enabled.technical_name,
                        'admin_url': f"/admin/core_marketplace/enabledmodule/{enabled.id}/change/",
                    }
                    for enabled, catalog in items
                ],
            })

        cache.set(jazzmin_apps_cache_key, jazzmin_apps, CACHE_TTL * 2)

    # ─── Dashboard-only metrics (solo para /admin/) ─────────────────────
    if request.path != "/admin/":
        return {'jazzmin_apps': jazzmin_apps}

    dashboard_cache_key = "admin_dashboard_metrics"
    cached = cache.get(dashboard_cache_key)
    if cached:
        return {**cached, 'jazzmin_apps': jazzmin_apps}

    from django.contrib.auth import get_user_model
    from apps.core_companies.models import Company, Membership
    from apps.core_marketplace.models import ModuleCatalogItem, ModuleLicense

    User = get_user_model()
    now = timezone.now()
    week_ago = now - timedelta(days=7)

    # Core metrics
    total_users = User.objects.count()
    new_users = User.objects.filter(date_joined__gte=week_ago).count()
    total_companies = Company.objects.count()

    # Marketplace
    active_catalog = ModuleCatalogItem.objects.filter(is_active=True).count()
    installed_count = EnabledModule.objects.filter(status='active').count()
    total_licenses = ModuleLicense.objects.filter(is_active=True).count()
    licenses_expiring = ModuleLicense.objects.filter(
        is_active=True,
        valid_until__lte=now + timedelta(days=30),
        valid_until__gt=now,
    ).count()
    expired = ModuleLicense.objects.filter(is_active=True, valid_until__lt=now).count()

    dashboard_cards = {
        'total_users': total_users,
        'new_users': new_users,
        'total_companies': total_companies,
        'active_modules': active_catalog,
        'installed_modules': installed_count,
        'total_licenses': total_licenses,
        'licenses_expiring': licenses_expiring,
        'licenses_expired': expired,
    }

    recent_installs = list(
        EnabledModule.objects.filter(status='active')
        .order_by('-id')[:5]
    )

    result = {
        'dashboard_cards': dashboard_cards,
        'recent_installs': recent_installs,
        'jazzmin_apps': jazzmin_apps,
    }
    cache.set(dashboard_cache_key, result, CACHE_TTL)
    return result


def invalidate_dashboard_cache():
    """Invalidar cache (llamar después de instalar/desinstalar módulos)."""
    cache.delete('admin_dashboard_metrics')
    cache.delete('jazzmin_side_menu_apps')
