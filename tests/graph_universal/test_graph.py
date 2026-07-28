"""
Tests for SHUNYA Universal Business Graph — Phase Z10.

Validates: Entity lifecycle, Identity resolution, Relationship graph,
Property versioning, Graph events, Traversal, Inspection, Agnosticism.
"""

import pytest
from app.graph_universal.entity import Entity, get_store, reset_store
from app.graph_universal.relationship import Relationship, get_store as get_rel_store, reset_store as reset_rel_store
from app.graph_universal.identity import IdentityResolver, get_resolver, reset_resolver
from app.graph_universal.property import PropertyVersion, get_store as get_prop_store, reset_store as reset_prop_store
from app.graph_universal.event import GraphEvent, get_store as get_event_store, reset_store as reset_event_store
from app.graph_universal.traversal import GraphQueryEngine, get_engine, reset_engine


# ══════════════════════════════════════════════════════════════
# Entity Tests
# ══════════════════════════════════════════════════════════════


class TestEntity:
    def test_create_entity(self):
        e = Entity(entity_id="e1", name="Test Corp", entity_type="organization")
        assert e.entity_id == "e1"
        assert e.entity_type == "organization"
        assert e.status == "active"

    def test_entity_with_aliases(self):
        e = Entity(entity_id="e1", name="Test Corp", entity_type="organization", aliases=["TC", "TestCo"])
        assert len(e.aliases) == 2
        assert "TC" in e.aliases

    def test_entity_to_dict(self):
        e = Entity(entity_id="e1", name="Test", entity_type="person")
        d = e.to_dict()
        assert d["entity_id"] == "e1"
        assert d["entity_type"] == "person"


class TestEntityStore:
    def setup_method(self):
        reset_store()

    def test_add_and_get(self):
        store = get_store()
        store.add(Entity(entity_id="e1", name="T", entity_type="org"))
        assert store.get("e1") is not None
        assert store.count == 1

    def test_get_by_type(self):
        store = get_store()
        store.add(Entity(entity_id="e1", name="T1", entity_type="org"))
        store.add(Entity(entity_id="e2", name="T2", entity_type="person"))
        assert len(store.get_by_type("org")) == 1
        assert len(store.get_by_type("person")) == 1

    def test_find_by_alias(self):
        store = get_store()
        store.add(Entity(entity_id="e1", name="Test Corp", entity_type="org", aliases=["TC"]))
        assert store.find_by_alias("TC") is not None
        assert store.find_by_alias("Test Corp") is not None
        assert store.find_by_alias("Nonexistent") is None


# ══════════════════════════════════════════════════════════════
# Identity Resolution Tests
# ══════════════════════════════════════════════════════════════


class TestIdentity:
    def setup_method(self):
        reset_store()
        reset_resolver()

    def test_register_and_resolve(self):
        store = get_store()
        e = Entity(entity_id="e1", name="Test", entity_type="org", aliases=["T"])
        store.add(e)
        ir = get_resolver()
        ir.register(e)
        assert ir.resolve("e1") is e
        assert ir.resolve("T") is e

    def test_merge(self):
        store = get_store()
        e1 = Entity(entity_id="e1", name="Primary", entity_type="org", aliases=["P"])
        e2 = Entity(entity_id="e2", name="Secondary", entity_type="org", aliases=["S"])
        store.add(e1)
        store.add(e2)
        ir = get_resolver()
        ir.register(e1)
        ir.register(e2)
        merged = ir.merge("e1", "e2")
        assert merged is not None
        assert "e2" in merged.merged_entity_ids
        assert "S" in merged.aliases


# ══════════════════════════════════════════════════════════════
# Relationship Tests
# ══════════════════════════════════════════════════════════════


class TestRelationship:
    def setup_method(self):
        reset_rel_store()

    def test_add_relationship(self):
        store = get_rel_store()
        r = Relationship(rel_id="r1", source_id="e1", target_id="e2", rel_type="manages")
        store.add(r)
        assert store.count == 1

    def test_get_for_entity(self):
        store = get_rel_store()
        store.add(Relationship(rel_id="r1", source_id="e1", target_id="e2", rel_type="manages"))
        store.add(Relationship(rel_id="r2", source_id="e2", target_id="e3", rel_type="owns"))
        assert len(store.get_for_entity("e1")) == 1
        assert len(store.get_for_entity("e2")) == 2

    def test_get_neighbors(self):
        store = get_rel_store()
        store.add(Relationship(rel_id="r1", source_id="e1", target_id="e2", rel_type="manages"))
        store.add(Relationship(rel_id="r2", source_id="e1", target_id="e3", rel_type="owns"))
        nbrs = store.get_neighbors("e1")
        assert len(nbrs) == 2
        assert "e2" in nbrs
        assert "e3" in nbrs


# ══════════════════════════════════════════════════════════════
# Property Versioning Tests
# ══════════════════════════════════════════════════════════════


