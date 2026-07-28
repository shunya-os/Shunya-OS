"""
Tests for SHUNYA Knowledge Graph — Graph Validator (E-003-MOD-004).

Architecture references:
    UNIVERSAL_KNOWLEDGE_GRAPH_ARCHITECTURE.md §3.4 — Edge validation
    UNIVERSAL_KNOWLEDGE_GRAPH_ARCHITECTURE.md §1.4  — Identity
    UNIVERSAL_KNOWLEDGE_GRAPH_ARCHITECTURE.md §1.6  — Types
    UNIVERSAL_KNOWLEDGE_GRAPH_ARCHITECTURE.md §1.9  — Confidence
    UNIVERSAL_KNOWLEDGE_GRAPH_ARCHITECTURE.md §1.10 — Versioning
    UNIVERSAL_KNOWLEDGE_GRAPH_ARCHITECTURE.md §13.2 — Visibility
    UNIVERSAL_KNOWLEDGE_GRAPH_ARCHITECTURE.md §3.2.1 — Source/target existence
    UNIVERSAL_KNOWLEDGE_GRAPH_ARCHITECTURE.md §3.2.3 — Triple uniqueness
    UNIVERSAL_KNOWLEDGE_GRAPH_ARCHITECTURE.md §3.4.5 — Edge type compatibility

Constitutional invariants tested:
    O-01: Node identity never changes
    O-11: Node type is immutable after creation
    KG-ID: Identity is permanent, unique, never reused
    KG-01: No duplicate (source, target, type) triples
    KG-02: Source and target must exist in the graph
    KG-03: Edge type compatible with source/target families
"""

import pytest
from app.graph.node import (
    Node, InMemoryNodeStore, get_node_store, reset_node_store,
    NodeStatus, VisibilityLevel,
)
from app.graph.edge import (
    Edge, InMemoryEdgeStore, get_edge_store, reset_edge_store,
    EdgeDirection, EdgeStatus,
)
from app.graph.consistency import (
    GraphValidator, ValidationResult, ValidationError,
    E_NODE_ID_EMPTY, E_NODE_TYPE_UNKNOWN,
    E_NODE_CONFIDENCE_RANGE, E_NODE_CONFIDENCE_NEGATIVE,
    E_NODE_VERSION_LT_ONE, E_NODE_STATUS_INVALID,
    E_NODE_VISIBILITY_INVALID,
    E_EDGE_SOURCE_MISSING, E_EDGE_TARGET_MISSING,
    E_EDGE_TRIPLE_DUPLICATE, E_EDGE_TYPE_UNKNOWN,
    E_EDGE_CONFIDENCE_RANGE, E_EDGE_CONFIDENCE_NEGATIVE,
    E_EDGE_DIRECTION_INVALID, E_EDGE_STATUS_INVALID,
    E_EDGE_TYPE_INCOMPATIBLE,
    E_INV_NODE_ID_DUPLICATE,
    W_NODE_NO_LABELS, W_NODE_NO_OWNER, W_NODE_NO_EVIDENCE,
    W_EDGE_NO_EVIDENCE, W_EDGE_LOW_CONFIDENCE, W_EDGE_ZERO_WEIGHT,
)
from app.kernel.types import reset_registry
from app.kernel.object import EvidenceRef


# =========================================================================
# Fixtures
# =========================================================================


@pytest.fixture(autouse=True)
def reset_stores():
    """Reset all stores and registries before each test."""
    reset_registry()
    reset_node_store()
    reset_edge_store()
    yield


@pytest.fixture
def node_store():
    return get_node_store()


@pytest.fixture
def edge_store():
    return get_edge_store()


@pytest.fixture
def validator(node_store, edge_store):
    return GraphValidator(node_store=node_store, edge_store=edge_store)


@pytest.fixture
def person_node():
    return Node(node_type="Person", owner_id="user_1")


@pytest.fixture
def org_node():
    return Node(node_type="Organization", owner_id="user_1")


@pytest.fixture
def doc_node():
    return Node(node_type="Document", owner_id="user_2")


# =========================================================================
# ValidationResult Tests
# =========================================================================


