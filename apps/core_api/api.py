"""
API principal de ERP Nexus — Django Ninja.

Todas las rutas de la API viven aquí.
Versionado: /api/v1/
"""
from ninja import NinjaAPI

api = NinjaAPI(
    title="ERP Nexus API",
    version="0.5.0",
    description="API REST para el ecosistema ERP Nexus",
    docs_url="/docs",
)

# ─── Health check (público) ─────────────────────────────────────────
@api.get("/health", tags=["system"])
def health(request):
    """Health check — verifica estado del sistema."""
    from django.db import connection
    from django.core.cache import cache

    checks = {"status": "ok", "version": "0.5.0"}

    # Verificar DB
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        checks["database"] = "ok"
    except Exception as e:
        checks["database"] = f"error: {str(e)[:50]}"
        checks["status"] = "degraded"

    # Verificar cache
    try:
        cache.set("health_check", "ok", 10)
        val = cache.get("health_check")
        checks["cache"] = "ok" if val == "ok" else "error"
    except Exception as e:
        checks["cache"] = f"error: {str(e)[:50]}"
        checks["status"] = "degraded"

    return checks


# ─── Auth (público) ─────────────────────────────────────────────────
from apps.core_api.v1.auth import router as auth_router  # noqa: E402
api.add_router("/auth/", auth_router, tags=["auth"])

# ─── Password Reset (público) ───────────────────────────────────────
from apps.core_api.v1.password_reset import router as password_reset_router  # noqa: E402
api.add_router("/auth/password-reset/", password_reset_router, tags=["auth"])

# ─── Users (protegido) ──────────────────────────────────────────────
from apps.core_api.v1.users import router as users_router  # noqa: E402
api.add_router("/users/", users_router, tags=["users"])

# ─── Módulos (protegido) ────────────────────────────────────────────
from apps.core_api.v1.modules import router as modules_router  # noqa: E402
api.add_router("/modules/", modules_router, tags=["modules"])

# ─── Events (protegido) ─────────────────────────────────────────────
from apps.core_api.v1.events import router as events_router  # noqa: E402
api.add_router("/events/", events_router, tags=["events"])

# ─── Audit (protegido) ──────────────────────────────────────────────
from apps.core_api.v1.audit import router as audit_router  # noqa: E402
api.add_router("/audit/", audit_router, tags=["audit"])

# ─── Marketplace (protegido) ────────────────────────────────────────
from apps.core_api.v1.marketplace import router as marketplace_router  # noqa: E402
api.add_router("/marketplace/", marketplace_router, tags=["marketplace"])

# ─── Stats (protegido) ──────────────────────────────────────────────
from apps.core_api.v1.stats import router as stats_router  # noqa: E402
api.add_router("/stats/", stats_router, tags=["stats"])

# ─── Page Builder (protegido) ───────────────────────────────────────
from apps.core_api.v1.pages import router as pages_router  # noqa: E402
api.add_router("/pages/", pages_router, tags=["pages"])
