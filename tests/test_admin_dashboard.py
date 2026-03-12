from django.contrib.auth import get_user_model
from django.test import TestCase


class AdminDashboardTestCase(TestCase):
    def test_admin_dashboard_renders(self):
        User = get_user_model()
        User.objects.create_superuser(username="admin", email="admin@local", password="pass")

        self.client.login(username="admin", password="pass")
        response = self.client.get("/admin/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Usuarios Totales")