class TestValidationResult:
    """ValidationResult — structured output container."""

    def test_empty_result_is_valid(self):
        """An empty result is valid with no errors or warnings."""
        result = ValidationResult()
        assert result.is_valid
        assert result.error_count == 0
        assert result.warning_count == 0
        assert result.node_count == 0
        assert result.edge_count == 0

    def test_summary_valid(self):
        """Summary reports VALID when no errors."""
        result = ValidationResult(node_count=5, edge_count=3)
        assert "VALID" in result.summary
        assert "5 node(s)" in result.summary
        assert "3 edge(s)" in result.summary

    def test_summary_invalid(self):
        """Summary reports INVALID with error count."""
        result = ValidationResult(node_count=1, edge_count=0)
        result.errors.append(ValidationError(
            code=E_NODE_ID_EMPTY, message="Empty ID"
        ))
        assert not result.is_valid
        assert "INVALID" in result.summary
        assert "1 error(s)" in result.summary

    def test_merge(self):
        """Merge combines two results."""
        r1 = ValidationResult(node_count=2, edge_count=1)
        r2 = ValidationResult(node_count=3, edge_count=4)
        r2.errors.append(ValidationError(
            code=E_NODE_ID_EMPTY, message="Empty ID"
        ))
        r1.merge(r2)
        assert r1.error_count == 1

    def test_to_dict(self):
        """Serialization to dictionary works."""
        result = ValidationResult(node_count=1)
        result.errors.append(ValidationError(
            code=E_NODE_ID_EMPTY, message="Empty ID",
            node_id="n_test",
        ))
        d = result.to_dict()
        assert not d["is_valid"]  # errors make it invalid
        assert d["node_count"] == 1
        assert d["error_count"] == 1
        assert d["errors"][0]["code"] == E_NODE_ID_EMPTY
        assert d["errors"][0]["node_id"] == "n_test"


# =========================================================================
# Node Validation Tests
# =========================================================================


class TestNodeValidation:
    """GraphValidator.validate_nodes — Node-level checks."""

    def test_valid_node_passes(self, validator, person_node):
        """A well-formed Node passes validation."""
        result = validator.validate_node(person_node)
        assert result.is_valid
        assert result.error_count == 0

    def test_empty_node_id_fails(self, validator):
        """E-NODE-001: Node with empty identity fails.

        Uses object.__new__ to bypass __post_init__ auto-ID generation.
        """
        node = object.__new__(Node)
        node.node_id = ""
        node.node_type = "Person"
        node.owner_id = "u1"
        node.labels = set()
        node.attributes = {}
        node.evidence = []
        node.metadata = type('NM', (), {'created_at': '', 'updated_at': '',
                                        'created_by': '', 'provenance': ''})()
        node.confidence = 1.0
        node.version = 1
        node.status = "active"
        node.visibility = "private"
        result = validator.validate_node(node)
        assert not result.is_valid
        codes = [e.code for e in result.errors]
        assert E_NODE_ID_EMPTY in codes

    def test_unknown_type_fails(self, validator):
        """E-NODE-003: Node with unregistered type fails."""
        node = Node(node_type="NonExistentType123", owner_id="u1")
        result = validator.validate_node(node)
        assert not result.is_valid
        codes = [e.code for e in result.errors]
        assert E_NODE_TYPE_UNKNOWN in codes

    def test_confidence_too_high_fails(self, validator):
        """E-NODE-004: Node with confidence > 1.0 fails."""
        node = Node(node_type="Person", confidence=1.5, owner_id="u1")
        result = validator.validate_node(node)
        assert not result.is_valid
        codes = [e.code for e in result.errors]
        assert E_NODE_CONFIDENCE_RANGE in codes

    def test_confidence_negative_fails(self, validator):
        """E-NODE-008: Node with negative confidence fails."""
        node = Node(node_type="Person", confidence=-0.5, owner_id="u1")
        result = validator.validate_node(node)
        assert not result.is_valid
        codes = [e.code for e in result.errors]
        assert E_NODE_CONFIDENCE_NEGATIVE in codes

    def test_confidence_zero_passes(self, validator):
        """Confidence of exactly 0.0 is valid."""
        node = Node(node_type="Person", confidence=0.0, owner_id="u1")
        result = validator.validate_node(node)
        assert result.is_valid

    def test_version_zero_fails(self, validator):
        """E-NODE-005: Node with version < 1 fails."""
        node = Node(node_type="Person", version=0, owner_id="u1")
        result = validator.validate_node(node)
        assert not result.is_valid
        codes = [e.code for e in result.errors]
        assert E_NODE_VERSION_LT_ONE in codes

    def test_version_negative_fails(self, validator):
        """E-NODE-005: Node with negative version fails."""
        node = Node(node_type="Person", version=-3, owner_id="u1")
        result = validator.validate_node(node)
        assert not result.is_valid
        codes = [e.code for e in result.errors]
        assert E_NODE_VERSION_LT_ONE in codes

    def test_invalid_status_fails(self, validator):
        """E-NODE-006: Node with invalid status fails."""
        node = Node(node_type="Person", status="invalid_status", owner_id="u1")
        result = validator.validate_node(node)
        assert not result.is_valid
        codes = [e.code for e in result.errors]
        assert E_NODE_STATUS_INVALID in codes

    def test_invalid_visibility_fails(self, validator):
        """E-NODE-007: Node with invalid visibility fails."""
        node = Node(node_type="Person", visibility="top_secret", owner_id="u1")
        result = validator.validate_node(node)
        assert not result.is_valid
        codes = [e.code for e in result.errors]
        assert E_NODE_VISIBILITY_INVALID in codes

    def test_multiple_nodes_batch(self, validator):
        """Batch validation collects errors from all nodes."""
        node1 = Node(node_type="Person", owner_id="u1")
        node2 = Node(node_type="NonExistent", owner_id="u2")
        node3 = Node(node_type="Document", owner_id="u3", confidence=2.0)
        result = validator.validate_nodes(nodes=[node1, node2, node3])
        assert not result.is_valid
        assert result.error_count == 2
        assert result.node_count == 3


