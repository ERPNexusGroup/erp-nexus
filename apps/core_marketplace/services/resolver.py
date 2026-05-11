# resolver.py — Dependency resolution service for ERP Nexus Marketplace
#
# Responsibilities:
# - Resolve installation order for modules with dependencies
# - Detect circular dependencies
# - Detect conflicts between modules
# - Provide upgrade safety analysis

from __future__ import annotations

from collections import deque, defaultdict
from dataclasses import dataclass, field
from typing import List, Set, Optional

from django.db import transaction

from apps.core_marketplace.models import (
    ModuleCatalogItem,
    ModuleDependency,
    EnabledModule,
)


# ═══════════════════════════════════════════════════════════════
# Data structures
# ═══════════════════════════════════════════════════════════════


@dataclass(frozen=True, slots=True)
class Conflict:
    """Represents an undisolvable conflict between modules."""
    module_a: str
    module_b: str
    reason: str


@dataclass(frozen=True, slots=True)
class InstallPlan:
    """Result of dependency resolution for a module install."""
    to_install: List[ModuleCatalogItem]  # ordered list (deps first)
    conflicts: List[Conflict] = field(default_factory=list)
    missing_deps: List[str] = field(default_factory=list)
    already_installed: List[EnabledModule] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


@dataclass(frozen=True, slots=True)
class UpgradeCheck:
    """Result of upgrade safety analysis."""
    status: str  # 'SAFE', 'BREAKING_MAJOR', 'BREAKING_MINOR', 'UNKNOWN'
    breaking_changes: List[str] = field(default_factory=list)
    recommended: bool = True


# ═══════════════════════════════════════════════════════════════
# Resolver
# ═══════════════════════════════════════════════════════════════


