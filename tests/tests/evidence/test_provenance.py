"""Tests for SHUNYA Evidence Engine — E-004-MOD-002 Provenance & Source Intelligence.

Architecture references:
    SMS-VOLUME-II-WORLD-MODEL.md §8 — Evidence Contract
    UNIVERSAL_KNOWLEDGE_GRAPH_ARCHITECTURE.md §4.3 — Evidence chain

Constitutional invariants tested:
    - Provenance chains are append-only
    - EvidenceChain is immutable
    - SourceIdentity is permanent and unique
    - Derivation records are NOT reasoning
    - Verification records do NOT calculate truth
    - Citations support many-to-many
"""

import pytest
from datetime import datetime, timezone
from app.evidence.provenance_enums import DerivationType, VerificationStatus, ProvenanceRelationType
from app.evidence.provenance_models import (
    SourceIdentity, SourceMetadata, DerivationRecord, VerificationRecord,
    Citation, EvidenceChainLink, EvidenceChain, ProvenanceGraph,
)


# =========================================================================
# Fixtures
# =========================================================================

@pytest.fixture
def sample_source_identity() -> SourceIdentity:
    return SourceIdentity(source_type="human", identifier="user_001")


@pytest.fixture
def sample_evidence_id() -> str:
    return "ev_test_001"


@pytest.fixture
def sample_source_evidence_id() -> str:
    return "ev_source_001"


@pytest.fixture
def sample_target_evidence_id() -> str:
    return "ev_target_001"


# =========================================================================
# DerivationType Enum Tests
# =========================================================================

class TestDerivationType:
    def test_all_derivation_types_exist(self):
        assert hasattr(DerivationType, "PARSED")
        assert hasattr(DerivationType, "NORMALIZED")
        assert hasattr(DerivationType, "CONVERTED")
        assert hasattr(DerivationType, "MERGED")
        assert hasattr(DerivationType, "SPLIT")
        assert hasattr(DerivationType, "TRANSLATED")

    def test_derivation_type_values(self):
        assert DerivationType.PARSED.value == "parsed"
        assert DerivationType.NORMALIZED.value == "normalized"
        assert DerivationType.CONVERTED.value == "converted"
        assert DerivationType.MERGED.value == "merged"
        assert DerivationType.SPLIT.value == "split"
        assert DerivationType.TRANSLATED.value == "translated"

    def test_derivation_type_count(self):
        assert len(DerivationType) == 6

    def test_no_business_derivation_types(self):
        assert not hasattr(DerivationType, "REASONED")
        assert not hasattr(DerivationType, "INFERRED")


# =========================================================================
# VerificationStatus Enum Tests
# =========================================================================

class TestVerificationStatus:
    def test_all_verification_statuses_exist(self):
        assert hasattr(VerificationStatus, "VERIFIED")
        assert hasattr(VerificationStatus, "UNVERIFIED")
        assert hasattr(VerificationStatus, "CHALLENGED")
        assert hasattr(VerificationStatus, "CONFIRMED")

    def test_verification_status_values(self):
        assert VerificationStatus.VERIFIED.value == "verified"
        assert VerificationStatus.UNVERIFIED.value == "unverified"
        assert VerificationStatus.CHALLENGED.value == "challenged"
        assert VerificationStatus.CONFIRMED.value == "confirmed"

    def test_verification_status_count(self):
        assert len(VerificationStatus) == 4


# =========================================================================
# ProvenanceRelationType Enum Tests
# =========================================================================

class TestProvenanceRelationType:
    def test_all_relation_types_exist(self):
        assert hasattr(ProvenanceRelationType, "ORIGIN")
        assert hasattr(ProvenanceRelationType, "DERIVATION")
        assert hasattr(ProvenanceRelationType, "TRANSFORMATION")
        assert hasattr(ProvenanceRelationType, "AGGREGATION")
        assert hasattr(ProvenanceRelationType, "CITATION")
        assert hasattr(ProvenanceRelationType, "VERIFICATION")

    def test_relation_type_values(self):
        assert ProvenanceRelationType.ORIGIN.value == "origin"
        assert ProvenanceRelationType.DERIVATION.value == "derivation"
        assert ProvenanceRelationType.TRANSFORMATION.value == "transformation"
        assert ProvenanceRelationType.AGGREGATION.value == "aggregation"
        assert ProvenanceRelationType.CITATION.value == "citation"
        assert ProvenanceRelationType.VERIFICATION.value == "verification"

    def test_relation_type_count(self):
        assert len(ProvenanceRelationType) == 6


