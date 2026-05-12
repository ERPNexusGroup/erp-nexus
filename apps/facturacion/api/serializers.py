"""
Serializers para Facturación Core API.
"""
from rest_framework import serializers
from django.db import transaction

from ..models import Customer, Invoice, InvoiceLine


class CustomerSerializer(serializers.ModelSerializer):
    """Serializer para Customer (lectura/escritura)."""
    company_name = serializers.CharField(source='company.name', read_only=True)

    class Meta:
        model = Customer
        fields = [
            'id', 'company', 'company_name', 'identification_type',
            'identification_number', 'name', 'email', 'phone', 'address',
            'razon_social', 'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']


class InvoiceLineSerializer(serializers.ModelSerializer):
    product_code = serializers.CharField(source='product.code', read_only=True)
    product_name = serializers.CharField(source='product.name', read_only=True)

    class Meta:
        model = InvoiceLine
        fields = [
            'id', 'product', 'product_code', 'product_name',
            'description', 'quantity', 'unit_price', 'unit_discount',
            'subtotal', 'tax_rate', 'tax_amount', 'discount', 'total'
        ]
        read_only_fields = ['subtotal', 'tax_amount', 'total']


class InvoiceReadSerializer(serializers.ModelSerializer):
    """Serializer para lectura de Invoice (con líneas)."""
    customer_name = serializers.CharField(source='customer.name', read_only=True)
    customer_id = serializers.CharField(source='customer.identification_number', read_only=True)
    lines = InvoiceLineSerializer(many=True, read_only=True, source='facturacion_lines')
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)

    class Meta:
        model = Invoice
        fields = [
            'id', 'company', 'customer', 'customer_name', 'customer_id',
            'number', 'date', 'subtotal', 'tax_total', 'total', 'status',
            'notes', 'created_by', 'created_by_name',
            'created_at', 'updated_at', 'lines'
        ]


class InvoiceWriteSerializer(serializers.ModelSerializer):
    """Serializer para crear/actualizar Invoice (sin líneas, se crean aparte)."""
    lines = InvoiceLineSerializer(many=True, write_only=True)

    class Meta:
        model = Invoice
        fields = [
            'id', 'company', 'customer', 'number', 'date',
            'subtotal', 'tax_total', 'total', 'status', 'notes',
            'lines'
        ]
        read_only_fields = ['subtotal', 'tax_total', 'total']

    def validate(self, data):
        if 'lines' in data and not data['lines']:
            raise serializers.ValidationError("La factura debe tener al menos una línea")
        return data

    @transaction.atomic
    def create(self, validated_data):
        lines_data = validated_data.pop('lines')
        validated_data['created_by'] = self.context['request'].user

        invoice = Invoice.objects.create(**validated_data)

        for line_data in lines_data:
            InvoiceLine.objects.create(invoice=invoice, **line_data)

        # Los signals recalcularán totals automáticamente
        return invoice

    @transaction.atomic
    def update(self, instance, validated_data):
        lines_data = validated_data.pop('lines', None)

        # Actualizar campos de Invoice
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if lines_data is not None:
            # Eliminar líneas existentes y recrear
            instance.facturacion_lines.all().delete()
            for line_data in lines_data:
                InvoiceLine.objects.create(invoice=instance, **line_data)

        return instance
