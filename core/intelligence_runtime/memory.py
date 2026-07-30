"""Memory Engine — short-term, long-term, organization, and business memory."""

from __future__ import annotations

from typing import Any

from .types import MemoryEntry, MemoryType


class MemoryEngine:
    """Multi-tier memory system."""

    def __init__(self):
        self._stores: dict[MemoryType, dict[str, MemoryEntry]] = {
            MemoryType.SHORT_TERM: {},
            MemoryType.LONG_TERM: {},
            MemoryType.ORGANIZATION: {},
            MemoryType.BUSINESS: {},
        }

    def store(self, key: str, content: str, memory_type: MemoryType = MemoryType.SHORT_TERM,
              source: str = "", confidence: float = 1.0, ttl_seconds: int = 0) -> None:
        entry = MemoryEntry(key=key, content=content, memory_type=memory_type,
                            source=source, confidence=confidence, ttl_seconds=ttl_seconds)
        self._stores[memory_type][key] = entry

    def get(self, key: str, memory_type: MemoryType | None = None) -> MemoryEntry | None:
        """Get a memory entry. Checks all stores if type not specified."""
        if memory_type:
            entry = self._stores[memory_type].get(key)
            if entry and not entry.is_expired():
                return entry
            return None
        for store_type in MemoryType:
            entry = self._stores[store_type].get(key)
            if entry and not entry.is_expired():
                return entry
        return None

    def search(self, query: str, memory_type: MemoryType | None = None) -> list[MemoryEntry]:
        """Search memory by query string."""
        q = query.lower()
        results = []
        stores = [memory_type] if memory_type else list(MemoryType)
        for mt in stores:
            for entry in self._stores[mt].values():
                if entry.is_expired():
                    continue
                if q in entry.content.lower() or q in entry.key.lower():
                    results.append(entry)
        results.sort(key=lambda e: -e.confidence)
        return results[:10]

    def recall_recent(self, memory_type: MemoryType = MemoryType.SHORT_TERM, limit: int = 10) -> list[MemoryEntry]:
        """Get recent entries from a memory store."""
        entries = [e for e in self._stores[memory_type].values() if not e.is_expired()]
        entries.sort(key=lambda e: e.timestamp, reverse=True)
        return entries[:limit]

    def forget(self, key: str, memory_type: MemoryType | None = None) -> bool:
        """Remove a memory entry."""
        if memory_type:
            if key in self._stores[memory_type]:
                del self._stores[memory_type][key]
                return True
            return False
        for mt in MemoryType:
            if key in self._stores[mt]:
                del self._stores[mt][key]
                return True
        return False

    def clear(self, memory_type: MemoryType | None = None) -> None:
        if memory_type:
            self._stores[memory_type].clear()
        else:
            for mt in MemoryType:
                self._stores[mt].clear()

    def count(self, memory_type: MemoryType | None = None) -> int:
        if memory_type:
            return len(self._stores[memory_type])
        return sum(len(s) for s in self._stores.values())