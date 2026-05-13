"""
Serializers para core_pagebuilder API.

PageSerializer: CRUD completo de páginas con validación de layout JSON.
ComponentSerializer: Catálogo de componentes reutilizables.
"""
from rest_framework import serializers
from django.utils.text import slugify
from .models import Page, Component
from .validators import validate_layout_schema


class ComponentSerializer(serializers.ModelSerializer):
    """Serializer de catálogo de componentes (read-only para frontend)."""
    class Meta:
        model = Component
        fields = ['id', 'name', 'component_type', 'description', 'default_props', 'template_html', 'is_active']


class PageSerializer(serializers.ModelSerializer):
    """
    Serializer para crear/editar páginas.

    Valida que `layout` cumpla el schema JSON.
    Campo `slug` auto-generado si no se provee.
    """
    layout = serializers.JSONField(
        required=True,
        help_text="Lista de componentes del layout (JSON schema validado)",
    )

    class Meta:
        model = Page
        fields = [
            'id', 'title', 'slug', 'description', 'status',
            'layout', 'meta_title', 'meta_description',
            'created_by', 'created_at', 'updated_at', 'published_at',
        ]
        read_only_fields = ['id', 'slug', 'created_at', 'updated_at', 'published_at']

    def validate_layout(self, value):
        """Valida el schema JSON del layout."""
        validate_layout_schema(value)
        return value

    def create(self, validated_data):
        # Auto-generar slug si no viene
        if not validated_data.get('slug'):
            validated_data['slug'] = slugify(validated_data['title'])
        return super().create(validated_data)

    def update(self, instance, validated_data):
        instance = super().update(instance, validated_data)
        # Re-calcular slug si cambió el título
        if 'title' in validated_data and not validated_data.get('slug'):
            instance.slug = slugify(instance.title)
            instance.save(update_fields=['slug'])
        return instance


class PageListSerializer(serializers.ModelSerializer):
    """Serializer liviano para listado de páginas."""
    component_count = serializers.SerializerMethodField()

    class Meta:
        model = Page
        fields = ['id', 'title', 'slug', 'status', 'component_count', 'updated_at']

    def get_component_count(self, obj):
        return len(obj.layout) if obj.layout else 0


class PageRenderSerializer(serializers.ModelSerializer):
    """
    Serializer para renderizado público (solo campos públicos).
    Incluye HTML renderizado del layout.
    """
    html = serializers.SerializerMethodField()

    class Meta:
        model = Page
        fields = ['title', 'description', 'html', 'meta_title', 'meta_description']

    def get_html(self, obj):
        """Retorna el HTML renderizado del layout."""
        from .renderer import PageRenderer
        renderer = PageRenderer()
        return renderer.render_to_html(obj)
