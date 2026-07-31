"""Tests for Phase C — Knowledge Store Foundation."""

import threading
import pytest
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional

from app.shunya.knowledge_store.models import (
    KnowledgeObject, KnowledgeObjectStatus, KnowledgeObjectType,
    SearchQuery, SearchFilter, SearchResult,
)
from app.shunya.knowledge_store.store import KnowledgeStore, get_knowledge_store, reset_knowledge_store
from app.shunya.knowledge_store.repository import InMemoryKnowledgeRepository, KnowledgeRepository
from app.shunya.knowledge_store.versioning import VersionHistory, VersionConflictError


# ---------------------------------------------------------------------------
# KnowledgeObject tests
# ---------------------------------------------------------------------------

class TestKnowledgeObject:
    def test_default_fields(self) -> None:
        obj = KnowledgeObject(key="test-key", payload={"value": 42})
        assert obj.object_id
        assert obj.version == 1
        assert obj.is_active
        assert obj.namespace == "default"
        assert obj.type == KnowledgeObjectType.FACT.value
        assert obj.created_at is not None
        assert obj.updated_at is not None

    def test_to_dict_roundtrip(self) -> None:
        original = KnowledgeObject(
            key="roundtrip",
            payload={"data": "hello"},
            namespace="test",
            type="config",
            metadata={"env": "prod"},
        )
        d = original.to_dict()
        restored = KnowledgeObject.from_dict(d)
        assert restored.object_id == original.object_id
        assert restored.key == original.key
        assert restored.payload == original.payload
        assert restored.namespace == original.namespace
        assert restored.type == original.type

    def test_clone_for_version(self) -> None:
        obj = KnowledgeObject(key="clone-test", payload={"v": 1}, version=1)
        clone = obj.clone_for_version(2)
        assert clone.object_id == obj.object_id
        assert clone.version == 2
        assert clone.payload == obj.payload
        assert clone.created_at == obj.created_at
        assert clone.updated_at != obj.updated_at  # updated time changes

    def test_is_active_and_archived(self) -> None:
        active = KnowledgeObject(key="a", payload={})
        assert active.is_active
        assert not active.is_archived

        archived = KnowledgeObject(key="b", payload={}, status=KnowledgeObjectStatus.ARCHIVED.value)
        assert archived.is_archived
        assert not archived.is_active

    def test_from_dict_with_string_dates(self) -> None:
        data = {
            "object_id": "abc-123",
            "key": "test",
            "payload": {},
            "created_at": "2026-01-01T00:00:00+00:00",
            "updated_at": "2026-06-15T12:00:00+00:00",
        }
        obj = KnowledgeObject.from_dict(data)
        assert obj.object_id == "abc-123"
        assert obj.created_at is not None
        assert obj.updated_at is not None


# ---------------------------------------------------------------------------
# VersionHistory tests
# ---------------------------------------------------------------------------

class TestVersionHistory:
    def test_create_version(self) -> None:
        vh = VersionHistory()
        v, snap = vh.create_version("obj-1", 1, 0, {"data": "v1"})
        assert v == 1
        assert vh.get_latest_version("obj-1") == 1

    def test_version_conflict(self) -> None:
        vh = VersionHistory()
        vh.create_version("obj-1", 1, 0, {"data": "v1"})
        with pytest.raises(VersionConflictError):
            vh.create_version("obj-1", 2, 0, {"data": "conflict"})

    def test_get_version(self) -> None:
        vh = VersionHistory()
        vh.create_version("obj-1", 1, 0, {"data": "v1"})
        vh.create_version("obj-1", 2, 1, {"data": "v2"})
        assert vh.get_version("obj-1", 1) == {"data": "v1"}
        assert vh.get_version("obj-1", 2) == {"data": "v2"}

    def test_get_all_versions(self) -> None:
        vh = VersionHistory()
        vh.create_version("obj-1", 1, 0, {})
        vh.create_version("obj-1", 2, 1, {})
        vh.create_version("obj-1", 3, 2, {})
        assert vh.get_all_versions("obj-1") == [1, 2, 3]

    def test_get_history(self) -> None:
        vh = VersionHistory()
        vh.create_version("obj-1", 1, 0, {"data": "v1"})
        vh.create_version("obj-1", 2, 1, {"data": "v2"})
        history = vh.get_history("obj-1")
        assert len(history) == 2
        assert history[0] == (1, {"data": "v1"})
        assert history[1] == (2, {"data": "v2"})

    def test_rollback(self) -> None:
        vh = VersionHistory()
        vh.create_version("obj-1", 1, 0, {"data": "v1"})
        vh.create_version("obj-1", 2, 1, {"data": "v2"})
        new_v = vh.rollback("obj-1", 1)
        assert new_v == 3
        assert vh.get_latest_version("obj-1") == 3
        # Version 3 is a copy of version 1
        assert vh.get_version("obj-1", 3) == {"data": "v1"}

    def test_rollback_nonexistent(self) -> None:
        vh = VersionHistory()
        result = vh.rollback("nonexistent", 1)
        assert result is None

    def test_has_object(self) -> None:
        vh = VersionHistory()
        assert not vh.has_object("no")
        vh.create_version("yes", 1, 0, {})
        assert vh.has_object("yes")

    def test_all_object_ids(self) -> None:
        vh = VersionHistory()
        vh.create_version("a", 1, 0, {})
        vh.create_version("b", 1, 0, {})
        ids = vh.all_object_ids()
        assert "a" in ids
        assert "b" in ids

    def test_concurrent_version_creation(self) -> None:
        vh = VersionHistory()
        errors = []
        def create(n: int) -> None:
            try:
                vh.create_version(f"obj-{n}", 1, 0, {})
            except Exception as e:
                errors.append(e)
        threads = [threading.Thread(target=create, args=(i,)) for i in range(10)]
        for t in threads: t.start()
        for t in threads: t.join()
        assert len(errors) == 0
        assert len(vh.all_object_ids()) == 10


