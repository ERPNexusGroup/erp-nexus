"""
Tests básicos para print_manager module — placeholder.
"""
from django.test import TestCase


class PrintManagerModuleTestCase(TestCase):
    """Test suite para el módulo print_manager."""

    def test_module_imports(self):
        """El módulo se puede importar correctamente."""
        from apps.print_manager import __version__, models
        self.assertIsNotNone(__version__)
