"""
Módulo ERP Nexus — inventory
============================

Sistema de gestión de inventario: productos, categorías y movimientos.
"""

technical_name = "inventory"
display_name = "Inventario"
component_type = "module"
package_type = "essential"  # Essential module — integrated in core
domain = "inventory"

python = ">=3.11"
erp_version = ">=0.2.0"

version = "0.1.0"
license = "MIT"
keywords = ["erp", "nexus", "inventory", "stock", "productos"]
description = "Sistema de inventario: productos, categorías, movimientos y alertas de stock"

authors = [
    {
        "name": "ERP Nexus Team",
        "role": "author",
        "email": "team@erp-nexus.org",
    }
]

depends = []

external_dependencies = {
    "python": [],
    "bin": [],
}

installable = True  # Essential modules always installed
auto_install = False

registry_flags = {
    "models": True,
    "api": True,
    "workers": False,
    "tasks": False,
}
