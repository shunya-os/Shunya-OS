"""SHUNYA Kernel — Relationship Engine.

Relationships are first-class citizens in SHUNYA.
They are graph-navigable, typed, and bidirectional.
Never treat relationships as simple foreign keys.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple


class RelationshipType(str, Enum):
    """Universal relationship types."""
    OWNS = "owns"
    MEMBER_OF = "member_of"
    WORKS_AT = "works_at"
    REPORTS_TO = "reports_to"
    CREATED = "created"
    MODIFIED = "modified"
    REFERENCES = "references"
    DERIVED_FROM = "derived_from"
    SUPPORTS = "supports"
    CONTRADICTS = "contradicts"
    ATTACHED_TO = "attached_to"
    CONTAINS = "contains"
    PART_OF = "part_of"
    FOLLOWS = "follows"
    PRECEDES = "precedes"
    RELATED_TO = "related_to"


@dataclass
class Relationship:
    """A first-class relationship between two objects.

    Relationships are directional but always have an inverse.
    """

    source_id: str
    target_id: str
    relationship_type: str = RelationshipType.RELATED_TO.value
    label: str = ""
    confidence: float = 1.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: str = ""
    created_by: str = ""

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now(timezone.utc).isoformat()


class RelationshipEngine:
    """Graph-navigable relationship store.

    Supports traversal, filtering, and bidirectional lookup.
    """

    def __init__(self):
        self._outgoing: Dict[str, List[Relationship]] = {}
        self._incoming: Dict[str, List[Relationship]] = {}

    def add(self, rel: Relationship) -> Relationship:
        """Add a relationship. Automatically tracked bidirectionally."""
        self._outgoing.setdefault(rel.source_id, []).append(rel)
        self._incoming.setdefault(rel.target_id, []).append(rel)
        return rel

    def add_bidirectional(self, source_id: str, target_id: str,
                          type_fwd: str, type_rev: str,
                          **kwargs) -> Tuple[Relationship, Relationship]:
        """Add a relationship in both directions."""
        fwd = Relationship(
            source_id=source_id, target_id=target_id,
            relationship_type=type_fwd, **kwargs,
        )
        rev = Relationship(
            source_id=target_id, target_id=source_id,
            relationship_type=type_rev, **kwargs,
        )
        self.add(fwd)
        self.add(rev)
        return fwd, rev

    def get_outgoing(self, object_id: str,
                     type_filter: Optional[str] = None
                     ) -> List[Relationship]:
        """Get relationships where this object is the source."""
        rels = self._outgoing.get(object_id, [])
        if type_filter:
            rels = [r for r in rels if r.relationship_type == type_filter]
        return rels

    def get_incoming(self, object_id: str,
                     type_filter: Optional[str] = None
                     ) -> List[Relationship]:
        """Get relationships where this object is the target."""
        rels = self._incoming.get(object_id, [])
        if type_filter:
            rels = [r for r in rels if r.relationship_type == type_filter]
        return rels

    def get_all(self, object_id: str) -> List[Relationship]:
        """Get all relationships for an object (both directions)."""
        return (self.get_outgoing(object_id) + self.get_incoming(object_id))

    def get_connected(self, object_id: str,
                      type_filter: Optional[str] = None
                      ) -> Set[str]:
        """Get all connected object IDs, optionally filtered by type."""
        connected: Set[str] = set()
        for rel in self.get_outgoing(object_id, type_filter):
            connected.add(rel.target_id)
        for rel in self.get_incoming(object_id, type_filter):
            connected.add(rel.source_id)
        return connected

    def traverse(self, start_id: str, max_depth: int = 3,
                 type_filter: Optional[str] = None
                 ) -> Dict[str, List[Dict]]:
        """BFS traversal from a starting object ID.

        Returns {depth: [{source, target, type, label}, ...]}
        """
        visited: Set[str] = {start_id}
        results: Dict[int, List[Dict]] = {}
        current_level: Set[str] = {start_id}

        for depth in range(1, max_depth + 1):
            next_level: Set[str] = set()
            level_rels: List[Dict] = []

            for obj_id in current_level:
                for rel in self.get_outgoing(obj_id, type_filter):
                    if rel.target_id not in visited:
                        visited.add(rel.target_id)
                        next_level.add(rel.target_id)
                        level_rels.append({
                            "source": rel.source_id[:12],
                            "target": rel.target_id[:12],
                            "type": rel.relationship_type,
                            "label": rel.label,
                        })
                for rel in self.get_incoming(obj_id, type_filter):
                    if rel.source_id not in visited:
                        visited.add(rel.source_id)
                        next_level.add(rel.source_id)
                        level_rels.append({
                            "source": rel.source_id[:12],
                            "target": rel.target_id[:12],
                            "type": rel.relationship_type,
                            "label": rel.label,
                        })

            if level_rels:
                results[depth] = level_rels
            current_level = next_level

        return results

    def remove(self, source_id: str, target_id: str,
               relationship_type: str) -> bool:
        """Remove a specific relationship."""
        found = False
        # Remove from outgoing
        if source_id in self._outgoing:
            before = len(self._outgoing[source_id])
            self._outgoing[source_id] = [
                r for r in self._outgoing[source_id]
                if not (r.target_id == target_id
                        and r.relationship_type == relationship_type)
            ]
            if len(self._outgoing[source_id]) < before:
                found = True
        # Remove from incoming
        if target_id in self._incoming:
            self._incoming[target_id] = [
                r for r in self._incoming[target_id]
                if not (r.source_id == source_id
                        and r.relationship_type == relationship_type)
            ]
        return found

    def count(self) -> int:
        """Total number of relationships."""
        return sum(len(rels) for rels in self._outgoing.values())


_GLOBAL_RELATIONSHIP_ENGINE: Optional[RelationshipEngine] = None


def get_relationship_engine() -> RelationshipEngine:
    global _GLOBAL_RELATIONSHIP_ENGINE
    if _GLOBAL_RELATIONSHIP_ENGINE is None:
        _GLOBAL_RELATIONSHIP_ENGINE = RelationshipEngine()
    return _GLOBAL_RELATIONSHIP_ENGINE


def reset_relationship_engine() -> None:
    global _GLOBAL_RELATIONSHIP_ENGINE
    _GLOBAL_RELATIONSHIP_ENGINE = None