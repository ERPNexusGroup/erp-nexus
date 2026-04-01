"""
Módulo ERP Nexus — inventory_basic
===================================

Sistema de inventario básico: productos, categorías y movimientos.
"""

technical_name = "inventory_basic"
display_name = "Inventario Básico"
component_type = "module"
package_type = "extension"
domain = "inventory"

python = ">=3.11"
erp_version = ">=0.2.0"

version = "0.1.0"
license = "MIT"
keywords = ["erp", "nexus", "inventory", "stock", "productos"]
description = "Sistema de inventario básico: productos, categorías, movimientos y alertas de stock"

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

installable = True
auto_install = False

registry_flags = {
    "models": True,
    "api": True,
    "workers": False,
    "tasks": False,
}