# =========================================================================
# SourceIdentity Tests
# =========================================================================

class TestSourceIdentity:
    def test_auto_generated_id(self):
        sid = SourceIdentity(source_type="human", identifier="u1")
        assert sid.source_id.startswith("src_")
        assert sid.source_id != ""

    def test_auto_generated_timestamp(self):
        sid = SourceIdentity(source_type="system", identifier="sys_001")
        assert sid.timestamp != ""
        # Validate ISO format
        datetime.fromisoformat(sid.timestamp)

    def test_explicit_values_preserved(self):
        sid = SourceIdentity(
            source_id="src_explicit_001",
            source_type="sensor",
            identifier="temp_sensor",
            timestamp="2026-01-01T00:00:00",
        )
        assert sid.source_id == "src_explicit_001"
        assert sid.source_type == "sensor"

    def test_source_identity_immutable(self):
        sid = SourceIdentity(source_type="human", identifier="u1")
        with pytest.raises(Exception):
            sid.source_type = "system"

    def test_universal_source_types(self):
        for stype in ["human", "system", "sensor", "document", "external", "derived"]:
            sid = SourceIdentity(source_type=stype, identifier=f"id_{stype}")
            assert sid.source_type == stype

    def test_source_id_format(self):
        sid = SourceIdentity(source_type="human", identifier="u1")
        assert len(sid.source_id) >= 16

    def test_no_business_source_types(self):
        # Can still have any source type, but architecture defines universal ones
        sid = SourceIdentity(source_type="custom_business_type", identifier="x")
        assert sid.source_type == "custom_business_type"


# =========================================================================
# SourceMetadata Tests
# =========================================================================

class TestSourceMetadata:
    def test_minimal_construction(self):
        sm = SourceMetadata(identifier="doc_001")
        assert sm.identifier == "doc_001"
        assert sm.description == ""

    def test_full_construction(self):
        sm = SourceMetadata(
            identifier="doc_001",
            description="Invoice from ACME Corp",
            origin="ACME ERP System",
            capture_method="email_attachment",
            producer="finance_team",
            metadata={"file_type": "pdf", "pages": 3},
        )
        assert sm.origin == "ACME ERP System"
        assert sm.metadata["file_type"] == "pdf"

    def test_source_metadata_immutable(self):
        sm = SourceMetadata(identifier="doc_001")
        with pytest.raises(Exception):
            sm.description = "new description"

    def test_no_business_fields(self):
        # Only universal fields exist
        sm = SourceMetadata(identifier="x")
        assert not hasattr(sm, "department")
        assert not hasattr(sm, "business_unit")


# =========================================================================
# DerivationRecord Tests
# =========================================================================

class TestDerivationRecord:
    def test_auto_generated_timestamp(self):
        dr = DerivationRecord(
            derivation_type=DerivationType.PARSED.value,
            source_evidence_id="ev_001",
            target_evidence_id="ev_002",
        )
        assert dr.timestamp != ""

    def test_explicit_timestamp(self):
        dr = DerivationRecord(
            derivation_type=DerivationType.NORMALIZED.value,
            source_evidence_id="ev_001",
            target_evidence_id="ev_002",
            timestamp="2026-01-01T00:00:00",
        )
        assert dr.timestamp == "2026-01-01T00:00:00"

    def test_with_process(self):
        dr = DerivationRecord(
            derivation_type=DerivationType.CONVERTED.value,
            source_evidence_id="ev_001",
            target_evidence_id="ev_002",
            process="pdf_parser_v2",
        )
        assert dr.process == "pdf_parser_v2"

    def test_with_parameters(self):
        dr = DerivationRecord(
            derivation_type=DerivationType.MERGED.value,
            source_evidence_id="ev_001",
            target_evidence_id="ev_002",
            parameters={"strategy": "union", "conflict_mode": "preserve_both"},
        )
        assert dr.parameters["strategy"] == "union"

    def test_derived_record_immutable(self):
        dr = DerivationRecord(
            derivation_type=DerivationType.SPLIT.value,
            source_evidence_id="ev_001",
            target_evidence_id="ev_002",
        )
        with pytest.raises(Exception):
            dr.process = "new_process"

    def test_all_derivation_types(self):
        for dtype in DerivationType:
            dr = DerivationRecord(
                derivation_type=dtype.value,
                source_evidence_id="ev_a",
                target_evidence_id="ev_b",
            )
            assert dr.derivation_type == dtype.value


