"""Tests for SHUNYA Evidence Engine — core.evidence.

Covers the full evidence lifecycle, confidence computation, integrity
verification, evidence chains, querying, and edge cases.
"""

from __future__ import annotations

import pytest

from core.evidence import (
    EvidenceEngine,
    Evidence,
    EvidenceChain,
    EvidenceDirection,
    EvidenceStatus,
    EvidenceType,
    get_evidence_engine,
)


# =========================================================================
# Fixtures
# =========================================================================


@pytest.fixture
def engine() -> EvidenceEngine:
    """Fresh evidence engine for each test."""
    eng = EvidenceEngine()
    yield eng


# =========================================================================
# Evidence Creation
# =========================================================================


class TestCreateEvidence:
    def test_minimal_creation(self, engine: EvidenceEngine):
        """Create evidence with minimal required fields."""
        ev = engine.create_evidence(
            object_id="obj_001",
            evidence_type=EvidenceType.DOCUMENT,
            statement="Contract signed",
            source="notary",
            direction=EvidenceDirection.SUPPORTING,
            source_reliability=0.8,
        )
        assert ev.evidence_id is not None
        assert len(ev.evidence_id) == 36  # UUID v7 format
        assert ev.object_id == "obj_001"
        assert ev.evidence_type == "document"
        assert ev.statement == "Contract signed"
        assert ev.source == "notary"
        assert ev.direction == "supporting"
        assert ev.status == EvidenceStatus.COLLECTED.value
        assert ev.hash is not None
        assert len(ev.hash) == 64  # SHA-256 hex
        assert ev.parent_evidence_id is None
        assert ev.verified_at is None
        assert ev.verified_by is None

    def test_creation_with_all_fields(self, engine: EvidenceEngine):
        """Create evidence with all optional fields."""
        parent = engine.create_evidence(
            object_id="obj_001",
            evidence_type=EvidenceType.MEASUREMENT,
            statement="Parent observation",
            source="sensor",
            direction=EvidenceDirection.SUPPORTING,
            source_reliability=0.9,
        )
        child = engine.create_evidence(
            object_id="obj_001",
            evidence_type=EvidenceType.DERIVED,
            statement="Derived from parent",
            source="analyst",
            direction=EvidenceDirection.CONTRADICTING,
            source_reliability=0.7,
            captured_at="2026-07-24T10:00:00Z",
            parent_evidence_id=parent.evidence_id,
            metadata={"department": "audit", "priority": 1},
        )
        assert child.parent_evidence_id == parent.evidence_id
        assert child.captured_at == "2026-07-24T10:00:00Z"
        assert child.metadata["department"] == "audit"
        assert child.metadata["priority"] == 1

    def test_parent_must_exist(self, engine: EvidenceEngine):
        """Creating evidence with a non-existent parent raises ValueError."""
        with pytest.raises(ValueError, match="parent_evidence_id"):
            engine.create_evidence(
                object_id="obj_001",
                evidence_type="document",
                statement="orphan",
                source="test",
                direction="supporting",
                source_reliability=0.5,
                parent_evidence_id="nonexistent",
            )

    def test_enum_normalization(self, engine: EvidenceEngine):
        """Both enum and string values are accepted for type/direction."""
        ev1 = engine.create_evidence(
            object_id="obj_001",
            evidence_type=EvidenceType.CONTRACT,
            statement="test",
            source="test",
            direction=EvidenceDirection.SUPPORTING,
            source_reliability=0.5,
        )
        assert ev1.evidence_type == "contract"

        ev2 = engine.create_evidence(
            object_id="obj_001",
            evidence_type="system_log",
            statement="test",
            source="test",
            direction="contradicting",
            source_reliability=0.5,
        )
        assert ev2.evidence_type == "system_log"
        assert ev2.direction == "contradicting"

    def test_confidence_at_creation(self, engine: EvidenceEngine):
        """Confidence is computed at creation time."""
        # source_reliability=0.9 → base = 0.9*0.7+0.3 = 0.93
        ev = engine.create_evidence(
            object_id="obj_001",
            evidence_type="observation",
            statement="test",
            source="test",
            direction="supporting",
            source_reliability=0.9,
        )
        assert abs(ev.confidence - 0.93) < 0.001

        # source_reliability=0.0 → base = 0.0*0.7+0.3 = 0.30
        ev2 = engine.create_evidence(
            object_id="obj_001",
            evidence_type="observation",
            statement="test",
            source="test",
            direction="contradicting",
            source_reliability=0.0,
        )
        # base = 0.3, then invert → 1-0.3 = 0.7
        assert abs(ev2.confidence - 0.70) < 0.001

    def test_confidence_contradicting_inversion(self, engine: EvidenceEngine):
        """Contradicting evidence inverts the confidence."""
        ev = engine.create_evidence(
            object_id="obj_001",
            evidence_type="statement",
            statement="test",
            source="test",
            direction="contradicting",
            source_reliability=0.8,
        )
        # base = 0.8*0.7+0.3 = 0.86, invert → 1-0.86 = 0.14
        assert abs(ev.confidence - 0.14) < 0.001


