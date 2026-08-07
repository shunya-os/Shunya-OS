"""Identity Intelligence — Stream D.

Models identity, intent, goals, values, preferences, constraints,
responsibilities, authorities, communication style, decision style,
working style, and learning style.

Identity is continuous. Memory composes Identity.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


class DecisionStyle(str, Enum):
    ANALYTICAL = "analytical"
    INTUITIVE = "intuitive"
    COLLABORATIVE = "collaborative"
    DECISIVE = "decisive"
    FLEXIBLE = "flexible"


class CommunicationStyle(str, Enum):
    DIRECT = "direct"
    DIPLOMATIC = "diplomatic"
    ANALYTICAL = "analytical"
    EXPRESSIVE = "expressive"
    STRUCTURED = "structured"


class WorkingStyle(str, Enum):
    FOCUSED = "focused"
    COLLABORATIVE = "collaborative"
    FLEXIBLE = "flexible"
    STRUCTURED = "structured"
    EXPERIMENTAL = "experimental"


class LearningStyle(str, Enum):
    VISUAL = "visual"
    AUDITORY = "auditory"
    READING = "reading"
    KINESTHETIC = "kinesthetic"
    EXPERIMENTAL = "experimental"


@dataclass
class Goal:
    goal_id: str = ""
    title: str = ""
    description: str = ""
    target_date: str = ""
    priority: str = "medium"
    status: str = "active"
    progress_pct: float = 0.0
    evidence_ids: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {"goal_id": self.goal_id, "title": self.title,
                "description": self.description, "target_date": self.target_date,
                "priority": self.priority, "status": self.status,
                "progress_pct": self.progress_pct}


@dataclass
class Identity:
    """Complete identity model — the full picture of a person or organization."""

    identity_id: str = ""
    identity_type: str = "person"  # person, organization, system
    name: str = ""
    bio: str = ""
    values: list[str] = field(default_factory=list)
    preferences: dict[str, Any] = field(default_factory=dict)
    constraints: list[str] = field(default_factory=list)
    responsibilities: list[str] = field(default_factory=list)
    authorities: list[str] = field(default_factory=list)
    goals: list[Goal] = field(default_factory=list)
    intent: str = ""
    decision_style: str = DecisionStyle.ANALYTICAL.value
    communication_style: str = CommunicationStyle.DIRECT.value
    working_style: str = WorkingStyle.FOCUSED.value
    learning_style: str = LearningStyle.READING.value
    memory_ids: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=_now_iso)
    updated_at: str = field(default_factory=_now_iso)

    def to_dict(self) -> dict[str, Any]:
        return {"identity_id": self.identity_id, "identity_type": self.identity_type,
                "name": self.name, "bio": self.bio, "values": list(self.values),
                "preferences": dict(self.preferences), "constraints": list(self.constraints),
                "responsibilities": list(self.responsibilities),
                "authorities": list(self.authorities),
                "goals": [g.to_dict() for g in self.goals],
                "intent": self.intent,
                "decision_style": self.decision_style,
                "communication_style": self.communication_style,
                "working_style": self.working_style,
                "learning_style": self.learning_style,
                "tags": list(self.tags), "created_at": self.created_at,
                "updated_at": self.updated_at}


class IdentityEngine:
    """Manages identity profiles — memory composes identity."""

    def __init__(self) -> None:
        self._identities: dict[str, Identity] = {}

    def create(self, identity_id: str, name: str,
               identity_type: str = "person") -> Identity:
        identity = Identity(identity_id=identity_id, name=name,
                           identity_type=identity_type)
        self._identities[identity_id] = identity
        return identity

    def get(self, identity_id: str) -> Identity | None:
        return self._identities.get(identity_id)

    def update(self, identity_id: str, **kwargs: Any) -> Identity | None:
        identity = self._identities.get(identity_id)
        if not identity:
            return None
        for key, val in kwargs.items():
            if hasattr(identity, key) and key not in ("identity_id", "created_at"):
                setattr(identity, key, val)
        identity.updated_at = _now_iso()
        return identity

    def add_goal(self, identity_id: str, title: str, description: str = "",
                 priority: str = "medium") -> Goal | None:
        identity = self._identities.get(identity_id)
        if not identity:
            return None
        import uuid
        goal = Goal(goal_id=str(uuid.uuid4()), title=title,
                    description=description, priority=priority)
        identity.goals.append(goal)
        identity.updated_at = _now_iso()
        return goal

    def update_goal(self, identity_id: str, goal_id: str,
                    **kwargs: Any) -> bool:
        identity = self._identities.get(identity_id)
        if not identity:
            return False
        for goal in identity.goals:
            if goal.goal_id == goal_id:
                for key, val in kwargs.items():
                    if hasattr(goal, key):
                        setattr(goal, key, val)
                identity.updated_at = _now_iso()
                return True
        return False

    def list_identities(self) -> list[Identity]:
        return list(self._identities.values())

    def find_by_intent(self, intent: str) -> list[Identity]:
        q = intent.lower()
        return [i for i in self._identities.values() if q in i.intent.lower()]

    def health_check(self) -> dict[str, Any]:
        return {"status": "healthy", "identities": len(self._identities),
                "goals": sum(len(i.goals) for i in self._identities.values())}