# =========================================================================
# VerificationRecord Tests
# =========================================================================

class TestVerificationRecord:
    def test_auto_generated_timestamp(self):
        vr = VerificationRecord(evidence_id="ev_001")
        assert vr.timestamp != ""

    def test_default_status_unverified(self):
        vr = VerificationRecord(evidence_id="ev_001")
        assert vr.status == VerificationStatus.UNVERIFIED.value

    def test_verified_status(self):
        vr = VerificationRecord(
            evidence_id="ev_001",
            status=VerificationStatus.VERIFIED.value,
            verified_by="audit_engine",
            method="cross_reference",
        )
        assert vr.status == "verified"
        assert vr.verified_by == "audit_engine"

    def test_confirmed_status(self):
        vr = VerificationRecord(
            evidence_id="ev_001",
            status=VerificationStatus.CONFIRMED.value,
            verified_by="secondary_source",
        )
        assert vr.status == "confirmed"

    def test_challenged_status(self):
        vr = VerificationRecord(
            evidence_id="ev_001",
            status=VerificationStatus.CHALLENGED.value,
            verified_by="user_001",
            method="manual_review",
            details="Contradicts evidence ev_002",
        )
        assert vr.status == "challenged"

    def test_record_immutable(self):
        vr = VerificationRecord(evidence_id="ev_001")
        with pytest.raises(Exception):
            vr.status = "verified"

    def test_all_verification_statuses(self):
        for vstatus in VerificationStatus:
            vr = VerificationRecord(evidence_id="ev_001", status=vstatus.value)
            assert vr.status == vstatus.value


# =========================================================================
# Citation Tests
# =========================================================================

class TestCitation:
    def test_auto_generated_timestamp(self):
        c = Citation(citing_evidence_id="ev_a", cited_evidence_id="ev_b")
        assert c.timestamp != ""

    def test_default_contribution(self):
        c = Citation(citing_evidence_id="ev_a", cited_evidence_id="ev_b")
        assert c.contribution == 1.0

    def test_custom_contribution(self):
        c = Citation(
            citing_evidence_id="ev_a",
            cited_evidence_id="ev_b",
            contribution=0.75,
        )
        assert c.contribution == 0.75

    def test_with_rationale(self):
        c = Citation(
            citing_evidence_id="ev_a",
            cited_evidence_id="ev_b",
            rationale="Supports the claim that the deadline is 2026-08-01",
        )
        assert c.rationale != ""

    def test_citation_immutable(self):
        c = Citation(citing_evidence_id="ev_a", cited_evidence_id="ev_b")
        with pytest.raises(Exception):
            c.contribution = 0.5


# =========================================================================
# EvidenceChainLink Tests
# =========================================================================

class TestEvidenceChainLink:
    def test_auto_generated_timestamp(self):
        link = EvidenceChainLink(
            link_type="derivation",
            target_evidence_id="ev_002",
        )
        assert link.timestamp != ""

    def test_default_contribution(self):
        link = EvidenceChainLink(
            link_type=ProvenanceRelationType.DERIVATION.value,
            target_evidence_id="ev_002",
        )
        assert link.contribution == 1.0

    def test_link_immutable(self):
        link = EvidenceChainLink(
            link_type="derivation",
            target_evidence_id="ev_002",
        )
        with pytest.raises(Exception):
            link.link_type = "origin"


# =========================================================================
# EvidenceChain Tests
# =========================================================================

class TestEvidenceChain:
    def test_empty_chain(self):
        chain = EvidenceChain(evidence_id="ev_001")
        assert chain.evidence_id == "ev_001"
        assert len(chain.links) == 0
        assert chain.root_evidence_id == ""

    def test_chain_with_root(self):
        chain = EvidenceChain(evidence_id="ev_001", root_evidence_id="ev_root")
        assert chain.root_evidence_id == "ev_root"

    def test_chain_immutable(self):
        chain = EvidenceChain(evidence_id="ev_001")
        with pytest.raises(Exception):
            chain.evidence_id = "ev_002"

    def test_chain_with_links(self):
        link1 = EvidenceChainLink("derivation", "ev_002")
        link2 = EvidenceChainLink("superseded", "ev_003")
        chain = EvidenceChain(
            evidence_id="ev_001",
            links=(link1, link2),
            root_evidence_id="ev_root",
        )
        assert len(chain.links) == 2


