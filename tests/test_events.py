"""Tests para core_events — EventBus, EventLog, subscriptions."""
import pytest
from django.test import TestCase

from apps.core_events.models import EventLog, EventSubscription
from apps.core_events.bus import EventBus


class TestEventLog(TestCase):
    def test_create_event(self):
        event = EventLog.objects.create(
            event_type="invoice.created",
            source_module="invoicing",
            payload={"invoice_id": 42},
        )
        assert event.id is not None
        assert event.processed is False
        assert str(event) == "⏳ invoice.created from invoicing"

    def test_mark_processed(self):
        event = EventLog.objects.create(
            event_type="test.event",
            source_module="test",
        )
        event.mark_processed()
        assert event.processed is True
        assert event.processed_at is not None

    def test_mark_failed(self):
        event = EventLog.objects.create(
            event_type="test.event",
            source_module="test",
        )
        event.mark_failed("Something went wrong")
        assert event.error_message == "Something went wrong"


class TestEventBus(TestCase):
    def test_emit_creates_log(self):
        event = EventBus.emit(
            "payment.received",
            "payments",
            {"amount": 100},
        )
        assert event.event_type == "payment.received"
        assert event.source_module == "payments"
        assert event.processed is True

    def test_emit_with_handler(self):
        """Un handler registrado en memoria se ejecuta al emitir."""
        received = []

        def my_handler(payload):
            received.append(payload)

        EventBus.subscribe_handler("custom.event", my_handler)
        EventBus.emit("custom.event", "test", {"data": "hello"})

        assert len(received) == 1
        assert received[0]["data"] == "hello"

    def test_get_stats(self):
        EventBus.emit("a", "mod1", {})
        EventBus.emit("b", "mod2", {})

        stats = EventBus.get_stats()
        assert stats["total_events"] >= 2
        assert stats["pending_events"] == 0

    def test_get_event_history(self):
        EventBus.emit("history.test", "mod1", {"x": 1})
        EventBus.emit("history.test", "mod2", {"x": 2})

        history = EventBus.get_event_history(event_type="history.test")
        assert len(history) >= 2

    def test_subscribe_to_db(self):
        EventBus.subscribe(
            "invoice.created",
            "accounting",
            "accounting.events.on_invoice",
        )
        sub = EventSubscription.objects.get(
            event_type="invoice.created",
            subscriber_module="accounting",
        )
        assert sub.handler_path == "accounting.events.on_invoice"
        assert sub.active is True


class TestEventSubscription(TestCase):
    def test_unique_constraint(self):
        EventSubscription.objects.create(
            event_type="test",
            subscriber_module="mod1",
            handler_path="mod1.handler",
        )
        with pytest.raises(Exception):
            EventSubscription.objects.create(
                event_type="test",
                subscriber_module="mod1",
                handler_path="mod1.other",
            )
