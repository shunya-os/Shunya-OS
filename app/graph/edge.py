"""SHUNYA Knowledge Graph — Edge Model and Store.

Implements the core Edge dataclass and InMemoryEdgeStore as defined in:
    UNIVERSAL_KNOWLEDGE_GRAPH_ARCHITECTURE.md §1.3 — Edge structure
    UNIVERSAL_KNOWLEDGE_GRAPH_ARCHITECTURE.md §3 — Relationship Architecture
    UNIVERSAL_KNOWLEDGE_GRAPH_ARCHITECTURE.md §3.1 — Canonical edge families
    UNIVERSAL_KNOWLEDGE_GRAPH_ARCHITECTURE.md §3.2 — Edge creation rules
    UNIVERSAL_KNOWLEDGE_GRAPH_ARCHITECTURE.md §3.3 — Edge lifecycle
    UNIVERSAL_KNOWLEDGE_GRAPH_ARCHITECTURE.md §3.4 — Edge validation

Constitutional rules:
    - Every Edge must have valid source and target Nodes (§3.2.1).
    - No two Edges may share the same (source, target, type) triple (§3.2.3).
    - The Graph builds on the Kernel. The Kernel must never depend on the Graph.
"""

from __future__ import annotations

import uuid
import threading
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple

from app.kernel.object import EvidenceRef
from app.graph.node import NodeStore, InMemoryNodeStore, get_node_store


# ---------------------------------------------------------------------------
# Edge direction (§1.3)
# ---------------------------------------------------------------------------

class EdgeDirection(str, Enum):
    """Direction of an Edge in the graph (§1.3)."""
    DIRECTED = "directed"
    BIDIRECTIONAL = "bidirectional"


# ---------------------------------------------------------------------------
# Edge lifecycle status (§3.3)
# ---------------------------------------------------------------------------

class EdgeStatus(str, Enum):
    """Lifecycle status of an Edge (§3.3)."""
    PROPOSED = "proposed"
    ACTIVE = "active"
    STALE = "stale"
    ARCHIVED = "archived"
    REMOVED = "removed"


# ---------------------------------------------------------------------------
# Canonical edge type constants (§3.1)
# ---------------------------------------------------------------------------

class EdgeType(str, Enum):
    """Canonical edge families from KG §3.1.

    Each family maps to one or more specific relationship types.
    """
    # ownership
    OWNS = "owns"
    CREATED_BY = "created_by"
    ASSIGNED_TO = "assigned_to"
    # membership
    BELONGS_TO = "belongs_to"
    MEMBER_OF = "member_of"
    WORKS_AT = "works_at"
    # dependency
    DEPENDS_ON = "depends_on"
    REQUIRES = "requires"
    BLOCKS = "blocks"
    # reference
    MENTIONS = "mentions"
    REFERENCES = "references"
    CITES = "cites"
    # evidential
    SUPPORTS = "supports"
    CONTRADICTS = "contradicts"
    PROVES = "proves"
    # causal
    CAUSES = "causes"
    RESULTS_IN = "results_in"
    LEADS_TO = "leads_to"
    # temporal
    PRECEDES = "precedes"
    FOLLOWS = "follows"
    OVERLAPS = "overlaps"
    # derivation
    DERIVED_FROM = "derived_from"
    INFERRED_FROM = "inferred_from"
    PREDICTED_BY = "predicted_by"
    # hierarchical
    CONTAINS = "contains"
    PARENT_OF = "parent_of"
    SUPERSEDES = "supersedes"
    # inheritance
    INHERITS_FROM = "inherits_from"
    EXTENDS = "extends"
    SPECIALIZES = "specializes"
    # social
    KNOWS = "knows"
    COLLABORATES_WITH = "collaborates_with"
    RELATES_TO = "relates_to"
    # contextual
    OBSERVED_IN = "observed_in"
    OCCURRED_DURING = "occurred_during"
    RELEVANT_TO = "relevant_to"
    # predicted
    FORECAST_FOR = "forecast_for"
    # historical
    VERSION_OF = "version_of"
    # attribution
    ATTRIBUTED_TO = "attributed_to"
    SOURCE_OF = "source_of"
    ORIGINATED_FROM = "originated_from"

    # Generic
    RELATED_TO = "related_to"


# ---------------------------------------------------------------------------
# Time range for validity (§5.3)
# ---------------------------------------------------------------------------

@dataclass
class TimeRange:
    """Temporal validity period for an Edge (§5.3)."""
    start: str = ""
    end: Optional[str] = None

    def __post_init__(self) -> None:
        if not self.start:
            self.start = datetime.now(timezone.utc).isoformat()

    def is_active_at(self, timestamp: str) -> bool:
        """Check if this time range is active at the given timestamp."""
        if self.end is not None and timestamp > self.end:
            return False
        return timestamp >= self.start

    def is_current(self) -> bool:
        """Check if this time range is currently active."""
        now = datetime.now(timezone.utc).isoformat()
        return self.is_active_at(now)


