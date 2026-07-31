"""
Tests for the Relationship Engine (core/relationship/).

Covers CRUD, graph traversal (BFS neighbors, path finding, subgraph),
validation, filtering, and edge cases.
"""

from __future__ import annotations

from datetime import datetime, timezone, timedelta
from uuid import UUID

import pytest

from core.relationship import (
    RelationshipEngine,
    Relationship,
    RelationshipType,
    RelationshipDirection,
    RelationshipStatus,
    get_relationship_engine,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def engine() -> RelationshipEngine:
    return RelationshipEngine()


def _sample_graph(eng: RelationshipEngine) -> dict[str, list]:
    """Build a small social/org graph for traversal tests.

    Structure:
        alice --member_of--> acme
        bob   --works_at---> acme
        alice --reports_to-> bob
        doc   --created----> alice
        acme  --member_of--> mega_corp
        charlie --works_at-> mega_corp
        bob   --reports_to-> charlie
    """
    r1 = eng.add_relationship("alice", "acme", "member_of", strength=1.0, label="Employee")
    r2 = eng.add_relationship("bob", "acme", "works_at", strength=0.9)
    r3 = eng.add_relationship("alice", "bob", "reports_to", strength=0.8)
    r4 = eng.add_relationship("doc", "alice", "created", strength=1.0)
    r5 = eng.add_relationship("acme", "mega_corp", "member_of", strength=0.7)
    r6 = eng.add_relationship("charlie", "mega_corp", "works_at", strength=0.95)
    r7 = eng.add_relationship("bob", "charlie", "reports_to", strength=0.85)
    return {
        "r1": r1, "r2": r2, "r3": r3, "r4": r4,
        "r5": r5, "r6": r6, "r7": r7,
    }


# ---------------------------------------------------------------------------
# Relationship Creation
# ---------------------------------------------------------------------------

class TestCreateRelationship:
    def test_basic_directional(self, engine: RelationshipEngine):
        rel = engine.add_relationship("a", "b", "owns")
        assert rel.source_id == "a"
        assert rel.target_id == "b"
        assert rel.relationship_type == RelationshipType.OWNS
        assert rel.direction == RelationshipDirection.DIRECTIONAL
        assert rel.strength == 1.0
        assert rel.status == RelationshipStatus.ACTIVE
        assert UUID(rel.relationship_id)  # valid UUID

    def test_with_all_params(self, engine: RelationshipEngine):
        now = datetime.now(timezone.utc)
        later = now + timedelta(days=30)
        rel = engine.add_relationship(
            source_id="human_1",
            target_id="org_1",
            relationship_type="member_of",
            direction="bidirectional",
            strength=0.85,
            label="Engineering member",
            metadata={"role": "developer"},
            evidence_ids=["ev_contract_001", "ev_offer_letter"],
            created_by="admin",
            valid_from=now,
            valid_until=later,
        )
        assert rel.relationship_type == RelationshipType.MEMBER_OF
        assert rel.direction == RelationshipDirection.BIDIRECTIONAL
        assert rel.strength == 0.85
        assert rel.label == "Engineering member"
        assert rel.metadata == {"role": "developer"}
        assert len(rel.evidence_ids) == 2
        assert rel.created_by == "admin"
        assert rel.valid_from == now
        assert rel.valid_until == later

    def test_invalid_type_string(self, engine: RelationshipEngine):
        with pytest.raises(ValueError, match="Invalid relationship_type"):
            engine.add_relationship("a", "b", "flies_to")

    def test_invalid_direction_string(self, engine: RelationshipEngine):
        with pytest.raises(ValueError, match="Invalid direction"):
            engine.add_relationship("a", "b", "owns", direction="diagonal")

    def test_same_source_target(self, engine: RelationshipEngine):
        with pytest.raises(ValueError, match="must be different"):
            engine.add_relationship("a", "a", "owns")

    def test_empty_source(self, engine: RelationshipEngine):
        with pytest.raises(ValueError, match="source_id must be a non-empty string"):
            engine.add_relationship("", "b", "owns")

    def test_empty_target(self, engine: RelationshipEngine):
        with pytest.raises(ValueError, match="target_id must be a non-empty string"):
            engine.add_relationship("a", "", "owns")

    def test_strength_out_of_range(self, engine: RelationshipEngine):
        with pytest.raises(ValueError, match="strength must be in"):
            engine.add_relationship("a", "b", "owns", strength=1.5)

    def test_temporal_requires_valid_until(self, engine: RelationshipEngine):
        with pytest.raises(ValueError, match="TEMPORAL relationships must specify"):
            engine.add_relationship("a", "b", "owns", direction="temporal")

    def test_temporal_valid_from_after_until(self, engine: RelationshipEngine):
        now = datetime.now(timezone.utc)
        earlier = now - timedelta(days=1)
        with pytest.raises(ValueError, match="valid_from must precede"):
            engine.add_relationship(
                "a", "b", "owns", valid_from=now, valid_until=earlier
            )

    def test_bidirectional_indexing(self, engine: RelationshipEngine):
        """Bidirectional edges should be reachable from both sides."""
        rel = engine.add_relationship("a", "b", "related_to", direction="bidirectional")
        # Both a and b should see this as outgoing
        a_out = engine.get_outgoing("a")
        b_out = engine.get_outgoing("b")
        assert len(a_out) == 1
        assert len(b_out) == 1
        assert a_out[0].relationship_id == rel.relationship_id
        assert b_out[0].relationship_id == rel.relationship_id


# ---------------------------------------------------------------------------
# Relationship Retrieval
# ---------------------------------------------------------------------------

class TestGetRelationship:
    def test_get_by_id(self, engine: RelationshipEngine):
        rel = engine.add_relationship("a", "b", "owns")
        found = engine.get_relationship(rel.relationship_id)
        assert found is not None
        assert found.relationship_id == rel.relationship_id

    def test_get_nonexistent(self, engine: RelationshipEngine):
        assert engine.get_relationship("nonexistent") is None


class TestRemoveRelationship:
    def test_remove_existing(self, engine: RelationshipEngine):
        rel = engine.add_relationship("a", "b", "owns")
        assert engine.remove_relationship(rel.relationship_id)
        assert engine.get_relationship(rel.relationship_id) is None
        # Index should be cleaned up
        assert len(engine.get_outgoing("a")) == 0
        assert len(engine.get_incoming("b")) == 0

    def test_remove_nonexistent(self, engine: RelationshipEngine):
        assert not engine.remove_relationship("nonexistent")

    def test_remove_bidirectional(self, engine: RelationshipEngine):
        rel = engine.add_relationship("a", "b", "related_to", direction="bidirectional")
        engine.remove_relationship(rel.relationship_id)
        assert engine.get_relationship(rel.relationship_id) is None
        assert len(engine.get_outgoing("a")) == 0
        assert len(engine.get_outgoing("b")) == 0


# ---------------------------------------------------------------------------
# Query Operations
# ---------------------------------------------------------------------------

class TestQueryRelationships:
    def test_get_outgoing(self, engine: RelationshipEngine):
        g = _sample_graph(engine)
        out = engine.get_outgoing("alice")
        assert len(out) == 2  # member_of acme, reports_to bob

    def test_get_outgoing_filtered_by_type(self, engine: RelationshipEngine):
        g = _sample_graph(engine)
        out = engine.get_outgoing("alice", type_filter="reports_to")
        assert len(out) == 1
        assert out[0].target_id == "bob"

    def test_get_outgoing_filtered_by_strength(self, engine: RelationshipEngine):
        g = _sample_graph(engine)
        out = engine.get_outgoing("alice", min_strength=0.9)
        assert len(out) == 1  # only member_of (1.0)

    def test_get_incoming(self, engine: RelationshipEngine):
        g = _sample_graph(engine)
        inc = engine.get_incoming("alice")
        assert len(inc) == 1  # doc -> alice (created)

    def test_get_incoming_filtered(self, engine: RelationshipEngine):
        g = _sample_graph(engine)
        inc = engine.get_incoming("alice", type_filter="created")
        assert len(inc) == 1
        assert inc[0].source_id == "doc"

    def test_get_all(self, engine: RelationshipEngine):
        g = _sample_graph(engine)
        all_alice = engine.get_all("alice")
        assert len(all_alice) == 3  # 2 outgoing + 1 incoming

    def test_get_all_with_direction_filter(self, engine: RelationshipEngine):
        g = _sample_graph(engine)
        directional = engine.get_all("alice", direction=RelationshipDirection.DIRECTIONAL)
        assert len(directional) == 3  # all are directional in this graph

    def test_get_relationship_count(self, engine: RelationshipEngine):
        g = _sample_graph(engine)
        assert engine.get_relationship_count("alice") == 3
        assert engine.get_relationship_count("mega_corp") == 2

    def test_get_relationship_types(self, engine: RelationshipEngine):
        types = engine.get_relationship_types()
        assert isinstance(types, list)
        assert len(types) == len(RelationshipType)
        assert "owns" in types
        assert "member_of" in types
        assert "reports_to" in types
        assert types == sorted(t.value for t in RelationshipType)


# ---------------------------------------------------------------------------
# Graph Traversal
# ---------------------------------------------------------------------------

class TestNeighbors:
    def test_direct_neighbors(self, engine: RelationshipEngine):
        g = _sample_graph(engine)
        neighbors = engine.get_neighbors("alice", max_depth=1)
        assert set(neighbors) == {"acme", "bob", "doc"}

    def test_neighbors_depth_2(self, engine: RelationshipEngine):
        g = _sample_graph(engine)
        neighbors = engine.get_neighbors("alice", max_depth=2)
        assert "mega_corp" in neighbors
        assert "charlie" in neighbors

    def test_neighbors_filtered_by_type(self, engine: RelationshipEngine):
        g = _sample_graph(engine)
        neighbors = engine.get_neighbors("alice", type_filter="member_of", max_depth=1)
        assert neighbors == ["acme"]

    def test_neighbors_filtered_by_strength(self, engine: RelationshipEngine):
        g = _sample_graph(engine)
        neighbors = engine.get_neighbors("alice", min_strength=0.9, max_depth=1)
        assert set(neighbors) == {"acme", "doc"}

    def test_no_neighbors(self, engine: RelationshipEngine):
        neighbors = engine.get_neighbors("lonely", max_depth=1)
        assert neighbors == []

    def test_self_is_excluded(self, engine: RelationshipEngine):
        engine.add_relationship("a", "b", "owns")
        neighbors = engine.get_neighbors("a", max_depth=1)
        assert "a" not in neighbors


class TestPathFinding:
    def test_direct_path(self, engine: RelationshipEngine):
        g = _sample_graph(engine)
        path = engine.find_path("alice", "acme", max_depth=3)
        assert len(path) == 1
        assert path[0].relationship_type == RelationshipType.MEMBER_OF

    def test_two_hop_path(self, engine: RelationshipEngine):
        g = _sample_graph(engine)
        path = engine.find_path("alice", "mega_corp", max_depth=5)
        assert len(path) == 2
        assert path[0].target_id == "acme"
        assert path[1].target_id == "mega_corp"

    def test_no_path(self, engine: RelationshipEngine):
        g = _sample_graph(engine)
        path = engine.find_path("alice", "charlie", max_depth=2)
        # alice -> bob -> charlie is 2 hops via bob->charlie reports_to
        # Actually let's verify: alice --reports_to-> bob --reports_to-> charlie
        path = engine.find_path("alice", "charlie", max_depth=5)
        assert len(path) > 0

    def test_path_to_self_returns_empty(self, engine: RelationshipEngine):
        g = _sample_graph(engine)
        path = engine.find_path("alice", "alice", max_depth=5)
        assert path == []

    def test_path_below_max_depth(self, engine: RelationshipEngine):
        g = _sample_graph(engine)
        path = engine.find_path("alice", "mega_corp", max_depth=1)
        assert path == []  # 2 hops needed

    def test_path_with_type_filter(self, engine: RelationshipEngine):
        g = _sample_graph(engine)
        path = engine.find_path("alice", "mega_corp", type_filter="works_at")
        # No works_at path alice -> ... -> mega_corp directly
        assert path == []


class TestSubgraph:
    def test_subgraph_depth_1(self, engine: RelationshipEngine):
        g = _sample_graph(engine)
        sg = engine.get_subgraph("alice", depth=1)
        assert set(sg.keys()) == {"alice", "acme", "bob", "doc"}

    def test_subgraph_depth_2(self, engine: RelationshipEngine):
        g = _sample_graph(engine)
        sg = engine.get_subgraph("alice", depth=2)
        assert "mega_corp" in sg
        assert "charlie" in sg

    def test_subgraph_filtered(self, engine: RelationshipEngine):
        g = _sample_graph(engine)
        sg = engine.get_subgraph("alice", depth=2, type_filter="reports_to")
        # Only reports_to edges: alice->bob, bob->charlie
        assert "alice" in sg
        assert "bob" in sg
        assert "charlie" in sg
        assert "acme" not in sg  # member_of, not reports_to

    def test_isolated_node_subgraph(self, engine: RelationshipEngine):
        sg = engine.get_subgraph("lonely", depth=2)
        assert sg == {"lonely": []}


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

class TestValidate:
    def test_valid_relationship(self, engine: RelationshipEngine):
        rel = engine.add_relationship("a", "b", "owns")
        assert engine.validate_relationship(rel)

    def test_invalid_empty_source(self, engine: RelationshipEngine):
        with pytest.raises(ValueError, match="source_id must be a non-empty string"):
            Relationship(source_id="", target_id="b")

    def test_invalid_same_object(self, engine: RelationshipEngine):
        with pytest.raises(ValueError, match="must be different"):
            Relationship(source_id="a", target_id="a")

    def test_invalid_strength(self, engine: RelationshipEngine):
        with pytest.raises(ValueError):
            Relationship(source_id="a", target_id="b", strength=2.0)

    def test_invalid_relationship_type(self, engine: RelationshipEngine):
        """validate_relationship should reject non-enum types."""
        # Can't create via constructor due to type hint — test via duck
        rel = Relationship.__new__(Relationship)
        object.__setattr__(rel, 'source_id', 'a')
        object.__setattr__(rel, 'target_id', 'b')
        object.__setattr__(rel, 'relationship_type', "invalid_type")
        object.__setattr__(rel, 'direction', RelationshipDirection.DIRECTIONAL)
        object.__setattr__(rel, 'strength', 1.0)
        object.__setattr__(rel, 'status', RelationshipStatus.ACTIVE)
        object.__setattr__(rel, 'valid_from', None)
        object.__setattr__(rel, 'valid_until', None)
        assert not engine.validate_relationship(rel)


# ---------------------------------------------------------------------------
# Clear / Reset
# ---------------------------------------------------------------------------

class TestEngineLifecycle:
    def test_clear(self, engine: RelationshipEngine):
        _sample_graph(engine)
        assert engine.get_relationship_count("alice") > 0
        engine.clear()
        assert len(engine.get_all_relationships()) == 0
        assert engine.get_relationship_count("alice") == 0

    def test_get_all_relationships(self, engine: RelationshipEngine):
        g = _sample_graph(engine)
        all_rels = engine.get_all_relationships()
        assert len(all_rels) == 7

    def test_get_all_relationships_empty(self, engine: RelationshipEngine):
        assert engine.get_all_relationships() == []


# ---------------------------------------------------------------------------
# Singleton convenience
# ---------------------------------------------------------------------------

class TestSingleton:
    def test_get_relationship_engine_returns_instance(self):
        eng = get_relationship_engine()
        assert isinstance(eng, RelationshipEngine)

    def test_singleton_is_persistent(self):
        eng1 = get_relationship_engine()
        eng2 = get_relationship_engine()
        assert eng1 is eng2
        eng1.clear()  # clean up


# ---------------------------------------------------------------------------
# Temporal queries
# ---------------------------------------------------------------------------

class TestTemporal:
    def test_is_active_now(self, engine: RelationshipEngine):
        rel = engine.add_relationship("a", "b", "owns")
        assert rel.is_active_now

    def test_is_active_now_future_valid_from(self, engine: RelationshipEngine):
        future = datetime.now(timezone.utc) + timedelta(days=30)
        rel = engine.add_relationship(
            "a", "b", "owns",
            valid_from=future,
        )
        assert not rel.is_active_now

    def test_is_active_now_expired(self, engine: RelationshipEngine):
        past = datetime.now(timezone.utc) - timedelta(days=1)
        rel = engine.add_relationship(
            "a", "b", "owns",
            valid_until=past,
        )
        assert not rel.is_active_now

    def test_is_valid_at(self, engine: RelationshipEngine):
        now = datetime.now(timezone.utc)
        future = now + timedelta(days=30)
        rel = engine.add_relationship("a", "b", "owns", valid_from=now, valid_until=future)
        assert rel.is_valid_at(now + timedelta(days=15))
        assert not rel.is_valid_at(now - timedelta(days=1))
        assert not rel.is_valid_at(future + timedelta(days=1))


# ---------------------------------------------------------------------------
# Reversed relationship
# ---------------------------------------------------------------------------

class TestReverse:
    def test_reversed_swaps_source_target(self, engine: RelationshipEngine):
        rel = engine.add_relationship("a", "b", "owns")
        rev = rel.reversed()
        assert rev.source_id == "b"
        assert rev.target_id == "a"
        assert rev.relationship_type == RelationshipType.OWNS
        assert rev.strength == rel.strength
        assert rev.relationship_id != rel.relationship_id


# ---------------------------------------------------------------------------
# Filter edge cases
# ---------------------------------------------------------------------------

class TestFilterEdgeCases:
    def test_matches_type_none(self, engine: RelationshipEngine):
        from core.relationship import matches_type
        rel = engine.add_relationship("a", "b", "owns")
        assert matches_type(rel, None)

    def test_matches_type_string(self, engine: RelationshipEngine):
        from core.relationship import matches_type
        rel = engine.add_relationship("a", "b", "owns")
        assert matches_type(rel, "owns")
        assert not matches_type(rel, "member_of")

    def test_matches_strength_none(self, engine: RelationshipEngine):
        from core.relationship import matches_strength
        rel = engine.add_relationship("a", "b", "owns", strength=0.5)
        assert matches_strength(rel, None)

    def test_matches_strength_threshold(self, engine: RelationshipEngine):
        from core.relationship import matches_strength
        rel = engine.add_relationship("a", "b", "owns", strength=0.5)
        assert matches_strength(rel, 0.4)
        assert not matches_strength(rel, 0.6)
