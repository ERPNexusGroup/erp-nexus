"""
Router de marketplace — catálogo, instalación, desinstalación y licencias.
"""
from ninja import Router, Schema, Form
from typing import List, Optional

from apps.core_api.auth import JWTAuth
from apps.core_marketplace.models import ModuleCatalogItem, EnabledModule, ModuleDownload, ModuleLicense
from apps.core_marketplace.utils.module_loader import read_modules_enabled
from django.core.management import call_command

router = Router(auth=JWTAuth())
router.app_name = "marketplace"


# ─── Schemas ──────────────────────────────────────────────────────────
class ModuleCatalogOut(Schema):
    technical_name: str
    display_name: str
    description: Optional[str] = ''
    version: str
    module_type: str
    repo_url: Optional[str]
    min_erp_version: str
    max_erp_version: Optional[str]
    python_dependencies: dict
    system_dependencies: dict
    documentation_url: Optional[str]
    is_licensed: bool
    license_required: bool
    trial_days: int
    price_monthly: Optional[float]
    price_yearly: Optional[float]
    is_installed: bool
    installed_at: Optional[str]


class EnabledModuleOut(Schema):
    technical_name: str
    django_app: str
    status: str
    enabled_at: str


class LicenseCreate(Schema):
    module_id: int
    license_type: str = "free"
    valid_until_days: Optional[int] = None  # for trial
    max_seats: int = 1
    company_id: Optional[int] = None


class LicenseOut(Schema):
    id: int
    module_name: str
    license_key: str
    license_type: str
    valid_from: str
    valid_until: Optional[str]
    max_seats: int
    used_seats: int
    remaining_seats: int
    is_active: bool
    is_valid: bool


class MessageResponse(Schema):
    message: str
    success: bool


# ─── GET /api/v1/marketplace/catalog/ ─────────────────────────────────
@router.get("/catalog", response=List[ModuleCatalogOut])
def list_catalog(request, module_type: Optional[str] = None, installed: Optional[bool] = None, q: Optional[str] = None):
    qs = ModuleCatalogItem.objects.filter(is_active=True)
    if module_type:
        qs = qs.filter(module_type=module_type)
    if installed is True:
        qs = qs.filter(installed_at__isnull=False)
    elif installed is False:
        qs = qs.filter(installed_at__isnull=True)
    if q:
        qs = qs.filter(description__icontains=q) | qs.filter(display_name__icontains=q) | qs.filter(technical_name__icontains=q)

    enabled_apps = read_modules_enabled()
    installed_technical_names = set(
        EnabledModule.objects.values_list("technical_name", flat=True)
    )

    result = []
    for item in qs:
        is_installed = item.technical_name in installed_technical_names or item.installed_at is not None
        result.append(ModuleCatalogOut(
            technical_name=item.technical_name,
            display_name=item.display_name or item.technical_name,
            description=item.description or '',
            version=item.version,
            module_type=item.module_type,
            repo_url=item.repo_url,
            min_erp_version=item.min_erp_version,
            max_erp_version=item.max_erp_version,
            python_dependencies=item.python_dependencies,
            system_dependencies=item.system_dependencies,
            documentation_url=item.documentation_url,
            is_licensed=item.is_licensed,
            license_required=item.license_required,
            trial_days=item.trial_days,
            price_monthly=float(item.price_monthly) if item.price_monthly else None,
            price_yearly=float(item.price_yearly) if item.price_yearly else None,
            is_installed=is_installed,
            installed_at=str(item.installed_at) if item.installed_at else None,
        ))
    return result


# ─── POST /api/v1/marketplace/{name}/install/ ─────────────────────────
@router.post("/{technical_name}/install", response=MessageResponse)
def install_module(request, technical_name: str, license_key: Optional[str] = Form(None)):
    try:
        call_command("module_install", technical_name, license_key=license_key or "")
        return {"message": f"Module '{technical_name}' installed successfully", "success": True}
    except Exception as exc:
        return {"message": f"Install failed: {str(exc)}", "success": False}


# ─── POST /api/v1/marketplace/{name}/uninstall/ ───────────────────────
@router.post("/{technical_name}/uninstall", response=MessageResponse)
def uninstall_module(request, technical_name: str):
    try:
        call_command("module_uninstall", technical_name)
        return {"message": f"Module '{technical_name}' uninstalled successfully", "success": True}
    except Exception as exc:
        return {"message": f"Uninstall failed: {str(exc)}", "success": False}


