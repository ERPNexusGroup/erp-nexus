# URLs del módulo facturacion
# Importante: Este módulo se registra en erp_nexus/urls.py vía include()
# Las rutas del API Ninja se exponen en /api/v1/ a través de core_api
"""
from django.urls import path
from django.shortcuts import render

app_name = "facturacion"

# Admin ya está gestionado por Django/admin/ → no necesita ruta aquí
urlpatterns = [
    # Dashboard del módulo (vista HTML)
    path("", views.dashboard, name="dashboard"),
]
