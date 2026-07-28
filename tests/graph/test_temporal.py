"""Tests for SHUNYA Knowledge Graph — Temporal Graph (E-003-MOD-003).

Architecture references:
    UNIVERSAL_KNOWLEDGE_GRAPH_ARCHITECTURE.md §5 — Temporal Graph
    UNIVERSAL_KNOWLEDGE_GRAPH_ARCHITECTURE.md §5.2 — Temporal edge types
    UNIVERSAL_KNOWLEDGE_GRAPH_ARCHITECTURE.md §5.4 — Temporal queries
    UNIVERSAL_KNOWLEDGE_GRAPH_ARCHITECTURE.md §5.5 — Temporal invariants
"""

import pytest
from datetime import datetime, timezone, timedelta
from app.graph.temporal import (
    TemporalStore, TemporalEdgeType,
    get_temporal_store, reset_temporal_store,
)
from app.graph.edge import (
    Edge, EdgeType, TimeRange,
    get_edge_store, reset_edge_store,
)
from app.graph.node import Node, get_node_store, reset_node_store


def _ts(offset_days: float = 0) -> str:
    """Generate an ISO timestamp offset from now."""
    return (datetime.now(timezone.utc) + timedelta(days=offset_days)).isoformat()


# =========================================================================
# Temporal Edge Classification Tests
# =========================================================================

class TestTemporalClassification:
    """UNIVERSAL_KNOWLEDGE_GRAPH_ARCHITECTURE.md §5.2."""

    def test_current_no_validity(self):
        """§5.2 — Edge without validity is CURRENT."""
        edge = Edge(source_id="n_a", target_id="n_b", edge_type="knows")
        assert TemporalStore.classify_edge(edge) == TemporalEdgeType.CURRENT

    def test_current_within_validity(self):
        """§5.2 — Edge active now is CURRENT."""
        edge = Edge(source_id="n_a", target_id="n_b", edge_type="knows",
                    validity=TimeRange(start=_ts(-1), end=_ts(1)))
        assert TemporalStore.classify_edge(edge) == TemporalEdgeType.CURRENT

    def test_future_edge(self):
        """§5.2 — Edge starting in the future is FUTURE."""
        edge = Edge(source_id="n_a", target_id="n_b", edge_type="knows",
                    validity=TimeRange(start=_ts(2), end=_ts(5)))
        assert TemporalStore.classify_edge(edge) == TemporalEdgeType.FUTURE

    def test_scheduled_edge(self):
        """§5.2 — Edge with future start is FUTURE and is_scheduled."""
        edge = Edge(source_id="n_a", target_id="n_b", edge_type="knows",
                    validity=TimeRange(start=_ts(2), end=_ts(5)))
        # Classified as FUTURE (predicted to be true)
        assert TemporalStore.classify_edge(edge) == TemporalEdgeType.FUTURE
        # Also detected as scheduled (has specific future time)
        assert TemporalStore.is_scheduled(edge)

    def test_expired_edge(self):
        """§5.2 — Edge with end in the past is EXPIRED."""
        edge = Edge(source_id="n_a", target_id="n_b", edge_type="knows",
                    validity=TimeRange(start=_ts(-5), end=_ts(-1)))
        assert TemporalStore.classify_edge(edge) == TemporalEdgeType.EXPIRED

    def test_superseded_edge(self):
        """§5.2 — superseded_by edge with end in past is SUPERSEDED."""
        edge = Edge(source_id="n_a", target_id="n_b", edge_type="superseded_by",
                    validity=TimeRange(start=_ts(-5), end=_ts(-1)))
        assert TemporalStore.classify_edge(edge) == TemporalEdgeType.SUPERSEDED

    def test_version_of_edge_superseded(self):
        """§5.2 — version_of edge with end in past is SUPERSEDED."""
        edge = Edge(source_id="n_a", target_id="n_b", edge_type="version_of",
                    validity=TimeRange(start=_ts(-5), end=_ts(-1)))
        assert TemporalStore.classify_edge(edge) == TemporalEdgeType.SUPERSEDED

    def test_historical_edge_type_list(self):
        """Temporal edge types list has 6 entries."""
        types = TemporalStore.get_temporal_types()
        assert len(types) == 6
        assert TemporalEdgeType.HISTORICAL in types
        assert TemporalEdgeType.CURRENT in types
        assert TemporalEdgeType.FUTURE in types


# =========================================================================
# Temporal Query Tests
# =========================================================================

