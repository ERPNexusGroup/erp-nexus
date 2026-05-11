"""
Tests E2E para Marketplace + License System.
"""
import pytest
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta

from apps.core_marketplace.models import ModuleCatalogItem, ModuleLicense, EnabledModule
from apps.core_companies.models import Company
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

# Import helpers de JWT
from apps.core_api.v1.auth import generate_tokens


pytestmark = pytest.mark.django_db


@pytest.fixture
def staff_user(django_user_model):
    return django_user_model.objects.create_user(
        username="staff_test",
        email="staff@test.com",
        password="testpass123",
        is_staff=True,
        is_superuser=True,
    )


@pytest.fixture
def api_client_auth(staff_user):
    """APIClient autenticado con JWT."""
    client = APIClient()
    tokens = generate_tokens(staff_user.id)
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {tokens['access_token']}")
    return client


@pytest.fixture
def company():
    return Company.objects.create(name="Test Company", tax_id="0991234567001")


@pytest.fixture
def optional_module():
    return ModuleCatalogItem.objects.create(
        technical_name="optional_test",
        display_name="Optional Test Module",
        version="0.1.0",
        module_type="optional",
        repo_url="https://github.com/test/optional",
        is_licensed=False,
        license_required=False,
    )


@pytest.fixture
def licensed_module():
    return ModuleCatalogItem.objects.create(
        technical_name="licensed_test",
        display_name="Licensed Test Module",
        version="1.0.0",
        module_type="optional",
        repo_url="https://github.com/test/licensed",
        is_licensed=True,
        license_required=True,
    )


@pytest.fixture
def valid_license(licensed_module, company):
    return ModuleLicense.objects.create(
        module=licensed_module,
        license_key="VALIDKEY1234567890123456789012",
        license_type="paid",
        valid_until=timezone.now() + timedelta(days=365),
        max_seats=5,
        used_seats=1,
        company=company,
        is_active=True,
    )


@pytest.fixture
def expired_license(licensed_module):
    return ModuleLicense.objects.create(
        module=licensed_module,
        license_key="EXPIREDKEY12345678901234567890",
        license_type="trial",
        valid_until=timezone.now() - timedelta(days=1),
        max_seats=2,
        used_seats=1,
        is_active=True,
    )


@pytest.fixture
def single_seat_license(licensed_module):
    return ModuleLicense.objects.create(
        module=licensed_module,
        license_key="SINGLESEAT12345678901234567890",
        license_type="paid",
        max_seats=1,
        used_seats=1,
        is_active=True,
    )


# ═══════════════════════════════════════════════════════════════════════
# Catalog Tests (API)
# ═══════════════════════════════════════════════════════════════════════

class TestMarketplaceCatalog:
    def test_list_catalog_returns_modules(self, api_client_auth, optional_module):
        url = reverse("api:list_catalog")
        resp = api_client_auth.get(url)
        assert resp.status_code == 200
        data = resp.json()
        assert any(item["technical_name"] == optional_module.technical_name for item in data)

    def test_catalog_filters_by_type(self, api_client_auth, optional_module, licensed_module):
        url = reverse("api:list_catalog") + "?module_type=optional"
        resp = api_client_auth.get(url)
        assert resp.status_code == 200
        for item in resp.json():
            assert item["module_type"] == "optional"

    def test_catalog_shows_license_info(self, api_client_auth, licensed_module):
        url = reverse("api:list_catalog")
        resp = api_client_auth.get(url)
        data = resp.json()
        lic_item = next((i for i in data if i["technical_name"] == licensed_module.technical_name), None)
        assert lic_item is not None
        assert lic_item["is_licensed"] is True
        assert lic_item["license_required"] is True


# ═══════════════════════════════════════════════════════════════════════
# Install Tests (API)
# ═══════════════════════════════════════════════════════════════════════

