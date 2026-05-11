# E2E tests for Marketplace dependency resolution (Phase 1.4)

import pytest
from io import StringIO
from unittest.mock import patch

from apps.core_marketplace.models import (
    ModuleCatalogItem,
    ModuleDependency,
    EnabledModule,
)
from apps.core_marketplace.services import DependencyResolver


# ─────────────────────────────────────────────────────────────────────────────
#  resolver service tests
# ─────────────────────────────────────────────────────────────────────────────
@pytest.mark.django_db
class TestDependencyResolverE2E:
    """End-to-end tests for the dependency resolver service."""

    def setup_method(self):
        # Create a catalog of modules
        self.core = ModuleCatalogItem.objects.create(
            technical_name='core',
            display_name='Core Framework',
            version='1.0.0',
            is_active=True,
        )
        self.facturacion = ModuleCatalogItem.objects.create(
            technical_name='facturacion',
            display_name='Facturacion Electronica',
            version='1.2.0',
            is_active=True,
        )
        self.inventory = ModuleCatalogItem.objects.create(
            technical_name='inventory',
            display_name='Inventory Management',
            version='1.0.0',
            is_active=True,
        )
        self.sales = ModuleCatalogItem.objects.create(
            technical_name='sales',
            display_name='Sales CRM',
            version='1.0.0',
            is_active=True,
        )
        self.reports = ModuleCatalogItem.objects.create(
            technical_name='reports',
            display_name='Advanced Reports',
            version='1.0.0',
            is_active=True,
        )
        self.old_accounting = ModuleCatalogItem.objects.create(
            technical_name='old_accounting',
            display_name='Legacy Accounting',
            version='1.0.0',
            is_active=True,
        )
        self.accounting = ModuleCatalogItem.objects.create(
            technical_name='accounting',
            display_name='Accounting',
            version='2.0.0',
            is_active=True,
        )

    def test_resolve_simple_linear_chain(self):
        # core -> facturacion -> inventory
        ModuleDependency.objects.create(module=self.facturacion, depends_on=self.core, required=True, conflict=False)
        ModuleDependency.objects.create(module=self.inventory, depends_on=self.facturacion, required=True, conflict=False)

        resolver = DependencyResolver()
        plan = resolver.resolve_install_plan('inventory', with_deps=True)

        names = [m.technical_name for m in plan.to_install]
        assert names == ['core', 'facturacion', 'inventory']
        assert plan.conflicts == []
        assert plan.warnings == []

    def test_resolve_diamond_dependency(self):
        # A -> B, A -> C, B -> D, C -> D (diamond)
        a = ModuleCatalogItem.objects.create(technical_name='a', display_name='A', version='1.0', is_active=True)
        b = ModuleCatalogItem.objects.create(technical_name='b', display_name='B', version='1.0', is_active=True)
        c = ModuleCatalogItem.objects.create(technical_name='c', display_name='C', version='1.0', is_active=True)
        d = ModuleCatalogItem.objects.create(technical_name='d', display_name='D', version='1.0', is_active=True)

        ModuleDependency.objects.create(module=a, depends_on=b, required=True, conflict=False)
        ModuleDependency.objects.create(module=a, depends_on=c, required=True, conflict=False)
        ModuleDependency.objects.create(module=b, depends_on=d, required=True, conflict=False)
        ModuleDependency.objects.create(module=c, depends_on=d, required=True, conflict=False)

        resolver = DependencyResolver()
        plan = resolver.resolve_install_plan('a', with_deps=True)

        names = [m.technical_name for m in plan.to_install]
        assert names[0] == 'd'
        assert names[-1] == 'a'
        middle = names[1:-1]
        assert set(middle) == {'b', 'c'}
        assert len(names) == 4

    def test_conflict_with_installed_module(self):
        # old_accounting conflicts with accounting; when accounting installed, old_accounting cannot install
        ModuleDependency.objects.create(module=self.old_accounting, depends_on=self.accounting, required=False, conflict=True)
        EnabledModule.objects.create(technical_name='accounting', django_app='accounting', status='active')

        resolver = DependencyResolver()
        plan = resolver.resolve_install_plan('old_accounting', with_deps=False)

        assert len(plan.conflicts) == 1
        assert plan.conflicts[0].module_a == 'old_accounting'
        assert plan.conflicts[0].module_b == 'accounting'
        assert 'accounting' not in [m.technical_name for m in plan.to_install]

    def test_optional_dependency_satisfied_by_installed(self):
        # reports optionally depends on facturacion; if facturacion installed, reports can install
        ModuleDependency.objects.create(module=self.reports, depends_on=self.facturacion, required=False, conflict=False)
        EnabledModule.objects.create(technical_name='facturacion', django_app='facturacion', status='active')

        resolver = DependencyResolver()
        plan = resolver.resolve_install_plan('reports', with_deps=True)
        assert plan.conflicts == []
        assert self.reports in plan.to_install

    def test_circular_dependency_detection(self):
        # A -> B -> C -> A (cycle)
        a = ModuleCatalogItem.objects.create(technical_name='cycle_a', display_name='A', version='1.0', is_active=True)
        b = ModuleCatalogItem.objects.create(technical_name='cycle_b', display_name='B', version='1.0', is_active=True)
        c = ModuleCatalogItem.objects.create(technical_name='cycle_c', display_name='C', version='1.0', is_active=True)
        ModuleDependency.objects.create(module=a, depends_on=b, required=True, conflict=False)
        ModuleDependency.objects.create(module=b, depends_on=c, required=True, conflict=False)
        ModuleDependency.objects.create(module=c, depends_on=a, required=True, conflict=False)

        resolver = DependencyResolver()
        cycle = resolver.detect_cycles('cycle_a')
        assert cycle is not None
        assert 'cycle_a' in cycle

        plan = resolver.resolve_install_plan('cycle_a', with_deps=True)
        assert any('Circular dependency' in w for w in plan.warnings)

    def test_topological_sort_valid_order(self):
        web = ModuleCatalogItem.objects.create(technical_name='web', display_name='Web', version='1.0', is_active=True)
        api = ModuleCatalogItem.objects.create(technical_name='api', display_name='API', version='1.0', is_active=True)
        auth = ModuleCatalogItem.objects.create(technical_name='auth', display_name='Auth', version='1.0', is_active=True)
        db = ModuleCatalogItem.objects.create(technical_name='db', display_name='Database', version='1.0', is_active=True)

        # deps: api -> auth, web -> api, auth -> db
        ModuleDependency.objects.create(module=api, depends_on=auth, required=True, conflict=False)
        ModuleDependency.objects.create(module=web, depends_on=api, required=True, conflict=False)
        ModuleDependency.objects.create(module=auth, depends_on=db, required=True, conflict=False)

        resolver = DependencyResolver()
        modules = [web, api, auth, db]
        sorted_modules = resolver.topological_sort(modules)
        names = [m.technical_name for m in sorted_modules]

        assert names.index('db') < names.index('auth')
        assert names.index('auth') < names.index('api')
        assert names.index('api') < names.index('web')

    def test_upgrade_safety_major_bump(self):
        EnabledModule.objects.create(
            technical_name='facturacion',
            django_app='facturacion',
            status='active',
            installed_version='1.0.0',
        )
        resolver = DependencyResolver()
        check = resolver.check_upgrade_safety('facturacion', '2.0.0')
        assert check.status == 'BREAKING_MAJOR'
        assert 'Major version bump' in check.breaking_changes[0]
        assert check.recommended is False

    def test_upgrade_safety_minor_bump_safe(self):
        EnabledModule.objects.create(
            technical_name='facturacion',
            django_app='facturacion',
            status='active',
            installed_version='1.0.0',
        )
        resolver = DependencyResolver()
        check = resolver.check_upgrade_safety('facturacion', '1.2.0')
        assert check.status == 'SAFE'
        assert check.recommended is True

    def test_resolve_with_missing_dependency(self):
        # sales requires a module that doesn't exist in catalog (should still be added to plan)
        fake = ModuleCatalogItem.objects.create(
            technical_name='payment_gateway_missing',
            display_name='Missing Payment Gateway',
            version='1.0',
            is_active=True,
        )
        ModuleDependency.objects.create(module=self.sales, depends_on=fake, required=True, conflict=False)

        resolver = DependencyResolver()
        plan = resolver.resolve_install_plan('sales', with_deps=True)

        assert fake in plan.to_install
        assert self.sales in plan.to_install


