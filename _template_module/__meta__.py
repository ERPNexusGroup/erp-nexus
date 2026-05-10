# Metadata del módulo — REQUERIDO
# Ver MODULE_SPEC.md para todos los campos

MODULE_META = {
    "name": "Mi Módulo",
    "technical_name": "mi_modulo",
    "version": "0.1.0",
    "description": "Descripción breve del módulo",
    "summary": "Una línea de descripción",
    "author": "Tu Nombre",
    "author_email": "email@ejemplo.com",
    "repo": "https://github.com/ERPNexus/mi_modulo",
    "license": "MIT",

    # Dependencias del core
    "dependencies": [
        "core_companies>=0.5.0",
        "core_users>=0.5.0",
    ],
    "optional_dependencies": [],

    # Compatibilidad ERP Nexus
    "min_erp_version": "0.5.0",
    "max_erp_version": "0.9.0",

    # Configuraciones default (se pueden sobrescribir)
    "settings": {
        "MI_MODULO_ENABLED": True,
    },

    # Licenciamiento (si es de pago)
    "licensing": {
        "type": "free",  # free|tiered|paid
        "plans": ["free"],
        "free_tier": {"limit": 100},
    },

    # UI
    "icon": "fa-cube",
    "menu_category": "General",
    "menu_order": 100,

    # URLs
    "docs_url": "",
    "support_url": "",
}
