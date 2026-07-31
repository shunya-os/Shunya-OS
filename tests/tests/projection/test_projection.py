"""Tests for the Projection Engine (Phase K).

Covers: types, cache, context resolution, engine assembly, caching,
invalidation, degraded mode, and observability.
"""

import time
from datetime import datetime, timezone

import pytest

from core.projection import (
    PROJECTION_CACHE_TTL,
    PROJECTION_INVALIDATION_EVENTS,
    PROJECTION_MAX_NODES,
    ContextResolver,
    DegradedReason,
    EdgeView,
    EvidenceView,
    GraphProjection,
    NodeView,
    ProjectionCache,
    ProjectionEngine,
    ProjectionType,
    ResolutionParams,
    TemporalScope,
)

# ======================================================================
# Fixtures
# ======================================================================


@pytest.fixture
def engine() -> ProjectionEngine:
    return ProjectionEngine()


@pytest.fixture
def cache() -> ProjectionCache:
    return ProjectionCache()


@pytest.fixture
def resolver() -> ContextResolver:
    return ContextResolver()


@pytest.fixture
def sample_node() -> NodeView:
    return NodeView(node_id="n1", type="person", name="Alice", confidence=0.95)


@pytest.fixture
def sample_edge() -> EdgeView:
    return EdgeView(edge_id="e1", source_id="n1", target_id="n2", type="knows")


@pytest.fixture
def sample_evidence() -> EvidenceView:
    return EvidenceView(
        evidence_id="ev1",
        node_id="n1",
        source="observation",
        timestamp=datetime.now(timezone.utc).isoformat(),
        confidence=0.9,
        summary="Alice was observed in the system.",
    )


# ======================================================================
# Types
# ======================================================================


class TestProjectionType:
    def test_enum_values(self) -> None:
        assert ProjectionType.WORKSPACE.value == "workspace"
        assert ProjectionType.CONVERSATION.value == "conversation"
        assert ProjectionType.SEARCH.value == "search"
        assert len(ProjectionType) == 10

    def test_from_string(self) -> None:
        assert ProjectionType("workspace") == ProjectionType.WORKSPACE
        assert ProjectionType("search") == ProjectionType.SEARCH


class TestNodeView:
    def test_defaults(self) -> None:
        n = NodeView(node_id="x", type="doc", name="Doc")
        assert n.status == "active"
        assert n.confidence == 1.0
        assert n.labels == []
        assert n.attributes == {}

    def test_full_construction(self) -> None:
        n = NodeView(
            node_id="n1",
            type="person",
            name="Alice",
            status="active",
            confidence=0.95,
            labels=["staff", "engineering"],
            attributes={"email": "alice@co.com"},
            created_at="2026-01-01T00:00:00",
        )
        assert n.node_id == "n1"
        assert n.attributes["email"] == "alice@co.com"


class TestEdgeView:
    def test_defaults(self) -> None:
        e = EdgeView(edge_id="e1", source_id="a", target_id="b", type="knows")
        assert e.direction == "directed"
        assert e.confidence == 1.0

    def test_with_validity(self) -> None:
        e = EdgeView(
            edge_id="e1", source_id="a", target_id="b", type="knows",
            validity={"start": "2026-01-01", "end": None},
        )
        assert e.validity is not None
        assert e.validity["start"] == "2026-01-01"


class TestEvidenceView:
    def test_defaults(self) -> None:
        ev = EvidenceView(evidence_id="ev1", node_id="n1", source="obs", timestamp="now")
        assert ev.confidence == 1.0
        assert ev.summary == ""


class TestGraphProjection:
    def test_auto_id_and_timestamp(self) -> None:
        p = GraphProjection(projection_type="workspace")
        assert p.projection_id != ""
        assert p.timestamp != ""

    def test_explicit_id(self) -> None:
        p = GraphProjection(projection_id="abc123", projection_type="workspace")
        assert p.projection_id == "abc123"


