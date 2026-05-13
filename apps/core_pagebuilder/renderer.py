"""
Renderer — Convierte layout JSON de páginas a HTML.

Uso:
    from .renderer import PageRenderer
    html = PageRenderer().render_to_html(page)
"""
from django.utils.html import mark_safe


class PageRenderer:
    """
    Renderiza un objeto Page a HTML seguro.

    Estrategia:
    - Cada tipo de componente se renderiza inline con templating simple.
    - Los componentes anidados (columns) se renderizan recursivamente.
    - El HTML resultante está marcado como safe para templates Django.
    """

    def render_to_html(self, page):
        """
        Renderiza la página completa a HTML.

        Args:
            page: instancia de Page con layout JSON

        Returns:
            SafeString: HTML renderizado y marcado como seguro
        """
        if not page.layout:
            return ''

        rendered_components = []
        for comp in page.layout:
            html = self._render_component(comp)
            rendered_components.append(html)

        return mark_safe('\n'.join(rendered_components))

    def _render_component(self, component):
        """
        Renderiza un solo componente.

        Args:
            component: dict con keys: type, props (y opcional id)

        Returns:
            SafeString: HTML del componente
        """
        comp_type = component.get('type')
        props = component.get('props', {})

        if comp_type == 'columns':
            return self._render_columns(props)
        elif comp_type == 'heading':
            return self._render_heading(props)
        elif comp_type == 'text':
            return self._render_text(props)
        elif comp_type == 'image':
            return self._render_image(props)
        elif comp_type == 'button':
            return self._render_button(props)
        elif comp_type == 'spacer':
            return self._render_spacer(props)
        elif comp_type == 'divider':
            return self._render_divider(props)
        elif comp_type == 'html':
            return self._render_html(props)
        else:
            # Componente desconocido
            return mark_safe(f'<!-- Unknown component: {comp_type} -->')

    # ─── Renderers por tipo ────────────────────────────────────────────

    def _render_heading(self, props):
        level = props.get('level', 1)
        text = props.get('text', '')
        html = f'<h{level} class="cp-heading cp-heading-{level}">{text}</h{level}>'
        return mark_safe(html)

    def _render_text(self, props):
        content = props.get('content', '')
        html = f'<div class="cp-text">{content}</div>'
        return mark_safe(html)

    def _render_image(self, props):
        src = props.get('src', '')
        alt = props.get('alt', '')
        width = f' width="{props.get("width", "")}"' if props.get('width') else ''
        height = f' height="{props.get("height", "")}"' if props.get('height') else ''
        html = f'<img src="{src}" alt="{alt}" class="cp-image" loading="lazy"{width}{height}>'
        return mark_safe(html)

    def _render_button(self, props):
        label = props.get('label', '')
        url = props.get('url', '#')
        target = props.get('target', '_self')
        rel = f' rel="{props.get("rel", "")}"' if props.get('rel') else ''
        html = f'<a href="{url}" class="cp-button btn" target="{target}"{rel}>{label}</a>'
        return mark_safe(html)

    def _render_spacer(self, props):
        height = props.get('height', 20)
        html = f'<div class="cp-spacer" style="height: {height}px;"></div>'
        return mark_safe(html)

    def _render_divider(self, props):
        html = '<hr class="cp-divider">'
        return mark_safe(html)

    def _render_html(self, props):
        content = props.get('content', '')
        # Contenido HTML confiable (admin-only)
        return mark_safe(content)

    def _render_columns(self, props):
        children = props.get('children', [])
        gap = props.get('gap', '1rem')

        if not children:
            return ''

        rendered_children = []
        for child in children:
            rendered_children.append(self._render_component(child))

        html = (
            f'<div class="cp-columns" style="display: grid; '
            f'grid-template-columns: repeat({len(children)}, 1fr); gap: {gap};">'
        )
        for child_html in rendered_children:
            html += f'<div class="cp-column">{child_html}</div>'
        html += '</div>'

        return mark_safe(html)

    def render_to_context(self, page):
        """
        Retorna un diccionario de contexto para usar en plantillas Django.

        Returns:
            dict: {'page': page, 'components_html': html_string, 'component_count': n}
        """
        return {
            'page': page,
            'components_html': self.render_to_html(page),
            'component_count': len(page.layout) if page.layout else 0,
        }
