"""
Relationship Engine — In-Memory Implementation

The RelationshipEngine manages typed, directed connections between
UniversalObjects in SHUNYA.  It supports the full relationship lifecycle
and graph traversal operations: BFS, path finding, subgraph extraction,
validity checking, and filtering.

All relationships are immutable after creation.  Status changes produce
new Relationship instances with updated ``updated_at`` timestamps.
"""

from __future__ import annotations

from collections import deque
from datetime import datetime
from typing import Any

from core.relationship.models import (
    Relationship,
    RelationshipDirection,
    RelationshipStatus,
    RelationshipType,
    matches_strength,
    matches_type,
)


class RelationshipEngine:
    """In-memory engine for managing typed relationships between objects.

    Maintains an adjacency-list-style index for efficient traversal
    (outgoing edges per source, incoming edges per target).

    This is a **single-threaded, in-memory** implementation suitable for
    prototyping, testing, and small-to-medium deployments.  Production
    deployments should back this with a graph database.

    **Rules** (from Universal Ontology §6, Business Canon §3.5):
    - Relationships are always between two objects.
    - Relationship types are canonical (RelationshipType enum).
    - A relationship can be directional or bidirectional.
    - Evidence can support a relationship.
    - Relationships can be time-bound (temporal).
    """

    def __init__(self) -> None:
        # Primary store: relationship_id -> Relationship
        self._relationships: dict[str, Relationship] = {}
        # Outgoing index: source_id -> list of relationship_ids
        self._outgoing: dict[str, list[str]] = {}
        # Incoming index: target_id -> list of relationship_ids
        self._incoming: dict[str, list[str]] = {}

    # ------------------------------------------------------------------
    # CRUD
    # ------------------------------------------------------------------

    def add_relationship(
        self,
        source_id: str,
        target_id: str,
        relationship_type: RelationshipType | str,
        direction: RelationshipDirection | str = RelationshipDirection.DIRECTIONAL,
        strength: float = 1.0,
        label: str = "",
        metadata: dict[str, Any] | None = None,
        evidence_ids: list[str] | None = None,
        created_by: str = "system",
        valid_from: datetime | None = None,
        valid_until: datetime | None = None,
    ) -> Relationship:
        """Create a new relationship between two objects.

        Args:
            source_id: The object from which the relationship originates.
            target_id: The object to which the relationship points.
            relationship_type: The canonical type (``RelationshipType``
                enum or string value).
            direction: Directionality semantics (``RelationshipDirection``
                enum or string value).
            strength: How well-established [0, 1].
            label: Optional human-readable label.
            metadata: Optional extensible metadata.
            evidence_ids: Optional list of evidence references.
            created_by: ID of the creating entity.
            valid_from: Optional start of validity window.
            valid_until: Optional end of validity window.

        Returns:
            The newly created ``Relationship``.

        Raises:
            ValueError: If either source or target is empty, if they
                are the same, or if the type/direction is invalid.
        """
        # Normalize enums
        if isinstance(relationship_type, str):
            try:
                relationship_type = RelationshipType(relationship_type)
            except ValueError:
                valid = [t.value for t in RelationshipType]
                raise ValueError(
                    f"Invalid relationship_type {relationship_type!r}. "
                    f"Valid values: {valid}"
                )
        if isinstance(direction, str):
            try:
                direction = RelationshipDirection(direction)
            except ValueError:
                valid = [d.value for d in RelationshipDirection]
                raise ValueError(
                    f"Invalid direction {direction!r}. "
                    f"Valid values: {valid}"
                )

        rel = Relationship(
            source_id=source_id,
            target_id=target_id,
            relationship_type=relationship_type,
            direction=direction,
            strength=strength,
            label=label,
            metadata=metadata or {},
            created_by=created_by,
            valid_from=valid_from,
            valid_until=valid_until,
            evidence_ids=tuple(evidence_ids or ()),
        )

        self._relationships[rel.relationship_id] = rel
        self._outgoing.setdefault(source_id, []).append(rel.relationship_id)
        self._incoming.setdefault(target_id, []).append(rel.relationship_id)

        # For bidirectional relationships, also add a reverse edge
        if direction == RelationshipDirection.BIDIRECTIONAL:
            self._outgoing.setdefault(target_id, []).append(rel.relationship_id)
            self._incoming.setdefault(source_id, []).append(rel.relationship_id)

        return rel

    def remove_relationship(self, relationship_id: str) -> bool:
        """Permanently remove a relationship from the graph.

        .. warning::
            This is a hard delete.  For audit trails, prefer marking
            the relationship status as ``ENDED`` instead.

        Args:
            relationship_id: The relationship ID to remove.

        Returns:
            ``True`` if the relationship was removed, ``False`` if it
            did not exist.
        """
        rel = self._relationships.pop(relationship_id, None)
        if rel is None:
            return False

        # Remove from outgoing index
        outgoing = self._outgoing.get(rel.source_id, [])
        if relationship_id in outgoing:
            outgoing.remove(relationship_id)
            if not outgoing:
                del self._outgoing[rel.source_id]

        # Remove from incoming index
        incoming = self._incoming.get(rel.target_id, [])
        if relationship_id in incoming:
            incoming.remove(relationship_id)
            if not incoming:
                del self._incoming[rel.target_id]

        # If bidirectional, remove the reverse index entries
        if rel.direction == RelationshipDirection.BIDIRECTIONAL:
            outgoing_rev = self._outgoing.get(rel.target_id, [])
            if relationship_id in outgoing_rev:
                outgoing_rev.remove(relationship_id)
                if not outgoing_rev:
                    del self._outgoing[rel.target_id]

            incoming_rev = self._incoming.get(rel.source_id, [])
            if relationship_id in incoming_rev:
                incoming_rev.remove(relationship_id)
                if not incoming_rev:
                    del self._incoming[rel.source_id]

        return True

    def get_relationship(self, relationship_id: str) -> Relationship | None:
        """Retrieve a relationship by its ID.

        Args:
            relationship_id: The relationship UUID.

        Returns:
            The ``Relationship`` if found, or ``None``.
        """
        return self._relationships.get(relationship_id)

    # ------------------------------------------------------------------
    # Query by Object
    # ------------------------------------------------------------------

    def get_outgoing(
        self,
        object_id: str,
        type_filter: RelationshipType | str | None = None,
        min_strength: float | None = None,
        status_filter: RelationshipStatus | None = None,
    ) -> list[Relationship]:
        """Return relationships where *object_id* is the source.

        Args:
            object_id: The source object ID.
            type_filter: Optional relationship type filter.
            min_strength: Optional minimum strength [0, 1].
            status_filter: Optional status filter.

        Returns:
            List of matching outgoing relationships.
        """
        rel_ids = self._outgoing.get(object_id, [])
        return self._filter_relationships(rel_ids, type_filter, min_strength, status_filter)

    def get_incoming(
        self,
        object_id: str,
        type_filter: RelationshipType | str | None = None,
        min_strength: float | None = None,
        status_filter: RelationshipStatus | None = None,
    ) -> list[Relationship]:
        """Return relationships where *object_id* is the target.

        Args:
            object_id: The target object ID.
            type_filter: Optional relationship type filter.
            min_strength: Optional minimum strength [0, 1].
            status_filter: Optional status filter.

        Returns:
            List of matching incoming relationships.
        """
        rel_ids = self._incoming.get(object_id, [])
        return self._filter_relationships(rel_ids, type_filter, min_strength, status_filter)

    def get_all(
        self,
        object_id: str,
        type_filter: RelationshipType | str | None = None,
        direction: RelationshipDirection | None = None,
        min_strength: float | None = None,
        status_filter: RelationshipStatus | None = None,
    ) -> list[Relationship]:
        """Return all relationships involving *object_id*.

        Combines outgoing and incoming relationships, deduplicating
        by relationship ID (for bidirectional edges).

        Args:
            object_id: The object ID to query.
            type_filter: Optional relationship type filter.
            direction: Optional direction filter.
            min_strength: Optional minimum strength [0, 1].
            status_filter: Optional status filter.

        Returns:
            List of all matching relationships involving the object.
        """
        seen: set[str] = set()
        results: list[Relationship] = []

        for rel_id in self._outgoing.get(object_id, []):
            if rel_id not in seen:
                seen.add(rel_id)
                rel = self._relationships.get(rel_id)
                if rel and self._matches(rel, type_filter, min_strength, status_filter):
                    if direction is None or rel.direction == direction:
                        results.append(rel)

        for rel_id in self._incoming.get(object_id, []):
            if rel_id not in seen:
                seen.add(rel_id)
                rel = self._relationships.get(rel_id)
                if rel and self._matches(rel, type_filter, min_strength, status_filter):
                    if direction is None or rel.direction == direction:
                        results.append(rel)

        return results

    def get_relationship_count(self, object_id: str) -> int:
        """Return the total number of relationships involving an object.

        Args:
            object_id: The object ID to count.

        Returns:
            Count of outgoing + incoming relationships.
        """
        count = 0
        count += len(self._outgoing.get(object_id, []))
        count += len(self._incoming.get(object_id, []))
        return count

    def get_relationship_types(self) -> list[str]:
        """Return all canonical relationship type strings.

        Returns:
            Sorted list of type strings.
        """
        return sorted(t.value for t in RelationshipType)

    # ------------------------------------------------------------------
    # Graph Traversal
    # ------------------------------------------------------------------

    def get_neighbors(
        self,
        object_id: str,
        type_filter: RelationshipType | str | None = None,
        max_depth: int = 1,
        min_strength: float | None = None,
    ) -> list[str]:
        """Return all object IDs reachable via BFS traversal.

        Args:
            object_id: Starting object ID.
            type_filter: Optional relationship type filter.
            max_depth: Maximum traversal depth (default: 1, i.e. direct
                neighbors only).
            min_strength: Optional minimum strength filter.

        Returns:
            List of unique object IDs reachable within the depth limit.
        """
        visited: set[str] = {object_id}
        queue: deque[tuple[str, int]] = deque()
        queue.append((object_id, 0))

        while queue:
            current, depth = queue.popleft()
            if depth >= max_depth:
                continue

            # Explore outgoing edges
            for rel_id in self._outgoing.get(current, []):
                rel = self._relationships.get(rel_id)
                if rel is None:
                    continue
                if not self._matches(rel, type_filter, min_strength, None):
                    continue
                neighbor = rel.target_id
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append((neighbor, depth + 1))

            # Explore incoming edges (traversal is undirected by default)
            for rel_id in self._incoming.get(current, []):
                rel = self._relationships.get(rel_id)
                if rel is None:
                    continue
                if not self._matches(rel, type_filter, min_strength, None):
                    continue
                neighbor = rel.source_id
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append((neighbor, depth + 1))

        visited.discard(object_id)
        return list(visited)

    def find_path(
        self,
        source_id: str,
        target_id: str,
        max_depth: int = 10,
        type_filter: RelationshipType | str | None = None,
        min_strength: float | None = None,
    ) -> list[Relationship]:
        """Find the shortest path between two objects via BFS.

        Returns a list of ``Relationship`` objects that form the path
        from *source_id* to *target_id*.

        Args:
            source_id: Starting object ID.
            target_id: Target object ID.
            max_depth: Maximum search depth (default: 10).
            type_filter: Optional relationship type filter.
            min_strength: Optional minimum strength filter.

        Returns:
            List of ``Relationship`` objects forming the path, or an
            empty list if no path exists within the depth limit.
        """
        if source_id == target_id:
            return []

        # BFS: track (current_node, path_of_relationships)
        visited: set[str] = {source_id}
        queue: deque[tuple[str, list[Relationship]]] = deque()
        queue.append((source_id, []))

        while queue:
            current, path = queue.popleft()
            if len(path) >= max_depth:
                continue

            # Explore outgoing edges
            for rel_id in self._outgoing.get(current, []):
                rel = self._relationships.get(rel_id)
                if rel is None:
                    continue
                if not self._matches(rel, type_filter, min_strength, None):
                    continue
                if rel.target_id in visited:
                    continue
                new_path = path + [rel]
                if rel.target_id == target_id:
                    return new_path
                visited.add(rel.target_id)
                queue.append((rel.target_id, new_path))

            # Explore incoming edges
            for rel_id in self._incoming.get(current, []):
                rel = self._relationships.get(rel_id)
                if rel is None:
                    continue
                if not self._matches(rel, type_filter, min_strength, None):
                    continue
                if rel.source_id in visited:
                    continue
                new_path = path + [rel]
                if rel.source_id == target_id:
                    return new_path
                visited.add(rel.source_id)
                queue.append((rel.source_id, new_path))

        return []

    def get_subgraph(
        self,
        object_id: str,
        depth: int = 1,
        type_filter: RelationshipType | str | None = None,
        min_strength: float | None = None,
    ) -> dict[str, list[Relationship]]:
        """Extract the subgraph within *depth* hops of *object_id*.

        Returns a dictionary mapping each object ID in the subgraph
        to its list of relationships (within the subgraph).

        Args:
            object_id: Center object ID.
            depth: Maximum hop distance from center.
            type_filter: Optional relationship type filter.
            min_strength: Optional minimum strength filter.

        Returns:
            Dict of ``{object_id: [Relationship, ...]}`` for all objects
            within the subgraph.
        """
        subgraph: dict[str, list[Relationship]] = {}
        visited: set[str] = {object_id}
        subgraph.setdefault(object_id, [])

        # BFS to collect nodes and edges
        queue: deque[tuple[str, int]] = deque()
        queue.append((object_id, 0))

        while queue:
            current, current_depth = queue.popleft()
            if current_depth >= depth:
                continue

            for rel_id in self._outgoing.get(current, []):
                rel = self._relationships.get(rel_id)
                if rel is None:
                    continue
                if not self._matches(rel, type_filter, min_strength, None):
                    continue
                neighbor = rel.target_id
                subgraph.setdefault(current, []).append(rel)
                subgraph.setdefault(neighbor, []).append(rel)
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append((neighbor, current_depth + 1))

            for rel_id in self._incoming.get(current, []):
                rel = self._relationships.get(rel_id)
                if rel is None:
                    continue
                if not self._matches(rel, type_filter, min_strength, None):
                    continue
                neighbor = rel.source_id
                subgraph.setdefault(current, []).append(rel)
                subgraph.setdefault(neighbor, []).append(rel)
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append((neighbor, current_depth + 1))

        return subgraph

    # ------------------------------------------------------------------
    # Validation
    # ------------------------------------------------------------------

    def validate_relationship(self, rel: Relationship) -> bool:
        """Validate a relationship against engine rules.

        Checks:
        - Source and target are non-empty and different.
        - Relationship type is a valid ``RelationshipType``.
        - Direction is a valid ``RelationshipDirection``.
        - Strength is in [0, 1].
        - Temporal relationships have a validity window.
        - valid_from precedes valid_until (if both set).

        Note:
            This validates the relationship *structure*, not whether
            the source/target object IDs exist in the system (since
            the engine doesn't manage objects).

        Args:
            rel: The ``Relationship`` to validate.

        Returns:
            ``True`` if the relationship is structurally valid.
        """
        try:
            # Trigger __post_init__ validation by checking invariants
            if not rel.source_id:
                return False
            if not rel.target_id:
                return False
            if rel.source_id == rel.target_id:
                return False
            if not 0.0 <= rel.strength <= 1.0:
                return False
            if not isinstance(rel.relationship_type, RelationshipType):
                return False
            if not isinstance(rel.direction, RelationshipDirection):
                return False
            if not isinstance(rel.status, RelationshipStatus):
                return False
            if rel.valid_from and rel.valid_until and rel.valid_from > rel.valid_until:
                return False
            if rel.direction == RelationshipDirection.TEMPORAL and rel.valid_until is None:
                return False
            return True
        except (ValueError, TypeError):
            return False

    # ------------------------------------------------------------------
    # Utility
    # ------------------------------------------------------------------

    def clear(self) -> None:
        """Reset the engine to its initial state (useful for testing)."""
        self._relationships.clear()
        self._outgoing.clear()
        self._incoming.clear()

    def get_all_relationships(self) -> list[Relationship]:
        """Return all relationships in the engine.

        Returns:
            List of all relationships, newest first.
        """
        return sorted(
            self._relationships.values(),
            key=lambda r: r.created_at,
            reverse=True,
        )

    # ------------------------------------------------------------------
    # Internal Helpers
    # ------------------------------------------------------------------

    def _filter_relationships(
        self,
        rel_ids: list[str],
        type_filter: RelationshipType | str | None,
        min_strength: float | None,
        status_filter: RelationshipStatus | None,
    ) -> list[Relationship]:
        """Filter a list of relationship IDs by type, strength, and status."""
        results: list[Relationship] = []
        for rid in rel_ids:
            rel = self._relationships.get(rid)
            if rel and self._matches(rel, type_filter, min_strength, status_filter):
                results.append(rel)
        return results

    def _matches(
        self,
        rel: Relationship,
        type_filter: RelationshipType | str | None,
        min_strength: float | None,
        status_filter: RelationshipStatus | None,
    ) -> bool:
        """Check if a relationship matches all given filters."""
        if not matches_type(rel, type_filter):
            return False
        if not matches_strength(rel, min_strength):
            return False
        if status_filter is not None and rel.status != status_filter:
            return False
        return True


# ---------------------------------------------------------------------------
# Convenience: create a default engine
# ---------------------------------------------------------------------------

_default_engine: RelationshipEngine | None = None


def get_relationship_engine() -> RelationshipEngine:
    """Return the default singleton ``RelationshipEngine`` instance.

    This is a convenience for simple use cases.  For production or
    testing, instantiate ``RelationshipEngine()`` directly.
    """
    global _default_engine
    if _default_engine is None:
        _default_engine = RelationshipEngine()
    return _default_engine