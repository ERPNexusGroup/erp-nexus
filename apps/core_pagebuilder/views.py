"""
Views para core_pagebuilder API.

PageViewSet: CRUD + publish action
ComponentViewSet: Read-only catálogo (admin puede modificar)
"""
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.db import transaction

from .models import Page, Component
from .serializers import PageSerializer, PageListSerializer, ComponentSerializer
from .renderer import PageRenderer


class IsAdminOrReadOnly(permissions.BasePermission):
    """
    Permiso: solo admins pueden crear/editar/eliminar.
    Lectura pública permitida para páginas published.
    """
    def has_permission(self, request, view):
        # Lectura GET siempre permitida
        if request.method in permissions.SAFE_METHODS:
            return True
        # Escritura requiere autenticación + is_staff
        return request.user and request.user.is_authenticated and request.user.is_staff

    def has_object_permission(self, request, view, obj):
        # Lectura: permiso si es published o usuario es staff
        if request.method in permissions.SAFE_METHODS:
            if obj.status == 'published':
                return True
            return request.user and request.user.is_authenticated and request.user.is_staff
        # Escritura: solo staff
        return request.user and request.user.is_authenticated and request.user.is_staff


class PageViewSet(viewsets.ModelViewSet):
    """
    API endpoint para gestionar páginas del page builder.

    Permissions:
      - GET list/retrieve: público si page.published, si no solo admin
      - POST/PUT/PATCH/DELETE: solo admin (is_staff=True)
    """
    queryset = Page.objects.all()
    permission_classes = [IsAdminOrReadOnly]
    lookup_field = 'slug'  # usar slug en URLs públicas

    def get_serializer_class(self):
        if self.action == 'list':
            return PageListSerializer
        return PageSerializer

    def get_queryset(self):
        """
        Filtrar según acción:
        - list: mostrar public + staff (staff ve todos)
        - retrieve: filtro por slug + status check en permission
        """
        qs = Page.objects.all()
        if self.action == 'list':
            # Staff ve todo; anon solo published
            if not self.request.user.is_staff:
                qs = qs.filter(status='published')
        return qs

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAdminUser])
    def publish(self, request, slug=None):
        """
        Endpoint: POST /api/v1/pages/<slug>/publish/
        Publica una página (status='published', published_at=now).
        """
        page = self.get_object()
        page.publish()
        serializer = self.get_serializer(page)
        return Response({
            'detail': 'Página publicada exitosamente.',
            'page': serializer.data
        })

    @action(detail=True, methods=['get'], permission_classes=[])
    def render(self, request, slug=None):
        """
        Endpoint: GET /api/v1/pages/<slug>/render/
        Retorna HTML renderizado (sin template wrapper).
        """
        page = get_object_or_404(Page, slug=slug, status='published')
        renderer = PageRenderer()
        html = renderer.render_to_html(page)
        return Response({
            'title': page.title,
            'html': html,
        })


class ComponentViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint para catálogo de componentes (read-only público).

    Admin puede modificar vía Django admin.
    """
    queryset = Component.objects.filter(is_active=True)
    serializer_class = ComponentSerializer
    permission_classes = [permissions.AllowAny]
