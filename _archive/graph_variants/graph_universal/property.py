"""
SHUNYA Universal Business Graph — Property Versioning

Properties are immutable. Every update creates a new version.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional


@dataclass(frozen=True)
class PropertyVersion:
    """An immutable property version. Frozen dataclass — cannot be modified."""

    prop_id: str
    entity_id: str
    key: str
    value: Any
    version: int = 1
    source: str = ""
    confidence: float = 1.0
    timestamp: str = ""

    def __post_init__(self):
        if not self.timestamp:
            object.__setattr__(self, "timestamp", datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> dict:
        return {
            "prop_id": self.prop_id,
            "entity_id": self.entity_id,
            "key": self.key,
            "value": self.value,
            "version": self.version,
            "source": self.source,
            "confidence": self.confidence,
            "timestamp": self.timestamp,
        }


class PropertyStore:
    def __init__(self):
        self._versions: dict[str, list[PropertyVersion]] = {}
        self._counter: int = 0

    def set_property(self, entity_id: str, key: str, value: Any,
                     source: str = "", confidence: float = 1.0) -> PropertyVersion:
        """Set a property value. Creates a new immutable version."""
        composite_key = f"{entity_id}:{key}"
        existing = self._versions.get(composite_key, [])
        version_num = len(existing) + 1
        self._counter += 1
        pv = PropertyVersion(
            prop_id=f"pv_{self._counter}",
            entity_id=entity_id,
            key=key,
            value=value,
            version=version_num,
            source=source,
            confidence=confidence,
        )
        if composite_key not in self._versions:
            self._versions[composite_key] = []
        self._versions[composite_key].append(pv)
        return pv

    def get_current(self, entity_id: str, key: str) -> Optional[PropertyVersion]:
        composite_key = f"{entity_id}:{key}"
        versions = self._versions.get(composite_key, [])
        return versions[-1] if versions else None

    def get_history(self, entity_id: str, key: str) -> list[PropertyVersion]:
        composite_key = f"{entity_id}:{key}"
        return self._versions.get(composite_key, [])

    def get_all_for_entity(self, entity_id: str) -> list[PropertyVersion]:
        result = []
        for ck, versions in self._versions.items():
            if ck.startswith(f"{entity_id}:"):
                result.append(versions[-1])
        return result

    @property
    def count(self) -> int:
        return len(self._versions)

    def clear(self) -> None:
        self._versions.clear()
        self._counter = 0


_store: Optional[PropertyStore] = None


def get_store() -> PropertyStore:
    global _store
    if _store is None:
        _store = PropertyStore()
    return _store


def reset_store() -> None:
    global _store
    _store = None