class TestTemporalQueries:
    """UNIVERSAL_KNOWLEDGE_GRAPH_ARCHITECTURE.md §5.4."""

    def setup_method(self):
        reset_node_store()
        reset_edge_store()
        reset_temporal_store()

    def _create_nodes_and_edges(self):
        """Helper to set up test data."""
        ns = get_node_store()
        es = get_edge_store()

        alice = Node(node_type="Person"); ns.create(alice)
        bob = Node(node_type="Person"); ns.create(bob)
        doc = Node(node_type="Document"); ns.create(doc)

        # Current edge (no validity)
        es.create(Edge(source_id=alice.node_id, target_id=bob.node_id,
                        edge_type=EdgeType.KNOWS.value))

        # Past edge (expired)
        es.create(Edge(source_id=alice.node_id, target_id=doc.node_id,
                        edge_type=EdgeType.WORKS_AT.value,
                        validity=TimeRange(start=_ts(-10), end=_ts(-5))))

        # Future edge (scheduled)
        es.create(Edge(source_id=bob.node_id, target_id=doc.node_id,
                        edge_type=EdgeType.CREATED_BY.value,
                        validity=TimeRange(start=_ts(3), end=_ts(10))))

        # Edge with start only (no end, started in past = current)
        es.create(Edge(source_id=bob.node_id, target_id=alice.node_id,
                        edge_type=EdgeType.KNOWS.value,
                        validity=TimeRange(start=_ts(-2))))

        return alice, bob, doc

    def test_point_in_time_returns_current_edges(self):
        """§5.4 — Point-in-time query returns edges active at a timestamp."""
        self._create_nodes_and_edges()
        ts = TemporalStore(get_edge_store())

        # Query at time 0 (now-ish, should match current edges)
        now = _ts(0)
        active = ts.point_in_time(now)
        assert len(active) == 2  # knows (no validity) + knows (started -2)

        # Query in the future
        future = ts.point_in_time(_ts(5))
        # Should include: knows (always), knows (started -2, still active),
        # created_by (scheduled for +3 to +10)
        assert len(future) >= 3

    def test_range_query(self):
        """§5.4 — Range query returns edges overlapping a time range."""
        self._create_nodes_and_edges()
        ts = TemporalStore(get_edge_store())

        # Range covering the expired period
        result = ts.range(_ts(-12), _ts(-4))
        # Should include: knows (always) + works_at (expired, in range) + knows (started -2)
        assert len(result) >= 2

        # Range covering only the future period
        result = ts.range(_ts(4), _ts(8))
        assert len(result) >= 2  # knows (always) + created_by (future)

    def test_changes_query(self):
        """§5.4 — Changes query returns what changed in a range."""
        self._create_nodes_and_edges()
        ts = TemporalStore(get_edge_store())

        # Changes in the past period
        changes = ts.changes(_ts(-12), _ts(-3))
        assert len(changes) >= 1
        # At least the works_at edge should have changes
        change_types = {c["change_type"] for c in changes}
        assert "created" in change_types or "activated" in change_types

    def test_future_query(self):
        """§5.4 — Future query returns predicted edges."""
        self._create_nodes_and_edges()
        ts = TemporalStore(get_edge_store())

        future_edges = ts.future(_ts(5))
        assert len(future_edges) == 1  # only the created_by edge
        assert future_edges[0].edge_type == EdgeType.CREATED_BY.value

    def test_current_query(self):
        """§5.5.3 — Current query returns all currently active edges."""
        self._create_nodes_and_edges()
        ts = TemporalStore(get_edge_store())

        current_edges = ts.current()
        assert len(current_edges) == 2  # knows (no validity) + knows (started -2)

    def test_no_validity_edges_always_active(self):
        """§5.5.1 — Edges without validity period are always active."""
        self._create_nodes_and_edges()
        ts = TemporalStore(get_edge_store())

        # Query at any time should include the always-active knows edge
        for days in [-100, -50, 0, 50, 100]:
            active = ts.point_in_time(_ts(days))
            # There should be at least 1 always-active edge (knows, no validity)
            assert len(active) >= 1


# =========================================================================
# Temporal Edge Type Classification Integration Tests
# =========================================================================

