"""
Management command: refresh_catalog

Sincroniza el catálogo de módulos desde fuentes externas (GitHub, JSON, etc.).
Escanea ModuleRegistry activos y actualiza ModuleCatalogItem.
"""
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction


class Command(BaseCommand):
    help = "Refresh marketplace catalog from configured registries (GitHub, JSON, etc.)"

    def add_arguments(self, parser):
        parser.add_argument(
            "--registry",
            type=str,
            help="Specific registry name to sync (default: all active)",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would change without saving",
        )
        parser.add_argument(
            "--force",
            action="store_true",
            help="Force update even if version unchanged",
        )

    def handle(self, *args, **options):
        registry_name = options.get("registry")
        dry_run = options.get("dry_run", False)
        force = options.get("force", False)

        from apps.core_marketplace.models import ModuleRegistry, ModuleCatalogItem

        # Determinar registros a procesar
        if registry_name:
            registries = ModuleRegistry.objects.filter(
                name=registry_name, is_active=True
            )
            if not registries.exists():
                raise CommandError(f"Registry '{registry_name}' not found or inactive")
        else:
            registries = ModuleRegistry.objects.filter(is_active=True)

        if not registries.exists():
            self.stdout.write(self.style.WARNING("No active registries found."))
            return

        total_created = 0
        total_updated = 0
        total_unchanged = 0
        total_deactivated = 0

        for registry in registries:
            self.stdout.write(
                self.style.MIGRATE_LABEL(f"\nSyncing registry: {registry.name}")
            )

            if registry.source_type == 'github':
                created, updated, unchanged, deactivated = self._sync_github(
                    registry, dry_run, force
                )
            elif registry.source_type in ('git', 'url', 'local'):
                self.stdout.write(
                    self.style.WARNING(f"  Source type '{registry.source_type}' not yet implemented")
                )
                continue
            else:
                self.stdout.write(
                    self.style.WARNING(f"  Unknown source type: {registry.source_type}")
                )
                continue

            total_created += created
            total_updated += updated
            total_unchanged += unchanged
            total_deactivated += deactivated

            if not dry_run:
                registry.last_sync = settings.timezone.now()
                registry.save(update_fields=['last_sync'])

        # Summary
        self.stdout.write("\n" + "=" * 50)
        self.stdout.write(self.style.SUCCESS("Sync Summary:"))
        self.stdout.write(f"  Created:   {total_created}")
        self.stdout.write(f"  Updated:   {total_updated}")
        self.stdout.write(f"  Unchanged: {total_unchanged}")
        self.stdout.write(f"  Deactivated: {total_deactivated}")
        self.stdout.write("=" * 50)

        if dry_run:
            self.stdout.write(self.style.WARNING("\nDry-run mode — no changes saved."))

    # ═══════════════════════════════════════════════════════════════════
    # GitHub sync logic
    # ═══════════════════════════════════════════════════════════════════
    def _sync_github(self, registry, dry_run=False, force=False):
        """
        Sincroniza desde GitHub organizacion.

        - Lee GITHUB_TOKEN de ENV
        - Lista repos de la org configurada en registry.url
        - Filtra por topic 'erp-nexus-module' y presencia de __meta__.py
        - Para cada repo: shallow clone → parse __meta__.py → upsert catalog
        """
        import os
        import subprocess
        import tempfile
        from pathlib import Path

        import requests

        from apps.core_marketplace.models import ModuleCatalogItem
        from apps.core_marketplace.utils.module_loader import parse_meta_file

        org_name = registry.url  # Ej: "erp-nexus" o nombre de org GitHub
        token = os.getenv("GITHUB_TOKEN")

        if not token:
            self.stdout.write(
                self.style.WARNING("  GITHUB_TOKEN not set — rate limit may apply (60/hr)")
            )

        headers = {}
        if token:
            headers["Authorization"] = f"token {token}"

        created = 0
        updated = 0
        unchanged = 0
        deactivated = 0

        try:
            # Paginación: obtener todos los repos
            page = 1
            per_page = 100
            all_repos = []

            while True:
                url = (
                    f"https://api.github.com/orgs/{org_name}/repos"
                    f"?type=all&per_page={per_page}&page={page}"
                )
                resp = requests.get(url, headers=headers, timeout=30)
                if resp.status_code != 200:
                    raise CommandError(
                        f"GitHub API error {resp.status_code}: {resp.text[:200]}"
                    )
                repos_page = resp.json()
                if not repos_page:
                    break
                all_repos.extend(repos_page)
                if len(repos_page) < per_page:
                    break
                page += 1

            self.stdout.write(f"  Found {len(all_repos)} repositories in '{org_name}'")

            # Filtrar repos válidos
            valid_repos = []
            for repo in all_repos:
                topics = repo.get("topics", [])
                has_topic = "erp-nexus-module" in topics or "erp-module" in topics

                if not has_topic:
                    continue

                # Verificar __meta__.py sin hacer clone aún (usar GitHub API)
                meta_url = f"https://raw.githubusercontent.com/{repo['full_name']}/main/__meta__.py"
                meta_resp = requests.head(meta_url, headers=headers, timeout=10)
                if meta_resp.status_code != 200:
                    # Probar rama 'master'
                    meta_url = f"https://raw.githubusercontent.com/{repo['full_name']}/master/__meta__.py"
                    meta_resp = requests.head(meta_url, headers=headers, timeout=10)
                    if meta_resp.status_code != 200:
                        continue  # No tiene __meta__.py

                valid_repos.append(repo)

            self.stdout.write(f"  → {len(valid_repos)} repos valid (topic + __meta__.py)")

            # Procesar cada repo válido
            technical_names_seen = set()

            for repo in valid_repos:
                full_name = repo["full_name"]
                clone_url = repo["clone_url"]
                default_branch = repo.get("default_branch") or "main"

                # Parse __meta__.py desde raw (sin clone si es posible)
                # Como fallback, clonamos shallow
                meta = self._get_meta_from_repo(clone_url, default_branch, token)

                if not meta:
                    self.stdout.write(self.style.WARNING(f"  ⚠ {full_name}: no __meta__.py"))
                    continue

                tech_name = meta.get("technical_name")
                if not tech_name:
                    self.stdout.write(self.style.WARNING(f"  ⚠ {full_name}: missing technical_name"))
                    continue

                technical_names_seen.add(tech_name)

                # Upsert ModuleCatalogItem
                version = meta.get("version", "0.1.0")
                try:
                    item, created_flag = ModuleCatalogItem.objects.update_or_create(
                        technical_name=tech_name,
                        defaults={
                            "display_name": meta.get("display_name", tech_name),
                            "version": version,
                            "module_type": meta.get("module_type", "optional"),
                            "repo_url": clone_url,
                            "min_erp_version": meta.get("min_erp_version", ""),
                            "max_erp_version": meta.get("max_erp_version", ""),
                            "python_dependencies": meta.get("python_dependencies", {}),
                            "system_dependencies": meta.get("system_dependencies", {}),
                            "documentation_url": meta.get("documentation_url", ""),
                            "description": meta.get("description", ""),
                            "is_licensed": meta.get("is_licensed", False),
                            "license_required": meta.get("license_required", False),
                            "trial_days": meta.get("trial_days", 0),
                            "price_monthly": meta.get("price_monthly"),
                            "price_yearly": meta.get("price_yearly"),
                            "is_active": True,
                            "status": "active",
                        },
                    )
                    if created_flag:
                        created += 1
                        self.stdout.write(self.style.SUCCESS(f"  ✔ {tech_name} (created)"))
                    elif force or item.version != version:
                        updated += 1
                        self.stdout.write(f"  ↻ {tech_name} (updated to v{version})")
                    else:
                        unchanged += 1
                        self.stdout.write(f"  ○ {tech_name} (unchanged)")
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"  ✗ {tech_name}: {e}"))

            # Desactivar items que ya no están en el catálogo
            # (solo si registry es default para evitar desactivaciones accidentales)
            if registry.is_default:
                orphaned = ModuleCatalogItem.objects.exclude(
                    technical_name__in=technical_names_seen
                ).filter(is_active=True, repo_url__isnull=False)
                orphaned_count = orphaned.count()
                if orphaned_count and not dry_run:
                    orphaned.update(is_active=False, status='inactive')
                deactivated = orphaned_count
                if orphaned_count:
                    self.stdout.write(
                        self.style.WARNING(f"  Deactivated {orphaned_count} orphaned items")
                    )

        except requests.RequestException as exc:
            raise CommandError(f"GitHub API request failed: {exc}")

        return created, updated, unchanged, deactivated

    def _get_meta_from_repo(self, clone_url, branch, token=None):
        """
        Obtiene __meta__.py desde el repositorio.
        Primero intenta via GitHub API raw, si falla clona shallow.
        """
        import os
        import subprocess
        import tempfile
        from pathlib import Path

        import requests

        # Intentar raw directo (más rápido)
        repo_name = clone_url.split("/")[-1].replace(".git", "")
        # Derivar owner/name del clone_url
        # git@github.com:owner/repo.git  o  https://github.com/owner/repo.git
        if ":" in clone_url:
            # SSH format: git@github.com:owner/repo.git
            parts = clone_url.split(":")[1].split("/")
            owner, repo = parts[0], parts[1].replace(".git", "")
        else:
            # HTTPS format
            parts = clone_url.rstrip(".git").split("/")
            owner, repo = parts[-2], parts[-1]

        # Probar rama principal
        for branch_name in (branch, "main", "master"):
            raw_url = f"https://raw.githubusercontent.com/{owner}/{repo}/{branch_name}/__meta__.py"
            headers = {}
            if token:
                headers["Authorization"] = f"token {token}"
            try:
                resp = requests.get(raw_url, headers=headers, timeout=10)
                if resp.status_code == 200:
                    # Parsear contenido
                    import ast
                    try:
                        tree = ast.parse(resp.text)
                        meta = {}
                        for node in ast.iter_child_nodes(tree):
                            if isinstance(node, ast.Assign):
                                for target in node.targets:
                                    if isinstance(target, ast.Name):
                                        try:
                                            import ast as ast_literal
                                            meta[target.id] = ast_literal.literal_eval(node.value)
                                        except Exception:
                                            pass
                        if "technical_name" in meta:
                            return meta
                    except SyntaxError:
                        pass
            except requests.RequestException:
                pass

        # Fallback: clone shallow
        with tempfile.TemporaryDirectory() as tmpdir:
            target = Path(tmpdir) / repo_name
            cmd = ["git", "clone", "--depth", "1", "--single-branch", clone_url, str(target)]
            if branch:
                cmd += ["-b", branch]

            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            if result.returncode != 0:
                return None

            meta_path = target / "__meta__.py"
            if meta_path.exists():
                return parse_meta_file(meta_path)

        return None
