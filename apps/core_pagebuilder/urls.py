"""
URLs para core_pagebuilder API.

Endpoints:
  /api/v1/pages/          — CRUD páginas (admin)
  /api/v1/pages/<slug>/   — retrieve/update/delete/publish/render
  /api/v1/components/     — catálogo de componentes
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import PageViewSet, ComponentViewSet

router = DefaultRouter()
router.register(r'pages', PageViewSet, basename='page')
router.register(r'components', ComponentViewSet, basename='component')

urlpatterns = [
    path('', include(router.urls)),
]
