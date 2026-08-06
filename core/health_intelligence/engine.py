"""Universal Health Intelligence — Core Engine.

Pure computation: health scoring, condition analysis, wellness reasoning,
preventive care recommendations, mental wellbeing assessment,
organizational/team health evaluation, adaptive health execution.

Composes from frozen UCPs via canonical ID references — no direct runtime calls.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

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


class HealthIntelligenceEngine:
    """Pure computation engine for Universal Health Intelligence."""

    # ── Health Scoring ──────────────────────────────────────────────────

    def compute_health_score(self, profile: HealthProfile) -> dict[str, Any]:
        """Compute an overall health score for a profile (0.0–1.0).

        Factors considered: active conditions, metric trends, wellness
        activity frequency, recommendation adherence, and dimension coverage.
        """
        score = 0.7  # baseline

        # Conditions reduce score based on severity
        for c in profile.active_conditions:
            if c.severity == HealthSeverity.CRITICAL.value:
                score -= 0.25
            elif c.severity == HealthSeverity.HIGH.value:
                score -= 0.15
            elif c.severity == HealthSeverity.MODERATE.value:
                score -= 0.08
            elif c.severity == HealthSeverity.LOW.value:
                score -= 0.03
            # Managed conditions are scored less harshly
            if c.managed:
                score += 0.05

        # Managed conditions are a positive signal
        managed_pct = len(profile.managed_conditions) / max(len(profile.conditions), 1)
        score += managed_pct * 0.1

        # Recent activity boosts score
        recent_activities = len(profile.recent_activities(14))
        score += min(recent_activities * 0.02, 0.15)

        # Recent metrics submitted is a positive signal
        recent_metrics = len(profile.recent_metrics(10))
        if recent_metrics >= 5:
            score += 0.05
        elif recent_metrics >= 2:
            score += 0.02

        # Composition coverage bonus (using multiple UCPs)
        comps = [
            bool(profile.journey_ids),
            bool(profile.relationship_ids),
            bool(profile.financial_profile_ids),
            bool(profile.knowledge_ids),
            bool(profile.decision_ids),
            bool(profile.agreement_ids),
            bool(profile.asset_ids),
            bool(profile.initiative_ids),
        ]
        ucp_count = sum(comps)
        score += min(ucp_count * 0.025, 0.15)

        score = max(0.0, min(1.0, score))

        if score >= 0.8:
            status = HealthStatus.EXCELLENT.value
        elif score >= 0.6:
            status = HealthStatus.GOOD.value
        elif score >= 0.4:
            status = HealthStatus.FAIR.value
        elif score >= 0.2:
            status = HealthStatus.AT_RISK.value
        else:
            status = HealthStatus.CRITICAL.value

        return {
            "score": round(score, 4),
            "status": status,
            "active_conditions": len(profile.active_conditions),
            "managed_conditions": len(profile.managed_conditions),
            "recent_activities": recent_activities,
            "recent_metrics": recent_metrics,
            "composition_count": ucp_count,
        }

    # ── Condition Analysis ──────────────────────────────────────────────

    def analyze_conditions(
        self, profile: HealthProfile,
    ) -> list[HealthRecommendation]:
        """Analyze all conditions and generate recommendations."""
        recs: list[HealthRecommendation] = []
        now = datetime.now(timezone.utc)

        for c in profile.conditions:
            # Critical conditions
            if c.severity == HealthSeverity.CRITICAL.value:
                recs.append(HealthRecommendation(
                    title=f"Critical: {c.name} requires immediate attention",
                    description=c.description or f"{c.name} is at critical severity",
                    priority="critical",
                    reasoning="Critical severity condition demands immediate intervention",
                    confidence=0.9,
                    assumptions=["Condition data is accurate", "Owner has access to care"],
                    alternatives=["Seek emergency care", "Consult specialist"],
                    expected_impact="Stabilization of critical condition",
                    evidence=[{"type": "condition_severity", "condition": c.name, "severity": c.severity}],
                ))

            # High severity — urgent
            elif c.severity == HealthSeverity.HIGH.value:
                recs.append(HealthRecommendation(
                    title=f"Urgent care recommended for {c.name}",
                    description=f"{c.name} is at high severity and needs monitoring",
                    priority="high",
                    reasoning="High severity conditions require consistent monitoring and care",
                    confidence=0.8,
                    assumptions=["Owner has access to healthcare"],
                    alternatives=["Schedule specialist consultation", "Increase monitoring frequency"],
                    expected_impact="Condition stabilization and prevention of escalation",
                    evidence=[{"type": "condition_severity", "condition": c.name, "severity": c.severity}],
                ))

            # Unmanaged conditions
            if not c.managed and c.severity != HealthSeverity.MINIMAL.value:
                recs.append(HealthRecommendation(
                    title=f"Management plan needed for {c.name}",
                    description=f"{c.name} is not actively managed",
                    priority="medium" if c.severity in (HealthSeverity.LOW.value, HealthSeverity.MINIMAL.value) else "high",
                    reasoning="Unmanaged conditions may worsen over time without active care",
                    confidence=0.7,
                    assumptions=["Owner is aware of the condition", "Management resources exist"],
                    alternatives=["Create a care plan", "Set up regular check-ins", "Automated monitoring"],
                    expected_impact="Condition is actively tracked and managed",
                    evidence=[{"type": "unmanaged_condition", "condition": c.name}],
                ))

        return recs

    # ── Wellness Reasoning ──────────────────────────────────────────────

    def reason_about_wellness(
        self, profile: HealthProfile,
    ) -> list[HealthRecommendation]:
        """Analyze wellness activities and generate recommendations."""
        recs: list[HealthRecommendation] = []
        recent = profile.recent_activities(14)

        if len(recent) == 0 and len(profile.activities) > 0:
            recs.append(HealthRecommendation(
                title="No recent wellness activity detected",
                description="No wellness activities recorded in the last 14 days",
                priority="medium",
                reasoning="Regular wellness activity supports all health dimensions",
                confidence=0.75,
                assumptions=["Activities are being recorded consistently"],
                alternatives=["Set a daily activity reminder", "Schedule recurring wellness time"],
                expected_impact="Consistent wellness routine established",
                evidence=[{"type": "no_recent_activity", "days": 14}],
            ))

        # Check dimension diversity
        dimensions_covered = set()
        for a in profile.activities:
            dimensions_covered.add(a.dimension)
        missing_dims = [
            d.value for d in [
                HealthDimension.WELLNESS,
                HealthDimension.PREVENTIVE_CARE,
                HealthDimension.MENTAL_WELLBEING,
            ]
            if d.value not in dimensions_covered and d.value != profile.entity_type
        ]
        if missing_dims and len(profile.activities) >= 3:
            recs.append(HealthRecommendation(
                title=f"Explore wellness in: {', '.join(missing_dims)}",
                description=f"Activities missing from dimensions: {', '.join(missing_dims)}",
                priority="low",
                reasoning="Diverse wellness dimensions provide holistic health benefits",
                confidence=0.6,
                assumptions=["Owner is open to exploring new wellness activities"],
                alternatives=[f"Try a {d} activity" for d in missing_dims],
                expected_impact="More balanced wellness profile across dimensions",
                evidence=[{"type": "missing_dimensions", "dimensions": missing_dims}],
            ))

        return recs

    # ── Preventive Care Analysis ────────────────────────────────────────

    def analyze_preventive_care(
        self, profile: HealthProfile,
    ) -> list[HealthRecommendation]:
        """Analyze preventive care status and generate recommendations."""
        recs: list[HealthRecommendation] = []

        # Check for screening metrics
        has_screening = any(
            m.metric_type == HealthMetricType.SCREENING_DATE.value
            for m in profile.metrics
        )
        if not has_screening and len(profile.metrics) >= 3:
            recs.append(HealthRecommendation(
                title="Schedule a preventive health screening",
                description="No screening records found in health metrics",
                priority="medium",
                reasoning="Regular screenings detect issues before they become serious",
                confidence=0.7,
                assumptions=["Owner has access to screening services"],
                alternatives=["Annual physical exam", "Blood work panel", "Age-appropriate screenings"],
                expected_impact="Early detection of potential health issues",
                evidence=[{"type": "no_screening_record", "metric_count": len(profile.metrics)}],
            ))

        # Check vaccination tracking
        has_vaccination = any(
            m.metric_type == HealthMetricType.VACCINATION_STATUS.value
            for m in profile.metrics
        )
        if not has_vaccination:
            recs.append(HealthRecommendation(
                title="Track vaccination status",
                description="Vaccination status not tracked in health profile",
                priority="medium",
                reasoning="Up-to-date vaccination is a cornerstone of preventive health",
                confidence=0.65,
                assumptions=["Owner has vaccination records available"],
                alternatives=["Add vaccination records", "Set reminder for upcoming vaccines"],
                expected_impact="Complete vaccination tracking for better preventive care",
                evidence=[{"type": "no_vaccination_tracking"}],
            ))

        return recs

    # ── Mental Wellbeing Assessment ─────────────────────────────────────

    def assess_mental_wellbeing(
        self, profile: HealthProfile,
    ) -> list[HealthRecommendation]:
        """Assess mental wellbeing based on available data."""
        recs: list[HealthRecommendation] = []

        stress_metrics = [
            m for m in profile.metrics
            if m.metric_type == HealthMetricType.STRESS_LEVEL.value
        ]
        mood_metrics = [
            m for m in profile.metrics
            if m.metric_type == HealthMetricType.MOOD_SCORE.value
        ]
        mindfulness_metrics = [
            m for m in profile.metrics
            if m.metric_type == HealthMetricType.MINDFULNESS_MINUTES.value
        ]

        # High stress
        high_stress = [m for m in stress_metrics if m.value > 7.0]
        if high_stress:
            avg_stress = sum(m.value for m in high_stress) / len(high_stress)
            recs.append(HealthRecommendation(
                title=f"Elevated stress level detected ({avg_stress:.1f}/10)",
                description="Stress levels consistently above healthy threshold",
                priority="high",
                reasoning="Chronic high stress affects all health dimensions",
                confidence=0.8,
                assumptions=["Stress measurement is accurate", "Causes may be work or life related"],
                alternatives=["Stress management techniques", "Counseling or therapy", "Lifestyle adjustment"],
                expected_impact="Reduced stress levels and improved mental wellbeing",
                evidence=[{"type": "high_stress", "avg_value": avg_stress, "readings": len(high_stress)}],
            ))

        # Low mood
        low_mood = [m for m in mood_metrics if m.value < 4.0]
        if low_mood:
            avg_mood = sum(m.value for m in low_mood) / len(low_mood)
            recs.append(HealthRecommendation(
                title=f"Low mood trend detected ({avg_mood:.1f}/10)",
                description="Mood scores consistently below wellbeing threshold",
                priority="high",
                reasoning="Persistent low mood may indicate underlying mental health concerns",
                confidence=0.75,
                assumptions=["Mood tracking is consistent", "Pattern reflects genuine state"],
                alternatives=["Speak with a mental health professional", "Increase social connections", "Mindfulness practice"],
                expected_impact="Improved mood and emotional wellbeing",
                evidence=[{"type": "low_mood", "avg_value": avg_mood, "readings": len(low_mood)}],
            ))

        # No mindfulness
        if not mindfulness_metrics and len(profile.metrics) >= 5:
            recs.append(HealthRecommendation(
                title="Try mindfulness or meditation",
                description="No mindfulness activity tracked in health profile",
                priority="low",
                reasoning="Regular mindfulness practice improves mental clarity and reduces stress",
                confidence=0.6,
                assumptions=["Owner has time for mindfulness practice"],
                alternatives=["Guided meditation app", "Breathing exercises", "Yoga practice"],
                expected_impact="Improved mental clarity and stress management",
                evidence=[{"type": "no_mindfulness_tracking"}],
            ))

        return recs

    # ── Organizational Health Assessment ────────────────────────────────

    def assess_organizational_health(
        self, profile: HealthProfile,
    ) -> list[HealthRecommendation]:
        """Assess health of an organization or team entity."""
        recs: list[HealthRecommendation] = []

        burnout_metrics = [
            m for m in profile.metrics
            if m.metric_type == HealthMetricType.BURNOUT_RISK.value
        ]
        satisfaction_metrics = [
            m for m in profile.metrics
            if m.metric_type == HealthMetricType.TEAM_SATISFACTION.value
        ]
        absenteeism_metrics = [
            m for m in profile.metrics
            if m.metric_type == HealthMetricType.ABSENTEEISM.value
        ]

        # Burnout risk
        high_burnout = [m for m in burnout_metrics if m.value > 6.0]
        if high_burnout:
            avg_burnout = sum(m.value for m in high_burnout) / len(high_burnout)
            recs.append(HealthRecommendation(
                title=f"Burnout risk elevated ({avg_burnout:.1f}/10)",
                description="Organizational burnout risk above healthy threshold",
                priority="high",
                reasoning="High burnout risk reduces productivity and increases turnover",
                confidence=0.8,
                assumptions=["Burnout metrics reflect organizational sentiment"],
                alternatives=["Workload redistribution", "Wellness programs", "Mental health days policy"],
                expected_impact="Reduced burnout and improved organizational health",
                evidence=[{"type": "burnout_risk", "avg_value": avg_burnout, "readings": len(high_burnout)}],
            ))

        # Low satisfaction
        low_satisfaction = [m for m in satisfaction_metrics if m.value < 5.0]
        if low_satisfaction:
            avg_sat = sum(m.value for m in low_satisfaction) / len(low_satisfaction)
            recs.append(HealthRecommendation(
                title=f"Team satisfaction below target ({avg_sat:.1f}/10)",
                description="Satisfaction scores suggest organizational health concerns",
                priority="high",
                reasoning="Low satisfaction correlates with reduced engagement and retention",
                confidence=0.75,
                assumptions=["Satisfaction data represents team sentiment"],
                alternatives=["Conduct engagement survey", "Improve work environment", "Review compensation"],
                expected_impact="Improved team satisfaction and organizational health",
                evidence=[{"type": "low_satisfaction", "avg_value": avg_sat, "readings": len(low_satisfaction)}],
            ))

        # Absenteeism
        high_absenteeism = [m for m in absenteeism_metrics if m.value > 10.0]
        if high_absenteeism:
            avg_abs = sum(m.value for m in high_absenteeism) / len(high_absenteeism)
            recs.append(HealthRecommendation(
                title=f"Elevated absenteeism ({avg_abs:.1f}%)",
                description="Absenteeism rate above organizational health threshold",
                priority="medium",
                reasoning="High absenteeism may indicate health or workplace issues",
                confidence=0.7,
                assumptions=["Absenteeism data is accurately tracked"],
                alternatives=["Wellness initiative", "Flexible work policy", "Health support programs"],
                expected_impact="Reduced absenteeism and improved workforce health",
                evidence=[{"type": "high_absenteeism", "avg_value": avg_abs, "readings": len(high_absenteeism)}],
            ))

        return recs

    # ── Metric Trend Analysis ───────────────────────────────────────────

    def analyze_metric_trends(
        self, profile: HealthProfile,
    ) -> list[HealthRecommendation]:
        """Analyze trends in health metrics."""
        recs: list[HealthRecommendation] = []

        # Group metrics by type
        by_type: dict[str, list[HealthMetric]] = {}
        for m in profile.metrics:
            by_type.setdefault(m.metric_type, []).append(m)

        for metric_type, metrics in by_type.items():
            if len(metrics) < 3:
                continue

            # Sort by time
            sorted_m = sorted(metrics, key=lambda x: x.recorded_at)
            values = [m.value for m in sorted_m]

            # Simple trend: compare first half to second half
            half = len(values) // 2
            first_half_avg = sum(values[:half]) / half if half > 0 else sum(values) / len(values)
            second_half_avg = sum(values[half:]) / (len(values) - half) if (len(values) - half) > 0 else 0

            delta = second_half_avg - first_half_avg

            # Flag declining trends for positive metrics
            positive_metrics = {
                HealthMetricType.EXERCISE_MINUTES.value,
                HealthMetricType.WATER_INTAKE.value,
                HealthMetricType.STEPS.value,
                HealthMetricType.SLEEP_HOURS.value,
                HealthMetricType.MOOD_SCORE.value,
                HealthMetricType.SOCIAL_INTERACTIONS.value,
                HealthMetricType.MINDFULNESS_MINUTES.value,
            }
            negative_metrics = {
                HealthMetricType.STRESS_LEVEL.value,
                HealthMetricType.BURNOUT_RISK.value,
                HealthMetricType.TURNOVER_RISK.value,
            }

            if metric_type in positive_metrics and delta < -0.5:
                recs.append(HealthRecommendation(
                    title=f"Declining trend in {metric_type}",
                    description=f"{metric_type} has decreased from {first_half_avg:.1f} to {second_half_avg:.1f}",
                    priority="medium",
                    reasoning="Declining trend in positive health metric may need attention",
                    confidence=0.7,
                    assumptions=["Metric data is consistently recorded", "Trend reflects genuine change"],
                    alternatives=["Increase activity in this area", "Set improvement targets", "Consult professional"],
                    expected_impact="Reversed declining trend and improved health metric",
                    evidence=[{"type": "declining_trend", "metric": metric_type, "delta": round(delta, 2)}],
                ))

            elif metric_type in negative_metrics and delta > 0.5:
                recs.append(HealthRecommendation(
                    title=f"Increasing trend in {metric_type}",
                    description=f"{metric_type} has increased from {first_half_avg:.1f} to {second_half_avg:.1f}",
                    priority="medium",
                    reasoning="Rising trend in negative health metric signals potential issue",
                    confidence=0.7,
                    assumptions=["Metric data is consistently recorded", "Trend reflects genuine change"],
                    alternatives=["Implement mitigation strategies", "Seek guidance", "Set reduction targets"],
                    expected_impact="Stabilized or reduced negative metric",
                    evidence=[{"type": "increasing_negative_trend", "metric": metric_type, "delta": round(delta, 2)}],
                ))

        return recs

    # ── Adaptive Health Execution ───────────────────────────────────────

    def adaptive_health_response(
        self, profile: HealthProfile,
        disruption_description: str,
    ) -> list[HealthRecommendation]:
        """Generate adaptive recommendations when health changes disruptively."""
        recs: list[HealthRecommendation] = []

        health = self.compute_health_score(profile)

        if health["status"] in (HealthStatus.AT_RISK.value, HealthStatus.CRITICAL.value):
            recs.append(HealthRecommendation(
                title="Health status requires adaptive response",
                description=(
                    f"Health status is {health['status']}. "
                    f"{disruption_description}"
                ),
                priority="critical",
                reasoning="Disruption requires immediate health adaptation plan",
                confidence=0.85,
                assumptions=["Disruption information is accurate", "Owner can act on recommendations"],
                alternatives=["Rest and recovery plan", "Seek professional medical advice", "Adjust health goals"],
                expected_impact="Adapted health plan addressing the disruption",
                evidence=[
                    {"type": "health_status", "status": health["status"]},
                    {"type": "disruption", "description": disruption_description},
                ],
            ))

        # Active conditions need review during disruption
        if profile.active_conditions:
            condition_names = [c.name for c in profile.active_conditions]
            recs.append(HealthRecommendation(
                title=f"Review {len(condition_names)} active condition(s) during disruption",
                description=f"Active conditions: {', '.join(condition_names)}",
                priority="high",
                reasoning="Disruptions can worsen existing conditions without proactive management",
                confidence=0.8,
                assumptions=["Condition data is current"],
                alternatives=["Prioritize condition management", "Contact care providers", "Increase monitoring"],
                expected_impact="Conditions remain stable despite disruption",
                evidence=[{"type": "active_conditions", "conditions": condition_names}],
            ))

        # Recommendations from other analyses
        if profile.recommendations:
            pending_recs = [
                r for r in profile.recommendations
                if r.priority in ("high", "critical")
            ]
            if pending_recs:
                recs.append(HealthRecommendation(
                    title=f"Complete {len(pending_recs)} pending high-priority recommendation(s)",
                    description="Unresolved high-priority recommendations need attention",
                    priority="high",
                    reasoning="Existing high-priority recommendations may compound disruption impact",
                    confidence=0.7,
                    assumptions=["Recommendations remain relevant"],
                    alternatives=["Review and reprioritize recommendations", "Create new care plan"],
                    expected_impact="Resolved pending recommendations reducing overall risk",
                    evidence=[{"type": "pending_recommendations", "count": len(pending_recs)}],
                ))

        return recs

    # ── Explainable Recommendation ──────────────────────────────────────

    def explain(self, rec: HealthRecommendation) -> dict[str, Any]:
        """Provide a full explanation of a recommendation."""
        return {
            "recommendation": rec.title,
            "description": rec.description,
            "reasoning": rec.reasoning,
            "confidence": rec.confidence,
            "assumptions": list(rec.assumptions),
            "alternatives": list(rec.alternatives),
            "expected_impact": rec.expected_impact,
            "evidence": rec.evidence,
            "explanation": "Based on the following evidence:",
            "evidence_summary": [
                {"basis": e.get("type", ""), "value": e.get("value", str(e))}
                for e in rec.evidence
            ],
        }

    # ── AI Context ──────────────────────────────────────────────────────

    def prepare_ai_context(self, profile: HealthProfile) -> dict[str, Any]:
        """Prepare a comprehensive health context for AI reasoning."""
        health = self.compute_health_score(profile)
        return {
            "profile": {
                "owner_id": profile.owner_id,
                "label": profile.label,
                "entity_type": profile.entity_type,
            },
            "health": health,
            "conditions": [
                {"name": c.name, "severity": c.severity, "status": c.status, "managed": c.managed}
                for c in profile.conditions
            ],
            "metrics_count": len(profile.metrics),
            "activities_count": len(profile.activities),
            "recommendations_count": len(profile.recommendations),
            "composition": {
                "journeys": len(profile.journey_ids),
                "relationships": len(profile.relationship_ids),
                "financial_profiles": len(profile.financial_profile_ids),
                "knowledge": len(profile.knowledge_ids),
                "decisions": len(profile.decision_ids),
                "agreements": len(profile.agreement_ids),
                "assets": len(profile.asset_ids),
                "initiatives": len(profile.initiative_ids),
            },
        }