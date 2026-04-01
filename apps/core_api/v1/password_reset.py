"""
Password Reset — recuperación de contraseña via email.

Flujo:
  1. POST /api/v1/auth/password-reset/request  → envía email con token
  2. POST /api/v1/auth/password-reset/confirm   → resetea con token

NOTA: En desarrollo, el token se imprime en consola (no envía email real).
Para producción, configurar email backend.
"""
import secrets
from datetime import timedelta

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.utils import timezone
from ninja import Router, Schema

from apps.core_api.rate_limit import auth_rate_limit

router = Router()


class PasswordResetRequest(Schema):
    email: str


class PasswordResetConfirm(Schema):
    token: str
    new_password: str


class MessageResponse(Schema):
    message: str


RESET_TOKEN_EXPIRY = 3600  # 1 hora en segundos


@router.post("/request", response=MessageResponse, auth=None)
@auth_rate_limit(requests=3, window=300)
def request_reset(request, data: PasswordResetRequest):
    """
    Solicita reset de contraseña.

    Genera un token y lo guarda en cache (1 hora de validez).
    En desarrollo, imprime el token en consola.
    """
    User = get_user_model()
    user = User.objects.filter(email=data.email, is_active=True).first()

    # Siempre retorna éxito (no revelar si el email existe)
    if not user:
        return {"message": "Si el email existe, recibirás instrucciones de reset."}

    # Generar token
    token = secrets.token_urlsafe(32)
    cache_key = f"password_reset:{token}"
    cache.set(cache_key, user.id, RESET_TOKEN_EXPIRY)

    # En desarrollo, imprimir token
    print(f"\n{'='*60}")
    print(f"🔐 PASSWORD RESET TOKEN para {user.email}:")
    print(f"   Token: {token}")
    print(f"   Válido por: {RESET_TOKEN_EXPIRY // 60} minutos")
    print(f"{'='*60}\n")

    # En producción, aquí se enviaría el email:
    # send_mail(
    #     subject="ERP Nexus — Reset de contraseña",
    #     message=f"Tu token de reset: {token}",
    #     from_email="noreply@erp-nexus.org",
    #     recipient_list=[user.email],
    # )

    return {"message": "Si el email existe, recibirás instrucciones de reset."}


@router.post("/confirm", response=MessageResponse, auth=None)
@auth_rate_limit(requests=5, window=60)
def confirm_reset(request, data: PasswordResetConfirm):
    """
    Confirma el reset de contraseña con el token.

    El token es válido por 1 hora.
    """
    if len(data.new_password) < 8:
        from ninja.errors import HttpError
        raise HttpError(400, "La contraseña debe tener al menos 8 caracteres")

    # Verificar token
    cache_key = f"password_reset:{data.token}"
    user_id = cache.get(cache_key)

    if not user_id:
        from ninja.errors import HttpError
        raise HttpError(400, "Token inválido o expirado")

    # Resetear contraseña
    User = get_user_model()
    try:
        user = User.objects.get(id=user_id, is_active=True)
    except User.DoesNotExist:
        from ninja.errors import HttpError
        raise HttpError(400, "Usuario no encontrado")

    user.set_password(data.new_password)
    user.save(update_fields=["password"])

    # Invalidar token
    cache.delete(cache_key)

    return {"message": "Contraseña actualizada exitosamente"}
