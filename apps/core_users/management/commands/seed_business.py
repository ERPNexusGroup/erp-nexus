# Management command — seed empresarial completo
# Uso: uv run python manage.py seed_business
"""
Crea una cadena de negocios completa para producción/QA:
- Estructura organizacional (Company + Users + Membership)
- Catálogos base (Año fiscal, Monedas, Tipos de cuenta)
- Inventario (categorías, productos, stock inicial)
- Ventas (cliente, cotización, orden, factura)
- Compras (proveedor, orden de compra)
- Catálogo SRI Ecuador (facturacion_ec)
- Configuraciones de pago (BankAccount, Commission)
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.apps import apps
from decimal import Decimal

User = get_user_model()


class Command(BaseCommand):
    help = "Crea una cadena de negocios completa para pruebas"

    def add_arguments(self, parser):
        parser.add_argument(
            "--skip-sri",
            action="store_true",
            help="No crear catálogo SRI",
        )
        parser.add_argument(
            "--skip-inventory",
            action="store_true",
            help="No crear productos/inventario",
        )

    def handle(self, *args, **options):
        skip_sri = options["skip_sri"]
        skip_inventory = options["skip_inventory"]

        self.stdout.write(self.style.MIGRATE_HEADING("=" * 60))
        self.stdout.write(self.style.MIGRATE_HEADING("   SEED EMPRESARIAL ERP NEXUS"))
        self.stdout.write(self.style.MIGRATE_HEADING("=" * 60 + "\n"))

        # 1. USUARIOS
        self.stdout.write(self.style.NOTICE("📋 1. USUARIOS"))
        admin = self._create_users()
        self.stdout.write("")

        # 2. COMPANY + MEMBERSHIP
        self.stdout.write(self.style.NOTICE("🏢 2. ORGANIZACIÓN"))
        company = self._create_company(admin)
        self.stdout.write("")

        # 3. CATÁLOGOS BASE
        self.stdout.write(self.style.NOTICE("📚 3. CATÁLOGOS BASE"))
        self._create_fiscal_year(company)
        self._create_currency()
        self._create_account_types(company)
        self.stdout.write("")

        # 4. INVENTARIO
        if not skip_inventory:
            self.stdout.write(self.style.NOTICE("📦 4. INVENTARIO"))
            self._create_products()
            self.stdout.write("")

        # 5. CLIENTES Y PROVEEDORES
        self.stdout.write(self.style.NOTICE("👥 5. CLIENTES Y PROVEEDORES"))
        customer = self._create_customers(company)
        supplier = self._create_suppliers(company)
        self.stdout.write("")

        # 6. VENTAS
        self.stdout.write(self.style.NOTICE("🛒 6. CICLO DE VENTAS"))
        quote = self._create_quote(customer, admin)
        order = self._create_order(customer, admin, quote)
        invoice = self._create_invoice(company, customer, admin, order)
        self.stdout.write("")

        # 7. COMPRAS
        self.stdout.write(self.style.NOTICE("📥 7. CICLO DE COMPRAS"))
        purchase_order = self._create_purchase_order(supplier, admin)
        self.stdout.write("")

        # 8. PAGOS
        self.stdout.write(self.style.NOTICE("💳 8. PAGOS Y BANCOS"))
        bank_account = self._create_bank_account(admin)
        self._create_commissions(admin, order)
        self.stdout.write("")

        # 9. SRI (ECUADOR)
        if not skip_sri:
            self.stdout.write(self.style.NOTICE("🇪🇨 9. CATÁLOGO SRI ECUADOR"))
            self._create_sri_catalog()
            self.stdout.write("")

        # RESUMEN
        self._print_summary(admin, company, customer, supplier, invoice, purchase_order, bank_account)

    def _create_users(self):
        """Crea usuarios: admin, vendedor, comprador, contador."""
        self.stdout.write("   👤 Creando usuarios...")

        users_data = [
            {
                "username": "admin",
                "email": "admin@nexus.ec",
                "first_name": "Walter",
                "last_name": "Cun",
                "is_staff": True,
                "is_superuser": True,
                "password": "admin123",
            },
            {
                "username": "vendedor",
                "email": "vendedor@nexus.ec",
                "first_name": "Carlos",
                "last_name": "Mendoza",
                "is_staff": False,
                "is_superuser": False,
                "password": "vendedor123",
            },
            {
                "username": "comprador",
                "email": "comprador@nexus.ec",
                "first_name": "Ana",
                "last_name": "Pérez",
                "is_staff": False,
                "is_superuser": False,
                "password": "comprador123",
            },
            {
                "username": "contador",
                "email": "contador@nexus.ec",
                "first_name": "Luis",
                "last_name": "Gómez",
                "is_staff": True,
                "is_superuser": False,
                "password": "contador123",
            },
        ]

        created_users = []
        for data in users_data:
            pwd = data.pop("password")
            user, created = User.objects.get_or_create(
                username=data["username"],
                defaults=data,
            )
            if created:
                user.set_password(pwd)
                user.save()
                self.stdout.write(f"     ✅ {data['username']} ({data['email']})")
            else:
                self.stdout.write(f"     ℹ️ {data['username']} ya existe")
            created_users.append(user)

        return created_users[0]

    def _create_company(self, admin):
        """Crea company principal y membership."""
        self.stdout.write("   🏢 Creando company...")
        Company = apps.get_model("core_companies", "Company")

        company, created = Company.objects.get_or_create(
            ruc="1791234567001",
            defaults={
                "name": "Nexus Business Group S.A.",
                "slug": "nexus-group",
                "address": "Av. 9 de Octubre N10-25 y Chimborazo, Guayaquil",
                "phone": "+593 4 2500-800",
                "email": "contacto@nexus.ec",
                "establishment_code": "001",
                "point_emission_code": "001",
            },
        )
        if created:
            self.stdout.write(f"     ✅ {company.name} (RUC: {company.ruc})")
        else:
            self.stdout.write(f"     ℹ️ Company ya existe")

        Membership = apps.get_model("core_companies", "Membership")
        membership, m_created = Membership.objects.get_or_create(
            user=admin,
            company=company,
            defaults={"role": "owner", "status": "active", "is_owner": True},
        )
        if m_created:
            self.stdout.write(f"     ✅ Membership: {admin.username} → Owner")
        else:
            self.stdout.write(f"     ℹ️ Membership ya existe")

        return company

    def _create_fiscal_year(self, company):
        """Crea año fiscal 2025."""
        self.stdout.write("   📅 Año fiscal...")
        try:
            FiscalYear = apps.get_model("core_fiscal_year", "FiscalYear")
            fy, created = FiscalYear.objects.get_or_create(
                name="2025",
                company=company,
                defaults={
                    "start_date": "2025-01-01",
                    "end_date": "2025-12-31",
                    "is_active": True,
                },
            )
            if created:
                self.stdout.write(f"     ✅ {fy.name} ({fy.start_date} → {fy.end_date})")
            else:
                self.stdout.write(f"     ℹ️ Año fiscal ya existe")
        except LookupError:
            self.stdout.write(self.style.WARNING("     ⚠️ core_fiscal_year no disponible"))

    def _create_currency(self):
        """Crea monedas USD y EUR."""
        self.stdout.write("   💱 Monedas...")
        try:
            Currency = apps.get_model("core_currency", "Currency")
            usd, _ = Currency.objects.get_or_create(code="USD", defaults={"name": "Dólar Estadounidense", "symbol": "$"})
            eur, _ = Currency.objects.get_or_create(code="EUR", defaults={"name": "Euro", "symbol": "€"})
            self.stdout.write(f"     ✅ USD, EUR")
        except LookupError:
            self.stdout.write(self.style.WARNING("     ⚠️ core_currency no disponible"))

    def _create_account_types(self, company):
        """Crea tipos de cuenta y cuenta raíz."""
        self.stdout.write("   📊 Cuentas contables...")
        try:
            AccountType = apps.get_model("core_chart_of_accounts", "AccountType")
            Account = apps.get_model("core_chart_of_accounts", "Account")

            tipos = [
                ("1", "Activo", "debit"),
                ("2", "Pasivo", "credit"),
                ("3", "Patrimonio", "credit"),
                ("4", "Ingreso", "credit"),
                ("5", "Gasto", "debit"),
            ]
            for code, name, nature in tipos:
                AccountType.objects.get_or_create(code=code, defaults={"name": name, "nature": nature})

            tipo_activo = AccountType.objects.get(code="1")
            Account.objects.get_or_create(
                code="1",
                company=company,
                defaults={"name": "Activos", "account_type": tipo_activo},
            )
            count = Account.objects.count()
            self.stdout.write(f"     ✅ {AccountType.objects.count()} tipos + {count} cuentas")
        except LookupError:
            self.stdout.write(self.style.WARNING("     ⚠️ core_chart_of_accounts no disponible"))

    def _create_products(self):
        """Crea productos de inventario."""
        self.stdout.write("   📦 Creando productos...")
        Product = apps.get_model("inventory", "Product")
        Category = apps.get_model("inventory", "Category")

        cat, _ = Category.objects.get_or_create(code="GEN", defaults={"name": "General", "is_active": True})

        productos = [
            {"sku": "LAP-001", "name": "Laptop HP EliteBook 840 G9", "unit_price": Decimal("1299.99"), "stock": 25, "min_stock": 5},
            {"sku": "MON-001", "name": "Monitor Dell Ultrasharp 27\"", "unit_price": Decimal("449.50"), "stock": 40, "min_stock": 10},
            {"sku": "TEC-001", "name": "Teclado Mecánico Keychron K2", "unit_price": Decimal("89.99"), "stock": 100, "min_stock": 20},
            {"sku": "MOU-001", "name": "Mouse Logitech MX Master 3S", "unit_price": Decimal("99.99"), "stock": 75, "min_stock": 15},
            {"sku": "SIL-001", "name": "Silla Ergonómica Herman Miller", "unit_price": Decimal("850.00"), "stock": 10, "min_stock": 2},
            {"sku": "IMP-001", "name": "Impresora Epson L3150", "unit_price": Decimal("259.00"), "stock": 30, "min_stock": 5},
            {"sku": "RED-001", "name": "Router TP-Link Archer AX50", "unit_price": Decimal("129.99"), "stock": 50, "min_stock": 10},
            {"sku": "AUD-001", "name": "Audífonos Sony WH-1000XM5", "unit_price": Decimal("349.99"), "stock": 20, "min_stock": 5},
            {"sku": "CAM-001", "name": "Webcam Logitech C920s", "unit_price": Decimal("79.99"), "stock": 60, "min_stock": 10},
            {"sku": "EST-001", "name": "Estantería Metálica 5 Niveles", "unit_price": Decimal("189.00"), "stock": 15, "min_stock": 3},
        ]

        created = 0
        for p in productos:
            prod, c = Product.objects.get_or_create(
                sku=p["sku"],
                defaults={
                    "name": p["name"],
                    "category": cat,
                    "unit_price": p["unit_price"],
                    "stock_quantity": p["stock"],
                    "min_stock": p["min_stock"],
                },
            )
            if c:
                created += 1

        total = Product.objects.count()
        self.stdout.write(f"     ✅ {created} productos creados ({total} total)")

    def _create_customers(self, company):
        """Crea clientes de ejemplo."""
        self.stdout.write("   👤 Clientes...")
        Customer = apps.get_model("facturacion", "Customer")

        clientes = [
            {"name": "Juan Pérez", "email": "juan.perez@techcorp.ec", "phone": "+593 99 123 4567", "id_type": "05", "id_number": "1723456789", "address": "Guayaquil, Centro"},
            {"name": "María González", "email": "maria.gonzalez@edutec.ec", "phone": "+593 99 765 4321", "id_type": "05", "id_number": "1750987654", "address": "Quito, Norte"},
            {"name": "Comercial XYZ S.A.", "email": "ventas@comercialxyz.ec", "phone": "+593 4 255 6789", "id_type": "04", "id_number": "0991234567001", "razon_social": "Comercial XYZ S.A.", "address": "Guayaquil, Industrial"},
            {"name": "Distribuidora ABC", "email": "pedidos@distribuidoraabc.ec", "phone": "+593 4 300 1000", "id_type": "04", "id_number": "1792345678001", "razon_social": "Distribuidora ABC", "address": "Cuenca, Centro"},
        ]

        created = 0
        for c in clientes:
            cust, created_flag = Customer.objects.get_or_create(
                company=company,
                identification_number=c["id_number"],
                defaults={
                    "name": c["name"],
                    "email": c["email"],
                    "phone": c["phone"],
                    "identification_type": c["id_type"],
                    "razon_social": c.get("razon_social") or c["name"],
                    "address": c["address"],
                },
            )
            if created_flag:
                created += 1

        self.stdout.write(f"     ✅ {created} clientes creados")
        return Customer.objects.filter(company=company).first()

    def _create_suppliers(self, company):
        """Crea proveedores (Customer + Supplier profile)."""
        self.stdout.write("   🏭 Proveedores...")
        Customer = apps.get_model("facturacion", "Customer")
        Supplier = apps.get_model("purchases", "Supplier")

        proveedores = [
            {"name": "Tech Import S.A.", "email": "compras@techimport.ec", "phone": "+593 4 2500-100", "id_number": "1793456789001", "vendor_number": "V-001"},
            {"name": "Distribuidora Nacional PC", "email": "ventas@dnpc.ec", "phone": "+593 4 2500-200", "id_number": "0994567890001", "vendor_number": "V-002"},
        ]

        created = 0
        for p in proveedores:
            cust, _ = Customer.objects.get_or_create(
                company=company,
                identification_number=p["id_number"],
                defaults={
                    "name": p["name"],
                    "email": p["email"],
                    "phone": p["phone"],
                    "identification_type": "04",
                    "razon_social": p["name"],
                    "address": "Guayaquil",
                },
            )
            sup, sup_created = Supplier.objects.get_or_create(
                customer=cust,
                defaults={
                    "vendor_number": p["vendor_number"],
                    "rating": 5,
                    "payment_terms_days": 30,
                },
            )
            if sup_created:
                created += 1
                self.stdout.write(f"     ✅ {sup.vendor_number} — {sup.customer.name}")

        self.stdout.write(f"     ✅ {created} proveedores creados")
        return Supplier.objects.first()

    def _create_quote(self, customer, admin):
        """Crea cotización con 3 productos."""
        self.stdout.write("   📝 Cotización...")
        Quote = apps.get_model("sales", "Quote")
        QuoteLine = apps.get_model("sales", "QuoteLine")
        Product = apps.get_model("inventory", "Product")

        quote, _ = Quote.objects.get_or_create(
            quote_number="COT-2025-0001",
            defaults={
                "customer": customer,
                "issue_date": timezone.now().date(),
                "expiry_date": (timezone.now() + timezone.timedelta(days=15)).date(),
                "status": "sent",
                "notes": "Cotización válida por 15 días",
            },
        )

        productos = Product.objects.filter(is_active=True)[:3]
        for idx, prod in enumerate(productos, 1):
            qty = idx + 1
            subtotal = qty * prod.unit_price
            QuoteLine.objects.get_or_create(
                quote=quote,
                product=prod,
                defaults={
                    "quantity": qty,
                    "unit_price": prod.unit_price,
                    "subtotal": subtotal,
                },
            )
        # Calcular totales
        lines = quote.lines.all()
        subtotal = sum(l.subtotal for l in lines)
        quote.subtotal = subtotal
        quote.tax = subtotal * Decimal("0.12")
        quote.total = subtotal + quote.tax
        quote.save(update_fields=["subtotal", "tax", "total"])
        self.stdout.write(f"     ✅ {quote.quote_number} → Total: ${quote.total}")
        return quote

    def _create_order(self, customer, admin, quote):
        """Convierte cotización a orden de venta."""
        self.stdout.write("   🛒 Orden de venta...")
        Order = apps.get_model("sales", "Order")
        OrderLine = apps.get_model("sales", "OrderLine")

        order, _ = Order.objects.get_or_create(
            order_number="VEN-2025-0001",
            defaults={
                "customer": customer,
                "issue_date": timezone.now().date(),
                "delivery_date": (timezone.now() + timezone.timedelta(days=7)).date(),
                "status": "confirmed",
            },
        )

        for ql in quote.lines.all():
            subtotal = ql.quantity * ql.unit_price
            OrderLine.objects.get_or_create(
                order=order,
                product=ql.product,
                defaults={
                    "quantity": ql.quantity,
                    "unit_price": ql.unit_price,
                    "subtotal": subtotal,
                },
            )
        # Calcular totales
        lines = order.lines.all()
        subtotal = sum(l.subtotal for l in lines)
        order.subtotal = subtotal
        order.tax = subtotal * Decimal("0.12")
        order.total = subtotal + order.tax
        order.save(update_fields=["subtotal", "tax", "total"])
        self.stdout.write(f"     ✅ {order.order_number} → Total: ${order.total}")
        return order

    def _create_invoice(self, company, customer, admin, order):
        """Crea factura desde orden."""
        self.stdout.write("   📄 Factura...")
        Invoice = apps.get_model("facturacion", "Invoice")
        InvoiceLine = apps.get_model("facturacion", "InvoiceLine")

        invoice, _ = Invoice.objects.get_or_create(
            number="001-001-000000001",
            defaults={
                "company": company,
                "customer": customer,
                "date": timezone.now().date(),
                "subtotal": order.subtotal,
                "tax_total": order.tax,
                "total": order.total,
                "status": "draft",
                "created_by": admin,
            },
        )

        for ol in order.lines.all():
            qty = ol.quantity
            up = ol.unit_price
            subtotal = qty * up
            tax_rate = Decimal("12.00")
            tax_amount = subtotal * (tax_rate / Decimal("100"))
            total = subtotal + tax_amount
            InvoiceLine.objects.get_or_create(
                invoice=invoice,
                product=ol.product,
                defaults={
                    "quantity": qty,
                    "unit_price": up,
                    "subtotal": subtotal,
                    "tax_rate": tax_rate,
                    "tax_amount": tax_amount,
                    "total": total,
                },
            )

        self.stdout.write(f"     ✅ Factura {invoice.number} [{invoice.status}]")
        return invoice

    def _create_purchase_order(self, supplier, admin):
        """Crea orden de compra."""
        self.stdout.write("   📥 Orden de compra...")
        PurchaseOrder = apps.get_model("purchases", "PurchaseOrder")
        POLine = apps.get_model("purchases", "PurchaseOrderLine")
        Product = apps.get_model("inventory", "Product")

        po, _ = PurchaseOrder.objects.get_or_create(
            po_number="OC-2025-0001",
            defaults={
                "supplier": supplier,
                "order_date": timezone.now().date(),
                "expected_delivery": (timezone.now() + timezone.timedelta(days=7)).date(),
                "status": "approved",
            },
        )

        productos = Product.objects.filter(is_active=True)[:2]
        for prod in productos:
            POLine.objects.get_or_create(
                po=po,
                product=prod,
                defaults={
                    "quantity_ordered": 50,
                    "unit_price": prod.unit_price * Decimal("0.9"),
                },
            )
        # Calcular totales
        from decimal import Decimal as _D
        subtotal = _D("0")
        for line in po.lines.all():
            subtotal += line.subtotal
        tax_rate = _D("0.12")
        po.subtotal = subtotal
        po.tax = subtotal * tax_rate
        po.total = subtotal + po.tax
        po.save(update_fields=["subtotal", "tax", "total"])
        self.stdout.write(f"     ✅ {po.po_number} → Total: ${po.total}")
        return po

    def _create_bank_account(self, admin_user):
        """Crea cuenta bancaria del usuario."""
        self.stdout.write("   🏦 Cuenta bancaria...")
        BankAccount = apps.get_model("core_payments", "BankAccount")

        account, _ = BankAccount.objects.get_or_create(
            user=admin_user,
            bank_code="01",
            account_number="00109987654321",
            defaults={
                "bank_name": "Banco del Pacífico",
                "account_type": BankAccount.AccountType.CHECKING,
                "holder_name": "Walter Cun",
                "holder_identification": "1791234567001",
                "is_verified": True,
                "is_default": True,
            },
        )
        self.stdout.write(f"     ✅ {account.bank_name} - {account.account_number}")
        return account

    def _create_commissions(self, admin_user, order):
        """Registra comisiones de ejemplo."""
        self.stdout.write("   💰 Comisiones...")
        Commission = apps.get_model("core_payments", "Commission")

        # Comisión del 10% sobre la orden de venta
        amount = order.total * Decimal("0.10")
        comm, _ = Commission.objects.get_or_create(
            user=admin_user,
            sale=order,
            defaults={
                "amount": amount,
                "description": f"Comisión venta {order.order_number}",
                "status": "PENDING",
            },
        )
        self.stdout.write(f"     ✅ Comisión pendiente: ${comm.amount}")

    def _create_sri_catalog(self):
        """Catálogo SRI Ecuador completo."""
        self.stdout.write("   🇪🇨 Catálogo SRI...")
        from modules.facturacion_ec.models import SriAmbiente, SriTipoEmision, SriServicio, SriTipoComprobante

        SriAmbiente.objects.get_or_create(code=1, defaults={"name": "Pruebas"})
        SriAmbiente.objects.get_or_create(code=2, defaults={"name": "Producción"})
        SriTipoEmision.objects.get_or_create(code="1", defaults={"name": "Normal"})
        SriServicio.objects.get_or_create(code="2", defaults={"nombre": "Autorizar comprobante", "descripcion": "Servicio de autorización SRI"})

        tipos = [
            ("01", "Factura", "Factura de venta"),
            ("02", "Nota de Crédito", "Nota de crédito"),
            ("03", "Nota de Débito", "Nota de débito"),
            ("04", "Guía de Remisión", "Guía de remisión"),
            ("05", "Liquidación de Compra", "Liquidación de compra"),
            ("06", "Nota de Crédito", "Nota de crédito por devolución"),
            ("07", "Comprobante de Retención", "Comprobante de retención"),
            ("08", "Comprobante de Cancelación", "Comprobante de cancelación"),
            ("09", "Guía de Remisión", "Guía para transporte"),
            ("10", "Factura de Exportación", "Exportación"),
            ("11", "Factura de Vínculo", "Vínculo tributario"),
            ("12", "Ticket", "Máquina registradora"),
            ("20", "Factura Simplificada", "Factura simplificada"),
        ]
        for codigo, nombre, desc in tipos:
            SriTipoComprobante.objects.get_or_create(code=codigo, defaults={"name": nombre, "description": desc})

        total = SriTipoComprobante.objects.count()
        self.stdout.write(f"     ✅ {total} tipos, 2 ambientes, 1 emisión, 1 servicio")

    def _print_summary(self, admin, company, customer, supplier, invoice, po, bank_account):
        from django.db.models import Sum

        Product = apps.get_model("inventory", "Product")
        Commission = apps.get_model("core_payments", "Commission")

        self.stdout.write("\n" + "=" * 60)
        self.stdout.write(self.style.SUCCESS("✅ SEED EMPRESARIAL COMPLETADO"))
        self.stdout.write("=" * 60)
        self.stdout.write("")
        self.stdout.write(self.style.NOTICE("🔐 ACCESO ADMIN:"))
        self.stdout.write(f"   URL:    http://localhost:8001/admin/")
        self.stdout.write(f"   User:   admin")
        self.stdout.write(f"   Pass:   admin123")
        self.stdout.write("")
        self.stdout.write(self.style.NOTICE("🏢 ORGANIZACIÓN:"))
        self.stdout.write(f"   • {company.name}")
        self.stdout.write(f"   • RUC: {company.ruc}")
        self.stdout.write(f"   • {company.address}")
        self.stdout.write("")
        self.stdout.write(self.style.NOTICE("📊 CADENA DE NEGOCIOS:"))
        self.stdout.write(f"   • Clientes:           3 activos")
        self.stdout.write(f"   • Proveedores:        2 registrados")
        self.stdout.write(f"   • Productos:          {Product.objects.count()} en inventario")

        Quote = apps.get_model("sales", "Quote")
        Order = apps.get_model("sales", "Order")
        q = Quote.objects.first()
        o = Order.objects.first()
        if q:
            self.stdout.write(f"   • Cotización:         {q.quote_number}")
        if o:
            self.stdout.write(f"   • Orden Venta:        {o.order_number}")

        self.stdout.write(f"   • Factura:            {invoice.number} [{invoice.status}]")
        self.stdout.write(f"   • Orden Compra:       {po.po_number} [{po.status}]")
        self.stdout.write("")
        self.stdout.write(self.style.NOTICE("💰 FINANZAS:"))
        self.stdout.write(f"   • Cuenta Bancaria:    {bank_account.bank_name} — {bank_account.account_number}")
        com_total = Commission.objects.aggregate(total=Sum('amount'))['total'] or 0
        self.stdout.write(f"   • Comisiones:         ${com_total}")
        self.stdout.write("")
        self.stdout.write(self.style.NOTICE("🇪🇨 SRI ECUADOR:"))
        self.stdout.write(f"   • Catálogo SRI:       cargado (13 tipos, 2 ambientes)")
        self.stdout.write("")
        self.stdout.write(self.style.WARNING("💡 PRÓXIMOS PASOS:"))
        self.stdout.write("   1. Aprobar factura → cambiar status a 'sent'")
        self.stdout.write("   2. Generar credenciales API para SRI")
        self.stdout.write("   3. Crear API Tokens para usuarios")
        self.stdout.write("   4. Probar endpoints REST en /api/v1/")
        self.stdout.write("   5. Configurar Sentry + backups automáticos")
        self.stdout.write("=" * 60)