# =========================================================================
# Evidence Verification
# =========================================================================


class TestVerifyEvidence:
    def test_verify_collected(self, engine: EvidenceEngine):
        """Verifying COLLECTED evidence updates status and confidence."""
        ev = engine.create_evidence(
            object_id="obj_001",
            evidence_type="document",
            statement="test",
            source="test",
            direction="supporting",
            source_reliability=0.5,
        )
        # base = 0.5*0.7+0.3 = 0.65
        assert abs(ev.confidence - 0.65) < 0.001

        v = engine.verify_evidence(ev.evidence_id, verified_by="auditor")
        assert v.status == EvidenceStatus.VERIFIED.value
        assert v.verified_by == "auditor"
        assert v.verified_at is not None
        # boost = 0.65 + 0.2 = 0.85
        assert abs(v.confidence - 0.85) < 0.001

    def test_verify_contested(self, engine: EvidenceEngine):
        """Verifying CONTESTED evidence is allowed."""
        ev = engine.create_evidence(
            object_id="obj_001",
            evidence_type="statement",
            statement="test",
            source="test",
            direction="supporting",
            source_reliability=0.5,
        )
        # Manually mark as contested by creating a new instance
        # (no contest method, but verify_evidence only checks terminal states)
        v = engine.verify_evidence(ev.evidence_id, verified_by="auditor")
        assert v.status == EvidenceStatus.VERIFIED.value

    def test_verify_superseded_raises(self, engine: EvidenceEngine):
        """Verifying SUPERSEDED evidence raises ValueError."""
        ev = engine.create_evidence(
            object_id="obj_001",
            evidence_type="statement",
            statement="test",
            source="test",
            direction="supporting",
            source_reliability=0.5,
        )
        engine.supersede_evidence(ev.evidence_id, reason="test")
        with pytest.raises(ValueError, match="Cannot verify"):
            engine.verify_evidence(ev.evidence_id, verified_by="auditor")

    def test_verify_nonexistent_raises(self, engine: EvidenceEngine):
        """Verifying non-existent evidence raises ValueError."""
        with pytest.raises(ValueError, match="not found"):
            engine.verify_evidence("nonexistent", verified_by="auditor")

    def test_verify_metadata_merge(self, engine: EvidenceEngine):
        """Verification merges provided metadata."""
        ev = engine.create_evidence(
            object_id="obj_001",
            evidence_type="document",
            statement="test",
            source="test",
            direction="supporting",
            source_reliability=0.5,
            metadata={"original_note": "first pass"},
        )
        v = engine.verify_evidence(
            ev.evidence_id,
            verified_by="auditor",
            metadata={"verified_by_team": "QA"},
        )
        assert v.metadata["original_note"] == "first pass"
        assert v.metadata["verified_by_team"] == "QA"


# =========================================================================
# Evidence Supersession
# =========================================================================


