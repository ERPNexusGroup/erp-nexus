"""
Rate limiting middleware para API.

Uso:
    from apps.core_api.rate_limit import rate_limit

    @router.get("/endpoint")
    @rate_limit(requests=100, window=60)  # 100 requests por minuto
    def my_view(request):
        ...
"""
import time
import hashlib
from functools import wraps
from typing import Callable

from django.core.cache import cache
from ninja.errors import HttpError


def rate_limit(requests: int = 60, window: int = 60, key_func: Callable = None):
    """
    Decorator de rate limiting.

    Args:
        requests: Número máximo de requests permitidas
        window: Ventana de tiempo en segundos
        key_func: Función opcional para generar la clave de rate limit
    """
    def decorator(func):
        @wraps(func)
        def wrapper(request, *args, **kwargs):
            from django.conf import settings

            # Skip rate limiting in test mode
            if getattr(settings, "TESTING", False) or getattr(settings, "DISABLE_RATE_LIMIT", False):
                return func(request, *args, **kwargs)

            # Generar clave de rate limit
            if key_func:
                cache_key = f"rl:{key_func(request)}"
            else:
                # Default: usar IP + path
                ip = _get_client_ip(request)
                path = request.path
                cache_key = f"rl:{hashlib.md5(f'{ip}:{path}'.encode()).hexdigest()}"

            # Verificar rate limit
            current = cache.get(cache_key, 0)
            if current >= requests:
                raise HttpError(
                    429,
                    f"Rate limit excedido. Máximo {requests} requests por {window} segundos."
                )

            # Incrementar contador
            if current == 0:
                cache.set(cache_key, 1, window)
            else:
                cache.incr(cache_key)

            return func(request, *args, **kwargs)
        return wrapper
    return decorator


def auth_rate_limit(requests: int = 10, window: int = 60):
    """
    Rate limit específico para endpoints de auth (más restrictivo).
    Default: 10 requests por minuto.
    """
    def decorator(func):
        @wraps(func)
        def wrapper(request, *args, **kwargs):
            from django.conf import settings

            # Skip rate limiting in test mode
            if getattr(settings, "TESTING", False) or getattr(settings, "DISABLE_RATE_LIMIT", False):
                return func(request, *args, **kwargs)

            ip = _get_client_ip(request)
            cache_key = f"rl:auth:{hashlib.md5(ip.encode()).hexdigest()}"

            current = cache.get(cache_key, 0)
            if current >= requests:
                raise HttpError(
                    429,
                    f"Demasiados intentos de autenticación. Espera {window} segundos."
                )

            if current == 0:
                cache.set(cache_key, 1, window)
            else:
                cache.incr(cache_key)

            return func(request, *args, **kwargs)
        return wrapper
    return decorator


def _get_client_ip(request) -> str:
    """Obtiene la IP real del cliente."""
    x_forwarded = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded:
        return x_forwarded.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR", "0.0.0.0")
