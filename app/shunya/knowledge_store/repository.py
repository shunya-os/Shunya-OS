"""SHUNYA — Knowledge Store repository (Phase C).

Repository layer with storage interfaces and persistence integration.
Supports in-memory and SQLAlchemy-backed storage backends.
Thread-safe. Atomic writes with transaction support.

Architectural authority: Phase C — Knowledge Store Foundation
"""

from __future__ import annotations

import threading
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Tuple

from app.shunya.knowledge_store.models import KnowledgeObject, SearchQuery, SearchResult


class KnowledgeRepository(ABC):
    """Abstract storage interface for knowledge objects.

    Implementations:
      - InMemoryKnowledgeRepository (testing / dev)
      - SqlKnowledgeRepository (production — Phase C+)
    """

    @abstractmethod
    def save(self, obj: KnowledgeObject) -> KnowledgeObject:
        """Save a knowledge object. Creates or updates (new version)."""

    @abstractmethod
    def get(self, object_id: str, version: Optional[int] = None) -> Optional[KnowledgeObject]:
        """Get a knowledge object by ID. If version is None, returns latest."""

    @abstractmethod
    def get_by_key(self, namespace: str, key: str, version: Optional[int] = None) -> Optional[KnowledgeObject]:
        """Get a knowledge object by namespace + key."""

    @abstractmethod
    def get_history(self, object_id: str) -> List[KnowledgeObject]:
        """Get all versions of a knowledge object."""

    @abstractmethod
    def search(self, query: SearchQuery) -> SearchResult:
        """Search knowledge objects with filtering and pagination."""

    @abstractmethod
    def delete(self, object_id: str) -> bool:
        """Soft-delete (archive) a knowledge object."""

    @abstractmethod
    def count(self, namespace: Optional[str] = None, object_type: Optional[str] = None) -> int:
        """Count objects matching criteria."""


class InMemoryKnowledgeRepository(KnowledgeRepository):
    """In-memory implementation for development and testing.

    Thread-safe. All operations are atomic within the storage lock.
    """

    def __init__(self) -> None:
        self._objects: Dict[str, Dict[int, KnowledgeObject]] = {}
        self._latest: Dict[str, int] = {}
        self._key_index: Dict[Tuple[str, str], str] = {}  # (namespace, key) -> object_id
        self._lock = threading.RLock()

    def save(self, obj: KnowledgeObject) -> KnowledgeObject:
        with self._lock:
            if obj.object_id not in self._objects:
                self._objects[obj.object_id] = {}
            latest = self._latest.get(obj.object_id, 0)
            if obj.version <= latest and latest > 0:
                # Creating a new version
                new_version = latest + 1
                obj = obj.clone_for_version(new_version)
            self._objects[obj.object_id][obj.version] = obj
            self._latest[obj.object_id] = obj.version
            if obj.key:
                self._key_index[(obj.namespace, obj.key)] = obj.object_id
            return obj

    def get(self, object_id: str, version: Optional[int] = None) -> Optional[KnowledgeObject]:
        with self._lock:
            versions = self._objects.get(object_id)
            if not versions:
                return None
            if version is not None:
                return versions.get(version)
            latest = self._latest.get(object_id)
            if latest is None:
                return None
            return versions.get(latest)

    def get_by_key(self, namespace: str, key: str, version: Optional[int] = None) -> Optional[KnowledgeObject]:
        with self._lock:
            object_id = self._key_index.get((namespace, key))
            if object_id is None:
                return None
            return self.get(object_id, version)

    def get_history(self, object_id: str) -> List[KnowledgeObject]:
        with self._lock:
            versions = self._objects.get(object_id, {})
            return [versions[v] for v in sorted(versions.keys())]

    def search(self, query: SearchQuery) -> SearchResult:
        with self._lock:
            all_objects: List[KnowledgeObject] = []
            for versions in self._objects.values():
                latest = max(versions.keys())
                obj = versions[latest]
                if query.matches(obj):
                    all_objects.append(obj)

            # Sort
            all_objects.sort(
                key=lambda o: (
                    getattr(o, query.sort_by, "") or ""
                    if not query.sort_desc
                    else getattr(o, query.sort_by, "") or ""
                ),
                reverse=query.sort_desc,
            )

            total = len(all_objects)
            paginated = all_objects[query.offset:query.offset + query.limit]
            return SearchResult(
                items=paginated,
                total=total,
                limit=query.limit,
                offset=query.offset,
                has_more=(query.offset + query.limit) < total,
            )

    def delete(self, object_id: str) -> bool:
        with self._lock:
            versions = self._objects.get(object_id)
            if not versions:
                return False
            latest = self._latest.get(object_id)
            if latest is None:
                return False
            obj = versions[latest]
            from app.shunya.knowledge_store.models import KnowledgeObjectStatus
            obj.status = KnowledgeObjectStatus.ARCHIVED.value
            return True

    def count(self, namespace: Optional[str] = None, object_type: Optional[str] = None) -> int:
        with self._lock:
            count = 0
            for versions in self._objects.values():
                latest = max(versions.keys())
                obj = versions[latest]
                if namespace and obj.namespace != namespace:
                    continue
                if object_type and obj.type != object_type:
                    continue
                count += 1
            return count

    def clear(self) -> None:
        with self._lock:
            self._objects.clear()
            self._latest.clear()
            self._key_index.clear()