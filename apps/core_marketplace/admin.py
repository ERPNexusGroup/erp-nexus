# Admin de Marketplace — Mejorado con Jazzmin actions y UI estilo ERPNext.
from django.contrib import admin
from django.db import models
from django.http import HttpResponseRedirect
from django.urls import path
from django.utils.html import format_html

from .models import EnabledModule, ModuleCatalogItem, ModuleDownload, ModuleRegistry, ModuleLicense


# ═══════════════════════════════════════════════════════════════════════
# ModuleCatalogItem — Catálogo de módulos
# ═══════════════════════════════════════════════════════════════════════
@admin.register(ModuleCatalogItem)
class ModuleCatalogItemAdmin(admin.ModelAdmin):
    """Admin: catálogo de módulos disponibles en marketplace."""
    jazzmin_simple = ["mark_inactive_action"]

    list_display = (
        "technical_name",
        "display_name",
        "version",
        "module_type",
        "is_licensed",
        "license_required",
        "price_monthly",
        "price_yearly",
        "trial_days",
        "installed",
        "actions_buttons",
    )
    list_filter = ("module_type", "is_licensed", "license_required", "status", "is_active")
    search_fields = ("technical_name", "display_name", "version", "repo_url", "django_app")
    readonly_fields = ("installed_at", "installed_path")

    fieldsets = (
        ("Basic Info", {
            "fields": ("technical_name", "display_name", "version", "module_type", "django_app")
        }),
        ("Repository", {
            "fields": ("repo_url", "installed_path", "installed_at"),
        }),
        ("Compatibility", {
            "fields": ("min_erp_version", "max_erp_version"),
        }),
        ("Dependencies", {
            "fields": ("python_dependencies", "system_dependencies"),
            "classes": ("collapse",),
        }),
        ("License", {
            "fields": ("is_licensed", "license_required", "trial_days", "price_monthly", "price_yearly"),
        }),
        ("Metadata", {
            "fields": ("documentation_url", "admin_menu", "status", "is_active"),
        }),
        ("Marketplace Menu", {
            "fields": ("admin_menu_category",),
            "description": "Categoría en el menú lateral (ERPNext-style)",
        }),
    )

    # ─── Utilidades ────────────────────────────────────────────────────
    def installed(self, obj):
        return obj.installed_at is not None
    installed.boolean = True
    installed.short_description = "Instalado"

    def actions_buttons(self, obj):
        if not obj.is_active:
            return "-"
        if obj.installed_at:
            license_badge = "🔒" if obj.is_licensed else ""
            return format_html(
                '<span style="color: green;">✓ Instalado</span> {}'
                '<a href="{}" class="button" style="margin-left: 5px;">Reinstalar</a>',
                license_badge,
                f"./install/?catalog_id={obj.id}"
            )
        else:
            lock_icon = "🔒 " if obj.is_licensed else ""
            return format_html(
                '<a href="{}" class="button" style="background: #79aec8;">{}Instalar</a>',
                f"./install/?catalog_id={obj.id}",
                lock_icon,
            )
    actions_buttons.short_description = "Acciones"

    # ─── Jazzmin Action: Desactivar seleccionados ──────────────────────
    def mark_inactive_action(self, request, queryset):
        updated = queryset.update(is_active=False, status='inactive')
        self.message_user(request, f"{updated} modules marked as inactive.")
    mark_inactive_action.short_description = "Desactivar seleccionados"

    # ─── Custom URLs (install desde admin) ─────────────────────────────
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                "<path:object_id>/install/",
                self.admin_site.admin_view(self.install_view),
                name="core_marketplace_modulecatalogitem_install",
            ),
        ]
        return custom_urls + urls

    def install_view(self, request, object_id, *args, **kwargs):
        from django.contrib import messages
        from django.core.management import call_command

        try:
            catalog_item = ModuleCatalogItem.objects.get(pk=object_id)
            if not catalog_item.repo_url:
                self.message_user(request, "Cannot install: no repo_url defined", level=messages.ERROR)
                return HttpResponseRedirect("../..")

            # Check license requirement
            license_key = request.POST.get("license_key")
            if catalog_item.license_required and not license_key:
                self.message_user(
                    request,
                    f"Module '{catalog_item.technical_name}' requires a license key. Please provide it.",
                    level=messages.WARNING,
                )
                return HttpResponseRedirect("../..")

            call_command(
                "module_install",
                catalog_item.technical_name,
                license_key=license_key or "",
                stdout=self.stdout,
                stderr=self.stderr,
            )
            self.message_user(
                request,
                f"Module '{catalog_item.technical_name}' installed successfully!",
                level=messages.SUCCESS,
            )
        except Exception as exc:
            self.message_user(request, f"Install failed: {exc}", level=messages.ERROR)

        return HttpResponseRedirect("../..")

    def stdout(self, msg):
        pass

    def stderr(self, msg):
        pass