class TestModuleInstall:
    def test_install_optional_module_without_license(self, api_client_auth, optional_module):
        url = reverse("api:install_module", args=[optional_module.technical_name])
        resp = api_client_auth.post(url)
        assert resp.status_code == 200
        assert resp.json()["success"] is True
        assert EnabledModule.objects.filter(technical_name=optional_module.technical_name).exists()

    def test_install_licensed_module_fails_without_key(self, api_client_auth, licensed_module):
        url = reverse("api:install_module", args=[licensed_module.technical_name])
        resp = api_client_auth.post(url)
        data = resp.json()
        # El endpoint devuelve 200 incluso en errores; verificar mensaje de error
        assert data["success"] is False
        assert "license" in data["message"].lower()
        assert "key" in data["message"].lower() or "required" in data["message"].lower()

    def test_install_licensed_with_valid_key(self, api_client_auth, licensed_module, valid_license):
        url = reverse("api:install_module", args=[licensed_module.technical_name])
        resp = api_client_auth.post(url, {"license_key": valid_license.license_key})
        assert resp.json()["success"] is True
        valid_license.refresh_from_db()
        assert valid_license.used_seats == 2  # se incrementa desde 0→1

    def test_install_with_expired_license_fails(self, api_client_auth, licensed_module, expired_license):
        url = reverse("api:install_module", args=[licensed_module.technical_name])
        resp = api_client_auth.post(url, {"license_key": expired_license.license_key})
        assert resp.json()["success"] is False
        assert "expired" in resp.json()["message"].lower()

    def test_install_exceeds_seat_limit_fails(self, api_client_auth, licensed_module, single_seat_license):
        url = reverse("api:install_module", args=[licensed_module.technical_name])
        resp = api_client_auth.post(url, {"license_key": single_seat_license.license_key})
        assert resp.json()["success"] is False
        assert "seat" in resp.json()["message"].lower()


# ═══════════════════════════════════════════════════════════════════════
# License API Tests
# ═══════════════════════════════════════════════════════════════════════

class TestLicenseAPI:
    def test_create_trial_license(self, api_client_auth, licensed_module):
        url = reverse("api:create_license")
        payload = {
            "module_id": licensed_module.id,
            "license_type": "trial",
            "valid_until_days": 30,
            "max_seats": 3,
        }
        resp = api_client_auth.post(url, payload, format='json')
        assert resp.status_code == 200
        data = resp.json()
        assert "trial" in data["license_type"].lower()
        assert data["max_seats"] == 3
        assert data["remaining_seats"] == 3

    def test_list_licenses(self, api_client_auth, valid_license):
        url = reverse("api:list_licenses")
        resp = api_client_auth.get(url)
        assert resp.status_code == 200
        assert len(resp.json()) >= 1

    def test_validate_license(self, api_client_auth, valid_license):
        # validate_license es pública (no requiere auth) — se mantiene sin credenciales
        url = reverse("api:validate_license", args=[valid_license.license_key])
        resp = api_client_auth.get(url)
        assert resp.status_code == 200
        assert resp.json()["valid"] is True

    def test_revoke_license(self, api_client_auth, valid_license):
        url = reverse("api:revoke_license", args=[valid_license.license_key])
        resp = api_client_auth.delete(url)
        assert resp.status_code == 200
        valid_license.refresh_from_db()
        assert valid_license.is_active is False


# ═══════════════════════════════════════════════════════════════════════
# Public Catalog Page Tests (Django views)
# ═══════════════════════════════════════════════════════════════════════

class TestPublicCatalogPage:
    def test_catalog_page_loads(self, client):
        url = reverse("core_marketplace:public_catalog")
        resp = client.get(url)
        assert resp.status_code == 200
        assert "Catálogo de Módulos" in resp.content.decode()

    def test_catalog_shows_modules(self, client, optional_module):
        url = reverse("core_marketplace:public_catalog")
        resp = client.get(url)
        assert optional_module.display_name in resp.content.decode()

    def test_catalog_search_filter(self, client, optional_module):
        url = reverse("core_marketplace:public_catalog") + f"?q={optional_module.technical_name}"
        resp = client.get(url)
        assert resp.status_code == 200
        assert optional_module.display_name in resp.content.decode()
