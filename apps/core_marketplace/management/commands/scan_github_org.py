"""
Management command: scan_github_org

Scanea una organización de GitHub buscando repositorios que contengan
un módulo ERP Nexus válido (con __meta__.py) y los registra en ModuleCatalog.
"""
import ast
import os
from pathlib import Path
from typing import Optional

import requests
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from apps.core_marketplace.models import ModuleCatalogItem, ModuleRegistry


class Command(BaseCommand):
    help = "Scan a GitHub organization for ERP Nexus modules and register them in the catalog"

    def add_arguments(self, parser):
        parser.add_argument(
            "org_name",
            type=str,
            help="GitHub organization name (e.g., 'ERPNexus')",
        )
        parser.add_argument(
            "--token",
            type=str,
            help="GitHub personal access token (or set GITHUB_TOKEN env var)",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would be registered without saving",
        )
        parser.add_argument(
            "--create-registry",
            action="store_true",
            help="Create a ModuleRegistry entry for this org if missing",
        )

    def handle(self, *args, **options):
        org_name = options["org_name"]
        token = options.get("token") or os.environ.get("GITHUB_TOKEN") or os.environ.get("GITHUB_APIKEY")
        dry_run = options["dry_run"]
        create_registry = options["create_registry"]

        if not token:
            self.stdout.write(self.style.WARNING("No GitHub token provided. Using unauthenticated requests (rate limit 60/hr)"))

        self.stdout.write(f"🔍 Scanning GitHub organization: {org_name}")

        # Ensure registry exists
        registry = self._get_or_create_registry(org_name, token, create_registry)

        # Fetch repos
        repos = self._fetch_github_repos(org_name, token)
        self.stdout.write(f"   Found {len(repos)} repositories")

        # Filter repos with __meta__.py
        modules_found = []
        for repo in repos:
            repo_name = repo["name"]
            self.stdout.write(f"   Checking: {repo_name}...", ending=" ")
            if self._repo_has_meta(repo, token):
                self.stdout.write(self.style.SUCCESS("✅"))
                meta = self._fetch_and_parse_meta(repo, token)
                if meta:
                    modules_found.append((repo, meta))
                else:
                    self.stdout.write(self.style.WARNING("   ⚠️  __meta__.py malformed or missing required fields"))
            else:
                self.stdout.write("✖️")

        self.stdout.write(f"\n📦 Modules discovered: {len(modules_found)}")

        # Register/update in DB
        if not dry_run:
            created, updated = self._register_modules(registry, modules_found, token)
            self.stdout.write(self.style.SUCCESS(f"\n✅ Registered: {created} new, {updated} updated"))
        else:
            self.stdout.write(self.style.WARNING("\n💡 Dry-run mode — no changes saved"))
            for repo, meta in modules_found:
                tech_name = meta.get("technical_name", "unknown")
                version = meta.get("version", "?")
                self.stdout.write(f"   [DRY-RUN] {tech_name} v{version}")

    def _get_or_create_registry(self, org_name: str, token: Optional[str], create_flag: bool) -> ModuleRegistry:
        """Get or create a ModuleRegistry for the GitHub org."""
        try:
            registry = ModuleRegistry.objects.get(name=org_name)
            self.stdout.write(f"   📦 Using existing registry: {org_name}")
            return registry
        except ModuleRegistry.DoesNotExist:
            if create_flag:
                registry = ModuleRegistry.objects.create(
                    name=org_name,
                    source_type="github",
                    url=f"https://github.com/{org_name}",
                    description=f"Auto-discovered modules from {org_name} GitHub organization",
                    is_active=True,
                    is_default=True,
                    priority=100,
                )
                self.stdout.write(self.style.SUCCESS(f"   ✅ Created registry: {org_name}"))
                return registry
            else:
                raise CommandError(f"Registry '{org_name}' not found. Use --create-registry to create it.")

    def _fetch_github_repos(self, org_name: str, token: Optional[str]) -> list:
        """Fetch all public repos for the org."""
        headers = {"Accept": "application/vnd.github.v3+json"}
        if token:
            headers["Authorization"] = f"token {token}"

        repos = []
        page = 1
        per_page = 100

        while True:
            url = f"https://api.github.com/orgs/{org_name}/repos?page={page}&per_page={per_page}"
            resp = requests.get(url, headers=headers, timeout=30)
            if resp.status_code != 200:
                raise CommandError(f"GitHub API error {resp.status_code}: {resp.text[:200]}")

            batch = resp.json()
            if not batch:
                break
            repos.extend(batch)
            if len(batch) < per_page:
                break
            page += 1

        return repos

    def _repo_has_meta(self, repo: dict, token: Optional[str]) -> bool:
        """Check if repo contains __meta__.py at root."""
        # Only check default branch (cheap)
        default_branch = repo.get("default_branch", "main")
        repo_name = repo["name"]
        org_name = repo["owner"]["login"]

        # Try to fetch __meta__.py HEAD
        url = f"https://raw.githubusercontent.com/{org_name}/{repo_name}/{default_branch}/__meta__.py"
        headers = {}
        if token:
            headers["Authorization"] = f"token {token}"

        try:
            resp = requests.get(url, headers=headers, timeout=10)
            return resp.status_code == 200
        except requests.RequestException:
            return False

    def _fetch_and_parse_meta(self, repo: dict, token: Optional[str]) -> Optional[dict]:
        """Fetch __meta__.py from repo and parse required fields."""
        org_name = repo["owner"]["login"]
        repo_name = repo["name"]
        default_branch = repo.get("default_branch", "main")
        url = f"https://raw.githubusercontent.com/{org_name}/{repo_name}/{default_branch}/__meta__.py"

        headers = {}
        if token:
            headers["Authorization"] = f"token {token}"

        try:
            resp = requests.get(url, headers=headers, timeout=10)
            if resp.status_code != 200:
                return None
            content = resp.text
            return self._parse_meta_py(content, repo)
        except Exception as exc:
            self.stdout.write(self.style.WARNING(f"   ⚠️  Error fetching meta: {exc}"))
            return None

    def _parse_meta_py(self, content: str, repo: dict) -> Optional[dict]:
        """Parse __meta__.py AST and extract required fields."""
        try:
            tree = ast.parse(content)
        except SyntaxError as exc:
            self.stdout.write(self.style.WARNING(f"   ⚠️  Syntax error in __meta__.py: {exc}"))
            return None

        # Find assignments to top-level variables
        meta = {}
        for node in ast.iter_child_nodes(tree):
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        key = target.id
                        try:
                            # Evaluate constant values only (safe for our use case)
                            if isinstance(node.value, (ast.Constant, ast.Str, ast.Num, ast.List, ast.Dict)):
                                # Use ast.literal_eval safely
                                import ast as ast_literal
                                meta[key] = ast_literal.literal_eval(node.value)
                        except Exception:
                            pass  # Skip complex expressions

        # Required fields
        required = ["technical_name", "version"]
        for field in required:
            if field not in meta:
                self.stdout.write(self.style.WARNING(f"   ⚠️  Missing required field: {field}"))
                return None

        # Populate defaults
        meta.setdefault("display_name", meta.get("technical_name", "").title())
        meta.setdefault("module_type", "optional")
        meta.setdefault("repo_url", repo.get("html_url", ""))
        meta.setdefault("python_dependencies", {})
        meta.setdefault("system_dependencies", {})
        meta.setdefault("documentation_url", "")

        return meta

    def _register_modules(self, registry: ModuleRegistry, modules: list, token: Optional[str]) -> tuple:
        """Create or update ModuleCatalogItem entries."""
        created = 0
        updated = 0

        with transaction.atomic():
            for repo, meta in modules:
                tech_name = meta["technical_name"]
                version = meta["version"]

                item, created_flag = ModuleCatalogItem.objects.update_or_create(
                    technical_name=tech_name,
                    defaults={
                        "display_name": meta.get("display_name", tech_name),
                        "version": version,
                        "module_type": meta.get("module_type", "optional"),
                        "repo_url": meta.get("repo_url") or repo.get("html_url", ""),
                        "min_erp_version": meta.get("min_erp_version", ""),
                        "max_erp_version": meta.get("max_erp_version"),
                        "python_dependencies": meta.get("python_dependencies", {}),
                        "system_dependencies": meta.get("system_dependencies", {}),
                        "documentation_url": meta.get("documentation_url", ""),
                        "django_app": tech_name,  # Assumption: module name == Django app label
                        "status": "active",
                        "is_active": True,
                    },
                )
                if created_flag:
                    created += 1
                    self.stdout.write(f"   ✅ Created: {tech_name} v{version}")
                else:
                    updated += 1
                    self.stdout.write(f"   🔄 Updated: {tech_name} v{version}")

        return created, updated
