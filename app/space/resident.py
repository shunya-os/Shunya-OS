"""SHUNYA Phase A1A — Persistent AI Resident.

Each Space owns persistent AI state that survives reopening.
Never recreate AI memory from scratch.

State includes:
- Current understanding
- Open questions
- Hypotheses
- Risks
- Opportunities
- Confidence
- Recommendations
- Reasoning snapshots
- Pending observations
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from app.space.store import get_store, SpaceStore


# =========================================================================
# AI Resident State
# =========================================================================


@dataclass
class AIResidentState:
    """Persistent AI state owned by a single Space.

    AI context survives reopening the Space.
    Never recreate AI memory from scratch.
    """
    space_id: str
    current_understanding: str = ""
    """What the AI currently understands about this Space."""
    open_questions: List[str] = field(default_factory=list)
    """Questions the AI is still working to answer."""
    hypotheses: List[Dict[str, Any]] = field(default_factory=list)
    """List of {hypothesis: str, confidence: float, evidence: [str]}"""
    risks: List[Dict[str, Any]] = field(default_factory=list)
    """List of {risk: str, severity: str, probability: float}"""
    opportunities: List[Dict[str, Any]] = field(default_factory=list)
    """List of {opportunity: str, potential: str, confidence: float}"""
    confidence: float = 0.5
    """Overall AI confidence in its understanding (0.0-1.0)."""
    recommendations: List[str] = field(default_factory=list)
    """AI-generated recommendations for this Space."""
    reasoning_snapshots: List[Dict[str, Any]] = field(default_factory=list)
    """List of {timestamp: str, reasoning: str, context: str}"""
    pending_observations: List[str] = field(default_factory=list)
    """Observations the AI has queued for processing."""
    updated_at: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if not self.updated_at:
            self.updated_at = datetime.now(timezone.utc).isoformat()

    def add_hypothesis(self, hypothesis: str, confidence: float = 0.5,
                       evidence: Optional[List[str]] = None) -> None:
        self.hypotheses.append({
            "hypothesis": hypothesis,
            "confidence": confidence,
            "evidence": evidence or [],
            "created_at": datetime.now(timezone.utc).isoformat(),
        })
        self.updated_at = datetime.now(timezone.utc).isoformat()

    def add_risk(self, risk: str, severity: str = "medium",
                 probability: float = 0.5) -> None:
        self.risks.append({
            "risk": risk,
            "severity": severity,
            "probability": probability,
            "created_at": datetime.now(timezone.utc).isoformat(),
        })
        self.updated_at = datetime.now(timezone.utc).isoformat()

    def add_opportunity(self, opportunity: str, potential: str = "medium",
                        confidence: float = 0.5) -> None:
        self.opportunities.append({
            "opportunity": opportunity,
            "potential": potential,
            "confidence": confidence,
            "created_at": datetime.now(timezone.utc).isoformat(),
        })
        self.updated_at = datetime.now(timezone.utc).isoformat()

    def add_reasoning_snapshot(self, reasoning: str,
                               context: str = "") -> None:
        self.reasoning_snapshots.append({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "reasoning": reasoning,
            "context": context,
        })
        self.updated_at = datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> dict:
        return {
            "space_id": self.space_id,
            "current_understanding": self.current_understanding,
            "open_questions": self.open_questions,
            "hypotheses": self.hypotheses,
            "risks": self.risks,
            "opportunities": self.opportunities,
            "confidence": self.confidence,
            "recommendations": self.recommendations,
            "reasoning_snapshots": self.reasoning_snapshots[-10:],
            "pending_observations": self.pending_observations,
            "updated_at": self.updated_at,
        }


# =========================================================================
# AI Resident Manager
# =========================================================================


class AIResidentManager:
    """Manages persistent AI residents for each Space.

    AI context survives reopening the Space.
    Never recreate AI memory from scratch.
    """

    def __init__(self, store: Optional[SpaceStore] = None):
        self._store = store or get_store()

    def get_resident(self, space_id: str) -> Optional[AIResidentState]:
        """Get the AI resident state for a Space."""
        space = self._store.get(space_id)
        if not space:
            return None
        return space.ai_resident

    def update_understanding(self, space_id: str,
                             understanding: str) -> bool:
        """Update the AI's current understanding of this Space."""
        space = self._store.get(space_id)
        if not space:
            return False
        space.ai_resident.current_understanding = understanding
        space.ai_resident.updated_at = datetime.now(timezone.utc).isoformat()
        return True

    def add_question(self, space_id: str, question: str) -> bool:
        """Add an open question."""
        space = self._store.get(space_id)
        if not space:
            return False
        if question not in space.ai_resident.open_questions:
            space.ai_resident.open_questions.append(question)
            space.ai_resident.updated_at = datetime.now(timezone.utc).isoformat()
        return True

    def close_question(self, space_id: str, question: str) -> bool:
        """Remove an open question (answered)."""
        space = self._store.get(space_id)
        if not space:
            return False
        space.ai_resident.open_questions = [
            q for q in space.ai_resident.open_questions if q != question
        ]
        space.ai_resident.updated_at = datetime.now(timezone.utc).isoformat()
        return True

    def add_hypothesis(self, space_id: str, hypothesis: str,
                       confidence: float = 0.5,
                       evidence: Optional[List[str]] = None) -> bool:
        space = self._store.get(space_id)
        if not space:
            return False
        space.ai_resident.add_hypothesis(hypothesis, confidence, evidence)
        return True

    def add_risk(self, space_id: str, risk: str,
                 severity: str = "medium",
                 probability: float = 0.5) -> bool:
        space = self._store.get(space_id)
        if not space:
            return False
        space.ai_resident.add_risk(risk, severity, probability)
        return True

    def add_opportunity(self, space_id: str, opportunity: str,
                        potential: str = "medium",
                        confidence: float = 0.5) -> bool:
        space = self._store.get(space_id)
        if not space:
            return False
        space.ai_resident.add_opportunity(opportunity, potential, confidence)
        return True

    def add_recommendation(self, space_id: str,
                           recommendation: str) -> bool:
        space = self._store.get(space_id)
        if not space:
            return False
        space.ai_resident.recommendations.append(recommendation)
        space.ai_resident.updated_at = datetime.now(timezone.utc).isoformat()
        return True

    def add_reasoning_snapshot(self, space_id: str,
                               reasoning: str,
                               context: str = "") -> bool:
        space = self._store.get(space_id)
        if not space:
            return False
        space.ai_resident.add_reasoning_snapshot(reasoning, context)
        return True

    def add_observation(self, space_id: str,
                        observation: str) -> bool:
        space = self._store.get(space_id)
        if not space:
            return False
        space.ai_resident.pending_observations.append(observation)
        space.ai_resident.updated_at = datetime.now(timezone.utc).isoformat()
        return True

    def update_confidence(self, space_id: str,
                          confidence: float) -> bool:
        space = self._store.get(space_id)
        if not space:
            return False
        space.ai_resident.confidence = max(0.0, min(1.0, confidence))
        space.ai_resident.updated_at = datetime.now(timezone.utc).isoformat()
        return True

    def get_snapshot(self, space_id: str) -> Optional[Dict[str, Any]]:
        """Get a full summary of AI resident state."""
        resident = self.get_resident(space_id)
        if not resident:
            return None
        return {
            "understanding": resident.current_understanding,
            "open_questions": resident.open_questions,
            "hypotheses": resident.hypotheses,
            "risks": resident.risks,
            "opportunities": resident.opportunities,
            "confidence": resident.confidence,
            "recommendations": resident.recommendations,
            "recent_snapshots": resident.reasoning_snapshots[-3:],
            "pending_observations": resident.pending_observations,
        }


# =========================================================================
# Singleton
# =========================================================================

_manager: Optional[AIResidentManager] = None


def get_resident_manager() -> AIResidentManager:
    global _manager
    if _manager is None:
        _manager = AIResidentManager()
    return _manager


def reset_resident_manager() -> None:
    global _manager
    _manager = None