# =========================================================================
# Edge Validation Tests
# =========================================================================


class TestEdgeValidation:
    """GraphValidator.validate_edges — Edge-level checks.

    Notes on test design:
        The EdgeStore itself validates source/target existence at create()
        time. To test the validator's edge checks independently, we pass
        Edge objects directly via validate_edges(edges=[...]) without
        persisting them in the store.
    """

    def test_valid_edge_passes(self, validator, node_store, person_node, doc_node):
        """A well-formed Edge between valid nodes passes validation."""
        n1 = node_store.create(person_node)
        n2 = node_store.create(doc_node)
        edge = Edge(source_id=n1.node_id, target_id=n2.node_id, edge_type="owns")
        result = validator.validate_edge(edge)
        assert result.is_valid
        assert result.error_count == 0

    def test_source_missing_fails(self, validator, node_store, person_node):
        """E-EDGE-002: Edge with non-existent source fails."""
        n = node_store.create(person_node)
        # Construct edge directly — don't go through store which blocks missing targets
        edge = Edge(source_id="n_nonexistent", target_id=n.node_id, edge_type="knows")
        result = validator.validate_edge(edge)
        assert not result.is_valid
        codes = [e.code for e in result.errors]
        assert E_EDGE_SOURCE_MISSING in codes

    def test_target_missing_fails(self, validator, node_store, person_node):
        """E-EDGE-003: Edge with non-existent target fails."""
        n1 = node_store.create(person_node)
        edge = Edge(source_id=n1.node_id, target_id="n_nonexistent", edge_type="knows")
        result = validator.validate_edge(edge)
        assert not result.is_valid
        codes = [e.code for e in result.errors]
        assert E_EDGE_TARGET_MISSING in codes

    def test_duplicate_triple_detected(self, validator, node_store, person_node, doc_node):
        """E-EDGE-001: Duplicate (source, target, type) triple detected."""
        n1 = node_store.create(person_node)
        n2 = node_store.create(doc_node)
        edge1 = Edge(source_id=n1.node_id, target_id=n2.node_id, edge_type="references")
        edge2 = Edge(source_id=n1.node_id, target_id=n2.node_id, edge_type="references")
        # Pass edges directly to validator — store rejects duplicates at create()
        result = validator.validate_edges(edges=[edge1, edge2])
        codes = [e.code for e in result.errors]
        assert E_EDGE_TRIPLE_DUPLICATE in codes

    def test_unknown_edge_type_fails(self, validator, node_store, person_node, doc_node):
        """E-EDGE-004: Edge with unknown type fails."""
        n1 = node_store.create(person_node)
        n2 = node_store.create(doc_node)
        edge = Edge(source_id=n1.node_id, target_id=n2.node_id, edge_type="teleports_to")
        result = validator.validate_edge(edge)
        assert not result.is_valid
        codes = [e.code for e in result.errors]
        assert E_EDGE_TYPE_UNKNOWN in codes

    def test_confidence_too_high_fails(self, validator, node_store, person_node, doc_node):
        """E-EDGE-005: Edge confidence > 1.0 fails."""
        n1 = node_store.create(person_node)
        n2 = node_store.create(doc_node)
        edge = Edge(source_id=n1.node_id, target_id=n2.node_id,
                    edge_type="references", confidence=2.0)
        result = validator.validate_edge(edge)
        assert not result.is_valid
        codes = [e.code for e in result.errors]
        assert E_EDGE_CONFIDENCE_RANGE in codes

    def test_confidence_negative_fails(self, validator, node_store, person_node, doc_node):
        """E-EDGE-009: Edge with negative confidence fails."""
        n1 = node_store.create(person_node)
        n2 = node_store.create(doc_node)
        edge = Edge(source_id=n1.node_id, target_id=n2.node_id,
                    edge_type="references", confidence=-0.1)
        result = validator.validate_edge(edge)
        assert not result.is_valid
        codes = [e.code for e in result.errors]
        assert E_EDGE_CONFIDENCE_NEGATIVE in codes

    def test_invalid_direction_fails(self, validator, node_store, person_node, doc_node):
        """E-EDGE-006: Invalid direction fails."""
        n1 = node_store.create(person_node)
        n2 = node_store.create(doc_node)
        edge = Edge(source_id=n1.node_id, target_id=n2.node_id,
                    edge_type="references", direction="sideways")
        result = validator.validate_edge(edge)
        assert not result.is_valid
        codes = [e.code for e in result.errors]
        assert E_EDGE_DIRECTION_INVALID in codes

    def test_invalid_status_fails(self, validator, node_store, person_node, doc_node):
        """E-EDGE-007: Invalid status fails."""
        n1 = node_store.create(person_node)
        n2 = node_store.create(doc_node)
        edge = Edge(source_id=n1.node_id, target_id=n2.node_id,
                    edge_type="references", status="floating")
        result = validator.validate_edge(edge)
        assert not result.is_valid
        codes = [e.code for e in result.errors]
        assert E_EDGE_STATUS_INVALID in codes

    def test_edge_type_incompatible_fails(self, validator, node_store, person_node, doc_node):
        """E-EDGE-008: Edge type incompatible with node families fails."""
        n1 = node_store.create(person_node)
        n2 = node_store.create(doc_node)
        # "supersedes" is HIERARCHICAL — not in compatibility matrix for Person→Document
        edge = Edge(source_id=n1.node_id, target_id=n2.node_id, edge_type="supersedes")
        result = validator.validate_edge(edge)
        assert not result.is_valid
        codes = [e.code for e in result.errors]
        assert E_EDGE_TYPE_INCOMPATIBLE in codes


