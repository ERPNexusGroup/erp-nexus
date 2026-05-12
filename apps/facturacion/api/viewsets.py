"""
ViewSets para Facturación Core (REST API).
"""
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response

from ..models import Customer, Invoice
from . import serializers


class CustomerViewSet(viewsets.ModelViewSet):
    """CRUD completo de clientes."""
    queryset = Customer.objects.all()
    serializer_class = serializers.CustomerSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        company = getattr(user, 'company', None)
        if company:
            return Customer.objects.filter(company=company)
        return Customer.objects.none()


class InvoiceViewSet(viewsets.ModelViewSet):
    """Gestión de facturas locales."""
    queryset = Invoice.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ['company', 'status', 'date']
    search_fields = ['number', 'customer__name']

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return serializers.InvoiceWriteSerializer
        return serializers.InvoiceReadSerializer

    def get_queryset(self):
        user = self.request.user
        company = getattr(user, 'company', None)
        if company:
            return Invoice.objects.filter(company=company)
        return Invoice.objects.none()

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    @action(detail=False, methods=['get'])
    def draft(self, request):
        qs = self.get_queryset().filter(status='draft')
        page = self.paginate_queryset(qs)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(qs, many=True)
        return Response(serializer.data)
