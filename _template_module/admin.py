"""Admin Django para mi_modulo."""
from django.contrib import admin
from django.db.models import Count, Sum

from .models import ExampleModel


@admin.register(ExampleModel)
class ExampleModelAdmin(admin.ModelAdmin):
    """Admin personalizado para ExampleModel."""
    list_display = ["name", "company", "amount", "is_active", "created_at"]
    list_filter = ["is_active", "company"]
    search_fields = ["name", "description"]
    readonly_fields = ["created_at", "updated_at"]
    autocomplete_fields = ["company"]

    def get_queryset(self, request):
        """Filtrar por company activa del usuario."""
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(company=request.active_company)

    def save_model(self, request, obj, form, change):
        """Set company y created_by automáticamente."""
        if not change:
            obj.company = request.active_company
            obj.created_by = request.user
        obj.save()