class TestTemporalEdgeTypeIntegration:
    """End-to-end temporal edge classification with real store."""

    def setup_method(self):
        reset_node_store()
        reset_edge_store()
        reset_temporal_store()

    def test_get_edges_by_temporal_type_current(self):
        """Filter edges by CURRENT temporal classification."""
        ns = get_node_store()
        es = get_edge_store()
        a = Node(node_type="Person"); ns.create(a)
        b = Node(node_type="Person"); ns.create(b)

        es.create(Edge(source_id=a.node_id, target_id=b.node_id,
                        edge_type=EdgeType.KNOWS.value))
        es.create(Edge(source_id=a.node_id, target_id=b.node_id,
                        edge_type=EdgeType.COLLABORATES_WITH.value))

        ts = TemporalStore(get_edge_store())
        current = ts.get_edges_by_temporal_type(TemporalEdgeType.CURRENT)
        assert len(current) == 2

    def test_get_edges_by_temporal_type_mixed(self):
        """Filter edges by temporal classification with mixed validity."""
        ns = get_node_store()
        es = get_edge_store()
        a = Node(node_type="Person"); ns.create(a)
        b = Node(node_type="Person"); ns.create(b)

        es.create(Edge(source_id=a.node_id, target_id=b.node_id,
                        edge_type=EdgeType.KNOWS.value))
        es.create(Edge(source_id=a.node_id, target_id=b.node_id,
                        edge_type=EdgeType.WORKS_AT.value,
                        validity=TimeRange(start=_ts(-10), end=_ts(-5))))
        es.create(Edge(source_id=a.node_id, target_id=b.node_id,
                        edge_type=EdgeType.MEMBER_OF.value,
                        validity=TimeRange(start=_ts(3), end=_ts(10))))

        ts = TemporalStore(get_edge_store())
        current = ts.get_edges_by_temporal_type(TemporalEdgeType.CURRENT)
        assert len(current) == 1  # only KNOWS

        expired = ts.get_edges_by_temporal_type(TemporalEdgeType.EXPIRED)
        assert len(expired) == 1  # only WORKS_AT

        future = ts.get_edges_by_temporal_type(TemporalEdgeType.FUTURE)
        assert len(future) == 1  # only MEMBER_OF (future start)
        # Verify is_scheduled also detects it
        scheduled_edges = [e for e in es.all() if TemporalStore.is_scheduled(e)]
        assert len(scheduled_edges) == 1  # MEMBER_OF

    def test_has_temporal_edges(self):
        """has_temporal_edges detects presence of validity periods."""
        ns = get_node_store()
        es = get_edge_store()
        ts = TemporalStore(get_edge_store())

        a = Node(node_type="Person"); ns.create(a)
        b = Node(node_type="Person"); ns.create(b)
        es.create(Edge(source_id=a.node_id, target_id=b.node_id,
                        edge_type=EdgeType.KNOWS.value))
        assert not ts.has_temporal_edges()

        es.create(Edge(source_id=a.node_id, target_id=b.node_id,
                        edge_type=EdgeType.WORKS_AT.value,
                        validity=TimeRange(start=_ts(-5))))
        assert ts.has_temporal_edges()


# =========================================================================
# Temporal Invariant Tests
# =========================================================================

class TestTemporalInvariants:
    """UNIVERSAL_KNOWLEDGE_GRAPH_ARCHITECTURE.md §5.5."""

    def setup_method(self):
        reset_node_store()
        reset_edge_store()

    def test_historical_edges_not_deleted(self):
        """§5.5.2 — Historical edges are preserved."""
        ns = get_node_store()
        es = get_edge_store()
        a = Node(node_type="Person"); ns.create(a)
        b = Node(node_type="Company"); ns.create(b)

        edge = Edge(source_id=a.node_id, target_id=b.node_id,
                     edge_type=EdgeType.WORKS_AT.value,
                     validity=TimeRange(start=_ts(-365), end=_ts(-1)))
        es.create(edge)
        assert es.count() == 1  # Still in the store

    def test_query_without_time_returns_current(self):
        """§5.5.3 — Query without time returns current state."""
        ns = get_node_store()
        es = get_edge_store()
        a = Node(node_type="Person"); ns.create(a)
        b = Node(node_type="Person"); ns.create(b)

        es.create(Edge(source_id=a.node_id, target_id=b.node_id,
                        edge_type=EdgeType.KNOWS.value))
        es.create(Edge(source_id=a.node_id, target_id=b.node_id,
                        edge_type=EdgeType.WORKS_AT.value,
                        validity=TimeRange(start=_ts(-10), end=_ts(-5))))

        ts = TemporalStore(get_edge_store())
        current = ts.current()
        assert len(current) == 1  # only KNOWS

    def test_temporal_store_singleton(self):
        """TemporalStore has singleton accessor."""
        reset_temporal_store()
        t1 = get_temporal_store()
        t2 = get_temporal_store()
        assert t1 is t2