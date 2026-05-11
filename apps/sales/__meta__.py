"""
Módulo ERP Nexus — sales
========================

Gestión de ventas: cotizaciones, órdenes, y facturación desde ventas.
"""

technical_name = "sales"
display_name = "Ventas"
component_type = "module"
package_type = "essential"
domain = "sales"

python = ">=3.11"
erp_version = ">=0.2.0"

version = "0.1.0"
license = "MIT"
keywords = ["erp", "nexus", "sales", "quotes", "orders"]
description = "Módulo de ventas: cotizaciones, órdenes y generación de facturas"

authors = [
    {
        "name": "ERP Nexus Team",
        "role": "author",
        "email": "team@erp-nexus.org",
    }
]

depends = ["apps.facturacion", "apps.inventory"]

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
