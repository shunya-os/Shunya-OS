"""
SHUNYA Autonomous Organization Runtime — Coordination

Multiple Actors may collaborate. CoordinationSession maintains:
  Participants, Shared Objective, Dependencies, Current Blockers,
  Outstanding Responsibilities, Evidence, Outcome
"""

from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Optional

from app.organization.actor import Actor, get_store as get_actor_store


class SessionStatus(Enum):
    ACTIVE = "active"
    BLOCKED = "blocked"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


@dataclass
class CoordinationSession:
    """A coordination session for multi-actor collaboration."""

    session_id: str
    decision_id: str
    objective: str
    participant_ids: list[str] = field(default_factory=list)
    dependency_ids: list[str] = field(default_factory=list)
    blockers: list[str] = field(default_factory=list)
    outstanding_responsibilities: list[str] = field(default_factory=list)
    evidence_ids: list[str] = field(default_factory=list)
    status: SessionStatus = SessionStatus.ACTIVE
    created_at: str = ""
    completed_at: Optional[str] = None
    outcome: str = ""
    metadata: dict = field(default_factory=dict)

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now(timezone.utc).isoformat()

    def add_participant(self, actor_id: str) -> None:
        if actor_id not in self.participant_ids:
            self.participant_ids.append(actor_id)

    def add_blocker(self, blocker: str) -> None:
        self.blockers.append(blocker)
        self.status = SessionStatus.BLOCKED

    def resolve_blocker(self, blocker: str) -> None:
        self.blockers = [b for b in self.blockers if b != blocker]
        if not self.blockers:
            self.status = SessionStatus.ACTIVE

    def complete(self, outcome: str) -> None:
        self.status = SessionStatus.COMPLETED
        self.completed_at = datetime.now(timezone.utc).isoformat()
        self.outcome = outcome

    def to_dict(self) -> dict:
        return {
            "session_id": self.session_id,
            "decision_id": self.decision_id,
            "objective": self.objective,
            "participants": self.participant_ids,
            "dependencies": self.dependency_ids,
            "blockers": self.blockers,
            "outstanding_responsibilities": self.outstanding_responsibilities,
            "evidence_ids": self.evidence_ids,
            "status": self.status.value,
            "created_at": self.created_at,
            "completed_at": self.completed_at,
            "outcome": self.outcome,
        }


class CoordinationStore:
    def __init__(self):
        self._sessions: dict[str, CoordinationSession] = {}

    def add(self, session: CoordinationSession) -> None:
        self._sessions[session.session_id] = session

    def get(self, session_id: str) -> Optional[CoordinationSession]:
        return self._sessions.get(session_id)

    def get_by_decision(self, decision_id: str) -> list[CoordinationSession]:
        return [s for s in self._sessions.values() if s.decision_id == decision_id]

    def get_active(self) -> list[CoordinationSession]:
        return [s for s in self._sessions.values() if s.status == SessionStatus.ACTIVE]

    @property
    def count(self) -> int:
        return len(self._sessions)

    def clear(self) -> None:
        self._sessions.clear()


_store: Optional[CoordinationStore] = None


def get_store() -> CoordinationStore:
    global _store
    if _store is None:
        _store = CoordinationStore()
    return _store


def reset_store() -> None:
    global _store
    _store = None