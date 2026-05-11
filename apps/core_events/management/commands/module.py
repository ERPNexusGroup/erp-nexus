"""
manage.py module — Gestión de módulos (list, info, update).
"""
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from apps.core_marketplace.models import ModuleCatalogItem
from apps.core_marketplace.manifest import load_and_validate_manifest, ManifestError


class Command(BaseCommand):
    help = "Gestión de módulos ERP Nexus (list, info)."

    def add_arguments(self, parser):
        subparsers = parser.add_subparsers(dest="subcommand", required=True)

        # list
        subparsers.add_parser("list", help="Lista módulos instalados")

        # info
        info_parser = subparsers.add_parser("info", help="Info de un módulo")
        info_parser.add_argument("technical_name")

        # sync
        subparsers.add_parser("sync", help="Sincronizar filesystem con DB")

    def handle(self, *args, **options):
        subcommand = options["subcommand"]
        if subcommand == "list":
            self._list_modules()
        elif subcommand == "info":
            self._module_info(options["technical_name"])
        elif subcommand == "sync":
            self._sync_modules()

    def _list_modules(self):
        modules = ModuleCatalogItem.objects.all().order_by("technical_name")

        if not modules.exists():
            self.stdout.write("No hay módulos instalados.")
            return

        self.stdout.write(f"\n{'Nombre':<30} {'Versión':<10} {'Estado':<10} {'App Django':<30}")
        self.stdout.write("-" * 80)

        for m in modules:
            status_icon = "✅" if m.is_active else "❌"
            django_app = m.django_app or "—"
            self.stdout.write(
                f"{m.technical_name:<30} {m.version:<10} {status_icon} {m.status:<7} {django_app:<30}"
            )

        self.stdout.write(f"\nTotal: {modules.count()} módulos")

    def _module_info(self, name: str):
        module = ModuleCatalogItem.objects.filter(technical_name=name).first()
        if not module:
            raise CommandError(f"Módulo no encontrado: {name}")

        # Leer metadata actual del filesystem
        modules_dir = Path(getattr(settings, "MODULES_DIR", settings.BASE_DIR / "modules"))
        meta_path = modules_dir / name / "__meta__.py"

        self.stdout.write(f"\n📦 {module.technical_name}")
        self.stdout.write(f"   Versión:       {module.version}")
        self.stdout.write(f"   Estado:        {'✅ Activo' if module.is_active else '❌ Inactivo'}")
        self.stdout.write(f"   Django App:    {module.django_app or '—'}")
        self.stdout.write(f"   Instalado:     {module.installed_at}")
        self.stdout.write(f"   Ruta:          {module.installed_path or '—'}")
        self.stdout.write(f"   Fuente:        {module.source or '—'}")

        if meta_path.exists():
            try:
                manifest = load_and_validate_manifest(meta_path)
                self.stdout.write(f"\n   📋 Metadata actual:")
                self.stdout.write(f"      Display:    {manifest.display_name if hasattr(manifest, 'display_name') else '—'}")
                self.stdout.write(f"      Type:       {manifest.component_type}")
                self.stdout.write(f"      Python:     {manifest.python}")
                self.stdout.write(f"      ERP:        {manifest.erp_version}")
            except ManifestError:
                self.stdout.write(self.style.WARNING("\n   ⚠ Error leyendo metadata actual"))
        else:
            self.stdout.write(self.style.WARNING("\n   ⚠ __meta__.py no encontrado en filesystem"))

    def _sync_modules(self):
        """Sincroniza módulos del filesystem con la DB."""
        modules_dir = Path(getattr(settings, "MODULES_DIR", settings.BASE_DIR / "modules"))

        if not modules_dir.exists():
            self.stdout.write(self.style.WARNING(f"No existe MODULES_DIR: {modules_dir}"))
            return

        active_names = []
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
                manifest = load_and_validate_manifest(meta_path)
            except ManifestError as e:
                errors += 1
                self.stdout.write(self.style.WARNING(f"✗ {child.name}: {e}"))
                continue

            active_names.append(manifest.technical_name)
            ModuleCatalogItem.objects.update_or_create(
                technical_name=manifest.technical_name,
                defaults={
                    "version": manifest.version,
                    "installed_path": str(child.resolve()),
                    "installed_at": timezone.now(),
                    "status": "active",
                    "is_active": True,
                    "django_app": manifest.django_app,
                },
            )

        # Marcar como inactivos los que ya no están en filesystem
        if active_names:
            ModuleCatalogItem.objects.exclude(technical_name__in=active_names).update(
                status="inactive", is_active=False
            )

        self.stdout.write(self.style.SUCCESS(
            f"Sync completado. Escaneados: {scanned}. "
            f"Activos: {len(active_names)}. Errores: {errors}."
        ))
