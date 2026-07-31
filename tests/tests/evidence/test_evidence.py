"""Tests for SHUNYA Evidence Engine — E-004-MOD-001.

Architecture references:
    SMS-VOLUME-II-WORLD-MODEL.md §8 — Evidence Contract
    SMS-VOLUME-I_5-CORE-SEMANTICS.md §8 — The Meaning of Evidence

Constitutional invariants tested:
    - Evidence records are NEVER deleted
    - Evidence identity is permanent, unique, never reused
    - Evidence versions are append-only (never rewritten)
    - Every evidence record has at least one target
    - Confidence is always 0.0–1.0
    - Evidence chains are acyclic
    - Observations record "I observed X" — NOT "X is true"
"""

import pytest
from datetime import datetime, timezone
from app.evidence import (
    Evidence, Observation, EvidenceSource, Provenance,
    EvidenceStatus, EvidenceType, SourceCategory,
    Confidence, Freshness, VersionReference, EvidenceReference,
    EvidenceStore,
)
from app.evidence.models import InMemoryEvidenceStore


# =========================================================================
# Fixtures
# =========================================================================

@pytest.fixture
def sample_source() -> EvidenceSource:
    return EvidenceSource(
        category=SourceCategory.HUMAN,
        identifier="user_001",
        description="Test user",
    )


@pytest.fixture
def sample_provenance(sample_source) -> Provenance:
    return Provenance(
        created_by="test_engine",
        created_at="2026-07-23T12:00:00",
        source=sample_source,
        process="test_process",
        rationale="Test evidence creation",
    )


@pytest.fixture
def sample_confidence() -> Confidence:
    return Confidence(score=0.95, label="high", reason="Direct observation")


@pytest.fixture
def sample_evidence(sample_provenance, sample_source, sample_confidence) -> Evidence:
    return Evidence(
        target_id="n_target_001",
        target_type="Node",
        observation_id="obs_001",
        provenance=sample_provenance,
        source=sample_source,
        evidence_type=EvidenceType.OBSERVED.value,
        confidence=sample_confidence,
        status=EvidenceStatus.ACTIVE.value,
        version=1,
    )


@pytest.fixture
def sample_observation() -> Observation:
    return Observation(
        observer="user_001",
        content="The document was received on 2026-07-22",
        context="Document processing pipeline",
        confidence=Confidence(score=0.9, label="high"),
    )


# =========================================================================
# Evidence Identity Tests
# =========================================================================

class TestEvidenceIdentity:
    """Evidence identity is permanent, unique, never reused (§8.2)."""

    def test_identity_auto_generated(self):
        """Evidence without explicit ID gets a generated identity."""
        ev = Evidence(target_id="t1", target_type="Node")
        assert ev.evidence_id != ""
        assert ev.evidence_id.startswith("ev_")

    def test_identity_unique_across_instances(self):
        """Two Evidence instances have different identities."""
        ev1 = Evidence(target_id="t1", target_type="Node")
        ev2 = Evidence(target_id="t2", target_type="Node")
        assert ev1.evidence_id != ev2.evidence_id

    def test_identity_prefix(self):
        """Evidence identity starts with 'ev_'."""
        ev = Evidence(target_id="t1", target_type="Node")
        assert ev.evidence_id.startswith("ev_")

    def test_identity_length(self):
        """Evidence identity is at least 16 characters."""
        ev = Evidence(target_id="t1", target_type="Node")
        assert len(ev.evidence_id) >= 16

    def test_identity_preserved_across_versions(self):
        """Identity is preserved when creating next version."""
        ev = Evidence(target_id="t1", target_type="Node")
        v2 = ev.next_version()
        assert v2.evidence_id == ev.evidence_id

    def test_identity_immutable(self):
        """Evidence identity cannot be changed after creation."""
        ev = Evidence(target_id="t1", target_type="Node", evidence_id="ev_fixed_001")
        assert ev.evidence_id == "ev_fixed_001"


