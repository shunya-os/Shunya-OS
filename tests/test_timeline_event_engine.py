"""Comprehensive tests for the SHUNYA Timeline Engine and Event Engine."""

from __future__ import annotations

import time
from typing import Any

import pytest

from core.timeline import (
    GENESIS_HASH,
    TimelineEngine,
    TimelineEvent,
    TimelineEventType,
    compute_event_hash,
)
from core.event import EventEngine, EventPriority, EventType, SystemEvent


# ============================================================================
# TimelineEngine Tests
# ============================================================================


class TestTimelineEvent:
    """TimelineEvent dataclass construction and validation."""

    def test_default_construction(self) -> None:
        ev = TimelineEvent(object_id="o1", event_type=TimelineEventType.OBJECT_CREATED, actor_id="sys")
        assert isinstance(ev.event_id, str)
        assert "-" in ev.event_id
        assert ev.event_type == TimelineEventType.OBJECT_CREATED
        assert ev.previous_hash == GENESIS_HASH
        assert ev.verify_hash() is False  # no integrity_hash set yet
        assert ev.data == {}
        assert ev.evidence_ids == []

    def test_verify_hash_with_integrity_hash(self) -> None:
        # Simulate what the engine does: set integrity_hash after construction
        ev = TimelineEvent(object_id="o1", event_type=TimelineEventType.OBJECT_CREATED, actor_id="sys")
        h = compute_event_hash(ev.data, ev.previous_hash)
        ev.integrity_hash = h
        assert ev.verify_hash() is True

    def test_verify_hash_false_on_mismatch(self) -> None:
        ev = TimelineEvent(previous_hash=GENESIS_HASH)
        ev.integrity_hash = "f" * 64  # wrong hash
        assert ev.verify_hash() is False

    def test_from_string_known(self) -> None:
        assert TimelineEventType.from_string("object_created") == TimelineEventType.OBJECT_CREATED

    def test_from_string_unknown_falls_to_custom(self) -> None:
        assert TimelineEventType.from_string("garbage") == TimelineEventType.CUSTOM

    def test_enum_has_12_members(self) -> None:
        assert len(TimelineEventType) == 12


class TestTimelineEngineRecording:
    """Event recording and chronological ordering."""

    def test_record_event(self) -> None:
        tl = TimelineEngine()
        ev = tl.record_event("o1", TimelineEventType.OBJECT_CREATED, "sys", data={"v": 1})
        assert ev.object_id == "o1"
        assert ev.event_type == TimelineEventType.OBJECT_CREATED
        assert ev.data == {"v": 1}

    def test_record_event_with_string_type(self) -> None:
        tl = TimelineEngine()
        ev = tl.record_event("o1", "object_created", "sys")
        assert ev.event_type == TimelineEventType.OBJECT_CREATED

    def test_record_event_with_evidence(self) -> None:
        tl = TimelineEngine()
        ev = tl.record_event("o1", "object_modified", "u", evidence_ids=["ev_001"])
        assert ev.evidence_ids == ["ev_001"]

    def test_record_event_raises_on_empty_object_id(self) -> None:
        tl = TimelineEngine()
        with pytest.raises(ValueError, match="object_id is required"):
            tl.record_event("", "custom", "sys")

    def test_chronological_ordering(self) -> None:
        tl = TimelineEngine()
        tl.record_event("o1", TimelineEventType.OBJECT_CREATED, "sys", data={"v": 1})
        tl.record_event("o1", TimelineEventType.OBJECT_MODIFIED, "u", data={"v": 2})
        tl.record_event("o1", TimelineEventType.STATUS_CHANGED, "u", data={"v": 3})
        events = tl.get_timeline("o1")
        assert events[0].event_type == TimelineEventType.OBJECT_CREATED
        assert events[1].event_type == TimelineEventType.OBJECT_MODIFIED
        assert events[2].event_type == TimelineEventType.STATUS_CHANGED

    def test_record_event_with_metadata(self) -> None:
        tl = TimelineEngine()
        ev = tl.record_event("o1", "custom", "sys", metadata={"trace": "abc"})
        assert ev.metadata == {"trace": "abc"}