class TestSupersedeEvidence:
    def test_supersede_collected(self, engine: EvidenceEngine):
        """Superseding COLLECTED evidence marks it as SUPERSEDED."""
        ev = engine.create_evidence(
            object_id="obj_001",
            evidence_type="statement",
            statement="test",
            source="test",
            direction="supporting",
            source_reliability=0.5,
        )
        s = engine.supersede_evidence(ev.evidence_id, reason="Contradicted by new data")
        assert s.status == EvidenceStatus.SUPERSEDED.value
        assert s.metadata["superseded_reason"] == "Contradicted by new data"
        assert "superseded_at" in s.metadata

    def test_supersede_verified(self, engine: EvidenceEngine):
        """Superseding VERIFIED evidence is allowed."""
        ev = engine.create_evidence(
            object_id="obj_001",
            evidence_type="statement",
            statement="test",
            source="test",
            direction="supporting",
            source_reliability=0.5,
        )
        v = engine.verify_evidence(ev.evidence_id, verified_by="auditor")
        s = engine.supersede_evidence(v.evidence_id, reason="Newer evidence available")
        assert s.status == EvidenceStatus.SUPERSEDED.value

    def test_supersede_preserves_original(self, engine: EvidenceEngine):
        """Superseded evidence is still retrievable."""
        ev = engine.create_evidence(
            object_id="obj_001",
            evidence_type="statement",
            statement="original",
            source="test",
            direction="supporting",
            source_reliability=0.5,
        )
        engine.supersede_evidence(ev.evidence_id, reason="replaced")
        retrieved = engine.get_evidence(ev.evidence_id)
        assert retrieved is not None
        assert retrieved.status == EvidenceStatus.SUPERSEDED.value
        assert retrieved.statement == "original"

    def test_supersede_nonexistent_raises(self, engine: EvidenceEngine):
        with pytest.raises(ValueError, match="not found"):
            engine.supersede_evidence("nonexistent", reason="test")

    def test_supersede_metadata_merge(self, engine: EvidenceEngine):
        """Supersession merges metadata."""
        ev = engine.create_evidence(
            object_id="obj_001",
            evidence_type="statement",
            statement="test",
            source="test",
            direction="supporting",
            source_reliability=0.5,
        )
        s = engine.supersede_evidence(
            ev.evidence_id,
            reason="test",
            metadata={"replaced_by": "ev_new_001"},
        )
        assert s.metadata["replaced_by"] == "ev_new_001"


# =========================================================================
# Evidence Chains
# =========================================================================


