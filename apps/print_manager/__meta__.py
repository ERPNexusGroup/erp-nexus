"""
Módulo ERP Nexus — print_manager
=================================

Generador de PDFs reutilizable (WeasyPrint/ReportLab).
"""

technical_name = "print_manager"
display_name = "Print Manager"
component_type = "module"
package_type = "essential"
domain = "printing"

python = ">=3.11"
erp_version = ">=0.2.0"

version = "0.1.0"
license = "MIT"
keywords = ["erp", "nexus", "pdf", "print", "report"]
description = "Generador de PDFs reutilizable para facturas y documentos"

authors = [
    {
        "name": "ERP Nexus Team",
        "role": "author",
        "email": "team@erp-nexus.org",
    }
]

depends = []

external_dependencies = {
    "python": ["weasyprint"],
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