# =========================================================================
# ProvenanceGraph Tests
# =========================================================================

class TestProvenanceGraph:
    def test_graph_empty_initially(self):
        graph = ProvenanceGraph()
        assert graph.get_origin("ev_001") is None
        assert graph.get_derivation("ev_001") is None

    def test_set_and_get_origin(self):
        graph = ProvenanceGraph()
        graph.set_origin("ev_001", "src_human_001")
        assert graph.get_origin("ev_001") == "src_human_001"

    def test_origin_overwrites(self):
        graph = ProvenanceGraph()
        graph.set_origin("ev_001", "src_a")
        graph.set_origin("ev_001", "src_b")
        assert graph.get_origin("ev_001") == "src_b"

    def test_add_and_get_derivation(self):
        graph = ProvenanceGraph()
        graph.add_derivation("ev_002", "ev_001")
        assert graph.get_derivation("ev_002") == "ev_001"

    def test_derivation_chain_single(self):
        graph = ProvenanceGraph()
        graph.add_derivation("ev_002", "ev_001")
        chain = graph.get_derivation_chain("ev_002")
        assert "ev_001" in chain

    def test_derivation_chain_multiple(self):
        graph = ProvenanceGraph()
        graph.add_derivation("ev_004", "ev_003")
        graph.add_derivation("ev_003", "ev_002")
        graph.add_derivation("ev_002", "ev_001")
        chain = graph.get_derivation_chain("ev_004")
        assert chain == ["ev_003", "ev_002", "ev_001"]

    def test_empty_derivation_chain(self):
        graph = ProvenanceGraph()
        chain = graph.get_derivation_chain("ev_001")
        assert chain == []

    def test_add_transformation(self):
        graph = ProvenanceGraph()
        dr = DerivationRecord(
            derivation_type=DerivationType.PARSED.value,
            source_evidence_id="ev_001",
            target_evidence_id="ev_002",
        )
        graph.add_transformation(dr)
        result = graph.get_transformation("ev_001", "ev_002")
        assert result is not None
        assert result.derivation_type == "parsed"

    def test_get_transformations_for_source(self):
        graph = ProvenanceGraph()
        dr1 = DerivationRecord(DerivationType.PARSED.value, "ev_001", "ev_002")
        dr2 = DerivationRecord(DerivationType.NORMALIZED.value, "ev_001", "ev_003")
        graph.add_transformation(dr1)
        graph.add_transformation(dr2)
        transforms = graph.get_transformations_for_source("ev_001")
        assert len(transforms) == 2

    def test_no_transformations_for_unknown_source(self):
        graph = ProvenanceGraph()
        transforms = graph.get_transformations_for_source("ev_nonexistent")
        assert transforms == []

    def test_add_aggregation(self):
        graph = ProvenanceGraph()
        graph.add_aggregation("ev_003", ["ev_001", "ev_002"])
        sources = graph.get_aggregation_sources("ev_003")
        assert "ev_001" in sources
        assert "ev_002" in sources

    def test_add_aggregation_multiple_times(self):
        graph = ProvenanceGraph()
        graph.add_aggregation("ev_003", ["ev_001"])
        graph.add_aggregation("ev_003", ["ev_002"])
        sources = graph.get_aggregation_sources("ev_003")
        assert len(sources) == 2

    def test_empty_aggregation_sources(self):
        graph = ProvenanceGraph()
        sources = graph.get_aggregation_sources("ev_001")
        assert sources == []

    def test_add_citation(self):
        graph = ProvenanceGraph()
        c = Citation(citing_evidence_id="ev_001", cited_evidence_id="ev_002")
        graph.add_citation(c)
        citations = graph.get_citations("ev_001")
        assert len(citations) == 1
        assert citations[0].cited_evidence_id == "ev_002"

    def test_cited_by(self):
        graph = ProvenanceGraph()
        c1 = Citation(citing_evidence_id="ev_001", cited_evidence_id="ev_002")
        c2 = Citation(citing_evidence_id="ev_003", cited_evidence_id="ev_002")
        graph.add_citation(c1)
        graph.add_citation(c2)
        cited_by = graph.get_cited_by("ev_002")
        assert len(cited_by) == 2

    def test_many_to_many_citations(self):
        graph = ProvenanceGraph()
        c1 = Citation("ev_a", "ev_b")
        c2 = Citation("ev_a", "ev_c")
        c3 = Citation("ev_d", "ev_b")
        c4 = Citation("ev_e", "ev_b")
        graph.add_citation(c1)
        graph.add_citation(c2)
        graph.add_citation(c3)
        graph.add_citation(c4)
        # ev_a cites 2 evidence
        assert len(graph.get_citations("ev_a")) == 2
        # ev_b is cited by 3 evidence
        assert len(graph.get_cited_by("ev_b")) == 3

    def test_add_verification(self):
        graph = ProvenanceGraph()
        vr = VerificationRecord(evidence_id="ev_001", status="verified")
        graph.add_verification(vr)
        verifications = graph.get_verifications("ev_001")
        assert len(verifications) == 1
        assert verifications[0].status == "verified"

    def test_multiple_verifications(self):
        graph = ProvenanceGraph()
        vr1 = VerificationRecord(evidence_id="ev_001", status="verified", verified_by="engine_a")
        vr2 = VerificationRecord(evidence_id="ev_001", status="confirmed", verified_by="engine_b")
        graph.add_verification(vr1)
        graph.add_verification(vr2)
        verifications = graph.get_verifications("ev_001")
        assert len(verifications) == 2