class TestTimelineEngineIntegrity:
    """SHA-256 integrity hash chain."""

    def test_genesis_hash_on_first_event(self) -> None:
        tl = TimelineEngine()
        ev = tl.record_event("chain", TimelineEventType.OBJECT_CREATED, "sys", data={"s": 1})
        assert ev.previous_hash == GENESIS_HASH

    def test_chain_links_three_events(self) -> None:
        tl = TimelineEngine()
        tl.record_event("chain", "object_created", "sys", data={"s": 1})
        tl.record_event("chain", "object_modified", "u", data={"s": 2})
        tl.record_event("chain", "object_modified", "u", data={"s": 3})
        chain = tl.get_integrity_chain("chain")
        assert len(chain) == 3
        assert chain[0].previous_hash == GENESIS_HASH
        assert chain[1].previous_hash != GENESIS_HASH
        assert chain[2].previous_hash != GENESIS_HASH

    def test_verify_integrity_valid(self) -> None:
        tl = TimelineEngine()
        tl.record_event("chain", "object_created", "sys", data={"s": 1})
        tl.record_event("chain", "object_modified", "u", data={"s": 2})
        assert tl.verify_integrity("chain") is True

    def test_verify_integrity_detects_tamper(self) -> None:
        tl = TimelineEngine()
        tl.record_event("chain", "object_created", "sys", data={"s": 1})
        tl.record_event("chain", "object_modified", "u", data={"s": 2})
        chain = tl.get_integrity_chain("chain")
        chain[1].data["s"] = 999  # tamper
        assert tl.verify_integrity("chain") is False

    def test_verify_integrity_unknown_object(self) -> None:
        tl = TimelineEngine()
        assert tl.verify_integrity("nope") is False

    def test_single_event_chain_valid(self) -> None:
        tl = TimelineEngine()
        tl.record_event("solo", "object_created", "sys", data={})
        assert tl.verify_integrity("solo") is True

    def test_hash_determinism(self) -> None:
        h1 = compute_event_hash({"a": 1, "b": 2}, GENESIS_HASH)
        h2 = compute_event_hash({"b": 2, "a": 1}, GENESIS_HASH)
        assert h1 == h2
        assert len(h1) == 64
        assert all(c in "0123456789abcdef" for c in h1)

    def test_hash_different_data(self) -> None:
        h1 = compute_event_hash({"a": 1}, GENESIS_HASH)
        h2 = compute_event_hash({"a": 2}, GENESIS_HASH)
        assert h1 != h2

    def test_hash_different_prev_hash(self) -> None:
        h1 = compute_event_hash({"a": 1}, GENESIS_HASH)
        h2 = compute_event_hash({"a": 1}, "f" * 64)
        assert h1 != h2


class TestTimelineEngineQueries:
    """Event queries with filtering and pagination."""

    def setup(self) -> TimelineEngine:
        tl = TimelineEngine()
        for i in range(5):
            tl.record_event("q1", "object_modified", "alice", data={"i": i})
        tl.record_event("q2", "object_created", "bob", data={"n": "B"})
        return tl

    def test_get_events(self) -> None:
        tl = self.setup()
        assert len(tl.get_events("q1")) == 5

    def test_get_events_unknown(self) -> None:
        tl = TimelineEngine()
        assert tl.get_events("nope") == []

    def test_get_events_pagination_limit(self) -> None:
        tl = self.setup()
        assert len(tl.get_events("q1", limit=2)) == 2

    def test_get_events_pagination_offset(self) -> None:
        tl = self.setup()
        assert len(tl.get_events("q1", limit=2, offset=2)) == 2

    def test_get_latest_events(self) -> None:
        tl = self.setup()
        latest = tl.get_latest_events("q1", 1)
        assert len(latest) == 1
        assert latest[0].data["i"] == 4  # newest

    def test_get_latest_events_unknown(self) -> None:
        tl = TimelineEngine()
        assert tl.get_latest_events("nope") == []

    def test_get_timeline(self) -> None:
        tl = self.setup()
        assert len(tl.get_timeline("q1")) == 5

    def test_get_events_by_type(self) -> None:
        tl = self.setup()
        events = tl.get_events_by_type(TimelineEventType.OBJECT_CREATED)
        assert len(events) == 1

    def test_get_events_by_type_with_string(self) -> None:
        tl = self.setup()
        events = tl.get_events_by_type("object_created")
        assert len(events) == 1

    def test_get_events_by_actor(self) -> None:
        tl = self.setup()
        events = tl.get_events_by_actor("bob")
        assert len(events) == 1

    def test_get_events_in_range(self) -> None:
        tl = self.setup()
        events = tl.get_events_in_range("2000-01-01T00:00:00Z", "2099-01-01T00:00:00Z", limit=2)
        assert len(events) == 2

    def test_get_all_objects(self) -> None:
        tl = self.setup()
        assert tl.get_all_objects() == ["q1", "q2"]


