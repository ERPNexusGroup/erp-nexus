from django.contrib.auth import get_user_model
from django.test import TestCase

from apps.core_companies.models import Company, Membership
from apps.core_users.models import UserProfile


class MultiTenancyTestCase(TestCase):
    def test_company_membership_and_active_company(self):
        User = get_user_model()
        user = User.objects.create_user(username="alice", password="pass")
        profile = UserProfile.objects.create(user=user, display_name="Alice")

        company = Company.objects.create(name="Acme Corp", slug="acme")
        Membership.objects.create(user=user, company=company, role="admin")

        profile.active_company = company
        profile.save(update_fields=["active_company"])

        profile.refresh_from_db()
        self.assertEqual(profile.active_company, company)
