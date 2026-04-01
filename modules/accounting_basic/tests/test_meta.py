"""Tests para accounting_basic."""
from pathlib import Path
from sdk import ComponentValidator


def test_meta_is_valid():
    """Verifica que __meta__.py del módulo es válido."""
    validator = ComponentValidator()
    meta = validator.validate_component(Path(__file__).parent.parent)
    assert meta.technical_name == "accounting_basic"
    assert meta.version == "0.1.0"
    assert meta.component_type == "module"