# ═══════════════════════════════════════════════════════════════════════
# EnabledModule — Módulos instalados
# ═══════════════════════════════════════════════════════════════════════
@admin.register(EnabledModule)
class EnabledModuleAdmin(admin.ModelAdmin):
    list_display = ("technical_name", "django_app", "status", "enabled_at")
    list_filter = ("status",)
    search_fields = ("technical_name", "django_app")
    readonly_fields = ("enabled_at",)
    actions = ["uninstall_action"]

    # ─── Jazzmin Action: Desinstalar ───────────────────────────────────
    def uninstall_action(self, request, queryset):
        from django.contrib import messages
        from django.core.management import call_command

        count = 0
        for enabled in queryset:
            try:
                call_command(
                    "module_uninstall",
                    enabled.technical_name,
                    stdout=self.stdout,
                    stderr=self.stderr,
                )
                count += 1
            except Exception:
                pass
        self.message_user(request, f"Uninstalled {count} module(s).")
    uninstall_action.short_description = "Uninstall selected"

    def stdout(self, msg):
        pass

    def stderr(self, msg):
        pass


# ═══════════════════════════════════════════════════════════════════════
# ModuleDownload — Historial de descargas
# ═══════════════════════════════════════════════════════════════════════
@admin.register(ModuleDownload)
class ModuleDownloadAdmin(admin.ModelAdmin):
    list_display = ("module_name", "version", "status", "downloaded_at", "downloaded_by")
    list_filter = ("status",)
    search_fields = ("module_name", "source")
    readonly_fields = ("downloaded_at",)


# ═══════════════════════════════════════════════════════════════════════
# ModuleRegistry — Fuentes de catálogo (GitHub, JSON, etc.)
# ═══════════════════════════════════════════════════════════════════════
@admin.register(ModuleRegistry)
class ModuleRegistryAdmin(admin.ModelAdmin):
    """Admin: fuentes de catálogo (registros GitHub/JSON)."""
    list_display = (
        "name",
        "source_type",
        "url",
        "is_active",
        "is_default",
        "priority",
        "last_sync",
        "sync_button",
    )
    list_filter = ("source_type", "is_active", "is_default")
    search_fields = ("name", "url")
    readonly_fields = ("created_at", "updated_at", "cached_modules_preview")
    actions = ["sync_now_action"]

    fieldsets = (
        ("Basic", {
            "fields": ("name", "source_type", "url", "description")
        }),
        ("Flags", {
            "fields": ("is_active", "is_default", "priority"),
        }),
        ("Cache", {
            "fields": ("cached_modules_preview", "last_sync"),
            "classes": ("collapse",),
        }),
        ("Timestamps", {
            "fields": ("created_at", "updated_at"),
            "classes": ("collapse",),
        }),
    )

    # ─── cached_modules preview ──────────────────────────────────────────
    def cached_modules_preview(self, obj):
        import json
        if obj.cached_modules:
            return format_html(
                '<pre style="font-size: 11px; max-height: 200px; overflow: auto;">{}</pre>',
                json.dumps(obj.cached_modules, indent=2)[:500]
            )
        return "-"
    cached_modules_preview.short_description = "Cached Modules (preview)"

    # ─── Botón Sync en listado ─────────────────────────────────────────
    def sync_button(self, obj):
        """Botón Sync Now en listado (Jazzmin inline action)."""
        if obj.source_type != 'github':
            return "-"
        url = f"./sync/?registry_id={obj.id}"
        return format_html(
            '<a href="{}" class="button" style="background: #79aec8; padding: 4px 8px; font-size: 11px;">Sync</a>',
            url,
        )
    sync_button.short_description = "Sync"

    # ─── Last sync formateado ────────────────────────────────────────────
    def last_sync(self, obj):
        if obj.last_sync:
            return obj.last_sync.strftime('%Y-%m-%d %H:%M')
        return '-'
    last_sync.short_description = 'Last Sync'
    last_sync.admin_order_field = 'last_sync'

    # ─── Vista personalizada Sync ──────────────────────────────────────
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                "sync/",
                self.admin_site.admin_view(self.sync_view),
                name="core_marketplace_moduleregistry_sync",
            ),
        ]
        return custom_urls + urls

    def sync_view(self, request, *args, **kwargs):
        from django.contrib import messages
        from django.core.management import call_command
        from io import StringIO

        registry_id = request.GET.get("registry_id")
        try:
            registry = ModuleRegistry.objects.get(id=registry_id) if registry_id else None
            if registry and not registry.is_active:
                self.message_user(
                    request,
                    f"Registry '{registry.name}' is inactive.",
                    level=messages.WARNING,
                )
                return HttpResponseRedirect("../")

            out = StringIO()
            call_command(
                "refresh_catalog",
                registry=registry.name if registry else None,
                stdout=out,
                stderr=StringIO(),
            )
            self.message_user(
                request,
                "Catalog sync completed successfully. Check logs for details.",
                level=messages.SUCCESS,
            )
        except Exception as exc:
            self.message_user(request, f"Sync failed: {exc}", level=messages.ERROR)
        return HttpResponseRedirect("../")

    # ─── Jazzmin Action: Sync múltiples registros ───────────────────────
    def sync_now_action(self, request, queryset):
        """Jazzmin action: sync selected registries."""
        from django.contrib import messages
        from django.core.management import call_command
        from io import StringIO

        count = 0
        for registry in queryset:
            if not registry.is_active:
                continue
            try:
                out = StringIO()
                call_command(
                    "refresh_catalog",
                    registry=registry.name,
                    stdout=out,
                    stderr=StringIO(),
                )
                count += 1
            except Exception:
                pass
        self.message_user(request, f"Synced {count} registry(ies).")
    sync_now_action.short_description = "Sync from GitHub"


