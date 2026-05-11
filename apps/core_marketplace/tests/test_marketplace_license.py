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


# ═══════════════════════════════════════════════════════════════════════
# Fixtures
# ═══════════════════════════════════════════════════════════════════════

@pytest.fixture
def staff_user(django_user_model):
    return django_user_model.objects.create_user(
        username="staff",
        email="staff@example.com",
        password="pass",
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
def api_client():
    """APIClient sin autenticación (para vistas públicas)."""
    return APIClient()


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
def company():
    return Company.objects.create(name="TestCo", tax_id="1234567890")


@pytest.fixture
def valid_license(licensed_module, company):
    return ModuleLicense.objects.create(
        module=licensed_module,
        license_key="VALIDLICENSEKEY123456789012345678",
        license_type="paid",
        valid_until=timezone.now() + timedelta(days=365),
        max_seats=5,
        used_seats=0,
        company=company,
    )


@pytest.fixture
def expired_license(licensed_module, company):
    return ModuleLicense.objects.create(
        module=licensed_module,
        license_key="EXPIREDKEY123456789012345678",
        license_type="trial",
        valid_until=timezone.now() - timedelta(days=1),
        max_seats=5,
        used_seats=0,
        company=company,
    )


@pytest.fixture
def single_seat_license(licensed_module, company):
    return ModuleLicense.objects.create(
        module=licensed_module,
        license_key="SINGLESEAT123456789012345678",
        license_type="free",
        valid_until=timezone.now() + timedelta(days=30),
        max_seats=1,
        used_seats=1,
        company=company,
    )


@pytest.fixture
def staff_client(staff_user):
    """Client Django autenticado como staff (para admin views)."""
    from django.test import Client
    client = Client()
    client.force_login(staff_user)
    return client


# ═══════════════════════════════════════════════════════════════════════
# Marketplace Catalog Tests (REST API)
# ═══════════════════════════════════════════════════════════════════════

class TestMarketplaceCatalog:
    def test_list_catalog_returns_modules(self, api_client_auth, optional_module, licensed_module):
        url = reverse("api:list_catalog")
        resp = api_client_auth.get(url)
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) >= 2
        names = {item["technical_name"] for item in data}
        assert optional_module.technical_name in names
        assert licensed_module.technical_name in names

    def test_catalog_filters_by_type(self, api_client_auth, optional_module, licensed_module):
        url = reverse("api:list_catalog") + "?module_type=optional"
        resp = api_client_auth.get(url)
        assert resp.status_code == 200
        data = resp.json()
        for item in data:
            assert item["module_type"] == "optional"

    def test_catalog_shows_license_info(self, api_client_auth, licensed_module):
        url = reverse("api:list_catalog")
        resp = api_client_auth.get(url)
        assert resp.status_code == 200
        data = resp.json()
        licensed = next((i for i in data if i["technical_name"] == licensed_module.technical_name), None)
        assert licensed is not None
        assert licensed["is_licensed"] is True
        assert licensed["license_required"] is True


# ═══════════════════════════════════════════════════════════════════════
# Module Install Tests (API + Command)
# ═══════════════════════════════════════════════════════════════════════

class TestModuleInstall:
    def test_install_optional_module_without_license(self, api_client_auth, optional_module, monkeypatch):
        url = reverse("api:install_module", args=[optional_module.technical_name])
        resp = api_client_auth.post(url)
        data = resp.json()
        assert data["success"] is True
        assert EnabledModule.objects.filter(technical_name=optional_module.technical_name).exists()

    def test_install_licensed_module_fails_without_key(self, api_client_auth, licensed_module):
        url = reverse("api:install_module", args=[licensed_module.technical_name])
        resp = api_client_auth.post(url)
        data = resp.json()
        assert data["success"] is False
        assert "license" in data["message"].lower()
        assert "key" in data["message"].lower() or "required" in data["message"].lower()

    def test_install_licensed_with_valid_key(self, api_client_auth, licensed_module, valid_license):
        url = reverse("api:install_module", args=[licensed_module.technical_name])
        resp = api_client_auth.post(url, {"license_key": valid_license.license_key})
        assert resp.json()["success"] is True
        valid_license.refresh_from_db()
        assert valid_license.used_seats == 1  # se incrementa desde 0→1

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


# ═══════════════════════════════════════════════════════════════════════
# Sidebar Integration Tests (admin_menu_category + Jazzmin UI)
# ═══════════════════════════════════════════════════════════════════════

