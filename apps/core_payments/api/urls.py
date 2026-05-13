# apps/core_payments/api/urls.py
"""
URLs para Payout Automation API.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register(r'bank-accounts', views.BankAccountViewSet, basename='bankaccount')
router.register(r'commissions', views.CommissionViewSet, basename='commission')
router.register(r'payouts', views.PayoutViewSet, basename='payout')
router.register(r'schedule', views.PayoutScheduleViewSet, basename='payoutschedule')

urlpatterns = [
    path('', include(router.urls)),
]
