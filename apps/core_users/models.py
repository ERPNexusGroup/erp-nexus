from django.conf import settings
from django.db import models



class UserProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="erp_profile",
        null=True,
        blank=True,
    )
    display_name = models.CharField(max_length=150)
    is_active = models.BooleanField(default=True)
    groups = models.ManyToManyField(
        "core_groups.Group",
        blank=True,
        related_name="users",
    )
    active_company = models.ForeignKey(
        "core_companies.Company",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="active_users",
    )

    def __str__(self) -> str:
        return self.display_name
