"""
URLs públicas para core_pagebuilder.

Rutas accesibles sin autenticación:
  /pages/<slug>/        — Vista pública de página (solo published)
  /pages/<slug>/render/ — JSON con HTML renderizado
"""
from django.urls import path
from . import views_public

urlpatterns = [
    path('<slug:slug>/', views_public.page_detail, name='page_detail'),
    path('<slug:slug>/render/', views_public.render_page, name='page_render'),
]