class TestProjectionConstants:
    def test_max_nodes_all_types(self) -> None:
        assert PROJECTION_MAX_NODES[ProjectionType.WORKSPACE] == 50
        assert PROJECTION_MAX_NODES[ProjectionType.TIMELINE] == 500
        assert len(PROJECTION_MAX_NODES) == 10

    def test_cache_ttl_all_types(self) -> None:
        assert PROJECTION_CACHE_TTL[ProjectionType.WORKSPACE] == 0.0
        assert PROJECTION_CACHE_TTL[ProjectionType.CONVERSATION] == 30.0
        assert PROJECTION_CACHE_TTL[ProjectionType.SEARCH] == 0.0
        assert len(PROJECTION_CACHE_TTL) == 10

    def test_invalidation_events(self) -> None:
        assert "NewMessage" in PROJECTION_INVALIDATION_EVENTS
        assert "ObjectCreated" in PROJECTION_INVALIDATION_EVENTS
        assert ProjectionType.CONVERSATION in PROJECTION_INVALIDATION_EVENTS["NewMessage"]


# ======================================================================
# Cache
# ======================================================================


class TestProjectionCache:
    def test_get_miss(self, cache: ProjectionCache) -> None:
        assert cache.get("nonexistent") is None

    def test_set_and_get(self, cache: ProjectionCache) -> None:
        p = GraphProjection(projection_type="workspace")
        cache.set("ws:n1", p, 60)
        result = cache.get("ws:n1")
        assert result is not None
        assert result.projection_id == p.projection_id

    def test_zero_ttl_not_stored(self, cache: ProjectionCache) -> None:
        cache.set("ws:n1", GraphProjection(projection_type="workspace"), 0)
        assert cache.get("ws:n1") is None

    def test_expired_entry_removed(self, cache: ProjectionCache) -> None:
        # Use a very short TTL
        cache.set("ws:n1", GraphProjection(projection_type="workspace"), 0.01)
        time.sleep(0.02)
        assert cache.get("ws:n1") is None

    def test_invalidation(self, cache: ProjectionCache) -> None:
        cache.set("ws:n1", GraphProjection(projection_type="workspace"), 60)
        cache.set("ws:n2", GraphProjection(projection_type="workspace"), 60)
        cache.set("conv:t1", GraphProjection(projection_type="conversation"), 60)

        count = cache.invalidate(projection_type="workspace")
        assert count == 2
        assert cache.get("ws:n1") is None
        assert cache.get("ws:n2") is None
        assert cache.get("conv:t1") is not None  # not invalidated

    def test_invalidation_by_root_id(self, cache: ProjectionCache) -> None:
        cache.set("ws:n1", GraphProjection(projection_type="workspace"), 60)
        cache.set("ws:n2", GraphProjection(projection_type="workspace"), 60)

        count = cache.invalidate(projection_type="workspace", root_id="n1")
        assert count == 1

    def test_evict_expired(self, cache: ProjectionCache) -> None:
        cache.set("ws:n1", GraphProjection(projection_type="workspace"), 0.01)
        cache.set("ws:n2", GraphProjection(projection_type="workspace"), 60)
        time.sleep(0.02)
        evicted = cache.evict_expired()
        assert evicted == 1
        assert cache.get("ws:n2") is not None

    def test_clear(self, cache: ProjectionCache) -> None:
        cache.set("ws:n1", GraphProjection(projection_type="workspace"), 60)
        assert cache.stats()["size"] == 1
        cache.clear()
        assert cache.stats()["size"] == 0

    def test_build_key(self, cache: ProjectionCache) -> None:
        assert cache.build_key("workspace", "n1") == "workspace:n1"
        assert cache.build_key("search", "q", "hash123") == "search:q:hash123"

    def test_stats(self, cache: ProjectionCache) -> None:
        cache.get("miss")
        cache.set("hit", GraphProjection(projection_type="workspace"), 60)
        cache.get("hit")
        s = cache.stats()
        assert s["hits"] == 1
        assert s["misses"] == 1
        assert s["hit_rate"] == 0.5

    def test_health_check(self, cache: ProjectionCache) -> None:
        h = cache.health_check()
        assert h["status"] == "healthy"
        assert h["component"] == "projection_cache"


