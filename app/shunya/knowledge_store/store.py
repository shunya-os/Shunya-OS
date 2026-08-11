"""SHUNYA — Knowledge Store (Phase C).

The authoritative persistent knowledge layer.
Immutable, versioned, business-agnostic foundation for all engines.

Architectural authority: Phase C — Knowledge Store Foundation
"""

from __future__ import annotations

import time
from typing import Any, Dict, List, Optional

from app.shunya.knowledge_store.models import (
    KnowledgeObject,
    KnowledgeObjectStatus,
    SearchQuery,
    SearchResult,
)
from app.shunya.knowledge_store.repository import KnowledgeRepository, InMemoryKnowledgeRepository
from app.shunya.knowledge_store.versioning import VersionHistory, VersionConflictError
from core.knowledge_interface import KnowledgeInterface, KnowledgeCategory, KnowledgeReference


class KnowledgeStore:
    """The authoritative knowledge store.

    Provides:
      - Create / read / update (new version) operations
      - Version management with optimistic concurrency
      - Search with filtering and pagination
      - Archive (soft delete)
      - Event publishing integrated with Event Bus
      - Health and metrics reporting
    """

    def __init__(
        self,
        repository: Optional[KnowledgeRepository] = None,
        version_history: Optional[VersionHistory] = None,
        logger: Any = None,
        metrics_registry: Any = None,
        health_registry: Any = None,
        event_bus: Any = None,
    ) -> None:
        self._repo = repository or InMemoryKnowledgeRepository()
        self._version_history = version_history or VersionHistory()
        self._logger = logger
        self._metrics = metrics_registry
        self._health = health_registry
        self._event_bus = event_bus

        # Track version history alongside repository
        self._version_map: Dict[str, int] = {}

        # Metrics
        if self._metrics:
            self._create_counter = self._metrics.counter("knowledge_objects_created", "Objects created")
            self._read_counter = self._metrics.counter("knowledge_objects_read", "Objects read")
            self._update_counter = self._metrics.counter("knowledge_objects_updated", "Objects updated")
            self._search_counter = self._metrics.counter("knowledge_searches", "Searches performed")
            self._object_gauge = self._metrics.gauge("knowledge_objects_total", "Total objects")
            self._latency_histogram = self._metrics.histogram(
                "knowledge_operation_latency_ms", "Operation latency",
                buckets=[1, 5, 10, 25, 50, 100, 250, 500],
            )

        # Health
        if self._health:
            self._health.register("knowledge_store", self._health_check)

    # ---- Core operations ---------------------------------------------------

    def create(
        self,
        key: str,
        payload: Dict[str, Any],
        namespace: str = "default",
        object_type: str = "fact",
        metadata: Optional[Dict[str, Any]] = None,
        created_by: str = "system",
        description: str = "",
    ) -> KnowledgeObject:
        """Create a new knowledge object (version 1).

        Args:
            key: Unique key within the namespace.
            payload: The knowledge data.
            namespace: Logical grouping (e.g. "travel", "governance").
            object_type: Type classification.
            metadata: Optional metadata.
            created_by: Identifier of the creator.
            description: Human-readable description.

        Returns:
            The created KnowledgeObject (version 1).
        """
        start = time.time()
        obj = KnowledgeObject(
            key=key,
            namespace=namespace,
            type=object_type,
            payload=payload,
            metadata=metadata or {},
            version=1,
            created_by=created_by,
            description=description,
        )
        saved = self._repo.save(obj)
        self._version_history.create_version(
            obj.object_id, 1, 0, saved.to_dict()
        )
        self._version_map[obj.object_id] = 1

        self._emit_created(saved)
        self._record_metrics("create", start)
        return saved

    def get(self, object_id: str, version: Optional[int] = None) -> Optional[KnowledgeObject]:
        """Get a knowledge object by ID.

        Args:
            object_id: The object's unique identifier.
            version: Specific version. None = latest.

        Returns:
            The KnowledgeObject, or None if not found.
        """
        start = time.time()
        obj = self._repo.get(object_id, version)
        self._record_metrics("read", start)
        return obj

    def get_by_key(self, namespace: str, key: str, version: Optional[int] = None) -> Optional[KnowledgeObject]:
        """Get a knowledge object by namespace + key."""
        start = time.time()
        obj = self._repo.get_by_key(namespace, key, version)
        self._record_metrics("read", start)
        return obj

    def update(
        self,
        object_id: str,
        payload: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None,
        expected_version: Optional[int] = None,
        updated_by: str = "system",
    ) -> KnowledgeObject:
        """Update a knowledge object (creates a new version).

        Args:
            object_id: The object to update.
            payload: New payload.
            metadata: Optional metadata update.
            expected_version: Required for optimistic concurrency. If provided,
                              must match the current latest version.
            updated_by: Identifier of the updater.

        Returns:
            The new version of the KnowledgeObject.

        Raises:
            VersionConflictError: If expected_version doesn't match latest.
            ValueError: If object_id doesn't exist.
        """
        start = time.time()
        existing = self._repo.get(object_id)
        if existing is None:
            raise ValueError(f"Knowledge object not found: {object_id}")

        if expected_version is not None and existing.version != expected_version:
            raise VersionConflictError(
                f"Version conflict for {object_id}: "
                f"expected {expected_version}, current {existing.version}"
            )

        new_obj = existing.clone_for_version(existing.version + 1)
        new_obj.payload = payload
        if metadata is not None:
            new_obj.metadata = {**existing.metadata, **metadata}
        new_obj.updated_at = __import__("datetime").datetime.now(
            __import__("datetime").timezone.utc
        )

        saved = self._repo.save(new_obj)
        self._version_history.create_version(
            object_id, new_obj.version, existing.version, saved.to_dict()
        )
        self._version_map[object_id] = new_obj.version

        self._emit_updated(saved)
        self._record_metrics("update", start)
        return saved

    def archive(self, object_id: str) -> bool:
        """Archive (soft-delete) a knowledge object.

        The object's version history remains intact.
        Only the status changes to ARCHIVED.
        """
        start = time.time()
        obj = self._repo.get(object_id)
        if obj is None:
            return False
        result = self._repo.delete(object_id)
        if result:
            obj.status = KnowledgeObjectStatus.ARCHIVED.value
            self._emit_archived(obj)
        self._record_metrics("archive", start)
        return result

    def get_history(self, object_id: str) -> List[KnowledgeObject]:
        """Get all versions of a knowledge object."""
        start = time.time()
        history = self._repo.get_history(object_id)
        self._record_metrics("read", start)
        return history

    def rollback(self, object_id: str, target_version: int) -> Optional[KnowledgeObject]:
        """Rollback to a previous version.

        Creates a new version whose payload is a copy of target_version.
        Previous versions remain intact.
        """
        start = time.time()
        target = self._repo.get(object_id, target_version)
        if target is None:
            return None
        result = self.update(
            object_id,
            payload=dict(target.payload),
            metadata=dict(target.metadata),
            updated_by="system.rollback",
        )
        self._emit_updated(result)
        self._record_metrics("update", start)
        return result

    # ---- Search ------------------------------------------------------------

    def search(self, query: SearchQuery) -> SearchResult:
        """Search knowledge objects with filtering and pagination."""
        start = time.time()
        result = self._repo.search(query)
        self._record_metrics("search", start)
        return result

    def count(
        self, namespace: Optional[str] = None, object_type: Optional[str] = None
    ) -> int:
        """Count objects matching criteria."""
        return self._repo.count(namespace, object_type)

    # ---- Health ------------------------------------------------------------

    def _health_check(self) -> Any:
        from app.shunya.infrastructure.health import HealthCheckResult, HealthStatus

        repo_type = type(self._repo).__name__
        return HealthCheckResult(
            component="knowledge_store",
            status=HealthStatus.HEALTHY,
            detail=f"Repository: {repo_type}",
            metrics={
                "repository": repo_type,
                "objects": self._repo.count(),
                "object_ids": len(self._version_map),
            },
        )

    # ---- Events ------------------------------------------------------------

    def _emit_created(self, obj: KnowledgeObject) -> None:
        if self._event_bus is None:
            return
        from app.shunya.infrastructure.event_bus import CanonicalEvent
        event = CanonicalEvent(
            event_type="knowledge.created",
            object_id=obj.object_id,
            object_type="knowledge_object",
            object_version=obj.version,
            payload={
                "object_id": obj.object_id,
                "key": obj.key,
                "namespace": obj.namespace,
                "type": obj.type,
                "version": obj.version,
            },
        )
        self._event_bus.publish(event)

    def _emit_updated(self, obj: KnowledgeObject) -> None:
        if self._event_bus is None:
            return
        from app.shunya.infrastructure.event_bus import CanonicalEvent
        event = CanonicalEvent(
            event_type="knowledge.updated",
            object_id=obj.object_id,
            object_type="knowledge_object",
            object_version=obj.version,
            payload={
                "object_id": obj.object_id,
                "key": obj.key,
                "namespace": obj.namespace,
                "type": obj.type,
                "version": obj.version,
                "status": obj.status,
            },
        )
        self._event_bus.publish(event)
        # Also emit a version-specific event
        version_event = CanonicalEvent(
            event_type="knowledge.version_created",
            object_id=obj.object_id,
            object_type="knowledge_object",
            object_version=obj.version,
            payload={
                "object_id": obj.object_id,
                "key": obj.key,
                "namespace": obj.namespace,
                "type": obj.type,
                "version": obj.version,
            },
        )
        self._event_bus.publish(version_event)

    def _emit_archived(self, obj: KnowledgeObject) -> None:
        if self._event_bus is None:
            return
        from app.shunya.infrastructure.event_bus import CanonicalEvent
        event = CanonicalEvent(
            event_type="knowledge.archived",
            object_id=obj.object_id,
            object_type="knowledge_object",
            object_version=obj.version,
            payload={
                "object_id": obj.object_id,
                "key": obj.key,
                "namespace": obj.namespace,
                "type": obj.type,
                "version": obj.version,
            },
        )
        self._event_bus.publish(event)

    # ---- Internal ----------------------------------------------------------

    def _record_metrics(self, operation: str, start: float) -> None:
        duration = (time.time() - start) * 1000
        if self._metrics:
            self._latency_histogram.observe(duration)
            if operation == "create":
                self._create_counter.inc()
                self._object_gauge.inc()
            elif operation == "read":
                self._read_counter.inc()
            elif operation == "update":
                self._update_counter.inc()
            elif operation == "search":
                self._search_counter.inc()

    def clear(self) -> None:
        """Clear all state. Useful for testing."""
        if isinstance(self._repo, InMemoryKnowledgeRepository):
            self._repo.clear()
        self._version_history.clear()
        self._version_map.clear()


# ---- Module-level convenience -----------------------------------------------

_store: Optional[KnowledgeStore] = None


def get_knowledge_store(**kwargs: Any) -> KnowledgeStore:
    """Return the application-wide KnowledgeStore (lazily created)."""
    global _store
    if _store is None:
        _store = KnowledgeStore(**kwargs)
    return _store


def reset_knowledge_store() -> None:
    """Reset the global KnowledgeStore. Useful for testing."""
    global _store
    if _store:
        _store.clear()
    _store = None