"""
Módulo ERP Nexus — purchases
=============================

Gestión de compras: órdenes de compra, proveedores y recepción de mercancía.
"""

technical_name = "purchases"
display_name = "Compras"
component_type = "module"
package_type = "essential"
domain = "purchases"

python = ">=3.11"
erp_version = ">=0.2.0"

version = "0.1.0"
license = "MIT"
keywords = ["erp", "nexus", "purchases", "po", "suppliers"]
description = "Módulo de compras: órdenes de compra y recepción de mercancía"

authors = [
    {
        "name": "ERP Nexus Team",
        "role": "author",
        "email": "team@erp-nexus.org",
    }
]

depends = ["apps.inventory", "apps.facturacion"]

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
