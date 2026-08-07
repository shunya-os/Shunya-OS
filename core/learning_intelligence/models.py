"""Universal Learning Intelligence — Data Models.

Learning Intelligence models continuous learning by individuals and organizations.
It does not model LMS, education software, or training administration.

Every Living Object has: identity (UUID), time (created_at/updated_at),
space (owner_id), reality (notify), evidence (evidence_ids).

Every recommendation exposes: reasoning, evidence, confidence, assumptions,
alternatives, expected impact.

UCP-11 — Universal Learning Intelligence.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _generate_id() -> str:
    import uuid
    return str(uuid.uuid4())


# ── Enums ─────────────────────────────────────────────────────────────────


class SkillProficiency(str, Enum):
    """Proficiency levels for skills — universal continuum."""
    UNKNOWN = "unknown"
    NOVICE = "novice"
    ADVANCED_BEGINNER = "advanced_beginner"
    COMPETENT = "competent"
    PROFICIENT = "proficient"
    EXPERT = "expert"


class CompetencyLevel(str, Enum):
    """Behavioral competency levels — not skill proficiency."""
    AWARENESS = "awareness"
    UNDERSTANDING = "understanding"
    APPLICATION = "application"
    ANALYSIS = "analysis"
    SYNTHESIS = "synthesis"
    EVALUATION = "evaluation"


class LearningGoalStatus(str, Enum):
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    ON_HOLD = "on_hold"
    CANCELLED = "cancelled"


class LearningPathStatus(str, Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    COMPLETED = "completed"
    PAUSED = "paused"
    CANCELLED = "cancelled"


class LearningStyle(str, Enum):
    """Canonical learning style modalities."""
    VISUAL = "visual"
    AUDITORY = "auditory"
    READING = "reading"
    KINESTHETIC = "kinesthetic"
    SOCIAL = "social"
    SOLITARY = "solitary"
    MIXED = "mixed"


class InteractionMode(str, Enum):
    """Mode of interaction in a learning context."""
    SELF_STUDY = "self_study"
    ONE_ON_ONE = "one_on_one"
    GROUP = "group"
    WORKSHOP = "workshop"
    SEMINAR = "seminar"
    HANDS_ON = "hands_on"
    SIMULATION = "simulation"
    PROJECT = "project"
    AI_GUIDED = "ai_guided"
    PEER_REVIEW = "peer_review"
    READING = "reading"
    VISUAL = "visual"
    AUDITORY = "auditory"
    TUTORIAL = "tutorial"
    ASSESSMENT = "assessment"
    MIXED = "mixed"


class AssessmentType(str, Enum):
    """Types of assessment in learning."""
    DIAGNOSTIC = "diagnostic"
    FORMATIVE = "formative"
    SUMMATIVE = "summative"
    SELF = "self"
    PEER = "peer"
    AI_ASSISTED = "ai_assisted"
    PERFORMANCE = "performance"
    PORTFOLIO = "portfolio"


# ── Data Models ────────────────────────────────────────────────────────────


@dataclass
class Skill:
    """A skill — a learned capacity to perform an action or task.

    Living Object: identity (skill_id), time (created_at/updated_at),
    space (owner_id), reality (notify), evidence (evidence_ids).
    """
    skill_id: str = field(default_factory=_generate_id)
    owner_id: str = ""
    name: str = ""
    description: str = ""
    category: str = ""  # technical, soft, domain, language, leadership, etc.
    tags: list[str] = field(default_factory=list)
    proficiency: str = SkillProficiency.UNKNOWN.value
    proficiency_score: float = 0.0  # 0.0 - 1.0
    hours_practiced: float = 0.0
    last_practiced: str = ""
    source: str = ""  # education, work, self_study, coaching, certification
    prerequisites: list[str] = field(default_factory=list)  # skill_ids
    related_skills: list[str] = field(default_factory=list)
    evidence_ids: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=_now_iso)
    updated_at: str = field(default_factory=_now_iso)

    def to_dict(self) -> dict[str, Any]:
        return {
            "skill_id": self.skill_id,
            "owner_id": self.owner_id,
            "name": self.name,
            "description": self.description,
            "category": self.category,
            "tags": list(self.tags),
            "proficiency": self.proficiency,
            "proficiency_score": self.proficiency_score,
            "hours_practiced": self.hours_practiced,
            "last_practiced": self.last_practiced,
            "source": self.source,
            "prerequisites": list(self.prerequisites),
            "related_skills": list(self.related_skills),
            "evidence_ids": list(self.evidence_ids),
            "metadata": dict(self.metadata),
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


@dataclass
class KnowledgeGrowthEntry:
    """A record of knowledge growth — acquisition, deepening, or connection.

    Living Object: identity (entry_id), time (created_at/updated_at),
    space (owner_id), reality (notify), evidence (evidence_ids).
    """
    entry_id: str = field(default_factory=_generate_id)
    owner_id: str = ""
    knowledge_id: str = ""
    title: str = ""
    domain: str = ""
    previous_confidence: float = 0.0
    new_confidence: float = 0.0
    delta: float = 0.0
    trigger: str = ""  # study, practice, teaching, application, discussion
    context: str = ""
    reflection: str = ""
    evidence_ids: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=_now_iso)
    updated_at: str = field(default_factory=_now_iso)

    @property
    def growth_pct(self) -> float:
        if self.previous_confidence == 0:
            return 100.0 if self.new_confidence > 0 else 0.0
        return round(((self.new_confidence - self.previous_confidence) / self.previous_confidence) * 100, 1)

    def to_dict(self) -> dict[str, Any]:
        return {
            "entry_id": self.entry_id,
            "owner_id": self.owner_id,
            "knowledge_id": self.knowledge_id,
            "title": self.title,
            "domain": self.domain,
            "previous_confidence": self.previous_confidence,
            "new_confidence": self.new_confidence,
            "delta": self.delta,
            "growth_pct": self.growth_pct,
            "trigger": self.trigger,
            "context": self.context,
            "reflection": self.reflection,
            "evidence_ids": list(self.evidence_ids),
            "metadata": dict(self.metadata),
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


@dataclass
class Competency:
    """A behavioral competency — demonstrable capability combining knowledge,
    skills, and attitudes.

    Living Object: identity (competency_id), time (created_at/updated_at),
    space (owner_id), reality (notify), evidence (evidence_ids).
    """
    competency_id: str = field(default_factory=_generate_id)
    owner_id: str = ""
    name: str = ""
    description: str = ""
    level: str = CompetencyLevel.AWARENESS.value
    assessment_date: str = ""
    assessor: str = ""  # person, system, or ai
    skill_ids: list[str] = field(default_factory=list)
    knowledge_ids: list[str] = field(default_factory=list)
    demonstrated_through: list[str] = field(default_factory=list)
    evidence_ids: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=_now_iso)
    updated_at: str = field(default_factory=_now_iso)

    def to_dict(self) -> dict[str, Any]:
        return {
            "competency_id": self.competency_id,
            "owner_id": self.owner_id,
            "name": self.name,
            "description": self.description,
            "level": self.level,
            "assessment_date": self.assessment_date,
            "assessor": self.assessor,
            "skill_ids": list(self.skill_ids),
            "knowledge_ids": list(self.knowledge_ids),
            "demonstrated_through": list(self.demonstrated_through),
            "evidence_ids": list(self.evidence_ids),
            "metadata": dict(self.metadata),
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


@dataclass
class Certification:
    """A certification — formal recognition of demonstrated competence.

    Living Object: identity (certification_id), time (created_at/updated_at),
    space (owner_id), reality (notify), evidence (evidence_ids).
    """
    certification_id: str = field(default_factory=_generate_id)
    owner_id: str = ""
    name: str = ""
    issuing_body: str = ""
    description: str = ""
    competency_ids: list[str] = field(default_factory=list)
    skill_ids: list[str] = field(default_factory=list)
    issue_date: str = ""
    expiry_date: str = ""
    renewal_required: bool = False
    credential_url: str = ""
    status: str = "active"  # active, expired, revoked, pending
    evidence_ids: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=_now_iso)
    updated_at: str = field(default_factory=_now_iso)

    @property
    def is_expired(self) -> bool:
        if not self.expiry_date:
            return False
        try:
            exp = datetime.fromisoformat(self.expiry_date.replace("Z", "+00:00"))
            return datetime.now(timezone.utc) > exp
        except (ValueError, TypeError):
            return False

    @property
    def is_due_for_renewal(self) -> bool:
        if not self.renewal_required or not self.expiry_date:
            return False
        try:
            from datetime import timedelta
            exp = datetime.fromisoformat(self.expiry_date.replace("Z", "+00:00"))
            return timedelta(days=90) >= (exp - datetime.now(timezone.utc)) >= timedelta(days=0)
        except (ValueError, TypeError):
            return False

    def to_dict(self) -> dict[str, Any]:
        return {
            "certification_id": self.certification_id,
            "owner_id": self.owner_id,
            "name": self.name,
            "issuing_body": self.issuing_body,
            "description": self.description,
            "competency_ids": list(self.competency_ids),
            "skill_ids": list(self.skill_ids),
            "issue_date": self.issue_date,
            "expiry_date": self.expiry_date,
            "renewal_required": self.renewal_required,
            "credential_url": self.credential_url,
            "status": self.status,
            "is_expired": self.is_expired,
            "is_due_for_renewal": self.is_due_for_renewal,
            "evidence_ids": list(self.evidence_ids),
            "metadata": dict(self.metadata),
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


@dataclass
class PracticeSession:
    """A deliberate practice session — structured repetition for skill growth.

    Living Object: identity (session_id), time (created_at/updated_at),
    space (owner_id), reality (notify), evidence (evidence_ids).
    """
    session_id: str = field(default_factory=_generate_id)
    owner_id: str = ""
    skill_ids: list[str] = field(default_factory=list)
    title: str = ""
    description: str = ""
    duration_minutes: float = 0.0
    intensity: str = "medium"  # low, medium, high, focused
    outcome: str = ""
    performance_score: float = 0.0  # 0.0 - 1.0
    errors_made: int = 0
    insights: list[str] = field(default_factory=list)
    next_focus: str = ""
    evidence_ids: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=_now_iso)
    updated_at: str = field(default_factory=_now_iso)

    @property
    def effective_score(self) -> float:
        error_penalty = min(self.errors_made * 0.05, 0.5)
        return max(0.0, min(1.0, self.performance_score - error_penalty))

    def to_dict(self) -> dict[str, Any]:
        return {
            "session_id": self.session_id,
            "owner_id": self.owner_id,
            "skill_ids": list(self.skill_ids),
            "title": self.title,
            "description": self.description,
            "duration_minutes": self.duration_minutes,
            "intensity": self.intensity,
            "outcome": self.outcome,
            "performance_score": self.performance_score,
            "errors_made": self.errors_made,
            "effective_score": self.effective_score,
            "insights": list(self.insights),
            "next_focus": self.next_focus,
            "evidence_ids": list(self.evidence_ids),
            "metadata": dict(self.metadata),
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


@dataclass
class ExperienceRecord:
    """A learning experience — knowledge or skill gained through doing.

    Living Object: identity (experience_id), time (created_at/updated_at),
    space (owner_id), reality (notify), evidence (evidence_ids).
    """
    experience_id: str = field(default_factory=_generate_id)
    owner_id: str = ""
    title: str = ""
    description: str = ""
    context: str = ""
    duration: str = ""
    skills_gained: list[str] = field(default_factory=list)
    knowledge_gained: list[str] = field(default_factory=list)
    lessons_learned: list[str] = field(default_factory=list)
    challenges: list[str] = field(default_factory=list)
    success_factors: list[str] = field(default_factory=list)
    domain: str = ""
    tags: list[str] = field(default_factory=list)
    evidence_ids: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=_now_iso)
    updated_at: str = field(default_factory=_now_iso)

    def to_dict(self) -> dict[str, Any]:
        return {
            "experience_id": self.experience_id,
            "owner_id": self.owner_id,
            "title": self.title,
            "description": self.description,
            "context": self.context,
            "duration": self.duration,
            "skills_gained": list(self.skills_gained),
            "knowledge_gained": list(self.knowledge_gained),
            "lessons_learned": list(self.lessons_learned),
            "challenges": list(self.challenges),
            "success_factors": list(self.success_factors),
            "domain": self.domain,
            "tags": list(self.tags),
            "evidence_ids": list(self.evidence_ids),
            "metadata": dict(self.metadata),
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


@dataclass
class CoachingEngagement:
    """A coaching engagement — structured guidance for growth.

    Living Object: identity (engagement_id), time (created_at/updated_at),
    space (owner_id/coach_id), reality (notify), evidence (evidence_ids).

    Composes from Relationship Intelligence (coach relationship).
    """
    engagement_id: str = field(default_factory=_generate_id)
    owner_id: str = ""  # coachee/learner
    coach_id: str = ""
    relationship_profile_id: str = ""  # references Relationship UCP profile
    title: str = ""
    purpose: str = ""
    goals: list[str] = field(default_factory=list)
    focus_areas: list[str] = field(default_factory=list)
    session_count: int = 0
    total_hours: float = 0.0
    status: str = "active"  # active, completed, paused, cancelled
    outcomes: list[str] = field(default_factory=list)
    feedback: str = ""
    skill_ids: list[str] = field(default_factory=list)
    action_ids: list[str] = field(default_factory=list)  # from Initiative UCP
    evidence_ids: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=_now_iso)
    updated_at: str = field(default_factory=_now_iso)

    def to_dict(self) -> dict[str, Any]:
        return {
            "engagement_id": self.engagement_id,
            "owner_id": self.owner_id,
            "coach_id": self.coach_id,
            "relationship_profile_id": self.relationship_profile_id,
            "title": self.title,
            "purpose": self.purpose,
            "goals": list(self.goals),
            "focus_areas": list(self.focus_areas),
            "session_count": self.session_count,
            "total_hours": self.total_hours,
            "status": self.status,
            "outcomes": list(self.outcomes),
            "feedback": self.feedback,
            "skill_ids": list(self.skill_ids),
            "action_ids": list(self.action_ids),
            "evidence_ids": list(self.evidence_ids),
            "metadata": dict(self.metadata),
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


@dataclass
class MentoringRelationship:
    """A mentoring relationship — experienced guidance for development.

    Living Object: identity (relationship_id), time (created_at/updated_at),
    space (owner_id/mentor_id), reality (notify), evidence (evidence_ids).

    Composes from Relationship Intelligence (mentor relationship).
    """
    relationship_id: str = field(default_factory=_generate_id)
    owner_id: str = ""  # mentee
    mentor_id: str = ""
    relationship_profile_id: str = ""  # references Relationship UCP profile
    title: str = ""
    focus_area: str = ""
    format: str = ""  # regular_meetings, async, hybrid
    frequency: str = ""  # weekly, biweekly, monthly
    goals: list[str] = field(default_factory=list)
    topics_covered: list[str] = field(default_factory=list)
    milestones: list[dict[str, Any]] = field(default_factory=list)
    outcomes: list[str] = field(default_factory=list)
    satisfaction_score: float = 0.0
    status: str = "active"
    duration_months: int = 0
    evidence_ids: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=_now_iso)
    updated_at: str = field(default_factory=_now_iso)

    def to_dict(self) -> dict[str, Any]:
        return {
            "relationship_id": self.relationship_id,
            "owner_id": self.owner_id,
            "mentor_id": self.mentor_id,
            "relationship_profile_id": self.relationship_profile_id,
            "title": self.title,
            "focus_area": self.focus_area,
            "format": self.format,
            "frequency": self.frequency,
            "goals": list(self.goals),
            "topics_covered": list(self.topics_covered),
            "milestones": list(self.milestones),
            "outcomes": list(self.outcomes),
            "satisfaction_score": self.satisfaction_score,
            "status": self.status,
            "duration_months": self.duration_months,
            "evidence_ids": list(self.evidence_ids),
            "metadata": dict(self.metadata),
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


@dataclass
class OrganizationalLearning:
    """Organizational learning — collective knowledge and capability growth.

    Living Object: identity (org_learning_id), time (created_at/updated_at),
    space (owner_id/org_id), reality (notify), evidence (evidence_ids).

    Composes from Initiative UCP (learning programmes as initiatives).
    """
    org_learning_id: str = field(default_factory=_generate_id)
    owner_id: str = ""
    org_id: str = ""
    initiative_ids: list[str] = field(default_factory=list)  # from Initiative UCP
    name: str = ""
    description: str = ""
    programmes: list[dict[str, Any]] = field(default_factory=list)
    learning_culture_score: float = 0.0
    total_learners: int = 0
    total_capabilities: int = 0
    knowledge_base_ids: list[str] = field(default_factory=list)  # from Knowledge UCP
    lessons_learned: list[dict[str, Any]] = field(default_factory=list)
    impact_metrics: dict[str, float] = field(default_factory=dict)
    evidence_ids: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=_now_iso)
    updated_at: str = field(default_factory=_now_iso)

    def to_dict(self) -> dict[str, Any]:
        return {
            "org_learning_id": self.org_learning_id,
            "owner_id": self.owner_id,
            "org_id": self.org_id,
            "initiative_ids": list(self.initiative_ids),
            "name": self.name,
            "description": self.description,
            "programmes": list(self.programmes),
            "learning_culture_score": self.learning_culture_score,
            "total_learners": self.total_learners,
            "total_capabilities": self.total_capabilities,
            "knowledge_base_ids": list(self.knowledge_base_ids),
            "lessons_learned": list(self.lessons_learned),
            "impact_metrics": dict(self.impact_metrics),
            "evidence_ids": list(self.evidence_ids),
            "metadata": dict(self.metadata),
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


@dataclass
class LearningSession:
    """A learning session — a discrete unit of learning activity.

    Living Object: identity (session_id), time (created_at/updated_at),
    space (owner_id), reality (notify), evidence (evidence_ids).
    """
    session_id: str = field(default_factory=_generate_id)
    owner_id: str = ""
    learning_path_id: str = ""
    title: str = ""
    description: str = ""
    mode: str = InteractionMode.SELF_STUDY.value
    duration_minutes: float = 0.0
    focus_area: str = ""
    topics: list[str] = field(default_factory=list)
    resources: list[str] = field(default_factory=list)
    ai_guidance: str = ""  # AI-guided learning context / prompts
    comprehension_score: float = 0.0
    notes: str = ""
    action_items: list[str] = field(default_factory=list)
    evidence_ids: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=_now_iso)
    updated_at: str = field(default_factory=_now_iso)

    def to_dict(self) -> dict[str, Any]:
        return {
            "session_id": self.session_id,
            "owner_id": self.owner_id,
            "learning_path_id": self.learning_path_id,
            "title": self.title,
            "description": self.description,
            "mode": self.mode,
            "duration_minutes": self.duration_minutes,
            "focus_area": self.focus_area,
            "topics": list(self.topics),
            "resources": list(self.resources),
            "ai_guidance": self.ai_guidance,
            "comprehension_score": self.comprehension_score,
            "notes": self.notes,
            "action_items": list(self.action_items),
            "evidence_ids": list(self.evidence_ids),
            "metadata": dict(self.metadata),
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


@dataclass
class LearningGoal:
    """A learning goal — intended outcome of a learning journey.

    Living Object: identity (goal_id), time (created_at/updated_at),
    space (owner_id), reality (notify), evidence (evidence_ids).
    """
    goal_id: str = field(default_factory=_generate_id)
    owner_id: str = ""
    learning_path_id: str = ""
    title: str = ""
    description: str = ""
    desired_outcome: str = ""
    target_date: str = ""
    status: str = LearningGoalStatus.NOT_STARTED.value
    skill_ids: list[str] = field(default_factory=list)
    competency_ids: list[str] = field(default_factory=list)
    knowledge_ids: list[str] = field(default_factory=list)
    progress_pct: float = 0.0
    evidence_ids: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=_now_iso)
    updated_at: str = field(default_factory=_now_iso)

    @property
    def is_overdue(self) -> bool:
        if not self.target_date:
            return False
        try:
            target = datetime.fromisoformat(self.target_date.replace("Z", "+00:00"))
            return datetime.now(timezone.utc) > target and self.status != LearningGoalStatus.COMPLETED.value
        except (ValueError, TypeError):
            return False

    def to_dict(self) -> dict[str, Any]:
        return {
            "goal_id": self.goal_id,
            "owner_id": self.owner_id,
            "learning_path_id": self.learning_path_id,
            "title": self.title,
            "description": self.description,
            "desired_outcome": self.desired_outcome,
            "target_date": self.target_date,
            "status": self.status,
            "skill_ids": list(self.skill_ids),
            "competency_ids": list(self.competency_ids),
            "knowledge_ids": list(self.knowledge_ids),
            "progress_pct": self.progress_pct,
            "is_overdue": self.is_overdue,
            "evidence_ids": list(self.evidence_ids),
            "metadata": dict(self.metadata),
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


@dataclass
class LearningPath:
    """A learning path — structured sequence of activities toward mastery.

    Living Object: identity (path_id), time (created_at/updated_at),
    space (owner_id), reality (notify), evidence (evidence_ids).
    """
    path_id: str = field(default_factory=_generate_id)
    owner_id: str = ""
    title: str = ""
    description: str = ""
    status: str = LearningPathStatus.DRAFT.value
    goals: list[LearningGoal] = field(default_factory=list)
    sessions: list[LearningSession] = field(default_factory=list)
    practice_sessions: list[PracticeSession] = field(default_factory=list)
    target_skills: list[str] = field(default_factory=list)
    target_competencies: list[str] = field(default_factory=list)
    prerequisites: list[str] = field(default_factory=list)
    estimated_hours: float = 0.0
    completed_hours: float = 0.0
    mode: str = InteractionMode.MIXED.value
    assessment_type: str = AssessmentType.PORTFOLIO.value
    ai_guided: bool = False
    mentor_id: str = ""
    coach_id: str = ""
    evidence_ids: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=_now_iso)
    updated_at: str = field(default_factory=_now_iso)

    @property
    def progress_pct(self) -> float:
        total = len(self.goals)
        if total == 0:
            return 0.0
        completed = sum(1 for g in self.goals if g.status == LearningGoalStatus.COMPLETED.value)
        return round((completed / total) * 100, 1)

    @property
    def overdue_goals(self) -> list[LearningGoal]:
        return [g for g in self.goals if g.is_overdue]

    def to_dict(self) -> dict[str, Any]:
        return {
            "path_id": self.path_id,
            "owner_id": self.owner_id,
            "title": self.title,
            "description": self.description,
            "status": self.status,
            "goals": [g.to_dict() for g in self.goals],
            "sessions": [s.to_dict() for s in self.sessions],
            "practice_sessions": [p.to_dict() for p in self.practice_sessions],
            "target_skills": list(self.target_skills),
            "target_competencies": list(self.target_competencies),
            "prerequisites": list(self.prerequisites),
            "estimated_hours": self.estimated_hours,
            "completed_hours": self.completed_hours,
            "progress_pct": self.progress_pct,
            "overdue_goals": len(self.overdue_goals),
            "mode": self.mode,
            "assessment_type": self.assessment_type,
            "ai_guided": self.ai_guided,
            "mentor_id": self.mentor_id,
            "coach_id": self.coach_id,
            "evidence_ids": list(self.evidence_ids),
            "metadata": dict(self.metadata),
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


@dataclass
class LearningRecommendation:
    """A recommendation for learning — actionable guidance.

    Every recommendation exposes: reasoning, evidence, confidence, assumptions,
    alternatives, expected impact.
    """
    rec_id: str = field(default_factory=_generate_id)
    title: str = ""
    description: str = ""
    priority: str = "medium"
    reasoning: str = ""
    evidence: list[dict[str, Any]] = field(default_factory=list)
    confidence: float = 0.0
    assumptions: list[str] = field(default_factory=list)
    alternatives: list[str] = field(default_factory=list)
    expected_impact: str = ""
    affected_skills: list[str] = field(default_factory=list)
    affected_goals: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "rec_id": self.rec_id,
            "title": self.title,
            "description": self.description,
            "priority": self.priority,
            "reasoning": self.reasoning,
            "evidence": list(self.evidence),
            "confidence": self.confidence,
            "assumptions": list(self.assumptions),
            "alternatives": list(self.alternatives),
            "expected_impact": self.expected_impact,
            "affected_skills": list(self.affected_skills),
            "affected_goals": list(self.affected_goals),
            "metadata": dict(self.metadata),
        }


@dataclass
class LearningProfile:
    """A learner's complete learning intelligence profile.

    The primary accessor — the living intelligence for a learner.
    """
    profile_id: str = field(default_factory=_generate_id)
    owner_id: str = ""
    label: str = ""
    learning_paths: list[LearningPath] = field(default_factory=list)
    skills: list[Skill] = field(default_factory=list)
    competencies: list[Competency] = field(default_factory=list)
    certifications: list[Certification] = field(default_factory=list)
    knowledge_growth: list[KnowledgeGrowthEntry] = field(default_factory=list)
    practice_sessions: list[PracticeSession] = field(default_factory=list)
    experiences: list[ExperienceRecord] = field(default_factory=list)
    coaching_engagements: list[CoachingEngagement] = field(default_factory=list)
    mentoring_relationships: list[MentoringRelationship] = field(default_factory=list)
    organizational_learning: list[OrganizationalLearning] = field(default_factory=list)
    recommendations: list[LearningRecommendation] = field(default_factory=list)
    preferred_style: str = LearningStyle.MIXED.value
    total_learning_hours: float = 0.0
    evidence_ids: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=_now_iso)
    updated_at: str = field(default_factory=_now_iso)

    @property
    def total_skills(self) -> int:
        return len(self.skills)

    @property
    def active_paths(self) -> list[LearningPath]:
        return [p for p in self.learning_paths if p.status in (
            LearningPathStatus.ACTIVE.value, LearningPathStatus.DRAFT.value)]

    @property
    def completed_certifications(self) -> list[Certification]:
        return [c for c in self.certifications if c.status == "active"]

    @property
    def overall_proficiency_avg(self) -> float:
        scores = [s.proficiency_score for s in self.skills]
        return sum(scores) / len(scores) if scores else 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "profile_id": self.profile_id,
            "owner_id": self.owner_id,
            "label": self.label,
            "learning_paths": [p.to_dict() for p in self.learning_paths],
            "skills": [s.to_dict() for s in self.skills],
            "competencies": [c.to_dict() for c in self.competencies],
            "certifications": [c.to_dict() for c in self.certifications],
            "knowledge_growth": [k.to_dict() for k in self.knowledge_growth],
            "practice_sessions": [p.to_dict() for p in self.practice_sessions],
            "experiences": [e.to_dict() for e in self.experiences],
            "coaching_engagements": [c.to_dict() for c in self.coaching_engagements],
            "mentoring_relationships": [m.to_dict() for m in self.mentoring_relationships],
            "organizational_learning": [o.to_dict() for o in self.organizational_learning],
            "recommendations": [r.to_dict() for r in self.recommendations],
            "preferred_style": self.preferred_style,
            "total_learning_hours": self.total_learning_hours,
            "total_skills": self.total_skills,
            "active_paths": len(self.active_paths),
            "completed_certifications": len(self.completed_certifications),
            "overall_proficiency_avg": round(self.overall_proficiency_avg, 2),
            "evidence_ids": list(self.evidence_ids),
            "metadata": dict(self.metadata),
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }