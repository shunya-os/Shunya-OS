"""Projection Engine — public API."""

from .cache import ProjectionCache
from .engine import ProjectionEngine, ProjectionTrace
from .resolution import ContextResolver, ResolutionContext, ResolutionParams
from .types import (
    PROJECTION_CACHE_TTL,
    PROJECTION_INVALIDATION_EVENTS,
    PROJECTION_MAX_NODES,
    DegradedReason,
    EdgeView,
    EvidenceView,
    GraphProjection,
    NodeView,
    ProjectionMetadata,
    ProjectionType,
    TemporalScope,
)

__all__ = [
    "PROJECTION_CACHE_TTL",
    "PROJECTION_INVALIDATION_EVENTS",
    "PROJECTION_MAX_NODES",
    "ContextResolver",
    "DegradedReason",
    "EdgeView",
    "EvidenceView",
    "GraphProjection",
    "NodeView",
    "ProjectionCache",
    "ProjectionEngine",
    "ProjectionMetadata",
    "ProjectionTrace",
    "ProjectionType",
    "ResolutionContext",
    "ResolutionParams",
    "TemporalScope",
]