# =========================================================================
# Invariant Validation Tests
# =========================================================================


class TestInvariantValidation:
    """GraphValidator.validate_invariants — Graph-wide invariant checks."""

    def test_orphan_edge_source_detected(self, validator, node_store):
        """E-INV-002: Edge referencing non-existent source is detected."""
        n = node_store.create(Node(node_type="Person", owner_id="u1"))
        edge = Edge(source_id="n_nonexistent", target_id=n.node_id, edge_type="knows")
        result = validator.validate_invariants(
            nodes=[n],
            edges=[edge],
        )
        assert not result.is_valid
        codes = [e.code for e in result.errors]
        assert "E-INV-002" in codes

    def test_orphan_edge_target_detected(self, validator, node_store):
        """E-INV-003: Edge referencing non-existent target is detected."""
        n = node_store.create(Node(node_type="Person", owner_id="u1"))
        edge = Edge(source_id=n.node_id, target_id="n_nonexistent", edge_type="knows")
        result = validator.validate_invariants(
            nodes=[n],
            edges=[edge],
        )
        assert not result.is_valid
        codes = [e.code for e in result.errors]
        assert "E-INV-003" in codes

    def test_duplicate_node_ids_detected(self, validator):
        """E-INV-004: Duplicate node IDs are detected."""
        node_a = Node(node_id="n_dup", node_type="Person")
        node_b = Node(node_id="n_dup", node_type="Document")
        result = validator.validate_invariants(
            nodes=[node_a, node_b],
            edges=[],
        )
        assert not result.is_valid
        codes = [e.code for e in result.errors]
        assert E_INV_NODE_ID_DUPLICATE in codes

    def test_no_orphans_on_clean_graph(self, validator, node_store, person_node, org_node):
        """No orphan errors for a valid graph."""
        n1 = node_store.create(person_node)
        n2 = node_store.create(org_node)
        edge = Edge(source_id=n1.node_id, target_id=n2.node_id, edge_type="works_at")
        result = validator.validate_invariants(
            nodes=[n1, n2],
            edges=[edge],
        )
        assert result.is_valid


