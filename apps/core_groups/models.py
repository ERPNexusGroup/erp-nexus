from django.db import models



class Group(models.Model):
    name = models.CharField(max_length=100, unique=True)
    is_active = models.BooleanField(default=True)
    permissions = models.ManyToManyField(
        "core_permissions.Permission",
        blank=True,
        related_name="groups",
    )

    def __str__(self) -> str:
        return self.name
