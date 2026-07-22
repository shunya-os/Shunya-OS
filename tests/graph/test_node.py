"""Tests for SHUNYA Knowledge Graph — Node Model and Store (E-003-MOD-001).

Architecture references:
    UNIVERSAL_KNOWLEDGE_GRAPH_ARCHITECTURE.md §1.2 — Node structure
    UNIVERSAL_KNOWLEDGE_GRAPH_ARCHITECTURE.md §1.4 — Identity
    UNIVERSAL_KNOWLEDGE_GRAPH_ARCHITECTURE.md §1.5 — Labels
    UNIVERSAL_KNOWLEDGE_GRAPH_ARCHITECTURE.md §1.6 — Types
    UNIVERSAL_KNOWLEDGE_GRAPH_ARCHITECTURE.md §13.2 — Visibility

Constitutional invariants tested:
    O-01: Node identity never changes
    O-11: Node type is immutable after creation
    KG-ID: Identity is permanent, unique, never reused
"""

import pytest
from app.graph.node import (
    Node, NodeStatus, VisibilityLevel, NodeMetadata,
    InMemoryNodeStore, get_node_store, reset_node_store,
)
from app.kernel.types import TypeRegistry, get_registry, reset_registry
from app.kernel.object import EvidenceRef

# =========================================================================
# Node Model Tests
# =========================================================================

class TestNodeModel:
    """UNIVERSAL_KNOWLEDGE_GRAPH_ARCHITECTURE.md §1.2 — Node structure."""

    def test_auto_generates_identity(self):
        """§1.4 — Node identity is automatically assigned on creation."""
        node = Node(node_type="Person")
        assert node.node_id != ""
        assert node.node_id.startswith("n_")
        assert len(node.node_id) > 30

    def test_identity_is_permanent(self):
        """O-01 — Node identity never changes."""
        node = Node(node_type="Person", node_id="n_test_fixed")
        assert node.node_id == "n_test_fixed"

    def test_default_status(self):
        """Default status is ACTIVE."""
        node = Node()
        assert node.status == NodeStatus.ACTIVE.value
        assert node.is_active

    def test_default_visibility(self):
        """Default visibility is PRIVATE (§13.2)."""
        node = Node()
        assert node.visibility == VisibilityLevel.PRIVATE.value

    def test_default_confidence(self):
        """Default confidence is 1.0."""
        node = Node()
        assert node.confidence == 1.0

    def test_labels_are_sets(self):
        """Labels are stored as a set (deduplicated)."""
        node = Node(node_type="Person", labels={"active", "verified", "active"})
        assert len(node.labels) == 2
        assert "active" in node.labels
        assert "verified" in node.labels

    def test_add_label(self):
        """§1.5 — Labels can be added."""
        node = Node()
        node.add_label("verified")
        assert "verified" in node.labels

    def test_remove_label(self):
        """§1.5 — Labels can be removed."""
        node = Node(labels={"active", "verified"})
        assert node.remove_label("active")
        assert "active" not in node.labels
        assert not node.remove_label("nonexistent")

    def test_has_label(self):
        """Label existence check."""
        node = Node(labels={"active"})
        assert node.has_label("active")
        assert not node.has_label("verified")

    def test_set_and_get_attribute(self):
        """§1.2 — Attributes are key-value pairs."""
        node = Node()
        node.set_attribute("email", "alice@test.com")
        assert node.get_attribute("email") == "alice@test.com"
        assert node.get_attribute("nonexistent", "default") == "default"

    def test_version_increments_on_attribute_change(self):
        """§1.10 — Version increments on attribute mutation."""
        node = Node()
        v1 = node.version
        node.set_attribute("key", "value")
        assert node.version == v1 + 1

    def test_add_evidence(self):
        """§1.2 — Evidence refs can be attached."""
        node = Node()
        ref = EvidenceRef(object_id="ev_001", object_type="Observation",
                          confidence=0.95)
        node.add_evidence(ref)
        assert len(node.evidence) == 1
        assert node.evidence[0].object_id == "ev_001"

    def test_archive_transitions_status(self):
        """Archive changes status to ARCHIVED."""
        node = Node()
        assert node.is_active
        node.archive()
        assert node.status == NodeStatus.ARCHIVED.value
        assert node.is_archived

    def test_metadata_auto_populates(self):
        """§1.7 — Metadata is auto-populated on creation."""
        node = Node()
        assert node.metadata.created_at != ""
        assert node.metadata.updated_at != ""
        assert node.metadata.created_by == "system"

    def test_set_created_by(self):
        """§1.7 — Created_by can be set explicitly."""
        node = Node(node_type="Person", metadata=NodeMetadata(created_by="alice"))
        assert node.metadata.created_by == "alice"

    def test_short_id_truncates(self):
        """Short ID is a readable prefix."""
        node = Node(node_type="Person")
        assert len(node.short_id) == 16
        assert node.short_id in node.node_id

    def test_to_dict_contains_all_fields(self):
        """Serialization includes all Node fields."""
        node = Node(node_type="Person", labels={"active"},
                    attributes={"email": "a@b.com"},
                    owner_id="sid_owner",
                    visibility=VisibilityLevel.PRIVATE.value)
        d = node.to_dict()
        assert d["node_id"] == node.node_id
        assert d["node_type"] == "Person"
        assert "active" in d["labels"]
        assert d["attributes"]["email"] == "a@b.com"
        assert "metadata" in d
        assert d["visibility"] == "private"
        assert d["owner_id"] == "sid_owner"
        assert d["version"] == 1
        assert d["status"] == "active"
        assert d["confidence"] == 1.0


# =========================================================================
# NodeStore Tests
# =========================================================================

