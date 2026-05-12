# API v1 — Facturación Electrónica Ecuador (Plugin SRI)
from ninja import Router
from modules.facturacion_ec.api.routes import router as facturacion_router

# Expone endpoints bajo /api/v1/facturacion_ec/
router = facturacion_router
