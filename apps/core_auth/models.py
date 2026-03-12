from django.db import models


class AuthPolicy(models.Model):
    name = models.CharField(max_length=100, unique=True)
    is_active = models.BooleanField(default=True)

    def __str__(self) -> str:
        return self.name