# ═══════════════════════════════════════════════════════════════════════
# ModuleLicense — Gestión de licencias
# ═══════════════════════════════════════════════════════════════════════
@admin.register(ModuleLicense)
class ModuleLicenseAdmin(admin.ModelAdmin):
    """Admin para gestión de licencias de módulos."""
    jazzmin_simple = ["generate_license_key_action"]

    list_display = (
        "module_name",
        "license_key_short",
        "license_type",
        "valid_until",
        "used_seats",
        "max_seats",
        "seat_usage_bar",
        "is_active",
        "is_valid_badge",
    )
    list_filter = ("license_type", "is_active", "valid_until", "module")
    search_fields = ("license_key", "module__display_name", "module__technical_name", "company__name")
    readonly_fields = ("license_key", "valid_from", "used_seats", "is_valid_badge", "seat_usage_bar")
    actions = ["revoke_license_action", "generate_license_key_action"]

    fieldsets = (
        ("License", {
            "fields": ("module", "license_key", "license_type")
        }),
        ("Validity", {
            "fields": ("valid_from", "valid_until", "is_active"),
        }),
        ("Seats", {
            "fields": ("max_seats", "used_seats", "seat_usage_bar"),
        }),
        ("Company & Features", {
            "fields": ("company", "features", "notes"),
            "classes": ("collapse",),
        }),
    )

    def module_name(self, obj):
        return obj.module.display_name or obj.module.technical_name
    module_name.short_description = "Module"
    module_name.admin_order_field = "module__display_name"

    def license_key_short(self, obj):
        return obj.license_key[:12] + "..." if len(obj.license_key) > 12 else obj.license_key
    license_key_short.short_description = "License Key"

    def is_valid_badge(self, obj):
        if obj.is_valid():
            return format_html('<span style="color: green;">✓ Valid</span>')
        return format_html('<span style="color: red;">✗ Invalid</span>')
    is_valid_badge.short_description = "Status"

    def seat_usage_bar(self, obj):
        if obj.max_seats > 0:
            pct = int((obj.used_seats / obj.max_seats) * 100)
            color = "red" if pct >= 100 else "orange" if pct >= 75 else "green"
            return format_html(
                '<div style="width: 100px; background: #eee; border: 1px solid #ccc;">'
                '<div style="width: {}%; height: 16px; background: {}; color: white; text-align: center; font-size: 10px;">'
                '{}%</div></div>',
                min(pct, 100),
                color,
                pct,
            )
        return "-"
    seat_usage_bar.short_description = "Seats"

    # ─── Action: Revocar licencia ───────────────────────────────────────
    def revoke_license_action(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f"{updated} license(s) revoked.")
    revoke_license_action.short_description = "Revoke selected licenses"

    # ─── Action: Generar license key ────────────────────────────────────
    def generate_license_key_action(self, request, queryset):
        import secrets
        from django.contrib import messages

        count = 0
        for license_obj in queryset:
            if not license_obj.license_key:
                license_obj.license_key = secrets.token_urlsafe(32)
                license_obj.save(update_fields=['license_key'])
                count += 1
        self.message_user(request, f"Generated keys for {count} license(s).")
    generate_license_key_action.short_description = "Generate license key"
