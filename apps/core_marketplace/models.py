from django.db import models


class ModuleCatalogItem(models.Model):
    technical_name = models.CharField(max_length=100, unique=True)
    version = models.CharField(max_length=50)
    is_active = models.BooleanField(default=True)

    def __str__(self) -> str:
        return f"{self.technical_name} ({self.version})"
