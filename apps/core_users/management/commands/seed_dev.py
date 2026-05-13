# Management command — seed de desarrollo rápido
# Uso: uv run python manage.py seed_dev
"""
Crea datos mínimos de prueba para desarrollo local:
- Superusuario: admin / admin123
- Company: RUC 1791234567001
- Catálogo SRI básico (ambientes, tipos emisión, servicios, tipos comprobante)
"""

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model


User = get_user_model()


class Command(BaseCommand):
    help = "Crea datos mínimos de prueba para desarrollo"

    def handle(self, *args, **options):
        from django.apps import apps

        self.stdout.write(self.style.MIGRATE_HEADING("=== Seed Desarrollo ERP NEXUS ===\n"))

        # 1. Superusuario
        self.stdout.write("👤 Superusuario...")
        admin, created = User.objects.get_or_create(
            username="admin",
            defaults={
                "email": "admin@erp-nexus.local",
                "first_name": "Admin",
                "last_name": "System",
                "is_staff": True,
                "is_superuser": True,
            },
        )
        if created:
            admin.set_password("admin123")
            admin.save()
            self.stdout.write(self.style.SUCCESS(f"  ✅ admin/admin123 creado"))
        else:
            self.stdout.write(self.style.NOTICE("  ℹ️ admin ya existe"))

        # 2. Company
        self.stdout.write("🏢 Company...")
        try:
            Company = apps.get_model("core_companies", "Company")
            company, _ = Company.objects.get_or_create(
                ruc="1791234567001",
                defaults={
                    "name": "Empresa de Prueba ERP NEXUS",
                    "slug": "empresa-prueba",
                    "address": "Av. 9 de Octubre 123, Guayaquil",
                    "phone": "+593 4 200 1000",
                    "email": "info@erp-test.ec",
                    "establishment_code": "001",
                    "point_emission_code": "001",
                },
            )
            self.stdout.write(self.style.SUCCESS(f"  ✅ {company.name} (RUC: {company.ruc})"))
        except LookupError:
            self.stdout.write(self.style.WARNING("  ⚠️ App core_companies no encontrada"))

        # 3. Catálogo SRI (facturacion_ec)
        self.stdout.write("🇪🇨 Catálogo SRI...")
        try:
            from modules.facturacion_ec.models import (
                SriAmbiente,
                SriTipoEmision,
                SriServicio,
                SriTipoComprobante,
            )

            # Ambientes
            SriAmbiente.objects.get_or_create(code=1, defaults={"name": "Pruebas"})
            SriAmbiente.objects.get_or_create(code=2, defaults={"name": "Producción"})

            # Tipos de emisión
            SriTipoEmision.objects.get_or_create(code="1", defaults={"name": "Normal"})

            # Servicios
            SriServicio.objects.get_or_create(
                code="1",
                defaults={"nombre": "Firmar comprobante", "descripcion": "Servicio de firma electrónica SRI"}
            )

            # Tipos de comprobante
            tipos = [
                ("01", "Factura", "Factura de venta"),
                ("02", "Nota de Crédito", "Nota de crédito"),
                ("03", "Nota de Débito", "Nota de débito"),
                ("04", "Guía de Remisión", "Guía de remisión"),
                ("05", "Liquidación de Compra", "Liquidación de compra"),
            ]
            for codigo, nombre, desc in tipos:
                SriTipoComprobante.objects.get_or_create(
                    code=codigo,
                    defaults={"name": nombre, "description": desc},
                )

            count = SriTipoComprobante.objects.count()
            self.stdout.write(self.style.SUCCESS(f"  ✅ Catálogo SRI: {count} tipos, 2 ambientes, 1 emisión, 1 servicio"))
        except ImportError as e:
            self.stdout.write(self.style.WARNING(f"  ⚠️ facturacion_ec no disponible: {e}"))

        self.stdout.write("\n" + "=" * 50)
        self.stdout.write(self.style.SUCCESS("✅ Seed de desarrollo completado\n"))
        self.stdout.write(self.style.NOTICE("🔐 Credenciales admin:"))
        self.stdout.write("   URL:   http://localhost:8001/admin/")
        self.stdout.write("   User:  admin")
        self.stdout.write("   Pass:  admin123")
        self.stdout.write("\n📌 Estado actual:")
        self.stdout.write("   • Superusuario activo (is_staff=True, is_superuser=True)")
        self.stdout.write("   • Company: Empresa de Prueba ERP NEXUS (RUC: 1791234567001)")
        self.stdout.write("   • Catálogo SRI cargado (si facturacion_ec disponible)")
        self.stdout.write("\n💡 Próximos pasos:")
        self.stdout.write("   1. Crear Company membership para admin")
        self.stdout.write("   2. Generar API Token para admin (en /admin/)")
        self.stdout.write("   3. Añadir productos y clientes")
        self.stdout.write("=" * 50)
