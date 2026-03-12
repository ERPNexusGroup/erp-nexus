from django.core.management.base import BaseCommand, CommandError

from apps.core_marketplace.activation import write_modules_enabled
from apps.core_marketplace.models import EnabledModule, ModuleCatalogItem


class Command(BaseCommand):
    help = "Activa un módulo del catálogo para cargar su app Django."

    def add_arguments(self, parser):
        parser.add_argument("technical_name")

    def handle(self, *args, **options):
        technical_name = options["technical_name"]
        item = ModuleCatalogItem.objects.filter(technical_name=technical_name).first()
        if not item:
            raise CommandError(f"No existe en catálogo: {technical_name}")
        if not item.django_app:
            raise CommandError("El módulo no define django_app en __meta__.py")

        EnabledModule.objects.update_or_create(
            technical_name=technical_name,
            defaults={"django_app": item.django_app, "status": "active"},
        )
        write_modules_enabled()
        self.stdout.write(self.style.SUCCESS(f"Módulo activado: {technical_name}"))