class DependencyResolver:
    """Resolve module dependencies and detect conflicts."""

    def __init__(self):
        self._visited: Set[str] = set()
        self._stack: Set[str] = set()  # for cycle detection

    def resolve_install_plan(
        self,
        module_name: str,
        with_deps: bool = True,
    ) -> InstallPlan:
        """
        Compute the plan to install a module.

        Args:
            module_name: technical_name of the module to install
            with_deps: if True, include required dependencies in the plan

        Returns:
            InstallPlan with ordered modules to install and any issues
        """
        try:
            target = ModuleCatalogItem.objects.get(technical_name=module_name, is_active=True)
        except ModuleCatalogItem.DoesNotExist:
            return InstallPlan(
                to_install=[],
                missing_deps=[module_name],
                conflicts=[],
                warnings=[f"Module '{module_name}' not found in catalog"],
            )

        # Get currently installed modules
        installed_modules = set(
            EnabledModule.objects.filter(status='active').values_list('technical_name', flat=True)
        )

        self._visited.clear()
        self._stack.clear()

        to_install: List[ModuleCatalogItem] = []
        conflicts: List[Conflict] = []
        missing_deps: List[str] = []
        warnings: List[str] = []

        if target.technical_name in installed_modules:
            # Already installed — this is an upgrade
            return InstallPlan(
                to_install=[],
                already_installed=list(EnabledModule.objects.filter(technical_name=module_name)),
            )

        # DFS to collect dependencies
        def dfs_collect(item: ModuleCatalogItem) -> bool:
            """Collect dependencies for item. Returns False if conflict/missing."""
            if item.technical_name in self._visited:
                return True  # already processed
            if item.technical_name in self._stack:
                # Cycle detected
                warnings.append(f"Circular dependency involving '{item.technical_name}'")
                return False

            self._stack.add(item.technical_name)

            # Get declared dependencies for this module
            deps = ModuleDependency.objects.filter(module=item, required=True).select_related('depends_on')

            for dep in deps:
                dep_item = dep.depends_on

                # Check conflict: is the dependency conflicting with something already planned?
                conflict_with = self._find_conflict(dep_item, installed_modules | {m.technical_name for m in to_install})
                if conflict_with:
                    conflicts.append(Conflict(item.technical_name, conflict_with, "Incompatible modules"))
                    self._stack.remove(item.technical_name)
                    return False

                # Is dependency already installed?
                if dep_item.technical_name in installed_modules:
                    continue  # skip, already present

                # Recurse
                if not dfs_collect(dep_item):
                    self._stack.remove(item.technical_name)
                    return False

                # Add dependency to install list (before current module)
                if dep_item not in to_install:
                    to_install.append(dep_item)

            self._stack.remove(item.technical_name)
            self._visited.add(item.technical_name)
            return True

        # Process target module
        if with_deps:
            success = dfs_collect(target)
            if not success:
                # Cycle or conflict detected during dependency traversal
                pass

            # Check if target itself conflicts with already-installed modules
            conflict_with_target = self._find_conflict(target, installed_modules)
            if conflict_with_target:
                conflicts.append(Conflict(target.technical_name, conflict_with_target, "Incompatible modules"))

            # Finally add target itself (after its deps)
            if target not in to_install:
                to_install.append(target)
        else:
            # No deps — just the target, but check conflicts
            conflict_with = self._find_conflict(target, installed_modules)
            if conflict_with:
                conflicts.append(Conflict(module_a=target.technical_name, module_b=conflict_with, reason="Incompatible modules"))
            # Always include the target in the plan when with_deps=False
            if target not in to_install:
                to_install.append(target)

        return InstallPlan(
            to_install=to_install,
            conflicts=conflicts,
            missing_deps=missing_deps,
            already_installed=list(EnabledModule.objects.filter(status='active')),
            warnings=warnings,
        )

    def _find_conflict(self, item: ModuleCatalogItem, candidates: Set[str]) -> Optional[str]:
        """Check if item conflicts with any module in candidates."""
        # A conflict exists if some other module declares conflict with `item`
        conflicts = ModuleDependency.objects.filter(
            depends_on=item,
            conflict=True
        ).select_related('module')
        for c in conflicts:
            if c.module.technical_name in candidates:
                return c.module.technical_name
        # Also check if item itself conflicts with something already installed
        self_conflicts = ModuleDependency.objects.filter(
            module=item,
            conflict=True
        ).select_related('depends_on')
        for c in self_conflicts:
            if c.depends_on.technical_name in candidates:
                return c.depends_on.technical_name
        return None

    def detect_cycles(self, module_name: str) -> Optional[List[str]]:
        """Detect if adding this module would create a cycle."""
        try:
            target = ModuleCatalogItem.objects.get(technical_name=module_name, is_active=True)
        except ModuleCatalogItem.DoesNotExist:
            return None

        self._visited.clear()
        self._stack.clear()

        def dfs(item: ModuleCatalogItem) -> Optional[List[str]]:
            if item.technical_name in self._visited:
                return None
            if item.technical_name in self._stack:
                # Cycle detected — return the cycle path
                idx = list(self._stack).index(item.technical_name)
                return list(self._stack)[idx:] + [item.technical_name]
            self._stack.add(item.technical_name)
            for dep in ModuleDependency.objects.filter(module=item, required=True).select_related('depends_on'):
                cycle = dfs(dep.depends_on)
                if cycle:
                    return cycle
            self._stack.remove(item.technical_name)
            self._visited.add(item.technical_name)
            return None

        return dfs(target)

    def topological_sort(self, modules: List[ModuleCatalogItem]) -> List[ModuleCatalogItem]:
        """Kahn's algorithm for topological sorting."""
        in_degree: dict[str, int] = {m.technical_name: 0 for m in modules}
        adj: dict[str, List[str]] = defaultdict(list)
        name_to_item = {m.technical_name: m for m in modules}

        for m in modules:
            for dep in ModuleDependency.objects.filter(module=m, required=True).select_related('depends_on'):
                dep_name = dep.depends_on.technical_name
                if dep_name in name_to_item:
                    adj[dep_name].append(m.technical_name)
                    in_degree[m.technical_name] += 1

        queue = deque([n for n, d in in_degree.items() if d == 0])
        result: List[ModuleCatalogItem] = []

        while queue:
            name = queue.popleft()
            result.append(name_to_item[name])
            for neighbor in adj[name]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)

        if len(result) != len(modules):
            raise ValueError("Cycle detected in dependency graph")
        return result

    def check_upgrade_safety(self, module_name: str, target_version: str) -> UpgradeCheck:
        """Check if upgrading to target_version is safe."""
        try:
            current = EnabledModule.objects.get(technical_name=module_name)
        except EnabledModule.DoesNotExist:
            return UpgradeCheck(status='UNKNOWN', breaking_changes=[], recommended=True)

        from apps.core_marketplace.utils.semver import check_upgrade_safety as semver_check

        # Use installed_version if present, fallback to version for backward compatibility
        current_version = getattr(current, 'installed_version', None) or getattr(current, 'version', '0.0.0') or '0.0.0'
        status = semver_check(current_version, target_version)
        breaking: List[str] = []
        if status == 'BREAKING_MAJOR':
            breaking.append("Major version bump — may contain breaking API changes")
            breaking.append("Review release notes before upgrading")
        elif status == 'BREAKING_MINOR':
            breaking.append("Minor version bump in 0.x series — may contain breaking changes")
        return UpgradeCheck(
            status=status,
            breaking_changes=breaking,
            recommended=(status in ('SAFE', 'UNKNOWN')),
        )


def resolve_dependencies(module_name: str, with_deps: bool = True) -> InstallPlan:
    """Convenience wrapper."""
    resolver = DependencyResolver()
    return resolver.resolve_install_plan(module_name, with_deps=with_deps)