# =========================================================================
# Warning Tests
# =========================================================================


class TestWarnings:
    """GraphValidator warnings for missing optional fields."""

    def test_node_no_labels_warning(self, validator):
        """W-NODE-001: Node with no labels produces a warning."""
        node = Node(node_type="Person", owner_id="u1")
        result = validator.validate_node(node)
        codes = [w.code for w in result.warnings]
        assert W_NODE_NO_LABELS in codes

    def test_node_no_owner_warning(self, validator):
        """W-NODE-002: Node with no owner produces a warning."""
        node = Node(node_type="Person")
        result = validator.validate_node(node)
        codes = [w.code for w in result.warnings]
        assert W_NODE_NO_OWNER in codes

    def test_node_no_evidence_warning(self, validator):
        """W-NODE-003: Node with no evidence produces a warning."""
        node = Node(node_type="Person", owner_id="u1")
        result = validator.validate_node(node)
        codes = [w.code for w in result.warnings]
        assert W_NODE_NO_EVIDENCE in codes

    def test_node_with_labels_no_warning(self, validator):
        """Node with labels does not emit labels warning."""
        node = Node(node_type="Person", owner_id="u1", labels={"verified"})
        result = validator.validate_node(node)
        codes = [w.code for w in result.warnings]
        assert W_NODE_NO_LABELS not in codes

    def test_node_with_owner_no_warning(self, validator):
        """Node with owner does not emit owner warning."""
        node = Node(node_type="Person", owner_id="user_42")
        result = validator.validate_node(node)
        codes = [w.code for w in result.warnings]
        assert W_NODE_NO_OWNER not in codes

    def test_node_with_evidence_no_warning(self, validator):
        """Node with evidence does not emit evidence warning."""
        ref = EvidenceRef(object_id="ev_1", object_type="Observation",
                          field="content", confidence=0.9)
        node = Node(node_type="Person", owner_id="u1", evidence=[ref])
        result = validator.validate_node(node)
        codes = [w.code for w in result.warnings]
        assert W_NODE_NO_EVIDENCE not in codes

    def test_edge_no_evidence_warning(self, validator, node_store, person_node, doc_node):
        """W-EDGE-001: Edge with no evidence produces a warning."""
        n1 = node_store.create(person_node)
        n2 = node_store.create(doc_node)
        edge = Edge(source_id=n1.node_id, target_id=n2.node_id, edge_type="references")
        result = validator.validate_edge(edge)
        codes = [w.code for w in result.warnings]
        assert W_EDGE_NO_EVIDENCE in codes

    def test_edge_low_confidence_warning(self, validator, node_store, person_node, doc_node):
        """W-EDGE-002: Edge with low confidence produces a warning."""
        n1 = node_store.create(person_node)
        n2 = node_store.create(doc_node)
        edge = Edge(source_id=n1.node_id, target_id=n2.node_id,
                    edge_type="references", confidence=0.2)
        result = validator.validate_edge(edge)
        codes = [w.code for w in result.warnings]
        assert W_EDGE_LOW_CONFIDENCE in codes

    def test_edge_zero_weight_warning(self, validator, node_store, person_node, doc_node):
        """W-EDGE-003: Edge with zero weight produces a warning."""
        n1 = node_store.create(person_node)
        n2 = node_store.create(doc_node)
        edge = Edge(source_id=n1.node_id, target_id=n2.node_id,
                    edge_type="references", weight=0.0)
        result = validator.validate_edge(edge)
        codes = [w.code for w in result.warnings]
        assert W_EDGE_ZERO_WEIGHT in codes


