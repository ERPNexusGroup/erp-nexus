from django.contrib.auth import get_user_model
from django.test import TestCase

from apps.core_auth.models import AuthPolicy
from apps.core_groups.models import Group
from apps.core_marketplace.models import ModuleCatalogItem
from apps.core_permissions.models import Permission
from apps.core_users.models import UserProfile


class CoreModelsTestCase(TestCase):
    def test_core_models_create(self):
        User = get_user_model()
        user = User.objects.create_user(username="admin", password="pass")

        policy = AuthPolicy.objects.create(name="default")
        group = Group.objects.create(name="admins")
        perm = Permission.objects.create(code="core.view")
        profile = UserProfile.objects.create(user=user, display_name="Admin")
        mod = ModuleCatalogItem.objects.create(technical_name="core_auth", version="0.1.0")

        self.assertEqual(policy.name, "default")
        self.assertEqual(group.name, "admins")
        self.assertEqual(perm.code, "core.view")
        self.assertEqual(profile.display_name, "Admin")
        self.assertEqual(mod.technical_name, "core_auth")

        group.permissions.add(perm)
        profile.groups.add(group)
        self.assertEqual(group.permissions.count(), 1)
        self.assertEqual(profile.groups.count(), 1)
