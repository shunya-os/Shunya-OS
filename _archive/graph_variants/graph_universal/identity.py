"""
SHUNYA Universal Business Graph — Identity Resolution

Canonical identity, aliases, merged identities, external references.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional

from app.graph_universal.entity import Entity, get_store as get_entity_store


@dataclass
class IdentityRecord:
    identity_id: str
    canonical_entity_id: str
    aliases: list[str] = field(default_factory=list)
    merged_entity_ids: list[str] = field(default_factory=list)
    external_references: dict = field(default_factory=dict)
    created_at: str = ""

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> dict:
        return {
            "identity_id": self.identity_id,
            "canonical_entity_id": self.canonical_entity_id,
            "aliases": self.aliases,
            "merged_entity_ids": self.merged_entity_ids,
            "external_references": self.external_references,
            "created_at": self.created_at,
        }


class IdentityResolver:
    """Universal identity resolution. Canonical identity + aliases + merge."""

    def __init__(self):
        self._records: dict[str, IdentityRecord] = {}

    def register(self, entity: Entity) -> IdentityRecord:
        record = IdentityRecord(
            identity_id=f"id_{entity.entity_id}",
            canonical_entity_id=entity.entity_id,
            aliases=entity.aliases.copy(),
        )
        self._records[record.identity_id] = record
        return record

    def resolve(self, identifier: str) -> Optional[Entity]:
        """Resolve any identifier (ID, alias, name) to a canonical entity."""
        es = get_entity_store()
        # Try direct ID
        e = es.get(identifier)
        if e:
            return e
        # Try alias lookup
        for record in self._records.values():
            if identifier in record.aliases:
                return es.get(record.canonical_entity_id)
            # Check merged entities
            for merged_id in record.merged_entity_ids:
                if identifier == merged_id:
                    return es.get(record.canonical_entity_id)
        return None

    def merge(self, primary_id: str, secondary_id: str) -> Optional[IdentityRecord]:
        """Merge a secondary identity into a primary one."""
        primary = None
        secondary = None
        for record in self._records.values():
            if record.canonical_entity_id == primary_id:
                primary = record
            if record.canonical_entity_id == secondary_id:
                secondary = record

        if not primary or not secondary:
            return None

        primary.merged_entity_ids.append(secondary_id)
        primary.aliases.extend(a for a in secondary.aliases if a not in primary.aliases)
        return primary

    def get(self, identity_id: str) -> Optional[IdentityRecord]:
        return self._records.get(identity_id)

    @property
    def count(self) -> int:
        return len(self._records)

    def clear(self) -> None:
        self._records.clear()


_resolver: Optional[IdentityResolver] = None


def get_resolver() -> IdentityResolver:
    global _resolver
    if _resolver is None:
        _resolver = IdentityResolver()
    return _resolver


def reset_resolver() -> None:
    global _resolver
    _resolver = None