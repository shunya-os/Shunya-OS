"""Tests for SHUNYA Knowledge Graph — Node and Edge Families (E-003-MOD-002).

Architecture references:
    UNIVERSAL_KNOWLEDGE_GRAPH_ARCHITECTURE.md §2.1 — Canonical node families
    UNIVERSAL_KNOWLEDGE_GRAPH_ARCHITECTURE.md §3.1 — Canonical edge families
    UNIVERSAL_KNOWLEDGE_GRAPH_ARCHITECTURE.md §3.4.5 — Edge type compatibility
"""

import pytest
from app.graph.families import (
    Families, NodeFamily, EdgeFamily,
    ALL_NODE_FAMILIES, ALL_EDGE_FAMILIES, ALL_EDGE_TYPES,
)
from app.kernel.types import get_registry, reset_registry


# =========================================================================
# Node Family Tests
# =========================================================================

class TestNodeFamilies:
    """UNIVERSAL_KNOWLEDGE_GRAPH_ARCHITECTURE.md §2.1."""

    def setup_method(self):
        reset_registry()
        # Ensure TypeRegistry is initialized with defaults
        get_registry()

    def test_18_node_families(self):
        """§2.1 — There are 18 canonical node families."""
        families = Families.get_node_families()
        assert len(families) == 18
        assert NodeFamily.PERSON in families
        assert NodeFamily.DOCUMENT in families
        assert NodeFamily.EVENT in families

    def test_resolve_person_family(self):
        """Person type resolves to PERSON family."""
        family = Families.get_node_family("Person")
        assert family == NodeFamily.PERSON

    def test_resolve_document_family(self):
        """Document type resolves to DOCUMENT family."""
        family = Families.get_node_family("Document")
        assert family == NodeFamily.DOCUMENT

    def test_resolve_organization_subtype(self):
        """Organization subtypes resolve to ORGANIZATION family."""
        family = Families.get_node_family("Company")
        assert family == NodeFamily.ORGANIZATION
        family = Families.get_node_family("Team")
        assert family == NodeFamily.ORGANIZATION

    def test_resolve_entity_abstract(self):
        """Abstract type 'Entity' does not have a direct family mapping."""
        # Entity is the parent of Person, Organization, etc.
        # It is not directly listed in family roots
        family = Families.get_node_family("Entity")
        # Entity's parent is Object, which maps to nothing
        # So this should fall through
        assert family is None

    def test_resolve_object_root(self):
        """Root type 'Object' has no family."""
        family = Families.get_node_family("Object")
        assert family is None

    def test_resolve_unknown_type(self):
        """Unknown type returns None."""
        family = Families.get_node_family("NonExistentType")
        assert family is None

    def test_resolve_task_family(self):
        """Task type resolves to TASK family."""
        family = Families.get_node_family("Task")
        assert family == NodeFamily.TASK

    def test_resolve_event_family(self):
        """Event type resolves to EVENT family."""
        family = Families.get_node_family("Event")
        assert family == NodeFamily.EVENT

    def test_resolve_commitment_family(self):
        """Commitment resolves to COMMITMENT family."""
        family = Families.get_node_family("Commitment")
        assert family == NodeFamily.COMMITMENT

    def test_get_node_family_root(self):
        """Family root type is correct."""
        assert Families.get_node_family_root(NodeFamily.PERSON) == "Person"
        assert Families.get_node_family_root(NodeFamily.DOCUMENT) == "Document"
        assert Families.get_node_family_root(NodeFamily.EVENT) == "Event"

    def test_all_node_families_list(self):
        """ALL_NODE_FAMILIES contains all 18 families."""
        assert len(ALL_NODE_FAMILIES) == 18


# =========================================================================
# Edge Family Tests
# =========================================================================

