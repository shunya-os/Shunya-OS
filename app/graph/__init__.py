"""SHUNYA Knowledge Graph — Core Graph Package.

The Knowledge Graph is the canonical representation of how everything
in SHUNYA connects. Every Node and Edge is stored here.

Architecture references:
    UNIVERSAL_KNOWLEDGE_GRAPH_ARCHITECTURE.md §1 — Graph Architecture
    UNIVERSAL_KNOWLEDGE_GRAPH_ARCHITECTURE.md §1.1 — Graph primitives
    UNIVERSAL_KNOWLEDGE_GRAPH_ARCHITECTURE.md §1.2 — Node structure
    UNIVERSAL_KNOWLEDGE_GRAPH_ARCHITECTURE.md §1.3 — Edge structure
    UNIVERSAL_KNOWLEDGE_GRAPH_ARCHITECTURE.md §1.4 — Identity

Constitutional rules:
    The Graph builds on the Kernel (imports from app.kernel).
    The Kernel must never depend on the Graph.
"""

from app.graph.node import (
    Node, NodeStore, InMemoryNodeStore,
    NodeStatus, VisibilityLevel,
    get_node_store, reset_node_store,
)
from app.graph.edge import (
    Edge, EdgeStore, InMemoryEdgeStore,
    EdgeDirection, EdgeStatus,
    get_edge_store, reset_edge_store,
)
from app.graph.families import (
    Families, NodeFamily, EdgeFamily,
    ALL_NODE_FAMILIES, ALL_EDGE_FAMILIES, ALL_EDGE_TYPES,
)
from app.graph.temporal import (
    TemporalStore, TemporalEdgeType,
    get_temporal_store, reset_temporal_store,
)

__all__ = [
    # Node
    "Node", "NodeStore", "InMemoryNodeStore",
    "NodeStatus", "VisibilityLevel",
    "get_node_store", "reset_node_store",
    # Edge
    "Edge", "EdgeStore", "InMemoryEdgeStore",
    "EdgeDirection", "EdgeStatus",
    "get_edge_store", "reset_edge_store",
    # Families
    "Families", "NodeFamily", "EdgeFamily",
    "ALL_NODE_FAMILIES", "ALL_EDGE_FAMILIES", "ALL_EDGE_TYPES",
    # Temporal
    "TemporalStore", "TemporalEdgeType",
    "get_temporal_store", "reset_temporal_store",
]