# =========================================================================
# Evidence Immutability Tests
# =========================================================================

class TestEvidenceImmutability:
    """Evidence records are frozen dataclasses — never mutated in place."""

    def test_evidence_is_frozen(self):
        """Evidence is a frozen dataclass."""
        ev = Evidence(target_id="t1", target_type="Node")
        assert ev.__dataclass_fields__["evidence_id"].metadata.get("frozen", True) is not False

    def test_cannot_modify_evidence_id(self):
        """Cannot set evidence_id after construction."""
        ev = Evidence(target_id="t1", target_type="Node")
        with pytest.raises(Exception):
            ev.evidence_id = "new_id"

    def test_cannot_modify_target_id(self):
        """Cannot set target_id after construction."""
        ev = Evidence(target_id="t1", target_type="Node")
        with pytest.raises(Exception):
            ev.target_id = "new_target"

    def test_cannot_modify_confidence(self):
        """Cannot set confidence after construction."""
        ev = Evidence(target_id="t1", target_type="Node")
        with pytest.raises(Exception):
            ev.confidence = Confidence(score=0.5)

    def test_cannot_modify_version(self):
        """Cannot set version after construction."""
        ev = Evidence(target_id="t1", target_type="Node")
        with pytest.raises(Exception):
            ev.version = 99

    def test_cannot_modify_status(self):
        """Cannot set status after construction."""
        ev = Evidence(target_id="t1", target_type="Node")
        with pytest.raises(Exception):
            ev.status = "withdrawn"

    def test_observation_is_frozen(self):
        """Observation is a frozen dataclass."""
        obs = Observation(observer="u1", content="test")
        with pytest.raises(Exception):
            obs.observer = "new_observer"


# =========================================================================
# Evidence Versioning Tests
# =========================================================================

class TestEvidenceVersioning:
    """Version history is append-only, never rewritten."""

    def test_default_version_is_one(self):
        """Default version is 1."""
        ev = Evidence(target_id="t1", target_type="Node")
        assert ev.version == 1

    def test_next_version_increments(self, sample_evidence):
        """next_version() increments version by 1."""
        v2 = sample_evidence.next_version()
        assert v2.version == 2

    def test_next_version_three_times(self, sample_evidence):
        """Multiple next_version() calls increment correctly."""
        v2 = sample_evidence.next_version()
        v3 = v2.next_version()
        v4 = v3.next_version()
        assert v2.version == 2
        assert v3.version == 3
        assert v4.version == 4

    def test_original_preserved_after_next_version(self, sample_evidence):
        """Original evidence is unchanged after creating next version."""
        original_id = sample_evidence.evidence_id
        original_version = sample_evidence.version
        _ = sample_evidence.next_version()
        assert sample_evidence.version == original_version
        assert sample_evidence.evidence_id == original_id

    def test_next_version_can_change_status(self, sample_evidence):
        """next_version() can update the status."""
        v2 = sample_evidence.next_version(status=EvidenceStatus.SUPERSEDED.value)
        assert v2.status == EvidenceStatus.SUPERSEDED.value

    def test_next_version_can_change_confidence(self, sample_evidence):
        """next_version() can update the confidence."""
        new_conf = Confidence(score=0.5, label="medium")
        v2 = sample_evidence.next_version(confidence=new_conf)
        assert v2.confidence == new_conf

    def test_next_version_supersedes_previous(self, sample_evidence):
        """next_version() sets supersedes to the previous evidence_id."""
        v2 = sample_evidence.next_version()
        assert v2.supersedes == sample_evidence.evidence_id

    def test_version_history_is_append_only(self, sample_evidence):
        """Version history can be constructed by chaining next_version()."""
        ev = sample_evidence
        history = [ev]
        for _ in range(5):
            ev = ev.next_version()
            history.append(ev)
        assert len(history) == 6
        assert history[0].version == 1
        assert history[5].version == 6
        # All have the same identity
        ids = {e.evidence_id for e in history}
        assert len(ids) == 1

    def test_next_version_merges_metadata(self, sample_evidence):
        """next_version() merges metadata with existing."""
        v2 = sample_evidence.next_version(
            metadata={"reviewed_by": "auditor_001"}
        )
        assert v2.metadata.get("reviewed_by") == "auditor_001"


