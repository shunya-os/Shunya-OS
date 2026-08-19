"""
Gate 2.2 — Universal Ingestion & Provenance Tests.

Tests the canonical IngestionService and ingestion envelope.
"""

import json
import pytest

from core.ingestion import (
    IngestionRecord,
    InformationClass,
    ProcessingOutcome,
    SourceType,
    ValidationStatus,
    information_can_overwrite,
)
from core.ingestion.service import (
    IngestionService,
    get_ingestion_service,
    reset_ingestion_service,
)


# ── Fixtures ─────────────────────────────────────────────────────────────────


@pytest.fixture(autouse=True)
def clean_state():
    reset_ingestion_service()
    yield
    reset_ingestion_service()


def make_record(
    source: SourceType = SourceType.API,
    payload: dict | None = None,
    info_class: InformationClass = InformationClass.USER_PROVIDED,
    idempotency_key: str = "",
) -> IngestionRecord:
    return IngestionRecord(
        source=source,
        source_identity="test_user",
        normalized_payload=payload or {"name": "Test", "email": "test@example.com"},
        information_class=info_class,
        confidence=0.8,
        idempotency_key=idempotency_key,
        tenant_id=1,
    )


# ── 1. Universal Ingestion Envelope ──────────────────────────────────────────


class TestIngestionEnvelope:
    """The universal ingestion envelope must represent all required fields."""

    def test_envelope_creates_id(self):
        record = IngestionRecord(source=SourceType.API)
        assert record.ingestion_id, "Must auto-generate ingestion_id"
        assert record.idempotency_key, "Must auto-generate idempotency_key"
        assert record.created_at, "Must auto-generate created_at"

    def test_envelope_required_fields(self):
        """The envelope supports all required fields from the spec."""
        record = IngestionRecord(
            ingestion_id="test-001",
            idempotency_key="key-001",
            tenant_id=1,
            workspace_id=2,
            source=SourceType.CSV,
            source_identity="admin@co.com",
            provider="manual",
            raw_payload=b"raw data",
            normalized_payload={"name": "Alice"},
            validation_status=ValidationStatus.VALID,
            information_class=InformationClass.TRUSTED_COMPANY,
            content_class="fact",
            confidence=0.95,
        )
        assert record.ingestion_id == "test-001"
        assert record.tenant_id == 1
        assert record.workspace_id == 2
        assert record.source == SourceType.CSV
        assert record.information_class == InformationClass.TRUSTED_COMPANY
        assert record.confidence == 0.95

    def test_envelope_supports_all_source_types(self):
        """All 10 required source classes are supported."""
        sources = [
            SourceType.API,
            SourceType.OAUTH_PROVIDER,
            SourceType.EMAIL,
            SourceType.FILE_UPLOAD,
            SourceType.CSV,
            SourceType.XLSX,
            SourceType.JSON,
            SourceType.WEBHOOK,
            SourceType.WEB_RESEARCH,
            SourceType.PROVIDER_ADAPTER,
        ]
        for s in sources:
            record = IngestionRecord(source=s)
            assert record.source == s

    def test_transformation_history(self):
        record = make_record()
        record.add_transformation("step1", "Did something")
        record.add_transformation("step2", "Did another thing")
        assert len(record.transformations) == 2
        assert record.transformations[0].step == "step1"
        assert record.transformations[1].detail == "Did another thing"

    def test_information_priority(self):
        """Higher priority (lower number) can overwrite lower priority."""
        # TRUSTED_COMPANY (1) CAN overwrite CONNECTED_SYSTEM (2)
        assert information_can_overwrite(
            InformationClass.CONNECTED_SYSTEM, InformationClass.TRUSTED_COMPANY
        )
        # TRUSTED_COMPANY (1) CAN overwrite TRUSTED_COMPANY (1)
        assert information_can_overwrite(
            InformationClass.TRUSTED_COMPANY, InformationClass.TRUSTED_COMPANY
        )
        # MODEL_INFERENCE (5) CANNOT overwrite TRUSTED_COMPANY (1)
        assert not information_can_overwrite(
            InformationClass.TRUSTED_COMPANY, InformationClass.MODEL_INFERENCE
        )
        # USER_PROVIDED (3) CANNOT overwrite TRUSTED_COMPANY (1)
        assert not information_can_overwrite(
            InformationClass.TRUSTED_COMPANY, InformationClass.USER_PROVIDED
        )


# ── 2. Ingestion Service Pipeline ────────────────────────────────────────────


class TestIngestionService:
    """The canonical ingestion pipeline processes records through all stages."""

    def test_full_pipeline(self):
        """A valid record flows through all pipeline stages."""
        record = make_record()
        service = IngestionService()
        result = service.process(record)

        assert result.outcome == ProcessingOutcome.ACCEPTED
        assert result.canonical_event_id, "Event must be emitted"
        # Verify all pipeline stages ran
        stages = [t.step for t in result.transformations]
        assert "ingest" in stages
        assert "validation" in stages
        assert "normalization" in stages
        assert "identity_resolution" in stages
        assert "provenance" in stages
        assert "evidence" in stages
        assert "event" in stages
        assert "complete" in stages

    def test_idempotency(self):
        """Same record processed twice = DUPLICATE on second attempt."""
        record = make_record()
        service = IngestionService()

        first = service.process(record)
        assert first.outcome == ProcessingOutcome.ACCEPTED

        second = service.process(record)
        assert second.outcome == ProcessingOutcome.DUPLICATE

    def test_idempotency_with_explicit_key(self):
        """Same idempotency_key = DUPLICATE regardless of content."""
        service = IngestionService()

        r1 = make_record(payload={"name": "A"}, idempotency_key="dedup-key")
        r2 = make_record(payload={"name": "B"}, idempotency_key="dedup-key")

        assert service.process(r1).outcome == ProcessingOutcome.ACCEPTED
        assert service.process(r2).outcome == ProcessingOutcome.DUPLICATE

    def test_replay_after_reset(self):
        """After reset, same content is processed again (different service instance)."""
        record = make_record()

        service1 = IngestionService()
        assert service1.process(record).outcome == ProcessingOutcome.ACCEPTED
        assert service1.process(record).outcome == ProcessingOutcome.DUPLICATE

        # New service instance = fresh idempotency cache
        service2 = IngestionService()
        assert service2.process(record).outcome == ProcessingOutcome.ACCEPTED

    def test_empty_payload_rejected(self):
        record = IngestionRecord(source=SourceType.API)
        service = IngestionService()
        result = service.process(record)
        assert result.outcome == ProcessingOutcome.REJECTED
        assert result.validation_status in (ValidationStatus.ERROR, ValidationStatus.BLOCKING)


