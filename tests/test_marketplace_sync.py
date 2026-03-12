from pathlib import Path
from tempfile import TemporaryDirectory

from django.core.management import call_command
from django.test import TestCase, override_settings

from apps.core_marketplace.manifest import ManifestError, load_and_validate_manifest
from apps.core_marketplace.models import ModuleCatalogItem


MIN_META = """technical_name = "billing"
display_name = "Billing"
component_type = "module"
package_type = "extension"
python = ">=3.11"
erp_version = ">=0.1.0"
version = "0.1.0"
"""


class ManifestParserTestCase(TestCase):
    def test_manifest_parser_valid_and_invalid(self):
        with TemporaryDirectory() as tmp:
            meta_path = Path(tmp) / "__meta__.py"
            meta_path.write_text(MIN_META, encoding="utf-8")
            manifest = load_and_validate_manifest(meta_path)
            self.assertEqual(manifest.technical_name, "billing")
            self.assertEqual(manifest.version, "0.1.0")

            meta_path.write_text('technical_name = f"bad"\n', encoding="utf-8")
            with self.assertRaises(ManifestError):
                load_and_validate_manifest(meta_path)


class SyncModulesCommandTestCase(TestCase):
    def _write_module(self, modules_dir: Path, name: str, content: str) -> Path:
        mod_dir = modules_dir / name
        mod_dir.mkdir(parents=True, exist_ok=True)
        (mod_dir / "__meta__.py").write_text(content, encoding="utf-8")
        return mod_dir

    def test_sync_modules_registers_and_marks_inactive(self):
        with TemporaryDirectory() as tmp:
            modules_dir = Path(tmp)
            mod_dir = self._write_module(modules_dir, "billing", MIN_META)

            with override_settings(MODULES_DIR=modules_dir):
                call_command("sync_modules")

                item = ModuleCatalogItem.objects.get(technical_name="billing")
                self.assertEqual(item.status, "active")
                self.assertTrue(item.is_active)
                self.assertEqual(item.installed_path, str(mod_dir.resolve()))

                # Remove module and resync
                for child in mod_dir.iterdir():
                    child.unlink()
                mod_dir.rmdir()

                call_command("sync_modules")

                item.refresh_from_db()
                self.assertEqual(item.status, "inactive")
                self.assertFalse(item.is_active)
