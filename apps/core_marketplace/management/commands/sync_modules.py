from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.core_marketplace.manifest import ManifestError, ManifestSchema, parse_meta_file
from apps.core_marketplace.models import ModuleCatalogItem


class Command(BaseCommand):
    help = "Sincroniza módulos instalados en el filesystem con el catálogo interno."

    def handle(self, *args, **options):
        modules_dir = Path(getattr(settings, "MODULES_DIR", settings.BASE_DIR / "modules"))
        if not modules_dir.exists():
            self.stdout.write(self.style.WARNING(f"No existe MODULES_DIR: {modules_dir}"))
            return

        active_names: list[str] = []
        scanned = 0
        errors = 0

        for child in modules_dir.iterdir():
            if not child.is_dir():
                continue
            meta_path = child / "__meta__.py"
            if not meta_path.exists():
                continue

            scanned += 1
            try:
                data = parse_meta_file(meta_path)
                manifest = ManifestSchema.model_validate(data)
            except ManifestError as e:
                errors += 1
                self.stdout.write(self.style.WARNING(f"✗ {child.name}: {e}"))
                continue

            active_names.append(manifest.technical_name)
            ModuleCatalogItem.objects.update_or_create(
                technical_name=manifest.technical_name,
                defaults={
                    "version": manifest.version,
                    "source": data.get("source"),
                    "installed_path": str(child.resolve()),
                    "installed_at": timezone.now(),
                    "status": "active",
                    "is_active": True,
                    "django_app": data.get("django_app"),
                    "admin_menu": data.get("admin_menu"),
                },
            )

        qs = ModuleCatalogItem.objects.exclude(technical_name__in=active_names) if active_names else ModuleCatalogItem.objects.all()
        qs.update(status="inactive", is_active=False)

        self.stdout.write(
            self.style.SUCCESS(
                f"Sync completado. Escaneados: {scanned}. "
                f"Activos: {len(active_names)}. Errores: {errors}."
            )
        )
