"""Tests para la API REST — endpoints básicos."""
import json
import pytest
from django.test import TestCase, Client
from django.contrib.auth import get_user_model


class TestHealthEndpoint(TestCase):
    def test_health_returns_ok(self):
        """Health check es público."""
        client = Client()
        response = client.get("/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] in ["ok", "degraded"]
        assert "database" in data


class TestModulesAPI(TestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(
            username="apiuser", email="api@test.com", password="testpass123"
        )
        client = Client()
        r = client.post(
            "/api/auth/login",
            data=json.dumps({"username": "apiuser", "password": "testpass123"}),
            content_type="application/json",
        )
        self.token = r.json()["access_token"]

    def test_list_modules_requires_auth(self):
        client = Client()
        response = client.get("/api/modules/")
        assert response.status_code == 401

    def test_list_modules_with_auth(self):
        client = Client()
        response = client.get(
            "/api/modules/",
            HTTP_AUTHORIZATION=f"Bearer {self.token}",
        )
        assert response.status_code == 200

    def test_module_stats(self):
        client = Client()
        response = client.get(
            "/api/modules/stats",
            HTTP_AUTHORIZATION=f"Bearer {self.token}",
        )
        assert response.status_code == 200
        data = response.json()
        assert "total" in data


class TestEventsAPI(TestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(
            username="evtuser", email="evt@test.com", password="testpass123"
        )
        client = Client()
        r = client.post(
            "/api/auth/login",
            data=json.dumps({"username": "evtuser", "password": "testpass123"}),
            content_type="application/json",
        )
        self.token = r.json()["access_token"]

    def test_list_events_requires_auth(self):
        client = Client()
        response = client.get("/api/events/")
        assert response.status_code == 401

    def test_list_events_with_auth(self):
        client = Client()
        response = client.get(
            "/api/events/",
            HTTP_AUTHORIZATION=f"Bearer {self.token}",
        )
        assert response.status_code == 200

    def test_event_stats(self):
        client = Client()
        response = client.get(
            "/api/events/stats",
            HTTP_AUTHORIZATION=f"Bearer {self.token}",
        )
        assert response.status_code == 200
