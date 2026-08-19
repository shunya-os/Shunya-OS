"""
SHUNYA — Universal Ingestion Service.

Gate 2.2: The canonical pipeline through which all external information
enters the SHUNYA truth architecture.

Pipeline:
    Ingress → Idempotency → Validation → Normalization →
    Identity Resolution → Provenance → Evidence →
    Canonical Event → Memory

Not every source must use every step. Every source must use the same
contract (IngestionRecord).
"""

from __future__ import annotations

import hashlib
import json
import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Optional

from core.ingestion import (
    IngestionRecord,
    InformationClass,
    ProcessingOutcome,
    Provenance,
    SourceType,
    ValidationStatus,
    information_can_overwrite,
)

logger = logging.getLogger(__name__)


class IngestionService:
    """Canonical ingestion pipeline — processes IngestionRecord through
    validation, identity resolution, provenance, evidence, and event emission.

    Usage:
        service = IngestionService()
        record = IngestionRecord(
            source=SourceType.CSV,
            source_identity="user@company.com",
            normalized_payload={"name": "Alice", "email": "alice@co.com"},
            information_class=InformationClass.USER_PROVIDED,
        )
        result = service.process(record)
    """

    def __init__(self) -> None:
        self._idempotency_cache: dict[str, str] = {}  # key → outcome

    # ── Main entry point ──────────────────────────────────────────────

    def process(self, record: IngestionRecord) -> IngestionRecord:
        """Process an ingestion record through the full pipeline."""
        record.add_transformation("ingest", "Ingestion started")

        # 1. Idempotency check
        if self._is_duplicate(record):
            record.outcome = ProcessingOutcome.DUPLICATE
            record.outcome_detail = "Duplicate — skipped"
            record.add_transformation("idempotency", "Duplicate detected, skipped")
            return record

        # 2. Validation
        record = self._validate(record)
        if record.validation_status in (ValidationStatus.ERROR, ValidationStatus.BLOCKING):
            record.outcome = ProcessingOutcome.REJECTED
            record.outcome_detail = "Validation failed"
            record.add_transformation("validation", f"Failed: {record.validation_status}")
            self._record_idempotency(record)
            return record

        record.add_transformation("validation", "Passed")

        # 3. Normalization
        record = self._normalize(record)
        record.add_transformation("normalization", "Applied")

        # 4. Identity resolution
        record = self._resolve_identity(record)
        record.add_transformation("identity_resolution",
            f"Resolved to person={record.resolved_person_id}")

        # 5. Provenance
        record = self._record_provenance(record)
        record.add_transformation("provenance", "Recorded")

        # 6. Evidence
        record = self._record_evidence(record)
        record.add_transformation("evidence", "Recorded")

        # 7. Canonical event
        record = self._emit_event(record)
        record.add_transformation("event", f"Emitted event={record.canonical_event_id}")

        # 8. Outcome
        record.outcome = ProcessingOutcome.ACCEPTED
        record.outcome_detail = "Ingested successfully"
        self._record_idempotency(record)
        record.add_transformation("complete", "Ingestion complete")

        return record

    # ── Idempotency ───────────────────────────────────────────────────

    def _idempotency_key(self, record: IngestionRecord) -> str:
        """Generate deterministic idempotency key."""
        # Use explicit key if provided, otherwise derive from payload
        if record.idempotency_key and record.idempotency_key != record.ingestion_id:
            return f"ingest:{record.tenant_id}:{record.idempotency_key}"
        payload_str = json.dumps(record.normalized_payload, sort_keys=True, default=str)
        content_hash = hashlib.sha256(payload_str.encode()).hexdigest()[:16]
        return f"ingest:{record.tenant_id}:{record.source.value}:{content_hash}"

    def _is_duplicate(self, record: IngestionRecord) -> bool:
        """Check if this ingestion has already been processed."""
        key = self._idempotency_key(record)
        return key in self._idempotency_cache

    def _record_idempotency(self, record: IngestionRecord) -> None:
        key = self._idempotency_key(record)
        self._idempotency_cache[key] = record.outcome.value

    # ── Validation ────────────────────────────────────────────────────

    def _validate(self, record: IngestionRecord) -> IngestionRecord:
        """Validate the ingestion record. Override in subclasses for
        source-specific validation."""
        if not record.normalized_payload and record.raw_payload is None:
            record.validation_status = ValidationStatus.BLOCKING
            record.validation_messages.append({
                "severity": "blocking",
                "message": "No payload provided",
            })
        else:
            record.validation_status = ValidationStatus.VALID
        return record

    # ── Normalization ─────────────────────────────────────────────────

    def _normalize(self, record: IngestionRecord) -> IngestionRecord:
        """Normalize the payload. Override in subclasses for source-specific
        normalization."""
        # Basic field normalization
        payload = {}
        for k, v in (record.normalized_payload or {}).items():
            if isinstance(v, str):
                payload[k] = v.strip()
            else:
                payload[k] = v
        record.normalized_payload = payload
        return record

    # ── Identity Resolution ───────────────────────────────────────────

    def _resolve_identity(self, record: IngestionRecord) -> IngestionRecord:
        """Resolve identity from the ingestion record using the canonical
        identity path."""
        try:
            from core.identity.normalizers import normalize_email, normalize_phone

            payload = record.normalized_payload or {}
            email = normalize_email(payload.get("email", ""))
            phone = normalize_phone(payload.get("phone", ""))

            if email or phone:
                # Use the legacy IdentityResolver for backward compatibility
                from app import db
                from app.shunya.identity import IdentityResolver
                resolver = IdentityResolver(session=db.session)

                if email:
                    result = resolver.resolve_by_email(email, record.tenant_id)
                    if result.status == "MATCHED" and hasattr(result, "person"):
                        record.resolved_person_id = str(result.person.id)
                        if hasattr(result.person, "identity_id"):
                            record.resolved_identity_id = result.person.identity_id

                if not record.resolved_person_id and phone:
                    result = resolver.resolve_by_phone(phone, record.tenant_id)
                    if result.status == "MATCHED" and hasattr(result, "person"):
                        record.resolved_person_id = str(result.person.id)
                        if hasattr(result.person, "identity_id"):
                            record.resolved_identity_id = result.person.identity_id
        except Exception as e:
            logger.warning("Identity resolution failed (non-blocking): %s", e)
            # Non-blocking — identity resolution failure is advisory
        return record

    # ── Provenance ────────────────────────────────────────────────────

    def _record_provenance(self, record: IngestionRecord) -> IngestionRecord:
        """Record provenance for the ingestion."""
        if record.provenance is None:
            record.provenance = Provenance(
                source_type=record.source,
                source_identity=record.source_identity,
                provider=record.provider,
                acquisition_timestamp=datetime.now(timezone.utc).isoformat(),
                confidence=record.confidence,         # None = unknown, NEVER fabricated
                source_reliability=record.confidence,  # None = unknown, NEVER fabricated
            )
        return record

    # ── Evidence ──────────────────────────────────────────────────────

    def _record_evidence(self, record: IngestionRecord) -> IngestionRecord:
        """Record evidence through the EvidenceEngine."""
        try:
            from core.evidence.engine import EvidenceEngine
            from core.evidence.models import EvidenceDirection, EvidenceType

            engine = EvidenceEngine()
            # Map InformationClass to class-level reliability (architectural constant)
            reliability_map = {
                InformationClass.TRUSTED_COMPANY: 1.0,
                InformationClass.CONNECTED_SYSTEM: 0.95,
                InformationClass.USER_PROVIDED: 0.8,
                InformationClass.VERIFIED_EXTERNAL: 0.6,
                InformationClass.MODEL_INFERENCE: 0.3,
            }
            class_reliability = reliability_map.get(record.information_class, 0.5)

            # Build metadata — preserve the distinction between unknown and explicit 0.5
            evidence_metadata = {
                "ingestion_id": record.ingestion_id,
                "source_type": record.source.value,
                "provider": record.provider,
                "information_class": record.information_class.value,
                "tenant_id": record.tenant_id,
                "confidence_unknown": record.confidence is None,
                "source_confidence": record.confidence,  # None = unknown
            }

            evidence = engine.create_evidence(
                object_id=record.resolved_person_id or record.ingestion_id,
                evidence_type=EvidenceType.RECORD,
                statement=json.dumps(record.normalized_payload, default=str)[:500],
                source=record.source.value,
                direction=EvidenceDirection.SUPPORTING,
                source_reliability=class_reliability,
                metadata=evidence_metadata,
            )
            record.add_transformation("evidence", f"evidence_id={evidence.evidence_id}")
        except Exception as e:
            logger.warning("Evidence recording failed (non-blocking): %s", e)
        return record

    # ── Canonical Event ───────────────────────────────────────────────

    def _emit_event(self, record: IngestionRecord) -> IngestionRecord:
        """Emit canonical event through the EventBus."""
        try:
            from app.shunya.infrastructure.event_bus import CanonicalEvent, get_event_bus

            event = CanonicalEvent(
                event_type=f"ingestion:{record.source.value}",
                tenant_id=record.tenant_id,
                workspace_id=record.workspace_id,
                actor_id=record.source_identity,
                actor_type="ingestion",
                actor_name=record.provider or record.source.value,
                object_id=record.resolved_person_id or record.ingestion_id,
                object_type="ingestion",
                payload={
                    "ingestion_id": record.ingestion_id,
                    "source_type": record.source.value,
                    "information_class": record.information_class.value,
                    "outcome": record.outcome.value,
                    "person_id": record.resolved_person_id,
                    "confidence_unknown": record.confidence is None,
                    "confidence": record.confidence,  # None = unknown, stays null in JSON
                },
                confidence=record.confidence if record.confidence is not None else 0.0,
            )
            event_id = get_event_bus().publish(event)
            record.canonical_event_id = event_id
        except Exception as e:
            logger.warning("Event emission failed (non-blocking): %s", e)
        return record


# ── Module-level convenience ──────────────────────────────────────────

_service: Optional[IngestionService] = None


def get_ingestion_service() -> IngestionService:
    global _service
    if _service is None:
        _service = IngestionService()
    return _service


def reset_ingestion_service() -> None:
    global _service
    _service = None


__all__ = [
    "IngestionService",
    "get_ingestion_service",
    "reset_ingestion_service",
]