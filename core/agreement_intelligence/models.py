"""Universal Agreement Intelligence — Data Models.

Agreement Intelligence models commitments established between two or more parties.
It does not model legal software, contract management, or procurement systems.
It models agreements.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any

from core.journey_semantics import (
    apply_transition as _apply_transition,
    compute_progress_pct as _compute_progress_pct,
    validate_transition as _validate_transition,
)


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _generate_id() -> str:
    import uuid
    return str(uuid.uuid4())


class AgreementStatus(str, Enum):
    DRAFT = "draft"
    PROPOSED = "proposed"
    NEGOTIATING = "negotiating"
    ACCEPTED = "accepted"
    ACTIVE = "active"
    PARTIALLY_FULFILLED = "partially_fulfilled"
    FULFILLED = "fulfilled"
    EXPIRED = "expired"
    RENEWED = "renewed"
    TERMINATED = "terminated"

    @classmethod
    def valid_transitions(cls) -> dict[str, list[str]]:
        return {
            "draft": ["proposed"],
            "proposed": ["negotiating", "accepted", "terminated"],
            "negotiating": ["accepted", "proposed", "terminated"],
            "accepted": ["active", "terminated"],
            "active": ["partially_fulfilled", "fulfilled", "expired", "terminated"],
            "partially_fulfilled": ["fulfilled", "expired", "terminated"],
            "fulfilled": ["expired", "renewed", "terminated"],
            "expired": ["renewed", "terminated"],
            "renewed": ["active", "terminated"],
            "terminated": [],
        }

    @classmethod
    def is_valid_transition(cls, current: str, target: str) -> bool:
        return _validate_transition(current, target, cls.valid_transitions())


class AgreementType(str, Enum):
    EMPLOYMENT = "employment"
    CUSTOMER_PURCHASE = "customer_purchase"
    SUPPLIER_CONTRACT = "supplier_contract"
    RENTAL = "rental"
    SERVICE = "service"
    PARTNERSHIP = "partnership"
    INSURANCE = "insurance"
    LOAN = "loan"
    MEMBERSHIP = "membership"
    SUBSCRIPTION = "subscription"
    MEDICAL_CONSENT = "medical_consent"
    EDUCATIONAL_ADMISSION = "educational_admission"
    GOVERNMENT_PERMIT = "government_permit"
    MARRIAGE_REGISTRATION = "marriage_registration"
    DIGITAL_TERMS = "digital_terms"


class ObligationStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    FULFILLED = "fulfilled"
    BREACHED = "breached"
    WAIVED = "waived"
    RENEGOTIATED = "renegotiated"


class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class Party:
    party_id: str = field(default_factory=_generate_id)
    name: str = ""
    role: str = ""  # buyer, seller, employer, employee, landlord, tenant, etc.
    contact: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {"party_id": self.party_id, "name": self.name, "role": self.role,
                "contact": self.contact, "metadata": dict(self.metadata)}


@dataclass
class Obligation:
    obligation_id: str = field(default_factory=_generate_id)
    description: str = ""
    party_id: str = ""
    status: str = ObligationStatus.PENDING.value
    due_date: str = ""
    fulfilled_date: str | None = None
    value: float = 0.0
    evidence_ids: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {"obligation_id": self.obligation_id, "description": self.description,
                "party_id": self.party_id, "status": self.status, "due_date": self.due_date,
                "fulfilled_date": self.fulfilled_date, "value": self.value,
                "evidence_ids": list(self.evidence_ids), "metadata": dict(self.metadata)}


@dataclass
class Condition:
    condition_id: str = field(default_factory=_generate_id)
    description: str = ""
    is_met: bool = False
    met_date: str | None = None
    evidence_ids: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {"condition_id": self.condition_id, "description": self.description,
                "is_met": self.is_met, "met_date": self.met_date,
                "evidence_ids": list(self.evidence_ids)}


@dataclass
class Milestone:
    milestone_id: str = field(default_factory=_generate_id)
    title: str = ""
    description: str = ""
    due_date: str = ""
    completed_date: str | None = None
    status: str = "pending"
    evidence_ids: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {"milestone_id": self.milestone_id, "title": self.title,
                "description": self.description, "due_date": self.due_date,
                "completed_date": self.completed_date, "status": self.status,
                "evidence_ids": list(self.evidence_ids)}


@dataclass
class Amendment:
    amendment_id: str = field(default_factory=_generate_id)
    title: str = ""
    description: str = ""
    changes: list[dict[str, Any]] = field(default_factory=list)
    status: str = "proposed"
    approved_by: list[str] = field(default_factory=list)
    created_at: str = field(default_factory=_now_iso)

    def to_dict(self) -> dict[str, Any]:
        return {"amendment_id": self.amendment_id, "title": self.title,
                "description": self.description, "changes": list(self.changes),
                "status": self.status, "approved_by": list(self.approved_by),
                "created_at": self.created_at}


@dataclass
class Agreement:
    agreement_id: str = field(default_factory=_generate_id)
    agreement_type: str = AgreementType.SERVICE.value
    status: str = AgreementStatus.DRAFT.value
    title: str = ""
    purpose: str = ""
    parties: list[Party] = field(default_factory=list)
    obligations: list[Obligation] = field(default_factory=list)
    conditions: list[Condition] = field(default_factory=list)
    milestones: list[Milestone] = field(default_factory=list)
    amendments: list[Amendment] = field(default_factory=list)
    financial_commitments: list[dict[str, Any]] = field(default_factory=list)
    documents: list[str] = field(default_factory=list)
    communications: list[str] = field(default_factory=list)
    evidence_ids: list[str] = field(default_factory=list)
    risks: list[dict[str, Any]] = field(default_factory=list)
    terms: str = ""
    rights: list[str] = field(default_factory=list)
    deliverables: list[str] = field(default_factory=list)
    dependencies: list[str] = field(default_factory=list)
    start_date: str = ""
    end_date: str = ""
    renewal_terms: str = ""
    auto_renew: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=_now_iso)
    updated_at: str = field(default_factory=_now_iso)

    @property
    def is_active(self) -> bool:
        return self.status in (AgreementStatus.ACTIVE.value, AgreementStatus.PARTIALLY_FULFILLED.value)

    @property
    def is_terminated(self) -> bool:
        return self.status == AgreementStatus.TERMINATED.value

    @property
    def fulfilment_pct(self) -> float:
        total = len(self.obligations)
        if total == 0:
            return 0.0
        fulfilled = sum(1 for o in self.obligations if o.status in (
            ObligationStatus.FULFILLED.value, ObligationStatus.WAIVED.value))
        return round((fulfilled / total) * 100, 1)

    def transition_to(self, new_status: str) -> bool:
        success, _ = _apply_transition(
            self.status, new_status,
            AgreementStatus.valid_transitions(),
            on_transition=lambda curr, tgt: setattr(self, 'updated_at', _now_iso()),
        )
        if success:
            self.status = new_status
        return success

    def to_dict(self) -> dict[str, Any]:
        return {
            "agreement_id": self.agreement_id,
            "agreement_type": self.agreement_type,
            "status": self.status,
            "title": self.title,
            "purpose": self.purpose,
            "parties": [p.to_dict() for p in self.parties],
            "obligations": [o.to_dict() for o in self.obligations],
            "conditions": [c.to_dict() for c in self.conditions],
            "milestones": [m.to_dict() for m in self.milestones],
            "amendments": [a.to_dict() for a in self.amendments],
            "financial_commitments": list(self.financial_commitments),
            "documents": list(self.documents),
            "communications": list(self.communications),
            "evidence_ids": list(self.evidence_ids),
            "risks": list(self.risks),
            "terms": self.terms,
            "rights": list(self.rights),
            "deliverables": list(self.deliverables),
            "dependencies": list(self.dependencies),
            "start_date": self.start_date,
            "end_date": self.end_date,
            "renewal_terms": self.renewal_terms,
            "auto_renew": self.auto_renew,
            "fulfilment_pct": self.fulfilment_pct,
            "is_active": self.is_active,
            "metadata": dict(self.metadata),
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


@dataclass
class AgreementProfile:
    profile_id: str = field(default_factory=_generate_id)
    owner_id: str = ""
    label: str = ""
    agreements: list[Agreement] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=_now_iso)
    updated_at: str = field(default_factory=_now_iso)

    @property
    def total_agreements(self) -> int:
        return len(self.agreements)

    @property
    def active_agreements(self) -> list[Agreement]:
        return [a for a in self.agreements if a.is_active]

    def to_dict(self) -> dict[str, Any]:
        return {"profile_id": self.profile_id, "owner_id": self.owner_id,
                "label": self.label, "agreements": [a.to_dict() for a in self.agreements],
                "metadata": dict(self.metadata), "created_at": self.created_at,
                "updated_at": self.updated_at, "total_agreements": self.total_agreements,
                "active_count": len(self.active_agreements)}


@dataclass
class AgreementRecommendation:
    rec_id: str = field(default_factory=_generate_id)
    title: str = ""
    description: str = ""
    priority: str = "medium"
    reasoning: str = ""
    confidence: float = 0.0
    obligations_affected: list[str] = field(default_factory=list)
    risks: list[dict[str, Any]] = field(default_factory=list)
    expected_outcome: str = ""
    evidence: list[dict[str, Any]] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    generated_at: str = field(default_factory=_now_iso)

    def to_dict(self) -> dict[str, Any]:
        return {"rec_id": self.rec_id, "title": self.title, "description": self.description,
                "priority": self.priority, "reasoning": self.reasoning,
                "confidence": self.confidence, "obligations_affected": list(self.obligations_affected),
                "risks": list(self.risks), "expected_outcome": self.expected_outcome,
                "evidence": list(self.evidence), "metadata": dict(self.metadata),
                "generated_at": self.generated_at}