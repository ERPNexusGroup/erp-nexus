from django.db import models


class UserProfile(models.Model):
    user_id = models.PositiveIntegerField(unique=True)
    display_name = models.CharField(max_length=150)
    is_active = models.BooleanField(default=True)

    def __str__(self) -> str:
        return self.display_name
