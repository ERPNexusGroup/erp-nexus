import ast
from pathlib import Path
from typing import Any, Dict

from pydantic import BaseModel, Field, ValidationError
from semantic_version import Version as SemVer, SimpleSpec


class AdminMenuItem(BaseModel):
    label: str
    app_label: str
    model: str


class ManifestSchema(BaseModel):
    technical_name: str = Field(..., min_length=3)
    version: str
    component_type: str
    package_type: str
    python: str
    erp_version: str
    django_app: str | None = None
    admin_menu: list[AdminMenuItem] | None = None

    @classmethod
    def validate_versions(cls, v: str) -> str:
        try:
            SemVer(v)
            return v
        except ValueError as e:
            raise ValueError(f"Versión inválida: {v}") from e

    @classmethod
    def validate_spec(cls, v: str) -> str:
        try:
            SimpleSpec(v)
            return v
        except ValueError as e:
            raise ValueError(f"Spec inválida: {v}") from e

    @staticmethod
    def _post_validate(values: "ManifestSchema") -> "ManifestSchema":
        return values

    @classmethod
    def model_validate(cls, obj: Any) -> "ManifestSchema":
        model = super().model_validate(obj)
        cls.validate_versions(model.version)
        cls.validate_spec(model.python)
        cls.validate_spec(model.erp_version)
        return model


class ManifestError(Exception):
    pass


def parse_meta_file(meta_path: Path) -> Dict[str, Any]:
    if not meta_path.exists():
        raise ManifestError(f"Archivo no encontrado: {meta_path}")
    try:
        tree = ast.parse(meta_path.read_text(encoding="utf-8"), filename=str(meta_path))
    except SyntaxError as e:
        raise ManifestError(f"Error de sintaxis en __meta__.py línea {e.lineno}: {e.msg}")

    metadata: Dict[str, Any] = {}
    for node in ast.iter_child_nodes(tree):
        if isinstance(node, ast.Assign) and len(node.targets) == 1:
            target = node.targets[0]
            if isinstance(target, ast.Name) and not target.id.startswith("_"):
                metadata[target.id] = _ast_node_to_safe_value(node.value, target.id)

    if not metadata:
        raise ManifestError("__meta__.py no contiene variables top-level válidas")
    return metadata


def _ast_node_to_safe_value(node: ast.AST, var_name: str) -> Any:
    if isinstance(node, ast.Constant):
        return node.value
    if isinstance(node, ast.List):
        return [_ast_node_to_safe_value(elt, var_name) for elt in node.elts]
    if isinstance(node, ast.Dict):
        keys = [_ast_node_to_safe_value(k, var_name) for k in node.keys]
        values = [_ast_node_to_safe_value(v, var_name) for v in node.values]
        return dict(zip(keys, values))
    if isinstance(node, ast.Name):
        if node.id in ("True", "False", "None"):
            return {"True": True, "False": False, "None": None}[node.id]
        raise ManifestError(
            f"Variable no permitida '{node.id}' en {var_name}. "
            f"Solo se permiten literales y True/False/None"
        )
    if isinstance(node, ast.JoinedStr):
        raise ManifestError(f"f-strings no permitidos en {var_name}")
    raise ManifestError(
        f"Tipo no soportado en {var_name}: {type(node).__name__} "
        f"(solo literales permitidos: str, int, float, bool, None, list, dict)"
    )


def load_and_validate_manifest(meta_path: Path) -> ManifestSchema:
    data = parse_meta_file(meta_path)
    try:
        return ManifestSchema.model_validate(data)
    except ValidationError as e:
        raise ManifestError(str(e)) from e
