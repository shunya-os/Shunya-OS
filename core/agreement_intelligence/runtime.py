"""Universal Agreement Intelligence — Runtime.

AgreementIntelligenceRuntime composes from all frozen UCPs.
No Contract Runtime. No Procurement Runtime. No Legal Runtime.
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from typing import Any

from core.agreement_intelligence.engine import AgreementIntelligenceEngine
from core.agreement_intelligence.models import (
    Agreement,
    AgreementProfile,
    AgreementRecommendation,
    AgreementStatus,
    AgreementType,
    Amendment,
    Condition,
    Milestone,
    Obligation,
    ObligationStatus,
    Party,
    RiskLevel,
    _generate_id,
    _now_iso,
)

logger = logging.getLogger(__name__)


class AgreementIntelligenceRuntime:
    """Universal Agreement Intelligence — single capability runtime."""

    def __init__(self) -> None:
        self._engine = AgreementIntelligenceEngine()
        self._profiles: dict[str, AgreementProfile] = {}
        self._reality_listeners: list[Callable[[dict[str, Any]], None]] = []

    def get_or_create_profile(self, owner_id: str, label: str = "") -> AgreementProfile:
        if owner_id in self._profiles:
            return self._profiles[owner_id]
        profile = AgreementProfile(
            owner_id=owner_id,
            label=label or f"Agreement profile for {owner_id}",
        )
        self._profiles[profile.profile_id] = profile
        return profile

    def get_profile(self, profile_id: str) -> AgreementProfile | None:
        return self._profiles.get(profile_id)

    # ── Agreement CRUD ──────────────────────────────────────────────────

    def create_agreement(
        self,
        profile_id: str,
        agreement_type: str = AgreementType.SERVICE.value,
        title: str = "",
        purpose: str = "",
        parties: list[dict[str, Any]] | None = None,
        obligations: list[dict[str, Any]] | None = None,
        conditions: list[dict[str, Any]] | None = None,
        milestones: list[dict[str, Any]] | None = None,
        terms: str = "",
        start_date: str = "",
        end_date: str = "",
        financial_commitments: list[dict[str, Any]] | None = None,
        auto_renew: bool = False,
    ) -> Agreement | None:
        profile = self._profiles.get(profile_id)
        if not profile:
            return None

        agreement = Agreement(
            agreement_type=agreement_type,
            title=title,
            purpose=purpose,
            parties=[Party(**p) for p in (parties or [])],
            obligations=[Obligation(**o) for o in (obligations or [])],
            conditions=[Condition(**c) for c in (conditions or [])],
            milestones=[Milestone(**m) for m in (milestones or [])],
            terms=terms,
            start_date=start_date,
            end_date=end_date,
            financial_commitments=financial_commitments or [],
            auto_renew=auto_renew,
        )
        profile.agreements.append(agreement)
        profile.updated_at = _now_iso()
        self._notify({"type": "agreement.created", "profile_id": profile_id,
                       "agreement_id": agreement.agreement_id, "title": title})
        return agreement

    def get_agreement(self, profile_id: str, agreement_id: str) -> Agreement | None:
        profile = self._profiles.get(profile_id)
        if not profile:
            return None
        for a in profile.agreements:
            if a.agreement_id == agreement_id:
                return a
        return None

    def transition_status(self, profile_id: str, agreement_id: str,
                          new_status: str) -> bool:
        agreement = self.get_agreement(profile_id, agreement_id)
        if not agreement:
            return False
        result = agreement.transition_to(new_status)
        if result:
            self._notify({"type": "agreement.status_changed", "profile_id": profile_id,
                           "agreement_id": agreement_id, "new_status": new_status})
        return result

    # ── Obligation Management ───────────────────────────────────────────

    def add_obligation(self, profile_id: str, agreement_id: str,
                       description: str, party_id: str,
                       due_date: str = "", value: float = 0.0) -> bool:
        agreement = self.get_agreement(profile_id, agreement_id)
        if not agreement:
            return False
        agreement.obligations.append(Obligation(
            description=description, party_id=party_id,
            due_date=due_date, value=value,
        ))
        agreement.updated_at = _now_iso()
        return True

    def update_obligation_status(self, profile_id: str, agreement_id: str,
                                  obligation_id: str, new_status: str) -> bool:
        agreement = self.get_agreement(profile_id, agreement_id)
        if not agreement:
            return False
        for o in agreement.obligations:
            if o.obligation_id == obligation_id:
                o.status = new_status
                if new_status == ObligationStatus.FULFILLED.value:
                    o.fulfilled_date = _now_iso()
                agreement.updated_at = _now_iso()
                self._notify({"type": "agreement.obligation_updated",
                               "agreement_id": agreement_id,
                               "obligation_id": obligation_id, "status": new_status})
                return True
        return False

    # ── Analysis ────────────────────────────────────────────────────────

    def analyze_agreement(self, profile_id: str, agreement_id: str) -> dict[str, Any] | None:
        """Full analysis of an agreement with all intelligence capabilities."""
        agreement = self.get_agreement(profile_id, agreement_id)
        if not agreement:
            return None

        return {
            "agreement": agreement.to_dict(),
            "obligations": self._engine.discover_obligations(agreement),
            "fulfilment": self._engine.monitor_fulfilment(agreement),
            "breaches": self._engine.detect_breaches(agreement),
            "dependencies": self._engine.analyze_dependencies(agreement),
            "compliance": self._engine.reason_about_compliance(agreement),
            "financial": self._engine.analyze_financial_obligations(agreement),
            "risks": self._engine.score_risks(agreement),
            "trust": self._engine.assess_trust_impact(agreement),
            "progress": self._engine.assess_execution_progress(agreement),
            "expiry": self._engine.predict_expiry(agreement),
        }

    def get_recommendations(self, profile_id: str, agreement_id: str) -> list[dict[str, Any]]:
        agreement = self.get_agreement(profile_id, agreement_id)
        if not agreement:
            return []

        recs: list[AgreementRecommendation] = []
        recs.extend(self._engine.reason_about_amendments(agreement))
        renewal = self._engine.recommend_renewal(agreement)
        if renewal:
            recs.append(renewal)

        return [r.to_dict() for r in recs]

    def get_ai_context(self, profile_id: str, agreement_id: str) -> dict[str, Any] | None:
        agreement = self.get_agreement(profile_id, agreement_id)
        if not agreement:
            return None
        return self._engine.prepare_ai_context(agreement)

    # ── Reality Integration ─────────────────────────────────────────────

    def notify(self, notification: dict[str, Any]) -> None:
        ntype = notification.get("type", "")
        if ntype == "agreement.obligation_fulfilled":
            pid = notification.get("profile_id", "")
            aid = notification.get("agreement_id", "")
            oid = notification.get("obligation_id", "")
            if pid and aid and oid:
                self.update_obligation_status(pid, aid, oid, ObligationStatus.FULFILLED.value)

    def initialize(self) -> None:
        logger.info("AgreementIntelligenceRuntime initialized")
    def shutdown(self) -> None:
        self._profiles.clear()
        self._reality_listeners.clear()
        logger.info("AgreementIntelligenceRuntime shut down")
    def health_check(self) -> dict[str, Any]:
        return {"status": "healthy", "runtime": "agreement_intelligence",
                "profile_count": len(self._profiles)}
    def handle_event(self, event: Any) -> None:
        if isinstance(event, dict):
            self.notify(event)
    def get_capabilities(self) -> list[str]:
        return ["agreement.profile", "agreement.create", "agreement.analyze",
                "agreement.obligations", "agreement.breaches", "agreement.risks",
                "agreement.renewal", "agreement.trust", "agreement.reality_integration"]

    def _notify(self, notification: dict[str, Any]) -> None:
        for listener in self._reality_listeners:
            try:
                listener(notification)
            except Exception:
                logger.exception("Listener failed")
    def register_reality_listener(self, listener: Callable[[dict[str, Any]], None]) -> None:
        self._reality_listeners.append(listener)
    def unregister_reality_listener(self, listener: Callable[[dict[str, Any]], None]) -> None:
        if listener in self._reality_listeners:
            self._reality_listeners.remove(listener)