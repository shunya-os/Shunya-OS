"""Projection Engine — orchestrates projection assembly, caching, and degraded mode.

The ProjectionEngine is the entry point for all projection operations.
It coordinates context resolution, projection assembly, caching,
invalidation, and graceful degradation.
"""

from __future__ import annotations

import time
import uuid
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from .cache import ProjectionCache
from .resolution import ContextResolver, ResolutionParams
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
)


@dataclass
class ProjectionTrace:
    """Observability trace for a single projection operation."""

    operation: str
    projection_type: str
    root_id: str
    timing_ms: float
    degraded: bool
    node_count: int
    edge_count: int
    timestamp: str = ""

    def __post_init__(self) -> None:
        if not self.timestamp:
            self.timestamp = datetime.now(timezone.utc).isoformat()


class ProjectionEngine:
    """Orchestrator for projection assembly, caching, and degraded mode.

    The engine does NOT query the Knowledge Graph directly. It receives
    graph data via callback functions, making it testable without a graph
    backend.
    """

    def __init__(self) -> None:
        self._cache = ProjectionCache()
        self._context_resolver = ContextResolver()
        self._traces: list[ProjectionTrace] = []
        # Callback hooks — set by the integrating layer
        self._resolve_root: Callable[[str, str], NodeView | None] | None = None
        self._resolve_neighbours: Callable[[str, str, int], list[NodeView]] | None = None
        self._resolve_edges: Callable[[str], list[EdgeView]] | None = None
        self._resolve_evidence: Callable[[str], list[EvidenceView]] | None = None

    # ------------------------------------------------------------------
    # Configuration
    # ------------------------------------------------------------------

    def set_resolve_root(self, fn: Callable[[str, str], NodeView | None]) -> None:
        """Set the callback that resolves a root Node by type + ID."""
        self._resolve_root = fn

    def set_resolve_neighbours(self, fn: Callable[[str, str, int], list[NodeView]]) -> None:
        """Set the callback that resolves neighbours for a root."""
        self._resolve_neighbours = fn

    def set_resolve_edges(self, fn: Callable[[str], list[EdgeView]]) -> None:
        """Set the callback that resolves edges for a root."""
        self._resolve_edges = fn

    def set_resolve_evidence(self, fn: Callable[[str], list[EvidenceView]]) -> None:
        """Set the callback that resolves evidence for a root."""
        self._resolve_evidence = fn

    # ------------------------------------------------------------------
    # Core projection API
    # ------------------------------------------------------------------

    def project(
        self,
        projection_type: str | ProjectionType,
        root_id: str,
        params: ResolutionParams | None = None,
        query_hash: str = "",
    ) -> GraphProjection:
        """Assemble a projection for the given type and root.

        The projection pipeline:
          1. Check cache (if TTL > 0)
          2. Resolve root Node
          3. Resolve neighbours + edges + evidence
          4. Filter and limit
          5. Build GraphProjection
          6. Cache (if TTL > 0)
          7. Return projection

        Args:
            projection_type: One of the 10 canonical projection types.
            root_id: The root Node's identifier.
            params: Optional resolution parameter overrides.
            query_hash: Optional hash for search query caching.

        Returns a GraphProjection (may be degraded on failure).
        """
        if isinstance(projection_type, str):
            projection_type = ProjectionType(projection_type)

        cache_key = self._cache.build_key(projection_type.value, root_id, query_hash)
        ptype = projection_type
        start = time.perf_counter()

        # 1. Check cache
        cached = self._cache.get(cache_key)
        if cached is not None:
            cached.metadata.source = "cache"
            elapsed = (time.perf_counter() - start) * 1000
            self._record_trace(ptype.value, root_id, elapsed, False, len(cached.nodes), len(cached.edges))
            return cached

        # 2. Resolve root
        root_node = self._resolve_root(root_id, ptype.value) if self._resolve_root else None
        if root_node is None:
            elapsed = (time.perf_counter() - start) * 1000
            return self._degraded_projection(ptype, root_id, DegradedReason.GRAPH_UNAVAILABLE, elapsed)

        # 3. Resolve neighbours, edges, evidence
        resolution_params = params or self._context_resolver.get_params(ptype)
        neighbours: list[NodeView] = []
        edges: list[EdgeView] = []
        evidence: list[EvidenceView] = []

        t0 = time.perf_counter()
        if self._resolve_neighbours:
            neighbours = self._resolve_neighbours(root_id, ptype.value, resolution_params.depth)
        if self._resolve_edges:
            edges = self._resolve_edges(root_id)
        if self._resolve_evidence:
            evidence = self._resolve_evidence(root_id)
        resolve_time = (time.perf_counter() - t0) * 1000

        # 4. Detect degraded mode
        is_degraded = False
        degraded_reason = DegradedReason.NONE
        if resolve_time > 500:
            is_degraded = True
            degraded_reason = DegradedReason.GRAPH_SLOW

        # 5. Filter and limit
        max_nodes = PROJECTION_MAX_NODES.get(ptype, 50)
        total_available = len(neighbours)
        neighbours = [n for n in neighbours if n.confidence >= resolution_params.confidence_min]
        neighbours = sorted(neighbours, key=lambda n: n.confidence, reverse=True)[:max_nodes]
        edges = edges[: max_nodes * 2]

        # 6. Build projection
        elapsed = (time.perf_counter() - start) * 1000
        projection = GraphProjection(
            projection_id=uuid.uuid4().hex[:16],
            projection_type=ptype.value,
            root_node=root_node,
            nodes=neighbours,
            edges=edges,
            evidence=evidence,
            metadata=ProjectionMetadata(
                timing_ms=round(elapsed, 2),
                total_available=total_available,
                filters_applied=[f"confidence_min={resolution_params.confidence_min}"],
                degraded=is_degraded,
                degraded_reason=degraded_reason.value,
                source="assembled",
                ttl_seconds=PROJECTION_CACHE_TTL.get(ptype, 0.0),
            ),
            timestamp=datetime.now(timezone.utc).isoformat(),
        )

        # 7. Cache
        ttl = PROJECTION_CACHE_TTL.get(ptype, 0.0)
        self._cache.set(cache_key, projection, ttl)

        # 8. Trace
        self._record_trace(ptype.value, root_id, elapsed, is_degraded, len(projection.nodes), len(projection.edges))

        return projection

    def invalidate(self, event_type: str, root_id: str | None = None) -> int:
        """Invalidate cached projections affected by an event.

        Args:
            event_type: The type of event that occurred (e.g. "NewMessage").
            root_id: Optional root node ID to scope invalidation.

        Returns the number of cache entries invalidated.
        """
        affected_types = PROJECTION_INVALIDATION_EVENTS.get(event_type, [])
        total = 0
        for pt in affected_types:
            total += self._cache.invalidate(projection_type=pt.value, root_id=root_id)
        return total

    def project_search(
        self,
        matches: list[NodeView],
        query: str = "",
    ) -> GraphProjection:
        """Assemble a Search projection from raw match results."""
        root = NodeView(node_id="search", type="search", name=f"Search: {query}" if query else "Search results")
        return GraphProjection(
            projection_id=uuid.uuid4().hex[:16],
            projection_type=ProjectionType.SEARCH.value,
            root_node=root,
            nodes=matches[: PROJECTION_MAX_NODES[ProjectionType.SEARCH]],
            metadata=ProjectionMetadata(source="assembled"),
            timestamp=datetime.now(timezone.utc).isoformat(),
        )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _degraded_projection(
        self,
        ptype: ProjectionType,
        root_id: str,
        reason: DegradedReason,
        timing_ms: float,
    ) -> GraphProjection:
        """Return a minimal degraded projection."""
        return GraphProjection(
            projection_id=uuid.uuid4().hex[:16],
            projection_type=ptype.value,
            root_node=NodeView(node_id=root_id, type="unknown", name=root_id),
            metadata=ProjectionMetadata(
                timing_ms=round(timing_ms, 2),
                degraded=True,
                degraded_reason=reason.value,
                source="degraded",
            ),
            timestamp=datetime.now(timezone.utc).isoformat(),
        )

    def _record_trace(
        self,
        ptype: str,
        root_id: str,
        timing_ms: float,
        degraded: bool,
        node_count: int,
        edge_count: int,
    ) -> None:
        self._traces.append(ProjectionTrace(
            operation="project",
            projection_type=ptype,
            root_id=root_id,
            timing_ms=round(timing_ms, 2),
            degraded=degraded,
            node_count=node_count,
            edge_count=edge_count,
        ))

    # ------------------------------------------------------------------
    # Observability
    # ------------------------------------------------------------------

    def get_traces(self, limit: int = 100) -> list[ProjectionTrace]:
        """Return recent projection traces."""
        return list(self._traces[-limit:])

    def clear_traces(self) -> None:
        """Clear all traces."""
        self._traces.clear()

    def health_check(self) -> dict[str, Any]:
        """Return engine health status."""
        cache_health = self._cache.health_check()
        return {
            "status": "healthy",
            "component": "projection_engine",
            "traces": len(self._traces),
            "cache": cache_health,
        }


__all__ = [
    "ProjectionEngine",
    "ProjectionTrace",
]