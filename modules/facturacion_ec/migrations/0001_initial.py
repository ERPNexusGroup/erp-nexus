# Generated manually — Plugin Facturación Electrónica Ecuador (SRI) initial migration
# Django 6.0.5

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('core_companies', '0001_initial'),
        ('facturacion', '0001_initial'),   # Depende de core facturación (Invoice, Customer)
    ]

    operations = [
        migrations.CreateModel(
            name='SriAmbiente',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('code', models.IntegerField(unique=True)),
                ('name', models.CharField(max_length=50)),
            ],
            options={
                'verbose_name': 'Ambiente SRI',
                'verbose_name_plural': 'Ambientes SRI',
            },
        ),
        migrations.CreateModel(
            name='SriImpuesto',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('code', models.CharField(max_length=2, unique=True)),
                ('name', models.CharField(max_length=100)),
                ('percent', models.DecimalField(decimal_places=2, max_digits=5)),
                ('is_active', models.BooleanField(default=True)),
            ],
            options={
                'verbose_name': 'Impuesto SRI',
                'verbose_name_plural': 'Impuestos SRI',
            },
        ),
        migrations.CreateModel(
            name='SriTipoComprobante',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('code', models.CharField(max_length=2, unique=True)),
                ('name', models.CharField(max_length=100)),
                ('description', models.TextField(blank=True)),
            ],
            options={
                'verbose_name': 'Tipo Comprobante SRI',
                'verbose_name_plural': 'Tipos Comprobante SRI',
            },
        ),
        migrations.CreateModel(
            name='InvoiceSRIExtension',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('ambiente', models.IntegerField(choices=[(1, 'Pruebas'), (2, 'Producción')], default=1)),
                ('access_key', models.CharField(help_text='Clave acceso SRI (49 dígitos)', max_length=50, unique=True)),
                ('sri_status', models.CharField(choices=[('draft', 'Borrador'), ('pending', 'Pendiente envío'), ('sent', 'Enviada a SRI'), ('accepted', 'Aceptada SRI'), ('rejected', 'Rechazada SRI'), ('cancelled', 'Anulada')], default='pending', max_length=20)),
                ('sri_message', models.TextField(blank=True, help_text='Mensaje respuesta SRI')),
                ('sri_xml_autorizado', models.TextField(blank=True, help_text='XML autorizado por SRI')),
                ('sri_authorization_date', models.DateTimeField(blank=True, null=True)),
                ('xml_content', models.TextField(blank=True, help_text='XML firmado (enviado)')),
                ('xml_original_hash', models.CharField(blank=True, max_length=128)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('invoice', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='sri_extension', to='facturacion.invoice')),
                ('tipo_comprobante', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to='facturacion_ec.sritipocomprobante')),
            ],
            options={
                'verbose_name': 'Extensión SRI Factura',
                'verbose_name_plural': 'Extensiones SRI Facturas',
                'indexes': [
                    models.Index(fields=['sri_status'], name='facturacion_sri_sta_992769_idx'),
                    models.Index(fields=['access_key'], name='facturacion_access__17b2dc_idx'),
                ],
            },
        ),
        migrations.CreateModel(
            name='SRISendLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('timestamp', models.DateTimeField(auto_now_add=True)),
                ('endpoint', models.CharField(max_length=200)),
                ('request_xml', models.TextField(blank=True)),
                ('response_xml', models.TextField(blank=True)),
                ('response_code', models.CharField(blank=True, max_length=20)),
                ('success', models.BooleanField(default=False)),
                ('error_message', models.TextField(blank=True)),
                ('invoice_extension', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='sri_logs', to='facturacion_ec.invoicesriextension')),
            ],
            options={
                'verbose_name': 'Log Envío SRI',
                'verbose_name_plural': 'Logs Envíos SRI',
                'ordering': ['-timestamp'],
            },
        ),
        migrations.CreateModel(
            name='CompanyLicense',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('activated_at', models.DateTimeField(auto_now_add=True)),
                ('expires_at', models.DateTimeField(blank=True, null=True)),
                ('is_active', models.BooleanField(default=True)),
                ('is_trial', models.BooleanField(default=False)),
                ('invoices_this_month', models.IntegerField(default=0)),
                ('current_month_year', models.CharField(blank=True, max_length=7)),
                ('company', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='facturacion_ec_licenses', to='core_companies.company')),
                ('license_type', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='facturacion_ec.sritipocomprobante')),
            ],
            options={
                'verbose_name': 'Licencia Facturación EC',
                'verbose_name_plural': 'Licencias Facturación EC',
                'indexes': [models.Index(fields=['company', 'is_active'], name='facturacion_company_716ecd_idx')],
            },
        ),
    ]
