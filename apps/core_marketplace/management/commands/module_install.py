"""
Management command: module_install

Installs a module from the catalog with full validation and license checks.
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
from apps.core_marketplace.utils.license import validate_license_for_module, consume_license


class Command(BaseCommand):
    help = "Install a module from the marketplace with validation and license checks"

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
            "--license-key",
            type=str,
            help="License key for licensed modules (required if module needs license)",
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
        license_key = options.get("license_key")
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
        # STEP 3 — License validation (before network operations)
        # ═══════════════════════════════════════════════════════════════
        license_obj = None
        if catalog_item.license_required:
            self.stdout.write(f"   🔐 Module requires a license key")
            if not license_key:
                raise CommandError(
                    f"Module '{tech_name}' requires --license-key. "
                    f"Get a key from the module vendor or admin."
                )
            try:
                license_obj = validate_license_for_module(catalog_item, license_key)
                self.stdout.write(self.style.SUCCESS(f"   ✅ License validated: {license_obj.license_key[:12]}..."))
            except ValueError as exc:
                raise CommandError(f"License error: {exc}")
        elif catalog_item.is_licensed and license_key:
            # Optional license provided even if not required
            try:
                license_obj = validate_license_for_module(catalog_item, license_key)
                self.stdout.write(self.style.SUCCESS(f"   ✅ License accepted (premium features)"))
            except ValueError as exc:
                self.stdout.write(self.style.WARNING(f"   ⚠️  Invalid license key ignored: {exc}"))
                license_obj = None

        # ═══════════════════════════════════════════════════════════════
        # STEP 4 — Clone/update repo
        # ═══════════════════════════════════════════════════════════════
        modules_dir = Path(settings.BASE_DIR) / "modules"
        modules_dir.mkdir(parents=True, exist_ok=True)
        target_path = modules_dir / tech_name

        self._clone_or_update_repo(catalog_item.repo_url, target_path, tag)

        # ═══════════════════════════════════════════════════════════════
        # STEP 5 — Security & validation checks
        # ═══════════════════════════════════════════════════════════════
        if not skip_validation:
            self._validate_module_safety(target_path, tech_name)
            self._validate_meta_file(target_path, tech_name)

        # ═══════════════════════════════════════════════════════════════
        # STEP 6 — Parse __meta__.py
        # ═══════════════════════════════════════════════════════════════
        meta_path = target_path / "__meta__.py"
        meta = self._parse_meta_file(meta_path)

        if meta.get("technical_name") != tech_name:
            raise CommandError(f"Technical name mismatch: {meta.get('technical_name')} != {tech_name}")

        django_app = meta.get("django_app", tech_name)

        # ═══════════════════════════════════════════════════════════════
        # STEP 7 — Check Python dependencies
        # ═══════════════════════════════════════════════════════════════
        python_deps = meta.get("python_dependencies", {})
        if python_deps:
            self.stdout.write(f"   📋 Python dependencies: {python_deps}")

        # ═══════════════════════════════════════════════════════════════
        # STEP 8 — Verify Django app structure exists
        # ═══════════════════════════════════════════════════════════════
        app_dir = target_path / django_app
        if not app_dir.exists():
            app_dir = target_path / tech_name
            if not app_dir.exists():
                raise CommandError(f"Module structure invalid: neither '{django_app}' nor '{tech_name}' directory found")

        # ═══════════════════════════════════════════════════════════════
        # STEP 9 — Register and update modules_enabled.py
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

            # Consume license seat AFTER successful DB prep
            if license_obj:
                consume_license(license_obj)
                self.stdout.write(f"   🎟️  License seat consumed ({license_obj.used_seats}/{license_obj.max_seats})")

            catalog_item.touch_installed()
            catalog_item.installed_path = str(target_path)
            catalog_item.save(update_fields=["installed_path"])

        # ═══════════════════════════════════════════════════════════════
        # STEP 10 — Log installation
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

        # Invalidate dashboard/sidebar cache so new module appears immediately
        from django.core.cache import cache
        cache.delete("admin_dashboard_metrics")
        cache.delete("jazzmin_side_menu_apps")

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
            self.stdout.write(self.style.WARNING(f"   ⚠️  Version '{version}' doesn't look like semver"))

        self.stdout.write("   ✅ __meta__.py validation passed")

    def _validate_module_safety(self, target_path: Path, tech_name: str) -> None:
        suspicious = ["../erp_nexus/", "../../erp_nexus/", "~erp_nexus"]
        for pattern in suspicious:
            if pattern in str(target_path):
                raise CommandError(f"Security violation: unsafe path detected")
        self.stdout.write("   ✅ Security checks passed")

    def _is_valid_version(self, version: str) -> bool:
        import re
        return bool(re.match(r'^\d+\.\d+(\.\d+)?$', version))
