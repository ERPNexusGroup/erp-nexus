from pathlib import Path
import os

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = "dev-secret-key-change-me"
DEBUG = True
ALLOWED_HOSTS: list[str] = []

INSTALLED_APPS = [
    "apps.core_dashboard",
    "jazzmin",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "apps.core_auth",
    "apps.core_users",
    "apps.core_permissions",
    "apps.core_groups",
    "apps.core_marketplace",
    "apps.core_companies",
    "apps.core_currency",
    "apps.core_chart_of_accounts",
    "apps.core_fiscal_year",
    "apps.core_config",
]

try:
    from .modules_enabled import MODULE_APPS
except Exception:
    MODULE_APPS = []

for app in MODULE_APPS:
    if app not in INSTALLED_APPS:
        INSTALLED_APPS.append(app)

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "apps.core_companies.middleware.ActiveCompanyMiddleware",
]

ROOT_URLCONF = "erp_nexus.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "apps.core_dashboard.context_processors.admin_metrics",
            ],
        },
    }
]

WSGI_APPLICATION = "erp_nexus.wsgi.application"
ASGI_APPLICATION = "erp_nexus.asgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

AUTH_PASSWORD_VALIDATORS = []

LANGUAGE_CODE = "es-ec"
TIME_ZONE = "America/Guayaquil"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
MODULES_DIR = BASE_DIR / "modules"

JAZZMIN_SETTINGS = {
    "site_title": "ERP Nexus",
    "site_header": "ERP Nexus",
    "site_brand": "ERP Nexus",
    "welcome_sign": "Panel Administrativo",
    "search_model": "auth.User",
    "topmenu_links": [
        {"name": "Dashboard", "url": "admin:index", "permissions": ["auth.view_user"]},
    ],
    "icons": {
        "auth": "fas fa-users-cog",
        "auth.user": "fas fa-user",
        "core_users.userprofile": "fas fa-id-badge",
        "core_companies.company": "fas fa-building",
        "core_companies.membership": "fas fa-user-tag",
        "core_marketplace.modulecatalogitem": "fas fa-puzzle-piece",
        "core_currency.currency": "fas fa-money-bill-dollar",
        "core_currency.exchangerate": "fas fa-calculator",
        "core_chart_of_accounts.account": "fas fa-chart-pie",
        "core_chart_of_accounts.accounttype": "fas fa-sitemap",
        "core_chart_of_accounts.journalentry": "fas fa-book",
        "core_fiscal_year.fiscalyear": "fas fa-calendar-alt",
        "core_fiscal_year.fiscalperiod": "fas fa-calendar-week",
        "core_config.configkey": "fas fa-sliders-h",
        "core_config.systemconfig": "fas fa-cog",
    },
}

# Configuración SRI Ecuador (facturacion)
FACTURACION = {
    "CERT_PATH": os.getenv("FACTURACION_CERT_PATH", ""),
    "CERT_PASSWORD": os.getenv("FACTURACION_CERT_PASSWORD", ""),
    "SRI_AMBIENTE": int(os.getenv("SRI_AMBIENTE", "1")),
    "ESTABLECIMIENTO_DEFAULT": os.getenv("ESTABLECIMIENTO_DEFAULT", "001"),
    "PUNTO_EMISION_DEFAULT": os.getenv("PUNTO_EMISION_DEFAULT", "001"),
}

FACTURACION_EC_AUTO_SEND = os.getenv("FACTURACION_EC_AUTO_SEND", "true").lower() == "true"
