"""Tests for SHUNYA Knowledge Graph — Edge Model and Store (E-003-MOD-001).

Architecture references:
    UNIVERSAL_KNOWLEDGE_GRAPH_ARCHITECTURE.md §1.3 — Edge structure
    UNIVERSAL_KNOWLEDGE_GRAPH_ARCHITECTURE.md §3.1 — Canonical edge families
    UNIVERSAL_KNOWLEDGE_GRAPH_ARCHITECTURE.md §3.2 — Edge creation rules
    UNIVERSAL_KNOWLEDGE_GRAPH_ARCHITECTURE.md §3.4 — Edge validation

Constitutional invariants tested:
    KG-01: No duplicate (source, target, type) triples
    KG-02: Source and target must exist in the graph
    KG-03: Edge creation validates source/target existence
"""

import pytest
from app.graph.node import Node, InMemoryNodeStore, get_node_store, reset_node_store
from app.graph.edge import (
    Edge, EdgeDirection, EdgeStatus, EdgeType,
    TimeRange, InMemoryEdgeStore, get_edge_store, reset_edge_store,
)
from app.kernel.object import EvidenceRef


# =========================================================================
# Edge Model Tests
# =========================================================================

class TestEdgeModel:
    """UNIVERSAL_KNOWLEDGE_GRAPH_ARCHITECTURE.md §1.3 — Edge structure."""

    def test_required_fields(self):
        """Edge requires source_id and target_id."""
        edge = Edge(source_id="n_source", target_id="n_target")
        assert edge.source_id == "n_source"
        assert edge.target_id == "n_target"

    def test_default_edge_type(self):
        """Default edge type is 'related_to'."""
        edge = Edge(source_id="n_src", target_id="n_tgt")
        assert edge.edge_type == EdgeType.RELATED_TO.value

    def test_default_direction(self):
        """Default direction is DIRECTED."""
        edge = Edge(source_id="n_src", target_id="n_tgt")
        assert edge.direction == EdgeDirection.DIRECTED.value
        assert not edge.is_bidirectional

    def test_bidirectional(self):
        """Bidirectional edge can be created."""
        edge = Edge(source_id="n_src", target_id="n_tgt",
                    direction=EdgeDirection.BIDIRECTIONAL.value)
        assert edge.is_bidirectional

    def test_default_status(self):
        """Default edge status is ACTIVE."""
        edge = Edge(source_id="n_src", target_id="n_tgt")
        assert edge.status == EdgeStatus.ACTIVE.value
        assert edge.is_active

    def test_default_weight_and_confidence(self):
        """Default weight and confidence are 1.0."""
        edge = Edge(source_id="n_src", target_id="n_tgt")
        assert edge.weight == 1.0
        assert edge.confidence == 1.0

    def test_triple_identity(self):
        """§1.4 — Edge identity is (source, target, type) triple."""
        edge = Edge(source_id="n_a", target_id="n_b", edge_type="knows")
        assert edge.triple == ("n_a", "n_b", "knows")

    def test_archive(self):
        """§3.3 — Edge can be archived."""
        edge = Edge(source_id="n_src", target_id="n_tgt")
        assert edge.is_active
        edge.archive()
        assert edge.status == EdgeStatus.ARCHIVED.value

    def test_mark_stale(self):
        """§3.3 — Edge can be marked as stale."""
        edge = Edge(source_id="n_src", target_id="n_tgt")
        edge.mark_stale()
        assert edge.status == EdgeStatus.STALE.value

    def test_to_dict(self):
        """Serialization includes all Edge fields."""
        edge = Edge(
            source_id="n_src", target_id="n_tgt",
            edge_type="knows", direction=EdgeDirection.DIRECTED.value,
            weight=0.8, confidence=0.95,
        )
        d = edge.to_dict()
        assert d["source_id"] == "n_src"
        assert d["target_id"] == "n_tgt"
        assert d["edge_type"] == "knows"
        assert d["direction"] == "directed"
        assert d["weight"] == 0.8
        assert d["confidence"] == 0.95
        assert d["status"] == "active"


# =========================================================================
# TimeRange Tests
# =========================================================================

