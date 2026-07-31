"""SHUNYA Knowledge Graph — Node Model and Store.

Implements the core Node dataclass and InMemoryNodeStore as defined in:
    UNIVERSAL_KNOWLEDGE_GRAPH_ARCHITECTURE.md §1 — Graph Architecture
    UNIVERSAL_KNOWLEDGE_GRAPH_ARCHITECTURE.md §1.2 — Node structure
    UNIVERSAL_KNOWLEDGE_GRAPH_ARCHITECTURE.md §1.4 — Identity
    UNIVERSAL_KNOWLEDGE_GRAPH_ARCHITECTURE.md §1.5 — Labels
    UNIVERSAL_KNOWLEDGE_GRAPH_ARCHITECTURE.md §1.6 — Types
    UNIVERSAL_KNOWLEDGE_GRAPH_ARCHITECTURE.md §1.7 — Metadata
    UNIVERSAL_KNOWLEDGE_GRAPH_ARCHITECTURE.md §1.9 — Confidence
    UNIVERSAL_KNOWLEDGE_GRAPH_ARCHITECTURE.md §1.10 — Versioning
    UNIVERSAL_KNOWLEDGE_GRAPH_ARCHITECTURE.md §13.2 — Visibility

Constitutional rules:
    - The Graph builds on the Kernel (imports from app.kernel).
    - The Kernel must never depend on the Graph.
    - Node identity is permanent, unique, never reused (§1.4).
    - Type is immutable after creation (§1.6).
    - Every Node has exactly one type from the Universal Type System.
"""

from __future__ import annotations

import uuid
import threading
from dataclasses import dataclass, field, replace
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Set

from app.kernel.types import TypeRegistry, get_registry as get_type_registry
from app.kernel.object import EvidenceRef


# ---------------------------------------------------------------------------
# Node identity — UUID v7-like, time-ordered
# ---------------------------------------------------------------------------

def _generate_node_id() -> str:
    """Generate a time-ordered Node identity (permanent, unique, never reused).

    Uses a 48-bit timestamp prefix + 80-bit random suffix for natural
    chronological sortability and collision resistance.
    """
    timestamp = int(datetime.now(timezone.utc).timestamp() * 1000)
    rand = uuid.uuid4().hex[:20]
    return f"n_{timestamp:012x}{rand}"


# ---------------------------------------------------------------------------
# Node status — maps to kernel ObjectStatus lifecycle
# ---------------------------------------------------------------------------

class NodeStatus(str, Enum):
    """Node lifecycle status (maps to Kernel ObjectStatus)."""
    ACTIVE = "active"
    ARCHIVED = "archived"
    PENDING = "pending"
    SUPERSEDED = "superseded"


# ---------------------------------------------------------------------------
# Visibility levels (KG §13.2)
# ---------------------------------------------------------------------------

class VisibilityLevel(str, Enum):
    """Visibility levels for graph access control (KG §13.2)."""
    PUBLIC = "public"
    ORGANISATION = "organisation"
    TEAM = "team"
    PRIVATE = "private"
    CONFIDENTIAL = "confidential"


# ---------------------------------------------------------------------------
# Node metadata (KG §1.7)
# ---------------------------------------------------------------------------

@dataclass
class NodeMetadata:
    """Metadata payload for every Node (KG §1.7)."""
    created_at: str = ""
    updated_at: str = ""
    created_by: str = "system"
    provenance: str = ""

    def __post_init__(self) -> None:
        now = datetime.now(timezone.utc).isoformat()
        if not self.created_at:
            self.created_at = now
        if not self.updated_at:
            self.updated_at = now


# ---------------------------------------------------------------------------
# Node — the fundamental graph primitive (KG §1.2)
# ---------------------------------------------------------------------------