class TestProperty:
    def setup_method(self):
        reset_prop_store()

    def test_set_property(self):
        store = get_prop_store()
        pv = store.set_property("e1", "revenue", 1000000, source="filing")
        assert pv.entity_id == "e1"
        assert pv.key == "revenue"
        assert pv.value == 1000000
        assert pv.version == 1

    def test_get_current(self):
        store = get_prop_store()
        store.set_property("e1", "revenue", 1000000)
        store.set_property("e1", "revenue", 2000000)
        current = store.get_current("e1", "revenue")
        assert current.value == 2000000
        assert current.version == 2

    def test_get_history(self):
        store = get_prop_store()
        store.set_property("e1", "employees", 100)
        store.set_property("e1", "employees", 120)
        store.set_property("e1", "employees", 150)
        history = store.get_history("e1", "employees")
        assert len(history) == 3
        assert history[0].value == 100
        assert history[2].value == 150

    def test_immutability(self):
        store = get_prop_store()
        pv = store.set_property("e1", "name", "Original")
        with pytest.raises(Exception):
            pv.value = "Modified"  # Frozen dataclass


# ══════════════════════════════════════════════════════════════
# Graph Event Tests
# ══════════════════════════════════════════════════════════════


class TestGraphEvent:
    def setup_method(self):
        reset_event_store()

    def test_record_event(self):
        store = get_event_store()
        evt = store.record("entity_created", "e1", {"name": "Test"})
        assert evt.event_type == "entity_created"
        assert store.count == 1

    def test_get_events_by_entity(self):
        store = get_event_store()
        store.record("entity_created", "e1")
        store.record("entity_created", "e2")
        store.record("relationship_added", "e1")
        events = store.get_events(entity_id="e1")
        assert len(events) == 2


# ══════════════════════════════════════════════════════════════
# Graph Traversal Tests
# ══════════════════════════════════════════════════════════════


class TestGraphTraversal:
    def setup_method(self):
        reset_store()
        reset_rel_store()

    def test_lookup(self):
        store = get_store()
        store.add(Entity(entity_id="e1", name="Test", entity_type="org"))
        engine = get_engine()
        assert engine.lookup("e1") is not None
        assert engine.lookup("nonexistent") is None

    def test_neighbors(self):
        store = get_store()
        rel_store = get_rel_store()
        for eid in ["e1", "e2", "e3"]:
            store.add(Entity(entity_id=eid, name=f"E{eid}", entity_type="org"))
        rel_store.add(Relationship(rel_id="r1", source_id="e1", target_id="e2", rel_type="link"))
        rel_store.add(Relationship(rel_id="r2", source_id="e1", target_id="e3", rel_type="link"))

        engine = get_engine()
        nbrs = engine.neighbors("e1", max_depth=1)
        assert "depth_1" in nbrs
        assert len(nbrs["depth_1"]) == 2

    def test_shortest_path(self):
        store = get_store()
        rel_store = get_rel_store()
        for eid in ["e1", "e2", "e3", "e4"]:
            store.add(Entity(entity_id=eid, name=f"E{eid}", entity_type="org"))
        rel_store.add(Relationship(rel_id="r1", source_id="e1", target_id="e2", rel_type="link"))
        rel_store.add(Relationship(rel_id="r2", source_id="e2", target_id="e3", rel_type="link"))
        rel_store.add(Relationship(rel_id="r3", source_id="e3", target_id="e4", rel_type="link"))

        engine = get_engine()
        path = engine.shortest_path("e1", "e4")
        assert path is not None
        assert len(path) == 4
        assert path == ["e1", "e2", "e3", "e4"]

    def test_search(self):
        store = get_store()
        store.add(Entity(entity_id="e1", name="Jupiter Media", entity_type="org", aliases=["JMC"]))
        store.add(Entity(entity_id="e2", name="Nexus Ventures", entity_type="org"))
        engine = get_engine()
        results = engine.search("jupiter")
        assert len(results) == 1
        assert results[0].entity_id == "e1"


# ══════════════════════════════════════════════════════════════
# Business Agnosticism Tests
# ══════════════════════════════════════════════════════════════


class TestBusinessAgnosticism:
    def test_entity_no_industry(self):
        e = Entity(entity_id="e1", name="T", entity_type="custom_type")
        assert not hasattr(e, "industry")
        assert not hasattr(e, "vertical")

    def test_relationship_no_industry(self):
        r = Relationship(rel_id="r1", source_id="s", target_id="t", rel_type="custom_rel")
        assert not hasattr(r, "project")

    def test_property_agnostic_types(self):
        store = get_prop_store()
        for val in ["string", 42, 3.14, True, ["a", "b"], {"key": "val"}]:
            pv = store.set_property("e1", "test", val)
            assert pv.value == val


# ══════════════════════════════════════════════════════════════
# Integration Tests
# ══════════════════════════════════════════════════════════════


class TestGraphIntegration:
    def test_graph_loads_with_app(self):
        from app import create_app
        app = create_app({'TESTING': True, 'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:'})
        with app.test_client() as c:
            assert c.get('/').status_code == 200
            assert c.get('/workspace/').status_code == 200
            r = c.get('/workspace/?inspect_graph=1')
            assert r.status_code == 200
            data = r.get_json()
            assert data is not None
            assert 'entities' in data
            assert 'relationships' in data
            assert 'identities' in data
            assert 'properties' in data
            assert 'events' in data

    def test_entities_loaded_on_startup(self):
        from app import create_app
        app = create_app({'TESTING': True, 'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:'})
        with app.test_client() as c:
            r = c.get('/workspace/?inspect_graph=1')
            data = r.get_json()
            assert data['entities']['total'] >= 4
            assert data['relationships']['total'] >= 2
            assert data['properties']['total'] >= 1
            assert data['events']['total'] >= 1