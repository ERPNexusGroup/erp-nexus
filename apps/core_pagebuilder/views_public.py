"""
Vistas públicas para core_pagebuilder.

Páginas web renders sin autenticación, solo para páginas publicadas.
"""
import logging
from django.shortcuts import render
from django.http import JsonResponse, Http404
from django.views.decorators.cache import cache_page
from django.views import View

from .models import Page
from .renderer import PageRenderer

logger = logging.getLogger(__name__)


# ─── Vista HTML de página (Class-Based) ───────────────────────────────
class PageDetailView(View):
    """Vista pública de una página (solo published). Cache 5 min."""
    def get(self, request, slug):
        logger.info(f"PageDetailView: buscando slug='{slug}'")
        try:
            page = Page.objects.get(slug=slug, status='published')
            logger.info(f"Página encontrada: id={page.id} title={page.title}")
        except Page.DoesNotExist:
            logger.warning(f"Página NO encontrada: slug='{slug}'")
            all_published = list(Page.objects.filter(status='published').values_list('slug', flat=True))
            logger.info(f"Páginas published: {all_published}")
            raise Http404(f"Página '{slug}' no encontrada")

        renderer = PageRenderer()
        context = {
            'page': page,
            'components_html': renderer.render_to_html(page),
        }
        return render(request, 'core_pagebuilder/page_detail.html', context)


page_detail = PageDetailView.as_view()


# ─── Endpoint JSON con HTML renderizado ───────────────────────────────
@cache_page(60 * 5)
def render_page(request, slug):
    """
    JSON con HTML renderizado de una página.

    URL: /pages/<slug>/render/
    """
    try:
        page = Page.objects.get(slug=slug, status='published')
    except Page.DoesNotExist:
        return JsonResponse({'error': 'Página no encontrada'}, status=404)

    renderer = PageRenderer()
    html = str(renderer.render_to_html(page))
    return JsonResponse({
        'title': page.title,
        'slug': page.slug,
        'html': html,
    })
