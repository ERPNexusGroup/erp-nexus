from django.conf import settings
from django.db import models


class Company(models.Model):
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True)
    is_active = models.BooleanField(default=True)
    # Datos fiscales Ecuador
    ruc = models.CharField(max_length=13, blank=True, null=True, unique=True, help_text="RUC - 13 dígitos")
    tax_id = models.CharField(max_length=20, blank=True, null=True, help_text="Identificación fiscal (cédula/RUC)")
    address = models.TextField(blank=True, null=True)
    phone = models.CharField(max_length=30, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    # Configuración facturación
    establishment_code = models.CharField(max_length=3, default="001", help_text="Código establecimiento (3 dígitos)")
    point_emission_code = models.CharField(max_length=3, default="001", help_text="Código punto emisión (3 dígitos)")
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return self.name


class Membership(models.Model):
    ROLE_CHOICES = [
        ("owner", "Owner"),
        ("admin", "Admin"),
        ("member", "Member"),
    ]
    STATUS_CHOICES = [
        ("active", "Active"),
        ("inactive", "Inactive"),
        ("invited", "Invited"),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="memberships")
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default="member")
    is_owner = models.BooleanField(default=False)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="active")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "company")

    def __str__(self) -> str:
        return f"{self.user} -> {self.company} ({self.role})"
