"""Tests for GKF enums — GKF-001A enriched."""

import pytest
from app.gkf.enums import (
    GKFNodeType, GKFEdgeType, AmendmentType, ElementStatus,
    SemanticCategory, AuthorityType,
)


class TestGKFNodeType:
    def test_count(self):
        assert len(GKFNodeType) == 16

    def test_governing_principle(self):
        assert GKFNodeType.GOVERNING_PRINCIPLE.value == "gkf_governing_principle"

    def test_enrichment_types_exist(self):
        assert GKFNodeType.AUTHORITY.value == "gkf_authority"
        assert GKFNodeType.CITATION.value == "gkf_citation"
        assert GKFNodeType.COMMENTARY.value == "gkf_commentary"
        assert GKFNodeType.EXAMPLE.value == "gkf_example"
        assert GKFNodeType.IMPLEMENTATION_GUIDANCE.value == "gkf_implementation_guidance"

    def test_legacy_principle_gone(self):
        assert not hasattr(GKFNodeType, "PRINCIPLE")


class TestGKFEdgeType:
    def test_count(self):
        assert len(GKFEdgeType) == 11

    def test_enrichment_edges_exist(self):
        assert GKFEdgeType.ATTRIBUTED_TO.value == "gkf_attributed_to"
        assert GKFEdgeType.ILLUSTRATES.value == "gkf_illustrates"
        assert GKFEdgeType.GUIDES.value == "gkf_guides"

    def test_all_have_gkf_prefix(self):
        for t in GKFEdgeType:
            assert t.value.startswith("gkf_")


class TestAmendmentType:
    def test_count(self):
        assert len(AmendmentType) == 4

    def test_values(self):
        assert AmendmentType.ADDITION.value == "addition"
        assert AmendmentType.MODIFICATION.value == "modification"
        assert AmendmentType.SUPERSESSION.value == "supersession"
        assert AmendmentType.REPEAL.value == "repeal"


class TestElementStatus:
    def test_count(self):
        assert len(ElementStatus) == 3

    def test_values(self):
        assert ElementStatus.ACTIVE.value == "active"
        assert ElementStatus.SUPERSEDED.value == "superseded"
        assert ElementStatus.DRAFT.value == "draft"


class TestSemanticCategory:
    def test_count(self):
        assert len(SemanticCategory) == 12

    def test_all_categories(self):
        assert SemanticCategory.ARCHITECTURE.value == "architecture"
        assert SemanticCategory.ENGINEERING.value == "engineering"
        assert SemanticCategory.GOVERNANCE.value == "governance"
        assert SemanticCategory.ETHICS.value == "ethics"
        assert SemanticCategory.SECURITY.value == "security"
        assert SemanticCategory.DATA.value == "data"
        assert SemanticCategory.AI.value == "ai"
        assert SemanticCategory.UX.value == "ux"
        assert SemanticCategory.OPERATIONS.value == "operations"
        assert SemanticCategory.PERFORMANCE.value == "performance"
        assert SemanticCategory.LEGAL.value == "legal"
        assert SemanticCategory.BUSINESS.value == "business"


class TestAuthorityType:
    def test_all_types(self):
        assert AuthorityType.FOUNDER.value == "founder"
        assert AuthorityType.ORGANIZATION.value == "organization"
        assert AuthorityType.STANDARDS_BODY.value == "standards_body"
        assert AuthorityType.GOVERNMENT.value == "government"
        assert AuthorityType.COURT.value == "court"
        assert AuthorityType.REGULATORY.value == "regulatory"