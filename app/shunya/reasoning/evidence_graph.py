"""SHUNYA — Reasoning Engine: Evidence Graph (Phase F — Canonical).

Evidence chaining linking every reasoning result back to:
  - WorkspaceContext
  - Identity
  - Knowledge objects
  - Source references

Every conclusion is explainable via its chain of evidence references.

Architectural authority: G5.7 — Canonical Phase F Architecture Decision
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from app.shunya.reasoning.models import (
    Contradiction, EvidenceReference, Finding, ReasoningResult,
)


# ---------------------------------------------------------------------------
# Evidence Node
# ---------------------------------------------------------------------------


@dataclass
class EvidenceNode:
    """A single node in the evidence graph."""

    node_id: str = ""
    node_type: str = ""  # "source", "finding", "contradiction", "assumption", "constraint"
    label: str = ""
    confidence: float = 1.0
    references: List[EvidenceReference] = field(default_factory=list)
    children: List[str] = field(default_factory=list)
    parent_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Evidence Graph
# ---------------------------------------------------------------------------


class EvidenceGraph:
    """Evidence chaining for the Reasoning Engine."""

    def __init__(self) -> None:
        self._nodes: Dict[str, EvidenceNode] = {}
        self._edges: List[tuple] = []

    def add_reasoning_result(self, result: ReasoningResult) -> None:
        root = EvidenceNode(
            node_id=result.result_id,
            node_type="reasoning_result",
            label=f"Reasoning Result {result.result_id[:8]}",
            confidence=result.confidence.overall_score if result.confidence else 0.0,
        )
        self._add_node(root)

        for f in result.findings:
            node = EvidenceNode(
                node_id=f.finding_id, node_type="finding",
                label=f.label or f.fact_key, confidence=f.confidence,
                references=f.evidence, parent_id=root.node_id,
                metadata={"finding_type": f.finding_type, "severity": f.severity},
            )
            self._add_node(node)
            self._add_edge(root.node_id, node.node_id)

        for c in result.contradictions:
            node = EvidenceNode(
                node_id=c.contradiction_id, node_type="contradiction",
                label=c.label, confidence=0.0, references=c.evidence,
                parent_id=root.node_id,
                metadata={"contradiction_type": c.contradiction_type, "severity": c.severity},
            )
            self._add_node(node)
            self._add_edge(root.node_id, node.node_id)

        for a in result.assumptions:
            node = EvidenceNode(
                node_id=a.assumption_id, node_type="assumption",
                label=a.label or a.fact_key, confidence=0.0,
                references=a.evidence, parent_id=root.node_id,
            )
            self._add_node(node)
            self._add_edge(root.node_id, node.node_id)

        for ct in result.constraints:
            node = EvidenceNode(
                node_id=ct.constraint_id, node_type="constraint",
                label=ct.label or ct.fact_key, confidence=0.0,
                references=ct.evidence, parent_id=root.node_id,
                metadata={"constraint_type": ct.constraint_type},
            )
            self._add_node(node)
            self._add_edge(root.node_id, node.node_id)

    def get_node(self, node_id: str) -> Optional[EvidenceNode]:
        return self._nodes.get(node_id)

    def get_children(self, node_id: str) -> List[EvidenceNode]:
        children: List[EvidenceNode] = []
        for source, target in self._edges:
            if source == node_id:
                child = self._nodes.get(target)
                if child:
                    children.append(child)
        return children

    def get_parent(self, node_id: str) -> Optional[EvidenceNode]:
        node = self._nodes.get(node_id)
        if node and node.parent_id:
            return self._nodes.get(node.parent_id)
        return None

    def get_path_to_source(self, node_id: str) -> List[EvidenceNode]:
        path: List[EvidenceNode] = []
        current = self._nodes.get(node_id)
        while current:
            path.append(current)
            parent_id = current.parent_id
            current = self._nodes.get(parent_id) if parent_id else None
        return path

    def explain(self, node_id: str) -> str:
        path = self.get_path_to_source(node_id)
        if not path:
            return f"No evidence path found for node {node_id}"
        parts: List[str] = []
        for i, node in enumerate(reversed(path)):
            indent = "  " * i
            parts.append(f"{indent}- {node.node_type}: {node.label} (confidence: {node.confidence})")
            if node.references:
                for ref in node.references:
                    src = ref.source_name or ref.source_uri or "unknown"
                    parts.append(f"{indent}  \u251c evidence: {ref.reference_type} from {src}")
        return "\n".join(parts)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "nodes": {nid: {"node_type": n.node_type, "label": n.label,
                            "confidence": n.confidence,
                            "references": [r.to_dict() for r in n.references],
                            "children": n.children, "parent_id": n.parent_id}
                      for nid, n in self._nodes.items()},
            "edges": [(s, t) for s, t in self._edges],
            "node_count": len(self._nodes),
            "edge_count": len(self._edges),
        }

    @property
    def node_count(self) -> int:
        return len(self._nodes)

    @property
    def edge_count(self) -> int:
        return len(self._edges)

    def _add_node(self, node: EvidenceNode) -> None:
        self._nodes[node.node_id] = node

    def _add_edge(self, source_id: str, target_id: str) -> None:
        self._edges.append((source_id, target_id))
        parent = self._nodes.get(source_id)
        if parent and target_id not in parent.children:
            parent.children.append(target_id)