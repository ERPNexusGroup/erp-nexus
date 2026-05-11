# Metadata del módulo facturacion (essential module)
# Formato: asignaciones de variables top-level (no diccionario)
# Según parser AST del core_marketplace

# Esential module — no se instala via Marketplace, viene en core
technical_name = "facturacion"
display_name = "Facturación Electrónica Ecuador"
description = "Módulo completo para emisión, firma y envío de facturas electrónicas al SRI Ecuador"
component_type = "essential_module"
package_type = "builtin"
version = "0.1.0"
author = "ERP Nexus Group"
author_email = "contact@erpnexus.ec"
license = "MIT"
homepage = "https://github.com/ERPNexus/erp-nexus"
repository = "https://github.com/ERPNexus/erp-nexus"
dependencies = ["core_companies>=0.1.0"]
python = ">=3.11"
erp_version = ">=0.1.0"
categories = ["accounting", "invoicing", "tax"]
keywords = ["facturacion", "sri", "ecuador", "xml", "firma digital"]

# Admin menu (cuando se instala)
admin_menu = [
    {"label": "Facturas", "app_label": "facturacion", "model": "invoice"},
    {"label": "Clientes", "app_label": "facturacion", "model": "customer"},
    {"label": "Productos", "app_label": "facturacion", "model": "product"},
    {"label": "Licencias", "app_label": "facturacion", "model": "companylicense"},
]

# Django app name (path Python)
django_app = "apps.facturacion"