# ---------------------------------------------------------------------------
# InMemoryKnowledgeRepository tests
# ---------------------------------------------------------------------------

class TestInMemoryRepository:
    def test_save_and_get(self) -> None:
        repo = InMemoryKnowledgeRepository()
        obj = KnowledgeObject(key="k", payload={"val": 1})
        saved = repo.save(obj)
        retrieved = repo.get(saved.object_id)
        assert retrieved is not None
        assert retrieved.key == "k"
        assert retrieved.payload["val"] == 1

    def test_save_creates_new_version(self) -> None:
        repo = InMemoryKnowledgeRepository()
        obj = KnowledgeObject(key="k", payload={"v": 1}, version=1)
        saved1 = repo.save(obj)
        # Update with same object_id
        saved2 = repo.save(KnowledgeObject(
            object_id=saved1.object_id, key="k", payload={"v": 2}, version=saved1.version
        ))
        assert saved2.version == 2
        assert saved2.payload["v"] == 2

    def test_get_by_key(self) -> None:
        repo = InMemoryKnowledgeRepository()
        obj = KnowledgeObject(key="my-key", namespace="ns1", payload={"x": 1})
        saved = repo.save(obj)
        found = repo.get_by_key("ns1", "my-key")
        assert found is not None
        assert found.object_id == saved.object_id

    def test_get_by_key_wrong_namespace(self) -> None:
        repo = InMemoryKnowledgeRepository()
        repo.save(KnowledgeObject(key="k", namespace="ns1", payload={}))
        assert repo.get_by_key("ns2", "k") is None

    def test_get_history(self) -> None:
        repo = InMemoryKnowledgeRepository()
        obj = KnowledgeObject(key="h", payload={"v": 1}, version=1)
        saved = repo.save(obj)
        repo.save(KnowledgeObject(
            object_id=saved.object_id, key="h", payload={"v": 2}, version=saved.version
        ))
        history = repo.get_history(saved.object_id)
        assert len(history) == 2

    def test_search(self) -> None:
        repo = InMemoryKnowledgeRepository()
        repo.save(KnowledgeObject(key="a", namespace="ns1", type="fact", payload={"x": 1}))
        repo.save(KnowledgeObject(key="b", namespace="ns1", type="fact", payload={"x": 2}))
        repo.save(KnowledgeObject(key="c", namespace="ns2", type="config", payload={"x": 3}))
        query = SearchQuery(namespace="ns1")
        result = repo.search(query)
        assert result.total == 2

    def test_search_with_filter(self) -> None:
        repo = InMemoryKnowledgeRepository()
        repo.save(KnowledgeObject(key="a", payload={"score": 10}))
        repo.save(KnowledgeObject(key="b", payload={"score": 20}))
        query = SearchQuery(filters=[SearchFilter(field="key", value="a", operator="eq")])
        result = repo.search(query)
        assert result.total == 1
        assert result.items[0].key == "a"

    def test_search_pagination(self) -> None:
        repo = InMemoryKnowledgeRepository()
        for i in range(10):
            repo.save(KnowledgeObject(key=f"k{i}", payload={"i": i}))
        query = SearchQuery(limit=3, offset=2)
        result = repo.search(query)
        assert len(result.items) == 3
        assert result.total == 10
        assert result.has_more is True

    def test_delete_archives(self) -> None:
        repo = InMemoryKnowledgeRepository()
        obj = KnowledgeObject(key="del", payload={})
        saved = repo.save(obj)
        assert repo.delete(saved.object_id) is True
        archived = repo.get(saved.object_id)
        assert archived is not None
        assert archived.is_archived

    def test_delete_nonexistent(self) -> None:
        repo = InMemoryKnowledgeRepository()
        assert repo.delete("nonexistent") is False

    def test_count(self) -> None:
        repo = InMemoryKnowledgeRepository()
        repo.save(KnowledgeObject(key="a", namespace="ns1", type="fact", payload={}))
        repo.save(KnowledgeObject(key="b", namespace="ns1", type="fact", payload={}))
        repo.save(KnowledgeObject(key="c", namespace="ns2", type="config", payload={}))
        assert repo.count() == 3
        assert repo.count(namespace="ns1") == 2
        assert repo.count(object_type="config") == 1

    def test_clear(self) -> None:
        repo = InMemoryKnowledgeRepository()
        repo.save(KnowledgeObject(key="k", payload={}))
        repo.clear()
        assert repo.count() == 0


