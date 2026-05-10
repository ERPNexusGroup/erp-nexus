# API v1 — Facturación Electrónica Ecuador
from ninja import Router
from apps.facturacion.api.routes import router as facturacion_router

# Exponer endpoints de facturación bajo /api/v1/facturacion/
router = facturacion_router