class TestSidebarIntegration:
    def test_sidebar_uses_admin_menu_category(self, staff_client):
        """Verifica que el context processor usa admin_menu_category para agrupar módulos instalados."""
        # Crear catálogo + instalaciones
        cat1 = ModuleCatalogItem.objects.create(
            technical_name="mod_ventas",
            display_name="Módulo de Ventas",
            version="1.0",
            admin_menu_category="Ventas",
        )
        cat2 = ModuleCatalogItem.objects.create(
            technical_name="mod_inventario",
            display_name="Módulo de Inventario",
            version="1.0",
            admin_menu_category="Inventario",
        )
        cat3 = ModuleCatalogItem.objects.create(
            technical_name="mod_general",
            display_name="Módulo General",
            version="1.0",
            admin_menu_category="Aplicaciones",
        )

        # Crear EnabledModule (simula módulos instalados)
        # module_install crea EnabledModule con technical_name + django_app
        EnabledModule.objects.create(
            technical_name=cat1.technical_name,
            django_app='sales',  # simula app instalada
            status='active',
        )
        EnabledModule.objects.create(
            technical_name=cat2.technical_name,
            django_app='inventory',
            status='active',
        )
        EnabledModule.objects.create(
            technical_name=cat3.technical_name,
            django_app='general',
            status='active',
        )

        # Invalidate cache manualmente
        from django.core.cache import cache
        cache.delete('admin_dashboard_metrics')
        cache.delete('jazzmin_side_menu_apps')

        # Petición al admin ejecuta context processors
        resp = staff_client.get('/admin/')
        assert resp.status_code == 200

        jazzmin_apps = resp.context.get('jazzmin_apps', [])
        assert jazzmin_apps, f'jazzmin_apps vacío, contexto: {list(resp.context.keys())}'

        labels = [app['label'] for app in jazzmin_apps]
        assert 'Ventas' in labels
        assert 'Inventario' in labels
        assert 'Aplicaciones' in labels

        ventas_app = next(a for a in jazzmin_apps if a['label'] == 'Ventas')
        assert any(m['name'] == 'Módulo de Ventas' for m in ventas_app['models'])

        inv_app = next(a for a in jazzmin_apps if a['label'] == 'Inventario')
        assert any(m['name'] == 'Módulo de Inventario' for m in inv_app['models'])

        apps_app = next(a for a in jazzmin_apps if a['label'] == 'Aplicaciones')
        assert any(m['name'] == 'Módulo General' for m in apps_app['models'])

    def test_dashboard_shows_installed_count(self, staff_client):
        # Crear catálogo + instalaciones
        for i in range(3):
            cat = ModuleCatalogItem.objects.create(
                technical_name=f"mod_{i}",
                display_name=f"Módulo {i}",
                version="1.0",
            )
            EnabledModule.objects.create(
                technical_name=cat.technical_name,
                django_app=f'app_{i}',
                status='active',
            )

        from django.core.cache import cache
        cache.delete('admin_dashboard_metrics')
        cache.delete('jazzmin_side_menu_apps')

        resp = staff_client.get('/admin/')
        assert resp.status_code == 200

        dashboard_cards = resp.context.get('dashboard_cards', {})
        assert dashboard_cards.get('active_modules') == 3
        assert dashboard_cards.get('installed_modules') == 3


# ═══════════════════════════════════════════════════════════════════════
# GitHub Registry + refresh_catalog Tests
# ═══════════════════════════════════════════════════════════════════════

class TestGitHubRegistry:
    def test_create_default_registry_on_command(self):
        """El comando refresh_catalog crea un ModuleRegistry default si no existe."""
        from django.core.management import call_command
        from apps.core_marketplace.models import ModuleRegistry

        # Asegurar que no existan registros
        ModuleRegistry.objects.all().delete()

        call_command('refresh_catalog', '--dry-run')

        # Debe crearse el registro default
        assert ModuleRegistry.objects.filter(is_default=True).exists()
        default = ModuleRegistry.objects.get(is_default=True)
        assert default.name == "GitHub Official"
        assert default.source_type == "github"
        assert default.url == "ERPNexusGroup"  # valor por defecto de GITHUB_ORG

    def test_refresh_catalog_dry_run_no_changes(self):
        """Dry run no modifica la base de datos (skip por falta de token)."""
        from django.core.management import call_command
        from apps.core_marketplace.models import ModuleCatalogItem
        from io import StringIO

        # Crear un módulo en catálogo
        ModuleCatalogItem.objects.create(
            technical_name="existing_mod",
            display_name="Existing Module",
            version="1.0",
        )

        out = StringIO()
        call_command('refresh_catalog', '--dry-run', stdout=out)

        # Sin GITHUB_TOKEN real, el comando skipea (no falla)
        # Verificar que el módulo original sigue ahí
        assert ModuleCatalogItem.objects.filter(technical_name="existing_mod").exists()
