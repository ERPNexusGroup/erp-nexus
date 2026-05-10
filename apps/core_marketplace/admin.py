from django.contrib import admin
from django.db import models
from django.http import HttpResponseRedirect
from django.urls import path
from django.utils.html import format_html
from django.utils.safestring import mark_safe

from .models import EnabledModule, ModuleCatalogItem, ModuleDownload, ModuleRegistry


@admin.register(ModuleCatalogItem)
class ModuleCatalogItemAdmin(admin.ModelAdmin):
    list_display = (
        "technical_name",
        "display_name",
        "version",
        "module_type",
        "repo_url",
        "min_erp_version",
        "is_active",
        "installed",
        "actions_buttons",
    )
    list_filter = ("module_type", "status", "is_active")
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
            return format_html(
                '<span style="color: green;">✓ Instalado</span> '
                '<a href="{}" class="button">Reinstalar</a> ',
                f"./install/?catalog_id={obj.id}"
            )
        else:
            return format_html(
                '<a href="{}" class="button" style="background: #79aec8;">Instalar</a>',
                f"./install/?catalog_id={obj.id}"
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
        """Install a module from the catalog."""
        from django.contrib import messages
        from django.core.management import call_command

        try:
            catalog_item = ModuleCatalogItem.objects.get(pk=object_id)
            if not catalog_item.repo_url:
                self.message_user(request, "Cannot install: no repo_url defined", level=messages.ERROR)
                return HttpResponseRedirect("../..")

            # Execute module_install command
            call_command("module_install", catalog_item.technical_name, stdout=self.stdout, stderr=self.stderr)
            self.message_user(request, f"Module '{catalog_item.technical_name}' installed successfully!", level=messages.SUCCESS)
        except Exception as exc:
            self.message_user(request, f"Install failed: {exc}", level=messages.ERROR)

        return HttpResponseRedirect("../..")

    # Make stdout/stderr available for call_command
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