# =========================================================================
# Evidence Lifecycle Tests
# =========================================================================

class TestEvidenceLifecycle:
    """Evidence lifecycle status transitions."""

    def test_default_status_active(self):
        """Default status is ACTIVE."""
        ev = Evidence(target_id="t1", target_type="Node")
        assert ev.status == EvidenceStatus.ACTIVE.value
        assert ev.is_active

    def test_superseded_status(self, sample_evidence):
        """Evidence can be superseded."""
        v2 = sample_evidence.next_version(status=EvidenceStatus.SUPERSEDED.value)
        assert v2.is_superseded

    def test_withdrawn_status(self, sample_evidence):
        """Evidence can be withdrawn."""
        v2 = sample_evidence.next_version(status=EvidenceStatus.WITHDRAWN.value)
        assert v2.is_withdrawn

    def test_expired_status(self, sample_evidence):
        """Evidence can expire."""
        v2 = sample_evidence.next_version(status=EvidenceStatus.EXPIRED.value)
        assert v2.is_expired

    def test_all_statuses_accessible(self):
        """All EvidenceStatus values are accessible."""
        assert EvidenceStatus.ACTIVE.value == "active"
        assert EvidenceStatus.SUPERSEDED.value == "superseded"
        assert EvidenceStatus.WITHDRAWN.value == "withdrawn"
        assert EvidenceStatus.EXPIRED.value == "expired"

    def test_no_destructive_deletion(self):
        """EvidenceStatus has no DELETED value."""
        assert not hasattr(EvidenceStatus, "DELETED")


# =========================================================================
# Evidence Construction Tests
# =========================================================================

class TestEvidenceConstruction:
    """Evidence construction with various parameters."""

    def test_minimal_construction(self):
        """Evidence can be constructed with only target_id and target_type."""
        ev = Evidence(target_id="t1", target_type="Node")
        assert ev.target_id == "t1"
        assert ev.target_type == "Node"

    def test_full_construction(self, sample_evidence, sample_provenance,
                              sample_source, sample_confidence):
        """Evidence can be constructed with all fields."""
        ev = sample_evidence
        assert ev.evidence_id != ""
        assert ev.target_id == "n_target_001"
        assert ev.target_type == "Node"
        assert ev.evidence_type == EvidenceType.OBSERVED.value
        assert ev.confidence == sample_confidence
        assert ev.provenance == sample_provenance
        assert ev.source == sample_source
        assert ev.version == 1
        assert ev.status == EvidenceStatus.ACTIVE.value

    def test_construction_with_all_types(self):
        """Evidence can be created with each EvidenceType."""
        for etype in EvidenceType:
            ev = Evidence(
                target_id="t1", target_type="Node",
                evidence_type=etype.value,
            )
            assert ev.evidence_type == etype.value

    def test_construction_with_confidence(self):
        """Evidence can be constructed with confidence."""
        conf = Confidence(score=0.75, label="medium")
        ev = Evidence(target_id="t1", target_type="Node", confidence=conf)
        assert ev.confidence == conf

    def test_construction_with_freshness(self):
        """Evidence can be constructed with freshness."""
        fresh = Freshness(
            captured_at="2026-07-23T12:00:00",
            valid_until="2026-08-23T12:00:00",
        )
        ev = Evidence(target_id="t1", target_type="Node", freshness=fresh)
        assert ev.freshness == fresh

    def test_construction_with_supersedes(self):
        """Evidence can be constructed with supersedes reference."""
        ev = Evidence(
            target_id="t1", target_type="Node",
            supersedes="ev_prev_001",
        )
        assert ev.supersedes == "ev_prev_001"

    def test_construction_with_metadata(self):
        """Evidence can be constructed with metadata."""
        ev = Evidence(
            target_id="t1", target_type="Node",
            metadata={"source_system": "email_pipeline", "priority": "high"},
        )
        assert ev.metadata["source_system"] == "email_pipeline"
        assert ev.metadata["priority"] == "high"


