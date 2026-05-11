from django.contrib import admin
from django.urls import path, include

from apps.core_api.api import api

from django.http import JsonResponse
from django.db import connection


def health_check(request):
    """Production health endpoint.
    Verifica conexión a base de datos y retorna JSON.
    Used by Docker HEALTHCHECK y load balancers.
    """
    try:
        connection.ensure_connection()
        return JsonResponse({
            "status": "healthy",
            "db": "ok",
        })
    except Exception as exc:
        return JsonResponse({
            "status": "unhealthy",
            "db": "error",
            "error": str(exc),
        }, status=503)


urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/v1/", api.urls),  # Sin namespace extra — endpoints accesibles directamente
    path("marketplace/", include("apps.core_marketplace.urls")),  # Public catalog
    path("health/", health_check, name="health_check"),
]
