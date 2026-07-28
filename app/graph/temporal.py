"""SHUNYA Knowledge Graph — Temporal Graph.

Implements temporal edge types and temporal queries as defined in:
    UNIVERSAL_KNOWLEDGE_GRAPH_ARCHITECTURE.md §5 — Temporal Graph
    UNIVERSAL_KNOWLEDGE_GRAPH_ARCHITECTURE.md §5.2 — Temporal edge types
    UNIVERSAL_KNOWLEDGE_GRAPH_ARCHITECTURE.md §5.3 — Temporal edge validity
    UNIVERSAL_KNOWLEDGE_GRAPH_ARCHITECTURE.md §5.4 — Temporal queries
    UNIVERSAL_KNOWLEDGE_GRAPH_ARCHITECTURE.md §5.5 — Temporal invariants

Constitutional rules:
    - Every Edge may have a validity period (§5.5.1).
    - Historical edges are not deleted, marked with end timestamp (§5.5.2).
    - Temporal queries without a time return current state (§5.5.3).
    - Alternative timelines are isolated from the main timeline (§5.5.4).
"""

from __future__ import annotations

import threading
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple

from app.graph.edge import Edge, EdgeStore, TimeRange, InMemoryEdgeStore, get_edge_store


# ---------------------------------------------------------------------------
# Temporal edge types (§5.2)
# ---------------------------------------------------------------------------

class TemporalEdgeType(str, Enum):
    """Canonical temporal edge types (§5.2)."""
    HISTORICAL = "historical"
    CURRENT = "current"
    FUTURE = "future"
    SCHEDULED = "scheduled"
    EXPIRED = "expired"
    SUPERSEDED = "superseded"


# ---------------------------------------------------------------------------
# Temporal query types (§5.4)
# ---------------------------------------------------------------------------

@staticmethod
def _now() -> str:
    """Get the current UTC timestamp as ISO string."""
    return datetime.now(timezone.utc).isoformat()


# ---------------------------------------------------------------------------
# TemporalStore — temporal query layer over EdgeStore
# ---------------------------------------------------------------------------

