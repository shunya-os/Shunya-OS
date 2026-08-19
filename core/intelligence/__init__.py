"""
SHUNYA — Canonical Intelligence Request & Response Envelope.

Gate 2.4: One canonical intelligence contract for all SHUNYA intelligence
operations. Every intelligence request carries tenant/workspace, user context,
company-first evidence, provenance, and explicit fact/inference separation.

The intelligence hierarchy:
    COMPANY/USER CONTEXT FIRST
    → CANONICAL OBJECTS/EVIDENCE/MEMORY
    → DETERMINISTIC COMPUTATION
    → EXTERNAL CURRENT INFORMATION WHEN NEEDED
    → MODEL REASONING WHEN ACTUALLY USEFUL
    → EVIDENCE-BACKED ANSWER
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional


# ═══════════════════════════════════════════════════════════════════
# Knowledge Classification — what the system knows
# ═══════════════════════════════════════════════════════════════════


class KnowledgeStatus(str, Enum):
    """Classification of knowledge status for a claim or answer."""
    FACT = "fact"                     # Supported by canonical record or evidence
    INFERENCE = "inference"           # Derived from facts
    ASSUMPTION = "assumption"         # Required but not proven
    UNKNOWN = "unknown"               # Information unavailable
    RECOMMENDATION = "recommendation" # Proposed action, not a fact
    ERROR = "error"                   # Failed to determine


# ═══════════════════════════════════════════════════════════════════
# Evidence Source — where a fact came from
# ═══════════════════════════════════════════════════════════════════


@dataclass
class EvidenceSource:
    """A single source of evidence for a claim."""
    type: str                               # "company_data" | "external" | "deterministic" | "model"
    source: str                             # Specific source identifier
    timestamp: str = ""                     # When the source was acquired
    confidence: Optional[float] = None      # None = unknown
    detail: str = ""                        # Human-readable description
    url: str = ""                           # External URL if applicable


# ═══════════════════════════════════════════════════════════════════
# Knowledge Claim — a single atomic fact/inference/assumption
# ═══════════════════════════════════════════════════════════════════


@dataclass
class KnowledgeClaim:
    """A single knowledge claim with explicit status and evidence."""
    statement: str
    status: KnowledgeStatus = KnowledgeStatus.UNKNOWN
    confidence: Optional[float] = None          # None = unknown
    sources: list[EvidenceSource] = field(default_factory=list)
    detail: str = ""


# ═══════════════════════════════════════════════════════════════════
# Intelligence Capability — what the request asks for
# ═══════════════════════════════════════════════════════════════════


class IntelligenceCapability(str, Enum):
    EXPLAIN = "explain"                 # "Why is this happening?"
    SUMMARIZE = "summarize"              # "What changed?"
    COMPARE = "compare"                  # "Which option is better?"
    PRIORITIZE = "prioritize"           # "What matters now?"
    RECOMMEND = "recommend"             # "What should we do next?"
    PLAN = "plan"                       # "What is the best path forward?"
    FORECAST = "forecast"               # "What is likely to happen?"
    RESEARCH = "research"               # "What is currently true externally?"
    DATA_ANALYSIS = "data_analysis"     # "What does our data show?"
    GENERAL = "general"                 # General question


# ═══════════════════════════════════════════════════════════════════
# Freshness Requirement
# ═══════════════════════════════════════════════════════════════════


@dataclass
class FreshnessRequirement:
    """How fresh the information needs to be."""
    max_age_seconds: Optional[int] = None   # None = any age is fine
    requires_external_verification: bool = False
    explicit_stale_ok: bool = False         # True if stale data is acceptable


# ═══════════════════════════════════════════════════════════════════
# Intelligence Request — the canonical input
# ═══════════════════════════════════════════════════════════════════


@dataclass
class IntelligenceRequest:
    """Canonical intelligence request — every SHUNYA intelligence operation
    enters through this contract."""
    # Identity and scope
    tenant_id: int = 0
    workspace_id: Optional[int] = None
    actor_id: str = ""
    actor_identity_id: str = ""

    # The question
    question: str = ""
    capability: IntelligenceCapability = IntelligenceCapability.GENERAL
    context_object_id: str = ""           # Current object/user is working on
    context_object_type: str = ""          # Object type for context

    # Freshness
    freshness: FreshnessRequirement = field(default_factory=FreshnessRequirement)

    # Authorization
    authorization_scope: str = "tenant"    # "tenant" | "workspace" | "self"

    # Model controls
    preferred_model: str = ""
    max_tokens: int = 2048
    temperature: float = 0.3

    # Metadata
    request_id: str = ""
    created_at: str = ""

    def __post_init__(self) -> None:
        if not self.request_id:
            import uuid
            self.request_id = f"iq_{uuid.uuid4().hex[:16]}"
        if not self.created_at:
            self.created_at = datetime.now(timezone.utc).isoformat()


# ═══════════════════════════════════════════════════════════════════
# Intelligence Signal — a governed notification
# ═══════════════════════════════════════════════════════════════════


@dataclass
class IntelligenceSignal:
    """A governed intelligence signal (not a fake notification).

    Each signal has reason, evidence, relevance, priority, and a
    suggested next action.
    """
    signal_type: str                       # "change" | "attention" | "risk" | "commitment" | "information" | "pattern" | "opportunity"
    title: str
    description: str
    evidence: list[EvidenceSource] = field(default_factory=list)
    relevance: float = 0.5                # [0, 1]
    priority: str = "normal"              # "critical" | "high" | "normal" | "low"
    suggested_action: str = ""
    suggested_action_payload: dict = field(default_factory=dict)
    knowledge_status: KnowledgeStatus = KnowledgeStatus.INFERENCE
    created_at: str = ""

    def __post_init__(self) -> None:
        if not self.created_at:
            self.created_at = datetime.now(timezone.utc).isoformat()


# ═══════════════════════════════════════════════════════════════════
# Intelligence Response — the canonical output
# ═══════════════════════════════════════════════════════════════════


@dataclass
class IntelligenceResponse:
    """Canonical intelligence response — every SHUNYA intelligence
    operation returns this contract.

    Every claim is explicitly classified as FACT, INFERENCE, ASSUMPTION,
    UNKNOWN, RECOMMENDATION, or ERROR.
    """
    request_id: str = ""
    question: str = ""
    capability: IntelligenceCapability = IntelligenceCapability.GENERAL

    # The answer
    answer: str = ""
    summary: str = ""

    # Knowledge claims — explicit fact/inference/assumption separation
    claims: list[KnowledgeClaim] = field(default_factory=list)

    # Company-first context
    context_used: list[EvidenceSource] = field(default_factory=list)
    external_sources_used: list[EvidenceSource] = field(default_factory=list)

    # Deterministic computation
    deterministic_result: Optional[dict] = None
    deterministic_type: str = ""           # "calculation" | "aggregation" | "filter" | "comparison"

    # Model info
    model_used: str = ""
    provider_used: str = ""
    model_provenance: str = ""             # "free" | "paid" | "local"

    # Freshness
    freshness_verified: bool = False
    freshness_ok: bool = False
    freshness_note: str = ""

    # Error/degraded
    error: Optional[str] = None
    degraded: bool = False

    # Signals
    signals: list[IntelligenceSignal] = field(default_factory=list)

    # Timestamps
    created_at: str = ""
    duration_ms: float = 0.0

    def __post_init__(self) -> None:
        if not self.created_at:
            self.created_at = datetime.now(timezone.utc).isoformat()

    def add_claim(self, statement: str, status: KnowledgeStatus = KnowledgeStatus.UNKNOWN,
                  confidence: Optional[float] = None,
                  sources: Optional[list[EvidenceSource]] = None,
                  detail: str = "") -> None:
        self.claims.append(KnowledgeClaim(
            statement=statement, status=status, confidence=confidence,
            sources=sources or [], detail=detail,
        ))

    def add_signal(self, signal_type: str, title: str, description: str,
                   relevance: float = 0.5, priority: str = "normal",
                   suggested_action: str = "") -> None:
        self.signals.append(IntelligenceSignal(
            signal_type=signal_type, title=title, description=description,
            relevance=relevance, priority=priority,
            suggested_action=suggested_action,
        ))


from core.intelligence.service import IntelligenceService, get_intelligence_service, reset_intelligence_service  # noqa: F401

__all__ = [
    "KnowledgeStatus",
    "EvidenceSource",
    "KnowledgeClaim",
    "IntelligenceCapability",
    "FreshnessRequirement",
    "IntelligenceRequest",
    "IntelligenceSignal",
    "IntelligenceResponse",
    "IntelligenceService",
    "get_intelligence_service",
    "reset_intelligence_service",
]