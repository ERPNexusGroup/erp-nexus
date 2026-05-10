"""Tests del módulo mi_modulo."""
import pytest
from django.conf import settings

pytestmark = pytest.mark.django_db


class TestExampleModel:
    """Tests for ExampleModel."""

    def test_create(self, company, user):
        """Crear ejemplo básico."""
        from modules.mi_modulo.models import ExampleModel
        obj = ExampleModel.objects.create(
            company=company,
            name="Test",
            amount=100,
            created_by=user,
        )
        assert obj.id is not None
        assert obj.company == company

    def test_calculate_total(self):
        """Test cálculo de total con IVA."""
        from modules.mi_modulo.services import calculate_total
        from decimal import Decimal
        total = calculate_total(Decimal("100.00"))
        assert total == Decimal("112.00")