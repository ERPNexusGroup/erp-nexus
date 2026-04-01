"""
Módulo ERP Nexus — accounting_basic
====================================

Sistema contable básico para ERP Nexus.
Registra cuentas, asientos contables y genera balances.
"""

technical_name = "accounting_basic"
display_name = "Contabilidad Básica"
component_type = "module"
package_type = "extension"
domain = "accounting"

python = ">=3.11"
erp_version = ">=0.2.0"

version = "0.1.0"
license = "MIT"
keywords = ["erp", "nexus", "accounting", "contabilidad", "asientos"]
description = "Sistema contable básico: cuentas, asientos y balances para ERP Nexus"

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