# ---------------------------------------------------------------------------
# Edge — a connection between two Nodes (KG §1.3)
# ---------------------------------------------------------------------------

@dataclass
class Edge:
    """A single Edge connecting two Nodes in the graph.

    Constitutional invariants enforced:
        O-05: Everything is connected (edge creation rule)
        I-02: Merge preserves evidence (edge tracks provenance)
        KG-01: No duplicate (source, target, type) triples
        KG-02: Source and target must exist in the graph
    """

    # Source and target Node identities (§1.3)
    source_id: str
    target_id: str

    # Edge type from canonical families (§3.1)
    edge_type: str = EdgeType.RELATED_TO.value

    # Direction (§1.3)
    direction: str = EdgeDirection.DIRECTED.value

    # Confidence score 0.0–1.0 (§1.3)
    confidence: float = 1.0

    # Evidence chain references (§1.3)
    evidence: List[EvidenceRef] = field(default_factory=list)

    # Temporal validity (§5.3, optional)
    validity: Optional[TimeRange] = None

    # Traversal weight 0.0–1.0 (§1.8)
    weight: float = 1.0

    # Provenance
    provenance: str = "graph"

    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)

    # Lifecycle status (§3.3)
    status: str = EdgeStatus.ACTIVE.value

    # Creation timestamp
    created_at: str = ""

    def __post_init__(self) -> None:
        if not self.created_at:
            self.created_at = datetime.now(timezone.utc).isoformat()

    # ---- Property helpers ---------------------------------------------------

    @property
    def is_active(self) -> bool:
        return self.status == EdgeStatus.ACTIVE.value

    @property
    def is_bidirectional(self) -> bool:
        return self.direction == EdgeDirection.BIDIRECTIONAL.value

    @property
    def triple(self) -> Tuple[str, str, str]:
        """Canonical identity triple: (source, target, type)."""
        return (self.source_id, self.target_id, self.edge_type)

    @property
    def short_source(self) -> str:
        return self.source_id[:16] if self.source_id else ""

    @property
    def short_target(self) -> str:
        return self.target_id[:16] if self.target_id else ""

    # ---- Mutation helpers ---------------------------------------------------

    def archive(self) -> None:
        self.status = EdgeStatus.ARCHIVED.value

    def mark_stale(self) -> None:
        self.status = EdgeStatus.STALE.value

    # ---- Serialization ------------------------------------------------------

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to a canonical dictionary."""
        d: Dict[str, Any] = {
            "source_id": self.source_id,
            "target_id": self.target_id,
            "edge_type": self.edge_type,
            "direction": self.direction,
            "confidence": self.confidence,
            "evidence": [
                {"object_id": e.object_id, "object_type": e.object_type,
                 "field": e.field, "confidence": e.confidence}
                for e in self.evidence
            ],
            "weight": self.weight,
            "status": self.status,
            "created_at": self.created_at,
            "metadata": dict(self.metadata),
        }
        if self.validity:
            d["validity"] = {
                "start": self.validity.start,
                "end": self.validity.end,
            }
        return d


# ---------------------------------------------------------------------------
# EdgeStore — abstract interface
# ---------------------------------------------------------------------------

class EdgeStore:
    """Abstract interface for Edge storage.

    Implementations:
        - InMemoryEdgeStore (development / testing)
        - SqlEdgeStore (production — Phase 9F+)
    """

    def create(self, edge: Edge) -> Edge:
        """Persist a new Edge. Validates source/target exist and triple uniqueness."""
        raise NotImplementedError

    def get(self, source_id: str, target_id: str, edge_type: str) -> Optional[Edge]:
        """Get a specific Edge by its identity triple."""
        raise NotImplementedError

    def get_outgoing(self, node_id: str, edge_type: Optional[str] = None) -> List[Edge]:
        """Get all outgoing Edges from a Node."""
        raise NotImplementedError

    def get_incoming(self, node_id: str, edge_type: Optional[str] = None) -> List[Edge]:
        """Get all incoming Edges to a Node."""
        raise NotImplementedError

    def get_all(self, node_id: str) -> List[Edge]:
        """Get all Edges (outgoing + incoming) for a Node."""
        raise NotImplementedError

    def remove(self, source_id: str, target_id: str, edge_type: str) -> bool:
        """Remove a specific Edge. Returns True if it existed."""
        raise NotImplementedError

    def count(self, edge_type: Optional[str] = None) -> int:
        """Count Edges, optionally filtered by type."""
        raise NotImplementedError

    def all(self) -> List[Edge]:
        """Get all Edges in the store."""
        raise NotImplementedError


# ---------------------------------------------------------------------------
# InMemoryEdgeStore — thread-safe in-memory implementation
# ---------------------------------------------------------------------------

class InMemoryEdgeStore(EdgeStore):
    """In-memory Edge store for development and testing.

    Thread-safe via RLock.
    Indexed by source, target, and triple for O(1) lookups.
    Validates Edge creation rules from §3.2 and §3.4.
    """

    def __init__(self, node_store: Optional[NodeStore] = None):
        self._edges: Dict[Tuple[str, str, str], Edge] = {}
        self._source_index: Dict[str, Set[Tuple[str, str, str]]] = {}
        self._target_index: Dict[str, Set[Tuple[str, str, str]]] = {}
        self._node_store: NodeStore = node_store or get_node_store()
        self._lock = threading.RLock()

    # ---- Core CRUD ----------------------------------------------------------

    def create(self, edge: Edge) -> Edge:
        """Persist a new Edge with validation (§3.2, §3.4).

        Raises:
            ValueError: If source or target Node does not exist
            ValueError: If a duplicate triple already exists
        """
        with self._lock:
            # §3.4.1 — Source Node must exist
            if not self._node_store.exists(edge.source_id):
                raise ValueError(
                    f"Source Node '{edge.short_source}' not found in graph. "
                    "Every Edge must have a valid source Node (§3.2.1)."
                )
            # §3.4.2 — Target Node must exist
            if not self._node_store.exists(edge.target_id):
                raise ValueError(
                    f"Target Node '{edge.short_target}' not found in graph. "
                    "Every Edge must have a valid target Node (§3.2.1)."
                )
            # §3.4.3 — No duplicate triple
            if edge.triple in self._edges:
                raise ValueError(
                    f"Duplicate Edge triple ({edge.short_source}, "
                    f"{edge.short_target}, {edge.edge_type}). "
                    "No two Edges may share the same triple (§3.2.3)."
                )

            self._edges[edge.triple] = edge
            self._source_index.setdefault(edge.source_id, set()).add(edge.triple)
            self._target_index.setdefault(edge.target_id, set()).add(edge.triple)
            return edge

    def get(self, source_id: str, target_id: str, edge_type: str) -> Optional[Edge]:
        triple = (source_id, target_id, edge_type)
        with self._lock:
            return self._edges.get(triple)

    def get_outgoing(self, node_id: str, edge_type: Optional[str] = None) -> List[Edge]:
        with self._lock:
            triples = self._source_index.get(node_id, set())
            return self._filter_by_type(triples, edge_type)

    def get_incoming(self, node_id: str, edge_type: Optional[str] = None) -> List[Edge]:
        with self._lock:
            triples = self._target_index.get(node_id, set())
            return self._filter_by_type(triples, edge_type)

    def get_all(self, node_id: str) -> List[Edge]:
        with self._lock:
            triples = (self._source_index.get(node_id, set())
                       | self._target_index.get(node_id, set()))
            return [self._edges[t] for t in triples if t in self._edges]

    def remove(self, source_id: str, target_id: str, edge_type: str) -> bool:
        triple = (source_id, target_id, edge_type)
        with self._lock:
            edge = self._edges.pop(triple, None)
            if edge is None:
                return False
            # Clean indexes
            src_set = self._source_index.get(source_id)
            if src_set:
                src_set.discard(triple)
                if not src_set:
                    del self._source_index[source_id]
            tgt_set = self._target_index.get(target_id)
            if tgt_set:
                tgt_set.discard(triple)
                if not tgt_set:
                    del self._target_index[target_id]
            return True

    def count(self, edge_type: Optional[str] = None) -> int:
        with self._lock:
            if edge_type:
                return sum(
                    1 for e in self._edges.values()
                    if e.edge_type == edge_type
                )
            return len(self._edges)

    def all(self) -> List[Edge]:
        with self._lock:
            return list(self._edges.values())

    # ---- Internal -----------------------------------------------------------

    def _filter_by_type(self, triples: Set[Tuple[str, str, str]],
                        edge_type: Optional[str] = None) -> List[Edge]:
        """Filter edges by type from a set of triples."""
        result = [self._edges[t] for t in triples if t in self._edges]
        if edge_type:
            result = [e for e in result if e.edge_type == edge_type]
        return result

    # ---- Testing helpers ----------------------------------------------------

    def clear(self) -> None:
        with self._lock:
            self._edges.clear()
            self._source_index.clear()
            self._target_index.clear()


# ---------------------------------------------------------------------------
# Singleton
# ---------------------------------------------------------------------------

_GLOBAL_EDGE_STORE: Optional[InMemoryEdgeStore] = None


def get_edge_store() -> InMemoryEdgeStore:
    """Get the global EdgeStore singleton."""
    global _GLOBAL_EDGE_STORE
    if _GLOBAL_EDGE_STORE is None:
        _GLOBAL_EDGE_STORE = InMemoryEdgeStore(node_store=get_node_store())
    return _GLOBAL_EDGE_STORE


def reset_edge_store() -> None:
    """Reset the global EdgeStore (for testing)."""
    global _GLOBAL_EDGE_STORE
    if _GLOBAL_EDGE_STORE:
        _GLOBAL_EDGE_STORE.clear()
    _GLOBAL_EDGE_STORE = None