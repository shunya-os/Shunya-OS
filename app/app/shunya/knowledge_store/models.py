"""SHUNYA — Knowledge Store domain models (Phase C).

Immutable knowledge objects with versioning, namespacing, and status lifecycle.
No object is ever silently overwritten — every mutation creates a new version.

Architectural authority: Phase C — Knowledge Store Foundation
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional


class KnowledgeObjectStatus(Enum):
    ACTIVE = "active"
    ARCHIVED = "archived"
    SUPERSEDED = "superseded"


class KnowledgeObjectType(Enum):
    FACT = "fact"
    CONFIG = "config"
    POLICY = "policy"
    TEMPLATE = "template"
    REFERENCE = "reference"
    METADATA = "metadata"


@dataclass
class KnowledgeObject:
    """An immutable knowledge object.

    Every object has a unique identity across all versions.
    Mutations create new versions — the original is never overwritten.
    """

    object_id: str = ""
    type: str = KnowledgeObjectType.FACT.value
    namespace: str = "default"
    key: str = ""
    version: int = 1
    payload: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    status: str = KnowledgeObjectStatus.ACTIVE.value
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    created_by: str = "system"
    description: str = ""

    def __post_init__(self) -> None:
        if not self.object_id:
            self.object_id = str(uuid.uuid4())
        if self.created_at is None:
            self.created_at = datetime.now(timezone.utc)
        if self.updated_at is None:
            self.updated_at = self.created_at

    @property
    def is_active(self) -> bool:
        return self.status == KnowledgeObjectStatus.ACTIVE.value

    @property
    def is_archived(self) -> bool:
        return self.status == KnowledgeObjectStatus.ARCHIVED.value

    def to_dict(self) -> Dict[str, Any]:
        return {
            "object_id": self.object_id,
            "type": self.type,
            "namespace": self.namespace,
            "key": self.key,
            "version": self.version,
            "payload": self.payload,
            "metadata": self.metadata,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "created_by": self.created_by,
            "description": self.description,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "KnowledgeObject":
        return cls(
            object_id=data.get("object_id", ""),
            type=data.get("type", KnowledgeObjectType.FACT.value),
            namespace=data.get("namespace", "default"),
            key=data.get("key", ""),
            version=data.get("version", 1),
            payload=data.get("payload", {}),
            metadata=data.get("metadata", {}),
            status=data.get("status", KnowledgeObjectStatus.ACTIVE.value),
            created_at=_parse_dt(data.get("created_at")),
            updated_at=_parse_dt(data.get("updated_at")),
            created_by=data.get("created_by", "system"),
            description=data.get("description", ""),
        )

    def clone_for_version(self, new_version: int) -> "KnowledgeObject":
        """Create a new version of this object with the same identity."""
        return KnowledgeObject(
            object_id=self.object_id,
            type=self.type,
            namespace=self.namespace,
            key=self.key,
            version=new_version,
            payload=dict(self.payload),
            metadata=dict(self.metadata),
            status=KnowledgeObjectStatus.ACTIVE.value,
            created_at=self.created_at,
            updated_at=datetime.now(timezone.utc),
            created_by=self.created_by,
            description=self.description,
        )


def _parse_dt(value: Any) -> Optional[datetime]:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value
    if isinstance(value, str):
        try:
            return datetime.fromisoformat(value)
        except (ValueError, TypeError):
            return None
    return None


# ---- Search types -----------------------------------------------------------


@dataclass
class SearchFilter:
    field: str
    value: Any
    operator: str = "eq"  # eq, neq, contains, gt, gte, lt, lte, in

    def matches(self, obj: KnowledgeObject) -> bool:
        obj_dict = obj.to_dict()
        actual = obj_dict.get(self.field)
        if self.operator == "eq":
            return actual == self.value
        if self.operator == "neq":
            return actual != self.value
        if self.operator == "contains":
            return self.value in str(actual)
        if self.operator in ("gt", "gte", "lt", "lte"):
            try:
                if self.operator == "gt":
                    return actual is not None and actual > self.value
                if self.operator == "gte":
                    return actual is not None and actual >= self.value
                if self.operator == "lt":
                    return actual is not None and actual < self.value
                if self.operator == "lte":
                    return actual is not None and actual <= self.value
            except TypeError:
                return False
        if self.operator == "in":
            return actual in self.value if isinstance(self.value, (list, tuple)) else False
        return False


@dataclass
class SearchQuery:
    filters: List[SearchFilter] = field(default_factory=list)
    namespace: Optional[str] = None
    object_type: Optional[str] = None
    status: Optional[str] = None
    limit: int = 100
    offset: int = 0
    sort_by: str = "updated_at"
    sort_desc: bool = True

    def matches(self, obj: KnowledgeObject) -> bool:
        if self.namespace and obj.namespace != self.namespace:
            return False
        if self.object_type and obj.type != self.object_type:
            return False
        if self.status and obj.status != self.status:
            return False
        for f in self.filters:
            if not f.matches(obj):
                return False
        return True


@dataclass
class SearchResult:
    items: List[KnowledgeObject]
    total: int
    limit: int
    offset: int
    has_more: bool = False