"""
Middleware de autenticación JWT para API.

Uso en Django Ninja:
    from apps.core_api.auth import JWTAuth

    @router.get("/protected", auth=JWTAuth())
    def protected_endpoint(request):
        return {"user": request.auth.username}
"""
from typing import Optional

from django.contrib.auth import get_user_model
from ninja.security import HttpBearer

from apps.core_api.v1.auth import decode_token


class JWTAuth(HttpBearer):
    """
    Autenticación JWT Bearer para endpoints protegidos.

    Uso:
        @router.get("/endpoint", auth=JWTAuth())
        def my_view(request):
            user = request.auth  # El usuario autenticado
    """

    def authenticate(self, request, token: str) -> Optional["User"]:
        """Valida el token y retorna el usuario."""
        payload = decode_token(token, "access")
        if not payload:
            return None

        User = get_user_model()
        try:
            user = User.objects.get(id=int(payload["sub"]), is_active=True)
            return user
        except User.DoesNotExist:
            return None


class OptionalJWTAuth(HttpBearer):
    """
    Autenticación JWT opcional — permite acceso sin token
    pero si hay token válido, carga el usuario.

    Uso:
        @router.get("/public-or-user", auth=OptionalJWTAuth())
        def my_view(request):
            user = request.auth  # Puede ser None
    """

    def authenticate(self, request, token: str) -> Optional["User"]:
        if not token:
            return None

        payload = decode_token(token, "access")
        if not payload:
            return None

        User = get_user_model()
        try:
            return User.objects.get(id=int(payload["sub"]), is_active=True)
        except User.DoesNotExist:
            return None