class TestTimelineEngineStateReconstruction:
    """Point-in-time state reconstruction."""

    def test_reconstruct_state_empty_before_events(self) -> None:
        tl = TimelineEngine()
        tl.record_event("s1", "object_created", "sys", data={"name": "W", "v": 1})
        state = tl.reconstruct_state("s1", "2000-01-01T00:00:00Z")
        assert state == {}

    def test_reconstruct_state_after_events(self) -> None:
        tl = TimelineEngine()
        tl.record_event("s1", "object_created", "sys", data={"name": "W", "v": 1})
        tl.record_event(
            "s1", "object_modified", "u", data={"v": 2},
            new_state={"name": "W", "v": 2, "status": "draft"},
        )
        tl.record_event(
            "s1", "status_changed", "u", data={"old": "draft", "new": "active"},
            previous_state={"name": "W", "v": 2, "status": "draft"},
            new_state={"name": "W", "v": 2, "status": "active"},
        )
        state = tl.reconstruct_state("s1", "2099-01-01T00:00:00Z")
        assert state["name"] == "W"
        assert state["v"] == 2
        assert state["status"] == "active"

    def test_reconstruct_state_unknown_object(self) -> None:
        tl = TimelineEngine()
        assert tl.reconstruct_state("nope", "2099Z") == {}


class TestTimelineEngineSummary:
    """Timeline summary generation."""

    def test_summary_with_events(self) -> None:
        tl = TimelineEngine()
        tl.record_event("s1", "object_created", "sys", data={"v": 1})
        tl.record_event("s1", "object_modified", "u", data={"v": 2})
        summary = tl.get_timeline_summary("s1")
        assert summary["total_events"] == 2
        assert summary["event_counts_by_type"]["object_created"] == 1
        assert summary["event_counts_by_type"]["object_modified"] == 1
        assert summary["first_event"] is not None
        assert summary["last_event"] is not None
        assert isinstance(summary["duration_days"], float)

    def test_summary_empty_object(self) -> None:
        tl = TimelineEngine()
        summary = tl.get_timeline_summary("nope")
        assert summary["total_events"] == 0
        assert summary["event_counts_by_type"] == {}
        assert summary["first_event"] is None
        assert summary["last_event"] is None
        assert summary["duration_days"] == 0.0


class TestTimelineEngineClear:
    """Engine reset."""

    def test_clear_removes_all(self) -> None:
        tl = TimelineEngine()
        tl.record_event("o1", "object_created", "sys", data={})
        tl.clear()
        assert tl.get_all_objects() == []
        assert tl.verify_integrity("o1") is False


# ============================================================================
# EventEngine Tests
# ============================================================================


class TestSystemEvent:
    """SystemEvent dataclass construction."""

    def test_default_construction(self) -> None:
        se = SystemEvent(
            event_type=EventType.OBJECT_CREATED, source="test", actor_id="sys", object_id="o1",
        )
        assert "-" in se.event_id
        assert se.event_version == 1
        assert se.priority == EventPriority.NORMAL
        assert se.ttl_seconds is None
        assert se.payload == {}
        assert se.related_object_ids == []
        assert se.evidence_ids == []


