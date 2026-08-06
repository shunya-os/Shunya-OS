"""Universal Memory — continuous, not conversation-bound.

Composes from Knowledge Intelligence (UCP-04) for long-term storage.
Short-term memory is in-process.
"""

from __future__ import annotations
from typing import Any
from core.personal_os.models import MemoryRecord


class MemoryEngine:
    """Continuous memory — short-term, long-term, organizational."""

    def __init__(self) -> None:
        self._owner_id: str = ""
        self._short_term: list[MemoryRecord] = []
        self._long_term: list[MemoryRecord] = []

    def set_owner(self, owner_id: str) -> None:
        self._owner_id = owner_id

    def store(self, content: str, source: str = "", tags: list[str] | None = None,
              memory_type: str = "short_term") -> MemoryRecord:
        rec = MemoryRecord(
            owner_id=self._owner_id, memory_type=memory_type,
            content=content, source=source, tags=tags or [],)
        if memory_type == "short_term":
            self._short_term.append(rec)
            if len(self._short_term) > 100:
                # Promote oldest to long-term
                oldest = self._short_term.pop(0)
                oldest.memory_type = "long_term"
                self._long_term.append(oldest)
        else:
            self._long_term.append(rec)
        return rec

    def recall(self, query: str, limit: int = 10) -> list[MemoryRecord]:
        """Simple text-based recall from both memory stores."""
        q = query.lower()
        results = []
        for rec in self._short_term + self._long_term:
            if q in rec.content.lower() or any(q in t.lower() for t in rec.tags):
                rec.access_count += 1
                results.append(rec)
        # Sort by importance then access count
        results.sort(key=lambda r: (r.importance, r.access_count), reverse=True)
        return results[:limit]

    def count(self) -> int:
        return len(self._short_term) + len(self._long_term)

    def clear(self) -> None:
        self._short_term.clear()
        self._long_term.clear()