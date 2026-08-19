"""
SHUNYA — Universal Ingestion Envelope.

Gate 2.2: One canonical source-neutral ingestion contract for all
external information entering the SHUNYA truth architecture.

The source may differ. The truth architecture must converge.

Every production ingestion path produces an IngestionRecord that
flows through: Ingress → Validation → Normalization → Identity
Resolution → Provenance → Event (where applicable) → Memory.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional


# ═══════════════════════════════════════════════════════════════════
# Source Types — classification of where the information came from
# ═══════════════════════════════════════════════════════════════════


class SourceType(str, Enum):
    API = "api"                     # Programmatic API call
    OAUTH_PROVIDER = "oauth"        # OAuth provider (Gmail, Google, etc.)
    EMAIL = "email"                 # Email message
    FILE_UPLOAD = "file_upload"     # Uploaded file (PDF, text, image)
    CSV = "csv"                     # CSV structured import
    XLSX = "xlsx"                   # Excel structured import
    JSON = "json"                   # JSON structured import
    WEBHOOK = "webhook"             # Webhook callback
    WEB_RESEARCH = "web_research"   # External web research/scrape
    PROVIDER_ADAPTER = "provider"   # Future provider adapter


# ═══════════════════════════════════════════════════════════════════
# Validation Status
# ═══════════════════════════════════════════════════════════════════


class ValidationStatus(str, Enum):
    PENDING = "pending"             # Awaiting validation
    VALID = "valid"                 # Passed validation
    WARNING = "warning"             # Passed with warnings
    ERROR = "error"                 # Failed validation
    BLOCKING = "blocking"           # Fatal, cannot proceed


# ═══════════════════════════════════════════════════════════════════
# Processing Outcome
# ═══════════════════════════════════════════════════════════════════


class ProcessingOutcome(str, Enum):
    ACCEPTED = "accepted"           # Fully processed and stored
    DUPLICATE = "duplicate"         # Duplicate of existing data
    PARTIAL = "partial"             # Partially processed
    ERROR = "error"                 # Processing error
    REJECTED = "rejected"           # Rejected by governance
    PENDING = "pending"             # Awaiting further processing


# ═══════════════════════════════════════════════════════════════════
# Information Classification (Company-First Trust Hierarchy)
# ═══════════════════════════════════════════════════════════════════


class InformationClass(str, Enum):
    """Information classification per the Gate 2.1 company-first hierarchy.

    This governs how ingested information interacts with existing truth.
    Higher-priority classes can only be overwritten by equal or higher
    priority information.
    """
    TRUSTED_COMPANY = "trusted_company"       # Priority 1
    CONNECTED_SYSTEM = "connected_system"      # Priority 2
    USER_PROVIDED = "user_provided"            # Priority 3
    VERIFIED_EXTERNAL = "verified_external"    # Priority 4
    MODEL_INFERENCE = "model_inference"        # Priority 5


_INFORMATION_PRIORITY: dict[InformationClass, int] = {
    InformationClass.TRUSTED_COMPANY: 1,
    InformationClass.CONNECTED_SYSTEM: 2,
    InformationClass.USER_PROVIDED: 3,
    InformationClass.VERIFIED_EXTERNAL: 4,
    InformationClass.MODEL_INFERENCE: 5,
}


def information_can_overwrite(
    existing: InformationClass,
    incoming: InformationClass,
) -> bool:
    """Check if incoming information can overwrite existing information.

    Returns True only if incoming has equal or higher priority (lower number).
    """
    return _INFORMATION_PRIORITY[incoming] <= _INFORMATION_PRIORITY[existing]


# ═══════════════════════════════════════════════════════════════════
# Content Classification — what semantic type the content is
# ═══════════════════════════════════════════════════════════════════


class ContentClass(str, Enum):
    FACT = "fact"                   # Verified company truth
    INFERENCE = "inference"         # Derived from existing data
    RECOMMENDATION = "recommendation"  # Suggested action
    DRAFT = "draft"                 # Unverified, in-progress
    ACTION = "action"               # Committed action/decision
    UNKNOWN = "unknown"             # Not yet classified


# ═══════════════════════════════════════════════════════════════════
# Provenance — complete source tracking
# ═══════════════════════════════════════════════════════════════════


@dataclass
class Provenance:
    """Complete source provenance for a single ingestion event.

    Every production ingestion path must preserve this.
    Unknown values remain unknown — never fabricate.
    """
    source_type: SourceType
    source_identity: str                    # Who sent/provided the data
    provider: str = ""                      # Provider name (Gmail, WhatsApp, etc.)
    external_reference: str = ""            # External ID (message ID, file ID, etc.)
    acquisition_timestamp: str = ""         # When SHUNYA received it
    observed_timestamp: str = ""            # When the event actually occurred
    actor: str = ""                         # System actor that performed ingestion
    raw_payload_ref: str = ""               # Reference to raw payload (file path, blob key)
    source_reliability: float = 0.5         # [0, 1] — 0.5 = unknown
    confidence: float = 0.5                 # [0, 1] — 0.5 = unknown
    transformation_history: list[str] = field(default_factory=list)


# ═══════════════════════════════════════════════════════════════════
# Transformation — a single step in processing
# ═══════════════════════════════════════════════════════════════════


@dataclass
class Transformation:
    """A single transformation step applied during ingestion."""
    step: str
    timestamp: str = ""
    detail: str = ""

    def __post_init__(self) -> None:
        if not self.timestamp:
            self.timestamp = datetime.now(timezone.utc).isoformat()


# ═══════════════════════════════════════════════════════════════════
# Ingestion Record — the universal envelope
# ═══════════════════════════════════════════════════════════════════


@dataclass
class IngestionRecord:
    """Universal ingestion envelope — produced by every ingestion path.

    This is the canonical container for all information entering SHUNYA.
    Every source adapter produces one of these and submits it to the
    IngestionService.
    """
    ingestion_id: str = ""
    idempotency_key: str = ""
    tenant_id: int = 0
    workspace_id: Optional[int] = None

    # Source identification
    source: SourceType = SourceType.API
    source_identity: str = ""
    provider: str = ""

    # Payload
    raw_payload: Any = None
    raw_payload_ref: str = ""
    normalized_payload: dict[str, Any] = field(default_factory=dict)

    # Processing
    validation_status: ValidationStatus = ValidationStatus.PENDING
    validation_messages: list[dict] = field(default_factory=list)
    transformations: list[Transformation] = field(default_factory=list)
    provenance: Optional[Provenance] = None

    # Identity resolution
    resolved_identity_id: str = ""
    resolved_person_id: str = ""

    # Classification
    information_class: InformationClass = InformationClass.MODEL_INFERENCE
    content_class: ContentClass = ContentClass.UNKNOWN
    confidence: float = 0.5

    # Outcome
    outcome: ProcessingOutcome = ProcessingOutcome.PENDING
    outcome_detail: str = ""
    error: Optional[str] = None

    # Event
    canonical_event_id: str = ""

    # Timestamps
    created_at: str = ""

    def __post_init__(self) -> None:
        if not self.created_at:
            self.created_at = datetime.now(timezone.utc).isoformat()
        if not self.ingestion_id:
            import uuid
            self.ingestion_id = str(uuid.uuid4())
        if not self.idempotency_key:
            self.idempotency_key = self.ingestion_id

    def add_transformation(self, step: str, detail: str = "") -> None:
        self.transformations.append(Transformation(step=step, detail=detail))

    @property
    def priority(self) -> int:
        """Numeric priority per company-first hierarchy (1=highest)."""
        return _INFORMATION_PRIORITY.get(self.information_class, 5)


__all__ = [
    "SourceType",
    "ValidationStatus",
    "ProcessingOutcome",
    "InformationClass",
    "ContentClass",
    "Provenance",
    "Transformation",
    "IngestionRecord",
    "information_can_overwrite",
]