class TestTimeRange:
    """§5.3 — Temporal validity period."""

    def test_default_start_is_now(self):
        tr = TimeRange()
        assert tr.start != ""

    def test_is_current_with_no_end(self):
        tr = TimeRange()
        assert tr.is_current()

    def test_is_active_at(self):
        tr = TimeRange(start="2026-01-01T00:00:00", end="2026-12-31T00:00:00")
        assert tr.is_active_at("2026-06-15T00:00:00")
        assert not tr.is_active_at("2025-01-01T00:00:00")
        assert not tr.is_active_at("2027-01-01T00:00:00")

    def test_is_active_with_end_none(self):
        tr = TimeRange(start="2026-01-01T00:00:00")
        assert tr.is_active_at("2026-06-15T00:00:00")
        assert not tr.is_active_at("2025-01-01T00:00:00")


# =========================================================================
# EdgeStore Tests
# =========================================================================

class TestInMemoryEdgeStore:
    """InMemoryEdgeStore — CRUD, validation, and indexing."""

    def setup_method(self):
        reset_node_store()
        reset_edge_store()

    def _create_person_node(self, store=None, **kw) -> Node:
        if store is None:
            store = get_node_store()
        node = Node(node_type="Person", **kw)
        store.create(node)
        return node

    def test_create_and_get(self):
        """Edge can be created and retrieved by triple."""
        node_store = get_node_store()
        src = self._create_person_node(node_store)
        tgt = self._create_person_node(node_store)
        edge_store = get_edge_store()

        edge = Edge(source_id=src.node_id, target_id=tgt.node_id,
                    edge_type=EdgeType.KNOWS.value)
        edge_store.create(edge)

        retrieved = edge_store.get(src.node_id, tgt.node_id, EdgeType.KNOWS.value)
        assert retrieved is not None
        assert retrieved.source_id == src.node_id
        assert retrieved.target_id == tgt.node_id
        assert retrieved.edge_type == EdgeType.KNOWS.value

    def test_create_missing_source_raises(self):
        """KG-02 — Edge with missing source Node raises ValueError (§3.4.1)."""
        edge_store = get_edge_store()
        edge = Edge(source_id="n_nonexistent", target_id="n_target",
                    edge_type="knows")
        with pytest.raises(ValueError, match="Source Node"):
            edge_store.create(edge)

    def test_create_missing_target_raises(self):
        """KG-02 — Edge with missing target Node raises ValueError (§3.4.2)."""
        node_store = get_node_store()
        src = self._create_person_node(node_store)
        edge_store = get_edge_store()
        edge = Edge(source_id=src.node_id, target_id="n_nonexistent",
                    edge_type="knows")
        with pytest.raises(ValueError, match="target Node"):
            edge_store.create(edge)

    def test_create_duplicate_triple_raises(self):
        """KG-01 — Duplicate (source, target, type) raises ValueError (§3.2.3, §3.4.3)."""
        node_store = get_node_store()
        src = self._create_person_node(node_store)
        tgt = self._create_person_node(node_store)
        edge_store = get_edge_store()

        edge = Edge(source_id=src.node_id, target_id=tgt.node_id,
                    edge_type=EdgeType.KNOWS.value)
        edge_store.create(edge)

        duplicate = Edge(source_id=src.node_id, target_id=tgt.node_id,
                         edge_type=EdgeType.KNOWS.value)
        with pytest.raises(ValueError, match="Duplicate Edge triple"):
            edge_store.create(duplicate)

    def test_get_outgoing(self):
        """Outgoing Edges can be queried by source."""
        node_store = get_node_store()
        src = self._create_person_node(node_store)
        tgt1 = self._create_person_node(node_store)
        tgt2 = self._create_person_node(node_store)
        edge_store = get_edge_store()

        edge_store.create(Edge(source_id=src.node_id, target_id=tgt1.node_id,
                                edge_type=EdgeType.KNOWS.value))
        edge_store.create(Edge(source_id=src.node_id, target_id=tgt2.node_id,
                                edge_type=EdgeType.WORKS_AT.value))

        outgoing = edge_store.get_outgoing(src.node_id)
        assert len(outgoing) == 2

        filtered = edge_store.get_outgoing(src.node_id, edge_type=EdgeType.KNOWS.value)
        assert len(filtered) == 1
        assert filtered[0].target_id == tgt1.node_id

    def test_get_incoming(self):
        """Incoming Edges can be queried by target."""
        node_store = get_node_store()
        src1 = self._create_person_node(node_store)
        src2 = self._create_person_node(node_store)
        tgt = self._create_person_node(node_store)
        edge_store = get_edge_store()

        edge_store.create(Edge(source_id=src1.node_id, target_id=tgt.node_id,
                                edge_type=EdgeType.KNOWS.value))
        edge_store.create(Edge(source_id=src2.node_id, target_id=tgt.node_id,
                                edge_type=EdgeType.KNOWS.value))

        incoming = edge_store.get_incoming(tgt.node_id)
        assert len(incoming) == 2

    def test_get_all(self):
        """All edges (outgoing + incoming) for a Node."""
        node_store = get_node_store()
        a = self._create_person_node(node_store)
        b = self._create_person_node(node_store)
        c = self._create_person_node(node_store)
        edge_store = get_edge_store()

        edge_store.create(Edge(source_id=a.node_id, target_id=b.node_id,
                                edge_type=EdgeType.KNOWS.value))
        edge_store.create(Edge(source_id=c.node_id, target_id=a.node_id,
                                edge_type=EdgeType.KNOWS.value))

        all_edges = edge_store.get_all(a.node_id)
        assert len(all_edges) == 2

    def test_remove(self):
        """Edge can be removed by triple."""
        node_store = get_node_store()
        src = self._create_person_node(node_store)
        tgt = self._create_person_node(node_store)
        edge_store = get_edge_store()

        edge_store.create(Edge(source_id=src.node_id, target_id=tgt.node_id,
                                edge_type=EdgeType.KNOWS.value))
        assert edge_store.count() == 1
        assert edge_store.remove(src.node_id, tgt.node_id, EdgeType.KNOWS.value)
        assert edge_store.count() == 0

    def test_remove_nonexistent_returns_false(self):
        """Removing a non-existent Edge returns False."""
        edge_store = get_edge_store()
        assert not edge_store.remove("n_a", "n_b", "knows")

    def test_count(self):
        """Count returns total Edges, optionally filtered by type."""
        node_store = get_node_store()
        src = self._create_person_node(node_store)
        tgt1 = self._create_person_node(node_store)
        tgt2 = self._create_person_node(node_store)
        edge_store = get_edge_store()

        edge_store.create(Edge(source_id=src.node_id, target_id=tgt1.node_id,
                                edge_type=EdgeType.KNOWS.value))
        edge_store.create(Edge(source_id=src.node_id, target_id=tgt2.node_id,
                                edge_type=EdgeType.WORKS_AT.value))

        assert edge_store.count() == 2
        assert edge_store.count(edge_type=EdgeType.KNOWS.value) == 1

    def test_all(self):
        """All returns every Edge in the store."""
        node_store = get_node_store()
        a = self._create_person_node(node_store)
        b = self._create_person_node(node_store)
        edge_store = get_edge_store()

        edge_store.create(Edge(source_id=a.node_id, target_id=b.node_id,
                                edge_type=EdgeType.KNOWS.value))
        assert len(edge_store.all()) == 1

    def test_remove_cleans_indexes(self):
        """Removing an Edge cleans up source and target indexes."""
        node_store = get_node_store()
        src = self._create_person_node(node_store)
        tgt = self._create_person_node(node_store)
        edge_store = get_edge_store()

        edge_store.create(Edge(source_id=src.node_id, target_id=tgt.node_id,
                                edge_type=EdgeType.KNOWS.value))
        edge_store.remove(src.node_id, tgt.node_id, EdgeType.KNOWS.value)
        assert len(edge_store.get_outgoing(src.node_id)) == 0
        assert len(edge_store.get_incoming(tgt.node_id)) == 0

    def test_clear(self):
        """Clear removes all Edges and resets indexes."""
        node_store = get_node_store()
        a = self._create_person_node(node_store)
        b = self._create_person_node(node_store)
        edge_store = get_edge_store()

        edge_store.create(Edge(source_id=a.node_id, target_id=b.node_id,
                                edge_type=EdgeType.KNOWS.value))
        edge_store.clear()
        assert edge_store.count() == 0

    def test_edge_with_evidence(self):
        """§1.3 — Edge can carry evidence refs."""
        node_store = get_node_store()
        src = self._create_person_node(node_store)
        tgt = self._create_person_node(node_store)
        edge_store = get_edge_store()

        ev = EvidenceRef(object_id="ev_001", object_type="Observation",
                         confidence=0.9)
        edge = Edge(source_id=src.node_id, target_id=tgt.node_id,
                    edge_type=EdgeType.KNOWS.value,
                    evidence=[ev])
        edge_store.create(edge)

        retrieved = edge_store.get(src.node_id, tgt.node_id, EdgeType.KNOWS.value)
        assert retrieved is not None
        assert len(retrieved.evidence) == 1
        assert retrieved.evidence[0].object_id == "ev_001"

    def test_edge_with_validity(self):
        """§5.3 — Edge can carry a temporal validity period."""
        node_store = get_node_store()
        src = self._create_person_node(node_store)
        tgt = self._create_person_node(node_store)
        edge_store = get_edge_store()

        validity = TimeRange(start="2026-01-01T00:00:00", end="2026-12-31T00:00:00")
        edge = Edge(source_id=src.node_id, target_id=tgt.node_id,
                    edge_type=EdgeType.WORKS_AT.value,
                    validity=validity)
        edge_store.create(edge)

        retrieved = edge_store.get(src.node_id, tgt.node_id, EdgeType.WORKS_AT.value)
        assert retrieved is not None
        assert retrieved.validity is not None
        assert retrieved.validity.start == "2026-01-01T00:00:00"
        assert retrieved.validity.end == "2026-12-31T00:00:00"

    def test_self_referencing_edge(self):
        """§3.2.5 — Self-referencing edges are valid for certain types."""
        node_store = get_node_store()
        node = self._create_person_node(node_store)
        edge_store = get_edge_store()

        edge = Edge(source_id=node.node_id, target_id=node.node_id,
                    edge_type=EdgeType.VERSION_OF.value)
        edge_store.create(edge)
        assert edge_store.count() == 1

    def test_multiple_edge_types_between_same_nodes(self):
        """Different edge types between same nodes are distinct (§3.2.3)."""
        node_store = get_node_store()
        a = self._create_person_node(node_store)
        b = self._create_person_node(node_store)
        edge_store = get_edge_store()

        edge_store.create(Edge(source_id=a.node_id, target_id=b.node_id,
                                edge_type=EdgeType.KNOWS.value))
        edge_store.create(Edge(source_id=a.node_id, target_id=b.node_id,
                                edge_type=EdgeType.WORKS_AT.value))
        assert edge_store.count() == 2


