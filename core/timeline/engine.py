"""
SHUNYA — Timeline Engine

The Timeline Engine provides the universal timeline service used by every
object. It records every state change, status transition, relationship
modification, and evidence change as immutable, chronologically-ordered
events with integrity hash chaining.

Capabilities:
    - Record immutable timeline events for any object
    - Query events by object, type, actor, and time range
    - Reconstruct object state at any point in time
    - Verify integrity of SHA-256 hash chains
    - Generate timeline summaries with counts and durations

References:
    - docs/canon/04_universal_object_protocol.md §7 (Timeline)
    - docs/canon/05_runtime_canon.md §6 (Timeline Engine)
"""

from __future__ import annotations

import bisect
from copy import deepcopy
from datetime import datetime
from typing import Any

from core.timeline.models import (
    GENESIS_HASH,
    TimelineEvent,
    TimelineEventType,
    compute_event_hash,
)

# ── Public API ─────────────────────────────────────────────────────────────────


class TimelineEngine:
    """In-memory timeline engine with integrity-protected event chains.

    The engine tracks every event for every object in the system. Events
    are stored in chronological order per object, linked by a SHA-256
    integrity hash chain.

    The engine is designed to be:
        - **Immutable**: Events cannot be deleted or modified after creation
        - **Append-only**: New events are appended, never inserted
        - **Verifiable**: Integrity chains can be recomputed and validated
        - **Stateful**: Object state can be reconstructed at any point in time

    All methods are thread-safe for read operations. Write operations
    (record_event, clear) should be externally synchronized in multi-threaded
    contexts.

    Example::

        engine = TimelineEngine()

        event = engine.record_event(
            object_id="obj_abc_123",
            event_type=TimelineEventType.OBJECT_CREATED,
            actor_id="system",
            data={"source": "import", "name": "Widget Alpha"},
        )

        events = engine.get_events(object_id="obj_abc_123")
        state  = engine.reconstruct_state(object_id="obj_abc_123", at_time="2026-01-15T09:00:00Z")
        valid  = engine.verify_integrity(object_id="obj_abc_123")
    """

    def __init__(self) -> None:
        """Initialize an empty timeline engine."""
        # Ordered list of ALL events across all objects (insertion order)
        self._all_events: list[TimelineEvent] = []
        # Per-object event lists, maintained in timestamp order
        self._events_by_object: dict[str, list[TimelineEvent]] = {}
        # Per-object latest hash (for chaining)
        self._latest_hash: dict[str, str] = {}
        # Per-object latest event_id (for previous_hash chain)
        self._latest_event_id: dict[str, str] = {}

    # ── Recording ─────────────────────────────────────────────────────────────

    def record_event(
        self,
        object_id: str,
        event_type: TimelineEventType | str,
        actor_id: str,
        data: dict[str, Any] | None = None,
        evidence_ids: list[str] | None = None,
        previous_state: dict[str, Any] | None = None,
        new_state: dict[str, Any] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> TimelineEvent:
        """Record a new immutable event on an object's timeline.

        The event is appended to the object's timeline. Its integrity
        hash is automatically computed from the previous event in the
        object's chain.

        Args:
            object_id: The ObjectID this event belongs to.
            event_type: The type of event (TimelineEventType member or string).
            actor_id: The ObjectID of the actor that triggered the event.
            data: Event-specific payload. Defaults to empty dict.
            evidence_ids: Evidence references supporting this event.
            previous_state: Snapshot of state before the event (optional).
            new_state: Snapshot of state after the event (optional).
            metadata: Extensible metadata (optional).

        Returns:
            The newly created TimelineEvent, which is now immutable.

        Raises:
            ValueError: If object_id is empty.
        """
        if not object_id:
            raise ValueError("object_id is required")

        # Normalise event_type to enum
        if isinstance(event_type, str):
            event_type = TimelineEventType.from_string(event_type)
        elif not isinstance(event_type, TimelineEventType):
            raise ValueError(f"Invalid event_type: {event_type!r}")

        # Get the previous hash for the integrity chain
        previous_hash = self._latest_hash.get(object_id, GENESIS_HASH)

        event = TimelineEvent(
            object_id=object_id,
            event_type=event_type,
            actor_id=actor_id,
            data=data or {},
            evidence_ids=evidence_ids or [],
            previous_state=previous_state,
            new_state=new_state,
            previous_hash=previous_hash,
            metadata=metadata or {},
        )

        # Compute and store the integrity hash for this event
        # The hash covers this event's data + its previous_hash link
        event_hash = compute_event_hash(event.data, event.previous_hash)
        event.integrity_hash = event_hash

        # Store the event
        self._all_events.append(event)
        if object_id not in self._events_by_object:
            self._events_by_object[object_id] = []
        events = self._events_by_object[object_id]

        # Insert in chronological order using timestamp
        ts = event.timestamp
        # Use bisect_right so events with the same timestamp maintain FIFO order
        insert_idx = bisect.bisect_right(
            events, ts, key=lambda e: e.timestamp
        )
        events.insert(insert_idx, event)

        # Update the chain state for this object
        self._latest_hash[object_id] = event_hash
        self._latest_event_id[object_id] = event.event_id

        return event

    # ── Queries ───────────────────────────────────────────────────────────────

    def get_events(
        self,
        object_id: str,
        from_time: str | None = None,
        to_time: str | None = None,
        event_type: TimelineEventType | str | None = None,
        limit: int | None = None,
        offset: int = 0,
    ) -> list[TimelineEvent]:
        """Get events for an object, filtered and paginated.

        Events are returned in ascending chronological order (by timestamp).

        Args:
            object_id: The object to query events for.
            from_time: Optional ISO-8601 start bound (inclusive).
            to_time: Optional ISO-8601 end bound (inclusive).
            event_type: Optional filter by event type.
            limit: Maximum number of events to return.
            offset: Number of events to skip (for pagination).

        Returns:
            A list of matching TimelineEvent objects, ordered by timestamp
            ascending. Returns an empty list if the object has no events.
        """
        if object_id not in self._events_by_object:
            return []

        events = self._events_by_object[object_id]

        # Normalise event_type
        if isinstance(event_type, str):
            event_type_filter = TimelineEventType.from_string(event_type)
        else:
            event_type_filter = event_type

        # Filter
        result: list[TimelineEvent] = []
        for ev in events:
            if from_time and ev.timestamp < from_time:
                continue
            if to_time and ev.timestamp > to_time:
                continue
            if event_type_filter and ev.event_type != event_type_filter:
                continue
            result.append(ev)

        # Apply pagination
        if offset > 0:
            result = result[offset:]
        if limit is not None:
            result = result[:limit]

        return result

    def get_latest_events(
        self,
        object_id: str,
        count: int = 10,
    ) -> list[TimelineEvent]:
        """Get the most recent events for an object.

        Args:
            object_id: The object to query.
            count: Number of latest events to return (default 10).

        Returns:
            The *count* most recent events, ordered newest-first.
            Returns an empty list if the object has no events.
        """
        if object_id not in self._events_by_object:
            return []
        events = self._events_by_object[object_id]
        return events[-count:][::-1]

    def get_timeline(self, object_id: str) -> list[TimelineEvent]:
        """Get the full sorted timeline for an object.

        This returns every event for the object in chronological order,
        suitable for state reconstruction or full audit.

        Args:
            object_id: The object to retrieve the timeline for.

        Returns:
            All events for the object, ordered by timestamp ascending.
        """
        return self._events_by_object.get(object_id, [])

    def get_all_objects(self) -> list[str]:
        """Get all object IDs that have recorded events.

        Returns:
            A sorted list of all object_ids that appear in the timeline.
        """
        return sorted(self._events_by_object.keys())

    def get_events_by_type(
        self,
        event_type: TimelineEventType | str,
        limit: int | None = None,
        offset: int = 0,
    ) -> list[TimelineEvent]:
        """Get all events of a specific type across all objects.

        Args:
            event_type: The event type to filter by.
            limit: Maximum events to return.
            offset: Pagination offset.

        Returns:
            Matching events ordered by timestamp ascending.
        """
        if isinstance(event_type, str):
            event_type_filter = TimelineEventType.from_string(event_type)
        else:
            event_type_filter = event_type

        result = [ev for ev in self._all_events if ev.event_type == event_type_filter]

        if offset > 0:
            result = result[offset:]
        if limit is not None:
            result = result[:limit]
        return result

    def get_events_by_actor(
        self,
        actor_id: str,
        limit: int | None = None,
        offset: int = 0,
    ) -> list[TimelineEvent]:
        """Get all events triggered by a specific actor.

        Args:
            actor_id: The ObjectID of the actor.
            limit: Maximum events to return.
            offset: Pagination offset.

        Returns:
            Matching events ordered by timestamp ascending.
        """
        result = [ev for ev in self._all_events if ev.actor_id == actor_id]

        if offset > 0:
            result = result[offset:]
        if limit is not None:
            result = result[:limit]
        return result

    def get_events_in_range(
        self,
        from_time: str,
        to_time: str,
        limit: int | None = None,
        offset: int = 0,
    ) -> list[TimelineEvent]:
        """Get all events within a time range across all objects.

        Args:
            from_time: ISO-8601 start bound (inclusive).
            to_time: ISO-8601 end bound (inclusive).
            limit: Maximum events to return.
            offset: Pagination offset.

        Returns:
            Matching events ordered by timestamp ascending.
        """
        result = [
            ev for ev in self._all_events
            if from_time <= ev.timestamp <= to_time
        ]

        if offset > 0:
            result = result[offset:]
        if limit is not None:
            result = result[:limit]
        return result

    # ── State Reconstruction ──────────────────────────────────────────────────

    def reconstruct_state(
        self,
        object_id: str,
        at_time: str,
    ) -> dict[str, Any]:
        """Reconstruct the state of an object at a specific point in time.

        This replays the object's timeline up to *at_time*, merging
        ``new_state`` snapshots from each event to build the state dict.
        If an event has no ``new_state``, the event's ``data`` dict is
        used as a best-effort delta.

        If no events are found before *at_time*, an empty dict is returned.

        Args:
            object_id: The object to reconstruct state for.
            at_time: ISO-8601 timestamp — the point in time to reconstruct.

        Returns:
            A dict representing the object's state at *at_time*.
        """
        events = self._events_by_object.get(object_id, [])
        state: dict[str, Any] = {}

        for ev in events:
            if ev.timestamp > at_time:
                break

            if ev.new_state is not None:
                # Full-state snapshot — replace
                state = deepcopy(ev.new_state)
            elif ev.previous_state is not None:
                # Delta: apply data as update
                state.update(deepcopy(ev.data))
            else:
                # No state tracking — merge data as best-effort
                state.update(deepcopy(ev.data))

        return state

    # ── Timeline Summary ───────────────────────────────────────────────────────

    def get_timeline_summary(self, object_id: str) -> dict[str, Any]:
        """Generate a summary of the object's timeline.

        Args:
            object_id: The object to summarise.

        Returns:
            A dict with:
                - ``object_id``: The queried object
                - ``total_events``: Total event count
                - ``event_counts_by_type``: Dict mapping event type -> count
                - ``first_event``: The earliest event (or None)
                - ``last_event``: The most recent event (or None)
                - ``first_timestamp``: ISO-8601 of first event (or None)
                - ``last_timestamp``: ISO-8601 of last event (or None)
                - ``duration_days``: Total duration covered (float, or 0.0)
        """
        events = self._events_by_object.get(object_id, [])
        if not events:
            return {
                "object_id": object_id,
                "total_events": 0,
                "event_counts_by_type": {},
                "first_event": None,
                "last_event": None,
                "first_timestamp": None,
                "last_timestamp": None,
                "duration_days": 0.0,
            }

        # Count by type
        counts: dict[str, int] = {}
        for ev in events:
            counts[ev.event_type.value] = counts.get(ev.event_type.value, 0) + 1

        first_ts = events[0].timestamp
        last_ts = events[-1].timestamp

        # Calculate duration in days
        try:
            dt_first = datetime.fromisoformat(first_ts.replace("Z", "+00:00"))
            dt_last = datetime.fromisoformat(last_ts.replace("Z", "+00:00"))
            duration_days = (dt_last - dt_first).total_seconds() / 86400.0
        except (ValueError, TypeError):
            duration_days = 0.0

        return {
            "object_id": object_id,
            "total_events": len(events),
            "event_counts_by_type": counts,
            "first_event": events[0],
            "last_event": events[-1],
            "first_timestamp": first_ts,
            "last_timestamp": last_ts,
            "duration_days": round(duration_days, 4),
        }

    # ── Integrity Chain ────────────────────────────────────────────────────────

    def get_integrity_chain(self, object_id: str) -> list[TimelineEvent]:
        """Get the full integrity hash chain for an object.

        The chain is the chronological list of events where each event's
        ``previous_hash`` points to the hash of its predecessor.

        Args:
            object_id: The object to retrieve the chain for.

        Returns:
            Events in chronological order (same as get_timeline).
        """
        return self._events_by_object.get(object_id, [])

    def verify_integrity(self, object_id: str) -> bool:
        """Verify the integrity hash chain for an object's timeline.

        Recomputes every hash in the chain from scratch and checks two
        invariants:

        1. **Link integrity**: Each event's ``previous_hash`` matches
           the computed hash of its predecessor's data.
        2. **Self integrity**: Each event's ``integrity_hash`` matches
           the recomputed hash of its own data + previous_hash.

        If any event has been tampered with (data modified, previous_hash
        broken, or integrity_hash mismatched), the entire chain is invalid.

        Returns:
            True if every hash in the chain is valid. False if any link
            is broken (event modified, chain corrupted, or object unknown).
        """
        events = self._events_by_object.get(object_id)
        if events is None:
            return False
        if not events:
            return True  # Empty chain is trivially valid

        # First event must have GENESIS_HASH
        if events[0].previous_hash != GENESIS_HASH:
            return False

        # Verify each link in the chain
        prev_hash = GENESIS_HASH
        for ev in events:
            # Check backward link: previous_hash must match computed hash of predecessor
            if ev.previous_hash != prev_hash:
                return False

            # Check self integrity: recompute hash and compare with stored integrity_hash
            computed = compute_event_hash(ev.data, ev.previous_hash)
            if ev.integrity_hash != computed:
                return False

            # Chain forward: this event's hash becomes the next event's expected previous_hash
            prev_hash = computed

        return True

    # ── Lifecycle ─────────────────────────────────────────────────────────────

    def clear(self) -> None:
        """Reset the engine to its initial empty state.

        This is primarily useful for testing — it discards all recorded
        events and resets all integrity chains.
        """
        self._all_events.clear()
        self._events_by_object.clear()
        self._latest_hash.clear()
        self._latest_event_id.clear()