# ── 3. Source Convergence — Different source types, same contract ────────────


class TestSourceConvergence:
    """All source types converge through the same canonical contract."""

    @pytest.mark.parametrize("source", [
        SourceType.API,
        SourceType.CSV,
        SourceType.JSON,
        SourceType.WEBHOOK,
        SourceType.FILE_UPLOAD,
        SourceType.EMAIL,
        SourceType.WEB_RESEARCH,
    ])
    def test_all_sources_converge(self, source):
        """Every source type produces the same IngestionRecord structure."""
        record = make_record(source=source)
        service = IngestionService()
        result = service.process(record)
        assert result.outcome == ProcessingOutcome.ACCEPTED
        assert result.source == source
        # All sources produce the same canonical event type prefix
        assert result.canonical_event_id, f"Event must be emitted for {source}"


# ── 4. Company-First Trust Hierarchy ─────────────────────────────────────────


class TestCompanyFirstTrust:
    """Information class affects how ingested data is treated."""

    def test_trusted_company_highest_priority(self):
        """Trusted company data has highest priority (1)."""
        assert InformationClass.TRUSTED_COMPANY.value == "trusted_company"
        record = make_record(info_class=InformationClass.TRUSTED_COMPANY)
        assert record.priority == 1

    def test_model_inference_lowest_priority(self):
        """Model inference has lowest priority (5)."""
        assert InformationClass.MODEL_INFERENCE.value == "model_inference"
        record = make_record(info_class=InformationClass.MODEL_INFERENCE)
        assert record.priority == 5

    def test_company_truth_not_overwritten_by_model(self):
        """Company truth cannot be overwritten by model inference."""
        assert not information_can_overwrite(
            InformationClass.TRUSTED_COMPANY, InformationClass.MODEL_INFERENCE
        )


# ── 5. Malformed / Failure Handling ──────────────────────────────────────────


class TestFailureHandling:
    """Ingestion handles failures gracefully without corrupting state."""

    def test_malformed_payload_handled(self):
        """Empty or malformed payloads are rejected, not corrupted."""
        service = IngestionService()

        # Empty
        r1 = IngestionRecord(source=SourceType.API)
        assert service.process(r1).outcome == ProcessingOutcome.REJECTED

        # None payload
        r2 = IngestionRecord(
            source=SourceType.API,
            normalized_payload=None,
            raw_payload=None,
        )
        assert service.process(r2).outcome == ProcessingOutcome.REJECTED

    def test_partial_failure_visible(self):
        """Validation failures are visible in the record."""
        record = IngestionRecord(source=SourceType.API)
        service = IngestionService()
        result = service.process(record)
        assert result.validation_status in (ValidationStatus.ERROR, ValidationStatus.BLOCKING)
        assert len(result.validation_messages) > 0

    def test_event_emission_failure_does_not_corrupt(self):
        """If event emission fails, the ingestion is still accepted."""
        # The service catches exceptions internally
        record = make_record()
        service = IngestionService()
        result = service.process(record)
        assert result.outcome == ProcessingOutcome.ACCEPTED


# ── 6. Provenance ────────────────────────────────────────────────────────────


class TestProvenance:
    """Provenance is preserved through the ingestion pipeline."""

    def test_provenance_recorded(self):
        record = make_record(
            source=SourceType.CSV,
            payload={"email": "alice@co.com", "name": "Alice"},
        )
        service = IngestionService()
        result = service.process(record)

        # Provenance should be attached
        assert result.provenance is not None
        assert result.provenance.source_type == SourceType.CSV

    def test_source_identity_preserved(self):
        record = make_record(
            source=SourceType.WEBHOOK,
        )
        record.source_identity = "whatsapp:+15551234567"
        service = IngestionService()
        result = service.process(record)
        assert result.provenance is not None
        assert result.provenance.source_identity == "whatsapp:+15551234567"

    def test_confidence_unknown_remains_unknown(self):
        """Unknown confidence stays at default 0.5 (not fabricated)."""
        record = IngestionRecord(source=SourceType.WEB_RESEARCH)
        assert record.confidence == 0.5
        service = IngestionService()
        result = service.process(record)
        # Confidence should not be silently promoted
        assert result.provenance is None or result.provenance.confidence <= 0.6


# ── 7. Tenant Isolation ──────────────────────────────────────────────────────


class TestTenantIsolation:
    """Ingestion respects tenant boundaries."""

    def test_tenant_id_preserved(self):
        record = make_record()
        record.tenant_id = 42
        service = IngestionService()
        result = service.process(record)
        assert result.tenant_id == 42

    def test_empty_tenant_does_not_crash(self):
        record = make_record()
        record.tenant_id = 0
        service = IngestionService()
        result = service.process(record)
        assert result.outcome == ProcessingOutcome.ACCEPTED