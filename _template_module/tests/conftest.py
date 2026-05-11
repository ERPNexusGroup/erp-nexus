"""Fixtures compartidas para tests del módulo."""
import pytest


@pytest.fixture
def company(company_factory):
    """Company para tests."""
    return company_factory(name="Test Company")


@pytest.fixture
def user(user_factory):
    """Usuario para tests."""
    return user_factory(username="testuser")