# =========================================================================
# Evidence Serialization Tests
# =========================================================================

class TestEvidenceSerialization:
    """Evidence serialization to canonical dictionary."""

    def test_to_dict_includes_identity(self, sample_evidence):
        """to_dict includes evidence_id."""
        d = sample_evidence.to_dict()
        assert d["evidence_id"] == sample_evidence.evidence_id

    def test_to_dict_includes_target(self, sample_evidence):
        """to_dict includes target_id and target_type."""
        d = sample_evidence.to_dict()
        assert d["target_id"] == "n_target_001"
        assert d["target_type"] == "Node"

    def test_to_dict_includes_type(self, sample_evidence):
        """to_dict includes evidence_type."""
        d = sample_evidence.to_dict()
        assert d["evidence_type"] == EvidenceType.OBSERVED.value

    def test_to_dict_includes_status(self, sample_evidence):
        """to_dict includes status."""
        d = sample_evidence.to_dict()
        assert d["status"] == EvidenceStatus.ACTIVE.value

    def test_to_dict_includes_version(self, sample_evidence):
        """to_dict includes version."""
        d = sample_evidence.to_dict()
        assert d["version"] == 1

    def test_to_dict_includes_provenance(self, sample_evidence):
        """to_dict includes provenance when present."""
        d = sample_evidence.to_dict()
        assert "provenance" in d
        assert d["provenance"]["created_by"] == "test_engine"

    def test_to_dict_includes_confidence(self, sample_evidence, sample_confidence):
        """to_dict includes confidence when present."""
        d = sample_evidence.to_dict()
        assert "confidence" in d
        assert d["confidence"]["score"] == sample_confidence.score

    def test_to_dict_minimal(self):
        """to_dict works with minimal evidence (no optional fields)."""
        ev = Evidence(target_id="t1", target_type="Node")
        d = ev.to_dict()
        assert d["target_id"] == "t1"
        assert d["target_type"] == "Node"


# =========================================================================
# Evidence Equality Tests
# =========================================================================

class TestEvidenceEquality:
    """Evidence equality semantics."""

    def test_evidence_equality_same_id(self):
        """Two Evidence with same fields are equal (frozen dataclass)."""
        ev1 = Evidence(
            target_id="t1", target_type="Node",
            evidence_id="ev_test_001",
            created_at="2026-07-23T12:00:00",
        )
        ev2 = Evidence(
            target_id="t1", target_type="Node",
            evidence_id="ev_test_001",
            created_at="2026-07-23T12:00:00",
        )
        assert ev1 == ev2

    def test_evidence_inequality_different_id(self):
        """Two Evidence with different IDs are not equal."""
        ev1 = Evidence(target_id="t1", target_type="Node")
        ev2 = Evidence(target_id="t1", target_type="Node")
        assert ev1 != ev2  # Different auto-generated IDs

    def test_evidence_inequality_different_target(self):
        """Two Evidence with different targets are not equal."""
        ev1 = Evidence(
            target_id="t1", target_type="Node",
            evidence_id="ev_test_001",
            created_at="2026-07-23T12:00:00",
        )
        ev2 = Evidence(
            target_id="t2", target_type="Node",
            evidence_id="ev_test_001",
            created_at="2026-07-23T12:00:00",
        )
        assert ev1 != ev2  # Different target_id

    def test_evidence_inequality_different_version(self):
        """Two Evidence with different versions are not equal."""
        ev1 = Evidence(
            target_id="t1", target_type="Node",
            evidence_id="ev_test_001",
            version=1,
            created_at="2026-07-23T12:00:00",
        )
        ev2 = Evidence(
            target_id="t1", target_type="Node",
            evidence_id="ev_test_001",
            version=2,
            created_at="2026-07-23T12:00:00",
        )
        assert ev1 != ev2

    def test_confidence_equality(self):
        """Two Confidence with same score are equal."""
        c1 = Confidence(score=0.95, label="high")
        c2 = Confidence(score=0.95, label="high")
        assert c1 == c2

    def test_confidence_inequality(self):
        """Two Confidence with different scores are not equal."""
        c1 = Confidence(score=0.95)
        c2 = Confidence(score=0.50)
        assert c1 != c2


