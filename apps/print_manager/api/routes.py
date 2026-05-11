"""
API endpoints para el módulo print_manager.
"""
from ninja import Router
from django.db import transaction
from django.template import loader

from ..models import PrintTemplate, PrintJob

router = Router(tags=["Print Manager"])


@router.get("/templates/")
def list_templates(request):
    """Lista plantillas de impresión activas."""
    templates = PrintTemplate.objects.filter(is_active=True)
    return [
        {
            "id": t.id,
            "name": t.name,
            "key": t.template_key,
            "default_filename": t.default_filename,
        }
        for t in templates
    ]


@router.post("/render/")
def render_pdf(request):
    """
    Renderiza un PDF usando una plantilla.

    Body: {
        "template_key": "invoice",
        "context": { ... },
        "filename": "factura_123.pdf"  # opcional
    }
    """
    data = request.json
    template_key = data["template_key"]
    context = data.get("context", {})
    filename = data.get("filename", f"{template_key}.pdf")

    try:
        template = PrintTemplate.objects.get(template_key=template_key, is_active=True)
    except PrintTemplate.DoesNotExist:
        return {"error": f"Template '{template_key}' no encontrado"}, 404

    # Crear PrintJob (log)
    job = PrintJob.objects.create(
        template=template,
        context=context,
        status="processing",
    )

    try:
        # Renderizar HTML
        html = template.html_template.render(context)

        # Aquí iría WeasyPrint o ReportLab
        # Por ahora, placeholder: solo retornamos HTML (debug)
        # En producción: pdf = weasyprint.HTML(string=html).write_pdf()

        job.status = "completed"
        job.file_path = f"/tmp/{filename}"  # placeholder
        job.save()

        return {
            "job_id": job.id,
            "status": "completed",
            "filename": filename,
            # "pdf_url": f"/media/prints/{filename}"  # futuro
        }
    except Exception as exc:
        job.status = "failed"
        job.error_message = str(exc)
        job.save()
        return {"error": str(exc)}, 500


@router.get("/jobs/{job_id}/")
def get_job(request, job_id: int):
    """Consulta el estado de un PrintJob."""
    job = PrintJob.objects.get(id=job_id)
    return {
        "id": job.id,
        "template": job.template.template_key,
        "status": job.status,
        "file_path": job.file_path,
        "error": job.error_message,
        "created_at": job.created_at,
        "completed_at": job.completed_at,
    }