class TestEdgeFamilies:
    """UNIVERSAL_KNOWLEDGE_GRAPH_ARCHITECTURE.md §3.1."""

    def test_15_edge_families(self):
        """§3.1 — There are 15 canonical edge families."""
        families = Families.get_edge_families()
        assert len(families) == 15

    def test_ownership_family_types(self):
        """ownership family has owns, created_by, assigned_to."""
        types = Families.get_edge_types(EdgeFamily.OWNERSHIP)
        assert "owns" in types
        assert "created_by" in types
        assert "assigned_to" in types

    def test_social_family_types(self):
        """social family has knows, collaborates_with, relates_to."""
        types = Families.get_edge_types(EdgeFamily.SOCIAL)
        assert "knows" in types
        assert "collaborates_with" in types
        assert "relates_to" in types

    def test_membership_family_types(self):
        """membership family has belongs_to, member_of, works_at."""
        types = Families.get_edge_types(EdgeFamily.MEMBERSHIP)
        assert "belongs_to" in types
        assert "member_of" in types
        assert "works_at" in types

    def test_resolve_edge_family(self):
        """Concrete edge type resolves to its family."""
        assert Families.get_edge_family("knows") == EdgeFamily.SOCIAL
        assert Families.get_edge_family("owns") == EdgeFamily.OWNERSHIP
        assert Families.get_edge_family("references") == EdgeFamily.REFERENCE
        assert Families.get_edge_family("contains") == EdgeFamily.HIERARCHICAL

    def test_resolve_unknown_edge_type(self):
        """Unknown edge type returns None."""
        assert Families.get_edge_family("unknown_relation") is None

    def test_is_valid_edge_type(self):
        """Known edge types are valid."""
        assert Families.is_valid_edge_type("knows")
        assert Families.is_valid_edge_type("owns")
        assert Families.is_valid_edge_type("references")
        assert not Families.is_valid_edge_type("magic_connection")

    def test_get_all_edge_types(self):
        """All edge types are returned."""
        all_types = Families.get_all_edge_types()
        assert len(all_types) > 30
        assert "knows" in all_types
        assert "owns" in all_types

    def test_all_edge_families_and_types(self):
        """Convenience exports are correct."""
        assert len(ALL_EDGE_FAMILIES) == 15
        assert len(ALL_EDGE_TYPES) > 30


# =========================================================================
# Edge Compatibility Tests
# =========================================================================

