"""
manage.py catalog — Comandos de marketplace/catálogo.
"""
from pathlib import Path

from django.core.management.base import BaseCommand

from apps.core_marketplace.models import ModuleCatalogItem


class Command(BaseCommand):
    help = "Catálogo de módulos ERP Nexus (search, list)."

    def add_arguments(self, parser):
        subparsers = parser.add_subparsers(dest="subcommand", required=True)

        # search
        search = subparsers.add_parser("search", help="Buscar módulos")
        search.add_argument("--category", help="Filtrar por categoría/dominio")
        search.add_argument("--name", help="Buscar por nombre")

        # available
        subparsers.add_parser("available", help="Módulos disponibles en DB")

    def handle(self, *args, **options):
        if options["subcommand"] == "search":
            self._search(options.get("category"), options.get("name"))
        elif options["subcommand"] == "available":
            self._available()

    def _search(self, category: str | None, name: str | None):
        qs = ModuleCatalogItem.objects.filter(is_active=True)

        if name:
            qs = qs.filter(technical_name__icontains=name)

        if not qs.exists():
            self.stdout.write("No se encontraron módulos.")
            return

        self.stdout.write(f"\n{'Nombre':<30} {'Versión':<10} {'Estado':<10}")
        self.stdout.write("-" * 50)

        for m in qs:
            self.stdout.write(f"{m.technical_name:<30} {m.version:<10} {m.status}")

        self.stdout.write(f"\nTotal: {qs.count()} módulos")

    def _available(self):
        modules = ModuleCatalogItem.objects.filter(is_active=True)

        if not modules.exists():
            self.stdout.write("No hay módulos activos.")
            return

        for m in modules:
            self.stdout.write(f"  • {m.technical_name} v{m.version} ({m.status})")
