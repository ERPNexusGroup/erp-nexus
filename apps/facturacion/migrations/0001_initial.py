# Generated manually for facturacion core separation
# Django 5.0

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('core_companies', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Customer',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('identification_type', models.CharField(choices=[('04', 'RUC'), ('05', 'Cédula'), ('06', 'Pasaporte'), ('07', 'Consumidor final'), ('08', 'Identificación exterior')], default='05', max_length=5)),
                ('identification_number', models.CharField(max_length=20)),
                ('name', models.CharField(max_length=200)),
                ('email', models.EmailField(blank=True, max_length=254)),
                ('phone', models.CharField(blank=True, max_length=50)),
                ('address', models.TextField(blank=True)),
                ('razon_social', models.CharField(blank=True, max_length=200)),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('company', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='facturacion_customers', to='core_companies.company')),
            ],
            options={
                'verbose_name': 'Cliente',
                'verbose_name_plural': 'Clientes',
                'indexes': [models.Index(fields=['identification_number'], name='idx_fact_customer_ident'), models.Index(fields=['company', 'is_active'], name='idx_fact_customer_co_active')],
                'unique_together': {('company', 'identification_type', 'identification_number')},
            },
        ),
        migrations.CreateModel(
            name='Invoice',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('number', models.CharField(help_text='Número factura (ej: 001-001-000000001)', max_length=30, unique=True)),
                ('date', models.DateField(default=django.utils.timezone.now)),
                ('subtotal', models.DecimalField(decimal_places=2, default=0, max_digits=15)),
                ('tax_total', models.DecimalField(decimal_places=2, default=0, max_digits=15)),
                ('total', models.DecimalField(decimal_places=2, default=0, max_digits=15)),
                ('status', models.CharField(choices=[('draft', 'Borrador'), ('pending', 'Pendiente'), ('paid', 'Pagada'), ('cancelled', 'Anulada'), ('sent', 'Enviada (SRI)')], default='draft', max_length=20)),
                ('notes', models.TextField(blank=True, default='')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('company', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='facturacion_invoices', to='core_companies.company')),
                ('created_by', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='facturas_created_facturacion', to=settings.AUTH_USER_MODEL)),
                ('customer', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='facturacion_invoices', to='facturacion.customer')),
            ],
            options={
                'verbose_name': 'Factura',
                'verbose_name_plural': 'Facturas',
                'ordering': ['-date', '-id'],
                'indexes': [models.Index(fields=['company', 'date'], name='idx_fact_invoice_co_date'), models.Index(fields=['status'], name='idx_fact_invoice_status')],
            },
        ),
        migrations.CreateModel(
            name='InvoiceLine',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('description', models.CharField(blank=True, max_length=200)),
                ('quantity', models.DecimalField(decimal_places=4, default=1, max_digits=10)),
                ('unit_price', models.DecimalField(decimal_places=2, help_text='Precio unitario (sin impuestos)', max_digits=10)),
                ('unit_discount', models.DecimalField(decimal_places=2, default=0, help_text='Descuento por unidad', max_digits=10)),
                ('subtotal', models.DecimalField(decimal_places=2, help_text='quantity × (unit_price − unit_discount)', max_digits=12)),
                ('tax_rate', models.DecimalField(decimal_places=2, default=12.00, help_text='Porcentaje impuesto (ej: 12.00 para IVA Ecuador)', max_digits=5)),
                ('tax_amount', models.DecimalField(decimal_places=2, default=0, help_text='subtotal × (tax_rate / 100)', max_digits=12)),
                ('discount', models.DecimalField(decimal_places=2, default=0, help_text='Descuento total sobre la línea', max_digits=12)),
                ('total', models.DecimalField(decimal_places=2, help_text='subtotal + tax_amount − discount', max_digits=12)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('invoice', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='facturacion_lines', to='facturacion.invoice')),
                ('product', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='facturacion_invoice_lines', to='inventory.product')),
            ],
            options={
                'verbose_name': 'Línea de Factura',
                'verbose_name_plural': 'Líneas de Factura',
                'indexes': [models.Index(fields=['invoice'], name='idx_fact_line_invoice')],
            },
        ),
    ]
