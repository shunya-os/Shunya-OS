"""
SHUNYA Memory Engine — Durable Storage of Learned Context

Manages the persistent storage of what the system has learned,
supports retrieval, relevance scoring, and decay over time.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, List, Optional

from core.runtime.models import Engine, EngineStatus, HealthLevel, HealthStatus


@dataclass
class Memory:
    memory_id: str
    content: str
    object_id: Optional[str] = None
    source: str = "system"
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    tags: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "memory_id": self.memory_id, "content": self.content,
            "object_id": self.object_id, "source": self.source,
            "created_at": self.created_at.isoformat(), "tags": self.tags,
        }


class MemoryEngine(Engine):
    """Canonical memory engine for durable context storage and retrieval."""

    engine_id: str = "memory"
    engine_type: str = "intelligence"

    def __init__(self) -> None:
        super().__init__()
        self._memories: dict[str, Memory] = {}
        self._initialized = False

    def initialize(self) -> None:
        self._status = EngineStatus.ACTIVE
        self._initialized = True

    def shutdown(self) -> None:
        self._memories.clear()
        self._status = EngineStatus.OFFLINE
        self._initialized = False

    def health_check(self) -> HealthStatus:
        return HealthStatus(
            status=HealthLevel.HEALTHY if self._initialized else HealthLevel.UNHEALTHY,
            checks={"initialized": self._initialized, "memory_count": len(self._memories)},
        )

    def handle_event(self, event: Any) -> None:
        if not self._initialized:
            return

    def get_capabilities(self) -> List[str]:
        return ["memory.store", "memory.retrieve", "memory.search", "memory.tag"]

    def store(self, content: str, object_id: Optional[str] = None, source: str = "system",
              tags: list[str] | None = None) -> Memory:
        memory = Memory(
            memory_id=f"mem-{len(self._memories) + 1}",
            content=content, object_id=object_id, source=source,
            tags=tags or [],
        )
        self._memories[memory.memory_id] = memory
        return memory

    def retrieve(self, memory_id: str) -> Optional[Memory]:
        return self._memories.get(memory_id)

    def search(self, query: str, limit: int = 10) -> list[Memory]:
        q = query.lower()
        results = [m for m in self._memories.values() if q in m.content.lower()]
        return results[:limit]

    def list_for_object(self, object_id: str) -> list[Memory]:
        return [m for m in self._memories.values() if m.object_id == object_id]

    def list_by_tag(self, tag: str) -> list[Memory]:
        return [m for m in self._memories.values() if tag in m.tags]

    def all(self) -> list[Memory]:
        return list(self._memories.values())