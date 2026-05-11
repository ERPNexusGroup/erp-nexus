# Tests for ModuleVersionConstraint and ModuleDependency models (DB-backed)

import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from apps.core_marketplace.models import (
    ModuleCatalogItem,
    ModuleVersionConstraint,
    ModuleDependency,
    EnabledModule,
)


@pytest.mark.django_db
class TestModuleVersionConstraint:
    def test_create_constraint(self, django_user_model):
        # Create a catalog item
        item = ModuleCatalogItem.objects.create(
            technical_name="facturacion",
            display_name="Facturación",
            version="1.2.3",
        )
        constraint = ModuleVersionConstraint.objects.create(
            module=item,
            constraint_type="caret",
            version="1.0.0",
        )
        assert constraint.module == item
        assert constraint.constraint_type == "caret"
        assert constraint.version == "1.0.0"

    def test_is_satisfied_by_exact(self):
        item = ModuleCatalogItem.objects.create(
            technical_name="facturacion", display_name="Facturacion", version="1.2.3"
        )
        constraint = ModuleVersionConstraint.objects.create(
            module=item,
            constraint_type="equal",
            version="1.2.3",
        )
        assert constraint.is_satisfied_by("1.2.3") is True
        assert constraint.is_satisfied_by("1.2.4") is False

    def test_is_satisfied_by_caret(self):
        item = ModuleCatalogItem.objects.create(
            technical_name="facturacion", display_name="Facturacion", version="1.2.3"
        )
        constraint = ModuleVersionConstraint.objects.create(
            module=item, constraint_type="caret", version="1.2.3"
        )
        assert constraint.is_satisfied_by("1.2.3") is True
        assert constraint.is_satisfied_by("1.3.0") is True
        assert constraint.is_satisfied_by("2.0.0") is False
        assert constraint.is_satisfied_by("1.2.2") is False

    def test_is_satisfied_by_approx_equal(self):
        item = ModuleCatalogItem.objects.create(
            technical_name="facturacion", display_name="Facturacion", version="1.2.3"
        )
        constraint = ModuleVersionConstraint.objects.create(
            module=item, constraint_type="approx_equal", version="1.2.3"
        )
        assert constraint.is_satisfied_by("1.2.3") is True
        assert constraint.is_satisfied_by("1.2.4") is True
        assert constraint.is_satisfied_by("1.2.100") is True
        assert constraint.is_satisfied_by("1.3.0") is False

    def test_is_satisfied_by_greater_equal(self):
        item = ModuleCatalogItem.objects.create(
            technical_name="facturacion", display_name="Facturacion", version="1.2.3"
        )
        constraint = ModuleVersionConstraint.objects.create(
            module=item, constraint_type="greater_equal", version="1.2.0"
        )
        assert constraint.is_satisfied_by("1.1.9") is False
        assert constraint.is_satisfied_by("1.2.0") is True
        assert constraint.is_satisfied_by("1.3.0") is True

    def test_unique_together_not_enforced_manually(self):
        item = ModuleCatalogItem.objects.create(
            technical_name="facturacion", display_name="Facturacion", version="1.2.3"
        )
        ModuleVersionConstraint.objects.create(
            module=item, constraint_type="caret", version="1.0.0"
        )
        # Multiple constraints for same module are allowed (different types)
        second = ModuleVersionConstraint(
            module=item, constraint_type="greater_equal", version="1.2.0"
        )
        second.save()
        assert ModuleVersionConstraint.objects.filter(module=item).count() == 2


