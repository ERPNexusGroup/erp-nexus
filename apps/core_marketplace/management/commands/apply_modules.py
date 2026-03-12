from django.core.management.base import BaseCommand

from apps.core_marketplace.activation import write_modules_enabled
from apps.core_marketplace.models import EnabledModule


class Command(BaseCommand):
    help = "Genera el archivo modules_enabled.py basado en EnabledModule."

    def handle(self, *args, **options):
        path = write_modules_enabled()
        count = EnabledModule.objects.filter(status="active").count()
        self.stdout.write(self.style.SUCCESS(f"modules_enabled.py actualizado. Activos: {count}."))
        self.stdout.write(str(path))
