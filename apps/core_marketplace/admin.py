from django.contrib import admin
from django.db import models
from django.http import HttpResponseRedirect
from django.urls import path
from django.utils.html import format_html

from .models import EnabledModule, ModuleCatalogItem, ModuleDownload, ModuleRegistry, ModuleLicense


@admin.register(ModuleCatalogItem)
class ModuleCatalogItemAdmin(admin.ModelAdmin):
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
    )

    def installed(self, obj):
        return obj.installed_at is not None
    installed.boolean = True
    installed.short_description = "Installed"

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

            call_command("module_install", catalog_item.technical_name,
                         license_key=license_key, stdout=self.stdout, stderr=self.stderr)
            self.message_user(request, f"Module '{catalog_item.technical_name}' installed successfully!", level=messages.SUCCESS)
        except Exception as exc:
            self.message_user(request, f"Install failed: {exc}", level=messages.ERROR)

        return HttpResponseRedirect("../..")

    def stdout(self, msg):
        pass

    def stderr(self, msg):
        pass


@admin.register(EnabledModule)
class EnabledModuleAdmin(admin.ModelAdmin):
    list_display = ("technical_name", "django_app", "status", "enabled_at", "uninstall_button")
    list_filter = ("status",)
    search_fields = ("technical_name", "django_app")
    readonly_fields = ("enabled_at",)

    def uninstall_button(self, obj):
        if obj.status == 'inactive':
            return "-"
        return format_html(
            '<a href="{}" class="button" style="background: #ba2121;">Desinstalar</a>',
            f"./uninstall/?module_id={obj.id}"
        )
    uninstall_button.short_description = "Desinstalar"

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                "<path:object_id>/uninstall/",
                self.admin_site.admin_view(self.uninstall_view),
                name="core_marketplace_enabledmodule_uninstall",
            ),
        ]
        return custom_urls + urls

    def uninstall_view(self, request, object_id, *args, **kwargs):
        from django.contrib import messages
        from django.core.management import call_command

        try:
            enabled = EnabledModule.objects.get(pk=object_id)
            call_command("module_uninstall", enabled.technical_name, stdout=self.stdout, stderr=self.stderr)
            self.message_user(request, f"Module '{enabled.technical_name}' uninstalled successfully!", level=messages.SUCCESS)
        except Exception as exc:
            self.message_user(request, f"Uninstall failed: {exc}", level=messages.ERROR)

        return HttpResponseRedirect("../..")

    def stdout(self, msg):
        pass


@admin.register(ModuleDownload)
class ModuleDownloadAdmin(admin.ModelAdmin):
    list_display = ("module_name", "version", "status", "downloaded_at", "downloaded_by")
    list_filter = ("status",)
    search_fields = ("module_name", "source")
    readonly_fields = ("downloaded_at",)


@admin.register(ModuleRegistry)
class ModuleRegistryAdmin(admin.ModelAdmin):
    list_display = ("name", "source_type", "url", "is_active", "is_default", "priority", "last_sync")
    list_filter = ("source_type", "is_active", "is_default")
    search_fields = ("name", "url")
    readonly_fields = ("created_at", "updated_at", "cached_modules")
    fieldsets = (
        ("Basic", {
            "fields": ("name", "source_type", "url", "description")
        }),
        ("Flags", {
            "fields": ("is_active", "is_default", "priority"),
        }),
        ("Cache", {
            "fields": ("cached_modules", "last_sync"),
            "classes": ("collapse",),
        }),
        ("Timestamps", {
            "fields": ("created_at", "updated_at"),
            "classes": ("collapse",),
        }),
    )


@admin.register(ModuleLicense)
class ModuleLicenseAdmin(admin.ModelAdmin):
    """Admin para gestion de licencias de modulos."""

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
    list_filter = ("license_type", "is_active", "module__technical_name")
    search_fields = ("license_key", "module__technical_name", "module__display_name", "company__name")
    readonly_fields = ("valid_from", "used_seats", "is_valid_badge", "seat_usage_bar")
    fieldsets = (
        ("License Info", {
            "fields": ("module", "license_key", "license_type", "is_active")
        }),
        ("Validity", {
            "fields": ("valid_from", "valid_until"),
        }),
        ("Seats", {
            "fields": ("max_seats", "used_seats", "seat_usage_bar"),
        }),
        ("Assignment", {
            "fields": ("company",),
        }),
        ("Features & Notes", {
            "fields": ("features", "notes"),
            "classes": ("collapse",),
        }),
    )
    actions = ["generate_license_key_action", "revoke_licenses"]

    def module_name(self, obj):
        return obj.module.display_name or obj.module.technical_name
    module_name.short_description = "Module"
    module_name.admin_order_field = "module__technical_name"

    def license_key_short(self, obj):
        return f"{obj.license_key[:12]}...{obj.license_key[-4:]}"
    license_key_short.short_description = "License Key"

    def seat_usage_bar(self, obj):
        if obj.max_seats == 0:
            percentage = 100
        else:
            percentage = int((obj.used_seats / obj.max_seats) * 100)
        color = "red" if percentage >= 100 else "orange" if percentage >= 80 else "green"
        return format_html(
            '<div style="width: 100px; background: #eee; border-radius: 3px;">'
            '<div style="width: {}%; height: 12px; background: {}; border-radius: 3px;"></div>'
            '</div> <span style="font-size: 0.8em;">{}/{}</span>',
            percentage, color, obj.used_seats, obj.max_seats
        )
    seat_usage_bar.short_description = "Seats"

    def is_valid_badge(self, obj):
        if obj.is_valid:
            return format_html('<span style="color: green;">✅ Valid</span>')
        return format_html('<span style="color: red;">❌ Invalid/Expired</span>')
    is_valid_badge.short_description = "Status"
    is_valid_badge.boolean = True

    def generate_license_key_action(self, request, queryset):
        """Admin action: generate unique license key."""
        import secrets
        import string

        count = 0
        for license_obj in queryset:
            alphabet = string.ascii_letters + string.digits
            key = ''.join(secrets.choice(alphabet) for _ in range(32))
            license_obj.license_key = key
            license_obj.save(update_fields=['license_key'])
            count += 1

        self.message_user(request, f"Generated license keys for {count} modules.")
    generate_license_key_action.short_description = "Generate license key"

    def revoke_licenses(self, request, queryset):
        """Admin action: revoke licenses (mark inactive)."""
        updated = queryset.update(is_active=False)
        self.message_user(request, f"Revoked {updated} licenses.")
    revoke_licenses.short_description = "Revoke selected licenses"