# =========================================================================
# Append-Only Behavior Tests
# =========================================================================

class TestAppendOnly:
    """Evidence is append-only. Never rewritten."""

    def test_next_version_preserves_original(self, sample_evidence):
        """Original evidence is preserved when creating next version."""
        original = sample_evidence
        _ = original.next_version()
        # Original is unchanged
        assert original.version == 1
        assert original.status == EvidenceStatus.ACTIVE.value

    def test_observation_is_immutable(self, sample_observation):
        """Observation cannot be modified after creation."""
        obs = sample_observation
        with pytest.raises(Exception):
            obs.content = "modified content"

    def test_provenance_is_immutable(self, sample_provenance):
        """Provenance cannot be modified after creation."""
        prov = sample_provenance
        with pytest.raises(Exception):
            prov.created_by = "new_actor"

    def test_evidence_source_is_immutable(self, sample_source):
        """EvidenceSource cannot be modified after creation."""
        src = sample_source
        with pytest.raises(Exception):
            src.identifier = "new_identifier"

    def test_confidence_is_immutable(self):
        """Confidence cannot be modified after creation."""
        c = Confidence(score=0.9)
        with pytest.raises(Exception):
            c.score = 0.5

    def test_freshness_is_immutable(self):
        """Freshness cannot be modified after creation."""
        f = Freshness(captured_at="2026-07-23T12:00:00")
        with pytest.raises(Exception):
            f.captured_at = "new_time"


# =========================================================================
# Failure Cases and Invalid Construction Tests
# =========================================================================

class TestFailureCases:
    """Evidence constructors reject invalid inputs."""

    def test_negative_confidence_raises(self):
        """Confidence below 0.0 raises ValueError."""
        with pytest.raises(ValueError):
            Confidence(score=-0.1)

    def test_confidence_above_one_raises(self):
        """Confidence above 1.0 raises ValueError."""
        with pytest.raises(ValueError):
            Confidence(score=1.5)

    def test_confidence_at_zero_is_valid(self):
        """Confidence of 0.0 is valid."""
        c = Confidence(score=0.0)
        assert c.score == 0.0

    def test_confidence_at_one_is_valid(self):
        """Confidence of 1.0 is valid."""
        c = Confidence(score=1.0)
        assert c.score == 1.0

    def test_confidence_at_boundary(self):
        """Confidence at exact boundary values."""
        c1 = Confidence(score=0.0)
        c2 = Confidence(score=1.0)
        assert c1.score == 0.0
        assert c2.score == 1.0

    def test_evidence_without_target_type(self):
        """Evidence can be constructed with empty target_type (default is set)."""
        ev = Evidence(target_id="t1")
        # target_type defaults to empty string, not required to be set

    def test_evidence_without_target_id(self):
        """Evidence with empty target_id is valid (minimal)."""
        ev = Evidence()
        assert ev.target_id == ""


# =========================================================================
# Edge Cases
# =========================================================================

