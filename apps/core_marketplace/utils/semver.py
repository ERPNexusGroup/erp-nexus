# semver.py — Semantic Versioning utilities for ERP Nexus Marketplace
#
# Supports constraint operators: =, ~, ^, >, >=, <, <=
# Compatible with PEP 440 and npm-style semver ranges.

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Optional, List, Tuple


# ═══════════════════════════════════════════════════════════════
# Version Parsing
# ═══════════════════════════════════════════════════════════════

@dataclass(frozen=True, slots=True)
class Version:
    """Immutable semantic version representation."""
    major: int
    minor: int
    patch: int
    pre: Optional[str] = None  # e.g. "alpha", "beta", "rc"
    pre_num: Optional[int] = None
    dev: Optional[str] = None
    local: Optional[str] = None

    @classmethod
    def parse(cls, v: str) -> Version:
        v = v.strip().lstrip('v').lstrip('V')
        local_part = None
        if '+' in v:
            v, local_part = v.split('+', 1)
        pre_part = None
        if '-' in v:
            v, pre_part = v.split('-', 1)
        core_parts = v.split('.')
        if len(core_parts) < 3:
            raise ValueError(f"Invalid version '{v}': need X.Y.Z")
        try:
            major = int(core_parts[0])
            minor = int(core_parts[1])
            patch = int(core_parts[2])
        except ValueError as e:
            raise ValueError(f"Invalid version '{v}': numeric parts must be integers") from e
        pre = None
        pre_num = None
        if pre_part:
            m = re.match(r'([a-zA-Z]+)(?:\.?(\d+))?', pre_part)
            if m:
                pre = m.group(1).lower()
                if m.group(2):
                    pre_num = int(m.group(2))
            else:
                pre = pre_part.lower()
        return cls(
            major=major,
            minor=minor,
            patch=patch,
            pre=pre,
            pre_num=pre_num,
            local=local_part,
        )

    def __str__(self) -> str:
        parts = [f"{self.major}.{self.minor}.{self.patch}"]
        if self.pre:
            pre_str = self.pre
            if self.pre_num is not None:
                pre_str += str(self.pre_num)
            parts.append(f"-{pre_str}")
        if self.local:
            parts.append(f"+{self.local}")
        return ''.join(parts)

    def __lt__(self, other: Version) -> bool:
        if self.major != other.major:
            return self.major < other.major
        if self.minor != other.minor:
            return self.minor < other.minor
        if self.patch != other.patch:
            return self.patch < other.patch
        if self.pre != other.pre:
            if self.pre is None:
                return False
            if other.pre is None:
                return True
            if self.pre != other.pre:
                return self.pre < other.pre
            s_num = self.pre_num or 0
            o_num = other.pre_num or 0
            return s_num < o_num
        return False

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Version):
            return False
        return (
            self.major == other.major
            and self.minor == other.minor
            and self.patch == other.patch
            and self.pre == other.pre
            and self.pre_num == other.pre_num
        )

    def __le__(self, other: Version) -> bool:
        return self < other or self == other

    def __gt__(self, other: Version) -> bool:
        return not self <= other

    def __ge__(self, other: Version) -> bool:
        return not self < other


def compare_versions(v1: str, v2: str) -> int:
    v1_obj = Version.parse(v1)
    v2_obj = Version.parse(v2)
    if v1_obj < v2_obj:
        return -1
    if v1_obj > v2_obj:
        return 1
    return 0


# ═══════════════════════════════════════════════════════════════
# Constraint Satisfaction
# ═══════════════════════════════════════════════════════════════

def satisfies_constraint(version_str: str, op: str, constraint_str: str) -> bool:
    v = Version.parse(version_str)
    c = Version.parse(constraint_str)
    if op == 'equal':
        return v == c
    elif op == 'approx_equal':  # ~1.2.3 → >=1.2.3 <1.3.0
        if v.major != c.major or v.minor != c.minor:
            return False
        return v.patch >= c.patch
    elif op == 'caret':  # ^1.2.3 → >=1.2.3 <2.0.0
        if v.major != c.major:
            return False
        return v >= c
    elif op == 'greater':
        return v > c
    elif op == 'greater_equal':
        return v >= c
    elif op == 'less':
        return v < c
    elif op == 'less_equal':
        return v <= c
    else:
        raise ValueError(f"Unknown constraint operator: {op}")


def parse_constraint(constraint: str) -> Tuple[str, str]:
    operators = ['^', '~', '>=', '<=', '>', '<', '=']
    for op in operators:
        if constraint.startswith(op):
            return (op_to_type(op), constraint[len(op):])
    return ('equal', constraint)


def op_to_type(op: str) -> str:
    mapping = {
        '=': 'equal',
        '~': 'approx_equal',
        '^': 'caret',
        '>': 'greater',
        '>=': 'greater_equal',
        '<': 'less',
        '<=': 'less_equal',
    }
    return mapping[op]


def highest_compatible_version(constraints: List[str], available: List[str]) -> Optional[str]:
    candidates = []
    for v in available:
        all_match = True
        for constraint in constraints:
            op, cv = parse_constraint(constraint)
            if not satisfies_constraint(v, op, cv):
                all_match = False
                break
        if all_match:
            candidates.append(v)
    if not candidates:
        return None
    return max(candidates, key=lambda x: Version.parse(x))


# ═══════════════════════════════════════════════════════════════
# Upgrade Safety Analysis
# ═══════════════════════════════════════════════════════════════

def check_upgrade_safety(from_version: str, to_version: str) -> str:
    try:
        from_v = Version.parse(from_version)
        to_v = Version.parse(to_version)
    except ValueError:
        return 'UNKNOWN'
    if from_v.major == 0:
        if to_v.major != from_v.major:
            return 'BREAKING_MAJOR'
        if to_v.minor != from_v.minor:
            return 'BREAKING_MINOR'
        return 'SAFE'
    else:
        if to_v.major > from_v.major:
            return 'BREAKING_MAJOR'
        if to_v.minor > from_v.minor:
            return 'SAFE'
        return 'SAFE'


def is_compatible_with_erp(module_min_erp: str, module_max_erp: Optional[str], current_erp: str) -> bool:
    try:
        current = Version.parse(current_erp)
        min_v = Version.parse(module_min_erp) if module_min_erp else None
        max_v = Version.parse(module_max_erp) if module_max_erp else None
    except ValueError:
        return True
    if min_v and current < min_v:
        return False
    if max_v and current > max_v:
        return False
    return True


__all__ = [
    'Version',
    'compare_versions',
    'satisfies_constraint',
    'parse_constraint',
    'highest_compatible_version',
    'check_upgrade_safety',
    'is_compatible_with_erp',
]
