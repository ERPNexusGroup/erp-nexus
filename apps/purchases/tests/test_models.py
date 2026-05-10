"""
Tests básicos para purchases module — placeholder.
"""
from django.test import TestCase


class PurchasesModuleTestCase(TestCase):
    """Test suite para el módulo purchases."""

    def test_module_imports(self):
        """El módulo se puede importar correctamente."""
        from apps.purchases import __version__, models
        self.assertIsNotNone(__version__)
