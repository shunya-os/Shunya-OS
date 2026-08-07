"""Universal Relationship Intelligence — Core Engine.

The RelationshipIntelligenceEngine is the analytical core of UCP-02.
It computes trust scores, sentiment trends, relationship health,
AI-powered insights, and actionable recommendations.

Pure computation — no storage, no side effects.
Designed to be called by the runtime and consumed by any domain.
"""

from __future__ import annotations

from typing import Any

from core.relationship_intelligence.models import (
    CommitmentStatus,
    CommunicationRecord,
    HealthDimension,
    Insight,
    InteractionRecord,
    InteractionType,
    Recommendation,
    RelationshipHealth,
    RelationshipProfile,
    SentimentRecord,
    SentimentTrend,
    SharedCommitment,
    TrustLevel,
    TrustScore,
    _generate_id,
    _now_iso,
)


class RelationshipIntelligenceEngine:
    """Computes trust, sentiment, health, insights, and recommendations.

    Every method is a pure function: input → output, no state.
    Thread-safe by design.
    """

    # ── Trust Computation ────────────────────────────────────────────────

    def compute_trust(
        self,
        profile: RelationshipProfile,
        context: dict[str, Any] | None = None,
    ) -> TrustScore:
        """Compute a comprehensive trust score from relationship evidence.

        Evaluates four trust dimensions:
        - Reliability: consistency of behaviour over time
        - Integrity: honesty and adherence to shared values
        - Competence: ability to deliver on commitments
        - Benevolence: genuine care and goodwill
        """
        reliability = self._compute_reliability(profile)
        integrity = self._compute_integrity(profile)
        competence = self._compute_competence(profile)
        benevolence = self._compute_benevolence(profile)

        weights = {"reliability": 0.30, "integrity": 0.30, "competence": 0.25, "benevolence": 0.15}

        score = (
            reliability * weights["reliability"]
            + integrity * weights["integrity"]
            + competence * weights["competence"]
            + benevolence * weights["benevolence"]
        )

        level = self._trust_level_from_score(score)

        return TrustScore(
            relationship_id=profile.profile_id,
            level=level,
            score=round(score, 4),
            reliability=round(reliability, 4),
            integrity=round(integrity, 4),
            competence=round(competence, 4),
            benevolence=round(benevolence, 4),
            scored_by="relationship_intelligence_engine",
            context=context or {},
        )

    def _compute_reliability(self, profile: RelationshipProfile) -> float:
        """Consistency: communication regularity, commitment follow-through."""
        if not profile.communications and not profile.commitments:
            return 0.3  # neutral starting point

        score = 0.5  # baseline
        total_comm = len(profile.communications)
        total_interactions = len(profile.interactions)

        # More history = more data to assess reliability
        if total_comm + total_interactions > 0:
            recency_bonus = min(0.2, (total_comm + total_interactions) * 0.01)
            score += recency_bonus

        # Commitment fulfillment is the strongest reliability signal
        fulfilled_commitments = sum(
            1 for c in profile.commitments
            if c.status == CommitmentStatus.FULFILLED.value
        )
        broken_commitments = sum(
            1 for c in profile.commitments
            if c.status == CommitmentStatus.BROKEN.value
        )
        total_concluded = fulfilled_commitments + broken_commitments
        if total_concluded > 0:
            fulfillment_ratio = fulfilled_commitments / total_concluded
            score += (fulfillment_ratio - 0.5) * 0.3

        if broken_commitments > 0:
            score -= min(0.3, broken_commitments * 0.1)

        return max(0.0, min(1.0, score))

    def _compute_integrity(self, profile: RelationshipProfile) -> float:
        """Honesty: truthfulness in communications, alignment of words and actions."""
        score = 0.5  # baseline

        # Integrity is primarily demonstrated through commitment behaviour
        broken_pct = 0.0
        concluded = [
            c for c in profile.commitments
            if c.status in (
                CommitmentStatus.FULFILLED.value,
                CommitmentStatus.PARTIALLY_FULFILLED.value,
                CommitmentStatus.BROKEN.value,
                CommitmentStatus.CANCELLED.value,
            )
        ]
        if concluded:
            broken = sum(1 for c in concluded if c.status == CommitmentStatus.BROKEN.value)
            broken_pct = broken / len(concluded)
            score -= broken_pct * 0.4

        # Renegotiated commitments are positive (integrity = honest renegotiation)
        renegotiated = sum(1 for c in profile.commitments
                          if c.status == CommitmentStatus.RENEGOTIATED.value)
        score += min(0.15, renegotiated * 0.05)

        return max(0.0, min(1.0, score))

    def _compute_competence(self, profile: RelationshipProfile) -> float:
        """Ability: delivering on commitments on time and with quality."""
        if not profile.commitments and not profile.interactions:
            return 0.3

        score = 0.4

        # Fulfilled commitments demonstrate competence
        fulfilled = [c for c in profile.commitments
                     if c.status == CommitmentStatus.FULFILLED.value]
        if fulfilled:
            score += min(0.3, len(fulfilled) * 0.05)

        # Active commitments that are in_progress show ongoing engagement
        in_progress = [c for c in profile.commitments
                       if c.status == CommitmentStatus.IN_PROGRESS.value]
        score += min(0.1, len(in_progress) * 0.02)

        # Interaction outcomes
        positive_outcomes = sum(
            1 for i in profile.interactions
            if "success" in i.outcome.lower() or "completed" in i.outcome.lower()
        )
        if profile.interactions:
            score += min(0.2, (positive_outcomes / len(profile.interactions)) * 0.2)

        return max(0.0, min(1.0, score))

    def _compute_benevolence(self, profile: RelationshipProfile) -> float:
        """Goodwill: genuine care, going beyond transactional interaction."""
        score = 0.4

        # Shared journeys beyond transactional ones
        if len(profile.journeys) > 1:
            score += min(0.15, len(profile.journeys) * 0.05)

        # Creative collaborations indicate deeper relationship
        if profile.creative_assets:
            score += min(0.15, len(profile.creative_assets) * 0.05)

        # Introduction interactions show benevolence
        introductions = sum(
            1 for i in profile.interactions
            if i.interaction_type == InteractionType.INTRODUCTION.value
        )
        score += min(0.1, introductions * 0.03)

        # Length of relationship (via journey milestones)
        for journey in profile.journeys:
            if journey.milestones:
                score += min(0.1, len(journey.milestones) * 0.02)

        return max(0.0, min(1.0, score))

    def _trust_level_from_score(self, score: float) -> TrustLevel:
        if score >= 0.9:
            return TrustLevel.ABSOLUTE
        if score >= 0.75:
            return TrustLevel.HIGH
        if score >= 0.55:
            return TrustLevel.MODERATE
        if score >= 0.35:
            return TrustLevel.CAUTIOUS
        if score >= 0.15:
            return TrustLevel.LOW
        return TrustLevel.UNKNOWN

    # ── Sentiment Analysis ────────────────────────────────────────────────

    def compute_sentiment_trend(self, profile: RelationshipProfile) -> SentimentTrend:
        """Determine the overall sentiment direction from history."""
        if len(profile.sentiment_history) < 2:
            return SentimentTrend.NEUTRAL

        sorted_records = sorted(
            profile.sentiment_history, key=lambda s: s.observed_at
        )
        recent = sorted_records[-min(5, len(sorted_records)):]

        if len(recent) < 2:
            return SentimentTrend.NEUTRAL

        # Calculate slope of recent sentiment scores
        scores = [r.score for r in recent]
        x = list(range(len(scores)))
        n = len(scores)
        slope = (
            (n * sum(x[i] * scores[i] for i in range(n)) - sum(x) * sum(scores))
            / (n * sum(x[i] ** 2 for i in range(n)) - sum(x) ** 2)
            if (n * sum(x[i] ** 2 for i in range(n)) - sum(x) ** 2) != 0
            else 0
        )

        # Check volatility
        if max(scores) - min(scores) > 0.8:
            return SentimentTrend.VOLATILE

        if slope > 0.15:
            return SentimentTrend.IMPROVING
        if slope < -0.15:
            return SentimentTrend.DECLINING
        return SentimentTrend.STABLE

    def compute_average_sentiment(self, profile: RelationshipProfile) -> float:
        """Weighted average sentiment across all observations."""
        if not profile.sentiment_history:
            return 0.0
        recent_weight = 1.5  # recency multiplier
        sorted_records = sorted(
            profile.sentiment_history, key=lambda s: s.observed_at
        )
        total_weight = 0.0
        weighted_sum = 0.0
        for i, record in enumerate(sorted_records):
            w = 1.0 + (recent_weight - 1.0) * (i / max(len(sorted_records) - 1, 1))
            weighted_sum += record.score * w
            total_weight += w
        return weighted_sum / total_weight if total_weight > 0 else 0.0

    # ── Health Assessment ────────────────────────────────────────────────

    def assess_health(self, profile: RelationshipProfile) -> RelationshipHealth:
        """Compute composite relationship health from all available signals.

        Evaluates eight dimensions:
        - Trust: from the trust subsystem
        - Sentiment: average and trend
        - Recency: how recent the last interaction was
        - Consistency: regularity of communication
        - Commitment Fulfillment: rate of commitment completion
        - Communication Volume: density of communication
        - Shared Experiences: breadth of shared activities
        - Mutual Benefit: value exchange symmetry
        """
        trust = self.compute_trust(profile)
        sentiment_trend = self.compute_sentiment_trend(profile)
        avg_sentiment = self.compute_average_sentiment(profile)

        dimensions: dict[str, float] = {}

        # Trust dimension
        dimensions[HealthDimension.TRUST.value] = trust.score

        # Sentiment dimension (normalize from [-1,1] to [0,1])
        dimensions[HealthDimension.SENTIMENT.value] = (avg_sentiment + 1.0) / 2.0

        # Recency dimension
        dimensions[HealthDimension.RECENCY.value] = self._score_recency(profile)

        # Consistency dimension
        dimensions[HealthDimension.CONSISTENCY.value] = self._score_consistency(profile)

        # Commitment fulfillment
        dimensions[HealthDimension.COMMITMENT_FULFILLMENT.value] = (
            profile.commitment_fulfillment_rate
        )

        # Communication volume
        dimensions[HealthDimension.COMMUNICATION_VOLUME.value] = (
            self._score_communication_volume(profile)
        )

        # Shared experiences
        dimensions[HealthDimension.SHARED_EXPERIENCES.value] = (
            self._score_shared_experiences(profile)
        )

        # Mutual benefit
        dimensions[HealthDimension.MUTUAL_BENEFIT.value] = (
            self._score_mutual_benefit(profile)
        )

        # Weighted overall score
        weights = {
            HealthDimension.TRUST.value: 0.25,
            HealthDimension.SENTIMENT.value: 0.15,
            HealthDimension.RECENCY.value: 0.10,
            HealthDimension.CONSISTENCY.value: 0.10,
            HealthDimension.COMMITMENT_FULFILLMENT.value: 0.15,
            HealthDimension.COMMUNICATION_VOLUME.value: 0.05,
            HealthDimension.SHARED_EXPERIENCES.value: 0.10,
            HealthDimension.MUTUAL_BENEFIT.value: 0.10,
        }
        overall = sum(dimensions.get(k, 0.0) * weights.get(k, 0.0) for k in weights)

        # Risk level
        risk_level = self._compute_risk_level(overall, sentiment_trend, profile)

        return RelationshipHealth(
            relationship_id=profile.profile_id,
            overall_score=round(overall, 4),
            dimensions=dimensions,
            trend=sentiment_trend.value,
            risk_level=risk_level,
        )

    def _score_recency(self, profile: RelationshipProfile) -> float:
        """Score based on days since last interaction."""
        from datetime import datetime, timezone

        now = datetime.now(timezone.utc)
        latest = None
        for comm in profile.communications:
            try:
                dt = datetime.fromisoformat(comm.occurred_at.replace("Z", "+00:00"))
            except (ValueError, AttributeError):
                continue
            if latest is None or dt > latest:
                latest = dt
        for interaction in profile.interactions:
            try:
                dt = datetime.fromisoformat(interaction.occurred_at.replace("Z", "+00:00"))
            except (ValueError, AttributeError):
                continue
            if latest is None or dt > latest:
                latest = dt

        if latest is None:
            return 0.2  # no recent activity

        days_diff = (now - latest).days
        if days_diff <= 7:
            return 1.0
        if days_diff <= 30:
            return 0.8
        if days_diff <= 90:
            return 0.5
        if days_diff <= 365:
            return 0.3
        return 0.1

    def _score_consistency(self, profile: RelationshipProfile) -> float:
        """Score based on regularity of interactions over time."""
        total = len(profile.communications) + len(profile.interactions)
        if total == 0:
            return 0.2
        # Simple heuristic: more total interactions = more consistent
        return min(1.0, 0.3 + total * 0.02)

    def _score_communication_volume(self, profile: RelationshipProfile) -> float:
        """Score based on communication density."""
        total = len(profile.communications)
        if total == 0:
            return 0.0
        return min(1.0, total * 0.05)

    def _score_shared_experiences(self, profile: RelationshipProfile) -> float:
        """Score based on breadth of shared activities."""
        score = 0.0
        if profile.journeys:
            score += min(0.4, len(profile.journeys) * 0.1)
        if profile.documents:
            score += min(0.2, len(profile.documents) * 0.03)
        if profile.creative_assets:
            score += min(0.2, len(profile.creative_assets) * 0.04)
        return min(1.0, score)

    def _score_mutual_benefit(self, profile: RelationshipProfile) -> float:
        """Score based on evidence of bidirectional value exchange."""
        score = 0.3
        # Both parties making commitments
        if profile.commitments:
            # More commitments = more engagement
            score += min(0.2, len(profile.commitments) * 0.02)
        # Shared journeys suggest mutual investment
        if profile.journeys:
            score += min(0.3, len(profile.journeys) * 0.1)
        return min(1.0, score)

    def _compute_risk_level(self, overall: float, trend: SentimentTrend,
                            profile: RelationshipProfile) -> str:
        """Compute risk level based on health score, trend, and warning signs."""
        if overall < 0.3:
            return "critical"
        if overall < 0.5 and trend in (SentimentTrend.DECLINING, SentimentTrend.VOLATILE):
            return "high"
        if overall < 0.5 and trend == SentimentTrend.STABLE:
            return "medium"
        if overall < 0.7 and trend == SentimentTrend.DECLINING:
            return "medium"

        # Check for broken commitments
        broken = sum(1 for c in profile.commitments
                     if c.status == CommitmentStatus.BROKEN.value)
        if broken >= 2:
            return "high"
        if broken >= 1:
            return "medium"

        if overall >= 0.7:
            return "low"
        return "low"

    # ── Insight Generation ───────────────────────────────────────────────

    def generate_insights(self, profile: RelationshipProfile) -> list[Insight]:
        """Generate AI-powered insights about a relationship."""
        insights: list[Insight] = []

        # Pattern: Silence / Stale relationship
        health_result = self.assess_health(profile)
        if health_result.dimensions.get(HealthDimension.RECENCY.value, 1.0) < 0.3:
            insights.append(Insight(
                relationship_id=profile.profile_id,
                category="risk",
                title="Stale relationship — no recent interaction",
                description=(
                    f"Last interaction was too long ago. "
                    f"Regular engagement is needed to maintain relationship quality."
                ),
                confidence=0.85,
                actionable=True,
                action_suggestion="Reach out with a relevant touchpoint",
            ))

        # Pattern: Declining sentiment
        trend = self.compute_sentiment_trend(profile)
        if trend == SentimentTrend.DECLINING:
            insights.append(Insight(
                relationship_id=profile.profile_id,
                category="risk",
                title="Sentiment is declining",
                description=(
                    "Recent interactions show a negative sentiment trend. "
                    "Proactive intervention may be needed."
                ),
                confidence=0.75,
                actionable=True,
                action_suggestion="Investigate root cause and address concerns",
            ))

        # Pattern: High trust but low recency
        if profile.trust and profile.trust.score > 0.7 and health_result.dimensions.get(
                HealthDimension.RECENCY.value, 1.0) < 0.5:
            insights.append(Insight(
                relationship_id=profile.profile_id,
                category="opportunity",
                title="Strong foundation but out of touch",
                description=(
                    "High trust exists but recent engagement is low. "
                    "This is a low-risk opportunity to re-engage."
                ),
                confidence=0.70,
                actionable=True,
                action_suggestion="Schedule a catch-up or share valuable content",
            ))

        # Pattern: Multiple broken commitments
        broken = sum(1 for c in profile.commitments
                     if c.status == CommitmentStatus.BROKEN.value)
        if broken >= 2:
            insights.append(Insight(
                relationship_id=profile.profile_id,
                category="alert",
                title="Recurring commitment failures",
                description=(
                    f"{broken} commitments have been broken. "
                    f"This pattern erodes trust and requires intervention."
                ),
                confidence=0.9,
                actionable=True,
                action_suggestion="Discuss capacity constraints and reset expectations",
            ))

        # Pattern: Strong journey progression
        if len(profile.journeys) >= 2:
            insights.append(Insight(
                relationship_id=profile.profile_id,
                category="observation",
                title="Multiple shared journeys",
                description=(
                    f"The relationship spans {len(profile.journeys)} journeys, "
                    f"indicating depth and duration."
                ),
                confidence=0.8,
                actionable=False,
            ))

        # Pattern: High sentiment volatility
        if len(profile.sentiment_history) >= 3:
            scores = [s.score for s in profile.sentiment_history]
            if max(scores) - min(scores) > 0.8:
                insights.append(Insight(
                    relationship_id=profile.profile_id,
                    category="risk",
                    title="Emotional volatility in relationship",
                    description=(
                        "Sentiment swings widely. "
                        "This suggests inconsistent experiences."
                    ),
                    confidence=0.65,
                    actionable=True,
                    action_suggestion="Identify triggers and stabilize expectations",
                ))

        return insights

    # ── Recommendation Generation ────────────────────────────────────────

    def generate_recommendations(self, profile: RelationshipProfile) -> list[Recommendation]:
        """Generate actionable recommendations for a relationship."""
        recommendations: list[Recommendation] = []
        health_result = self.assess_health(profile)
        insights = self.generate_insights(profile)

        # React to critical/high risk
        if health_result.risk_level == "critical":
            recommendations.append(Recommendation(
                relationship_id=profile.profile_id,
                priority="critical",
                category="reconnect",
                title="Emergency relationship repair needed",
                description="Schedule immediate conversation to address relationship breakdown.",
                expected_impact="Prevents relationship termination",
                effort="high",
            ))

        if health_result.risk_level == "high":
            recommendations.append(Recommendation(
                relationship_id=profile.profile_id,
                priority="high",
                category="reconnect",
                title="Proactive relationship intervention",
                description=(
                    "Conduct a structured review of recent interactions "
                    "and address identified issues."
                ),
                expected_impact="Stabilizes declining relationship",
                effort="medium",
            ))

        # Low recency recommendations
        recency_score = health_result.dimensions.get(HealthDimension.RECENCY.value, 1.0)
        if recency_score < 0.5:
            recommendations.append(Recommendation(
                relationship_id=profile.profile_id,
                priority="high" if recency_score < 0.3 else "medium",
                category="reconnect",
                title="Re-engage with relationship",
                description="Recent interaction is stale. Initiate meaningful contact.",
                expected_impact="Restores engagement and visibility",
                effort="low",
            ))

        # Commitment related recommendations
        active = profile.active_commitments
        overdue_commitments = [
            c for c in active
            if c.due_date
        ]
        if overdue_commitments:
            recommendations.append(Recommendation(
                relationship_id=profile.profile_id,
                priority="high",
                category="fulfill",
                title="Attend to pending commitments",
                description=(
                    f"{len(overdue_commitments)} commitment(s) need attention."
                ),
                expected_impact="Demonstrates reliability and builds trust",
                effort="medium",
            ))

        # Growth recommendations
        if health_result.overall_score >= 0.7 and not profile.creative_assets:
            recommendations.append(Recommendation(
                relationship_id=profile.profile_id,
                priority="medium",
                category="grow",
                title="Explore creative collaboration",
                description=(
                    "Strong relationship foundation — "
                    "propose a collaborative project to deepen engagement."
                ),
                expected_impact="Deepens relationship beyond transactional",
                effort="medium",
            ))

        # Acknowledge recent achievements
        fulfilled = [c for c in profile.commitments
                     if c.status == CommitmentStatus.FULFILLED.value]
        if fulfilled:
            recommendations.append(Recommendation(
                relationship_id=profile.profile_id,
                priority="low",
                category="acknowledge",
                title="Acknowledge fulfilled commitments",
                description="Recognize and appreciate recently delivered commitments.",
                expected_impact="Reinforces positive behaviour and goodwill",
                effort="low",
            ))

        return recommendations

    # ── AI Understanding (text analysis stub for AI provider) ────────────

    def prepare_ai_context(self, profile: RelationshipProfile) -> dict[str, Any]:
        """Prepare structured context for AI understanding providers.

        Returns a dict that can be sent to any AI provider for:
        - Natural language understanding of the relationship
        - Pattern recognition
        - Opportunity identification
        - Communication assistance
        """
        health = self.assess_health(profile)
        trend = self.compute_sentiment_trend(profile)
        trust = profile.trust or self.compute_trust(profile)

        return {
            "relationship_summary": {
                "source_id": profile.source_id,
                "target_id": profile.target_id,
                "role": profile.role,
                "label": profile.label or f"Relationship with {profile.target_id}",
            },
            "health": {
                "overall_score": health.overall_score,
                "risk_level": health.risk_level,
                "trend": trend.value,
                "dimensions": health.dimensions,
            },
            "trust": {
                "level": trust.level.value,
                "score": trust.score,
                "reliability": trust.reliability,
                "integrity": trust.integrity,
                "competence": trust.competence,
                "benevolence": trust.benevolence,
            },
            "engagement": {
                "total_communications": len(profile.communications),
                "total_interactions": len(profile.interactions),
                "total_commitments": len(profile.commitments),
                "fulfillment_rate": profile.commitment_fulfillment_rate,
                "active_commitments": len(profile.active_commitments),
                "journeys": len(profile.journeys),
                "shared_documents": len(profile.documents),
                "creative_assets": len(profile.creative_assets),
            },
            "recent_activity": [
                {
                    "type": "communication",
                    "channel": c.channel,
                    "subject": c.subject,
                    "summary": c.summary,
                    "occurred_at": c.occurred_at,
                }
                for c in (sorted(profile.communications,
                                 key=lambda x: x.occurred_at, reverse=True)[:5])
            ],
            "insights": [i.to_dict() for i in self.generate_insights(profile)],
        }