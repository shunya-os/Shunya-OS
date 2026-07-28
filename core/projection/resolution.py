"""Context Resolution — resolve surrounding graph context for a given object.

Context Resolution provides the Knowledge Graph neighbourhood that feeds
Workspace and Relationship projections. It is a pure data assembly layer —
it defines the shape of context but does not query the graph directly.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import ClassVar

from .types import (
    EdgeView,
    EvidenceView,
    NodeView,
    ProjectionType,
    TemporalScope,
)


@dataclass
class ResolutionContext:
    """The assembled context around a focal object."""

    context_id: str = ""
    root_node: NodeView | None = None
    surrounding_nodes: list[NodeView] = field(default_factory=list)
    edges: list[EdgeView] = field(default_factory=list)
    evidence: list[EvidenceView] = field(default_factory=list)
    depth: int = 1
    max_nodes: int = 50
    confidence_min: float = 0.3
    temporal_scope: str = TemporalScope.CURRENT.value
    node_types: list[str] = field(default_factory=list)
    timestamp: str = ""

    def __post_init__(self) -> None:
        if not self.context_id:
            self.context_id = uuid.uuid4().hex[:12]
        if not self.timestamp:
            self.timestamp = datetime.now(timezone.utc).isoformat()

    @property
    def total_nodes(self) -> int:
        """Total nodes in this context (root + surrounding)."""
        return (1 if self.root_node else 0) + len(self.surrounding_nodes)


@dataclass
class ResolutionParams:
    """Parameters that control context resolution behaviour."""

    depth: int = 1
    max_nodes: int = 50
    confidence_min: float = 0.3
    temporal_scope: str = TemporalScope.CURRENT.value
    node_types: list[str] = field(default_factory=list)


class ContextResolver:
    """Pure context resolution logic.

    This class defines the *shape* of context resolution — the parameters,
    the structural model, and the filtering rules. Actual graph traversal
    is delegated to the caller (ProjectionEngine) which has access to the
    Knowledge Graph.
    """

    # Default resolution parameters per projection type
    # (depth, max_nodes, confidence_min)
    DEFAULTS: ClassVar[dict[ProjectionType, ResolutionParams]] = {
        ProjectionType.WORKSPACE: ResolutionParams(depth=1, max_nodes=50, confidence_min=0.3),
        ProjectionType.CONVERSATION: ResolutionParams(depth=0, max_nodes=200, confidence_min=0.0),
        ProjectionType.EXECUTION: ResolutionParams(depth=0, max_nodes=100, confidence_min=0.1),
        ProjectionType.MEETING: ResolutionParams(depth=1, max_nodes=100, confidence_min=0.0),
        ProjectionType.RELATIONSHIP: ResolutionParams(depth=2, max_nodes=200, confidence_min=0.3),
        ProjectionType.TIMELINE: ResolutionParams(depth=0, max_nodes=500, confidence_min=0.0),
        ProjectionType.EVIDENCE: ResolutionParams(depth=0, max_nodes=100, confidence_min=0.0),
        ProjectionType.PREDICTION: ResolutionParams(depth=0, max_nodes=50, confidence_min=0.0),
        ProjectionType.COMMITMENT: ResolutionParams(depth=0, max_nodes=50, confidence_min=0.0),
        ProjectionType.SEARCH: ResolutionParams(depth=0, max_nodes=100, confidence_min=0.0),
    }

    def get_params(self, projection_type: ProjectionType) -> ResolutionParams:
        """Return the default resolution parameters for a projection type."""
        return self.DEFAULTS.get(projection_type, ResolutionParams())

    def build_resolution_context(
        self,
        root_node: NodeView,
        surrounding_nodes: list[NodeView] | None = None,
        edges: list[EdgeView] | None = None,
        evidence: list[EvidenceView] | None = None,
        params: ResolutionParams | None = None,
    ) -> ResolutionContext:
        """Assemble a ResolutionContext from raw graph data.

        Args:
            root_node: The focal NodeView.
            surrounding_nodes: 1-hop (or 2-hop) neighbours.
            edges: Edges connecting the root to surrounding nodes.
            evidence: Evidence items associated with the root.
            params: Resolution parameters (used to populate metadata).

        Returns a fully populated ResolutionContext.
        """
        p = params or ResolutionParams()
        return ResolutionContext(
            root_node=root_node,
            surrounding_nodes=sorted(
                (surrounding_nodes or []),
                key=lambda n: n.confidence,
                reverse=True,
            )[: p.max_nodes],
            edges=(edges or [])[: p.max_nodes * 2],
            evidence=sorted(
                (evidence or []),
                key=lambda e: e.confidence,
                reverse=True,
            )[: p.max_nodes],
            depth=p.depth,
            max_nodes=p.max_nodes,
            confidence_min=p.confidence_min,
            temporal_scope=p.temporal_scope,
            node_types=(
                [t.strip() for t in p.node_types] if p.node_types else []
            ),
        )


__all__ = [
    "ContextResolver",
    "ResolutionContext",
    "ResolutionParams",
]