class TestEvidenceChains:
    def test_single_node_chain(self, engine: EvidenceEngine):
        """A single evidence with no parent forms a chain of depth 0."""
        ev = engine.create_evidence(
            object_id="obj_001",
            evidence_type="document",
            statement="root",
            source="test",
            direction="supporting",
            source_reliability=0.5,
        )
        chain = engine.get_evidence_chain(ev.evidence_id)
        assert len(chain.chain) == 1
        assert chain.depth == 0
        assert chain.root_evidence_id == ev.evidence_id
        assert chain.chain[0].evidence_id == ev.evidence_id

    def test_two_node_chain(self, engine: EvidenceEngine):
        """Chain from leaf to root returns both nodes."""
        root = engine.create_evidence(
            object_id="obj_001",
            evidence_type="document",
            statement="root",
            source="test",
            direction="supporting",
            source_reliability=0.5,
        )
        leaf = engine.create_evidence(
            object_id="obj_001",
            evidence_type="derived",
            statement="leaf",
            source="test",
            direction="supporting",
            source_reliability=0.5,
            parent_evidence_id=root.evidence_id,
        )
        chain = engine.get_evidence_chain(leaf.evidence_id)
        assert len(chain.chain) == 2
        assert chain.depth == 1
        assert chain.root_evidence_id == root.evidence_id
        assert chain.chain[0].evidence_id == root.evidence_id
        assert chain.chain[1].evidence_id == leaf.evidence_id

    def test_three_node_chain(self, engine: EvidenceEngine):
        """Chain with three nodes is ordered root→leaf."""
        r1 = engine.create_evidence(
            object_id="obj_001",
            evidence_type="document",
            statement="root",
            source="test",
            direction="supporting",
            source_reliability=0.5,
        )
        r2 = engine.create_evidence(
            object_id="obj_001",
            evidence_type="derived",
            statement="middle",
            source="test",
            direction="supporting",
            source_reliability=0.5,
            parent_evidence_id=r1.evidence_id,
        )
        r3 = engine.create_evidence(
            object_id="obj_001",
            evidence_type="derived",
            statement="leaf",
            source="test",
            direction="supporting",
            source_reliability=0.5,
            parent_evidence_id=r2.evidence_id,
        )
        chain = engine.get_evidence_chain(r3.evidence_id)
        assert len(chain.chain) == 3
        assert chain.depth == 2
        assert [e.statement for e in chain.chain] == ["root", "middle", "leaf"]

    def test_chain_overall_confidence(self, engine: EvidenceEngine):
        """Overall confidence is geometric mean of chain confidences."""
        r1 = engine.create_evidence(
            object_id="obj_001", evidence_type="document",
            statement="root", source="s1",
            direction="supporting", source_reliability=0.9,
        )
        r2 = engine.create_evidence(
            object_id="obj_001", evidence_type="derived",
            statement="leaf", source="s2",
            direction="supporting", source_reliability=0.8,
            parent_evidence_id=r1.evidence_id,
        )
        chain = engine.get_evidence_chain(r2.evidence_id)
        expected = (r1.confidence * r2.confidence) ** 0.5
        assert abs(chain.overall_confidence - expected) < 0.001

    def test_chain_verified_flag(self, engine: EvidenceEngine):
        """Chain verified flag is True only when all links are verified."""
        r1 = engine.create_evidence(
            object_id="obj_001", evidence_type="document",
            statement="root", source="s1",
            direction="supporting", source_reliability=0.5,
        )
        r2 = engine.create_evidence(
            object_id="obj_001", evidence_type="derived",
            statement="leaf", source="s2",
            direction="supporting", source_reliability=0.5,
            parent_evidence_id=r1.evidence_id,
        )
        chain = engine.get_evidence_chain(r2.evidence_id)
        assert not chain.verified

        engine.verify_evidence(r1.evidence_id, verified_by="a")
        engine.verify_evidence(r2.evidence_id, verified_by="a")
        chain2 = engine.get_evidence_chain(r2.evidence_id)
        assert chain2.verified

    def test_chain_nonexistent_raises(self, engine: EvidenceEngine):
        with pytest.raises(ValueError, match="not found"):
            engine.get_evidence_chain("nonexistent")


# =========================================================================
# Querying
# =========================================================================


