"""
Módulo ERP Nexus — notifications
================================

Sistema de notificaciones unificado (email, Telegram, cola).
"""

technical_name = "notifications"
display_name = "Notificaciones"
component_type = "module"
package_type = "essential"
domain = "notifications"

python = ">=3.11"
erp_version = ">=0.2.0"

version = "0.1.0"
license = "MIT"
keywords = ["erp", "nexus", "notifications", "email", "telegram"]
description = "Módulo de notificaciones: email, Telegram y cola asincrónica"

authors = [
    {
        "name": "ERP Nexus Team",
        "role": "author",
        "email": "team@erp-nexus.org",
    }
]

depends = ["apps.core_events"]

external_dependencies = {
    "python": ["django.core.mail", "requests"],
    "bin": [],
}

installable = True
auto_install = False

registry_flags = {
    "models": True,
    "api": True,
    "workers": True,   # Cola asincrónica
    "tasks": False,
}
