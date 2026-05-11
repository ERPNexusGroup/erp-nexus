"""
License validation utilities for module installation.

Provides functions to validate ModuleLicense objects during install.
"""
from datetime import timedelta

from django.utils import timezone

from apps.core_marketplace.models import ModuleLicense


def validate_license_for_module(module_catalog_item, license_key=None) -> ModuleLicense:
    """
    Validate that a module can be installed given its license requirements.

    Args:
        module_catalog_item: ModuleCatalogItem instance
        license_key: Optional license key provided by user

    Returns:
        ModuleLicense instance if valid

    Raises:
        ValueError: if license is invalid, missing, or expired
    """
    # Module doesn't require license → ok
    if not module_catalog_item.license_required:
        return None

    # License key required
    if not license_key:
        raise ValueError(f"Module '{module_catalog_item.technical_name}' requires a license key")

    try:
        license_obj = ModuleLicense.objects.get(license_key=license_key, module=module_catalog_item)
    except ModuleLicense.DoesNotExist:
        raise ValueError(f"Invalid license key for module '{module_catalog_item.technical_name}'")

    # Check active
    if not license_obj.is_active:
        raise ValueError("License is inactive")

    # Check expiry
    now = timezone.now()
    if license_obj.valid_until and now > license_obj.valid_until:
        raise ValueError(f"License expired on {license_obj.valid_until.date()}")

    # Check seats available
    if license_obj.used_seats >= license_obj.max_seats:
        raise ValueError(f"License seat limit reached ({license_obj.used_seats}/{license_obj.max_seats})")

    return license_obj


def consume_license(license_obj: ModuleLicense) -> None:
    """
    Increment used_seats when a module is installed.
    Call within a transaction.
    """
    license_obj.used_seats += 1
    license_obj.save(update_fields=['used_seats'])


def release_license(license_obj: ModuleLicense) -> None:
    """
    Decrement used_seats when a module is uninstalled.
    Call within a transaction.
    """
    if license_obj.used_seats > 0:
        license_obj.used_seats -= 1
        license_obj.save(update_fields=['used_seats'])


def create_trial_license(module_catalog_item, company=None, trial_days=30) -> ModuleLicense:
    """Create a trial license for a module."""
    import secrets
    import string

    alphabet = string.ascii_letters + string.digits
    key = ''.join(secrets.choice(alphabet) for _ in range(32))

    valid_until = timezone.now() + timedelta(days=trial_days)

    return ModuleLicense.objects.create(
        module=module_catalog_item,
        license_key=key,
        license_type='trial',
        valid_until=valid_until,
        max_seats=1,
        company=company,
        features={"trial": True, "support": "community"},
    )


def is_license_valid(license_obj: ModuleLicense) -> bool:
    """Quick check if license is currently valid."""
    return license_obj.is_valid