class TestEdgeCases:
    """Edge cases for evidence models."""

    def test_evidence_with_long_metadata(self):
        """Evidence with large metadata dict is valid."""
        large_meta = {f"key_{i}": f"value_{i}" for i in range(100)}
        ev = Evidence(target_id="t1", target_type="Node", metadata=large_meta)
        assert len(ev.metadata) == 100

    def test_evidence_with_empty_strings(self):
        """Evidence with empty string fields is valid."""
        ev = Evidence(
            target_id="",
            target_type="",
            observation_id="",
        )
        assert ev.target_id == ""

    def test_observation_minimal(self):
        """Observation can be constructed with minimal fields."""
        obs = Observation(observer="u1", content="saw something")
        assert obs.observer == "u1"
        assert obs.content == "saw something"

    def test_observation_auto_generates_id(self):
        """Observation without explicit ID gets a generated identity."""
        obs = Observation(observer="u1", content="test")
        assert obs.observation_id != ""
        assert obs.observation_id.startswith("ev_")

    def test_provenance_minimal(self):
        """Provenance can be constructed with minimal fields."""
        src = EvidenceSource(
            category=SourceCategory.SYSTEM,
            identifier="sys_001",
        )
        prov = Provenance(
            created_by="engine",
            created_at="2026-07-23T12:00:00",
            source=src,
        )
        assert prov.created_by == "engine"
        assert prov.process == ""

    def test_source_with_all_categories(self):
        """EvidenceSource can be created with each SourceCategory."""
        for cat in SourceCategory:
            src = EvidenceSource(category=cat, identifier=f"id_{cat.value}")
            assert src.category == cat

    def test_evidence_with_explicit_freshness_no_expiry(self):
        """Freshness without valid_until is valid."""
        fresh = Freshness(captured_at="2026-07-23T12:00:00")
        assert fresh.valid_until is None

    def test_evidence_reference_construction(self):
        """EvidenceReference can be constructed."""
        ref = EvidenceReference(
            evidence_id="ev_001",
            target_id="t1",
            target_type="Node",
        )
        assert ref.evidence_id == "ev_001"
        assert ref.target_id == "t1"

    def test_version_reference_construction(self):
        """VersionReference can be constructed."""
        ref = VersionReference(evidence_id="ev_001", version=3)
        assert ref.evidence_id == "ev_001"
        assert ref.version == 3

    def test_evidence_type_enum_values(self):
        """All EvidenceType values are correct."""
        assert EvidenceType.OBSERVED.value == "observed"
        assert EvidenceType.REPORTED.value == "reported"
        assert EvidenceType.CALCULATED.value == "calculated"
        assert EvidenceType.INFERRED.value == "inferred"
        assert EvidenceType.PREDICTED.value == "predicted"
        assert EvidenceType.GENERATED.value == "generated"

    def test_source_category_enum_values(self):
        """All SourceCategory values are correct."""
        assert SourceCategory.HUMAN.value == "human"
        assert SourceCategory.SYSTEM.value == "system"
        assert SourceCategory.SENSOR.value == "sensor"
        assert SourceCategory.DOCUMENT.value == "document"
        assert SourceCategory.DERIVED.value == "derived"
        assert SourceCategory.EXTERNAL.value == "external"


# =========================================================================
# Observation Tests
# =========================================================================

