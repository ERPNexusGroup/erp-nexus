# Metadata del módulo facturacion_ec
# Formato: asignaciones de variables top-level (no diccionario)
# Según parser AST del core_marketplace

technical_name = "facturacion_ec"
display_name = "Facturación Electrónica Ecuador"
description = "Módulo completo para emisión, firma y envío de facturas electrónicas al SRI Ecuador"
component_type = "module"
package_type = "extension"
version = "0.1.0"
author = "ERP Nexus Group"
author_email = "contact@erpnexus.ec"
license = "MIT"
homepage = "https://github.com/ERPNexusGroup/erp-nexus"
repository = "https://github.com/ERPNexusGroup/erp-nexus"
dependencies = ["core_companies>=0.1.0"]
python = ">=3.11"
erp_version = ">=0.1.0"
categories = ["accounting", "invoicing", "tax"]
keywords = ["facturacion", "sri", "ecuador", "xml", "firma digital"]

# Admin menu (cuando se instala)
admin_menu = [
    {"label": "Facturas", "app_label": "facturacion_ec", "model": "invoice"},
    {"label": "Clientes", "app_label": "facturacion_ec", "model": "customer"},
    {"label": "Productos", "app_label": "facturacion_ec", "model": "product"},
    {"label": "Licencias", "app_label": "facturacion_ec", "model": "companylicense"},
]

# Django app name (si difiere de modules.facturacion_ec)
django_app = "modules.facturacion_ec"
