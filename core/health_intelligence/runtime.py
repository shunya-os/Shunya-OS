"""Universal Health Intelligence — Runtime.

HealthIntelligenceRuntime composes from all frozen UCPs.
No Health Runtime. No Medical Runtime. No Wellness Runtime.
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from typing import Any

from core.health_intelligence.engine import HealthIntelligenceEngine
from core.health_intelligence.models import (
    HealthCondition,
    HealthDimension,
    HealthMetric,
    HealthMetricType,
    HealthProfile,
    HealthRecommendation,
    HealthSeverity,
    HealthStatus,
    WellnessActivity,
    _generate_id,
    _now_iso,
)

logger = logging.getLogger(__name__)


class HealthIntelligenceRuntime:
    """Runtime for Universal Health Intelligence.

    Composes from: Journey, Relationship, Financial, Knowledge, Decision,
    Agreement, Asset, Initiative UCPs via canonical ID references.
    """

    def __init__(self) -> None:
        self._engine = HealthIntelligenceEngine()
        self._profiles: dict[str, HealthProfile] = {}
        self._reality_listeners: list[Callable[[dict[str, Any]], None]] = []

    # ── Profile Management ──────────────────────────────────────────────

    def get_or_create_profile(
        self,
        owner_id: str,
        label: str = "",
        entity_type: str = "individual",
    ) -> HealthProfile:
        for p in self._profiles.values():
            if p.owner_id == owner_id:
                return p
        p = HealthProfile(
            owner_id=owner_id,
            label=label or f"Health profile for {owner_id}",
            entity_type=entity_type,
        )
        self._profiles[p.profile_id] = p
        return p

    def _resolve(self, owner_id: str) -> HealthProfile | None:
        for p in self._profiles.values():
            if p.owner_id == owner_id:
                return p
        return None

    # ── Metric Management ───────────────────────────────────────────────

    def add_metric(
        self,
        owner_id: str,
        metric_type: str = HealthMetricType.CUSTOM.value,
        value: float = 0.0,
        unit: str = "",
        notes: str = "",
        source: str = "",
        evidence_ids: list[str] | None = None,
    ) -> HealthMetric | None:
        profile = self._resolve(owner_id) or self.get_or_create_profile(owner_id)
        metric = HealthMetric(
            metric_type=metric_type,
            value=value,
            unit=unit,
            owner_id=owner_id,
            notes=notes,
            source=source,
            evidence_ids=evidence_ids or [],
        )
        profile.metrics.append(metric)
        profile.updated_at = _now_iso()
        self._notify({
            "type": "health.metric.added",
            "owner_id": owner_id,
            "metric_id": metric.metric_id,
            "metric_type": metric_type,
            "value": value,
        })
        return metric

    # ── Condition Management ────────────────────────────────────────────

    def add_condition(
        self,
        owner_id: str,
        name: str,
        description: str = "",
        dimension: str = HealthDimension.MEDICAL_HISTORY.value,
        severity: str = HealthSeverity.UNKNOWN.value,
        status: str = HealthStatus.UNKNOWN.value,
        diagnosed_at: str = "",
        managed: bool = False,
        notes: str = "",
        evidence_ids: list[str] | None = None,
    ) -> HealthCondition | None:
        profile = self._resolve(owner_id) or self.get_or_create_profile(owner_id)
        condition = HealthCondition(
            name=name,
            description=description,
            dimension=dimension,
            severity=severity,
            status=status,
            diagnosed_at=diagnosed_at,
            owner_id=owner_id,
            managed=managed,
            notes=notes,
            evidence_ids=evidence_ids or [],
        )
        profile.conditions.append(condition)
        profile.updated_at = _now_iso()
        self._notify({
            "type": "health.condition.added",
            "owner_id": owner_id,
            "condition_id": condition.condition_id,
            "name": name,
            "severity": severity,
        })
        return condition

    def update_condition_status(
        self, owner_id: str, condition_id: str, status: str, managed: bool | None = None,
    ) -> bool:
        profile = self._resolve(owner_id)
        if not profile:
            return False
        for c in profile.conditions:
            if c.condition_id == condition_id:
                c.status = status
                if managed is not None:
                    c.managed = managed
                c.updated_at = _now_iso()
                profile.updated_at = _now_iso()
                return True
        return False

    # ── Wellness Activity Management ────────────────────────────────────

    def add_activity(
        self,
        owner_id: str,
        name: str,
        activity_type: str = "exercise",
        dimension: str = HealthDimension.WELLNESS.value,
        duration_minutes: float = 0.0,
        intensity: str = "moderate",
        notes: str = "",
        evidence_ids: list[str] | None = None,
    ) -> WellnessActivity | None:
        profile = self._resolve(owner_id) or self.get_or_create_profile(owner_id)
        activity = WellnessActivity(
            name=name,
            activity_type=activity_type,
            dimension=dimension,
            duration_minutes=duration_minutes,
            intensity=intensity,
            owner_id=owner_id,
            notes=notes,
            evidence_ids=evidence_ids or [],
        )
        profile.activities.append(activity)
        profile.updated_at = _now_iso()
        self._notify({
            "type": "health.activity.added",
            "owner_id": owner_id,
            "activity_id": activity.activity_id,
            "name": name,
            "duration_minutes": duration_minutes,
        })
        return activity

    # ── Composition Links ───────────────────────────────────────────────

    def link_journey(self, owner_id: str, journey_id: str) -> bool:
        profile = self._resolve(owner_id)
        if not profile:
            return False
        if journey_id not in profile.journey_ids:
            profile.journey_ids.append(journey_id)
            profile.updated_at = _now_iso()
        return True

    def link_relationship(self, owner_id: str, relationship_id: str) -> bool:
        profile = self._resolve(owner_id)
        if not profile:
            return False
        if relationship_id not in profile.relationship_ids:
            profile.relationship_ids.append(relationship_id)
            profile.updated_at = _now_iso()
        return True

    def link_financial_profile(self, owner_id: str, financial_profile_id: str) -> bool:
        profile = self._resolve(owner_id)
        if not profile:
            return False
        if financial_profile_id not in profile.financial_profile_ids:
            profile.financial_profile_ids.append(financial_profile_id)
            profile.updated_at = _now_iso()
        return True

    def link_knowledge(self, owner_id: str, knowledge_id: str) -> bool:
        profile = self._resolve(owner_id)
        if not profile:
            return False
        if knowledge_id not in profile.knowledge_ids:
            profile.knowledge_ids.append(knowledge_id)
            profile.updated_at = _now_iso()
        return True

    def link_decision(self, owner_id: str, decision_id: str) -> bool:
        profile = self._resolve(owner_id)
        if not profile:
            return False
        if decision_id not in profile.decision_ids:
            profile.decision_ids.append(decision_id)
            profile.updated_at = _now_iso()
        return True

    def link_agreement(self, owner_id: str, agreement_id: str) -> bool:
        profile = self._resolve(owner_id)
        if not profile:
            return False
        if agreement_id not in profile.agreement_ids:
            profile.agreement_ids.append(agreement_id)
            profile.updated_at = _now_iso()
        return True

    def link_asset(self, owner_id: str, asset_id: str) -> bool:
        profile = self._resolve(owner_id)
        if not profile:
            return False
        if asset_id not in profile.asset_ids:
            profile.asset_ids.append(asset_id)
            profile.updated_at = _now_iso()
        return True

    def link_initiative(self, owner_id: str, initiative_id: str) -> bool:
        profile = self._resolve(owner_id)
        if not profile:
            return False
        if initiative_id not in profile.initiative_ids:
            profile.initiative_ids.append(initiative_id)
            profile.updated_at = _now_iso()
        return True

    # ── Analysis ────────────────────────────────────────────────────────

    def analyze(self, owner_id: str) -> dict[str, Any] | None:
        profile = self._resolve(owner_id)
        if not profile:
            return None

        # Run all engine analyses
        condition_recs = self._engine.analyze_conditions(profile)
        wellness_recs = self._engine.reason_about_wellness(profile)
        preventive_recs = self._engine.analyze_preventive_care(profile)
        mental_recs = self._engine.assess_mental_wellbeing(profile)
        org_recs = self._engine.assess_organizational_health(profile)
        trend_recs = self._engine.analyze_metric_trends(profile)

        all_recs = condition_recs + wellness_recs + preventive_recs + mental_recs + org_recs + trend_recs

        return {
            "profile": profile.to_dict(),
            "health": self._engine.compute_health_score(profile),
            "conditions": [c.to_dict() for c in profile.conditions],
            "metrics": [m.to_dict() for m in profile.recent_metrics(20)],
            "activities": [a.to_dict() for a in profile.recent_activities(20)],
            "recommendations": [r.to_dict() for r in all_recs],
            "condition_recs": [r.to_dict() for r in condition_recs],
            "wellness_recs": [r.to_dict() for r in wellness_recs],
            "preventive_recs": [r.to_dict() for r in preventive_recs],
            "mental_recs": [r.to_dict() for r in mental_recs],
            "organizational_recs": [r.to_dict() for r in org_recs],
            "trend_recs": [r.to_dict() for r in trend_recs],
        }

    def get_recommendations(self, owner_id: str) -> list[dict[str, Any]]:
        profile = self._resolve(owner_id)
        if not profile:
            return []
        recs = (
            self._engine.analyze_conditions(profile)
            + self._engine.reason_about_wellness(profile)
            + self._engine.analyze_preventive_care(profile)
            + self._engine.assess_mental_wellbeing(profile)
            + self._engine.assess_organizational_health(profile)
            + self._engine.analyze_metric_trends(profile)
        )
        return [r.to_dict() for r in recs]

    def adaptive_health_response(
        self, owner_id: str, disruption_description: str,
    ) -> list[dict[str, Any]]:
        profile = self._resolve(owner_id)
        if not profile:
            return []
        recs = self._engine.adaptive_health_response(profile, disruption_description)
        return [r.to_dict() for r in recs]

    # ── Runtime Lifecycle ───────────────────────────────────────────────

    def initialize(self) -> None:
        logger.info("HealthIntelligenceRuntime initialized")

    def shutdown(self) -> None:
        self._profiles.clear()
        self._reality_listeners.clear()

    def health_check(self) -> dict:
        return {
            "status": "healthy",
            "runtime": "health_intelligence",
            "profile_count": len(self._profiles),
        }

    def handle_event(self, event: Any) -> None:
        if isinstance(event, dict):
            self.notify(event)

    def get_capabilities(self) -> list[str]:
        return [
            "health.profile",
            "health.metrics",
            "health.conditions",
            "health.wellness",
            "health.activities",
            "health.assess",
            "health.analyze",
            "health.recommendations",
            "health.preventive",
            "health.mental_wellbeing",
            "health.organizational",
            "health.adaptive_response",
            "health.composition",
            "health.reality_integration",
        ]

    def notify(self, notification: dict[str, Any]) -> None:
        pass

    def _notify(self, n: dict) -> None:
        for l in self._reality_listeners:
            try:
                l(n)
            except Exception:
                pass

    def register_reality_listener(self, l: Callable) -> None:
        self._reality_listeners.append(l)

    def unregister_reality_listener(self, l: Callable) -> None:
        if l in self._reality_listeners:
            self._reality_listeners.remove(l)