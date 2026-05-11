"""
Settings de producción.
Variables de entorno requeridas:
  - DJANGO_SECRET_KEY
  - DJANGO_ALLOWED_HOSTS (comma-separated)
  - DATABASE_URL (PostgreSQL)
  - REDIS_URL
"""
import os

from .base import *  # noqa: F401,F403

DEBUG = False

# ─── Seguridad ───────────────────────────────────────────────────────
SECRET_KEY = os.environ["DJANGO_SECRET_KEY"]
ALLOWED_HOSTS = os.environ.get("DJANGO_ALLOWED_HOSTS", "").split(",")
CSRF_TRUSTED_ORIGINS = [
    f"https://{h}" for h in ALLOWED_HOSTS if h
]
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True

# ─── Database (PostgreSQL) ───────────────────────────────────────────
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.environ.get("POSTGRES_DB", "erp_nexus"),
        "USER": os.environ.get("POSTGRES_USER", "erp_nexus"),
        "PASSWORD": os.environ.get("POSTGRES_PASSWORD", ""),
        "HOST": os.environ.get("POSTGRES_HOST", "localhost"),
        "PORT": os.environ.get("POSTGRES_PORT", "5432"),
    }
}

# ─── Cache (Redis) ──────────────────────────────────────────────────
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.redis.RedisCache",
        "LOCATION": os.environ.get("REDIS_URL", "redis://localhost:6379/0"),
    }
}

# ─── Celery (Redis) ─────────────────────────────────────────────────
CELERY_BROKER_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
CELERY_RESULT_BACKEND = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
CELERY_TASK_ALWAYS_EAGER = False
CELERY_TASK_EAGER_PROPAGATES = False

# ─── Static files ───────────────────────────────────────────────────
STATICFILES_STORAGE = "django.contrib.staticfiles.storage.ManifestStaticFilesStorage"

# ─── Logging ────────────────────────────────────────────────────────
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "WARNING",
    },
}

# ─── Sentry (error tracking) ────────────────────────────────────────
# pip install sentry-sdk
# Descomentar y configurar SENTRY_DSN en .env
#
# import sentry_sdk
# from sentry_sdk.integrations.django import DjangoIntegration
# from sentry_sdk.integrations.celery import CeleryIntegration
#
# SENTRY_DSN = os.environ.get("SENTRY_DSN", "")
# if SENTRY_DSN:
#     sentry_sdk.init(
#         dsn=SENTRY_DSN,
#         integrations=[DjangoIntegration(), CeleryIntegration()],
#         traces_sample_rate=0.1,
#         send_default_pii=False,
#         environment=os.environ.get("SENTRY_ENVIRONMENT", "production"),
#     )
