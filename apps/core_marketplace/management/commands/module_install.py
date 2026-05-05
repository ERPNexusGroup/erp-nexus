# Management command: module_install
# Emula: nexus install <path> --target erp
from django.core.management.base import BaseCommand, CommandError
from pathlib import Path
from django.utils import timezone
from apps.core_marketplace.models import EnabledModule, ModuleCatalogItem
from apps.core_marketplace.activation import write_modules_enabled
from apps.core_marketplace.manifest import parse_meta_file, ManifestError


class Command(BaseCommand):
    help = "Instala un módulo desde directorio local (equivalente a 'nexus install')"

    def add_arguments(self, parser):
        parser.add_argument("path", help="Ruta al directorio del módulo (contiene __meta__.py)")
        parser.add_argument(
            "--name",
            help="Nombre técnico (si no se detecta de __meta__.py)"
        )
        parser.add_argument(
            "--enable-only",
            action="store_true",
            help="Solo activar módulo ya existente en catalog (no rescanear)"
        )

    def handle(self, *args, **options):
        module_path = Path(options["path"]).resolve()

        if not module_path.exists():
            raise CommandError(f"Directorio no existe: {module_path}")

        meta_path = module_path / "__meta__.py"
        if not meta_path.exists():
            raise CommandError(f"No encuentra __meta__.py en {module_path}")

        # 1. Parse metadata
        try:
            data = parse_meta_file(meta_path)
            from apps.core_marketplace.manifest import ManifestSchema
            manifest = ManifestSchema.model_validate(data)
        except ManifestError as e:
            raise CommandError(f"Error en __meta__.py: {e}")

        technical_name = options.get("name") or manifest.technical_name
        django_app = data.get("django_app", f"modules.{technical_name}")
        display_name = data.get("display_name", technical_name)

        self.stdout.write(f"📦 Instalando módulo: {display_name} v{manifest.version}")
        self.stdout.write(f"   Technical name: {technical_name}")
        self.stdout.write(f"   Django app: {django_app}")

        # 2. Registrar/actualizar en catálogo (ModuleCatalogItem)
        catalog_entry, created_cat = ModuleCatalogItem.objects.update_or_create(
            technical_name=technical_name,
            defaults={
                "version": manifest.version,
                "source": "local",
                "installed_path": str(module_path),
                "django_app": django_app,
                "status": "active",
                "is_active": True,
                "admin_menu": data.get("admin_menu"),
            },
        )
        action = "Creado" if created_cat else "Actualizado"
        self.stdout.write(self.style.SUCCESS(f"✅ Catálogo: {action}"))

        # 3. Activar módulo (EnabledModule)
        enabled, created_en = EnabledModule.objects.get_or_create(
            technical_name=technical_name,
            defaults={
                "django_app": django_app,
                "status": "active",
            },
        )
        if not created_en:
            enabled.status = "active"
            enabled.save()
            self.stdout.write(self.style.WARNING(f"⚠️  Módulo ya estaba activo, re-activado"))
        else:
            self.stdout.write(self.style.SUCCESS(f"✅ Activado en EnabledModule"))

        # 4. Generar modules_enabled.py
        write_modules_enabled()
        self.stdout.write(self.style.SUCCESS("✅ modules_enabled.py actualizado"))

        # 5. Instrucciones siguientes
        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS("🎉 Módulo instalado!"))
        self.stdout.write("")
        self.stdout.write("Próximos pasos:")
        self.stdout.write(f"  1. Aplicar migraciones:")
        self.stdout.write(f"     uv run python manage.py makemigrations {django_app.split('.')[-1]}")
        self.stdout.write(f"     uv run python manage.py migrate")
        self.stdout.write(f"  2. Reiniciar servidor Django")
        self.stdout.write(f"  3. Verificar en admin: Módulo aparece en catálogo")
        self.stdout.write("")
        self.stdout.write(f"📝 Para desinstalar: python manage.py module_uninstall {technical_name}")
