from django.contrib import admin
from django.urls import path, include

from apps.core_api.api import api

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/v1/", api.urls),  # Sin namespace extra — endpoints accesibles directamente
    path("marketplace/", include("apps.core_marketplace.urls")),  # Public catalog
]
