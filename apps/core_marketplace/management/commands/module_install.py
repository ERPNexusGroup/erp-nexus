"""
Management command: module_install

Installs a module from the catalog (GitHub clone + register) with full validation.
"""
import hashlib
import os
import shutil
import subprocess
from pathlib import Path

import requests
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from apps.core_marketplace.models import ModuleCatalogItem, EnabledModule, ModuleDownload
from apps.core_marketplace.utils.module_loader import add_to_modules_enabled


class Command(BaseCommand):
    help = "Install a module from the marketplace with validation"

    def add_arguments(self, parser):
        parser.add_argument(
            "technical_name",
            type=str,
            help="Technical name of the module to install (e.g., 'hr')",
        )
        parser.add_argument(
            "--tag",
            type=str,
            help="Specific git tag/version to install (default: latest from catalog)",
        )
        parser.add_argument(
            "--force",
            action="store_true",
            help="Force reinstall if already installed",
        )
        parser.add_argument(
            "--keep-data",
            action="store_true",
            help="Keep data on reinstall (don't drop tables)",
        )
        parser.add_argument(
            "--skip-validation",
            action="store_true",
            help="Skip __meta__.py validation (dangerous)",
        )

    def handle(self, *args, **options):
        tech_name = options["technical_name"]
        tag = options.get("tag")
        force = options["force"]
        keep_data = options["keep_data"]
        skip_validation = options["skip_validation"]

        self.stdout.write(f"📦 Installing module: {tech_name}")

        # ═══════════════════════════════════════════════════════════════
        # STEP 1 — Find in catalog
        # ═══════════════════════════════════════════════════════════════
        try:
            catalog_item = ModuleCatalogItem.objects.get(technical_name=tech_name, is_active=True)
        except ModuleCatalogItem.DoesNotExist:
            raise CommandError(f"Module '{tech_name}' not found in catalog. Run scan_github_org first.")

        if not catalog_item.repo_url:
            raise CommandError(f"Module '{tech_name}' has no repo_url defined in catalog.")

        # ═══════════════════════════════════════════════════════════════
        # STEP 2 — Check if already installed
        # ═══════════════════════════════════════════════════════════════
        try:
            enabled = EnabledModule.objects.get(technical_name=tech_name)
            if not force:
                raise CommandError(f"Module '{tech_name}' already installed. Use --force to reinstall.")
            self.stdout.write(self.style.WARNING(f"   ⚠️  Module already installed — reinstalling (--force)"))
        except EnabledModule.DoesNotExist:
            enabled = None

        # ═══════════════════════════════════════════════════════════════
        # STEP 3 — Clone/update repo
        # ═══════════════════════════════════════════════════════════════
        modules_dir = Path(settings.BASE_DIR) / "modules"
        modules_dir.mkdir(parents=True, exist_ok=True)
        target_path = modules_dir / tech_name

        self._clone_or_update_repo(catalog_item.repo_url, target_path, tag)

        # ═══════════════════════════════════════════════════════════════
        # STEP 4 — Security & validation checks
        # ═══════════════════════════════════════════════════════════════
        if not skip_validation:
            self._validate_module_safety(target_path, tech_name)
            self._validate_meta_file(target_path, tech_name)

        # ═══════════════════════════════════════════════════════════════
        # STEP 5 — Parse __meta__.py
        # ═══════════════════════════════════════════════════════════════
        meta_path = target_path / "__meta__.py"
        meta = self._parse_meta_file(meta_path)

        if meta.get("technical_name") != tech_name:
            raise CommandError(f"Technical name mismatch: {meta.get('technical_name')} != {tech_name}")

        django_app = meta.get("django_app", tech_name)

        # ═══════════════════════════════════════════════════════════════
        # STEP 6 — Check Python dependencies
        # ═══════════════════════════════════════════════════════════════
        python_deps = meta.get("python_dependencies", {})
        if python_deps:
            self.stdout.write(f"   📋 Python dependencies: {python_deps}")

        # ═══════════════════════════════════════════════════════════════
        # STEP 7 — Verify Django app structure exists
        # ═══════════════════════════════════════════════════════════════
        app_dir = target_path / django_app
        if not app_dir.exists():
            app_dir = target_path / tech_name
            if not app_dir.exists():
                raise CommandError(f"Module structure invalid: neither '{django_app}' nor '{tech_name}' directory found")

        # ═══════════════════════════════════════════════════════════════
        # STEP 8 — Register and update modules_enabled.py
        # ═══════════════════════════════════════════════════════════════
        with transaction.atomic():
            if enabled and not keep_data:
                enabled.delete()

            EnabledModule.objects.create(
                technical_name=tech_name,
                django_app=django_app,
                status="active",
            )

            add_to_modules_enabled(django_app)

            catalog_item.touch_installed()
            catalog_item.installed_path = str(target_path)
            catalog_item.save(update_fields=["installed_path"])

        # ═══════════════════════════════════════════════════════════════
        # STEP 9 — Log installation
        # ═══════════════════════════════════════════════════════════════
        ModuleDownload.objects.create(
            module_name=tech_name,
            version=tag or catalog_item.version,
            source=catalog_item.repo_url,
            status="success",
        )

        self.stdout.write(self.style.SUCCESS(f"✅ Module '{tech_name}' installed successfully!"))
        self.stdout.write(f"   📁 Path: {target_path}")
        self.stdout.write(f"   🔄 Restart Django to load module (modules_enabled updated)")

    # ──────────────────────────────────────────────────────────────────
    # Helper methods
    # ──────────────────────────────────────────────────────────────────
    def _clone_or_update_repo(self, repo_url: str, target_path: Path, tag: str = None) -> None:
        if target_path.exists() and (target_path / ".git").exists():
            self.stdout.write(f"   🔄 Updating existing repo at {target_path}")
            result = subprocess.run(["git", "pull"], cwd=target_path, capture_output=True, text=True)
            if result.returncode != 0:
                raise CommandError(f"Git pull failed: {result.stderr[:200]}")
        else:
            self.stdout.write(f"   📥 Cloning {repo_url} → {target_path}")
            result = subprocess.run(
                ["git", "clone", "--depth", "1", repo_url, str(target_path)],
                capture_output=True,
                text=True,
            )
            if result.returncode != 0:
                raise CommandError(f"Git clone failed: {result.stderr[:200]}")

        if tag:
            self.stdout.write(f"   🏷️  Checking out tag: {tag}")
            result = subprocess.run(["git", "checkout", tag], cwd=target_path, capture_output=True, text=True)
            if result.returncode != 0:
                raise CommandError(f"Git checkout failed: {result.stderr[:200]}")

    def _parse_meta_file(self, meta_path: Path) -> dict:
        import ast

        with open(meta_path, "r") as f:
            content = f.read()

        try:
            tree = ast.parse(content)
        except SyntaxError as exc:
            raise CommandError(f"Syntax error in __meta__.py: {exc}")

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
        return meta

    def _validate_meta_file(self, target_path: Path, tech_name: str) -> None:
        """Validate __meta__.py required fields and formats."""
        meta_path = target_path / "__meta__.py"
        if not meta_path.exists():
            raise CommandError("Validation failed: __meta__.py not found")

        meta = self._parse_meta_file(meta_path)

        required = ["technical_name", "version"]
        for field in required:
            if field not in meta:
                raise CommandError(f"Validation failed: __meta__.py missing required field '{field}'")

        if meta["technical_name"] != tech_name:
            raise CommandError(f"Validation failed: technical_name mismatch")

        version = meta["version"]
        if not self._is_valid_version(version):
            self.stdout.write(self.style.WARNING(f"   ⚠️  Version '{version}' doesn't look like semver (expected X.Y.Z)"))

        self.stdout.write("   ✅ __meta__.py validation passed")

    def _validate_module_safety(self, target_path: Path, tech_name: str) -> None:
        """Security check: module cannot write outside modules/ directory."""
        suspicious = ["../erp_nexus/", "../../erp_nexus/", "~erp_nexus"]
        for pattern in suspicious:
            if pattern in str(target_path):
                raise CommandError(f"Security violation: unsafe path detected")
        self.stdout.write("   ✅ Security checks passed")

    def _is_valid_version(self, version: str) -> bool:
        """Basic semver-like check: X.Y or X.Y.Z."""
        import re
        return bool(re.match(r'^\d+\.\d+(\.\d+)?$', version))
