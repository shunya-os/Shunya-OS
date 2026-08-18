"""
Tests for the non-blocking SSE stream manager and event serialization.

Verifies:
1. SSE client creation and tenant isolation
2. Event routing through the manager
3. Event serialization
4. Cross-tenant isolation
5. Queue full behavior
6. Client lifecycle (register/unregister)
"""

import json
import time
from datetime import datetime, timezone

import pytest

from app.reality_engine.sse_stream import (
    SSEClient,
    SSEStreamManager,
    serialize_event,
    serialize_heartbeat,
    get_sse_manager,
    reset_sse_manager,
)
from app.shunya.infrastructure.event_bus import CanonicalEvent, get_event_bus, reset_event_bus


# ── Fixtures ─────────────────────────────────────────────────────────────────


@pytest.fixture(autouse=True)
def clean_state():
    reset_event_bus()
    reset_sse_manager()
    yield
    reset_event_bus()
    reset_sse_manager()


def make_event(
    event_type: str = "test.event",
    tenant_id: int = 1,
    workspace_id: int = 1,
    object_id: str = "obj_001",
    object_type: str = "test",
    actor_id: str = "actor_001",
) -> CanonicalEvent:
    return CanonicalEvent(
        event_type=event_type,
        tenant_id=tenant_id,
        workspace_id=workspace_id,
        object_id=object_id,
        object_type=object_type,
        actor_id=actor_id,
        actor_type="user",
        timestamp=datetime.now(timezone.utc).isoformat(),
    )


# ── SSEClient tests ─────────────────────────────────────────────────────────


class TestSSEClient:
    def test_create_client(self):
        client = SSEClient(tenant_id=1, identity_id="user_1")
        assert client.tenant_id == 1
        assert client.identity_id == "user_1"
        assert client.client_id is not None
        assert client.queue.maxsize == 500

    def test_push_event(self):
        client = SSEClient(tenant_id=1, identity_id="user_1")
        event = make_event(tenant_id=1)
        result = client.push(event)
        assert result is True
        assert client.queue.qsize() == 1

    def test_cross_tenant_isolation(self):
        client = SSEClient(tenant_id=1, identity_id="user_1")
        event = make_event(tenant_id=2)  # Different tenant
        result = client.push(event)
        assert result is False  # Rejected — tenant isolation
        assert client.queue.qsize() == 0

    def test_workspace_isolation(self):
        client = SSEClient(tenant_id=1, identity_id="user_1", workspace_id=1)
        event = make_event(tenant_id=1, workspace_id=2)  # Different workspace
        result = client.push(event)
        assert result is False  # Rejected — workspace isolation
        assert client.queue.qsize() == 0

    def test_drain_events(self):
        client = SSEClient(tenant_id=1, identity_id="user_1")
        for i in range(5):
            client.push(make_event(event_type=f"test.{i}", tenant_id=1))
        events = client.drain(timeout=0.1)
        assert len(events) == 5

    def test_drain_empty_queue(self):
        client = SSEClient(tenant_id=1, identity_id="user_1")
        events = client.drain(timeout=0.1)
        assert len(events) == 0

    def test_queue_full(self):
        client = SSEClient(tenant_id=1, identity_id="user_1")
        # Fill the queue
        for i in range(500):
            client.push(make_event(event_type=f"test.{i}", tenant_id=1))
        # Next push should fail
        result = client.push(make_event(tenant_id=1))
        assert result is False


# ── SSEStreamManager tests ──────────────────────────────────────────────────


class TestSSEStreamManager:
    def test_create_manager(self):
        manager = SSEStreamManager()
        assert manager.active_client_count == 0

    def test_register_client(self):
        manager = SSEStreamManager()
        client = manager.register_client(tenant_id=1, identity_id="user_1")
        assert client is not None
        assert manager.active_client_count == 1

    def test_unregister_client(self):
        manager = SSEStreamManager()
        client = manager.register_client(tenant_id=1, identity_id="user_1")
        manager.unregister_client(client.client_id)
        assert manager.active_client_count == 0

    def test_route_event_to_clients(self):
        """SSE manager subscribes to the event bus and routes events to clients."""
        manager = SSEStreamManager()
        manager.start()

        client = manager.register_client(tenant_id=1, identity_id="user_1")
        event = make_event(tenant_id=1)

        # Publish via the event bus
        bus = get_event_bus()
        bus.publish(event)

        # Allow event to be routed
        time.sleep(0.1)

        # Client should have received the event
        events = client.drain(timeout=0.1)
        assert len(events) >= 1
        assert events[0].event_type == "test.event"

    def test_cross_tenant_isolation_in_manager(self):
        """Events from tenant A should not reach tenant B's clients."""
        manager = SSEStreamManager()
        manager.start()

        client_a = manager.register_client(tenant_id=1, identity_id="user_a")
        client_b = manager.register_client(tenant_id=2, identity_id="user_b")

        bus = get_event_bus()
        bus.publish(make_event(tenant_id=1))
        time.sleep(0.1)

        events_a = client_a.drain(timeout=0.1)
        events_b = client_b.drain(timeout=0.1)

        assert len(events_a) >= 1  # Tenant A gets the event
        assert len(events_b) == 0  # Tenant B does NOT

    def test_cleanup_stale_clients(self):
        manager = SSEStreamManager()
        client = manager.register_client(tenant_id=1, identity_id="user_1")
        # Make the client appear stale
        client.last_activity = time.time() - 400  # 400s ago
        removed = manager.cleanup_stale_clients(max_age_seconds=300)
        assert removed == 1
        assert manager.active_client_count == 0


# ── Serialization tests ─────────────────────────────────────────────────────


class TestSerialization:
    def test_serialize_event(self):
        event = make_event(
            event_type="test.event",
            tenant_id=1,
            workspace_id=1,
            object_id="obj_001",
            object_type="test_object",
            actor_id="actor_001",
        )
        sse_data = serialize_event(event)
        assert sse_data.startswith("data: ")
        assert sse_data.endswith("\n\n")

        parsed = json.loads(sse_data[6:].strip())
        assert parsed["event_type"] == "test.event"
        assert parsed["tenant_id"] == 1
        assert parsed["object"]["id"] == "obj_001"
        assert parsed["object"]["type"] == "test_object"
        assert parsed["actor"]["id"] == "actor_001"
        assert parsed["event_id"] == event.event_id

    def test_serialize_heartbeat(self):
        data = serialize_heartbeat()
        assert data.startswith(": heartbeat")
        assert data.endswith("\n\n")

    def test_serialize_roundtrip(self):
        """Verify that serialized data can be parsed and contains all fields."""
        event = make_event()
        sse = serialize_event(event)
        parsed = json.loads(sse[6:].strip())

        assert "event_id" in parsed
        assert "event_type" in parsed
        assert "timestamp" in parsed
        assert "tenant_id" in parsed
        assert "workspace_id" in parsed
        assert "actor" in parsed
        assert "object" in parsed
        assert "payload" in parsed
        assert "confidence" in parsed

        # Verify no internal fields are leaked
        assert "password" not in parsed
        assert "secret" not in parsed
        assert "token" not in parsed


# ── Singleton access tests ──────────────────────────────────────────────────


class TestSingleton:
    def test_get_sse_manager(self):
        manager = get_sse_manager()
        assert manager is not None
        assert manager._running is True

    def test_sse_manager_is_singleton(self):
        m1 = get_sse_manager()
        m2 = get_sse_manager()
        assert m1 is m2

    def test_reset_sse_manager(self):
        m1 = get_sse_manager()
        reset_sse_manager()
        m2 = get_sse_manager()
        assert m1 is not m2