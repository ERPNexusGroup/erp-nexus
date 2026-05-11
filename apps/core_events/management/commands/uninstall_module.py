"""
manage.py uninstall_module — Desinstala un módulo del ERP.
"""
import shutil
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from apps.core_marketplace.models import ModuleCatalogItem


class Command(BaseCommand):
    help = "Desinstala un módulo ERP Nexus."

    def add_arguments(self, parser):
        parser.add_argument("technical_name", help="Nombre técnico del módulo")
        parser.add_argument(
            "--keep-data",
            action="store_true",
            help="No eliminar datos del módulo",
        )

    def handle(self, *args, **options):
        name = options["technical_name"]

        module = ModuleCatalogItem.objects.filter(technical_name=name).first()
        if not module:
            raise CommandError(f"Módulo no encontrado: {name}")

        modules_dir = Path(getattr(settings, "MODULES_DIR", settings.BASE_DIR / "modules"))
        module_dir = modules_dir / name

        self.stdout.write(f"🗑️  Desinstalando: {name} v{module.version}")

        # Marcar como inactivo en DB
        module.status = "inactive"
        module.is_active = False
        module.save(update_fields=["status", "is_active"])

        # Eliminar archivos
        if module_dir.exists():
            shutil.rmtree(module_dir)
            self.stdout.write(f"   ✅ Archivos eliminados de {module_dir}")
        else:
            self.stdout.write(self.style.WARNING(f"   ⚠ Directorio no encontrado: {module_dir}"))

        # Eliminar de modules_enabled
        try:
            from apps.core_marketplace.activation import write_modules_enabled
            write_modules_enabled()
        except Exception:
            pass

        self.stdout.write(self.style.SUCCESS(f"✅ {name} desinstalado"))