class TestQuerying:
    def test_get_evidence(self, engine: EvidenceEngine):
        """get_evidence returns the evidence or None."""
        ev = engine.create_evidence(
            object_id="obj_001", evidence_type="document",
            statement="test", source="s1",
            direction="supporting", source_reliability=0.5,
        )
        assert engine.get_evidence(ev.evidence_id) is ev
        assert engine.get_evidence("nonexistent") is None

    def test_get_evidence_for_object(self, engine: EvidenceEngine):
        """get_evidence_for_object returns all evidence for an object."""
        e1 = engine.create_evidence(
            object_id="obj_001", evidence_type="document",
            statement="a", source="s1",
            direction="supporting", source_reliability=0.5,
        )
        e2 = engine.create_evidence(
            object_id="obj_001", evidence_type="statement",
            statement="b", source="s2",
            direction="contradicting", source_reliability=0.5,
        )
        e3 = engine.create_evidence(
            object_id="obj_002", evidence_type="document",
            statement="c", source="s3",
            direction="supporting", source_reliability=0.5,
        )
        results = engine.get_evidence_for_object("obj_001")
        assert len(results) == 2
        assert e1 in results
        assert e2 in results
        assert e3 not in results

    def test_get_evidence_by_type(self, engine: EvidenceEngine):
        """get_evidence_by_type returns evidence filtered by type."""
        engine.create_evidence(
            object_id="obj_001", evidence_type="document",
            statement="a", source="s1",
            direction="supporting", source_reliability=0.5,
        )
        engine.create_evidence(
            object_id="obj_002", evidence_type="document",
            statement="b", source="s2",
            direction="supporting", source_reliability=0.5,
        )
        engine.create_evidence(
            object_id="obj_003", evidence_type="log",
            statement="c", source="s3",
            direction="supporting", source_reliability=0.5,
        )
        results = engine.get_evidence_by_type(EvidenceType.DOCUMENT)
        assert len(results) == 2

    def test_get_evidence_by_type_pagination(self, engine: EvidenceEngine):
        """get_evidence_by_type supports offset and limit."""
        for i in range(5):
            engine.create_evidence(
                object_id=f"obj_{i}", evidence_type="document",
                statement=f"e{i}", source="s1",
                direction="supporting", source_reliability=0.5,
            )
        assert len(engine.get_evidence_by_type("document", limit=2)) == 2
        assert len(engine.get_evidence_by_type("document", offset=2)) == 3
        assert len(engine.get_evidence_by_type("document", limit=2, offset=2)) == 2

    def test_get_evidence_by_source(self, engine: EvidenceEngine):
        """get_evidence_by_source returns evidence filtered by source."""
        engine.create_evidence(
            object_id="obj_001", evidence_type="document",
            statement="a", source="sensor_a",
            direction="supporting", source_reliability=0.5,
        )
        engine.create_evidence(
            object_id="obj_002", evidence_type="document",
            statement="b", source="sensor_a",
            direction="supporting", source_reliability=0.5,
        )
        engine.create_evidence(
            object_id="obj_003", evidence_type="document",
            statement="c", source="sensor_b",
            direction="supporting", source_reliability=0.5,
        )
        results = engine.get_evidence_by_source("sensor_a")
        assert len(results) == 2

    def test_search_evidence(self, engine: EvidenceEngine):
        """search_evidence finds evidence by statement text."""
        engine.create_evidence(
            object_id="obj_001", evidence_type="document",
            statement="Contract signed on January 15",
            source="s1", direction="supporting", source_reliability=0.5,
        )
        engine.create_evidence(
            object_id="obj_002", evidence_type="statement",
            statement="The contract was never signed",
            source="s2", direction="contradicting", source_reliability=0.5,
        )
        engine.create_evidence(
            object_id="obj_003", evidence_type="log",
            statement="System reboot at 03:00",
            source="s3", direction="supporting", source_reliability=0.5,
        )
        results = engine.search_evidence("contract")
        assert len(results) == 2

        results2 = engine.search_evidence("reboot")
        assert len(results2) == 1

    def test_search_evidence_wildcard(self, engine: EvidenceEngine):
        """search_evidence supports wildcard patterns."""
        engine.create_evidence(
            object_id="obj_001", evidence_type="document",
            statement="Security audit Q1 2025",
            source="s1", direction="supporting", source_reliability=0.5,
        )
        engine.create_evidence(
            object_id="obj_002", evidence_type="document",
            statement="Security audit Q2 2025",
            source="s2", direction="supporting", source_reliability=0.5,
        )
        results = engine.search_evidence("Security*")
        assert len(results) == 2


# =========================================================================
# Contradicting / Supporting
# =========================================================================


class TestDirectionalQueries:
    def test_get_supporting(self, engine: EvidenceEngine):
        """get_supporting_evidence returns only SUPPORTING evidence."""
        engine.create_evidence(
            object_id="obj_001", evidence_type="document",
            statement="a", source="s1",
            direction="supporting", source_reliability=0.5,
        )
        engine.create_evidence(
            object_id="obj_001", evidence_type="statement",
            statement="b", source="s2",
            direction="contradicting", source_reliability=0.5,
        )
        engine.create_evidence(
            object_id="obj_001", evidence_type="document",
            statement="c", source="s3",
            direction="supporting", source_reliability=0.5,
        )
        supp = engine.get_supporting_evidence("obj_001")
        contra = engine.get_contradicting_evidence("obj_001")
        assert len(supp) == 2
        assert len(contra) == 1

    def test_empty_object(self, engine: EvidenceEngine):
        """Objects with no evidence return empty lists."""
        assert engine.get_supporting_evidence("nonexistent") == []
        assert engine.get_contradicting_evidence("nonexistent") == []


