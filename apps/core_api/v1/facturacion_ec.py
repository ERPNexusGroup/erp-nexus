# API v1 — Facturación Electrónica Ecuador
from ninja import Router
from modules.facturacion_ec.api.routes import router as facturacion_router

# Exponer endpoints de facturacion_ec bajo /api/v1/facturacion_ec/
router = facturacion_router
