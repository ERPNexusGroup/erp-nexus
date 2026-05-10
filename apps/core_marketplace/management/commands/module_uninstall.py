"""
Management command: module_uninstall

Uninstalls a module (removes from modules/, unregisters from EnabledModule).
"""
import shutil
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from apps.core_marketplace.models import EnabledModule, ModuleCatalogItem, ModuleDownload
from apps.core_marketplace.utils.module_loader import remove_from_modules_enabled


class Command(BaseCommand):
    help = "Uninstall a module from the marketplace"

    def add_arguments(self, parser):
        parser.add_argument(
            "technical_name",
            type=str,
            help="Technical name of the module to uninstall (e.g., 'hr')",
        )
        parser.add_argument(
            "--keep-data",
            action="store_true",
            help="Keep module files in modules/ directory (only unregister)",
        )
        parser.add_argument(
            "--force",
            action="store_true",
            help="Force uninstall even if module is marked as essential",
        )

    def handle(self, *args, **options):
        tech_name = options["technical_name"]
        keep_data = options["keep_data"]
        force = options["force"]

        self.stdout.write(f"🗑️  Uninstalling module: {tech_name}")

        # 1. Check if installed
        try:
            enabled = EnabledModule.objects.get(technical_name=tech_name)
        except EnabledModule.DoesNotExist:
            raise CommandError(f"Module '{tech_name}' is not installed.")

        # 2. Check catalog item for essential flag
        try:
            catalog_item = ModuleCatalogItem.objects.get(technical_name=tech_name)
            if catalog_item.module_type == 'essential' and not force:
                raise CommandError(
                    f"Module '{tech_name}' is marked as essential. Use --force to uninstall anyway."
                )
        except ModuleCatalogItem.DoesNotExist:
            self.stdout.write(self.style.WARNING(f"   ⚠️  Module not in catalog (orphaned)"))

        # 3. Remove from modules/ directory (unless --keep-data)
        modules_dir = Path(settings.BASE_DIR) / "modules"
        target_path = modules_dir / tech_name

        if target_path.exists():
            if keep_data:
                self.stdout.write(f"   📁 Keeping files at: {target_path}")
            else:
                self.stdout.write(f"   🗑️  Removing directory: {target_path}")
                shutil.rmtree(target_path)
        else:
            self.stdout.write(f"   ⚠️  Module directory not found: {target_path}")

        # 4. Remove from modules_enabled.py and unregister
        django_app = enabled.django_app
        with transaction.atomic():
            enabled.delete()
            self.stdout.write(f"   ✅ Removed from enabled modules")

            remove_from_modules_enabled(django_app)
            self.stdout.write(f"   ✅ Removed from modules_enabled.py")

            if catalog_item:
                catalog_item.mark_inactive()
                catalog_item.installed_path = None
                catalog_item.save(update_fields=["installed_path"])
                self.stdout.write(f"   ✅ Marked catalog item as inactive")

        # 5. Log uninstall
        ModuleDownload.objects.create(
            module_name=tech_name,
            version=catalog_item.version if catalog_item else "unknown",
            source=catalog_item.repo_url if catalog_item else "",
            status="failed",  # repurposed to track uninstalls
        )

        self.stdout.write(self.style.SUCCESS(f"\n✅ Module '{tech_name}' uninstalled successfully!"))
        self.stdout.write(f"   🔄 Restart Django to unload module")
