# Management command — create_demo_pages
# Crea páginas demo para el page builder (Home, About, Contact)
# Uso: uv run python manage.py create_demo_pages [--reset]

from django.core.management.base import BaseCommand
from django.utils import timezone
from apps.core_pagebuilder.models import Page


class Command(BaseCommand):
    help = "Crea páginas demo para el page builder (Home, About, Contact). Use --reset para eliminar primero."

    def add_arguments(self, parser):
        parser.add_argument(
            "--reset",
            action="store_true",
            help="Elimina todas las páginas demo antes de crearlas.",
        )

    def handle(self, *args, **options):
        reset = options["reset"]

        if reset:
            deleted, _ = Page.objects.filter(slug__in=['home', 'about', 'contact']).delete()
            self.stdout.write(self.style.WARNING(f"🗑️  Eliminadas {deleted} páginas existentes."))

        created = 0

        # ─── Home Page ─────────────────────────────────────────────────────
        home, created_flag = Page.objects.get_or_create(
            slug='home',
            defaults={
                'title': 'Inicio',
                'description': 'Página principal de ERP Nexus — Bienvenido a tu panel empresarial.',
                'status': 'published',
                'layout': [
                    {
                        "type": "heading",
                        "props": {"text": "Bienvenido a ERP Nexus", "level": 1},
                        "id": "heading-1"
                    },
                    {
                        "type": "text",
                        "props": {
                            "content": (
                                "<p>ERP Nexus es tu sistema empresarial integral. "
                                "Gestiona facturación, inventario, ventas, compras y más, "
                                "todo desde un solo lugar.</p>"
                            )
                        },
                        "id": "text-1"
                    },
                    {
                        "type": "spacer",
                        "props": {"height": 30},
                        "id": "spacer-1"
                    },
                    {
                        "type": "columns",
                        "props": {
                            "children": [
                                {
                                    "type": "text",
                                    "props": {
                                        "content": "<h3>⚡ Rápido</h3><p>Procesos automatizados que ahorran tiempo.</p>"
                                    },
                                    "id": "col-1-1"
                                },
                                {
                                    "type": "text",
                                    "props": {
                                        "content": "<h3>🔒 Seguro</h3><p>Datos encriptados y cumplimiento SRI.</p>"
                                    },
                                    "id": "col-1-2"
                                },
                                {
                                    "type": "text",
                                    "props": {
                                        "content": "<h3>🌐 Escalable</h3><p>Crece con tu empresa sin límites.</p>"
                                    },
                                    "id": "col-1-3"
                                }
                            ]
                        },
                        "id": "columns-1"
                    },
                    {
                        "type": "button",
                        "props": {"label": "Comenzar →", "url": "/auth/login/", "target": "_self"},
                        "id": "btn-1"
                    }
                ],
                'meta_title': 'ERP Nexus — Inicio',
                'meta_description': 'Sistema empresarial integral para Ecuador. Facturación SRI, inventario, ventas y más.',
            }
        )
        if created_flag:
            created += 1
            self.stdout.write(self.style.SUCCESS(f"✅ Home page creada: /pages/{home.slug}/"))

        # ─── About Page ────────────────────────────────────────────────────
        about, created_flag = Page.objects.get_or_create(
            slug='about',
            defaults={
                'title': 'Acerca de',
                'description': 'Conoce más sobre ERP Nexus y nuestra misión.',
                'status': 'published',
                'layout': [
                    {
                        "type": "heading",
                        "props": {"text": "Sobre ERP Nexus", "level": 1},
                        "id": "heading-2-1"
                    },
                    {
                        "type": "text",
                        "props": {
                            "content": (
                                "<p>ERP Nexus nace de la necesidad de un sistema "
                                "empresarial moderno, accesible y adaptado a la "
                                "regulación ecuatoriana. Nuestra misión es simplificar "
                                "la gestión de empresas con tecnología de vanguardia.</p>"
                            )
                        },
                        "id": "text-2-1"
                    },
                    {
                        "type": "image",
                        "props": {
                            "src": "/static/img/about-hero.jpg",
                            "alt": "Equipo ERP Nexus",
                            "width": "800px",
                        },
                        "id": "image-2-1"
                    },
                    {
                        "type": "divider",
                        "props": {},
                        "id": "divider-2-1"
                    },
                    {
                        "type": "text",
                        "props": {
                            "content": "<h2>📬 Contacto</h2><p>Escríbenos a hola@erpnexus.ec</p>"
                        },
                        "id": "text-2-2"
                    },
                ],
                'meta_title': 'Acerca de — ERP Nexus',
                'meta_description': 'Conoce ERP Nexus, el sistema empresarial hecho en Ecuador.',
            }
        )
        if created_flag:
            created += 1
            self.stdout.write(self.style.SUCCESS(f"✅ About page creada: /pages/{about.slug}/"))

        # ─── Contact Page ──────────────────────────────────────────────────
        contact, created_flag = Page.objects.get_or_create(
            slug='contact',
            defaults={
                'title': 'Contacto',
                'description': 'Página de contacto ERP Nexus.',
                'status': 'published',
                'layout': [
                    {
                        "type": "heading",
                        "props": {"text": "Contáctanos", "level": 1},
                        "id": "heading-3-1"
                    },
                    {
                        "type": "text",
                        "props": {
                            "content": (
                                "<p>¿Tienes preguntas? Estamos aquí para ayudarte.</p>"
                            )
                        },
                        "id": "text-3-1"
                    },
                    {
                        "type": "html",
                        "props": {
                            "content": (
                                "<form action=\"#\" method=\"post\" style=\"max-width:500px\">\n"
                                "  <div style=\"margin-bottom:1rem\">\n"
                                "    <label>Nombre</label><br>\n"
                                "    <input type=\"text\" name=\"name\" style=\"width:100%;padding:0.5rem\">\n"
                                "  </div>\n"
                                "  <div style=\"margin-bottom:1rem\">\n"
                                "    <label>Email</label><br>\n"
                                "    <input type=\"email\" name=\"email\" style=\"width:100%;padding:0.5rem\">\n"
                                "  </div>\n"
                                "  <div style=\"margin-bottom:1rem\">\n"
                                "    <label>Mensaje</label><br>\n"
                                "    <textarea name=\"message\" rows=\"5\" style=\"width:100%;padding:0.5rem\"></textarea>\n"
                                "  </div>\n"
                                "  <button type=\"submit\" class=\"cp-button btn-primary\">Enviar</button>\n"
                                "</form>"
                            )
                        },
                        "id": "html-3-1"
                    },
                ],
                'meta_title': 'Contacto — ERP Nexus',
                'meta_description': 'Contacta con el equipo de ERP Nexus para soporte o cotizaciones.',
            }
        )
        if created_flag:
            created += 1
            self.stdout.write(self.style.SUCCESS(f"✅ Contact page creada: /pages/{contact.slug}/"))

        # ─── Resumen ──────────────────────────────────────────────────────
        self.stdout.write("")
        self.stdout.write(self.style.MIGRATE_HEADING("📄 Páginas demo creadas:"))
        self.stdout.write(f"   • Total creadas: {created}")
        self.stdout.write(f"   • Home:    /pages/home/")
        self.stdout.write(f"   • About:   /pages/about/")
        self.stdout.write(f"   • Contact: /pages/contact/")
        self.stdout.write("")
        self.stdout.write(self.style.NOTICE("💡 Prueba en el navegador: http://localhost:8001/pages/home/"))
