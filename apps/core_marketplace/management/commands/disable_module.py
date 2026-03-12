from django.core.management.base import BaseCommand, CommandError

from apps.core_marketplace.activation import write_modules_enabled
from apps.core_marketplace.models import EnabledModule


class Command(BaseCommand):
    help = "Desactiva un módulo activo."

    def add_arguments(self, parser):
        parser.add_argument("technical_name")

    def handle(self, *args, **options):
        technical_name = options["technical_name"]
        module = EnabledModule.objects.filter(technical_name=technical_name).first()
        if not module:
            raise CommandError(f"No está activo: {technical_name}")

        module.status = "inactive"
        module.save(update_fields=["status"])
        write_modules_enabled()
        self.stdout.write(self.style.SUCCESS(f"Módulo desactivado: {technical_name}"))
