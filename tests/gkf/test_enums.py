"""Tests for GKF enums."""

import pytest
from app.gkf.enums import GKFNodeType, GKFEdgeType, AmendmentType, ElementStatus


class TestGKFNodeType:
    def test_count(self):
        assert len(GKFNodeType) == 11

    def test_values(self):
        assert GKFNodeType.COLLECTION.value == "gkf_collection"
        assert GKFNodeType.VOLUME.value == "gkf_volume"
        assert GKFNodeType.CHAPTER.value == "gkf_chapter"
        assert GKFNodeType.ARTICLE.value == "gkf_article"
        assert GKFNodeType.PRINCIPLE.value == "gkf_principle"
        assert GKFNodeType.INTERPRETATION.value == "gkf_interpretation"
        assert GKFNodeType.REFERENCE.value == "gkf_reference"
        assert GKFNodeType.EVIDENCE.value == "gkf_evidence"
        assert GKFNodeType.IMPLEMENTATION_LINK.value == "gkf_implementation_link"
        assert GKFNodeType.AMENDMENT.value == "gkf_amendment"
        assert GKFNodeType.VERSION.value == "gkf_version"

    def test_all_types_have_gkf_prefix(self):
        for t in GKFNodeType:
            assert t.value.startswith("gkf_")


class TestGKFEdgeType:
    def test_count(self):
        assert len(GKFEdgeType) == 8

    def test_values(self):
        assert GKFEdgeType.CONTAINS.value == "gkf_contains"
        assert GKFEdgeType.CLARIFIES.value == "gkf_clarifies"
        assert GKFEdgeType.CROSS_REFERENCES.value == "gkf_cross_references"
        assert GKFEdgeType.ESTABLISHED_BY.value == "gkf_established_by"
        assert GKFEdgeType.IS_IMPLEMENTED_BY.value == "gkf_is_implemented_by"
        assert GKFEdgeType.AMENDED_BY.value == "gkf_amended_by"
        assert GKFEdgeType.HAS_VERSION.value == "gkf_has_version"
        assert GKFEdgeType.EXPRESSED_IN.value == "gkf_expressed_in"

    def test_all_edges_have_gkf_prefix(self):
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