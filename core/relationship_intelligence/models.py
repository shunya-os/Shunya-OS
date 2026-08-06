"""Universal Relationship Intelligence — Data Models.

Living Object dataclasses for the universal relationship capability.
Every model has to_dict() for serialization, designed for composition
by domain-specific modules (CRM, HR, Support, etc.) — never embedded in them.

UCP-02 — Universal Relationship Intelligence.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any


# ── Timestamp helper ──────────────────────────────────────────────────────

def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _generate_id() -> str:
    import uuid
    return str(uuid.uuid4())


# ── Relationship Intelligence Types ────────────────────────────────────────

class RelationshipRole(str, Enum):
    """Canonical relationship roles — universal, not domain-specific.

    These are the fundamental types of connection between entities.
    Every domain (CRM, HR, Healthcare, etc.) composes from these.
    """
    CUSTOMER = "customer"
    PROSPECT = "prospect"
    EMPLOYEE = "employee"
    CANDIDATE = "candidate"
    SUPPLIER = "supplier"
    PARTNER = "partner"
    INVESTOR = "investor"
    ADVISOR = "advisor"
    MENTOR = "mentor"
    STUDENT = "student"
    TEACHER = "teacher"
    DOCTOR = "doctor"
    PATIENT = "patient"
    FAMILY = "family"
    FRIEND = "friend"
    GOVERNMENT = "government"
    COMMUNITY = "community"
    ORGANIZATION = "organization"


class TrustLevel(str, Enum):
    """Trust level continuum — from unknown to absolute."""
    UNKNOWN = "unknown"
    LOW = "low"
    CAUTIOUS = "cautious"
    MODERATE = "moderate"
    HIGH = "high"
    ABSOLUTE = "absolute"


class SentimentTrend(str, Enum):
    """Direction of sentiment change over time."""
    IMPROVING = "improving"
    STABLE = "stable"
    DECLINING = "declining"
    VOLATILE = "volatile"
    NEUTRAL = "neutral"


class InteractionType(str, Enum):
    """Universal interaction types — across all domains."""
    MEETING = "meeting"
    CALL = "call"
    EMAIL = "email"
    MESSAGE = "message"
    DOCUMENT_SHARED = "document_shared"
    COMMITMENT_MADE = "commitment_made"
    COMMITMENT_FULFILLED = "commitment_fulfilled"
    COMMITMENT_BROKEN = "commitment_broken"
    JOURNEY_MILESTONE = "journey_milestone"
    CREATIVE_COLLABORATION = "creative_collaboration"
    TRANSACTION = "transaction"
    FEEDBACK = "feedback"
    INTRODUCTION = "introduction"
    OBSERVATION = "observation"


class HealthDimension(str, Enum):
    """Dimensions that compose relationship health."""
    TRUST = "trust"
    SENTIMENT = "sentiment"
    RECENCY = "recency"
    CONSISTENCY = "consistency"
    COMMITMENT_FULFILLMENT = "commitment_fulfillment"
    COMMUNICATION_VOLUME = "communication_volume"
    SHARED_EXPERIENCES = "shared_experiences"
    MUTUAL_BENEFIT = "mutual_benefit"


class CommitmentStatus(str, Enum):
    """Status of a shared commitment in a relationship."""
    PROPOSED = "proposed"
    ACCEPTED = "accepted"
    IN_PROGRESS = "in_progress"
    FULFILLED = "fulfilled"
    PARTIALLY_FULFILLED = "partially_fulfilled"
    BROKEN = "broken"
    RENEGOTIATED = "renegotiated"
    CANCELLED = "cancelled"


# ── Data Models ────────────────────────────────────────────────────────────

@dataclass
class TrustScore:
    """Trust evaluation for a relationship at a point in time.

    Composite of reliability, integrity, competence, and benevolence.
    """
    trust_id: str = field(default_factory=_generate_id)
    relationship_id: str = ""
    level: TrustLevel = TrustLevel.UNKNOWN
    score: float = 0.0  # 0.0 - 1.0
    reliability: float = 0.0
    integrity: float = 0.0
    competence: float = 0.0
    benevolence: float = 0.0
    evidence_refs: list[str] = field(default_factory=list)
    scored_by: str = "system"
    scored_at: str = field(default_factory=_now_iso)
    context: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "trust_id": self.trust_id,
            "relationship_id": self.relationship_id,
            "level": self.level.value,
            "score": self.score,
            "reliability": self.reliability,
            "integrity": self.integrity,
            "competence": self.competence,
            "benevolence": self.benevolence,
            "evidence_refs": list(self.evidence_refs),
            "scored_by": self.scored_by,
            "scored_at": self.scored_at,
            "context": dict(self.context),
        }


@dataclass
class SentimentRecord:
    """Sentiment observation for a relationship at a point in time."""
    sentiment_id: str = field(default_factory=_generate_id)
    relationship_id: str = ""
    score: float = 0.0  # -1.0 (negative) to +1.0 (positive)
    magnitude: float = 0.0  # Emotional intensity 0.0 - 1.0
    source: str = ""  # e.g. "ai_analysis", "human_feedback", "interaction_analysis"
    context: str = ""  # What triggered this sentiment
    metadata: dict[str, Any] = field(default_factory=dict)
    observed_at: str = field(default_factory=_now_iso)

    def to_dict(self) -> dict[str, Any]:
        return {
            "sentiment_id": self.sentiment_id,
            "relationship_id": self.relationship_id,
            "score": self.score,
            "magnitude": self.magnitude,
            "source": self.source,
            "context": self.context,
            "metadata": dict(self.metadata),
            "observed_at": self.observed_at,
        }


@dataclass
class CommunicationRecord:
    """A communication event within a relationship."""
    comm_id: str = field(default_factory=_generate_id)
    relationship_id: str = ""
    channel: str = ""  # email, call, message, meeting, letter, etc.
    direction: str = ""  # outbound, inbound, bidirectional
    subject: str = ""
    summary: str = ""
    sentiment_score: float = 0.0
    duration_minutes: float = 0.0
    participants: list[str] = field(default_factory=list)
    attachments: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    occurred_at: str = field(default_factory=_now_iso)
    recorded_at: str = field(default_factory=_now_iso)

    def to_dict(self) -> dict[str, Any]:
        return {
            "comm_id": self.comm_id,
            "relationship_id": self.relationship_id,
            "channel": self.channel,
            "direction": self.direction,
            "subject": self.subject,
            "summary": self.summary,
            "sentiment_score": self.sentiment_score,
            "duration_minutes": self.duration_minutes,
            "participants": list(self.participants),
            "attachments": list(self.attachments),
            "metadata": dict(self.metadata),
            "occurred_at": self.occurred_at,
            "recorded_at": self.recorded_at,
        }


@dataclass
class InteractionRecord:
    """An interaction within a relationship — generic event record."""
    interaction_id: str = field(default_factory=_generate_id)
    relationship_id: str = ""
    interaction_type: str = InteractionType.OBSERVATION.value
    description: str = ""
    outcome: str = ""
    value: str = ""  # qualitative or quantitative value
    entities_involved: list[str] = field(default_factory=list)
    evidence_ids: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    occurred_at: str = field(default_factory=_now_iso)

    def to_dict(self) -> dict[str, Any]:
        return {
            "interaction_id": self.interaction_id,
            "relationship_id": self.relationship_id,
            "interaction_type": self.interaction_type,
            "description": self.description,
            "outcome": self.outcome,
            "value": self.value,
            "entities_involved": list(self.entities_involved),
            "evidence_ids": list(self.evidence_ids),
            "metadata": dict(self.metadata),
            "occurred_at": self.occurred_at,
        }


@dataclass
class SharedJourney:
    """A phase or milestone shared between entities."""
    journey_id: str = field(default_factory=_generate_id)
    relationship_id: str = ""
    name: str = ""
    phase: str = ""  # e.g. "discovery", "evaluation", "onboarding", "growth", "mature"
    description: str = ""
    milestones: list[dict[str, Any]] = field(default_factory=list)
    started_at: str = ""
    completed_at: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "journey_id": self.journey_id,
            "relationship_id": self.relationship_id,
            "name": self.name,
            "phase": self.phase,
            "description": self.description,
            "milestones": list(self.milestones),
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "metadata": dict(self.metadata),
        }


@dataclass
class SharedDocument:
    """A document co-created or shared within a relationship."""
    doc_id: str = field(default_factory=_generate_id)
    relationship_id: str = ""
    title: str = ""
    doc_type: str = ""  # contract, proposal, report, note, etc.
    url: str = ""
    shared_by: str = ""
    shared_with: list[str] = field(default_factory=list)
    version: int = 1
    metadata: dict[str, Any] = field(default_factory=dict)
    shared_at: str = field(default_factory=_now_iso)

    def to_dict(self) -> dict[str, Any]:
        return {
            "doc_id": self.doc_id,
            "relationship_id": self.relationship_id,
            "title": self.title,
            "doc_type": self.doc_type,
            "url": self.url,
            "shared_by": self.shared_by,
            "shared_with": list(self.shared_with),
            "version": self.version,
            "metadata": dict(self.metadata),
            "shared_at": self.shared_at,
        }


@dataclass
class SharedCreativeAsset:
    """A creative work co-created or shared within a relationship."""
    asset_id: str = field(default_factory=_generate_id)
    relationship_id: str = ""
    title: str = ""
    asset_type: str = ""  # design, copy, video, music, code, etc.
    url: str = ""
    contributors: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=_now_iso)

    def to_dict(self) -> dict[str, Any]:
        return {
            "asset_id": self.asset_id,
            "relationship_id": self.relationship_id,
            "title": self.title,
            "asset_type": self.asset_type,
            "url": self.url,
            "contributors": list(self.contributors),
            "metadata": dict(self.metadata),
            "created_at": self.created_at,
        }


@dataclass
class SharedCommitment:
    """A promise, agreement, or obligation within a relationship."""
    commitment_id: str = field(default_factory=_generate_id)
    relationship_id: str = ""
    title: str = ""
    description: str = ""
    commitment_type: str = ""  # agreement, promise, goal, obligation, SLA
    status: str = CommitmentStatus.PROPOSED.value
    due_date: str | None = None
    fulfilled_date: str | None = None
    value: str = ""
    parties: list[str] = field(default_factory=list)
    evidence_ids: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=_now_iso)
    updated_at: str = field(default_factory=_now_iso)

    def to_dict(self) -> dict[str, Any]:
        return {
            "commitment_id": self.commitment_id,
            "relationship_id": self.relationship_id,
            "title": self.title,
            "description": self.description,
            "commitment_type": self.commitment_type,
            "status": self.status,
            "due_date": self.due_date,
            "fulfilled_date": self.fulfilled_date,
            "value": self.value,
            "parties": list(self.parties),
            "evidence_ids": list(self.evidence_ids),
            "metadata": dict(self.metadata),
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


@dataclass
class RelationshipHealth:
    """Composite health assessment for a relationship."""
    health_id: str = field(default_factory=_generate_id)
    relationship_id: str = ""
    overall_score: float = 0.0  # 0.0 - 1.0
    dimensions: dict[str, float] = field(default_factory=dict)
    trend: str = SentimentTrend.NEUTRAL.value
    risk_level: str = "low"  # low, medium, high, critical
    last_assessed: str = field(default_factory=_now_iso)
    next_review: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "health_id": self.health_id,
            "relationship_id": self.relationship_id,
            "overall_score": self.overall_score,
            "dimensions": dict(self.dimensions),
            "trend": self.trend,
            "risk_level": self.risk_level,
            "last_assessed": self.last_assessed,
            "next_review": self.next_review,
            "metadata": dict(self.metadata),
        }


@dataclass
class Insight:
    """AI-generated insight about a relationship."""
    insight_id: str = field(default_factory=_generate_id)
    relationship_id: str = ""
    category: str = ""  # pattern, risk, opportunity, observation, alert
    title: str = ""
    description: str = ""
    evidence: list[str] = field(default_factory=list)
    confidence: float = 0.0  # 0.0 - 1.0
    actionable: bool = False
    action_suggestion: str = ""
    generated_by: str = "system"
    generated_at: str = field(default_factory=_now_iso)

    def to_dict(self) -> dict[str, Any]:
        return {
            "insight_id": self.insight_id,
            "relationship_id": self.relationship_id,
            "category": self.category,
            "title": self.title,
            "description": self.description,
            "evidence": list(self.evidence),
            "confidence": self.confidence,
            "actionable": self.actionable,
            "action_suggestion": self.action_suggestion,
            "generated_by": self.generated_by,
            "generated_at": self.generated_at,
        }


@dataclass
class Recommendation:
    """An action recommendation to improve or maintain a relationship."""
    recommendation_id: str = field(default_factory=_generate_id)
    relationship_id: str = ""
    priority: str = "medium"  # critical, high, medium, low
    category: str = ""  # reconnect, fulfill, acknowledge, align, grow
    title: str = ""
    description: str = ""
    expected_impact: str = ""
    effort: str = "medium"  # low, medium, high
    due_by: str | None = None
    is_implemented: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)
    generated_at: str = field(default_factory=_now_iso)

    def to_dict(self) -> dict[str, Any]:
        return {
            "recommendation_id": self.recommendation_id,
            "relationship_id": self.relationship_id,
            "priority": self.priority,
            "category": self.category,
            "title": self.title,
            "description": self.description,
            "expected_impact": self.expected_impact,
            "effort": self.effort,
            "due_by": self.due_by,
            "is_implemented": self.is_implemented,
            "metadata": dict(self.metadata),
            "generated_at": self.generated_at,
        }


@dataclass
class RelationshipProfile:
    """Complete intelligence profile for a relationship between two entities.

    This is the primary accessor — the living intelligence for a relationship.
    """
    profile_id: str = field(default_factory=_generate_id)
    source_id: str = ""
    target_id: str = ""
    role: str = RelationshipRole.CUSTOMER.value
    label: str = ""
    trust: TrustScore | None = None
    sentiment_history: list[SentimentRecord] = field(default_factory=list)
    communications: list[CommunicationRecord] = field(default_factory=list)
    interactions: list[InteractionRecord] = field(default_factory=list)
    journeys: list[SharedJourney] = field(default_factory=list)
    documents: list[SharedDocument] = field(default_factory=list)
    creative_assets: list[SharedCreativeAsset] = field(default_factory=list)
    commitments: list[SharedCommitment] = field(default_factory=list)
    health: RelationshipHealth | None = None
    insights: list[Insight] = field(default_factory=list)
    recommendations: list[Recommendation] = field(default_factory=list)
    created_at: str = field(default_factory=_now_iso)
    updated_at: str = field(default_factory=_now_iso)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "profile_id": self.profile_id,
            "source_id": self.source_id,
            "target_id": self.target_id,
            "role": self.role,
            "label": self.label,
            "trust": self.trust.to_dict() if self.trust else None,
            "sentiment_history": [s.to_dict() for s in self.sentiment_history],
            "communications": [c.to_dict() for c in self.communications],
            "interactions": [i.to_dict() for i in self.interactions],
            "journeys": [j.to_dict() for j in self.journeys],
            "documents": [d.to_dict() for d in self.documents],
            "creative_assets": [a.to_dict() for a in self.creative_assets],
            "commitments": [c.to_dict() for c in self.commitments],
            "health": self.health.to_dict() if self.health else None,
            "insights": [i.to_dict() for i in self.insights],
            "recommendations": [r.to_dict() for r in self.recommendations],
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "metadata": dict(self.metadata),
        }

    @property
    def current_sentiment(self) -> SentimentRecord | None:
        """Return the most recent sentiment observation."""
        if not self.sentiment_history:
            return None
        return sorted(self.sentiment_history, key=lambda s: s.observed_at, reverse=True)[0]

    @property
    def active_commitments(self) -> list[SharedCommitment]:
        """Return commitments that are still in progress or accepted."""
        active_stati = {
            CommitmentStatus.ACCEPTED.value,
            CommitmentStatus.IN_PROGRESS.value,
        }
        return [c for c in self.commitments if c.status in active_stati]

    @property
    def commitment_fulfillment_rate(self) -> float:
        """Fraction of fulfilled vs total concluded commitments."""
        concluded = [
            c for c in self.commitments
            if c.status in (
                CommitmentStatus.FULFILLED.value,
                CommitmentStatus.PARTIALLY_FULFILLED.value,
                CommitmentStatus.BROKEN.value,
                CommitmentStatus.CANCELLED.value,
            )
        ]
        if not concluded:
            return 1.0
        fulfilled = sum(1 for c in concluded if c.status == CommitmentStatus.FULFILLED.value)
        return fulfilled / len(concluded)