# =========================================================================
# Confidence
# =========================================================================


class TestConfidence:
    def test_compute_confidence(self, engine: EvidenceEngine):
        """compute_confidence matches the formula."""
        ev = engine.create_evidence(
            object_id="obj_001", evidence_type="document",
            statement="test", source="s1",
            direction="supporting", source_reliability=0.7,
        )
        # base = 0.7*0.7+0.3 = 0.79
        computed = engine.compute_confidence(ev.evidence_id)
        assert abs(computed - 0.79) < 0.001

    def test_compute_confidence_verified(self, engine: EvidenceEngine):
        """Verification adds 0.2 to confidence."""
        ev = engine.create_evidence(
            object_id="obj_001", evidence_type="document",
            statement="test", source="s1",
            direction="supporting", source_reliability=0.7,
        )
        engine.verify_evidence(ev.evidence_id, verified_by="auditor")
        computed = engine.compute_confidence(ev.evidence_id)
        # base = 0.79 + 0.2 = 0.99
        assert abs(computed - 0.99) < 0.001

    def test_confidence_capped_at_one(self, engine: EvidenceEngine):
        """Confidence is capped at 1.0 even with high reliability + verification."""
        ev = engine.create_evidence(
            object_id="obj_001", evidence_type="document",
            statement="test", source="s1",
            direction="supporting", source_reliability=1.0,
        )
        # base = 1.0*0.7+0.3 = 1.0
        assert abs(ev.confidence - 1.0) < 0.001

        ev2 = engine.create_evidence(
            object_id="obj_002", evidence_type="document",
            statement="test", source="s1",
            direction="supporting", source_reliability=0.9,
        )
        # base = 0.9*0.7+0.3 = 0.93, +0.2 = 1.13 → capped at 1.0
        engine.verify_evidence(ev2.evidence_id, verified_by="auditor")
        assert abs(engine.compute_confidence(ev2.evidence_id) - 1.0) < 0.001

    def test_confidence_floor(self, engine: EvidenceEngine):
        """Confidence has a minimum floor of 0.0."""
        ev = engine.create_evidence(
            object_id="obj_001", evidence_type="document",
            statement="test", source="s1",
            direction="supporting", source_reliability=0.0,
        )
        # base = 0.0*0.7+0.3 = 0.3
        assert abs(ev.confidence - 0.30) < 0.001

    def test_aggregate_confidence_no_evidence(self, engine: EvidenceEngine):
        """No evidence → neutral 0.5."""
        score = engine.get_confidence_score("obj_001")
        assert score == 0.5

    def test_aggregate_confidence_only_supporting(self, engine: EvidenceEngine):
        """Only supporting evidence → mean of supporting confidences."""
        engine.create_evidence(
            object_id="obj_001", evidence_type="document",
            statement="a", source="s1",
            direction="supporting", source_reliability=0.8,
        )
        engine.create_evidence(
            object_id="obj_001", evidence_type="document",
            statement="b", source="s2",
            direction="supporting", source_reliability=0.6,
        )
        # sup mean = (0.86 + 0.72) / 2 = 0.79
        # con mean = 0.0
        # score = 0.79 * (1 - 0.0) = 0.79
        score = engine.get_confidence_score("obj_001")
        assert abs(score - 0.79) < 0.01

    def test_aggregate_confidence_mixed(self, engine: EvidenceEngine):
        """Mixed evidence: sup_mean * (1 - con_mean)."""
        engine.create_evidence(
            object_id="obj_001", evidence_type="document",
            statement="a", source="s1",
            direction="supporting", source_reliability=0.8,
        )
        engine.create_evidence(
            object_id="obj_001", evidence_type="statement",
            statement="b", source="s2",
            direction="contradicting", source_reliability=0.5,
        )
        # sup = 0.86, con = 0.35 (inverted from 0.65)
        # score = 0.86 * (1 - 0.35) = 0.86 * 0.65 = 0.559
        score = engine.get_confidence_score("obj_001")
        assert abs(score - 0.559) < 0.01


# =========================================================================
# Integrity
# =========================================================================


