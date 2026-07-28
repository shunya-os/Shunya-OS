"""Projection Engine — type definitions and view models.

The Projection Engine transforms raw graph state into structured,
filtered projections that the workspace renders. The workspace never
queries the graph directly — it receives projections.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any

# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


class ProjectionType(str, Enum):
    """The 10 canonical projection types."""

    WORKSPACE = "workspace"
    CONVERSATION = "conversation"
    EXECUTION = "execution"
    MEETING = "meeting"
    RELATIONSHIP = "relationship"
    TIMELINE = "timeline"
    EVIDENCE = "evidence"
    PREDICTION = "prediction"
    COMMITMENT = "commitment"
    SEARCH = "search"


class TemporalScope(str, Enum):
    """Temporal scope for context resolution."""

    CURRENT = "current"
    HISTORICAL = "historical"
    FUTURE = "future"
    ALL = "all"


class DegradedReason(str, Enum):
    """Why a projection was returned in degraded mode."""

    GRAPH_UNAVAILABLE = "graph_unavailable"
    GRAPH_SLOW = "graph_slow"
    CACHE_MISS_GRAPH_FAILURE = "cache_miss_graph_failure"
    NONE = "none"


# ---------------------------------------------------------------------------
# View models — lightweight serializable representations of graph data
# ---------------------------------------------------------------------------


@dataclass
class NodeView:
    """Lightweight representation of a graph Node for projection output."""

    node_id: str
    type: str
    name: str
    status: str = "active"
    confidence: float = 1.0
    labels: list[str] = field(default_factory=list)
    attributes: dict[str, Any] = field(default_factory=dict)
    created_at: str = ""


@dataclass
class EdgeView:
    """Lightweight representation of a graph Edge for projection output."""

    edge_id: str
    source_id: str
    target_id: str
    type: str
    direction: str = "directed"
    confidence: float = 1.0
    validity: dict[str, str | None] | None = None  # {start, end}


@dataclass
class EvidenceView:
    """Lightweight representation of an evidence item."""

    evidence_id: str
    node_id: str
    source: str
    timestamp: str
    confidence: float = 1.0
    summary: str = ""


@dataclass
class ProjectionMetadata:
    """Metadata attached to every GraphProjection."""

    timing_ms: float = 0.0
    total_available: int = 0
    filters_applied: list[str] = field(default_factory=list)
    degraded: bool = False
    degraded_reason: str = DegradedReason.NONE.value
    source: str = "cache"
    ttl_seconds: float = 0.0


@dataclass
class GraphProjection:
    """The canonical projection dataclass.

    Every workspace render is backed by exactly one GraphProjection.
    The workspace never queries raw storage — it renders projections.
    """

    projection_id: str = ""
    projection_type: str = ""
    root_node: NodeView | None = None
    nodes: list[NodeView] = field(default_factory=list)
    edges: list[EdgeView] = field(default_factory=list)
    evidence: list[EvidenceView] = field(default_factory=list)
    metadata: ProjectionMetadata = field(default_factory=ProjectionMetadata)
    timestamp: str = ""

    def __post_init__(self) -> None:
        if not self.projection_id:
            self.projection_id = uuid.uuid4().hex[:16]
        if not self.timestamp:
            self.timestamp = datetime.now(timezone.utc).isoformat()


# ---------------------------------------------------------------------------
# Public API helpers
# ---------------------------------------------------------------------------

PROJECTION_MAX_NODES: dict[ProjectionType, int] = {
    ProjectionType.WORKSPACE: 50,
    ProjectionType.CONVERSATION: 200,
    ProjectionType.EXECUTION: 100,
    ProjectionType.MEETING: 100,
    ProjectionType.RELATIONSHIP: 200,
    ProjectionType.TIMELINE: 500,
    ProjectionType.EVIDENCE: 100,
    ProjectionType.PREDICTION: 50,
    ProjectionType.COMMITMENT: 50,
    ProjectionType.SEARCH: 100,
}

PROJECTION_CACHE_TTL: dict[ProjectionType, float] = {
    ProjectionType.WORKSPACE: 0.0,  # fresh only
    ProjectionType.CONVERSATION: 30.0,
    ProjectionType.EXECUTION: -1.0,  # until complete
    ProjectionType.MEETING: 300.0,
    ProjectionType.RELATIONSHIP: 60.0,
    ProjectionType.TIMELINE: 300.0,
    ProjectionType.EVIDENCE: 300.0,
    ProjectionType.PREDICTION: 60.0,
    ProjectionType.COMMITMENT: 60.0,
    ProjectionType.SEARCH: 0.0,  # fresh only
}

PROJECTION_INVALIDATION_EVENTS: dict[str, list[ProjectionType]] = {
    "NewMessage": [ProjectionType.CONVERSATION],
    "ExecutionOutcome": [ProjectionType.EXECUTION],
    "MeetingUpdate": [ProjectionType.MEETING],
    "RelationshipChanged": [ProjectionType.RELATIONSHIP, ProjectionType.WORKSPACE],
    "EvidenceAdded": [ProjectionType.EVIDENCE, ProjectionType.WORKSPACE],
    "PredictionResolved": [ProjectionType.PREDICTION],
    "CommitmentUpdated": [ProjectionType.COMMITMENT],
    "ObjectCreated": [ProjectionType.WORKSPACE, ProjectionType.RELATIONSHIP],
    "ObjectUpdated": [ProjectionType.WORKSPACE],
    "ObjectArchived": [ProjectionType.WORKSPACE],
}


__all__ = [
    "PROJECTION_CACHE_TTL",
    "PROJECTION_INVALIDATION_EVENTS",
    "PROJECTION_MAX_NODES",
    "DegradedReason",
    "EdgeView",
    "EvidenceView",
    "GraphProjection",
    "NodeView",
    "ProjectionMetadata",
    "ProjectionType",
    "TemporalScope",
]