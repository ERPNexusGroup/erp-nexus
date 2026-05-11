from django.urls import path
from . import views

app_name = "core_marketplace"

urlpatterns = [
    path("", views.public_catalog, name="public_catalog"),
]
