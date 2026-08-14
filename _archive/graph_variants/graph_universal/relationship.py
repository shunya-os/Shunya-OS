"""
SHUNYA Universal Business Graph — Relationship Engine

Relationships connect entities. Support many-to-many relationships.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional


@dataclass
class Relationship:
    rel_id: str
    source_id: str
    target_id: str
    rel_type: str
    confidence: float = 1.0
    created_by: str = ""
    status: str = "active"
    created_at: str = ""
    metadata: dict = field(default_factory=dict)

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> dict:
        return {
            "rel_id": self.rel_id,
            "source_id": self.source_id,
            "target_id": self.target_id,
            "rel_type": self.rel_type,
            "confidence": self.confidence,
            "created_by": self.created_by,
            "status": self.status,
            "created_at": self.created_at,
        }


class RelationshipStore:
    def __init__(self):
        self._rels: dict[str, Relationship] = {}

    def add(self, rel: Relationship) -> None:
        self._rels[rel.rel_id] = rel

    def get(self, rel_id: str) -> Optional[Relationship]:
        return self._rels.get(rel_id)

    def get_for_entity(self, entity_id: str) -> list[Relationship]:
        return [r for r in self._rels.values()
                if r.source_id == entity_id or r.target_id == entity_id]

    def get_neighbors(self, entity_id: str) -> list[str]:
        neighbor_ids = set()
        for r in self._rels.values():
            if r.source_id == entity_id:
                neighbor_ids.add(r.target_id)
            if r.target_id == entity_id:
                neighbor_ids.add(r.source_id)
        return list(neighbor_ids)

    @property
    def count(self) -> int:
        return len(self._rels)

    def clear(self) -> None:
        self._rels.clear()


_store: Optional[RelationshipStore] = None


def get_store() -> RelationshipStore:
    global _store
    if _store is None:
        _store = RelationshipStore()
    return _store


def reset_store() -> None:
    global _store
    _store = None