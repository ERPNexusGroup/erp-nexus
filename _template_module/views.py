"""Views del módulo mi_modulo."""
from django.shortcuts import render
from django.contrib.admin.views.decorators import staff_member_required


@staff_member_required
def dashboard(request):
    """Dashboard del módulo en admin."""
    from .models import ExampleModel
    company = request.active_company
    stats = {
        "total": ExampleModel.objects.filter(company=company).count(),
        "active": ExampleModel.objects.filter(company=company, is_active=True).count(),
    }
    return render(request, "mi_modulo/dashboard.html", {"stats": stats})