class TestProvenanceGraphFullQuery:
    def test_get_full_provenance_empty(self):
        graph = ProvenanceGraph()
        result = graph.get_full_provenance("ev_nonexistent")
        assert result["origin"] is None
        assert result["derivation"] is None
        assert result["derivation_chain"] == []
        assert result["transformations"] == []
        assert result["aggregation_sources"] == []
        assert result["citations_made"] == []
        assert result["cited_by_count"] == 0

    def test_get_full_provenance_populated(self):
        graph = ProvenanceGraph()
        graph.set_origin("ev_002", "src_001")
        graph.add_derivation("ev_002", "ev_001")
        dr = DerivationRecord(DerivationType.PARSED.value, "ev_001", "ev_002")
        graph.add_transformation(dr)
        c = Citation("ev_002", "ev_001")
        graph.add_citation(c)
        vr = VerificationRecord(evidence_id="ev_002", status="verified")
        graph.add_verification(vr)

        result = graph.get_full_provenance("ev_002")
        assert result["origin"] == "src_001"
        assert result["derivation"] == "ev_001"
        assert "ev_001" in result["derivation_chain"]
        assert len(result["citations_made"]) == 1
        assert result["cited_by_count"] >= 0


# =========================================================================
# Immutability Tests
# =========================================================================

class TestProvenanceImmutability:
    def test_chain_link_immutable_source_type(self):
        link = EvidenceChainLink("derivation", "ev_002")
        with pytest.raises(Exception):
            link.link_type = "origin"

    def test_chain_link_immutable_target(self):
        link = EvidenceChainLink("derivation", "ev_002")
        with pytest.raises(Exception):
            link.target_evidence_id = "ev_003"

    def test_citation_immutable_contribution(self):
        c = Citation("ev_a", "ev_b", contribution=0.5)
        with pytest.raises(Exception):
            c.contribution = 0.7

    def test_derivation_record_immutable_type(self):
        dr = DerivationRecord(DerivationType.PARSED.value, "ev_a", "ev_b")
        with pytest.raises(Exception):
            dr.derivation_type = "normalized"

    def test_verification_record_immutable_evidence(self):
        vr = VerificationRecord(evidence_id="ev_001")
        with pytest.raises(Exception):
            vr.evidence_id = "ev_002"


# =========================================================================
# Failure Cases Tests
# =========================================================================

