"""
AuditLog — Registro de actividad del sistema.

Registra:
  - Login/logout
  - Cambios en módulos (install/uninstall/activate)
  - Cambios de datos (create/update/delete)
  - Accesos a endpoints sensibles
"""
import uuid
from django.db import models
from django.utils import timezone


class AuditLog(models.Model):
    """
    Log inmutable de acciones del sistema.
    """
    ACTION_TYPES = [
        ("auth.login", "Login"),
        ("auth.logout", "Logout"),
        ("auth.register", "Registro"),
        ("auth.password_change", "Cambio de contraseña"),
        ("auth.password_reset", "Reset de contraseña"),
        ("module.install", "Instalar módulo"),
        ("module.uninstall", "Desinstalar módulo"),
        ("module.activate", "Activar módulo"),
        ("module.deactivate", "Desactivar módulo"),
        ("data.create", "Crear registro"),
        ("data.update", "Actualizar registro"),
        ("data.delete", "Eliminar registro"),
        ("api.access", "Acceso API"),
        ("system.error", "Error del sistema"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Quién
    user_id = models.IntegerField(null=True, blank=True, help_text="ID del usuario")
    username = models.CharField(max_length=150, blank=True, default="")

    # Qué
    action = models.CharField(max_length=50, choices=ACTION_TYPES, db_index=True)
    resource_type = models.CharField(
        max_length=100, blank=True, default="",
        help_text="Tipo de recurso (User, Module, Product, etc.)",
    )
    resource_id = models.CharField(max_length=100, blank=True, default="")

    # Detalles
    description = models.TextField(blank=True, default="")
    metadata = models.JSONField(default=dict, help_text="Datos adicionales")

    # Contexto
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True, default="")

    # Empresa (multi-tenancy)
    company_id = models.IntegerField(null=True, blank=True)
    company_name = models.CharField(max_length=200, blank=True, default="")

    # Timestamp
    created_at = models.DateTimeField(default=timezone.now, db_index=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["action", "created_at"]),
            models.Index(fields=["user_id", "created_at"]),
            models.Index(fields=["company_id", "created_at"]),
        ]
        verbose_name = "Audit Log"
        verbose_name_plural = "Audit Logs"

    def __str__(self):
        user = self.username or "system"
        return f"{user}: {self.action} ({self.resource_type})"

    @classmethod
    def log(
        cls,
        action: str,
        user=None,
        resource_type: str = "",
        resource_id: str = "",
        description: str = "",
        metadata: dict = None,
        request=None,
    ) -> "AuditLog":
        """
        Crea una entrada de audit log.

        Uso:
            AuditLog.log(
                action="module.install",
                user=request.user,
                resource_type="Module",
                resource_id="accounting_basic",
                description="Módulo accounting_basic instalado",
            )
        """
        ip = ""
        user_agent = ""
        company_id = None
        company_name = ""
        user_id = None
        username = ""

        if request:
            ip = _get_client_ip(request)
            user_agent = request.META.get("HTTP_USER_AGENT", "")[:500]

            # Usuario del request
            if hasattr(request, "user") and request.user.is_authenticated:
                user = request.user

            # Empresa activa
            if hasattr(request, "active_company") and request.active_company:
                company_id = request.active_company.id
                company_name = request.active_company.name

        if user:
            user_id = user.id
            username = getattr(user, "username", "")

        # Empresa del usuario si no hay en request
        if user and not company_id:
            try:
                profile = user.erp_profile
                if profile.active_company:
                    company_id = profile.active_company.id
                    company_name = profile.active_company.name
            except Exception:
                pass

        return cls.objects.create(
            user_id=user_id,
            username=username,
            action=action,
            resource_type=resource_type,
            resource_id=str(resource_id),
            description=description,
            metadata=metadata or {},
            ip_address=ip,
            user_agent=user_agent,
            company_id=company_id,
            company_name=company_name,
        )


def _get_client_ip(request) -> str:
    """Obtiene la IP real del cliente."""
    x_forwarded = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded:
        return x_forwarded.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR", "0.0.0.0")