class TemporalStore:
    """Temporal query layer over the EdgeStore.

    Provides point-in-time, range, change, and future queries across
    all edges, classified by their temporal validity period.

    Builds on the EdgeStore — does not duplicate edge storage.
    Maintains a temporal index for efficient time-range queries.
    """

    def __init__(self, edge_store: Optional[EdgeStore] = None):
        self._edge_store = edge_store or get_edge_store()
        # Temporal index: sorted list of (timestamp, edge_triple, event_type)
        # where event_type is "start" or "end" of a validity period
        self._temporal_index: List[Tuple[str, Tuple[str, str, str], str]] = []
        self._lock = threading.RLock()

    # ---- Temporal edge classification (§5.2) --------------------------------

    @staticmethod
    def classify_edge(edge: Edge) -> TemporalEdgeType:
        """Classify an edge by its temporal type based on validity period.

        Args:
            edge: The edge to classify.

        Returns:
            The TemporalEdgeType classification.
        """
        now = _now()
        if edge.validity is None:
            # No validity period = current (assumed valid from creation)
            return TemporalEdgeType.CURRENT

        if edge.validity.end is None:
            # Has start but no end = currently valid
            if edge.validity.start <= now:
                return TemporalEdgeType.CURRENT
            else:
                return TemporalEdgeType.FUTURE

        # Has both start and end
        if edge.validity.end < now:
            # End is in the past
            if edge.edge_type in ("superseded_by", "version_of"):
                return TemporalEdgeType.SUPERSEDED
            return TemporalEdgeType.EXPIRED

        if edge.validity.start > now:
            # Start is in the future = FUTURE (predicted to be true)
            return TemporalEdgeType.FUTURE

        # Start <= now <= end = currently valid
        return TemporalEdgeType.CURRENT

    @staticmethod
    def is_scheduled(edge: Edge) -> bool:
        """Check if an edge is scheduled (has a definite future time).

        An edge is SCHEDULED if it has a specific future validity start
        AND the edge type or metadata indicates it is a scheduled commitment
        (e.g., meeting, appointment, deadline).

        This is a semantic distinction from FUTURE (§5.2):
        - FUTURE: predicted to be true, no specific time certainty
        - SCHEDULED: will be true at a specific future time
        """
        if edge.validity is None:
            return False
        now = _now()
        if edge.validity.start > now:
            return True
        return False

    @staticmethod
    def get_temporal_types() -> List[TemporalEdgeType]:
        """Get all canonical temporal edge types."""
        return list(TemporalEdgeType)

    # ---- Temporal index ----------------------------------------------------

    def _index_edge(self, edge: Edge) -> None:
        """Add an edge to the temporal index."""
        if edge.validity is None:
            return
        with self._lock:
            self._temporal_index.append(
                (edge.validity.start, edge.triple, "start")
            )
            if edge.validity.end is not None:
                self._temporal_index.append(
                    (edge.validity.end, edge.triple, "end")
                )
            # Keep sorted by timestamp
            self._temporal_index.sort(key=lambda x: x[0])

    def _deindex_edge(self, edge: Edge) -> None:
        """Remove an edge from the temporal index."""
        if edge.validity is None:
            return
        with self._lock:
            self._temporal_index = [
                entry for entry in self._temporal_index
                if entry[1] != edge.triple
            ]

    def refresh_index(self) -> None:
        """Rebuild the temporal index from all edges in the store."""
        with self._lock:
            self._temporal_index.clear()
            for edge in self._edge_store.all():
                self._index_edge(edge)

    # ---- Temporal queries (§5.4) -------------------------------------------

    def point_in_time(self, timestamp: str) -> List[Edge]:
        """Query edges active at a specific point in time (§5.4).

        Returns all edges whose validity period contains the given timestamp,
        or edges with no validity period (assumed always active).

        Args:
            timestamp: ISO 8601 timestamp string.

        Returns:
            List of edges active at the given time.
        """
        results: List[Edge] = []
        for edge in self._edge_store.all():
            if edge.validity is None:
                # No validity = always active (§5.5.1)
                results.append(edge)
            elif edge.validity.is_active_at(timestamp):
                results.append(edge)
        return results

    def range(self, start: str, end: str) -> List[Edge]:
        """Query edges active between two timestamps (§5.4).

        Returns edges whose validity period overlaps with [start, end].

        Args:
            start: ISO 8601 start timestamp (inclusive).
            end: ISO 8601 end timestamp (inclusive).

        Returns:
            List of edges active during the range.
        """
        results: List[Edge] = []
        for edge in self._edge_store.all():
            if edge.validity is None:
                # No validity = always active
                results.append(edge)
            elif edge.validity.is_active_at(start):
                results.append(edge)
            elif edge.validity.is_active_at(end):
                results.append(edge)
            elif (edge.validity.start >= start and
                  (edge.validity.end is None or edge.validity.end <= end)):
                # Validity period fully contained in range
                results.append(edge)
        return results

    def changes(self, start: str, end: str) -> List[Dict[str, Any]]:
        """Query what changed between two timestamps (§5.4).

        Returns a list of change events: edges that were created, became
        active, expired, or were removed within the time range.

        Args:
            start: ISO 8601 start timestamp.
            end: ISO 8601 end timestamp.

        Returns:
            List of change dicts with 'edge', 'source', 'target', 'type',
            'change_type' (created, activated, expired, removed).
        """
        changes: List[Dict[str, Any]] = []
        for edge in self._edge_store.all():
            # Edge created within range
            if start <= edge.created_at <= end:
                changes.append({
                    "edge": edge,
                    "source_id": edge.source_id,
                    "target_id": edge.target_id,
                    "edge_type": edge.edge_type,
                    "change_type": "created",
                    "timestamp": edge.created_at,
                })
            # Validity changes within range
            if edge.validity is not None:
                if start <= edge.validity.start <= end:
                    changes.append({
                        "edge": edge,
                        "source_id": edge.source_id,
                        "target_id": edge.target_id,
                        "edge_type": edge.edge_type,
                        "change_type": "activated",
                        "timestamp": edge.validity.start,
                    })
                if edge.validity.end is not None and start <= edge.validity.end <= end:
                    changes.append({
                        "edge": edge,
                        "source_id": edge.source_id,
                        "target_id": edge.target_id,
                        "edge_type": edge.edge_type,
                        "change_type": "expired",
                        "timestamp": edge.validity.end,
                    })
        # Sort by timestamp
        changes.sort(key=lambda x: x["timestamp"])
        return changes

    def future(self, timestamp: str) -> List[Edge]:
        """Query edges predicted to be active at a future time (§5.4).

        Returns edges whose validity period will contain the given timestamp
        but whose start is in the future relative to now.

        Args:
            timestamp: ISO 8601 future timestamp.

        Returns:
            List of edges predicted to be active at the given time.
        """
        now = _now()
        results: List[Edge] = []
        for edge in self._edge_store.all():
            if edge.validity is None:
                continue
            if edge.validity.start > now and edge.validity.is_active_at(timestamp):
                results.append(edge)
        return results

    def current(self) -> List[Edge]:
        """Query all currently active edges (§5.5.3).

        Returns edges that are currently valid (no validity period, or
        validity period contains now).
        """
        now = _now()
        return self.point_in_time(now)

    # ---- Helper ------------------------------------------------------------

    def get_edges_by_temporal_type(self, temporal_type: TemporalEdgeType) -> List[Edge]:
        """Get all edges matching a specific temporal classification.

        Args:
            temporal_type: The TemporalEdgeType to filter by.

        Returns:
            List of edges matching the classification.
        """
        return [
            edge for edge in self._edge_store.all()
            if self.classify_edge(edge) == temporal_type
        ]

    def has_temporal_edges(self) -> bool:
        """Check if any edges have temporal validity periods."""
        return any(
            edge.validity is not None
            for edge in self._edge_store.all()
        )


# ---------------------------------------------------------------------------
# Singleton
# ---------------------------------------------------------------------------

_GLOBAL_TEMPORAL_STORE: Optional[TemporalStore] = None


def get_temporal_store() -> TemporalStore:
    """Get the global TemporalStore singleton."""
    global _GLOBAL_TEMPORAL_STORE
    if _GLOBAL_TEMPORAL_STORE is None:
        _GLOBAL_TEMPORAL_STORE = TemporalStore()
    return _GLOBAL_TEMPORAL_STORE


def reset_temporal_store() -> None:
    """Reset the global TemporalStore (for testing)."""
    global _GLOBAL_TEMPORAL_STORE
    _GLOBAL_TEMPORAL_STORE = None