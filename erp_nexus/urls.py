from django.contrib import admin
from django.urls import path

from apps.core_api.api import api

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/v1/", api.urls),  # Versionado v1
]
