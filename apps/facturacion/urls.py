from django.urls import path
from . import api

app_name = "facturacion"

urlpatterns = [
    # API endpoints agrupados en api/
    path("api/", api.router.urls),
]
