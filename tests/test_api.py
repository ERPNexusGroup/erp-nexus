"""Tests para la API REST — endpoints básicos."""
import pytest
from django.test import TestCase, Client


class TestHealthEndpoint(TestCase):
    def test_health_returns_ok(self):
        client = Client()
        response = client.get("/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"


class TestModulesAPI(TestCase):
    def test_list_modules(self):
        client = Client()
        response = client.get("/api/modules/")
        assert response.status_code == 200

    def test_module_stats(self):
        client = Client()
        response = client.get("/api/modules/stats")
        assert response.status_code == 200
        data = response.json()
        assert "total" in data


class TestEventsAPI(TestCase):
    def test_list_events(self):
        client = Client()
        response = client.get("/api/events/")
        assert response.status_code == 200

    def test_event_stats(self):
        client = Client()
        response = client.get("/api/events/stats")
        assert response.status_code == 200
