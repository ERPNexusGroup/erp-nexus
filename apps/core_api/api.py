"""
API principal de ERP Nexus — Django Ninja.

Todas las rutas de la API viven aquí.
Versionado: /api/v1/
"""
from ninja import NinjaAPI

api = NinjaAPI(
    title="ERP Nexus API",
    version="0.2.0",
    description="API REST para el ecosistema ERP Nexus",
    docs_url="/docs",
)

# ─── Health check ────────────────────────────────────────────────────
@api.get("/health", tags=["system"])
def health(request):
    return {"status": "ok", "version": "0.2.0"}


# ─── Importar routers de cada módulo ─────────────────────────────────
from apps.core_api.v1.modules import router as modules_router  # noqa: E402
from apps.core_api.v1.events import router as events_router  # noqa: E402

api.add_router("/modules/", modules_router, tags=["modules"])
api.add_router("/events/", events_router, tags=["events"])