@pytest.mark.django_db
class TestModuleDependency:
    def test_create_dependency(self):
        sales = ModuleCatalogItem.objects.create(
            technical_name="sales", display_name="Sales", version="1.0.0"
        )
        fact = ModuleCatalogItem.objects.create(
            technical_name="facturacion", display_name="Facturacion", version="1.2.0"
        )
        dep = ModuleDependency.objects.create(
            module=sales,
            depends_on=fact,
            required=True,
            conflict=False,
        )
        assert dep.module == sales
        assert dep.depends_on == fact
        assert dep.required is True
        assert dep.conflict is False

    def test_is_satisfied_required_present(self):
        sales = ModuleCatalogItem.objects.create(
            technical_name="sales", display_name="Sales", version="1.0.0"
        )
        fact = ModuleCatalogItem.objects.create(
            technical_name="facturacion", display_name="Facturacion", version="1.2.0"
        )
        ModuleDependency.objects.create(
            module=sales,
            depends_on=fact,
            required=True,
            conflict=False,
        )
        installed = {"facturacion"}
        # Retrieve the dep from DB to use the real method
        dep = ModuleDependency.objects.get(module=sales, depends_on=fact)
        assert dep.is_satisfied_by(installed) is True

    def test_is_satisfied_required_missing(self):
        sales = ModuleCatalogItem.objects.create(
            technical_name="sales", display_name="Sales", version="1.0.0"
        )
        fact = ModuleCatalogItem.objects.create(
            technical_name="facturacion", display_name="Facturacion", version="1.2.0"
        )
        ModuleDependency.objects.create(
            module=sales,
            depends_on=fact,
            required=True,
            conflict=False,
        )
        installed = {"inventory"}
        dep = ModuleDependency.objects.get(module=sales, depends_on=fact)
        assert dep.is_satisfied_by(installed) is False

    def test_is_satisfied_optional_missing(self):
        reports = ModuleCatalogItem.objects.create(
            technical_name="reports", display_name="Reports", version="1.0.0"
        )
        charts = ModuleCatalogItem.objects.create(
            technical_name="advanced_charts", display_name="Charts", version="1.0.0"
        )
        ModuleDependency.objects.create(
            module=reports,
            depends_on=charts,
            required=False,
            conflict=False,
        )
        installed = {"facturacion"}
        dep = ModuleDependency.objects.get(module=reports, depends_on=charts)
        assert dep.is_satisfied_by(installed) is True  # optional doesn't block

    def test_is_satisfied_conflict_installed(self):
        old_inv = ModuleCatalogItem.objects.create(
            technical_name="old_inventory", display_name="Old Inv", version="1.0.0"
        )
        inv = ModuleCatalogItem.objects.create(
            technical_name="inventory", display_name="Inventory", version="1.0.0"
        )
        ModuleDependency.objects.create(
            module=old_inv,
            depends_on=inv,
            required=False,
            conflict=True,
        )
        installed = {"inventory"}
        dep = ModuleDependency.objects.get(module=old_inv, depends_on=inv)
        assert dep.is_satisfied_by(installed) is False

    def test_is_satisfied_conflict_not_installed(self):
        old_inv = ModuleCatalogItem.objects.create(
            technical_name="old_inventory", display_name="Old Inv", version="1.0.0"
        )
        inv = ModuleCatalogItem.objects.create(
            technical_name="inventory", display_name="Inventory", version="1.0.0"
        )
        ModuleDependency.objects.create(
            module=old_inv,
            depends_on=inv,
            required=False,
            conflict=True,
        )
        installed = {"facturacion"}
        dep = ModuleDependency.objects.get(module=old_inv, depends_on=inv)
        assert dep.is_satisfied_by(installed) is True

    def test_clean_raises_if_required_and_conflict(self):
        sales = ModuleCatalogItem.objects.create(
            technical_name="sales", display_name="Sales", version="1.0.0"
        )
        fact = ModuleCatalogItem.objects.create(
            technical_name="facturacion", display_name="Facturacion", version="1.2.0"
        )
        dep = ModuleDependency(
            module=sales,
            depends_on=fact,
            required=True,
            conflict=True,
        )
        # full_clean() raises ValidationError before hitting the DB
        with pytest.raises(ValidationError):
            from django.db import transaction
            with transaction.atomic():
                dep.save()

    def test_unique_together(self):
        sales = ModuleCatalogItem.objects.create(
            technical_name="sales", display_name="Sales", version="1.0.0"
        )
        fact = ModuleCatalogItem.objects.create(
            technical_name="facturacion", display_name="Facturacion", version="1.2.0"
        )
        ModuleDependency.objects.create(
            module=sales,
            depends_on=fact,
            required=True,
            conflict=False,
        )
        # Duplicate (module, depends_on) should be prevented by unique_together
        with pytest.raises((IntegrityError, ValidationError)):
            from django.db import transaction
            with transaction.atomic():
                ModuleDependency.objects.create(
                    module=sales,
                    depends_on=fact,
                    required=False,
                    conflict=False,
                )


@pytest.mark.django_db
class TestDependencyGraph:
    def test_resolve_simple_chain(self):
        # A depends on B; B depends on C
        a = ModuleCatalogItem.objects.create(technical_name="a", display_name="A", version="1.0")
        b = ModuleCatalogItem.objects.create(technical_name="b", display_name="B", version="1.0")
        c = ModuleCatalogItem.objects.create(technical_name="c", display_name="C", version="1.0")

        ModuleDependency.objects.create(module=a, depends_on=b, required=True, conflict=False)
        ModuleDependency.objects.create(module=b, depends_on=c, required=True, conflict=False)

        from apps.core_marketplace.services import DependencyResolver
        resolver = DependencyResolver()
        plan = resolver.resolve_install_plan("a", with_deps=True)

        # Should install C, then B, then A
        names = [m.technical_name for m in plan.to_install]
        assert names == ["c", "b", "a"]
        assert plan.conflicts == []
        assert plan.warnings == []
        assert names == ["c", "b", "a"]
        assert plan.conflicts == []
        assert plan.warnings == []

    def test_conflict_detection(self):
        # X depends on Y (optional); Z conflicts with Y
        x = ModuleCatalogItem.objects.create(technical_name="x", display_name="X", version="1.0")
        y = ModuleCatalogItem.objects.create(technical_name="y", display_name="Y", version="1.0")
        z = ModuleCatalogItem.objects.create(technical_name="z", display_name="Z", version="1.0")

        ModuleDependency.objects.create(module=x, depends_on=y, required=False, conflict=False)
        ModuleDependency.objects.create(module=z, depends_on=y, required=False, conflict=True)

        from apps.core_marketplace.services import DependencyResolver
        resolver = DependencyResolver()
        # Installing z when y is installed should conflict
        # First simulate y installed
        EnabledModule.objects.create(technical_name="y", django_app="y", status="active")

        plan = resolver.resolve_install_plan("z", with_deps=False)
        # z conflicts with installed y
        assert len(plan.conflicts) == 1
        assert plan.conflicts[0].module_a == "z"
        assert plan.conflicts[0].module_b == "y"
        # x can be installed (optional dep on y, y installed)
        plan_x = resolver.resolve_install_plan("x", with_deps=False)
        assert plan_x.conflicts == []


__all__ = []
