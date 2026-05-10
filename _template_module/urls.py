"""URLs del módulo mi_modulo."""
from django.urls import path

from . import views

app_name = "mi_modulo"
urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    # path("api/", include(...)),  # Si usa API separada
]