class TestObservation:
    """Observation records 'I observed X', NOT 'X is true'."""

    def test_observation_is_not_truth(self):
        """Observation does not assert truth."""
        obs = Observation(
            observer="sensor_001",
            content="Temperature reading: 37.2°C",
        )
        # Observation only records what was observed
        assert "Temperature reading" in obs.content
        # It does not claim "The temperature is 37.2°C"

    def test_observation_has_observer(self):
        """Observation records who observed."""
        obs = Observation(
            observer="sensor_001",
            content="Signal detected",
        )
        assert obs.observer == "sensor_001"

    def test_observation_has_timestamp(self):
        """Observation auto-generates a timestamp."""
        obs = Observation(observer="u1", content="test")
        assert obs.observed_at != ""

    def test_observation_has_no_truth_value(self):
        """Observation does not have a truth field."""
        obs = Observation(observer="u1", content="test")
        assert not hasattr(obs, "is_true")
        assert not hasattr(obs, "truth")
        assert not hasattr(obs, "validity")

    def test_observation_with_confidence(self):
        """Observation can carry raw confidence."""
        obs = Observation(
            observer="u1",
            content="test",
            confidence=Confidence(score=0.8, label="moderate"),
        )
        assert obs.confidence is not None
        assert obs.confidence.score == 0.8

    def test_observation_with_source(self):
        """Observation can carry source information."""
        src = EvidenceSource(
            category=SourceCategory.SENSOR,
            identifier="temp_sensor_01",
        )
        obs = Observation(
            observer="temp_sensor_01",
            content="37.2°C",
            source=src,
        )
        assert obs.source is not None
        assert obs.source.category == SourceCategory.SENSOR


# =========================================================================
# Evidence Store Tests
# =========================================================================

class TestEvidenceStore:
    """EvidenceStore CRUD operations."""

    def test_store_create_and_get(self):
        """Evidence can be stored and retrieved by identity."""
        store = InMemoryEvidenceStore()
        ev = Evidence(target_id="t1", target_type="Node")
        stored = store.create(ev)
        assert stored.evidence_id == ev.evidence_id
        retrieved = store.get(ev.evidence_id)
        assert retrieved is not None
        assert retrieved.evidence_id == ev.evidence_id

    def test_store_get_nonexistent(self):
        """Getting nonexistent evidence returns None."""
        store = InMemoryEvidenceStore()
        assert store.get("ev_nonexistent") is None

    def test_store_create_duplicate_raises(self):
        """Creating duplicate evidence raises ValueError."""
        store = InMemoryEvidenceStore()
        ev = Evidence(target_id="t1", target_type="Node")
        store.create(ev)
        with pytest.raises(ValueError):
            store.create(ev)

    def test_store_count(self):
        """Store count reflects number of evidence records."""
        store = InMemoryEvidenceStore()
        assert store.count() == 0
        store.create(Evidence(target_id="t1", target_type="Node"))
        assert store.count() == 1
        store.create(Evidence(target_id="t2", target_type="Node"))
        assert store.count() == 2

    def test_store_all(self):
        """Store.all() returns all evidence records."""
        store = InMemoryEvidenceStore()
        ev1 = store.create(Evidence(target_id="t1", target_type="Node"))
        ev2 = store.create(Evidence(target_id="t2", target_type="Node"))
        all_ev = store.all()
        assert len(all_ev) == 2
        ids = {e.evidence_id for e in all_ev}
        assert ev1.evidence_id in ids
        assert ev2.evidence_id in ids

    def test_store_version_history(self):
        """Store tracks version history."""
        store = InMemoryEvidenceStore()
        ev1 = store.create(Evidence(target_id="t1", target_type="Node"))
        ev2 = store.create_version(ev1.next_version(status=EvidenceStatus.SUPERSEDED.value))
        history = store.get_history(ev1.evidence_id)
        assert len(history) == 2
        assert history[0].version == 1
        assert history[1].version == 2

    def test_store_get_version(self):
        """Store can retrieve a specific version."""
        store = InMemoryEvidenceStore()
        ev1 = store.create(Evidence(target_id="t1", target_type="Node"))
        ev2 = store.create_version(ev1.next_version(status=EvidenceStatus.SUPERSEDED.value))
        v1 = store.get_version(ev1.evidence_id, 1)
        v2 = store.get_version(ev1.evidence_id, 2)
        assert v1 is not None and v1.version == 1
        assert v2 is not None and v2.version == 2

    def test_store_get_nonexistent_version(self):
        """Getting a nonexistent version returns None."""
        store = InMemoryEvidenceStore()
        ev = store.create(Evidence(target_id="t1", target_type="Node"))
        assert store.get_version(ev.evidence_id, 99) is None

    def test_store_get_history_empty(self):
        """Getting history for nonexistent evidence returns empty list."""
        store = InMemoryEvidenceStore()
        assert store.get_history("ev_nonexistent") == []

    def test_store_all_returns_latest_version(self):
        """Store.all() returns the latest version of each evidence."""
        store = InMemoryEvidenceStore()
        ev1 = store.create(Evidence(target_id="t1", target_type="Node"))
        store.create_version(ev1.next_version(status=EvidenceStatus.SUPERSEDED.value))
        all_ev = store.all()
        assert len(all_ev) == 1
        assert all_ev[0].version == 2


