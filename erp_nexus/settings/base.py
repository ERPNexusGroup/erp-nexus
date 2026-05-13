"""
Settings base — compartidas entre todos los entornos.
"""
import os
import sys
import uuid
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Default generator for UUID primary keys
UUID_FIELD_DEFAULT = uuid.uuid4

# ─── Añadir Project ERP NEXUS al path para módulos externos ─────────────
PROJECT_ROOT = BASE_DIR.parent  # ~/Project ERP NEXUS
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# modules/core (core local dentro de erp-nexus)
CORE_PKG_DIR = BASE_DIR / "modules" / "core"
if str(CORE_PKG_DIR) not in sys.path:
    sys.path.insert(0, str(CORE_PKG_DIR))
# También BASE_DIR para imports de 'apps.*'
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

# ─── Seguridad ───────────────────────────────────────────────────────
SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "dev-secret-key-change-me")
DEBUG = False
ALLOWED_HOSTS: list[str] = []

# ─── Apps ────────────────────────────────────────────────────────────
INSTALLED_APPS = [
    "apps.core_dashboard",
    "jazzmin",
    "corsheaders",
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
    "apps.core_audit",
    "apps.core_stats",
    "apps.core_pagebuilder",
    "apps.core_payments",
    # Essential modules (integrated)
    "apps.inventory",
    "apps.sales",
    "apps.purchases",
    "apps.facturacion",  # Core facturación local (sin SRI)
    "apps.notifications",
    "apps.print_manager",
    "apps.payouts",
]

# Módulos externos cargados dinámicamente
# En pytest también cargamos MODULE_APPS para que los tests vean todas las apps
IN_PYTEST = bool(os.environ.get('PYTEST_VERSION'))
try:
    from erp_nexus.modules_enabled import MODULE_APPS  # type: ignore
    if IN_PYTEST:
        # En tests forzamos carga de plugins para validar integración
        pass  # MODULE_APPS ya contiene 'modules.facturacion_ec'
except ImportError:
    MODULE_APPS = []

for app in MODULE_APPS:
    if app not in INSTALLED_APPS:
        INSTALLED_APPS.append(app)

# ─── Middleware ───────────────────────────────────────────────────────
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "corsheaders.middleware.CorsMiddleware",
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

# ─── CORS ────────────────────────────────────────────────────────────
CORS_ALLOW_ALL_ORIGINS = False
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:5173",
    "http://localhost:8080",
]
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_HEADERS = [
    "accept",
    "authorization",
    "content-type",
    "origin",
    "x-requested-with",
]

# ─── Redis / Cache (override en production) ──────────────────────────
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
    }
}

# ─── Celery (override en production) ─────────────────────────────────
# En desarrollo: TASK_ALWAYS_EAGER=True (síncrono, sin broker)
# En producción: broker URL desde REDIS_URL, colas definidas abajo
CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True

# Configuración base de colas (se usa en producción)
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TASK_TRACK_STARTED = True
CELERY_TASK_TIME_LIMIT = 300  # 5 minutos máximo por tarea
CELERY_WORKER_MAX_TASKS_PER_CHILD = 1000  # prevenir memory leaks

# Definición de colas (queues) y prioridades
CELERY_TASK_QUEUES = {
    'default': {'exchange': 'default', 'routing_key': 'default'},
    'sri': {'exchange': 'sri', 'routing_key': 'sri.#', 'priority': 0},      # Alta prioridad
    'notifications': {'exchange': 'notifications', 'routing_key': 'notifications.#', 'priority': 1},
    'reports': {'exchange': 'reports', 'routing_key': 'reports.#', 'priority': 5},      # Baja prioridad
    'webhooks': {'exchange': 'webhooks', 'routing_key': 'webhooks.#', 'priority': 3},
}
CELERY_TASK_DEFAULT_QUEUE = 'default'
CELERY_TASK_DEFAULT_EXCHANGE = 'default'
CELERY_TASK_DEFAULT_ROUTING_KEY = 'default'
# Prioridad numérica: 0 (máxima) a 9 (mínima)

# ─── Payouts / Bank Integration ─────────────────────────────────────
BANK_API_TIMEOUT = int(os.environ.get('BANK_API_TIMEOUT', '30'))
BANK_RETRY_ATTEMPTS = int(os.environ.get('BANK_RETRY_ATTEMPTS', '3'))

BANK_PROVIDERS = {
    'produbanco': {
        'api_key': os.environ.get('BANK_PRODUBANCO_KEY', ''),
        'api_secret': os.environ.get('BANK_PRODUBANCO_SECRET', ''),
        'sandbox': os.environ.get('BANK_PRODUBANCO_SANDBOX', 'True').lower() in ('true', '1', 'yes'),
    },
    'pichincha': {
        'api_key': os.environ.get('BANK_PICHINCHA_KEY', ''),
        'api_secret': os.environ.get('BANK_PICHINCHA_SECRET', ''),
    },
    'guayaquil': {
        'api_key': os.environ.get('BANK_GUAYAQUIL_KEY', ''),
        'api_secret': os.environ.get('BANK_GUAYAQUIL_SECRET', ''),
    },
}

# Logging para payout banks
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'structured': {
            'format': '%(levelname)s %(asctime)s [%(name)s] %(message)s',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'structured',
        },
    },
    'loggers': {
        'payouts': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
        'payouts.banks': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}
