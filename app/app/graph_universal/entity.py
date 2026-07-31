"""
SHUNYA Universal Business Graph — Entity Model

Everything meaningful inside an organization is an Entity.
Entity types are extensible. Never hardcode business domains.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional


@dataclass
class Entity:
    entity_id: str
    name: str
    entity_type: str
    """Extensible type string. Never hardcode business domains."""
    aliases: list[str] = field(default_factory=list)
    status: str = "active"
    canonical_id: str = ""
    created_at: str = ""
    updated_at: str = ""
    metadata: dict = field(default_factory=dict)

    def __post_init__(self):
        now = datetime.now(timezone.utc).isoformat()
        if not self.created_at:
            self.created_at = now
        if not self.updated_at:
            self.updated_at = now
        if not self.canonical_id:
            self.canonical_id = self.entity_id

    def to_dict(self) -> dict:
        return {
            "entity_id": self.entity_id,
            "name": self.name,
            "entity_type": self.entity_type,
            "aliases": self.aliases,
            "status": self.status,
            "canonical_id": self.canonical_id,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


class EntityStore:
    def __init__(self):
        self._entities: dict[str, Entity] = {}

    def add(self, entity: Entity) -> None:
        self._entities[entity.entity_id] = entity

    def get(self, entity_id: str) -> Optional[Entity]:
        return self._entities.get(entity_id)

    def get_by_type(self, entity_type: str) -> list[Entity]:
        return [e for e in self._entities.values() if e.entity_type == entity_type]

    def find_by_alias(self, alias: str) -> Optional[Entity]:
        for e in self._entities.values():
            if alias in e.aliases or alias == e.name:
                return e
        return None

    @property
    def count(self) -> int:
        return len(self._entities)

    def clear(self) -> None:
        self._entities.clear()


_store: Optional[EntityStore] = None


def get_store() -> EntityStore:
    global _store
    if _store is None:
        _store = EntityStore()
    return _store


def reset_store() -> None:
    global _store
    _store = None