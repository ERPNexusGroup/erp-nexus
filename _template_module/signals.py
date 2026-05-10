"""Signals del módulo mi_modulo."""
from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver

from .models import ExampleModel


@receiver(post_save, sender=ExampleModel)
def examplemodel_post_save(sender, instance, created, **kwargs):
    """Hook post-guardado de ExampleModel."""
    if created:
        # Log creation, send notification, etc.
        pass


@receiver(pre_delete, sender=ExampleModel)
def examplemodel_pre_delete(sender, instance, **kwargs):
    """Validaciones pre-eliminación."""
    # Ejemplo: no permitir borrar si está referenciado
    if instance.is_active:
        raise Exception("No se puede eliminar un registro activo")
