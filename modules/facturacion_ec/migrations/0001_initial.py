# Initial migration for modules.facturacion_ec (separated plugin)
# Includes: SRI catalogs + Licensing + InvoiceSRIExtension

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('core_companies', '0001_initial'),
        ('facturacion', '0001_initial'),  # depends on core facturacion
    ]

    operations = [
        # ── Catálogos SRI ──
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
        # ── Licenciamiento ──
        migrations.CreateModel(
            name='LicenseType',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('plan_id', models.CharField(choices=[('free', 'Free (10 facturas/mes)'), ('monthly_10', 'Mensual $10/mes'), ('yearly_100', 'Anual $100/año'), ('lifetime_3500', 'Lifetime $3,500 (actualizaciones incluidas)'), ('lifetime_750', 'Lifetime $750 (sin actualizaciones)')], max_length=30, unique=True)),
                ('display_name', models.CharField(max_length=100)),
                ('description', models.TextField()),
                ('price_monthly_equivalent', models.DecimalField(decimal_places=2, help_text='Precio equivalente mensual (para comparación)', max_digits=10)),
                ('max_invoices_per_month', models.IntegerField(default=10, help_text='Límite de facturas por mes (0=ilimitado)')),
                ('allows_updates', models.BooleanField(default=False, help_text='Incluye actualizaciones de nuevas versiones')),
                ('priority_support', models.BooleanField(default=False, help_text='Soporte prioritario (email/chat directo)')),
                ('is_active', models.BooleanField(default=True)),
            ],
            options={
                'verbose_name': 'Tipo de Licencia',
                'verbose_name_plural': 'Tipos de Licencia',
            },
        ),
        migrations.CreateModel(
            name='CompanyLicense',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('activated_at', models.DateTimeField(auto_now_add=True)),
                ('expires_at', models.DateTimeField(blank=True, null=True)),
                ('last_check', models.DateTimeField(auto_now=True)),
                ('transaction_id', models.CharField(blank=True, max_length=200)),
                ('payment_provider', models.CharField(blank=True, choices=[('stripe', 'Stripe'), ('paypal', 'PayPal'), ('transfer', 'Transferencia bancaria'), ('manual', 'Manual (registrado a mano)')], max_length=50)),
                ('is_active', models.BooleanField(default=True)),
                ('is_trial', models.BooleanField(default=False)),
                ('trial_end_date', models.DateTimeField(blank=True, null=True)),
                ('invoices_this_month', models.IntegerField(default=0)),
                ('current_month_year', models.CharField(blank=True, max_length=7)),
                ('company', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='facturacion_ec_licenses', to='core_companies.company')),
                ('license_type', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='facturacion_ec.licensetype')),
            ],
            options={
                'verbose_name': 'Licencia de Empresa',
                'verbose_name_plural': 'Licencias de Empresas',
                'unique_together': {('company', 'license_type')},
            },
        ),
        # ── Extensión SRI para Facturas (core) ──
        migrations.CreateModel(
            name='InvoiceSRIExtension',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('ambiente', models.IntegerField(choices=[(1, 'Pruebas'), (2, 'Producción')], default=1)),
                ('access_key', models.CharField(blank=True, help_text='Clave de acceso SRI (49 dígitos)', max_length=50, null=True, unique=True)),
                ('xml_content', models.TextField(blank=True, help_text='XML firmado (enviado al SRI)')),
                ('xml_original_hash', models.CharField(blank=True, help_text='Hash del XML original', max_length=128)),
                ('sri_status', models.CharField(choices=[('pending', 'Pendiente envío'), ('sent', 'Enviada a SRI'), ('accepted', 'Aceptada SRI'), ('rejected', 'Rechazada SRI'), ('cancelled', 'Anulada')], default='pending', max_length=20)),
                ('sri_authorization_date', models.DateTimeField(blank=True, null=True)),
                ('sri_message', models.TextField(blank=True, help_text='Mensaje respuesta SRI')),
                ('sri_xml_autorizado', models.TextField(blank=True, help_text='XML devuelto por SRI')),
                ('guia_remision_number', models.CharField(blank=True, help_text='Número de guía de remisión', max_length=50)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('invoice', models.OneToOneField(help_text='Factura core que extiende', on_delete=django.db.models.deletion.CASCADE, related_name='sri_extension', to='facturacion.invoice')),
                ('tipo_comprobante', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to='facturacion_ec.sritipocomprobante')),
            ],
            options={
                'verbose_name': 'Extensión SRI Factura',
                'verbose_name_plural': 'Extensiones SRI Facturas',
                'ordering': ['-created_at'],
                'indexes': [models.Index(fields=['sri_status'], name='facturacion_ec_sri_status_idx'), models.Index(fields=['access_key'], name='facturacion_ec_access_key_idx')],
            },
        ),
    ]
