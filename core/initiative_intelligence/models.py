"""Universal Initiative Intelligence — Data Models.

Initiative Intelligence models every coordinated effort undertaken by
individuals or organizations to achieve an intended outcome over time.

It does not model project management software, task management, or
portfolio management. It models Initiatives.

UCP-08 — Universal Initiative Intelligence.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any

from core.journey_semantics import (
    Milestone as JourneyMilestone,
    compute_progress_pct as _j_progress,
    find_delayed_milestones as _j_delayed,
    find_blocked_milestones as _j_blocked,
    MilestoneStatus as JourneyMilestoneStatus,
)


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
def _generate_id() -> str:
    import uuid; return str(uuid.uuid4())


class InitiativeType(str, Enum):
    COMPANY_LAUNCH = "company_launch"
    PRODUCT_LAUNCH = "product_launch"
    PERSONAL_GOAL = "personal_goal"
    RESEARCH = "research"
    CONSTRUCTION = "construction"
    MARKETING_CAMPAIGN = "marketing_campaign"
    EVENT = "event"
    WEDDING = "wedding"
    GOVERNMENT_PROGRAMME = "government_programme"
    NGO_MISSION = "ngo_mission"
    ACADEMIC = "academic"
    SOFTWARE_DEVELOPMENT = "software_development"


class InitiativeStatus(str, Enum):
    IDEATION = "ideation"
    PLANNING = "planning"
    APPROVED = "approved"
    IN_PROGRESS = "in_progress"
    ON_HOLD = "on_hold"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class MilestoneStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    DELAYED = "delayed"
    BLOCKED = "blocked"
    CANCELLED = "cancelled"


class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class Participant:
    participant_id: str = field(default_factory=_generate_id)
    name: str = ""
    role: str = ""
    contact: str = ""
    def to_dict(self) -> dict[str, Any]:
        return {"participant_id": self.participant_id, "name": self.name,
                "role": self.role, "contact": self.contact}


@dataclass
class InitiativeMilestone:
    milestone_id: str = field(default_factory=_generate_id)
    title: str = ""
    description: str = ""
    status: str = MilestoneStatus.PENDING.value
    due_date: str = ""
    completed_date: str | None = None
    dependencies: list[str] = field(default_factory=list)
    evidence_ids: list[str] = field(default_factory=list)
    def to_dict(self) -> dict[str, Any]:
        return {"milestone_id": self.milestone_id, "title": self.title,
                "description": self.description, "status": self.status,
                "due_date": self.due_date, "completed_date": self.completed_date,
                "dependencies": list(self.dependencies),
                "evidence_ids": list(self.evidence_ids)}


@dataclass
class InitiativeConstraint:
    constraint_id: str = field(default_factory=_generate_id)
    description: str = ""
    constraint_type: str = "budget"
    max_value: float = 0.0
    is_hard: bool = True
    def to_dict(self) -> dict[str, Any]:
        return {"constraint_id": self.constraint_id, "description": self.description,
                "constraint_type": self.constraint_type, "max_value": self.max_value,
                "is_hard": self.is_hard}


@dataclass
class InitiativeRisk:
    risk_id: str = field(default_factory=_generate_id)
    description: str = ""
    level: str = RiskLevel.MEDIUM.value
    probability: float = 0.5
    impact: str = ""
    mitigation: str = ""
    owner: str = ""
    def to_dict(self) -> dict[str, Any]:
        return {"risk_id": self.risk_id, "description": self.description,
                "level": self.level, "probability": self.probability,
                "impact": self.impact, "mitigation": self.mitigation, "owner": self.owner}


@dataclass
class Initiative:
    initiative_id: str = field(default_factory=_generate_id)
    initiative_type: str = InitiativeType.PERSONAL_GOAL.value
    status: str = InitiativeStatus.IDEATION.value
    title: str = ""
    purpose: str = ""
    intended_outcome: str = ""
    scope: str = ""
    participants: list[Participant] = field(default_factory=list)
    stakeholders: list[str] = field(default_factory=list)
    milestones: list[InitiativeMilestone] = field(default_factory=list)
    dependencies: list[str] = field(default_factory=list)
    asset_ids: list[str] = field(default_factory=list)
    agreement_ids: list[str] = field(default_factory=list)
    financial_commitments: list[dict[str, Any]] = field(default_factory=list)
    knowledge_ids: list[str] = field(default_factory=list)
    decision_ids: list[str] = field(default_factory=list)
    communications: list[str] = field(default_factory=list)
    documents: list[str] = field(default_factory=list)
    risks: list[InitiativeRisk] = field(default_factory=list)
    constraints: list[InitiativeConstraint] = field(default_factory=list)
    opportunities: list[str] = field(default_factory=list)
    evidence_ids: list[str] = field(default_factory=list)
    completion_criteria: list[str] = field(default_factory=list)
    timeline: str = ""
    reality_changes: list[dict[str, Any]] = field(default_factory=list)
    budget: float = 0.0
    budget_spent: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=_now_iso)
    updated_at: str = field(default_factory=_now_iso)

    @property
    def progress_pct(self) -> float:
        return _j_progress(self.milestones)

    @property
    def is_active(self) -> bool:
        return self.status in (InitiativeStatus.IN_PROGRESS.value, InitiativeStatus.APPROVED.value)

    @property
    def budget_utilization_pct(self) -> float:
        if self.budget == 0:
            return 0.0
        return round((self.budget_spent / self.budget) * 100, 1)

    @property
    def delayed_milestones(self) -> list[InitiativeMilestone]:
        return _j_delayed(self.milestones)

    @property
    def blocked_milestones(self) -> list[InitiativeMilestone]:
        return _j_blocked(self.milestones)

    def to_dict(self) -> dict[str, Any]:
        return {
            "initiative_id": self.initiative_id, "initiative_type": self.initiative_type,
            "status": self.status, "title": self.title, "purpose": self.purpose,
            "intended_outcome": self.intended_outcome, "scope": self.scope,
            "participants": [p.to_dict() for p in self.participants],
            "stakeholders": list(self.stakeholders),
            "milestones": [m.to_dict() for m in self.milestones],
            "dependencies": list(self.dependencies),
            "risks": [r.to_dict() for r in self.risks],
            "constraints": [c.to_dict() for c in self.constraints],
            "completion_criteria": list(self.completion_criteria),
            "budget": self.budget, "budget_spent": self.budget_spent,
            "progress_pct": self.progress_pct, "is_active": self.is_active,
            "budget_utilization_pct": self.budget_utilization_pct,
            "delayed_milestones": [m.title for m in self.delayed_milestones],
            "blocked_milestones": [m.title for m in self.blocked_milestones],
            "created_at": self.created_at, "updated_at": self.updated_at,
        }


@dataclass
class InitiativeProfile:
    profile_id: str = field(default_factory=_generate_id)
    owner_id: str = ""
    label: str = ""
    initiatives: list[Initiative] = field(default_factory=list)
    def to_dict(self) -> dict[str, Any]:
        return {"profile_id": self.profile_id, "owner_id": self.owner_id,
                "label": self.label, "total": len(self.initiatives)}

    @property
    def active_initiatives(self) -> list[Initiative]:
        return [i for i in self.initiatives if i.is_active]


@dataclass
class InitiativeRecommendation:
    rec_id: str = field(default_factory=_generate_id)
    title: str = ""
    description: str = ""
    priority: str = "medium"
    reasoning: str = ""
    confidence: float = 0.0
    affected_milestones: list[str] = field(default_factory=list)
    expected_impact: str = ""
    evidence: list[dict[str, Any]] = field(default_factory=list)
    def to_dict(self) -> dict[str, Any]:
        return {"rec_id": self.rec_id, "title": self.title, "description": self.description,
                "priority": self.priority, "reasoning": self.reasoning,
                "confidence": self.confidence, "affected_milestones": list(self.affected_milestones),
                "expected_impact": self.expected_impact, "evidence": list(self.evidence)}