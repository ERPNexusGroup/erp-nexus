"""
Vistas públicas del Marketplace — catálogo de módulos disponibles.
"""
from django.shortcuts import render
from django.db.models import Q

from apps.core_marketplace.models import ModuleCatalogItem


def public_catalog(request):
    """
    Página pública del catálogo de módulos.

    Muestra todos los módulos activos con su información de licencia y precio.
    Solo staff puede ver botón de instalar.
    """
    query = request.GET.get("q", "")
    module_type = request.GET.get("type", "")
    licensed_only = request.GET.get("licensed", "")

    modules = ModuleCatalogItem.objects.filter(is_active=True).order_by("module_type", "technical_name")

    # Filtros
    if query:
        modules = modules.filter(
            Q(technical_name__icontains=query) |
            Q(display_name__icontains=query) |
            Q(description__icontains=query)
        )

    if module_type:
        modules = modules.filter(module_type=module_type)

    if licensed_only == "1":
        modules = modules.filter(is_licensed=True)

    # Agrupación por tipo
    grouped = {}
    for m in modules:
        tipo = m.get_module_type_display()
        grouped.setdefault(tipo, []).append(m)

    context = {
        "grouped_modules": grouped,
        "total_modules": modules.count(),
        "is_staff": request.user.is_staff if request.user.is_authenticated else False,
        "search_query": query,
        "selected_type": module_type,
        "licensed_only": licensed_only,
    }
    return render(request, "core_marketplace/catalog_public.html", context)
