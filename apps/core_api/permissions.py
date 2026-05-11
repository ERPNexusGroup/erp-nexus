"""
Sistema de permisos para API endpoints.

Uso:
    from apps.core_api.permissions import require_permission

    @router.get("/admin-only")
    @require_permission("admin.access")
    def admin_view(request):
        ...
"""
from functools import wraps
from typing import List, Optional

from ninja.errors import HttpError


def require_permission(*permission_codes: str):
    """
    Decorator que requiere que el usuario tenga uno de los permisos especificados.

    Uso:
        @require_permission("modules.install")
        @require_permission("admin.access", "superadmin")
    """
    def decorator(func):
        @wraps(func)
        def wrapper(request, *args, **kwargs):
            user = getattr(request, "auth", None)
            if not user:
                raise HttpError(401, "No autenticado")

            # Superuser siempre tiene acceso
            if user.is_superuser:
                return func(request, *args, **kwargs)

            # Verificar permisos del usuario
            user_permissions = _get_user_permissions(user)
            if not any(perm in user_permissions for perm in permission_codes):
                raise HttpError(403, "Permisos insuficientes")

            return func(request, *args, **kwargs)
        return wrapper
    return decorator


def require_staff(func):
    """Decorator que requiere que el usuario sea staff."""
    @wraps(func)
    def wrapper(request, *args, **kwargs):
        user = getattr(request, "auth", None)
        if not user:
            raise HttpError(401, "No autenticado")
        if not user.is_staff and not user.is_superuser:
            raise HttpError(403, "Acceso solo para staff")
        return func(request, *args, **kwargs)
    return wrapper


def require_company_access(func):
    """
    Decorator que filtra datos por la empresa activa del usuario.
    Añade request.active_company al request.
    """
    @wraps(func)
    def wrapper(request, *args, **kwargs):
        user = getattr(request, "auth", None)
        if not user:
            raise HttpError(401, "No autenticado")

        # Superuser puede ver todo
        if user.is_superuser:
            return func(request, *args, **kwargs)

        # Obtener empresa activa del usuario
        try:
            profile = user.erp_profile
            if not profile.active_company:
                raise HttpError(403, "No tiene empresa activa asignada")
            request.active_company = profile.active_company
        except Exception:
            raise HttpError(403, "Perfil no encontrado")

        return func(request, *args, **kwargs)
    return wrapper


def _get_user_permissions(user) -> set:
    """Obtiene los permisos de un usuario via grupos."""
    try:
        profile = user.erp_profile
        groups = profile.groups.filter(is_active=True)
        permissions = set()
        for group in groups:
            permissions.update(
                group.permissions.values_list("code", flat=True)
            )
        return permissions
    except Exception:
        return set()