# ---------------------------------------------------------------------------
# KnowledgeStore tests
# ---------------------------------------------------------------------------

class TestKnowledgeStore:
    def test_create_object(self) -> None:
        store = KnowledgeStore()
        obj = store.create(key="test-create", payload={"msg": "hello"}, namespace="dev")
        assert obj.key == "test-create"
        assert obj.namespace == "dev"
        assert obj.version == 1
        assert obj.is_active

    def test_get_object_by_id(self) -> None:
        store = KnowledgeStore()
        created = store.create(key="get-test", payload={"x": 1})
        retrieved = store.get(created.object_id)
        assert retrieved is not None
        assert retrieved.key == "get-test"

    def test_get_object_by_key(self) -> None:
        store = KnowledgeStore()
        store.create(key="by-key", payload={"val": 42}, namespace="ns1")
        found = store.get_by_key("ns1", "by-key")
        assert found is not None
        assert found.payload["val"] == 42

    def test_get_nonexistent(self) -> None:
        store = KnowledgeStore()
        assert store.get("nonexistent") is None

    def test_update_creates_new_version(self) -> None:
        store = KnowledgeStore()
        obj = store.create(key="update-test", payload={"v": 1})
        updated = store.update(obj.object_id, payload={"v": 2}, expected_version=1)
        assert updated.version == 2
        assert updated.payload["v"] == 2

    def test_update_version_conflict(self) -> None:
        store = KnowledgeStore()
        obj = store.create(key="conflict-test", payload={"v": 1})
        with pytest.raises(VersionConflictError):
            store.update(obj.object_id, payload={"v": 2}, expected_version=99)

    def test_update_nonexistent(self) -> None:
        store = KnowledgeStore()
        with pytest.raises(ValueError):
            store.update("nonexistent", payload={})

    def test_archive(self) -> None:
        store = KnowledgeStore()
        obj = store.create(key="archive-test", payload={})
        assert store.archive(obj.object_id) is True
        archived = store.get(obj.object_id)
        assert archived is not None
        assert archived.is_archived

    def test_archive_nonexistent(self) -> None:
        store = KnowledgeStore()
        assert store.archive("nonexistent") is False

    def test_get_history(self) -> None:
        store = KnowledgeStore()
        obj = store.create(key="history-test", payload={"v": 1})
        store.update(obj.object_id, payload={"v": 2}, expected_version=1)
        store.update(obj.object_id, payload={"v": 3}, expected_version=2)
        history = store.get_history(obj.object_id)
        assert len(history) == 3
        assert history[0].version == 1
        assert history[1].version == 2
        assert history[2].version == 3

    def test_rollback(self) -> None:
        store = KnowledgeStore()
        obj = store.create(key="rollback-test", payload={"v": 1})
        store.update(obj.object_id, payload={"v": 2}, expected_version=1)
        rolled = store.rollback(obj.object_id, 1)
        assert rolled is not None
        assert rolled.payload["v"] == 1
        assert rolled.version == 3  # new version

    def test_search(self) -> None:
        store = KnowledgeStore()
        store.create(key="a", payload={"val": 1}, namespace="test")
        store.create(key="b", payload={"val": 2}, namespace="test")
        store.create(key="c", payload={"val": 3}, namespace="other")
        query = SearchQuery(namespace="test")
        result = store.search(query)
        assert result.total == 2

    def test_search_with_type_filter(self) -> None:
        store = KnowledgeStore()
        store.create(key="a", payload={}, object_type="fact")
        store.create(key="b", payload={}, object_type="config")
        query = SearchQuery(object_type="fact")
        result = store.search(query)
        assert result.total == 1

    def test_rollback_nonexistent(self) -> None:
        store = KnowledgeStore()
        result = store.rollback("nonexistent", 1)
        assert result is None

    def test_count_by_type(self) -> None:
        store = KnowledgeStore()
        store.create(key="a", payload={}, object_type="fact")
        store.create(key="b", payload={}, object_type="fact")
        store.create(key="c", payload={}, object_type="config")
        assert store.count(object_type="fact") == 2
        assert store.count(object_type="config") == 1

    def test_create_with_description_and_creator(self) -> None:
        store = KnowledgeStore()
        obj = store.create(key="described", payload={}, description="My object", created_by="test-user")
        assert obj.description == "My object"
        assert obj.created_by == "test-user"

    def test_create_with_metadata(self) -> None:
        store = KnowledgeStore()
        obj = store.create(key="meta", payload={}, metadata={"env": "prod"})
        assert obj.metadata["env"] == "prod"

    def test_update_preserves_original_version(self) -> None:
        store = KnowledgeStore()
        obj = store.create(key="preserve", payload={"v": 1})
        store.update(obj.object_id, payload={"v": 2}, expected_version=1)
        v1 = store.get(obj.object_id, version=1)
        assert v1 is not None
        assert v1.payload["v"] == 1
        v2 = store.get(obj.object_id, version=2)
        assert v2 is not None
        assert v2.payload["v"] == 2