# ─── GET /api/v1/marketplace/installed/ ───────────────────────────────
@router.get("/installed", response=List[EnabledModuleOut])
def list_installed(request):
    modules = EnabledModule.objects.all().order_by("-enabled_at")
    return [
        EnabledModuleOut(
            technical_name=m.technical_name,
            django_app=m.django_app,
            status=m.status,
            enabled_at=str(m.enabled_at),
        )
        for m in modules
    ]


# ─── GET /api/v1/marketplace/status ───────────────────────────────────
@router.get("/status")
def marketplace_status(request):
    installed = EnabledModule.objects.count()
    catalog = ModuleCatalogItem.objects.filter(is_active=True).count()
    return {
        "installed_modules": installed,
        "available_in_catalog": catalog,
        "marketplace_ready": True,
    }


# ═══════════════════════════════════════════════════════════════════════
# License Endpoints
# ═══════════════════════════════════════════════════════════════════════

# ─── POST /api/v1/marketplace/licenses/ ─────────────────────────────────
@router.post("/licenses", response=LicenseOut)
def create_license(request, payload: LicenseCreate):
    from datetime import timedelta
    from django.utils import timezone
    import secrets
    import string

    try:
        module = ModuleCatalogItem.objects.get(id=payload.module_id, is_active=True)
    except ModuleCatalogItem.DoesNotExist:
        return {"message": "Module not found", "success": False}

    # Generate unique key
    alphabet = string.ascii_letters + string.digits
    key = ''.join(secrets.choice(alphabet) for _ in range(32))

    valid_until = None
    if payload.valid_until_days and payload.license_type == 'trial':
        valid_until = timezone.now() + timedelta(days=payload.valid_until_days)

    license_obj = ModuleLicense.objects.create(
        module=module,
        license_key=key,
        license_type=payload.license_type,
        valid_until=valid_until,
        max_seats=payload.max_seats,
        company_id=payload.company_id,
        features={"type": payload.license_type},
    )

    return LicenseOut(
        id=license_obj.id,
        module_name=module.technical_name,
        license_key=license_obj.license_key,
        license_type=license_obj.get_license_type_display(),
        valid_from=str(license_obj.valid_from),
        valid_until=str(license_obj.valid_until) if license_obj.valid_until else None,
        max_seats=license_obj.max_seats,
        used_seats=license_obj.used_seats,
        remaining_seats=license_obj.remaining_seats,
        is_active=license_obj.is_active,
        is_valid=license_obj.is_valid,
    )


# ─── GET /api/v1/marketplace/licenses/ ─────────────────────────────────
@router.get("/licenses", response=List[LicenseOut])
def list_licenses(request, module: Optional[str] = None, active_only: bool = False):
    qs = ModuleLicense.objects.all()
    if module:
        qs = qs.filter(module__technical_name=module)
    if active_only:
        qs = qs.filter(is_active=True)

    result = []
    for lic in qs:
        result.append(LicenseOut(
            id=lic.id,
            module_name=lic.module.technical_name,
            license_key=f"{lic.license_key[:12]}...",
            license_type=lic.get_license_type_display(),
            valid_from=str(lic.valid_from),
            valid_until=str(lic.valid_until) if lic.valid_until else None,
            max_seats=lic.max_seats,
            used_seats=lic.used_seats,
            remaining_seats=lic.remaining_seats,
            is_active=lic.is_active,
            is_valid=lic.is_valid,
        ))
    return result


# ─── GET /api/v1/marketplace/licenses/{key}/validate ───────────────────
@router.get("/licenses/{key}/validate")
def validate_license(request, key: str):
    try:
        lic = ModuleLicense.objects.get(license_key=key, is_active=True)
        return {
            "valid": lic.is_valid,
            "module": lic.module.technical_name,
            "license_type": lic.license_type,
            "remaining_seats": lic.remaining_seats,
            "valid_until": str(lic.valid_until) if lic.valid_until else None,
        }
    except ModuleLicense.DoesNotExist:
        return {"valid": False, "error": "License not found or inactive"}


# ─── DELETE /api/v1/marketplace/licenses/{key}/ ────────────────────────
@router.delete("/licenses/{key}")
def revoke_license(request, key: str):
    try:
        lic = ModuleLicense.objects.get(license_key=key)
        lic.is_active = False
        lic.save(update_fields=['is_active'])
        return {"message": f"License {key[:12]}... revoked", "success": True}
    except ModuleLicense.DoesNotExist:
        return {"message": "License not found", "success": False}


# ─── Helper para capturar output ──────────────────────────────────────
class StdoutCapture:
    def write(self, msg):
        pass
    def flush(self):
        pass
