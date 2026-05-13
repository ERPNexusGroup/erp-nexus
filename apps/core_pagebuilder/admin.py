from django.contrib import admin
from django.utils.html import format_html
from .models import Page, Component


@admin.register(Page)
class PageAdmin(admin.ModelAdmin):
    list_display = ["title", "slug", "status", "component_count", "updated_at"]
    list_filter = ["status"]
    search_fields = ["title", "slug"]
    prepopulated_fields = {"slug": ("title",)}
    readonly_fields = ["created_at", "updated_at", "published_at"]

    fieldsets = (
        (None, {
            "fields": ("title", "slug", "description", "status")
        }),
        ("Layout", {
            "fields": ("layout",),
            "classes": ("collapse",),
            "description": "Editar layout JSON (usa el validador de schema)"
        }),
        ("SEO", {
            "fields": ("meta_title", "meta_description")
        }),
        ("Metadata", {
            "fields": ("created_by", "created_at", "updated_at", "published_at"),
            "classes": ("collapse",),
        }),
    )

    def component_count(self, obj):
        return obj.component_count
    component_count.short_description = "Componentes"

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context['pagebuilder_info'] = {
            'components_count': Component.objects.filter(is_active=True).count(),
            'total_pages': Page.objects.count(),
            'published_pages': Page.objects.filter(status='published').count(),
        }
        return super().changelist_view(request, extra_context)

    def change_view(self, request, object_id, form_url='', extra_context=None):
        extra_context = extra_context or {}
        page = self.get_object(request, object_id)
        if page:
            extra_context['preview_url'] = f"/pages/{page.slug}/"
        return super().change_view(request, object_id, form_url, extra_context)


@admin.register(Component)
class ComponentAdmin(admin.ModelAdmin):
    list_display = ["name", "component_type", "is_active"]
    list_filter = ["component_type", "is_active"]
    search_fields = ["name"]
    readonly_fields = ["created_at"]

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        # Ordenar por tipo luego por nombre
        return qs.order_by('component_type', 'name')

