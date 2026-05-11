# Unit tests for core_marketplace semver utilities

import pytest
from apps.core_marketplace.utils.semver import (
    Version,
    compare_versions,
    satisfies_constraint,
    parse_constraint,
    highest_compatible_version,
    check_upgrade_safety,
)


class TestVersionParsing:
    def test_parse_simple_version(self):
        v = Version.parse("1.2.3")
        assert v.major == 1
        assert v.minor == 2
        assert v.patch == 3
        assert v.pre is None

    def test_parse_version_with_prerelease(self):
        v = Version.parse("1.2.3-alpha.1")
        assert v.major == 1
        assert v.minor == 2
        assert v.patch == 3
        assert v.pre == "alpha"
        assert v.pre_num == 1

    def test_parse_version_with_build_metadata(self):
        v = Version.parse("1.2.3+build.5")
        assert str(v) == "1.2.3+build.5"
        assert v.local == "build.5"

    def test_parse_version_v_prefix(self):
        v = Version.parse("v1.2.3")
        assert v.major == 1
        assert v.minor == 2
        assert v.patch == 3

    def test_parse_invalid_version_missing_patch(self):
        with pytest.raises(ValueError, match="need X.Y.Z"):
            Version.parse("1.2")

    def test_version_equality(self):
        v1 = Version.parse("1.2.3")
        v2 = Version.parse("1.2.3")
        v3 = Version.parse("1.2.4")
        assert v1 == v2
        assert v1 != v3

    def test_version_ordering(self):
        v1 = Version.parse("1.2.3")
        v2 = Version.parse("1.2.4")
        v3 = Version.parse("1.3.0")
        assert v1 < v2
        assert v2 < v3
        assert v1 < v3

    def test_prerelease_ordering(self):
        alpha = Version.parse("1.0.0-alpha")
        beta = Version.parse("1.0.0-beta")
        rc = Version.parse("1.0.0-rc")
        normal = Version.parse("1.0.0")
        assert alpha < beta < rc < normal


class TestConstraintSatisfaction:
    def test_equal_exact_match(self):
        assert satisfies_constraint("1.2.3", "equal", "1.2.3") is True
        assert satisfies_constraint("1.2.3", "equal", "1.2.4") is False

    def test_caret_constraint(self):
        # ^1.2.3 accepts >=1.2.3 <2.0.0
        assert satisfies_constraint("1.2.3", "caret", "1.2.3") is True
        assert satisfies_constraint("1.2.4", "caret", "1.2.3") is True
        assert satisfies_constraint("1.3.0", "caret", "1.2.3") is True
        assert satisfies_constraint("2.0.0", "caret", "1.2.3") is False
        assert satisfies_constraint("1.2.2", "caret", "1.2.3") is False

    def test_approx_equal_constraint(self):
        # ~1.2.3 accepts >=1.2.3 <1.3.0
        assert satisfies_constraint("1.2.3", "approx_equal", "1.2.3") is True
        assert satisfies_constraint("1.2.4", "approx_equal", "1.2.3") is True
        assert satisfies_constraint("1.2.100", "approx_equal", "1.2.3") is True
        assert satisfies_constraint("1.3.0", "approx_equal", "1.2.3") is False
        assert satisfies_constraint("1.2.2", "approx_equal", "1.2.3") is False

    def test_greater_constraints(self):
        assert satisfies_constraint("1.2.3", "greater", "1.2.0") is True
        assert satisfies_constraint("1.2.0", "greater", "1.2.0") is False
        assert satisfies_constraint("1.2.3", "greater_equal", "1.2.3") is True
        assert satisfies_constraint("1.2.3", "greater_equal", "1.2.0") is True

    def test_less_constraints(self):
        assert satisfies_constraint("1.2.3", "less", "1.3.0") is True
        assert satisfies_constraint("1.3.0", "less", "1.3.0") is False
        assert satisfies_constraint("1.2.3", "less_equal", "1.2.3") is True

    def test_parse_constraint_helper(self):
        assert parse_constraint("^1.2.3") == ("caret", "1.2.3")
        assert parse_constraint("~1.2.0") == ("approx_equal", "1.2.0")
        assert parse_constraint(">=1.0.0") == ("greater_equal", "1.0.0")
        assert parse_constraint("1.2.3") == ("equal", "1.2.3")

    def test_highest_compatible_version(self):
        available = ["1.0.0", "1.2.0", "1.2.3", "1.3.0", "2.0.0"]
        # ^1.2.0 means >=1.2.0 <2.0.0 → highest is 1.3.0
        assert highest_compatible_version(["^1.2.0"], available) == "1.3.0"
        # ~1.2.0 means >=1.2.0 <1.3.0 → highest is 1.2.3
        assert highest_compatible_version(["~1.2.0"], available) == "1.2.3"
        # >=1.0.0 and >1.2.0 → highest is 2.0.0
        assert highest_compatible_version([">=1.0.0", ">1.2.0"], available) == "2.0.0"
        # >2.0.0 → no available version satisfies
        assert highest_compatible_version([">2.0.0"], available) is None


class TestUpgradeSafety:
    def test_patch_bump_is_safe(self):
        assert check_upgrade_safety("1.2.3", "1.2.4") == 'SAFE'

    def test_minor_bump_is_safe(self):
        assert check_upgrade_safety("1.2.0", "1.3.0") == 'SAFE'

    def test_major_bump_is_breaking(self):
        assert check_upgrade_safety("1.2.3", "2.0.0") == 'BREAKING_MAJOR'

    def test_dev_version_minor_bump_is_breaking(self):
        assert check_upgrade_safety("0.1.0", "0.2.0") == 'BREAKING_MINOR'

    def test_dev_version_patch_bump_is_safe(self):
        assert check_upgrade_safety("0.1.0", "0.1.1") == 'SAFE'


__all__ = []