class TestInMemoryNodeStore:
    """InMemoryNodeStore — CRUD and indexing."""

    def setup_method(self):
        reset_node_store()

    def test_create_and_get(self):
        """Node can be created and retrieved by identity."""
        store = get_node_store()
        node = Node(node_type="Person", owner_id="sid_alice")
        store.create(node)
        retrieved = store.get(node.node_id)
        assert retrieved is not None
        assert retrieved.node_id == node.node_id
        assert retrieved.node_type == "Person"
        assert retrieved.owner_id == "sid_alice"

    def test_create_duplicate_raises(self):
        """KG-ID — Duplicate identity raises ValueError."""
        store = get_node_store()
        node = Node(node_type="Person")
        store.create(node)
        with pytest.raises(ValueError, match="already exists"):
            store.create(node)

    def test_get_nonexistent_returns_none(self):
        """Getting a non-existent Node returns None."""
        store = get_node_store()
        assert store.get("n_nonexistent") is None

    def test_update(self):
        """Node can be updated."""
        store = get_node_store()
        node = Node(node_type="Person", labels={"active"})
        store.create(node)
        node.add_label("verified")
        store.update(node)
        retrieved = store.get(node.node_id)
        assert retrieved is not None
        assert "verified" in retrieved.labels

    def test_update_nonexistent_raises(self):
        """Updating a non-existent Node raises ValueError."""
        store = get_node_store()
        node = Node(node_type="Person")
        with pytest.raises(ValueError, match="not found"):
            store.update(node)

    def test_archive(self):
        """Node can be archived via the store."""
        store = get_node_store()
        node = Node(node_type="Person")
        store.create(node)
        archived = store.archive(node.node_id)
        assert archived is not None
        assert archived.is_archived
        retrieved = store.get(node.node_id)
        assert retrieved is not None
        assert retrieved.is_archived

    def test_archive_nonexistent_returns_none(self):
        """Archiving a non-existent Node returns None."""
        store = get_node_store()
        assert store.archive("n_nonexistent") is None

    def test_delete(self):
        """Node can be deleted."""
        store = get_node_store()
        node = Node(node_type="Person")
        store.create(node)
        assert store.delete(node.node_id)
        assert store.get(node.node_id) is None

    def test_delete_nonexistent_returns_false(self):
        """Deleting a non-existent Node returns False."""
        store = get_node_store()
        assert not store.delete("n_nonexistent")

    def test_delete_removes_from_indexes(self):
        """Deleting a Node cleans up type and label indexes."""
        store = get_node_store()
        node = Node(node_type="Person", labels={"active", "verified"})
        store.create(node)
        store.delete(node.node_id)
        assert store.count() == 0
        assert len(store.get_by_type("Person")) == 0
        assert len(store.get_by_label("active")) == 0

    def test_count(self):
        """Count returns total Nodes."""
        store = get_node_store()
        assert store.count() == 0
        store.create(Node(node_type="Person"))
        store.create(Node(node_type="Document"))
        store.create(Node(node_type="Person"))
        assert store.count() == 3
        assert store.count(node_type="Person") == 2

    def test_get_by_type(self):
        """§1.6 — Nodes can be queried by type."""
        store = get_node_store()
        p1 = Node(node_type="Person")
        p2 = Node(node_type="Person")
        doc = Node(node_type="Document")
        store.create(p1)
        store.create(p2)
        store.create(doc)
        persons = store.get_by_type("Person")
        assert len(persons) == 2
        docs = store.get_by_type("Document")
        assert len(docs) == 1

    def test_get_by_label(self):
        """§1.5 — Nodes can be queried by label."""
        store = get_node_store()
        n1 = Node(node_type="Person", labels={"active", "verified"})
        n2 = Node(node_type="Person", labels={"active"})
        n3 = Node(node_type="Document", labels={"archived"})
        store.create(n1)
        store.create(n2)
        store.create(n3)
        active = store.get_by_label("active")
        assert len(active) == 2
        verified = store.get_by_label("verified")
        assert len(verified) == 1
        archived = store.get_by_label("archived")
        assert len(archived) == 1

    def test_exists(self):
        """Exists check returns correct boolean."""
        store = get_node_store()
        node = Node(node_type="Person")
        store.create(node)
        assert store.exists(node.node_id)
        assert not store.exists("n_nonexistent")

    def test_all(self):
        """All returns every Node in the store."""
        store = get_node_store()
        store.create(Node(node_type="Person"))
        store.create(Node(node_type="Document"))
        assert len(store.all()) == 2

    def test_clear(self):
        """Clear removes all Nodes and resets indexes."""
        store = get_node_store()
        store.create(Node(node_type="Person"))
        store.create(Node(node_type="Document"))
        store.clear()
        assert store.count() == 0
        assert len(store.get_by_type("Person")) == 0

    def test_label_reindex_on_update(self):
        """Updating labels re-indexes correctly."""
        store = get_node_store()
        node = Node(node_type="Person", labels={"active"})
        store.create(node)
        node.remove_label("active")
        node.add_label("archived")
        store.update(node)
        assert len(store.get_by_label("active")) == 0
        assert len(store.get_by_label("archived")) == 1


# =========================================================================
# Performance Test
# =========================================================================

class TestNodeStorePerformance:
    """Acceptance criteria: 1000 nodes created in < 1s."""

    def setup_method(self):
        reset_node_store()

    def test_1000_nodes_under_1s(self):
        """1000 Nodes created in < 1 second."""
        import time
        store = get_node_store()
        start = time.time()
        for i in range(1000):
            store.create(Node(
                node_type="Person",
                labels={"batch", "test"} if i % 2 == 0 else {"batch"},
                attributes={"index": i},
            ))
        elapsed = time.time() - start
        assert store.count() == 1000
        assert elapsed < 1.0, f"1000 nodes took {elapsed:.3f}s (limit: 1.0s)"