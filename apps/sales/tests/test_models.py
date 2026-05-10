"""
Tests básicos para sales module — placeholder.
"""
from django.test import TestCase


class SalesModuleTestCase(TestCase):
    """Test suite para el módulo sales."""

    def test_module_imports(self):
        """El módulo se puede importar correctamente."""
        from apps.sales import __version__, models, api
        self.assertIsNotNone(__version__)

    def test_quote_creation(self):
        """Creación básica de Quote."""
        from apps.sales.models import Quote
        self.assertEqual(Quote.objects.count(), 0)