class TestEventType:
    """EventType enum."""

    def test_has_23_members(self) -> None:
        assert len(EventType) == 23

    def test_from_string(self) -> None:
        assert EventType.from_string("object.created") == EventType.OBJECT_CREATED

    def test_from_string_invalid_raises(self) -> None:
        with pytest.raises(ValueError):
            EventType.from_string("garbage")


class TestEventPriority:
    """EventPriority enum."""

    def test_has_4_levels(self) -> None:
        assert len(EventPriority) == 4

    def test_values(self) -> None:
        assert EventPriority.CRITICAL.value == "critical"
        assert EventPriority.HIGH.value == "high"
        assert EventPriority.NORMAL.value == "normal"
        assert EventPriority.LOW.value == "low"


class TestEventEngineEmission:
    """Event emission."""

    def test_emit_returns_system_event(self) -> None:
        ee = EventEngine()
        ev = ee.emit(EventType.OBJECT_CREATED, "factory", "sys", "obj1", payload={"n": "A"})
        assert isinstance(ev, SystemEvent)
        assert ev.event_type == EventType.OBJECT_CREATED
        assert ev.payload == {"n": "A"}

    def test_emit_with_string_event_type(self) -> None:
        ee = EventEngine()
        ev = ee.emit("object.created", "factory", "sys", "o1")
        assert ev.event_type == EventType.OBJECT_CREATED

    def test_emit_with_priority_string(self) -> None:
        ee = EventEngine()
        ev = ee.emit(EventType.OBJECT_CREATED, "factory", "sys", "o1", priority="high")
        assert ev.priority == EventPriority.HIGH

    def test_emit_with_priority_enum(self) -> None:
        ee = EventEngine()
        ev = ee.emit(EventType.OBJECT_CREATED, "factory", "sys", "o1", priority=EventPriority.CRITICAL)
        assert ev.priority == EventPriority.CRITICAL

    def test_emit_with_related_and_evidence(self) -> None:
        ee = EventEngine()
        ev = ee.emit(
            EventType.OBJECT_DELETED, "factory", "u1", "obj1",
            related_object_ids=["obj2"],
            evidence_ids=["ev1"],
            metadata={"reason": "cleanup"},
        )
        assert ev.related_object_ids == ["obj2"]
        assert ev.evidence_ids == ["ev1"]
        assert ev.metadata == {"reason": "cleanup"}

    def test_emit_invalid_event_type_raises(self) -> None:
        ee = EventEngine()
        with pytest.raises(ValueError):
            ee.emit(999, "test", "sys", "o1")  # type: ignore[arg-type]

    def test_emit_invalid_priority_raises(self) -> None:
        ee = EventEngine()
        with pytest.raises(ValueError):
            ee.emit(EventType.OBJECT_CREATED, "test", "sys", "o1", priority="bogus")


