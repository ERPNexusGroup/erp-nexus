"""
manage.py install_module — Instala un módulo en el ERP.

Fuentes soportadas:
  - Directorio local:   manage.py install_module ./mi_modulo
  - Repositorio Git:    manage.py install_module --git https://github.com/org/modulo
  - Paquete .npkg/zip:  manage.py install_module --package ./modulo-0.1.0.npkg
"""
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from apps.core_marketplace.models import ModuleCatalogItem
from apps.core_marketplace.manifest import load_and_validate_manifest, ManifestError


class Command(BaseCommand):
    help = "Instala un módulo ERP Nexus desde directorio, git o paquete."

    def add_arguments(self, parser):
        parser.add_argument(
            "path",
            nargs="?",
            help="Ruta al directorio del módulo",
        )
        parser.add_argument(
            "--git",
            dest="git_url",
            help="URL del repositorio git del módulo",
        )
        parser.add_argument(
            "--package",
            dest="package_path",
            help="Ruta al paquete .npkg o .zip del módulo",
        )
        parser.add_argument(
            "--force",
            action="store_true",
            help="Forzar reinstalación si ya existe",
        )

    def handle(self, *args, **options):
        path = options.get("path")
        git_url = options.get("git_url")
        package_path = options.get("package_path")
        force = options.get("force", False)

        # Validar que se proporcionó una fuente
        sources = [s for s in [path, git_url, package_path] if s]
        if len(sources) == 0:
            raise CommandError("Especifica una fuente: directorio, --git o --package")
        if len(sources) > 1:
            raise CommandError("Especifica solo UNA fuente: directorio, --git o --package")

        modules_dir = Path(getattr(settings, "MODULES_DIR", settings.BASE_DIR / "modules"))
        modules_dir.mkdir(parents=True, exist_ok=True)

        # Resolver fuente a directorio temporal
        temp_dir = None
        try:
            if git_url:
                source_dir = self._clone_git(git_url)
                temp_dir = source_dir
            elif package_path:
                source_dir = self._extract_package(Path(package_path))
                temp_dir = source_dir
            else:
                source_dir = Path(path).resolve()
                if not source_dir.is_dir():
                    raise CommandError(f"No es un directorio: {path}")

            # Validar metadata
            meta_path = source_dir / "__meta__.py"
            if not meta_path.exists():
                raise CommandError(f"No se encontró __meta__.py en {source_dir}")

            try:
                manifest = load_and_validate_manifest(meta_path)
            except ManifestError as e:
                raise CommandError(f"Metadata inválida: {e}")

            name = manifest.technical_name
            target_dir = modules_dir / name

            # Verificar si ya existe
            if target_dir.exists() and not force:
                raise CommandError(
                    f"Módulo '{name}' ya instalado. Usa --force para reinstalar"
                )

            # Copiar al destino
            if target_dir.exists():
                shutil.rmtree(target_dir)

            self.stdout.write(f"📦 Instalando: {name} v{manifest.version}")
            shutil.copytree(source_dir, target_dir, dirs_exist_ok=True)

            # Registrar en DB
            ModuleCatalogItem.objects.update_or_create(
                technical_name=name,
                defaults={
                    "version": manifest.version,
                    "source": git_url or str(source_dir),
                    "installed_path": str(target_dir),
                    "installed_at": timezone.now(),
                    "status": "active",
                    "is_active": True,
                    "django_app": manifest.django_app,
                },
            )

            # Ejecutar migraciones si tiene django_app
            if manifest.django_app:
                self.stdout.write(f"🔄 Ejecutando migraciones para {manifest.django_app}...")
                try:
                    from django.core.management import call_command
                    call_command("migrate", manifest.django_app, verbosity=0)
                except Exception as e:
                    self.stdout.write(self.style.WARNING(
                        f"⚠ Migraciones fallaron (puede requerir setup manual): {e}"
                    ))

            self.stdout.write(self.style.SUCCESS(
                f"✅ {name} v{manifest.version} instalado en {target_dir}"
            ))

        finally:
            if temp_dir and temp_dir.exists():
                shutil.rmtree(temp_dir)

    def _clone_git(self, url: str) -> Path:
        """Clona un repositorio git y retorna el directorio."""
        temp_dir = Path(tempfile.mkdtemp(prefix="nexus_module_"))
        self.stdout.write(f"📥 Clonando: {url}")

        try:
            subprocess.run(
                ["git", "clone", "--depth", "1", url, str(temp_dir)],
                check=True,
                capture_output=True,
                text=True,
            )
        except subprocess.CalledProcessError as e:
            raise CommandError(f"Error clonando repositorio: {e.stderr}")

        return temp_dir

    def _extract_package(self, package_path: Path) -> Path:
        """Extrae un paquete .npkg/.zip y retorna el directorio."""
        if not package_path.exists():
            raise CommandError(f"Paquete no encontrado: {package_path}")

        temp_dir = Path(tempfile.mkdtemp(prefix="nexus_module_"))
        self.stdout.write(f"📦 Extrayendo: {package_path}")

        try:
            with zipfile.ZipFile(package_path, "r") as zf:
                zf.extractall(temp_dir)
        except zipfile.BadZipFile:
            raise CommandError(f"Paquete inválido: {package_path}")

        # Si el zip contiene un solo directorio, entrar a él
        items = list(temp_dir.iterdir())
        if len(items) == 1 and items[0].is_dir():
            return items[0]

        return temp_dir
