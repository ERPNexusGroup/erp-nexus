"""
Validadores para core_pagebuilder.

Valida el schema JSON del layout de páginas.
"""
import uuid
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _


# Tipos de componente permitidos
COMPONENT_TYPES = [
    'heading', 'text', 'image', 'button',
    'columns', 'spacer', 'divider', 'html'
]

# Props requeridos por tipo
REQUIRED_PROPS = {
    'heading': ['text', 'level'],
    'text': ['content'],
    'image': ['src', 'alt'],
    'button': ['label', 'url'],
    'columns': ['children'],
    'spacer': ['height'],
    'divider': [],
    'html': ['content'],
}

# Props opcionales por tipo (para validar que no hay props desconocidas)
OPTIONAL_PROPS = {
    'heading': ['id', 'className', 'style'],
    'text': ['id', 'className', 'style', 'html'],
    'image': ['id', 'className', 'style', 'width', 'height'],
    'button': ['id', 'className', 'style', 'target', 'rel'],
    'columns': ['id', 'className', 'style', 'gap'],
    'spacer': ['id', 'className', 'style'],
    'divider': ['id', 'className', 'style'],
    'html': ['id', 'className', 'style'],
}


def validate_layout_schema(layout):
    """
    Valida que el layout tenga la estructura correcta.

    Args:
        layout: lista de componentes (cada uno es dict con type, props, id opcional)

    Raises:
        ValidationError: si el layout no es válido
    """
    if not isinstance(layout, list):
        raise ValidationError(_("El layout debe ser una lista de componentes."))

    if len(layout) > 100:
        raise ValidationError(_("Máximo 100 componentes por página."))

    component_ids = set()

    for idx, component in enumerate(layout):
        _validate_component(component, idx, component_ids)

    return True


def _validate_component(component, index, used_ids):
    """
    Valida un componente individual.
    """
    if not isinstance(component, dict):
        raise ValidationError(_(f"Componente {index}: debe ser un objeto/dict."))

    # Validar tipo
    comp_type = component.get('type')
    if not comp_type:
        raise ValidationError(_(f"Componente {index}: falta el campo 'type'."))

    if comp_type not in COMPONENT_TYPES:
        raise ValidationError(
            _(f"Componente {index}: tipo '{comp_type}' no válido. "
              f"Tipos permitidos: {', '.join(COMPONENT_TYPES)}")
        )

    # Validar props
    props = component.get('props', {})
    if not isinstance(props, dict):
        raise ValidationError(_(f"Componente {index}: 'props' debe ser un objeto."))

    _validate_required_props(comp_type, props, index)
    _validate_optional_props(comp_type, props, index)

    # Validar ID único (si se provee)
    comp_id = component.get('id')
    if comp_id:
        if comp_id in used_ids:
            raise ValidationError(_(f"Componente {index}: ID duplicado '{comp_id}'."))
        used_ids.add(comp_id)

    # Validaciones específicas por tipo
    if comp_type == 'heading':
        level = props.get('level')
        if level not in [1, 2, 3, 4, 5, 6]:
            raise ValidationError(_(f"Componente {index}: heading 'level' debe ser 1-6."))
        if not isinstance(props.get('text'), str):
            raise ValidationError(_(f"Componente {index}: heading 'text' debe ser string."))

    elif comp_type == 'text':
        if not isinstance(props.get('content'), str):
            raise ValidationError(_(f"Componente {index}: text 'content' debe ser string."))

    elif comp_type == 'image':
        if not isinstance(props.get('src'), str):
            raise ValidationError(_(f"Componente {index}: image 'src' debe ser string."))
        if not isinstance(props.get('alt'), str):
            raise ValidationError(_(f"Componente {index}: image 'alt' debe ser string."))

    elif comp_type == 'button':
        if not isinstance(props.get('label'), str):
            raise ValidationError(_(f"Componente {index}: button 'label' debe ser string."))
        if not isinstance(props.get('url'), str):
            raise ValidationError(_(f"Componente {index}: button 'url' debe ser string."))

    elif comp_type == 'spacer':
        height = props.get('height')
        if not isinstance(height, int) or height < 0 or height > 1000:
            raise ValidationError(_(f"Componente {index}: spacer 'height' debe ser entero 0-1000."))

    elif comp_type == 'columns':
        children = props.get('children', [])
        if not isinstance(children, list):
            raise ValidationError(_(f"Componente {index}: columns 'children' debe ser lista."))
        if len(children) > 6:
            raise ValidationError(_(f"Componente {index}: máximo 6 columnas."))
        # Validar recursivamente cada child
        for child_idx, child in enumerate(children):
            _validate_component(child, f"{index}.{child_idx}", used_ids)


def _validate_required_props(comp_type, props, index):
    """
    Valida que todos los props requeridos estén presentes.
    """
    required = REQUIRED_PROPS.get(comp_type, [])
    for prop in required:
        if prop not in props:
            raise ValidationError(
                _(f"Componente {index} ({comp_type}): falta prop requerido '{prop}'.")
            )


def _validate_optional_props(comp_type, props, index):
    """
    Valida que todos los props sean conocidos (requeridos u opcionales).
    """
    required = set(REQUIRED_PROPS.get(comp_type, []))
    optional = set(OPTIONAL_PROPS.get(comp_type, []))
    allowed = required | optional

    for prop in props.keys():
        if prop not in allowed:
            raise ValidationError(
                _(f"Componente {index} ({comp_type}): prop '{prop}' no reconocido.")
            )


def generate_component_id():
    """Genera un UUID único para un componente."""
    return str(uuid.uuid4())