class TestEventEngineSubscriptions:
    """Event subscription and delivery."""

    def test_subscribe_and_receive(self) -> None:
        ee = EventEngine()
        got: list[SystemEvent] = []

        def handler(ev: SystemEvent) -> None:
            got.append(ev)

        ee.subscribe(EventType.OBJECT_CREATED, handler)
        ee.emit(EventType.OBJECT_CREATED, "test", "sys", "o1", payload={})
        time.sleep(0.2)
        assert len(got) == 1
        assert got[0].object_id == "o1"

    def test_subscribe_only_receives_new_events(self) -> None:
        ee = EventEngine()
        ee.emit(EventType.OBJECT_CREATED, "test", "sys", "o1", payload={})
        got: list[SystemEvent] = []

        def handler(ev: SystemEvent) -> None:
            got.append(ev)

        ee.subscribe(EventType.OBJECT_CREATED, handler)
        time.sleep(0.2)
        # Handler should NOT receive events emitted before subscription
        assert len(got) == 0

    def test_unsubscribe_prevents_delivery(self) -> None:
        ee = EventEngine()
        got: list[SystemEvent] = []

        def handler(ev: SystemEvent) -> None:
            got.append(ev)

        sid = ee.subscribe(EventType.OBJECT_CREATED, handler)
        ee.unsubscribe(sid)
        ee.emit(EventType.OBJECT_CREATED, "test", "sys", "o1", payload={})
        time.sleep(0.2)
        assert len(got) == 0

    def test_unsubscribe_unknown_returns_false(self) -> None:
        ee = EventEngine()
        assert ee.unsubscribe("fake") is False

    def test_wildcard_subscription(self) -> None:
        ee = EventEngine()
        got: list[SystemEvent] = []

        def handler(ev: SystemEvent) -> None:
            got.append(ev)

        ee.subscribe("*", handler)
        ee.emit(EventType.ERROR, "test", "sys", "o1", payload={})
        time.sleep(0.2)
        assert len(got) >= 1

    def test_all_wildcard_subscription(self) -> None:
        ee = EventEngine()
        got: list[SystemEvent] = []

        def handler(ev: SystemEvent) -> None:
            got.append(ev)

        ee.subscribe("all", handler)
        ee.emit(EventType.WARNING, "test", "sys", "o1", payload={})
        time.sleep(0.2)
        assert len(got) >= 1

    def test_get_subscriptions(self) -> None:
        ee = EventEngine()
        sid = ee.subscribe(EventType.ERROR, lambda e: None)
        subs = ee.get_subscriptions()
        assert "error" in subs
        assert len(subs["error"]) == 1
        assert subs["error"][0] == sid

    def test_handler_exception_does_not_crash_bus(self) -> None:
        ee = EventEngine()

        def crashing_handler(ev: SystemEvent) -> None:
            raise RuntimeError("handler crash")

        ee.subscribe(EventType.OBJECT_CREATED, crashing_handler)
        # Should not raise
        ee.emit(EventType.OBJECT_CREATED, "test", "sys", "o1", payload={})
        time.sleep(0.2)

    def test_multiple_handlers_same_type(self) -> None:
        ee = EventEngine()
        got1: list[SystemEvent] = []
        got2: list[SystemEvent] = []

        def h1(ev: SystemEvent) -> None:
            got1.append(ev)

        def h2(ev: SystemEvent) -> None:
            got2.append(ev)

        ee.subscribe(EventType.OBJECT_CREATED, h1)
        ee.subscribe(EventType.OBJECT_CREATED, h2)
        ee.emit(EventType.OBJECT_CREATED, "test", "sys", "o1", payload={})
        time.sleep(0.2)
        assert len(got1) == 1
        assert len(got2) == 1


class TestEventEngineRetrieval:
    """Event queries."""

    def setup(self) -> EventEngine:
        ee = EventEngine()
        ee.emit(EventType.OBJECT_CREATED, "factory", "sys", "obj1", payload={"n": "A"})
        ee.emit(EventType.OBJECT_MODIFIED, "factory", "u1", "obj1", payload={"f": "x"})
        ee.emit(EventType.OBJECT_DELETED, "factory", "u1", "obj1", payload={})
        return ee

    def test_get_event_by_id(self) -> None:
        ee = self.setup()
        ev = ee.get_events(event_type=EventType.OBJECT_CREATED)[0]
        assert ee.get_event(ev.event_id) is not None

    def test_get_event_unknown(self) -> None:
        ee = EventEngine()
        assert ee.get_event("nope") is None

    def test_get_events(self) -> None:
        ee = self.setup()
        assert len(ee.get_events()) == 3

    def test_get_events_by_type(self) -> None:
        ee = self.setup()
        assert len(ee.get_events(event_type=EventType.OBJECT_CREATED)) == 1

    def test_get_events_by_object(self) -> None:
        ee = self.setup()
        assert len(ee.get_events_by_object("obj1")) == 3

    def test_get_events_by_object_unknown(self) -> None:
        ee = EventEngine()
        assert ee.get_events_by_object("nope") == []

    def test_get_events_by_source(self) -> None:
        ee = self.setup()
        assert len(ee.get_events_by_source("factory")) == 3

    def test_get_events_by_source_unknown(self) -> None:
        ee = EventEngine()
        assert ee.get_events_by_source("nope") == []

    def test_get_events_pagination(self) -> None:
        ee = self.setup()
        assert len(ee.get_events(limit=2)) == 2

    def test_get_events_time_range(self) -> None:
        ee = self.setup()
        events = ee.get_events(from_time="2000Z", to_time="2099Z")
        assert len(events) == 3


