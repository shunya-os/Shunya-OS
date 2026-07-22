"""SHUNYA Kernel — Universal Object Contract.

Every meaningful entity in SHUNYA inherits from UniversalObject.
This enforces the canonical field contract defined in SHUNYA Core Models §2.

No entity may bypass this contract without explicit architectural approval.
"""

from __future__ import annotations

import uuid
import hashlib
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Type, TypeVar


# ---------------------------------------------------------------------------
# Object lifecycle states
# ---------------------------------------------------------------------------

class ObjectStatus(str, Enum):
    ACTIVE = "active"
    SUPERSEDED = "superseded"
    ARCHIVED = "archived"
    PENDING = "pending"
    DELETED = "deleted"


# ---------------------------------------------------------------------------
# UUID v7 — time-ordered UUID for sortability
# ---------------------------------------------------------------------------

def _uuid7() -> str:
    """Generate a time-ordered UUID (roughly UUID v7 semantics).

    Returns a 32-char hex string with a timestamp prefix for natural sorting.
    """
    timestamp = int(datetime.now(timezone.utc).timestamp() * 1000)
    rand = uuid.uuid4().hex[:16]
    return f"{timestamp:016x}{rand}"


# ---------------------------------------------------------------------------
# Evidence
# ---------------------------------------------------------------------------

@dataclass
class EvidenceRef:
    """A reference to evidence supporting an object's state."""
    object_id: str
    object_type: str
    field: str = ""
    confidence: float = 1.0
    captured_at: str = ""

    def __post_init__(self):
        if not self.captured_at:
            self.captured_at = datetime.now(timezone.utc).isoformat()


# ---------------------------------------------------------------------------
# Relationship stub (linked object)
# ---------------------------------------------------------------------------

@dataclass
class RelationshipRef:
    """A typed link to another UniversalObject."""
    object_id: str
    object_type: str
    relationship_type: str = "related_to"
    label: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Universal Object — the base contract
# ---------------------------------------------------------------------------

T = TypeVar("T", bound="UniversalObject")


@dataclass
class UniversalObject:
    """Canonical base for every entity in SHUNYA.

    Core Models §2 — UniversalObject mandatory fields.
    Every entity type inherits from this and adds domain-specific fields.
    """

    object_id: str = ""
    tenant_id: int = 0
    space_id: str = ""
    object_type: str = ""
    name: str = ""
    status: str = ObjectStatus.ACTIVE.value
    version: int = 1
    confidence: float = 1.0
    created_at: str = ""
    updated_at: str = ""
    created_by: str = ""
    updated_by: str = ""
    evidence: List[EvidenceRef] = field(default_factory=list)
    relationships: List[RelationshipRef] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if not self.object_id:
            self.object_id = _uuid7()
        if not self.created_at:
            self.created_at = datetime.now(timezone.utc).isoformat()
        if not self.updated_at:
            self.updated_at = self.created_at
        if not self.object_type:
            self.object_type = type(self).__name__

    # ---- Contract enforcement ------------------------------------------------

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to a canonical dictionary."""
        d = asdict(self)
        d["evidence"] = [asdict(e) for e in self.evidence]
        d["relationships"] = [asdict(r) for r in self.relationships]
        return d

    def add_evidence(self, ref: EvidenceRef) -> None:
        """Attach an evidence reference."""
        self.evidence.append(ref)
        self.updated_at = datetime.now(timezone.utc).isoformat()

    def add_relationship(self, ref: RelationshipRef) -> None:
        """Attach a typed relationship to another object."""
        self.relationships.append(ref)
        self.updated_at = datetime.now(timezone.utc).isoformat()

    def archive(self) -> None:
        """Transition to archived state."""
        self.status = ObjectStatus.ARCHIVED.value
        self.updated_at = datetime.now(timezone.utc).isoformat()

    def supersede(self) -> None:
        """Transition to superseded state (new version exists)."""
        self.status = ObjectStatus.SUPERSEDED.value
        self.updated_at = datetime.now(timezone.utc).isoformat()

    @property
    def is_active(self) -> bool:
        return self.status == ObjectStatus.ACTIVE.value

    @property
    def short_id(self) -> str:
        return self.object_id[:12] if self.object_id else ""


# ---------------------------------------------------------------------------
# Object Registry
# ---------------------------------------------------------------------------

class ObjectRegistry:
    """Registry of all object types with their handler classes.

    Enables type-based lookup, serialization, and relationship traversal
    without switch statements or type-specific routing.
    """

    def __init__(self):
        self._types: Dict[str, Type[UniversalObject]] = {}

    def register(self, obj_type: Type[UniversalObject]) -> None:
        """Register an object type (called automatically via metaclass)."""
        key = obj_type.__name__
        self._types[key] = obj_type

    def get_type(self, name: str) -> Optional[Type[UniversalObject]]:
        return self._types.get(name)

    def types(self) -> List[str]:
        return list(self._types.keys())

    def create(self, type_name: str, **kwargs) -> UniversalObject:
        cls = self.get_type(type_name)
        if not cls:
            raise ValueError(f"Unknown object type: {type_name}")
        return cls(**kwargs)


# Global registry — one per runtime
_GLOBAL_REGISTRY: Optional[ObjectRegistry] = None


def get_registry() -> ObjectRegistry:
    global _GLOBAL_REGISTRY
    if _GLOBAL_REGISTRY is None:
        _GLOBAL_REGISTRY = ObjectRegistry()
    return _GLOBAL_REGISTRY


def reset_registry() -> None:
    global _GLOBAL_REGISTRY
    _GLOBAL_REGISTRY = None


# ---------------------------------------------------------------------------
# Auto-registration via metaclass
# ---------------------------------------------------------------------------

class ObjectMeta(type):
    """Metaclass that auto-registers UniversalObject subclasses."""

    def __new__(mcs, name, bases, namespace):
        cls = super().__new__(mcs, name, bases, namespace)
        if name != "UniversalObject" and issubclass(cls, UniversalObject):
            reg = get_registry()
            reg.register(cls)
        return cls