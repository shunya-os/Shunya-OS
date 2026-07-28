"""
SHUNYA Explainable Intelligence — Provenance Chain Model

Every statement SHUNYA makes must be traceable back through a complete
reasoning chain. This module defines the provenance data model.

Chain:
  Source Object
    → Observed Event
      → Evidence
        → Observation
          → Relationship Graph
            → Reasoning
              → Insight
                → Recommendation
                  → Presentation

Each node preserves references to the previous layer.
No broken chains.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional


# ─── Node types ───

NODE_SOURCE = "source_object"
NODE_EVENT = "observed_event"
NODE_EVIDENCE = "evidence"
NODE_OBSERVATION = "observation"
NODE_RELATIONSHIP = "relationship_graph"
NODE_REASONING = "reasoning"
NODE_INSIGHT = "insight"
NODE_RECOMMENDATION = "recommendation"
NODE_PRESENTATION = "presentation"

VALID_NODE_TYPES = frozenset({
    NODE_SOURCE, NODE_EVENT, NODE_EVIDENCE, NODE_OBSERVATION,
    NODE_RELATIONSHIP, NODE_REASONING, NODE_INSIGHT,
    NODE_RECOMMENDATION, NODE_PRESENTATION,
})

CHAIN_ORDER = [
    NODE_SOURCE, NODE_EVENT, NODE_EVIDENCE, NODE_OBSERVATION,
    NODE_RELATIONSHIP, NODE_REASONING, NODE_INSIGHT,
    NODE_RECOMMENDATION, NODE_PRESENTATION,
]


@dataclass
class ProvenanceNode:
    """A single node in a provenance chain.

    Each node represents one layer of the explainability chain.
    The node_type indicates which layer this is.
    """

    node_id: str
    node_type: str
    label: str
    content: str
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    parent_id: Optional[str] = None
    confidence: float = 1.0
    metadata: dict = field(default_factory=dict)

    def __post_init__(self):
        if self.node_type not in VALID_NODE_TYPES:
            raise ValueError(
                f"Invalid node_type '{self.node_type}'. "
                f"Must be one of: {', '.join(sorted(VALID_NODE_TYPES))}"
            )
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError(
                f"Confidence must be between 0.0 and 1.0, got {self.confidence}"
            )

    def to_dict(self) -> dict:
        return {
            "node_id": self.node_id,
            "node_type": self.node_type,
            "label": self.label,
            "content": self.content,
            "timestamp": self.timestamp.isoformat(),
            "parent_id": self.parent_id,
            "confidence": self.confidence,
            "metadata": self.metadata,
        }


class ProvenanceChain:
    """A complete provenance chain from source object to presentation.

    Maintains a DAG of nodes that can be walked from any leaf back to root.
    """

    def __init__(self, chain_id: str):
        self.chain_id = chain_id
        self._nodes: dict[str, ProvenanceNode] = {}
        self._root_id: Optional[str] = None
        self._leaf_id: Optional[str] = None

    def add_node(self, node: ProvenanceNode) -> ProvenanceNode:
        """Add a node to the chain. Returns the node for chaining."""
        if node.node_id in self._nodes:
            raise ValueError(f"Node {node.node_id} already exists in chain {self.chain_id}")
        self._nodes[node.node_id] = node
        if node.parent_id is None:
            self._root_id = node.node_id
        self._leaf_id = node.node_id
        return node

    def get_node(self, node_id: str) -> Optional[ProvenanceNode]:
        return self._nodes.get(node_id)

    @property
    def root(self) -> Optional[ProvenanceNode]:
        if self._root_id:
            return self._nodes.get(self._root_id)
        return None

    @property
    def leaf(self) -> Optional[ProvenanceNode]:
        if self._leaf_id:
            return self._nodes.get(self._leaf_id)
        return None

    def resolve(self, node_id: str) -> list[ProvenanceNode]:
        """Walk backwards from a node to the root, returning the chain."""
        chain: list[ProvenanceNode] = []
        current = self._nodes.get(node_id)
        while current:
            chain.append(current)
            current = self._nodes.get(current.parent_id) if current.parent_id else None
        return chain

    def resolve_forward(self, node_id: str) -> list[ProvenanceNode]:
        """Walk forwards from a node to the leaf, returning the chain."""
        chain: list[ProvenanceNode] = []
        # Build reverse index: parent_id -> children
        children: dict[str, list[str]] = {}
        for nid, node in self._nodes.items():
            if node.parent_id:
                children.setdefault(node.parent_id, []).append(nid)

        current_id: Optional[str] = node_id
        while current_id:
            node = self._nodes.get(current_id)
            if node:
                chain.append(node)
            child_ids = children.get(current_id, [])
            current_id = child_ids[0] if child_ids else None
        return chain

    def verify_integrity(self) -> list[str]:
        """Verify no broken chains. Returns list of issues (empty = intact)."""
        issues: list[str] = []
        if not self._nodes:
            issues.append("Chain is empty")
            return issues

        # Check root exists
        if self._root_id is None:
            issues.append("No root node found (no node with parent_id=None)")
        elif self._root_id not in self._nodes:
            issues.append(f"Root node {self._root_id} not found in nodes")

        # Check every parent reference exists
        for nid, node in self._nodes.items():
            if node.parent_id is not None and node.parent_id not in self._nodes:
                issues.append(
                    f"Node {nid} references parent {node.parent_id} which does not exist"
                )

        # Check no orphaned leaf
        if self._leaf_id is not None and self._leaf_id not in self._nodes:
            issues.append(f"Leaf node {self._leaf_id} not found in nodes")

        return issues

    @property
    def is_intact(self) -> bool:
        return len(self.verify_integrity()) == 0

    @property
    def node_count(self) -> int:
        return len(self._nodes)

    def to_dict(self) -> dict:
        return {
            "chain_id": self.chain_id,
            "root_id": self._root_id,
            "leaf_id": self._leaf_id,
            "node_count": self.node_count,
            "is_intact": self.is_intact,
            "nodes": [n.to_dict() for n in self._nodes.values()],
        }


class ProvenanceStore:
    """In-memory store of provenance chains.

    In production, this would be backed by a database.
    The interface is designed to be swappable.
    """

    def __init__(self):
        self._chains: dict[str, ProvenanceChain] = {}

    def add_chain(self, chain: ProvenanceChain) -> None:
        self._chains[chain.chain_id] = chain

    def get_chain(self, chain_id: str) -> Optional[ProvenanceChain]:
        return self._chains.get(chain_id)

    def resolve_statement(self, statement_id: str) -> Optional[list[ProvenanceNode]]:
        """Find which chain contains this statement and resolve it."""
        for chain in self._chains.values():
            node = chain.get_node(statement_id)
            if node:
                return chain.resolve(statement_id)
        return None

    def all_issues(self) -> dict[str, list[str]]:
        """Verify integrity of all chains."""
        return {
            cid: chain.verify_integrity()
            for cid, chain in self._chains.items()
        }

    @property
    def chain_count(self) -> int:
        return len(self._chains)

    def clear(self) -> None:
        self._chains.clear()


# ─── Global store (singleton pattern) ───
_store: Optional[ProvenanceStore] = None


def get_store() -> ProvenanceStore:
    """Get or create the global provenance store."""
    global _store
    if _store is None:
        _store = ProvenanceStore()
    return _store


def reset_store() -> None:
    """Reset the global store (for testing)."""
    global _store
    _store = None