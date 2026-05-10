# Management command: register_facturacion
from django.core.management.base import BaseCommand
from apps.core_marketplace.models import ModuleCatalogItem


class Command(BaseCommand):
    help = "Registra el módulo facturacion en el catálogo del marketplace"

    def handle(self, *args, **options):
        data = {
            "technical_name": "facturacion",
            "version": "0.1.0",
            "source": "local",
            "installed_path": "apps/facturacion",
            "django_app": "apps.facturacion",
            "status": "active",
            "is_active": True,
            "admin_menu": {
                "name": "Facturación Electrónica",
                "icon": "fas fa-file-invoice-dollar",
                "order": 100,
            }
        }

        obj, created = ModuleCatalogItem.objects.update_or_create(
            technical_name=data["technical_name"],
            defaults=data
        )

        if created:
            self.stdout.write(self.style.SUCCESS(f"✅ Módulo registrado: {data['technical_name']} v{data['version']}"))
        else:
            self.stdout.write(self.style.WARNING(f"⚠️  Módulo actualizado: {data['technical_name']}"))