# =========================================================================
# Composite Validation Tests
# =========================================================================


class TestValidateAll:
    """GraphValidator.validate_all — composite validation."""

    def test_clean_graph_passes(self, validator, node_store, person_node, org_node):
        """A clean graph with valid nodes and edges passes all checks."""
        n1 = node_store.create(person_node)
        n2 = node_store.create(org_node)
        edge_store = get_edge_store()
        edge_store.create(
            Edge(source_id=n1.node_id, target_id=n2.node_id,
                 edge_type="works_at", evidence=[
                     EvidenceRef(object_id="ev_1", object_type="Observation",
                                 field="employment", confidence=1.0)
                 ])
        )
        result = validator.validate_all()
        assert result.is_valid
        assert result.node_count == 2
        assert result.edge_count == 1

    def test_corrupt_graph_detected(self, validator, node_store):
        """A graph with multiple issues catches all.

        Does not use edge_store.create() for invalid edges since the store
        validates source/target existence at creation time.
        """
        n1 = node_store.create(Node(node_type="Person", owner_id="u1"))
        # Store the valid node, then validate an edge set that includes an orphan
        bad_edge = Edge(source_id=n1.node_id, target_id="n_missing",
                        edge_type="knows", confidence=-0.5)
        # validate_all reads from stores for nodes, but for edges it also reads from store
        # Since the bad edge can't be in the store, use validate_edges directly
        node_result = validator.validate_nodes()
        edge_result = validator.validate_edges(edges=[bad_edge])

        assert node_result.is_valid
        assert not edge_result.is_valid
        assert edge_result.error_count >= 1

    def test_is_deterministic(self, validator, node_store):
        """Same graph always produces the same validation result."""
        n1 = node_store.create(Node(node_type="Person", owner_id="u1"))
        bad_edge = Edge(source_id=n1.node_id, target_id="n_missing",
                        edge_type="knows")

        # Run twice with identical inputs
        result1 = validator.validate_edges(edges=[bad_edge])
        result2 = validator.validate_edges(edges=[bad_edge])

        assert result1.is_valid == result2.is_valid
        assert result1.error_count == result2.error_count

    def test_validate_all_no_mutation(self, validator, node_store):
        """validate_all does not mutate the graph (side-effect free)."""
        original_count = node_store.count()
        _ = validator.validate_all()
        assert node_store.count() == original_count


# =========================================================================
# Convenience Wrapper Tests
# =========================================================================


class TestConvenienceWrappers:
    """GraphValidator convenience methods."""

    def test_validate_node_by_id_found(self, validator, node_store, person_node):
        """validate_node_by_id finds and validates the node."""
        n1 = node_store.create(person_node)
        result = validator.validate_node_by_id(n1.node_id)
        assert result.is_valid
        assert result.node_count == 1

    def test_validate_node_by_id_not_found(self, validator):
        """validate_node_by_id returns invalid result for missing node."""
        result = validator.validate_node_by_id("n_nonexistent")
        assert not result.is_valid

    def test_constructor_defaults(self):
        """GraphValidator with no args uses global stores."""
        v = GraphValidator()
        assert v is not None