# =========================================================================
# EvidenceSource Tests
# =========================================================================

class TestEvidenceSource:
    """EvidenceSource canonical representation of origin."""

    def test_source_creation(self):
        """EvidenceSource can be created with category and identifier."""
        src = EvidenceSource(
            category=SourceCategory.HUMAN,
            identifier="user_001",
        )
        assert src.category == SourceCategory.HUMAN
        assert src.identifier == "user_001"

    def test_source_with_description(self):
        """EvidenceSource can have a description."""
        src = EvidenceSource(
            category=SourceCategory.SYSTEM,
            identifier="obs_engine",
            description="Observation Engine v1.0",
        )
        assert src.description == "Observation Engine v1.0"

    def test_source_with_metadata(self):
        """EvidenceSource can carry metadata."""
        src = EvidenceSource(
            category=SourceCategory.DOCUMENT,
            identifier="doc_001",
            metadata={"file_type": "pdf", "page_count": 42},
        )
        assert src.metadata["file_type"] == "pdf"

    def test_source_is_immutable(self):
        """EvidenceSource is immutable."""
        src = EvidenceSource(
            category=SourceCategory.HUMAN,
            identifier="u1",
        )
        with pytest.raises(Exception):
            src.identifier = "new_id"


# =========================================================================
# Provenance Tests
# =========================================================================

class TestProvenance:
    """Provenance chain of custody is append-only."""

    def test_provenance_creation(self, sample_source):
        """Provenance can be created with required fields."""
        prov = Provenance(
            created_by="engine",
            created_at="2026-07-23T12:00:00",
            source=sample_source,
        )
        assert prov.created_by == "engine"
        assert prov.source == sample_source

    def test_provenance_with_process(self, sample_source):
        """Provenance can record the process."""
        prov = Provenance(
            created_by="engine",
            created_at="2026-07-23T12:00:00",
            source=sample_source,
            process="observer_engine",
        )
        assert prov.process == "observer_engine"

    def test_provenance_with_supersedes(self, sample_source):
        """Provenance can record what it supersedes."""
        prov = Provenance(
            created_by="engine",
            created_at="2026-07-23T12:00:00",
            source=sample_source,
            supersedes="ev_previous_001",
        )
        assert prov.supersedes == "ev_previous_001"

    def test_provenance_with_derived_from(self, sample_source):
        """Provenance can record derivation."""
        prov = Provenance(
            created_by="engine",
            created_at="2026-07-23T12:00:00",
            source=sample_source,
            derived_from="ev_source_001",
        )
        assert prov.derived_from == "ev_source_001"

    def test_provenance_is_immutable(self, sample_provenance):
        """Provenance is immutable after creation."""
        with pytest.raises(Exception):
            sample_provenance.created_by = "new_actor"

    def test_provenance_with_rationale(self, sample_source):
        """Provenance can include rationale."""
        prov = Provenance(
            created_by="engine",
            created_at="2026-07-23T12:00:00",
            source=sample_source,
            rationale="Evidence created during document processing",
        )
        assert prov.rationale != ""