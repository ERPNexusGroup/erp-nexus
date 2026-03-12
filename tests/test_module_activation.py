from pathlib import Path
from tempfile import TemporaryDirectory

from django.conf import settings
from django.core.management import call_command
from django.test import TestCase

from apps.core_marketplace.models import EnabledModule, ModuleCatalogItem


class ModuleActivationTestCase(TestCase):
    def test_enable_disable_generates_modules_file(self):
        ModuleCatalogItem.objects.create(
            technical_name="demo_mod",
            version="0.1.0",
            django_app="apps.demo_mod",
        )

        with TemporaryDirectory() as tmp:
            base_dir = Path(tmp)
            original_base = settings.BASE_DIR
            settings.BASE_DIR = base_dir
            try:
                call_command("enable_module", "demo_mod")
                file_path = base_dir / "erp_nexus" / "modules_enabled.py"
                content = file_path.read_text(encoding="utf-8")
                self.assertIn("apps.demo_mod", content)
                self.assertTrue(EnabledModule.objects.filter(technical_name="demo_mod", status="active").exists())

                call_command("disable_module", "demo_mod")
                content = file_path.read_text(encoding="utf-8")
                self.assertNotIn("apps.demo_mod", content)
            finally:
                settings.BASE_DIR = original_base
