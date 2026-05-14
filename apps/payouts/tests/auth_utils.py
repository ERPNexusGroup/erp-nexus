"""Utils de autenticación para tests de API."""
import jwt
from datetime import datetime, timezone, timedelta
from django.conf import settings


def generate_test_token(user):
    """Genera un token JWT de acceso para un usuario de prueba."""
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user.id),
        "type": "access",
        "iat": now,
        "exp": now + timedelta(hours=1),
        "jti": "test-jti",
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")


def auth_header(user):
    """Retorna header Authorization para un usuario."""
    token = generate_test_token(user)
    return {"Authorization": f"Bearer {token}"}
