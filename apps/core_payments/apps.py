# apps/core_payments/apps.py
from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class CorePaymentsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.core_payments'
    label = 'core_payments'
    verbose_name = _('Payments & Payouts')