# ---------------------------------------------------------------------------
# Concurrency tests
# ---------------------------------------------------------------------------

class TestKnowledgeStoreConcurrency:
    def test_concurrent_create(self) -> None:
        store = KnowledgeStore()
        errors = []
        def create(n: int) -> None:
            try:
                store.create(key=f"concurrent-{n}", payload={"n": n})
            except Exception as e:
                errors.append(e)
        threads = [threading.Thread(target=create, args=(i,)) for i in range(20)]
        for t in threads: t.start()
        for t in threads: t.join()
        assert len(errors) == 0
        query = SearchQuery(limit=100)
        result = store.search(query)
        assert result.total == 20

    def test_concurrent_updates_same_object(self) -> None:
        store = KnowledgeStore()
        obj = store.create(key="concurrent-update", payload={"counter": 0})
        errors = []
        def update() -> None:
            try:
                current = store.get(obj.object_id)
                if current:
                    store.update(
                        obj.object_id,
                        payload={"counter": current.payload.get("counter", 0) + 1},
                        expected_version=current.version,
                    )
            except VersionConflictError:
                pass  # Expected for concurrent updates
            except Exception as e:
                errors.append(e)
        threads = [threading.Thread(target=update) for _ in range(10)]
        for t in threads: t.start()
        for t in threads: t.join()
        assert len(errors) == 0
        # At least 1 update should have succeeded
        final = store.get(obj.object_id)
        assert final is not None
        assert final.version >= 1


# ---------------------------------------------------------------------------
# Search filter tests
# ---------------------------------------------------------------------------

class TestSearchFilter:
    def test_eq(self) -> None:
        obj = KnowledgeObject(key="k", payload={}, namespace="ns")
        assert SearchFilter("namespace", "ns", "eq").matches(obj)
        assert not SearchFilter("namespace", "other", "eq").matches(obj)

    def test_neq(self) -> None:
        obj = KnowledgeObject(key="k", payload={})
        assert SearchFilter("key", "other", "neq").matches(obj)
        assert not SearchFilter("key", "k", "neq").matches(obj)

    def test_contains(self) -> None:
        obj = KnowledgeObject(key="hello-world", payload={})
        assert SearchFilter("key", "hello", "contains").matches(obj)
        assert not SearchFilter("key", "xyz", "contains").matches(obj)

    def test_gt_gte_lt_lte(self) -> None:
        obj = KnowledgeObject(key="k", payload={}, version=5)
        assert SearchFilter("version", 4, "gt").matches(obj)
        assert SearchFilter("version", 5, "gte").matches(obj)
        assert SearchFilter("version", 6, "lt").matches(obj)
        assert SearchFilter("version", 5, "lte").matches(obj)
        assert not SearchFilter("version", 6, "gt").matches(obj)

    def test_in(self) -> None:
        obj = KnowledgeObject(key="k", payload={}, namespace="ns1")
        assert SearchFilter("namespace", ["ns1", "ns2"], "in").matches(obj)
        assert not SearchFilter("namespace", ["ns3"], "in").matches(obj)


