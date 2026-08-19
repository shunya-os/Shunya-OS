"""
Non-blocking SSE Stream — Real-time event delivery to frontend.

Connects the canonical event bus to SSE clients via a thread-safe queue.
Each client gets its own queue; events are filtered by tenant_id for isolation.

This replaces the disabled blocking-generator approach that killed gunicorn workers.
"""

import json
import logging
import queue
import threading
import time
import uuid
from datetime import datetime, timezone
from typing import Optional

from app.shunya.infrastructure.event_bus import CanonicalEvent, get_event_bus


# ── Per-client SSE queue ───────────────────────────────────────────────

class SSEClient:
    """A single SSE client subscription with tenant isolation."""

    def __init__(self, tenant_id: int, identity_id: str, workspace_id: Optional[int] = None):
        self.client_id = str(uuid.uuid4())
        self.tenant_id = tenant_id
        self.identity_id = identity_id
        self.workspace_id = workspace_id
        self.queue: queue.Queue = queue.Queue(maxsize=500)
        self.created_at = time.time()
        self.last_activity = time.time()

    def push(self, event: CanonicalEvent) -> bool:
        """Push an event to this client's queue. Returns False if queue is full."""
        if self.tenant_id != event.tenant_id:
            return False  # Tenant isolation — reject cross-tenant events
        if self.workspace_id is not None and event.workspace_id != self.workspace_id:
            return False  # Workspace isolation — reject cross-workspace events
        try:
            self.queue.put_nowait(event)
            self.last_activity = time.time()
            return True
        except queue.Full:
            return False

    def drain(self, timeout: float = 0.5) -> list[CanonicalEvent]:
        """Drain all available events from the queue (non-blocking)."""
        events: list[CanonicalEvent] = []
        deadline = time.time() + timeout
        # Block briefly for the first event
        try:
            ev = self.queue.get(timeout=min(timeout, 1.0))
            events.append(ev)
        except queue.Empty:
            pass
        # Drain remaining without blocking
        while time.time() < deadline:
            try:
                events.append(self.queue.get_nowait())
            except queue.Empty:
                break
        return events


# ── SSE Stream Manager ─────────────────────────────────────────────────

class SSEStreamManager:
    """Manages all SSE client subscriptions and routes events from the event bus."""

    def __init__(self):
        self._clients: dict[str, SSEClient] = {}
        self._lock = threading.Lock()
        self._subscription_id: Optional[str] = None
        self._running = False

    def start(self) -> None:
        """Subscribe to the canonical event bus and start routing events."""
        if self._running:
            return
        self._running = True
        bus = get_event_bus()
        self._subscription_id = bus.subscribe(
            "*",  # Subscribe to ALL event types — filter by tenant on delivery
            self._route_event,
            consumer_name="sse_stream_manager",
        )
        # Start Redis relay for cross-worker event delivery
        bus.start_redis_relay()

    def stop(self) -> None:
        """Unsubscribe from the event bus and clear all clients."""
        self._running = False
        if self._subscription_id:
            bus = get_event_bus()
            bus.unsubscribe(self._subscription_id)
            self._subscription_id = None
        with self._lock:
            self._clients.clear()

    def register_client(self, tenant_id: int, identity_id: str, workspace_id: Optional[int] = None) -> SSEClient:
        """Register a new SSE client. Returns the client object."""
        client = SSEClient(tenant_id, identity_id, workspace_id)
        with self._lock:
            self._clients[client.client_id] = client
        return client

    def unregister_client(self, client_id: str) -> None:
        """Remove a client subscription."""
        with self._lock:
            self._clients.pop(client_id, None)

    def _route_event(self, event: CanonicalEvent) -> Optional[str]:
        """Route an event from the bus to all matching SSE clients."""
        with self._lock:
            clients = list(self._clients.values())
        for client in clients:
            client.push(event)
        return None  # Success

    def cleanup_stale_clients(self, max_age_seconds: int = 300) -> int:
        """Remove clients inactive for more than max_age_seconds. Returns count removed."""
        now = time.time()
        stale = []
        with self._lock:
            for cid, client in list(self._clients.items()):
                if now - client.last_activity > max_age_seconds:
                    stale.append(cid)
            for cid in stale:
                del self._clients[cid]
        return len(stale)

    @property
    def active_client_count(self) -> int:
        return len(self._clients)


# Module-level singleton
_manager: Optional[SSEStreamManager] = None


def get_sse_manager() -> SSEStreamManager:
    """Return the application-wide SSE stream manager (lazily created)."""
    global _manager
    if _manager is None:
        _manager = SSEStreamManager()
        _manager.start()
        # Also start the awareness subscriber — it subscribes to the same EventBus
        try:
            from core.awareness.subscriber import start_awareness_subscriber
            start_awareness_subscriber()
        except Exception:
            logger.warning("Awareness subscriber could not be started", exc_info=True)
    return _manager


def reset_sse_manager() -> None:
    """Reset the SSE manager (for testing)."""
    global _manager
    if _manager:
        _manager.stop()
        _manager = None


# ── SSE event serializer ───────────────────────────────────────────────

def serialize_event(event: CanonicalEvent) -> str:
    """Serialize a CanonicalEvent to an SSE data frame."""
    payload = {
        "event_id": event.event_id,
        "event_type": event.event_type,
        "correlation_id": event.correlation_id,
        "trace_id": event.trace_id,
        "timestamp": event.timestamp,
        "tenant_id": event.tenant_id,
        "workspace_id": event.workspace_id,
        "actor": {
            "id": event.actor_id,
            "type": event.actor_type,
            "name": event.actor_name,
        },
        "object": {
            "id": event.object_id,
            "type": event.object_type,
            "version": event.object_version,
        },
        "payload": event.payload,
        "confidence": event.confidence,
    }
    return f"data: {json.dumps(payload, default=str)}\n\n"


def serialize_heartbeat() -> str:
    """Heartbeat to keep the SSE connection alive when no events are flowing."""
    return f": heartbeat {datetime.now(timezone.utc).isoformat()}\n\n"