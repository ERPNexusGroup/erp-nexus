"""
Fixtures para tests del Marketplace.
"""
import pytest
from django.utils import timezone
from datetime import timedelta

from apps.core_marketplace.models import ModuleCatalogItem, ModuleLicense, EnabledModule
from apps.core_companies.models import Company
from rest_framework.test import APIClient


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
    from apps.core_api.v1.auth import generate_tokens
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
        used_seats=0,  # starts at 0, install consumes to 1
        company=company,
        is_active=True,
    )


@pytest.fixture
def expired_license(licensed_module):
    return ModuleLicense.objects.create(
        module=licensed_module,
        license_key="EXPIREDKEY123456789012345678",
        license_type="trial",
        valid_until=timezone.now() - timedelta(days=1),
        max_seats=3,
        used_seats=1,
        is_active=True,
    )


@pytest.fixture
def single_seat_license(licensed_module):
    return ModuleLicense.objects.create(
        module=licensed_module,
        license_key="SINGLESEAT123456789012345678",
        license_type="paid",
        max_seats=1,
        used_seats=1,
        is_active=True,
    )


@pytest.fixture
def enabled_module_factory():
    def make(**kwargs):
        return EnabledModule.objects.create(
            technical_name=kwargs.get("technical_name", "other_module"),
            django_app=kwargs.get("django_app", "other_module"),
            status="active",
        )
    return make


@pytest.fixture(autouse=True)
def mock_call_command(monkeypatch):
    """Mock de call_command para tests de marketplace (evita git clone)."""
    from django.core.management.base import CommandError

    def fake_call_command(command_name, *args, **kwargs):
        if command_name == "module_install":
            technical_name = args[0]
            license_key = kwargs.get("license_key") or ""
            from apps.core_marketplace.models import ModuleCatalogItem, EnabledModule, ModuleLicense

            try:
                catalog_item = ModuleCatalogItem.objects.get(
                    technical_name=technical_name, is_active=True
                )
            except ModuleCatalogItem.DoesNotExist:
                raise CommandError(f"Module '{technical_name}' not found in catalog.")

            # License validation
            license_obj = None
            if catalog_item.license_required:
                if not license_key:
                    raise CommandError(
                        f"Module '{technical_name}' requires --license-key"
                    )
                try:
                    from apps.core_marketplace.utils.license import validate_license_for_module
                    license_obj = validate_license_for_module(catalog_item, license_key)
                except ValueError as exc:
                    raise CommandError(f"License error: {exc}")

            if EnabledModule.objects.filter(technical_name=technical_name).exists():
                raise CommandError(
                    f"Module '{technical_name}' already installed. Use --force to reinstall."
                )

            EnabledModule.objects.create(
                technical_name=technical_name,
                django_app=technical_name,
                status="active",
            )
            # NO modificar modules_enabled.py en tests — evita importación de apps falsas

            if license_obj:
                license_obj.used_seats += 1
                license_obj.save(update_fields=["used_seats"])

            catalog_item.touch_installed()
            catalog_item.installed_path = f"/mock/path/{technical_name}"
            catalog_item.save(update_fields=["installed_path"])
            return None

        elif command_name == "module_uninstall":
            technical_name = args[0]
            try:
                EnabledModule.objects.get(technical_name=technical_name).delete()
            except EnabledModule.DoesNotExist:
                pass
            return None

        else:
            from django.core.management import call_command as real_call_command
            return real_call_command(command_name, *args, **kwargs)

    monkeypatch.setattr("django.core.management.call_command", fake_call_command)
