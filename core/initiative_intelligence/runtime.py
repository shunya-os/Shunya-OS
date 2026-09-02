"""Universal Initiative Intelligence — Runtime.

InitiativeIntelligenceRuntime composes from all frozen UCPs.
No Project Runtime. No Task Runtime. No Portfolio Runtime.
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from typing import Any

from core.initiative_intelligence.engine import InitiativeIntelligenceEngine
from core.initiative_intelligence.models import (
    Initiative, InitiativeProfile, InitiativeMilestone, InitiativeConstraint,
    InitiativeRisk, InitiativeRecommendation, InitiativeType, InitiativeStatus,
    MilestoneStatus, Participant,
    _generate_id, _now_iso,
)

logger = logging.getLogger(__name__)


class InitiativeIntelligenceRuntime:
    def __init__(self) -> None:
        self._engine = InitiativeIntelligenceEngine()
        self._profiles: dict[str, InitiativeProfile] = {}
        self._reality_listeners: list[Callable[[dict[str, Any]], None]] = []

    def get_or_create_profile(self, owner_id: str, label: str = "") -> InitiativeProfile:
        for p in self._profiles.values():
            if p.owner_id == owner_id:
                return p
        p = InitiativeProfile(owner_id=owner_id, label=label or f"Initiative profile for {owner_id}")
        self._profiles[p.profile_id] = p
        return p

    def _resolve(self, owner_id: str) -> InitiativeProfile | None:
        for p in self._profiles.values():
            if p.owner_id == owner_id:
                return p
        return None

    def create_initiative(
        self, owner_id: str,
        initiative_type: str = InitiativeType.PERSONAL_GOAL.value,
        title: str = "", purpose: str = "", intended_outcome: str = "",
        scope: str = "", participants: list[dict] | None = None,
        milestones: list[dict] | None = None,
        budget: float = 0.0,
    ) -> Initiative | None:
        profile = self._resolve(owner_id) or self.get_or_create_profile(owner_id)
        ini = Initiative(
            initiative_type=initiative_type, title=title, purpose=purpose,
            intended_outcome=intended_outcome, scope=scope,
            participants=[Participant(**p) for p in (participants or [])],
            milestones=[InitiativeMilestone(**m) for m in (milestones or [])],
            budget=budget,
        )
        profile.initiatives.append(ini)
        self._notify({"type": "initiative.created", "owner_id": owner_id,
                       "initiative_id": ini.initiative_id, "title": title})
        return ini

    def get_initiative(self, owner_id: str, initiative_id: str) -> Initiative | None:
        profile = self._resolve(owner_id)
        if not profile:
            return None
        for i in profile.initiatives:
            if i.initiative_id == initiative_id:
                return i
        return None

    def update_milestone(self, owner_id: str, initiative_id: str,
                          milestone_id: str, status: str) -> bool:
        ini = self.get_initiative(owner_id, initiative_id)
        if not ini:
            return False
        for m in ini.milestones:
            if m.milestone_id == milestone_id:
                m.status = status
                if status == MilestoneStatus.COMPLETED.value:
                    m.completed_date = _now_iso()
                ini.updated_at = _now_iso()
                return True
        return False

    def analyze(self, owner_id: str, initiative_id: str) -> dict[str, Any] | None:
        ini = self.get_initiative(owner_id, initiative_id)
        if not ini:
            return None
        return {
            "initiative": ini.to_dict(),
            "milestone_recs": [r.to_dict() for r in self._engine.reason_about_milestones(ini)],
            "dependencies": self._engine.analyze_dependencies(ini),
            "risks": self._engine.predict_risks(ini),
            "health": self._engine.compute_health(ini),
            "bottlenecks": self._engine.detect_bottlenecks(ini),
            "outcome": self._engine.predict_outcome(ini),
        }

    def get_recommendations(self, owner_id: str, initiative_id: str) -> list[dict[str, Any]]:
        ini = self.get_initiative(owner_id, initiative_id)
        if not ini:
            return []
        recs = list(self._engine.reason_about_milestones(ini))
        recs.extend(self._engine.adaptive_replan(ini, "Routine assessment"))
        return [r.to_dict() for r in recs]

    def adaptive_replan(self, owner_id: str, initiative_id: str,
                         change_description: str) -> list[dict[str, Any]]:
        ini = self.get_initiative(owner_id, initiative_id)
        if not ini:
            return []
        recs = self._engine.adaptive_replan(ini, change_description)
        return [r.to_dict() for r in recs]

    def initialize(self) -> None: logger.info("InitiativeIntelligenceRuntime initialized")
    def shutdown(self) -> None: self._profiles.clear(); self._reality_listeners.clear()
    def health_check(self) -> dict: return {"status": "healthy", "runtime": "initiative_intelligence",
                                              "profile_count": len(self._profiles)}
    def handle_event(self, event: Any) -> None:
        if isinstance(event, dict): self.notify(event)
    def get_capabilities(self) -> list[str]: return ["initiative.profile", "initiative.create",
        "initiative.analyze", "initiative.milestones", "initiative.risks", "initiative.health",
        "initiative.bottlenecks", "initiative.replan", "initiative.reality_integration"]

    def notify(self, notification: dict[str, Any]) -> None: pass
    def _notify(self, n: dict) -> None:
        for l in self._reality_listeners:
            try: l(n)
            except Exception: pass
    def register_reality_listener(self, l: Callable) -> None: self._reality_listeners.append(l)
    def unregister_reality_listener(self, l: Callable) -> None:
        if l in self._reality_listeners: self._reality_listeners.remove(l)