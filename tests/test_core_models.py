from django.test import TestCase

from apps.core_auth.models import AuthPolicy
from apps.core_groups.models import Group
from apps.core_marketplace.models import ModuleCatalogItem
from apps.core_permissions.models import Permission
from apps.core_users.models import UserProfile


class CoreModelsTestCase(TestCase):
    def test_core_models_create(self):
        policy = AuthPolicy.objects.create(name="default")
        group = Group.objects.create(name="admins")
        perm = Permission.objects.create(code="core.view")
        user = UserProfile.objects.create(user_id=1, display_name="Admin")
        mod = ModuleCatalogItem.objects.create(technical_name="core_auth", version="0.1.0")

        self.assertEqual(policy.name, "default")
        self.assertEqual(group.name, "admins")
        self.assertEqual(perm.code, "core.view")
        self.assertEqual(user.display_name, "Admin")
        self.assertEqual(mod.technical_name, "core_auth")