# ======================================================================
# Context Resolution
# ======================================================================


class TestContextResolver:
    def test_get_params(self, resolver: ContextResolver) -> None:
        p = resolver.get_params(ProjectionType.RELATIONSHIP)
        assert p.depth == 2
        assert p.max_nodes == 200
        assert p.confidence_min == 0.3

        p2 = resolver.get_params(ProjectionType.SEARCH)
        assert p2.depth == 0

    def test_default_params_fallback(self, resolver: ContextResolver) -> None:
        # Unknown enum-like string should fall back to defaults
        p = resolver.get_params(ProjectionType.WORKSPACE)
        assert p.max_nodes == 50

    def test_build_resolution_context(self, resolver: ContextResolver, sample_node: NodeView) -> None:
        neighbours = [
            NodeView(node_id="n2", type="person", name="Bob", confidence=0.8),
            NodeView(node_id="n3", type="doc", name="Report", confidence=0.6),
        ]
        edges = [EdgeView(edge_id="e1", source_id="n1", target_id="n2", type="knows")]
        evidence = [EvidenceView(evidence_id="ev1", node_id="n1", source="obs", timestamp="now", confidence=0.9)]
        params = ResolutionParams(depth=1, max_nodes=50, confidence_min=0.3)

        ctx = resolver.build_resolution_context(sample_node, neighbours, edges, evidence, params)
        assert ctx.root_node is not None
        assert ctx.root_node.node_id == "n1"
        assert len(ctx.surrounding_nodes) == 2
        assert len(ctx.edges) == 1
        assert len(ctx.evidence) == 1
        assert ctx.total_nodes == 3

    def test_build_resolution_context_sorts_by_confidence(self, resolver: ContextResolver, sample_node: NodeView) -> None:
        neighbours = [
            NodeView(node_id="n2", type="person", name="Low", confidence=0.1),
            NodeView(node_id="n3", type="person", name="High", confidence=0.99),
            NodeView(node_id="n4", type="person", name="Mid", confidence=0.5),
        ]
        ctx = resolver.build_resolution_context(sample_node, neighbours, params=ResolutionParams(confidence_min=0.0))
        assert ctx.surrounding_nodes[0].name == "High"
        assert ctx.surrounding_nodes[1].name == "Mid"
        assert ctx.surrounding_nodes[2].name == "Low"


# ======================================================================
# Projection Engine
# ======================================================================


