import json
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.utils import timezone

from apps.core_companies.models import Company, Membership
from apps.core_marketplace.models import ModuleCatalogItem


def admin_metrics(request):
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
        users_per_company.append(
            {
                "label": company.name,
                "value": Membership.objects.filter(company=company, status="active").count(),
            }
        )

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

    return {
        "dashboard_cards": {
            "total_users": total_users,
            "new_users": new_users,
            "total_companies": total_companies,
            "active_modules": active_modules,
        },
        "dashboard_charts_json": json.dumps(charts),
    }