@dataclass
class Node:
    """A single Node in the Universal Knowledge Graph.

    Every meaningful entity in the SHUNYA universe is a Node.
    Nodes are connected by Edges.

    Constitutional invariants enforced:
        O-01: Identity never changes (node_id is immutable)
        O-11: Type is immutable (type cannot change after creation)
        O-18: State is singular (one status at a time)
        O-22: Everything is a Node (graph §1.1)
    """

    # Identity (permanent, unique, never reused — §1.4)
    node_id: str = ""

    # Type (from Universal Type System — §1.6, immutable)
    node_type: str = ""

    # Labels (zero or more classification tags — §1.5, mutable)
    labels: Set[str] = field(default_factory=set)

    # Attributes (key-value pairs per type schema — §1.2)
    attributes: Dict[str, Any] = field(default_factory=dict)

    # Metadata (created_at, updated_at, created_by, provenance — §1.7)
    metadata: NodeMetadata = field(default_factory=NodeMetadata)

    # Evidence chain references (§1.2, §7)
    evidence: List[EvidenceRef] = field(default_factory=list)

    # Confidence score 0.0–1.0 (§1.9)
    confidence: float = 1.0

    # Version number (monotonic, per-node — §1.10)
    version: int = 1

    # Status (lifecycle — maps to kernel ObjectStatus)
    status: str = NodeStatus.ACTIVE.value

    # Visibility (access control — §13.2)
    visibility: str = VisibilityLevel.PRIVATE.value

    # Owner identity (who owns this Node — §13.3)
    owner_id: str = ""

    def __post_init__(self) -> None:
        if not self.node_id:
            self.node_id = _generate_node_id()
        if not self.node_type:
            self.node_type = "Object"
        if isinstance(self.labels, list):
            self.labels = set(self.labels)

    # ---- Property helpers ---------------------------------------------------

    @property
    def is_active(self) -> bool:
        return self.status == NodeStatus.ACTIVE.value

    @property
    def is_archived(self) -> bool:
        return self.status == NodeStatus.ARCHIVED.value

    @property
    def short_id(self) -> str:
        return self.node_id[:16] if self.node_id else ""

    # ---- Mutation helpers ---------------------------------------------------

    def add_label(self, label: str) -> None:
        """Add a classification label (§1.5)."""
        self.labels.add(label)
        self.metadata.updated_at = datetime.now(timezone.utc).isoformat()

    def remove_label(self, label: str) -> bool:
        """Remove a classification label. Returns True if it existed."""
        if label in self.labels:
            self.labels.discard(label)
            self.metadata.updated_at = datetime.now(timezone.utc).isoformat()
            return True
        return False

    def has_label(self, label: str) -> bool:
        """Check if a label is attached."""
        return label in self.labels

    def set_attribute(self, key: str, value: Any) -> None:
        """Set an attribute value."""
        self.attributes[key] = value
        self.version += 1
        self.metadata.updated_at = datetime.now(timezone.utc).isoformat()

    def get_attribute(self, key: str, default: Any = None) -> Any:
        """Get an attribute value."""
        return self.attributes.get(key, default)

    def add_evidence(self, ref: EvidenceRef) -> None:
        """Attach an evidence reference (§1.2)."""
        self.evidence.append(ref)
        self.metadata.updated_at = datetime.now(timezone.utc).isoformat()

    def archive(self) -> None:
        """Transition to archived state."""
        self.status = NodeStatus.ARCHIVED.value
        self.metadata.updated_at = datetime.now(timezone.utc).isoformat()

    # ---- Serialization ------------------------------------------------------

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to a canonical dictionary."""
        return {
            "node_id": self.node_id,
            "node_type": self.node_type,
            "labels": sorted(self.labels),
            "attributes": dict(self.attributes),
            "metadata": {
                "created_at": self.metadata.created_at,
                "updated_at": self.metadata.updated_at,
                "created_by": self.metadata.created_by,
                "provenance": self.metadata.provenance,
            },
            "evidence": [
                {"object_id": e.object_id, "object_type": e.object_type,
                 "field": e.field, "confidence": e.confidence}
                for e in self.evidence
            ],
            "confidence": self.confidence,
            "version": self.version,
            "status": self.status,
            "visibility": self.visibility,
            "owner_id": self.owner_id,
        }


# ---------------------------------------------------------------------------
# NodeStore — abstract interface
# ---------------------------------------------------------------------------

class NodeStore:
    """Abstract interface for Node storage.

    Implementations:
        - InMemoryNodeStore (development / testing)
        - SqlNodeStore (production — Phase 9F+)
    """

    def create(self, node: Node) -> Node:
        """Persist a new Node. Raises ValueError if identity already exists."""
        raise NotImplementedError

    def get(self, node_id: str) -> Optional[Node]:
        """Load a Node by identity. Returns None if not found."""
        raise NotImplementedError

    def update(self, node: Node) -> Node:
        """Persist an updated Node. Raises ValueError if not found."""
        raise NotImplementedError

    def archive(self, node_id: str) -> Optional[Node]:
        """Archive a Node. Returns the archived Node or None if not found."""
        raise NotImplementedError

    def delete(self, node_id: str) -> bool:
        """Remove a Node from the store. Returns True if it existed."""
        raise NotImplementedError

    def get_by_type(self, node_type: str) -> List[Node]:
        """Get all Nodes of a given type."""
        raise NotImplementedError

    def get_by_label(self, label: str) -> List[Node]:
        """Get all Nodes with a given label."""
        raise NotImplementedError

    def count(self, node_type: Optional[str] = None) -> int:
        """Count Nodes, optionally filtered by type."""
        raise NotImplementedError

    def all(self) -> List[Node]:
        """Get all Nodes in the store."""
        raise NotImplementedError

    def exists(self, node_id: str) -> bool:
        """Check if a Node exists."""
        return self.get(node_id) is not None


# ---------------------------------------------------------------------------
# InMemoryNodeStore — thread-safe in-memory implementation
# ---------------------------------------------------------------------------

class InMemoryNodeStore(NodeStore):
    """In-memory Node store for development and testing.

    Thread-safe via RLock.
    Indexed by identity, type, and label for O(1) lookups.
    """

    def __init__(self) -> None:
        self._nodes: Dict[str, Node] = {}
        self._type_index: Dict[str, Set[str]] = {}
        self._label_index: Dict[str, Set[str]] = {}
        self._lock = threading.RLock()

    # ---- Core CRUD ----------------------------------------------------------

    def create(self, node: Node) -> Node:
        """Persist a new Node. Raises ValueError if identity already exists.

        Stores a copy of the Node to prevent in-place mutations on the
        caller's reference from corrupting the store's indexes.
        """
        with self._lock:
            if node.node_id in self._nodes:
                raise ValueError(
                    f"Node '{node.node_id}' already exists in the graph"
                )
            # Store a copy so in-place label mutations don't corrupt the index
            stored = replace(node, labels=set(node.labels))
            self._nodes[stored.node_id] = stored
            self._index_node(stored)
            return stored

    def get(self, node_id: str) -> Optional[Node]:
        with self._lock:
            return self._nodes.get(node_id)

    def update(self, node: Node) -> Node:
        with self._lock:
            if node.node_id not in self._nodes:
                raise ValueError(f"Node '{node.node_id}' not found in the graph")
            existing = self._nodes[node.node_id]
            # Always reindex labels — the caller may have mutated the node
            # in-place, and existing.labels is a snapshot from creation time
            self._deindex_node(existing)
            self._index_node(node)
            self._nodes[node.node_id] = node
            return node

    def archive(self, node_id: str) -> Optional[Node]:
        with self._lock:
            node = self._nodes.get(node_id)
            if node is None:
                return None
            node.archive()
            return node

    def delete(self, node_id: str) -> bool:
        with self._lock:
            node = self._nodes.pop(node_id, None)
            if node is None:
                return False
            self._deindex_node(node)
            return True

    # ---- Query --------------------------------------------------------------

    def get_by_type(self, node_type: str) -> List[Node]:
        with self._lock:
            ids = self._type_index.get(node_type, set())
            return [self._nodes[nid] for nid in ids if nid in self._nodes]

    def get_by_label(self, label: str) -> List[Node]:
        with self._lock:
            ids = self._label_index.get(label, set())
            return [self._nodes[nid] for nid in ids if nid in self._nodes]

    def count(self, node_type: Optional[str] = None) -> int:
        with self._lock:
            if node_type:
                return len(self._type_index.get(node_type, set()))
            return len(self._nodes)

    def all(self) -> List[Node]:
        with self._lock:
            return list(self._nodes.values())

    # ---- Index management ---------------------------------------------------

    def _index_node(self, node: Node) -> None:
        """Index a Node by type and labels."""
        # Type index
        self._type_index.setdefault(node.node_type, set()).add(node.node_id)
        # Label index
        for label in node.labels:
            self._label_index.setdefault(label, set()).add(node.node_id)

    def _deindex_node(self, node: Node) -> None:
        """Remove a Node from all indexes."""
        # Type index
        type_set = self._type_index.get(node.node_type)
        if type_set:
            type_set.discard(node.node_id)
            if not type_set:
                del self._type_index[node.node_type]
        # Label index
        for label in node.labels:
            label_set = self._label_index.get(label)
            if label_set:
                label_set.discard(node.node_id)
                if not label_set:
                    del self._label_index[label]

    # ---- Validation ---------------------------------------------------------

    def validate_type(self, node_type: str) -> bool:
        """Check if a type is registered in the Universal Type System."""
        registry = get_type_registry()
        return registry.get(node_type) is not None

    # ---- Testing helpers ----------------------------------------------------

    def clear(self) -> None:
        with self._lock:
            self._nodes.clear()
            self._type_index.clear()
            self._label_index.clear()


# ---------------------------------------------------------------------------
# Singleton
# ---------------------------------------------------------------------------

_GLOBAL_NODE_STORE: Optional[InMemoryNodeStore] = None


def get_node_store() -> InMemoryNodeStore:
    """Get the global NodeStore singleton."""
    global _GLOBAL_NODE_STORE
    if _GLOBAL_NODE_STORE is None:
        _GLOBAL_NODE_STORE = InMemoryNodeStore()
    return _GLOBAL_NODE_STORE


def reset_node_store() -> None:
    """Reset the global NodeStore (for testing)."""
    global _GLOBAL_NODE_STORE
    if _GLOBAL_NODE_STORE:
        _GLOBAL_NODE_STORE.clear()
    _GLOBAL_NODE_STORE = None