# Management command: module_uninstall
# Desinstala un módulo (lo desactiva)
from django.core.management.base import BaseCommand, CommandError
from apps.core_marketplace.models import EnabledModule
from apps.core_marketplace.activation import write_modules_enabled


class Command(BaseCommand):
    help = "Desinstala/desactiva un módulo (equivalente a 'nexus uninstall')"

    def add_arguments(self, parser):
        parser.add_argument("technical_name", help="Nombre técnico del módulo (ej: facturacion_ec)")
        parser.add_argument(
            "--force",
            action="store_true",
            help="Forzar desinstalación (no preguntar)"
        )

    def handle(self, *args, **options):
        tech_name = options["technical_name"]

        try:
            enabled = EnabledModule.objects.get(technical_name=tech_name)
        except EnabledModule.DoesNotExist:
            raise CommandError(f"Módulo no encontrado o ya desactivado: {tech_name}")

        if not options["force"]:
            confirm = input(f"¿Desinstalar módulo '{tech_name}'? (s/N): ")
            if confirm.lower() != "s":
                self.stdout.write("Cancelado.")
                return

        # Desactivar
        enabled.status = "inactive"
        enabled.save()

        # Regenerar modules_enabled.py
        write_modules_enabled()

        self.stdout.write(self.style.SUCCESS(f"✅ Módulo '{tech_name}' desactivado"))
        self.stdout.write("")
        self.stdout.write("Nota: Las tablas en BD NO se eliminan automáticamente.")
        self.stdout.write("Para eliminar datos, ejecute:")
        self.stdout.write(f"  uv run python manage.py migrate {enabled.django_app} zero")
        self.stdout.write(f"  uv run python manage.py migrate {enabled.django_app}")
        self.stdout.write("")
        self.stdout.write("Reinicie el servidor Django para que cambios surtan efecto.")
