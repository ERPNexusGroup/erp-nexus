"""
Router de usuarios — endpoints para gestión de perfiles.
Protegido con JWT Auth.
"""
from ninja import Router, Schema
from typing import Optional
from django.contrib.auth import get_user_model

from apps.core_api.auth import JWTAuth
from apps.core_api.v1.auth import get_user_from_token

router = Router(auth=JWTAuth())


class UserProfileOut(Schema):
    id: int
    username: str
    email: str
    display_name: Optional[str]
    is_active: bool
    is_staff: bool
    active_company: Optional[str]


class UserProfileUpdate(Schema):
    display_name: Optional[str] = None
    email: Optional[str] = None


class ChangePasswordRequest(Schema):
    current_password: str
    new_password: str


class MessageResponse(Schema):
    message: str


@router.get("/me", response=UserProfileOut)
def get_profile(request):
    """Obtiene el perfil del usuario actual."""
    user = get_user_from_token(request)

    display_name = None
    company_name = None
    try:
        profile = user.erp_profile
        display_name = profile.display_name
        if profile.active_company:
            company_name = profile.active_company.name
    except Exception:
        display_name = user.username

    return UserProfileOut(
        id=user.id,
        username=user.username,
        email=user.email,
        display_name=display_name,
        is_active=user.is_active,
        is_staff=user.is_staff,
        active_company=company_name,
    )


@router.patch("/me", response=UserProfileOut)
def update_profile(request, data: UserProfileUpdate):
    """Actualiza el perfil del usuario actual."""
    user = get_user_from_token(request)

    if data.email:
        User = get_user_model()
        if User.objects.filter(email=data.email).exclude(id=user.id).exists():
            from ninja.errors import HttpError
            raise HttpError(409, "Email ya en uso")
        user.email = data.email
        user.save(update_fields=["email"])

    if data.display_name:
        try:
            profile = user.erp_profile
            profile.display_name = data.display_name
            profile.save(update_fields=["display_name"])
        except Exception:
            from apps.core_users.models import UserProfile
            UserProfile.objects.create(user=user, display_name=data.display_name)

    return get_profile(request)


@router.post("/change-password", response=MessageResponse)
def change_password(request, data: ChangePasswordRequest):
    """Cambia la contraseña del usuario actual."""
    user = get_user_from_token(request)

    if not user.check_password(data.current_password):
        from ninja.errors import HttpError
        raise HttpError(400, "Contraseña actual incorrecta")

    if len(data.new_password) < 8:
        from ninja.errors import HttpError
        raise HttpError(400, "La nueva contraseña debe tener al menos 8 caracteres")

    user.set_password(data.new_password)
    user.save(update_fields=["password"])

    return {"message": "Contraseña actualizada exitosamente"}
