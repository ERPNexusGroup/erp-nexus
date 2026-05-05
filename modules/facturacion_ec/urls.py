# URLs del módulo facturacion_ec
from django.urls import path
from .api.routes import router as api_router

app_name = "facturacion_ec"

urlpatterns = [
    # Admin URLs (manejado por Django admin)
    # API endpoints
    path("api/", api_router.urls),
]
