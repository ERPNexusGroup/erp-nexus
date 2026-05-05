#!/usr/bin/env python3
"""
Test end-to-end del módulo facturacion_ec SIN enviar a SRI
"""
import os
from datetime import date

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "erp_nexus.settings")
import django; django.setup()

from django.contrib.auth import get_user_model
from apps.core_companies.models import Company, Membership
from modules.facturacion_ec.models import Customer, Product, Invoice, InvoiceLine, LicenseType, CompanyLicense, SriTipoComprobante
from modules.facturacion_ec.services.code_unique import generate_access_key, generate_invoice_number
from modules.facturacion_ec.services import XMLGenerator

User = get_user_model()

print("=" * 60)
print("  TEST FACTURACION_EC — End-to-End (sin SRI)")
print("=" * 60); print()

# 1. Company
print("1️⃣  Company...")
company = Company.objects.filter(slug="demo-ecuador-sa").first()
if not company:
    company = Company.objects.create(
        slug="demo-ecuador-sa", name="Demo Ecuador SA",
        ruc="1791234567001", tax_id="1791234567001",
        address="Av. Amazonas N34-56, Quito",
        phone="+593 2 555 1234", email="demo@demo-ec.com",
        establishment_code="001", point_emission_code="001",
    )
    print("   ✅ Creada")
else:
    print(f"   ✅ Existente: {company.name}")
print()

# 2. Membership
print("2️⃣  Membership...")
user = User.objects.filter(is_superuser=True).first() or User.objects.first()
Membership.objects.get_or_create(user=user, company=company, defaults={"role":"owner","is_owner":True,"status":"active"})
print(f"   ✅ {user.username} → {company.name}")
print()

# 3. License + CompanyLicense
print("3️⃣  Licencia...")
lt_free = LicenseType.objects.get(plan_id="free")
CompanyLicense.objects.get_or_create(company=company, license_type=lt_free, defaults={"is_active": True})
print(f"   ✅ Plan: {lt_free.display_name}")
print()

# 4. Customer
print("4️⃣  Customer...")
customer, _ = Customer.objects.get_or_create(
    company=company, identification_number="1750234556",
    defaults={"identification_type":"05","name":"Cliente Demo","address":"Guayaquil","email":"cliente@demo.com"}
)
print(f"   ✅ {customer.name}")
print()

# 5. Product
print("5️⃣  Product...")
product, _ = Product.objects.get_or_create(
    company=company, code="DEMO-001",
    defaults={"name":"Producto Demo","unit_price":100.00,"tax_percent":12.00,"tax_tariff":"2"}
)
print(f"   ✅ {product.name}")
print()

# 6. SriTipoComprobante
print("6️⃣  SriTipoComprobante...")
tipo_comp, _ = SriTipoComprobante.objects.get_or_create(code="01", defaults={"name":"Factura","description":"Factura electrónica"})
print(f"   ✅ {tipo_comp.code} - {tipo_comp.name}")
print()

# 7. Número + clave acceso
print("7️⃣  Generando factura...")
seq = 1
invoice_number = generate_invoice_number(company.establishment_code, company.point_emission_code, seq)
access_key = generate_access_key(ruc=company.ruc, ambiente=1, establishment_code=company.establishment_code, emission_point=company.point_emission_code, sequential=str(seq).zfill(15), date=date.today())
print(f"   Número: {invoice_number}")
print(f"   Clave: {access_key}")
print()

# 8. Invoice + Line
print("8️⃣  Creando Invoice + Line...")
invoice = Invoice.objects.create(
    company=company, number=invoice_number, date=date.today(), customer=customer,
    subtotal=200.00, tax_total=24.00, total=224.00, ambiente=1,
    created_by=user, access_key=access_key, sri_status="pending", tipo_comprobante=tipo_comp
)
line = InvoiceLine.objects.create(invoice=invoice, product=product, quantity=2, unit_price=100.00, subtotal=200.00, tax_rate=12.00, tax_amount=24.00, total=224.00)
print(f"   ✅ Invoice #{invoice.number}")
print()

# 9. Verificación totals
print("9️⃣  Verificando totals...")
total_lines = float(sum(l.total for l in invoice.lines.all()))
total_invoice = float(invoice.total)
assert abs(total_lines - total_invoice) < 0.01
print(f"   ${total_lines:.2f} == ${total_invoice:.2f} ✅")
print()

# 10. XML
print("🔟 XML Generator...")
xml_str = XMLGenerator(company).generate(invoice, [line])
print(f"   ✅ XML generado ({len(xml_str)} bytes)")
print(f"   'factura' en XML: {'factura' in xml_str}")
print(f"   'claveAcceso' en XML: {'claveAcceso' in xml_str}")
print()

print("=" * 60)
print("  ✅ TEST COMPLETO — Módulo facturacion_ec operativo")
print("=" * 60); print()
print("📊 Datos en BD:")
print(f"   • Company: {company.name} [{company.ruc}]")
print(f"   • Customer: {customer.name} [{customer.identification_number}]")
print(f"   • Product: {product.code} - {product.name}")
print(f"   • Invoice: #{invoice.number} | Total: ${invoice.total}")
print(f"   • LicenseType: {lt_free.display_name}")
print()
print("🔐 Para envío a SRI:")
print("   1. Configurar FACTURACION_EC_CERT_PATH y FACTURACION_EC_CERT_PASSWORD")
print("   2. Ejecutar: uv run python manage.py send_pending_facturacion")
print()
print("🌐 Admin: http://localhost:8000/admin")
print()