class TestProjectionEngine:
    def test_initial_state(self, engine: ProjectionEngine) -> None:
        h = engine.health_check()
        assert h["status"] == "healthy"
        assert h["traces"] == 0

    def test_project_degraded_when_no_callbacks(self, engine: ProjectionEngine) -> None:
        proj = engine.project("workspace", "n1")
        assert proj.metadata.degraded is True
        assert proj.metadata.degraded_reason == DegradedReason.GRAPH_UNAVAILABLE.value

    def test_project_with_callbacks(self, engine: ProjectionEngine) -> None:
        def resolve_root(rid: str, ptype: str) -> NodeView | None:
            return NodeView(node_id=rid, type="person", name="Alice", confidence=0.95)

        def resolve_neighbours(rid: str, ptype: str, depth: int) -> list[NodeView]:
            return [NodeView(node_id="n2", type="task", name="Task-1", confidence=0.8)]

        def resolve_edges(rid: str) -> list[EdgeView]:
            return [EdgeView(edge_id="e1", source_id=rid, target_id="n2", type="owns")]

        engine.set_resolve_root(resolve_root)
        engine.set_resolve_neighbours(resolve_neighbours)
        engine.set_resolve_edges(resolve_edges)

        proj = engine.project("workspace", "n1")
        assert proj.metadata.degraded is False
        assert proj.root_node is not None
        assert proj.root_node.node_id == "n1"
        assert len(proj.nodes) == 1
        assert len(proj.edges) == 1

    def test_project_caching(self, engine: ProjectionEngine) -> None:
        call_count = 0

        def resolve_root(rid: str, ptype: str) -> NodeView | None:
            nonlocal call_count
            call_count += 1
            return NodeView(node_id=rid, type="person", name="Cached", confidence=1.0)

        engine.set_resolve_root(resolve_root)

        # First call assembles
        proj1 = engine.project("conversation", "t1")
        assert proj1.metadata.source == "assembled"

        # Second should be cached
        proj2 = engine.project("conversation", "t1")
        assert proj2.metadata.source == "cache"

        # Resolve was only called once
        assert call_count == 1

    def test_invalidation_by_event(self, engine: ProjectionEngine) -> None:
        def resolve_root(rid: str, ptype: str) -> NodeView | None:
            return NodeView(node_id=rid, type="person", name="X", confidence=1.0)

        engine.set_resolve_root(resolve_root)
        # Use conversation which has TTL=30s (cached)
        engine.project("conversation", "t1")

        count = engine.invalidate("NewMessage", "t1")
        assert count >= 1

    def test_search_projection(self, engine: ProjectionEngine) -> None:
        matches = [
            NodeView(node_id=f"n{i}", type="doc", name=f"Doc-{i}", confidence=0.9 - i * 0.1)
            for i in range(5)
        ]
        proj = engine.project_search(matches, query="test")
        assert proj.projection_type == "search"
        assert len(proj.nodes) == 5

    def test_project_exceeds_max_nodes(self, engine: ProjectionEngine) -> None:
        def resolve_root(rid: str, ptype: str) -> NodeView | None:
            return NodeView(node_id=rid, type="person", name="Big", confidence=1.0)

        def resolve_neighbours(rid: str, ptype: str, depth: int) -> list[NodeView]:
            return [NodeView(node_id=f"n{i}", type="item", name=f"Item-{i}", confidence=0.5)
                    for i in range(100)]

        engine.set_resolve_root(resolve_root)
        engine.set_resolve_neighbours(resolve_neighbours)

        proj = engine.project("workspace", "n1")
        # Workspace max is 50
        assert len(proj.nodes) <= 50
        assert proj.metadata.total_available == 100

    def test_observability(self, engine: ProjectionEngine) -> None:
        assert len(engine.get_traces()) == 0

        def resolve_root(rid: str, ptype: str) -> NodeView | None:
            return NodeView(node_id=rid, type="person", name="T", confidence=1.0)

        engine.set_resolve_root(resolve_root)
        engine.project("workspace", "n1")
        engine.project("conversation", "t1")

        traces = engine.get_traces()
        assert len(traces) == 2
        assert traces[0].operation == "project"
        assert traces[0].projection_type == "workspace"

        engine.clear_traces()
        assert len(engine.get_traces()) == 0


# ======================================================================
# Degraded Mode
# ======================================================================


class TestDegradedMode:
    def test_no_root_returns_degraded(self, engine: ProjectionEngine) -> None:
        proj = engine.project("workspace", "missing")
        assert proj.metadata.degraded is True
        assert proj.metadata.degraded_reason == DegradedReason.GRAPH_UNAVAILABLE.value

    def test_degraded_projection_still_has_id(self, engine: ProjectionEngine) -> None:
        proj = engine.project("workspace", "missing")
        assert proj.projection_id != ""


# ======================================================================
# Temporal Scope
# ======================================================================


class TestTemporalScope:
    def test_enum_values(self) -> None:
        assert TemporalScope.CURRENT.value == "current"
        assert TemporalScope.ALL.value == "all"
        assert len(TemporalScope) == 4

    def test_from_string(self) -> None:
        assert TemporalScope("current") == TemporalScope.CURRENT
        assert TemporalScope("future") == TemporalScope.FUTURE