class TestEdgeCompatibility:
    """UNIVERSAL_KNOWLEDGE_GRAPH_ARCHITECTURE.md §3.4.5."""

    def setup_method(self):
        reset_registry()
        get_registry()

    def test_person_knows_person_is_valid(self):
        """knows edge between Person→Person is valid (social family)."""
        is_valid, reason = Families.validate_edge_compatibility(
            "Person", "Person", "knows"
        )
        assert is_valid, reason

    def test_person_knows_document_is_not_valid(self):
        """knows edge between Person→Document is not valid (social is Person→Person only)."""
        is_valid, reason = Families.validate_edge_compatibility(
            "Person", "Document", "knows"
        )
        assert not is_valid
        assert "not compatible" in reason

    def test_person_owns_document_is_valid(self):
        """owns edge between Person→Document is valid."""
        is_valid, reason = Families.validate_edge_compatibility(
            "Person", "Document", "owns"
        )
        assert is_valid, reason

    def test_person_works_at_organization_is_valid(self):
        """works_at edge between Person→Organization is valid (membership)."""
        is_valid, reason = Families.validate_edge_compatibility(
            "Person", "Organization", "works_at"
        )
        assert is_valid, reason

    def test_person_works_at_document_is_not_valid(self):
        """works_at edge between Person→Document is not valid."""
        is_valid, reason = Families.validate_edge_compatibility(
            "Person", "Document", "works_at"
        )
        assert not is_valid

    def test_document_references_document_is_valid(self):
        """references edge between Document→Document is valid (reference is universal)."""
        is_valid, reason = Families.validate_edge_compatibility(
            "Document", "Document", "references"
        )
        assert is_valid, reason

    def test_document_contains_document_is_valid(self):
        """contains edge between Document→Document is valid (hierarchical)."""
        is_valid, reason = Families.validate_edge_compatibility(
            "Document", "Document", "contains"
        )
        assert is_valid, reason

    def test_event_precedes_event_is_valid(self):
        """precedes edge between Event→Event is valid (temporal is universal)."""
        is_valid, reason = Families.validate_edge_compatibility(
            "Event", "Event", "precedes"
        )
        assert is_valid, reason

    def test_person_company_membership(self):
        """Member_of: Person→Company is valid (Company is Organization)."""
        is_valid, reason = Families.validate_edge_compatibility(
            "Person", "Company", "member_of"
        )
        assert is_valid, reason

    def test_unknown_edge_type(self):
        """Unknown edge type returns invalid."""
        is_valid, reason = Families.validate_edge_compatibility(
            "Person", "Person", "unknown_type"
        )
        assert not is_valid
        assert "Unknown edge type" in reason

    def test_unknown_node_type(self):
        """Unknown node type returns invalid."""
        is_valid, reason = Families.validate_edge_compatibility(
            "Alien", "Person", "knows"
        )
        assert not is_valid
        assert "Unknown source node type" in reason

    def test_get_valid_edge_types(self):
        """get_valid_edge_types returns all compatible types."""
        valid = Families.get_valid_edge_types("Person", "Person")
        assert "knows" in valid
        assert "relates_to" in valid
        assert "owns" in valid
        assert "references" in valid
        # should NOT include membership or hierarchical
        assert "works_at" not in valid
        assert "belongs_to" not in valid
        assert "contains" not in valid

    def test_get_valid_edge_types_person_document(self):
        """get_valid_edge_types for Person→Document."""
        valid = Families.get_valid_edge_types("Person", "Document")
        assert "owns" in valid
        assert "created_by" in valid
        assert "references" in valid
        assert "knows" not in valid
        assert "works_at" not in valid

    def test_constitutional_inheritance(self):
        """inherits_from is a known edge type in the inheritance family."""
        family = Families.get_edge_family("inherits_from")
        assert family == EdgeFamily.INHERITANCE
        assert Families.is_valid_edge_type("inherits_from")

    def test_person_container_document(self):
        """contains: Person→Document is not valid (hierarchical restricted)."""
        is_valid, reason = Families.validate_edge_compatibility(
            "Person", "Document", "contains"
        )
        # contains is hierarchical. Person is not in hierarchical matrix pairs.
        # But hierarchical is not in _UNIVERSAL_FAMILIES either.
        # Person→Document has _EDGE_COMPATIBILITY entries, and contains is NOT in those.
        # So it should fail.
        assert not is_valid, f"Expected invalid but got: {reason}"
        assert "not compatible" in reason


# =========================================================================
# Integration Tests
# =========================================================================

class TestFamiliesIntegration:
    """Families integrate with TypeRegistry for type resolution."""

    def setup_method(self):
        reset_registry()
        get_registry()

    def test_person_subtype_resolution(self):
        """Company is a subtype of Organization, resolves to ORGANIZATION family."""
        family = Families.get_node_family("Company")
        assert family == NodeFamily.ORGANIZATION

    def test_subtype_edge_compatibility(self):
        """Company inherits Person→Organization compatibility rules."""
        # Person→Company: works_at should be valid (Company is Organization subtype)
        is_valid, reason = Families.validate_edge_compatibility(
            "Person", "Company", "works_at"
        )
        assert is_valid, reason

    def test_commitment_to_person(self):
        """Person→Commitment compatibility."""
        is_valid, reason = Families.validate_edge_compatibility(
            "Person", "Commitment", "owns"
        )
        assert is_valid, reason

    def test_all_types_are_accounted_for(self):
        """Every edge type in the families module has a valid family."""
        for edge_type in ALL_EDGE_TYPES:
            family = Families.get_edge_family(edge_type)
            assert family is not None, f"Edge type '{edge_type}' has no family"