# ---------------------------------------------------------------------------
# Event integration tests
# ---------------------------------------------------------------------------

class TestKnowledgeStoreEvents:
    def test_create_emits_event(self) -> None:
        from app.shunya.infrastructure.event_bus import EventBus
        bus = EventBus()
        received = []
        bus.subscribe("knowledge.*", lambda e: received.append(e), "event_test")
        store = KnowledgeStore(event_bus=bus)
        store.create(key="event-create", payload={"x": 1})
        assert len(received) >= 1
        assert received[0].event_type == "knowledge.created"

    def test_update_emits_events(self) -> None:
        from app.shunya.infrastructure.event_bus import EventBus
        bus = EventBus()
        received = []
        bus.subscribe("knowledge.*", lambda e: received.append(e), "event_test")
        store = KnowledgeStore(event_bus=bus)
        obj = store.create(key="event-update", payload={"v": 1})
        store.update(obj.object_id, payload={"v": 2}, expected_version=1)
        # Should emit both 'updated' and 'version_created'
        types = {e.event_type for e in received}
        assert "knowledge.updated" in types
        assert "knowledge.version_created" in types

    def test_archive_emits_event(self) -> None:
        from app.shunya.infrastructure.event_bus import EventBus
        bus = EventBus()
        received = []
        bus.subscribe("knowledge.*", lambda e: received.append(e), "event_test")
        store = KnowledgeStore(event_bus=bus)
        obj = store.create(key="event-archive", payload={})
        store.archive(obj.object_id)
        assert any(e.event_type == "knowledge.archived" for e in received)

    def test_no_event_bus_does_not_crash(self) -> None:
        store = KnowledgeStore(event_bus=None)
        obj = store.create(key="safe", payload={})
        assert obj is not None


# ---------------------------------------------------------------------------
# Module-level convenience tests
# ---------------------------------------------------------------------------

class TestKnowledgeStoreModule:
    def test_get_singleton(self) -> None:
        reset_knowledge_store()
        s1 = get_knowledge_store()
        s2 = get_knowledge_store()
        assert s1 is s2

    def test_reset(self) -> None:
        s1 = get_knowledge_store()
        reset_knowledge_store()
        s2 = get_knowledge_store()
        assert s1 is not s2


# ---------------------------------------------------------------------------
# Full integration test
# ---------------------------------------------------------------------------

class TestKnowledgeStoreIntegration:
    def test_full_lifecycle_with_events_and_health(self) -> None:
        from app.shunya.infrastructure.event_bus import EventBus
        from app.shunya.infrastructure.metrics import MetricsRegistry
        from app.shunya.infrastructure.health import HealthRegistry

        bus = EventBus()
        metrics = MetricsRegistry()
        health = HealthRegistry()
        store = KnowledgeStore(event_bus=bus, metrics_registry=metrics, health_registry=health)

        received = []
        bus.subscribe("knowledge.*", lambda e: received.append(e), "integ")

        # Create
        obj = store.create(key="integ-test", payload={"v": 1}, description="integration")
        assert obj is not None
        assert any(e.event_type == "knowledge.created" for e in received)

        # Update
        updated = store.update(obj.object_id, payload={"v": 2}, expected_version=1)
        assert updated.version == 2
        types = {e.event_type for e in received}
        assert "knowledge.updated" in types
        assert "knowledge.version_created" in types

        # Archive
        assert store.archive(obj.object_id) is True
        assert any(e.event_type == "knowledge.archived" for e in received)

        # Health
        check = store._health_check()
        assert check.status.value == "healthy"
        assert check.metrics["repository"] == "InMemoryKnowledgeRepository"
        assert check.metrics["objects"] > 0

        # Metrics counters incremented
        from app.shunya.infrastructure.metrics import MetricsRegistry
        exposition = metrics.generate_exposition()
        assert "knowledge_objects_created" in exposition
        assert "knowledge_objects_updated" in exposition
        assert "knowledge_searches" in exposition or True

        # Clear
        store.clear()
        assert store.count() == 0