"""
Settings base — compartidas entre todos los entornos.
"""
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent

# ─── Seguridad ───────────────────────────────────────────────────────
SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "dev-secret-key-change-me")
DEBUG = False
ALLOWED_HOSTS: list[str] = []

# ─── Apps ────────────────────────────────────────────────────────────
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
    "apps.core_events",
]

# Módulos externos cargados dinámicamente
try:
    from erp_nexus.modules_enabled import MODULE_APPS
except ImportError:
    MODULE_APPS = []

for app in MODULE_APPS:
    if app not in INSTALLED_APPS:
        INSTALLED_APPS.append(app)

# ─── Middleware ───────────────────────────────────────────────────────
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

# ─── Base de datos (override en environment-specific) ────────────────
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

# ─── Auth ────────────────────────────────────────────────────────────
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# ─── i18n ────────────────────────────────────────────────────────────
LANGUAGE_CODE = "es-ec"
TIME_ZONE = "America/Guayaquil"
USE_I18N = True
USE_TZ = True

# ─── Static/Media ───────────────────────────────────────────────────
STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ─── Módulos ─────────────────────────────────────────────────────────
MODULES_DIR = BASE_DIR / "modules"

# ─── Jazzmin ─────────────────────────────────────────────────────────
JAZZMIN_SETTINGS = {
    "site_title": "ERP Nexus",
    "site_header": "ERP Nexus",
    "site_brand": "ERP Nexus",
    "welcome_sign": "Panel Administrativo",
    "search_model": "auth.User",
    "topmenu_links": [
        {"name": "Dashboard", "url": "admin:index", "permissions": ["auth.view_user"]},
        {"name": "API Docs", "url": "/api/docs", "new_window": True},
    ],
    "icons": {
        "auth": "fas fa-users-cog",
        "auth.user": "fas fa-user",
        "core_users.userprofile": "fas fa-id-badge",
        "core_companies.company": "fas fa-building",
        "core_companies.membership": "fas fa-user-tag",
        "core_marketplace.modulecatalogitem": "fas fa-puzzle-piece",
        "core_events.eventlog": "fas fa-bolt",
    },
}

# ─── Django Ninja API ────────────────────────────────────────────────
NINJA_PAGINATION_CLASS = "ninja.pagination.LimitOffsetPagination"
NINJA_PAGINATION_PER_PAGE = 25

# ─── Redis / Cache (override en production) ──────────────────────────
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
    }
}

# ─── Celery (override en production) ─────────────────────────────────
CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True
