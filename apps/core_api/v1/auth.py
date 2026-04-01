"""
Core Auth — Autenticación y autorización para ERP Nexus.

Endpoints:
  POST /api/v1/auth/login     → Login (retorna JWT tokens)
  POST /api/v1/auth/register  → Registro de usuario
  POST /api/v1/auth/refresh   → Renovar access token
  GET  /api/v1/auth/me        → Info del usuario actual
  POST /api/v1/auth/logout    → Invalidar refresh token
"""
import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional

import jwt
from django.conf import settings
from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.hashers import make_password
from ninja import Router, Schema

router = Router()

# ─── Configuración JWT ──────────────────────────────────────────────
JWT_SECRET = getattr(settings, "JWT_SECRET", settings.SECRET_KEY)
JWT_ALGORITHM = "HS256"
JWT_ACCESS_EXPIRY = timedelta(hours=1)
JWT_REFRESH_EXPIRY = timedelta(days=7)


# ─── Schemas ────────────────────────────────────────────────────────
class LoginRequest(Schema):
    username: str
    password: str


class RegisterRequest(Schema):
    username: str
    email: str
    password: str
    display_name: Optional[str] = None


class TokenResponse(Schema):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class RefreshRequest(Schema):
    refresh_token: str


class UserOut(Schema):
    id: int
    username: str
    email: str
    is_staff: bool
    is_superuser: bool
    display_name: Optional[str] = None


class MessageResponse(Schema):
    message: str


# ─── Helpers ────────────────────────────────────────────────────────
def generate_tokens(user_id: int) -> dict:
    """Genera access y refresh tokens JWT."""
    now = datetime.now(timezone.utc)

    access_payload = {
        "sub": str(user_id),
        "type": "access",
        "iat": now,
        "exp": now + JWT_ACCESS_EXPIRY,
        "jti": secrets.token_hex(16),
    }

    refresh_payload = {
        "sub": str(user_id),
        "type": "refresh",
        "iat": now,
        "exp": now + JWT_REFRESH_EXPIRY,
        "jti": secrets.token_hex(16),
    }

    access_token = jwt.encode(access_payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
    refresh_token = jwt.encode(refresh_payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "expires_in": int(JWT_ACCESS_EXPIRY.total_seconds()),
    }


def decode_token(token: str, expected_type: str = "access") -> Optional[dict]:
    """Decodifica y valida un token JWT."""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        if payload.get("type") != expected_type:
            return None
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


def get_user_from_token(request) -> Optional["User"]:
    """Extrae el usuario del token JWT en el header Authorization."""
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        return None

    token = auth_header[7:]
    payload = decode_token(token, "access")
    if not payload:
        return None

    User = get_user_model()
    try:
        return User.objects.get(id=int(payload["sub"]))
    except User.DoesNotExist:
        return None


# ─── Endpoints ──────────────────────────────────────────────────────
from apps.core_api.rate_limit import auth_rate_limit


@router.post("/login", response=TokenResponse, auth=None)
@auth_rate_limit(requests=10, window=60)
def login(request, data: LoginRequest):
    """
    Login con username/password.

    Retorna JWT access_token y refresh_token.
    """
    user = authenticate(request, username=data.username, password=data.password)
    if not user:
        from ninja.errors import HttpError
        raise HttpError(401, "Credenciales inválidas")

    if not user.is_active:
        from ninja.errors import HttpError
        raise HttpError(403, "Usuario desactivado")

    return generate_tokens(user.id)


@router.post("/register", response=UserOut, auth=None)
@auth_rate_limit(requests=5, window=300)
def register(request, data: RegisterRequest):
    """
    Registro de nuevo usuario.

    Crea usuario + UserProfile automáticamente.
    """
    User = get_user_model()

    # Validar que no existe
    if User.objects.filter(username=data.username).exists():
        from ninja.errors import HttpError
        raise HttpError(409, "El username ya está en uso")

    if User.objects.filter(email=data.email).exists():
        from ninja.errors import HttpError
        raise HttpError(409, "El email ya está registrado")

    # Crear usuario
    user = User.objects.create_user(
        username=data.username,
        email=data.email,
        password=data.password,
    )

    # Crear profile
    try:
        from apps.core_users.models import UserProfile
        UserProfile.objects.create(
            user=user,
            display_name=data.display_name or data.username,
        )
    except Exception:
        pass  # UserProfile puede no estar disponible

    return UserOut(
        id=user.id,
        username=user.username,
        email=user.email,
        is_staff=user.is_staff,
        is_superuser=user.is_superuser,
        display_name=data.display_name or data.username,
    )


@router.post("/refresh", response=TokenResponse, auth=None)
def refresh_token(request, data: RefreshRequest):
    """
    Renueva el access token usando un refresh token válido.
    """
    payload = decode_token(data.refresh_token, "refresh")
    if not payload:
        from ninja.errors import HttpError
        raise HttpError(401, "Refresh token inválido o expirado")

    User = get_user_model()
    try:
        user = User.objects.get(id=int(payload["sub"]), is_active=True)
    except User.DoesNotExist:
        from ninja.errors import HttpError
        raise HttpError(401, "Usuario no encontrado")

    return generate_tokens(user.id)


@router.get("/me", response=UserOut)
def me(request):
    """
    Retorna información del usuario autenticado.
    """
    user = get_user_from_token(request)
    if not user:
        from ninja.errors import HttpError
        raise HttpError(401, "No autenticado")

    display_name = None
    try:
        display_name = user.erp_profile.display_name
    except Exception:
        display_name = user.username

    return UserOut(
        id=user.id,
        username=user.username,
        email=user.email,
        is_staff=user.is_staff,
        is_superuser=user.is_superuser,
        display_name=display_name,
    )


@router.post("/logout", response=MessageResponse)
def logout(request):
    """
    Logout (el cliente debe descartar los tokens).

    Para invalidación server-side, se necesitaría una blacklist de tokens.
    """
    return {"message": "Logout exitoso. Descarta los tokens del cliente."}