# =========================================================================
# Performance Test
# =========================================================================

class TestEdgeStorePerformance:
    """Acceptance criteria: 1000 edges created in < 1s."""

    def setup_method(self):
        reset_node_store()
        reset_edge_store()

    def test_1000_edges_under_1s(self):
        """1000 Edges created in < 1 second."""
        import time
        node_store = get_node_store()
        edge_store = get_edge_store()

        # Create 251 source nodes and 251 target nodes (prime-based,
        # guarantees no triple collisions with 7 edge types across 1000 edges)
        sources = []
        targets = []
        for i in range(251):
            s = Node(node_type="Person", attributes={"index": i})
            node_store.create(s)
            sources.append(s)
            t = Node(node_type="Document", attributes={"index": i})
            node_store.create(t)
            targets.append(t)

        edge_types = [EdgeType.REFERENCES, EdgeType.CITES,
                      EdgeType.MENTIONS, EdgeType.DERIVED_FROM,
                      EdgeType.SUPPORTS, EdgeType.CONTRADICTS,
                      EdgeType.VERSION_OF]

        start = time.time()
        for i in range(1000):
            src = sources[i % 251]
            tgt = targets[i % 251]
            etype = edge_types[i % 7]
            edge_store.create(Edge(
                source_id=src.node_id,
                target_id=tgt.node_id,
                edge_type=etype,
            ))
        elapsed = time.time() - start
        assert edge_store.count() == 1000
        assert elapsed < 1.0, f"1000 edges took {elapsed:.3f}s (limit: 1.0s)"