class TestEventEngineReplay:
    """Event replay."""

    def test_replay_specific_type(self) -> None:
        ee = EventEngine()
        ee.emit(EventType.OBJECT_CREATED, "test", "sys", "o1", payload={})
        ee.emit(EventType.OBJECT_MODIFIED, "test", "sys", "o1", payload={})
        got: list[SystemEvent] = []

        def handler(ev: SystemEvent) -> None:
            got.append(ev)

        ee.subscribe(EventType.OBJECT_CREATED, handler)
        count = ee.replay(event_type=EventType.OBJECT_CREATED)
        time.sleep(0.2)
        assert count >= 1
        assert len(got) >= 1

    def test_replay_all(self) -> None:
        ee = EventEngine()
        ee.emit(EventType.OBJECT_CREATED, "test", "sys", "o1", payload={})
        got: list[SystemEvent] = []

        def handler(ev: SystemEvent) -> None:
            got.append(ev)

        ee.subscribe("all", handler)
        count = ee.replay()
        time.sleep(0.2)
        assert count >= 1
        assert len(got) >= 1


class TestEventEngineStats:
    """Event statistics."""

    def test_stats_empty(self) -> None:
        ee = EventEngine()
        stats = ee.get_stats()
        assert stats["total_events"] == 0
        assert stats["events_by_type"] == {}
        assert stats["events_by_priority"] == {}

    def test_stats_with_events(self) -> None:
        ee = EventEngine()
        ee.emit(EventType.ERROR, "test", "sys", "o1", payload={})
        ee.emit(EventType.WARNING, "test", "sys", "o2", payload={})
        stats = ee.get_stats()
        assert stats["total_events"] == 2
        assert "error" in stats["events_by_type"]
        assert "warning" in stats["events_by_type"]
        assert "normal" in stats["events_by_priority"]

    def test_stats_active_subscriptions(self) -> None:
        ee = EventEngine()
        ee.subscribe(EventType.ERROR, lambda e: None)
        stats = ee.get_stats()
        assert stats["active_subscriptions"] >= 1


class TestEventEngineClear:
    """Engine reset."""

    def test_clear_removes_events(self) -> None:
        ee = EventEngine()
        ev = ee.emit(EventType.OBJECT_CREATED, "test", "sys", "o1", payload={})
        ee.clear()
        assert len(ee.get_events()) == 0
        assert ee.get_event(ev.event_id) is None

    def test_subscriptions_survive_clear(self) -> None:
        ee = EventEngine()
        ee.subscribe(EventType.ERROR, lambda e: None)
        subs_before = len(ee.get_subscriptions())
        ee.clear()
        subs_after = len(ee.get_subscriptions())
        assert subs_after == subs_before


# ============================================================================
# Integration Tests
# ============================================================================


class TestTimelineEventIntegration:
    """Timeline Engine + Event Engine integration."""

    def test_event_bus_triggers_timeline_record(self) -> None:
        tl = TimelineEngine()
        ee = EventEngine()

        def on_created(ev: SystemEvent) -> None:
            tl.record_event(
                ev.object_id,
                TimelineEventType.from_string(ev.event_type.value.replace(".", "_")),
                ev.actor_id,
                data=ev.payload,
            )

        ee.subscribe(EventType.OBJECT_CREATED, on_created)
        ee.emit(EventType.OBJECT_CREATED, "factory", "sys", "integ_obj", payload={"name": "Integrated"})
        time.sleep(0.2)

        events = tl.get_events("integ_obj")
        assert len(events) >= 1
        assert tl.verify_integrity("integ_obj") is True

    def test_import_paths(self) -> None:
        """Verify the public API import paths work."""
        from core.timeline import TimelineEngine as TE, TimelineEvent as TEV, TimelineEventType as TET
        from core.event import EventEngine as EE, SystemEvent as SE, EventType as ET, EventPriority as EP
        assert TE is TimelineEngine
        assert EE is EventEngine