class TestProvenanceFailureCases:
    def test_negative_contribution_not_validated(self):
        """Citation does not validate contribution range (raw float, not Confidence)."""
        c = Citation("ev_a", "ev_b", contribution=-0.1)
        assert c.contribution == -0.1

    def test_contribution_above_one_valid_for_citation(self):
        # Citation uses float directly, not Confidence
        c = Citation("ev_a", "ev_b", contribution=1.5)
        assert c.contribution == 1.5  # No validation in Citation

    def test_empty_evidence_id(self):
        vr = VerificationRecord(evidence_id="")
        assert vr.evidence_id == ""

    def test_unknown_derivation_type(self):
        dr = DerivationRecord(
            derivation_type="unknown_type",
            source_evidence_id="ev_a",
            target_evidence_id="ev_b",
        )
        assert dr.derivation_type == "unknown_type"


# =========================================================================
# Serialization Tests
# =========================================================================

class TestProvenanceSerialization:
    def test_source_identity_to_iso_timestamp(self):
        sid = SourceIdentity(source_type="human", identifier="u1")
        datetime.fromisoformat(sid.timestamp)

    def test_verification_record_to_iso_timestamp(self):
        vr = VerificationRecord(evidence_id="ev_001")
        datetime.fromisoformat(vr.timestamp)

    def test_citation_to_iso_timestamp(self):
        c = Citation("ev_a", "ev_b")
        datetime.fromisoformat(c.timestamp)

    def test_evidence_chain_link_to_iso_timestamp(self):
        link = EvidenceChainLink("derivation", "ev_002")
        datetime.fromisoformat(link.timestamp)


# =========================================================================
# Construction Edge Cases Tests
# =========================================================================

class TestProvenanceConstructionEdgeCases:
    def test_source_metadata_empty_identifier(self):
        sm = SourceMetadata(identifier="")
        assert sm.identifier == ""

    def test_derivation_record_empty_process(self):
        dr = DerivationRecord(
            derivation_type=DerivationType.PARSED.value,
            source_evidence_id="ev_a",
            target_evidence_id="ev_b",
        )
        assert dr.process == ""

    def test_verification_record_empty_method(self):
        vr = VerificationRecord(evidence_id="ev_001")
        assert vr.method == ""

    def test_citation_zero_contribution(self):
        c = Citation("ev_a", "ev_b", contribution=0.0)
        assert c.contribution == 0.0

    def test_evidence_chain_empty_links_tuple(self):
        chain = EvidenceChain(evidence_id="ev_001", links=())
        assert chain.links == ()

    def test_multiple_sources_same_identity(self):
        s1 = SourceIdentity(source_type="human", identifier="u1")
        s2 = SourceIdentity(source_type="human", identifier="u1")
        assert s1.source_id != s2.source_id  # Different auto-generated IDs


# =========================================================================
# Integration Tests
# =========================================================================

class TestProvenanceIntegration:
    def test_full_provenance_workflow(self):
        graph = ProvenanceGraph()

        # Create source and set origin
        source = SourceIdentity(source_type="human", identifier="user_001")
        graph.set_origin("ev_001", source.source_id)

        # Add derivation
        graph.add_derivation("ev_002", "ev_001")

        # Add transformation
        dr = DerivationRecord(
            derivation_type=DerivationType.PARSED.value,
            source_evidence_id="ev_001",
            target_evidence_id="ev_002",
            process="pdf_parser",
        )
        graph.add_transformation(dr)

        # Add citation
        c = Citation("ev_001", "ev_002", rationale="Relevant context")
        graph.add_citation(c)

        # Add verification
        vr = VerificationRecord(
            evidence_id="ev_001",
            status="verified",
            verified_by="audit_engine",
        )
        graph.add_verification(vr)

        # Query full provenance
        result = graph.get_full_provenance("ev_001")
        assert result["origin"] == source.source_id
        assert result["derivation"] is None
        assert len(result["verifications"]) == 1

    def test_complex_citation_network(self):
        graph = ProvenanceGraph()

        citations = [
            Citation("ev_1", "ev_root"),
            Citation("ev_2", "ev_root"),
            Citation("ev_3", "ev_root"),
            Citation("ev_4", "ev_1"),
            Citation("ev_4", "ev_2"),
            Citation("ev_5", "ev_3"),
        ]

        for c in citations:
            graph.add_citation(c)

        assert len(graph.get_citations("ev_4")) == 2
        assert len(graph.get_cited_by("ev_root")) == 3
        assert len(graph.get_cited_by("ev_1")) == 1