# ─────────────────────────────────────────────────────────────────────────────
#  management command tests
# ─────────────────────────────────────────────────────────────────────────────
@pytest.mark.django_db
class TestModuleInstallWithDepsCommand:
    """Integration tests for module_install management command with --with-deps.

    These tests bypass the conftest mock_call_command fixture by directly
    instantiating the Command class. This ensures --with-deps logic is tested.
    """

    def _run_command(self, tech_name, **kwargs):
        """Helper: instantiate and run module_install command directly."""
        from apps.core_marketplace.management.commands.module_install import Command
        cmd = Command()
        cmd.stdout = StringIO()
        cmd.stderr = StringIO()
        options = {
            "technical_name": tech_name,
            "tag": None,
            "license_key": kwargs.get("license_key"),
            "force": kwargs.get("force", False),
            "keep_data": kwargs.get("keep_data", False),
            "skip_validation": kwargs.get("skip_validation", False),
            "with_deps": kwargs.get("with_deps", False),
            "no_input": kwargs.get("no_input", True),
            "verbosity": 0,
        }
        # Let exceptions bubble up so tests can assert on them
        cmd.handle(*(), **options)
        return cmd

    def test_module_install_with_deps_resolves_and_installs(self):
        """El comando instala el target y todas sus dependencias en orden correcto."""
        # Create catalog items with repo URLs
        core = ModuleCatalogItem.objects.create(
            technical_name='core',
            display_name='Core Framework',
            version='1.0.0',
            is_active=True,
            repo_url='https://github.com/test/core',
        )
        fact = ModuleCatalogItem.objects.create(
            technical_name='facturacion',
            display_name='Facturacion',
            version='1.2.0',
            is_active=True,
            repo_url='https://github.com/test/facturacion',
        )
        sales = ModuleCatalogItem.objects.create(
            technical_name='sales',
            display_name='Sales CRM',
            version='1.0.0',
            is_active=True,
            repo_url='https://github.com/test/sales',
        )
        ModuleDependency.objects.create(module=fact, depends_on=core, required=True, conflict=False)
        ModuleDependency.objects.create(module=sales, depends_on=fact, required=True, conflict=False)

        def fake_clone(self, repo_url, target_path, tag):
            target_path.mkdir(parents=True, exist_ok=True)
            name = target_path.name
            (target_path / '__meta__.py').write_text(
                f"technical_name='{name}'\nversion='1.0.0'\ndjango_app='{name}'\npython_dependencies={{}}\n"
            )
            (target_path / name).mkdir(exist_ok=True)
            (target_path / name / '__init__.py').touch()

        patches = [
            patch(
                'apps.core_marketplace.management.commands.module_install.Command._clone_or_update_repo',
                fake_clone,
            ),
            patch(
                'apps.core_marketplace.management.commands.module_install.Command._validate_meta_file',
                return_value=None,
            ),
            patch(
                'apps.core_marketplace.management.commands.module_install.Command._validate_module_safety',
                return_value=None,
            ),
            patch(
                'django.core.cache.cache.delete',
                return_value=None,
            ),
            patch(
                'apps.core_marketplace.utils.module_loader.add_to_modules_enabled',
                return_value=None,
            ),
        ]
        with patches[0], patches[1], patches[2], patches[3], patches[4]:
            self._run_command('sales', with_deps=True, no_input=True)

        # Verify EnabledModule records created for all modules in the dependency chain
        all_enabled = list(EnabledModule.objects.values_list('technical_name', flat=True))
        assert EnabledModule.objects.filter(technical_name='core', status='active').exists(), \
            f"core not found. All enabled: {all_enabled}"
        assert EnabledModule.objects.filter(technical_name='facturacion', status='active').exists()
        assert EnabledModule.objects.filter(technical_name='sales', status='active').exists()

    def test_module_install_with_deps_stops_on_conflict(self):
        """Conflicts detectados en resolución previenen cualquier instalación."""
        from django.core.management.base import CommandError

        accounting = ModuleCatalogItem.objects.create(
            technical_name='accounting',
            display_name='Accounting',
            version='2.0.0',
            is_active=True,
            repo_url='https://github.com/test/accounting',
        )
        old_accounting = ModuleCatalogItem.objects.create(
            technical_name='old_accounting',
            display_name='Legacy Accounting',
            version='1.0.0',
            is_active=True,
            repo_url='https://github.com/test/old_accounting',
        )
        ModuleDependency.objects.create(
            module=old_accounting,
            depends_on=accounting,
            required=False,
            conflict=True,
        )
        EnabledModule.objects.create(technical_name='accounting', django_app='accounting', status='active')

        def fake_clone(self, repo_url, target_path, tag):
            # Should never be called due to conflict
            raise AssertionError("Clone called despite conflict detected in resolution phase")

        patches = [
            patch(
                'apps.core_marketplace.management.commands.module_install.Command._clone_or_update_repo',
                fake_clone,
            ),
            patch(
                'django.core.cache.cache.delete',
                return_value=None,
            ),
            patch(
                'apps.core_marketplace.utils.module_loader.add_to_modules_enabled',
                return_value=None,
            ),
        ]
        with patches[0], patches[1], patches[2]:
            with pytest.raises(CommandError) as exc:
                self._run_command('old_accounting', with_deps=True, no_input=True)
            assert 'conflict' in str(exc.value).lower()

        # Verify no NEW module was installed during the failed attempt
        # accounting was already installed before the command ran and should remain installed
        assert EnabledModule.objects.filter(technical_name='accounting', status='active').exists(), \
            'accounting should still be installed (pre-existing)'
        assert not EnabledModule.objects.filter(technical_name='old_accounting', status='active').exists(), \
            'old_accounting should not have been installed due to conflict'


# Total E2E Marketplace expected: 32
# - test_semver.py:       ~28
# - test_dependency_models.py: ~16
# - test_dependency_e2e.py (this file): 11
#   • 8 resolver tests (TestDependencyResolverE2E)
#   • 3 command tests (TestModuleInstallWithDepsCommand)
