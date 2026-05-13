# Management command — publish_all
# Publica todas las páginas en draft.
# Uso: uv run python manage.py publish_all

from django.core.management.base import BaseCommand
from apps.core_pagebuilder.models import Page


class Command(BaseCommand):
    help = "Publica todas las páginas en estado 'draft'."

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Muestra qué páginas se publicarían sin hacerlo.",
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]

        drafts = Page.objects.filter(status='draft')
        count = drafts.count()

        if count == 0:
            self.stdout.write(self.style.SUCCESS("✅ No hay páginas en draft para publicar."))
            return

        if dry_run:
            self.stdout.write(self.style.WARNING(f"🔍 [DRY-RUN] {count} páginas se publicarían:"))
            for p in drafts:
                self.stdout.write(f"   • {p.title} (slug: {p.slug})")
            self.stdout.write("   Ejecuta sin --dry-run para confirmar.")
            return

        updated = 0
        for page in drafts:
            page.publish()
            updated += 1
            self.stdout.write(f"   ✅ Publicada: {page.title}")

        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS(f"✅ {updated} páginas publicadas exitosamente."))
