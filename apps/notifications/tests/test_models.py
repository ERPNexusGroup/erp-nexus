"""
Tests básicos para notifications module — placeholder.
"""
from django.test import TestCase


class NotificationsModuleTestCase(TestCase):
    """Test suite para el módulo notifications."""

    def test_module_imports(self):
        """El módulo se puede importar correctamente."""
        from apps.notifications import __version__, models
        self.assertIsNotNone(__version__)