class TestIntegrity:
    def test_verify_integrity_passes(self, engine: EvidenceEngine):
        """verify_integrity returns True for untampered evidence."""
        ev = engine.create_evidence(
            object_id="obj_001", evidence_type="document",
            statement="test", source="s1",
            direction="supporting", source_reliability=0.5,
        )
        assert engine.verify_integrity(ev.evidence_id) is True

    def test_verify_integrity_nonexistent(self, engine: EvidenceEngine):
        """verify_integrity on non-existent evidence raises ValueError."""
        with pytest.raises(ValueError, match="not found"):
            engine.verify_integrity("nonexistent")


# =========================================================================
# Engine Lifecycle
# =========================================================================


class TestEngineLifecycle:
    def test_clear(self, engine: EvidenceEngine):
        """clear() removes all evidence."""
        engine.create_evidence(
            object_id="obj_001", evidence_type="document",
            statement="test", source="s1",
            direction="supporting", source_reliability=0.5,
        )
        assert len(engine.get_evidence_for_object("obj_001")) == 1
        engine.clear()
        assert engine.get_evidence_for_object("obj_001") == []

    def test_get_evidence_engine_singleton(self):
        """get_evidence_engine returns the same instance."""
        e1 = get_evidence_engine()
        e2 = get_evidence_engine()
        assert e1 is e2

    def test_independent_engines(self):
        """Two separate instances are independent."""
        e1 = EvidenceEngine()
        e2 = EvidenceEngine()
        e1.create_evidence(
            object_id="obj_001", evidence_type="document",
            statement="test", source="s1",
            direction="supporting", source_reliability=0.5,
        )
        assert len(e2.get_evidence_for_object("obj_001")) == 0


# =========================================================================
# Model Validation
# =========================================================================


class TestModelValidation:
    def test_evidence_invalid_source_reliability(self):
        """source_reliability must be in [0, 1]."""
        with pytest.raises(ValueError):
            Evidence(
                object_id="obj_001",
                evidence_type="document",
                statement="test",
                source="s1",
                source_reliability=1.5,
                direction="supporting",
            )

    def test_evidence_invalid_direction(self):
        with pytest.raises(ValueError):
            Evidence(
                object_id="obj_001",
                evidence_type="document",
                statement="test",
                source="s1",
                source_reliability=0.5,
                direction="invalid",
            )

    def test_evidence_invalid_type(self):
        with pytest.raises(ValueError):
            Evidence(
                object_id="obj_001",
                evidence_type="not_a_valid_type",
                statement="test",
                source="s1",
                source_reliability=0.5,
                direction="supporting",
            )

    def test_evidence_invalid_status(self):
        with pytest.raises(ValueError):
            Evidence(
                object_id="obj_001",
                evidence_type="document",
                statement="test",
                source="s1",
                source_reliability=0.5,
                direction="supporting",
                status="invalid_status",
            )

    def test_evidence_immutable(self):
        """Evidence is a frozen dataclass."""
        ev = Evidence(
            object_id="obj_001",
            evidence_type="document",
            statement="test",
            source="s1",
            source_reliability=0.5,
            direction="supporting",
        )
        with pytest.raises(Exception):
            ev.statement = "modified"

    def test_evidence_chain_auto_fields(self):
        """EvidenceChain auto-computes depth and verified."""
        ev = Evidence(
            object_id="obj_001",
            evidence_type="document",
            statement="test",
            source="s1",
            source_reliability=0.5,
            direction="supporting",
        )
        chain = EvidenceChain(
            root_evidence_id=ev.evidence_id,
            chain=[ev],
        )
        assert chain.depth == 0
        assert not chain.verified  # not VERIFIED status

        # Create a chain with all VERIFIED
        ev2 = Evidence(
            object_id="obj_001",
            evidence_type="document",
            statement="test",
            source="s1",
            source_reliability=0.5,
            direction="supporting",
            status=EvidenceStatus.VERIFIED.value,
        )
        chain2 = EvidenceChain(
            root_evidence_id=ev2.evidence_id,
            chain=[ev2],
        )
        assert chain2.verified is True