"""Universal Relationship Intelligence — Runtime.

The RelationshipIntelligenceRuntime is the canonical UCP-02 runtime.
It integrates all relationship capabilities through a single interface:

- Relationship graph (via RelationshipEngine)
- Trust scoring
- Sentiment tracking
- Interaction & communication history
- Shared journeys, documents, creative assets, commitments
- Relationship health
- AI-powered understanding & insights
- Recommendations
- Reality integration via notify(notification)
- Adaptive execution integration

Every domain (CRM, HR, Healthcare, Education, etc.) composes from this runtime.
No domain-specific module should contain relationship logic.
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from typing import Any

from core.relationship_intelligence.engine import (
    RelationshipIntelligenceEngine,
)
from core.relationship_intelligence.models import (
    CommunicationRecord,
    Insight,
    InteractionRecord,
    Recommendation,
    RelationshipProfile,
    SentimentRecord,
    SharedCommitment,
    SharedCreativeAsset,
    SharedDocument,
    SharedJourney,
    TrustScore,
    _generate_id,
    _now_iso,
)
from core.relationship_intelligence.provider import (
    RelationshipAIProvider,
)
from core.relationship.models import (
    Relationship,
    RelationshipDirection,
    RelationshipStatus,
    RelationshipType,
)
from core.relationship.engine import (
    RelationshipEngine,
    get_relationship_engine,
)

logger = logging.getLogger(__name__)


class RelationshipIntelligenceRuntime:
    """Universal Relationship Intelligence — single capability runtime.

    Orchestrates the relationship graph, intelligence engine, AI providers,
    Reality notifications, and adaptive execution into one coherent interface.

    Usage:
        runtime = RelationshipIntelligenceRuntime()
        profile = runtime.get_or_create_profile(
            source_id="person_abc", target_id="org_xyz", role="customer"
        )

        # Record communication
        runtime.record_communication(profile.profile_id, ...)

        # Assess health
        health = runtime.assess_relationship_health(profile.profile_id)

        # Get recommendations
        recs = runtime.get_recommendations(profile.profile_id)
    """

    def __init__(
        self,
        relationship_engine: RelationshipEngine | None = None,
        ai_provider: RelationshipAIProvider | None = None,
    ) -> None:
        self._graph = relationship_engine or get_relationship_engine()
        self._engine = RelationshipIntelligenceEngine()
        # AI provider is optional — when None, the engine's built-in
        # heuristic methods are used directly. Set a custom provider to
        # override with LLM-based or service-based analysis.
        self._ai_provider: RelationshipAIProvider | None = ai_provider
        # In-memory profile store (replaced by persistent store in production)
        self._profiles: dict[str, RelationshipProfile] = {}
        self._reality_listeners: list[Callable[[dict[str, Any]], None]] = []

    # ── Profile Management ──────────────────────────────────────────────

    def get_or_create_profile(
        self,
        source_id: str,
        target_id: str,
        role: str = "customer",
        label: str = "",
    ) -> RelationshipProfile:
        """Get or create a relationship intelligence profile between two entities.

        Also ensures a corresponding Relationship exists in the graph engine.
        """
        profile_id = self._resolve_profile_id(source_id, target_id)

        if profile_id in self._profiles:
            return self._profiles[profile_id]

        # Create the profile
        profile = RelationshipProfile(
            source_id=source_id,
            target_id=target_id,
            role=role,
            label=label or f"Relationship between {source_id} and {target_id}",
        )
        self._profiles[profile.profile_id] = profile

        # Also add a graph relationship
        try:
            self._graph.add_relationship(
                source_id=source_id,
                target_id=target_id,
                relationship_type=role_to_type(role),
                direction=RelationshipDirection.BIDIRECTIONAL,
                label=profile.label,
                metadata={"profile_id": profile.profile_id, "role": role},
            )
        except (ValueError, KeyError):
            logger.debug("Graph relationship already exists or invalid role type")

        self._notify(notification={
            "type": "relationship_intelligence.profile_created",
            "profile_id": profile.profile_id,
            "source_id": source_id,
            "target_id": target_id,
            "role": role,
        })

        return profile

    def get_profile(self, profile_id: str) -> RelationshipProfile | None:
        """Get an existing profile by ID."""
        return self._profiles.get(profile_id)

    def get_profile_by_entities(self, source_id: str, target_id: str) -> RelationshipProfile | None:
        """Find a profile by entity pair."""
        profile_id = self._resolve_profile_id(source_id, target_id)
        return self._profiles.get(profile_id)

    def list_profiles_by_entity(self, entity_id: str) -> list[RelationshipProfile]:
        """Return all profiles involving an entity."""
        return [
            p for p in self._profiles.values()
            if p.source_id == entity_id or p.target_id == entity_id
        ]

    # ── Trust ───────────────────────────────────────────────────────────

    def compute_trust(self, profile_id: str,
                      context: dict[str, Any] | None = None) -> TrustScore | None:
        """Compute trust score for a relationship profile."""
        profile = self._profiles.get(profile_id)
        if not profile:
            return None
        trust = self._engine.compute_trust(profile, context)
        profile.trust = trust
        profile.updated_at = _now_iso()
        return trust

    # ── Sentiment ───────────────────────────────────────────────────────

    def record_sentiment(
        self,
        profile_id: str,
        score: float,
        magnitude: float = 0.0,
        source: str = "ai_analysis",
        context: str = "",
        metadata: dict[str, Any] | None = None,
    ) -> SentimentRecord | None:
        """Record a sentiment observation for a relationship."""
        profile = self._profiles.get(profile_id)
        if not profile:
            return None

        record = SentimentRecord(
            relationship_id=profile_id,
            score=max(-1.0, min(1.0, score)),
            magnitude=max(0.0, min(1.0, magnitude)),
            source=source,
            context=context,
            metadata=metadata or {},
        )
        profile.sentiment_history.append(record)
        profile.updated_at = _now_iso()

        self._notify(notification={
            "type": "relationship_intelligence.sentiment_recorded",
            "profile_id": profile_id,
            "score": score,
            "source": source,
        })

        return record

    # ── Communication History ───────────────────────────────────────────

    def record_communication(
        self,
        profile_id: str,
        channel: str = "",
        direction: str = "bidirectional",
        subject: str = "",
        summary: str = "",
        sentiment_score: float = 0.0,
        duration_minutes: float = 0.0,
        participants: list[str] | None = None,
        attachments: list[str] | None = None,
        occurred_at: str | None = None,
    ) -> CommunicationRecord | None:
        """Record a communication event within a relationship."""
        profile = self._profiles.get(profile_id)
        if not profile:
            return None

        record = CommunicationRecord(
            relationship_id=profile_id,
            channel=channel,
            direction=direction,
            subject=subject,
            summary=summary,
            sentiment_score=sentiment_score,
            duration_minutes=duration_minutes,
            participants=participants or [],
            attachments=attachments or [],
            occurred_at=occurred_at or _now_iso(),
        )
        profile.communications.append(record)
        profile.updated_at = _now_iso()

        self._notify(notification={
            "type": "relationship_intelligence.communication_recorded",
            "profile_id": profile_id,
            "channel": channel,
        })

        return record

    # ── Interaction History ─────────────────────────────────────────────

    def record_interaction(
        self,
        profile_id: str,
        interaction_type: str = "observation",
        description: str = "",
        outcome: str = "",
        value: str = "",
        entities_involved: list[str] | None = None,
        evidence_ids: list[str] | None = None,
    ) -> InteractionRecord | None:
        """Record an interaction within a relationship."""
        profile = self._profiles.get(profile_id)
        if not profile:
            return None

        record = InteractionRecord(
            relationship_id=profile_id,
            interaction_type=interaction_type,
            description=description,
            outcome=outcome,
            value=value,
            entities_involved=entities_involved or [],
            evidence_ids=evidence_ids or [],
        )
        profile.interactions.append(record)
        profile.updated_at = _now_iso()

        return record

    # ── Shared Journeys ─────────────────────────────────────────────────

    def add_journey(
        self,
        profile_id: str,
        name: str,
        phase: str = "",
        description: str = "",
        milestones: list[dict[str, Any]] | None = None,
    ) -> SharedJourney | None:
        """Add a shared journey to a relationship."""
        profile = self._profiles.get(profile_id)
        if not profile:
            return None

        journey = SharedJourney(
            relationship_id=profile_id,
            name=name,
            phase=phase,
            description=description,
            milestones=milestones or [],
            started_at=_now_iso(),
        )
        profile.journeys.append(journey)
        profile.updated_at = _now_iso()

        self._notify(notification={
            "type": "relationship_intelligence.journey_added",
            "profile_id": profile_id,
            "journey_name": name,
            "phase": phase,
        })

        return journey

    # ── Shared Documents ────────────────────────────────────────────────

    def add_document(
        self,
        profile_id: str,
        title: str,
        doc_type: str = "",
        url: str = "",
        shared_by: str = "",
        shared_with: list[str] | None = None,
    ) -> SharedDocument | None:
        """Record a shared document within a relationship."""
        profile = self._profiles.get(profile_id)
        if not profile:
            return None

        doc = SharedDocument(
            relationship_id=profile_id,
            title=title,
            doc_type=doc_type,
            url=url,
            shared_by=shared_by,
            shared_with=shared_with or [],
        )
        profile.documents.append(doc)
        profile.updated_at = _now_iso()

        return doc

    # ── Shared Creative Assets ──────────────────────────────────────────

    def add_creative_asset(
        self,
        profile_id: str,
        title: str,
        asset_type: str = "",
        url: str = "",
        contributors: list[str] | None = None,
    ) -> SharedCreativeAsset | None:
        """Record a shared creative asset within a relationship."""
        profile = self._profiles.get(profile_id)
        if not profile:
            return None

        asset = SharedCreativeAsset(
            relationship_id=profile_id,
            title=title,
            asset_type=asset_type,
            url=url,
            contributors=contributors or [],
        )
        profile.creative_assets.append(asset)
        profile.updated_at = _now_iso()

        return asset

    # ── Shared Commitments ──────────────────────────────────────────────

    def add_commitment(
        self,
        profile_id: str,
        title: str,
        description: str = "",
        commitment_type: str = "agreement",
        due_date: str | None = None,
        value: str = "",
        parties: list[str] | None = None,
        evidence_ids: list[str] | None = None,
    ) -> SharedCommitment | None:
        """Record a shared commitment within a relationship."""
        profile = self._profiles.get(profile_id)
        if not profile:
            return None

        commitment = SharedCommitment(
            relationship_id=profile_id,
            title=title,
            description=description,
            commitment_type=commitment_type,
            due_date=due_date,
            value=value,
            parties=parties or [],
            evidence_ids=evidence_ids or [],
        )
        profile.commitments.append(commitment)
        profile.updated_at = _now_iso()

        self._notify(notification={
            "type": "relationship_intelligence.commitment_added",
            "profile_id": profile_id,
            "commitment_id": commitment.commitment_id,
            "title": title,
        })

        return commitment

    def update_commitment_status(
        self,
        profile_id: str,
        commitment_id: str,
        new_status: str,
        fulfilled_date: str | None = None,
    ) -> bool:
        """Update the status of a shared commitment."""
        profile = self._profiles.get(profile_id)
        if not profile:
            return False

        for commitment in profile.commitments:
            if commitment.commitment_id == commitment_id:
                commitment.status = new_status
                if fulfilled_date:
                    commitment.fulfilled_date = fulfilled_date
                commitment.updated_at = _now_iso()
                profile.updated_at = _now_iso()

                self._notify(notification={
                    "type": "relationship_intelligence.commitment_status_changed",
                    "profile_id": profile_id,
                    "commitment_id": commitment_id,
                    "status": new_status,
                })
                return True
        return False

    # ── Relationship Health ─────────────────────────────────────────────

    def assess_relationship_health(self, profile_id: str) -> dict[str, Any] | None:
        """Assess composite health for a relationship profile."""
        profile = self._profiles.get(profile_id)
        if not profile:
            return None

        health = self._engine.assess_health(profile)
        profile.health = health
        profile.updated_at = _now_iso()

        # Auto-generate insights during health assessment
        new_insights = self._engine.generate_insights(profile)
        profile.insights = new_insights

        self._notify(notification={
            "type": "relationship_intelligence.health_assessed",
            "profile_id": profile_id,
            "overall_score": health.overall_score,
            "risk_level": health.risk_level,
            "trend": health.trend,
        })

        return health.to_dict()

    def get_cached_health(self, profile_id: str) -> dict[str, Any] | None:
        """Get the current health assessment from cache without re-computing.

        Returns the last computed health assessment. If none exists,
        performs a fresh assessment and returns it.
        """
        profile = self._profiles.get(profile_id)
        if not profile:
            return None
        if profile.health:
            return profile.health.to_dict()
        return self.assess_relationship_health(profile_id)

    # ── AI Understanding ────────────────────────────────────────────────

    def get_ai_insights(self, profile_id: str) -> list[dict[str, Any]] | None:
        """Get AI-powered insights for a relationship.

        When a custom AI provider is configured, its analysis is used.
        Otherwise the engine's built-in heuristic insight generation applies.
        """
        profile = self._profiles.get(profile_id)
        if not profile:
            return None

        if self._ai_provider is not None:
            insights = self._ai_provider.generate_insights(profile)
        else:
            insights = [i.to_dict() for i in self._engine.generate_insights(profile)]

        # Convert and store
        parsed: list[Insight] = []
        for ins in insights:
            insight = Insight(
                relationship_id=profile_id,
                category=ins.get("category", "observation"),
                title=ins.get("title", ""),
                description=ins.get("description", ""),
                evidence=ins.get("evidence", []),
                confidence=ins.get("confidence", 0.0),
                actionable=ins.get("actionable", False),
                action_suggestion=ins.get("action_suggestion", ""),
            )
            parsed.append(insight)
        profile.insights = parsed
        return [i.to_dict() for i in parsed]

    def get_ai_context(self, profile_id: str) -> dict[str, Any] | None:
        """Get structured context for an AI provider."""
        profile = self._profiles.get(profile_id)
        if not profile:
            return None
        return self._engine.prepare_ai_context(profile)

    # ── Recommendations ─────────────────────────────────────────────────

    def get_recommendations(self, profile_id: str) -> list[dict[str, Any]] | None:
        """Get actionable recommendations for a relationship.

        When a custom AI provider is configured, its recommendations are used.
        Otherwise the engine's built-in heuristic recommendations apply.
        """
        profile = self._profiles.get(profile_id)
        if not profile:
            return None

        if self._ai_provider is not None:
            recs = self._ai_provider.generate_recommendations(profile)
        else:
            recs = [r.to_dict() for r in self._engine.generate_recommendations(profile)]

        parsed: list[Recommendation] = []
        for rec in recs:
            recommendation = Recommendation(
                relationship_id=profile_id,
                priority=rec.get("priority", "medium"),
                category=rec.get("category", ""),
                title=rec.get("title", ""),
                description=rec.get("description", ""),
                expected_impact=rec.get("expected_impact", ""),
                effort=rec.get("effort", "medium"),
            )
            parsed.append(recommendation)
        profile.recommendations = parsed
        return [r.to_dict() for r in parsed]

    # ── Reality Integration ─────────────────────────────────────────────

    def notify(self, notification: dict[str, Any]) -> None:
        """Handle Reality notifications for relationship intelligence.

        This is the single public interface for Reality integration.
        Unknown notification types are silently ignored (contract).

        Supported notification types:
        - relationship_intelligence.* (internal)
        - execution.commitment_fulfilled
        - execution.task_completed
        - observation.created
        - communication.received
        """
        notification_type = notification.get("type", "")

        if notification_type == "execution.commitment_fulfilled":
            profile_id = notification.get("profile_id", "")
            commitment_id = notification.get("commitment_id", "")
            if profile_id and commitment_id:
                self.update_commitment_status(
                    profile_id, commitment_id, "fulfilled"
                )

        elif notification_type == "communication.received":
            profile_id = notification.get("profile_id", "")
            if profile_id:
                self.record_communication(
                    profile_id=profile_id,
                    channel=notification.get("channel", "unknown"),
                    summary=notification.get("summary", ""),
                    occurred_at=notification.get("occurred_at"),
                )

        elif notification_type == "observation.created":
            profile_id = notification.get("profile_id", "")
            if profile_id:
                self.record_interaction(
                    profile_id=profile_id,
                    interaction_type="observation",
                    description=notification.get("description", ""),
                )
        # Unknown types silently ignored (contract)

    # ── Adaptive Execution Integration ──────────────────────────────────

    def create_execution_context(self, profile_id: str) -> dict[str, Any]:
        """Create an execution context for adaptive execution runtime.

        Returns data that the ExecutionRuntime can use to schedule
        relationship-related actions (follow-ups, check-ins, reviews).
        """
        profile = self._profiles.get(profile_id)
        if not profile:
            return {"profile_id": profile_id, "error": "Profile not found"}

        health = self._engine.assess_health(profile)
        recs = self._engine.generate_recommendations(profile)

        return {
            "profile_id": profile_id,
            "source_id": profile.source_id,
            "target_id": profile.target_id,
            "role": profile.role,
            "health_overall": health.overall_score,
            "risk_level": health.risk_level,
            "trend": health.trend,
            "recommendations_count": len(recs),
            "priority_recommendations": [
                r.title for r in recs if r.priority in ("critical", "high")
            ],
            "active_commitments": [
                {"title": c.title, "due_date": c.due_date, "status": c.status}
                for c in profile.active_commitments
            ],
        }

    # ── Data Export ─────────────────────────────────────────────────────

    def get_profile_as_dict(self, profile_id: str) -> dict[str, Any] | None:
        """Get a full profile as a plain dict (for APIs, export, projection)."""
        profile = self._profiles.get(profile_id)
        if not profile:
            return None
        return profile.to_dict()

    # ── Engine Lifecycle (core.runtime.models.Engine contract) ──────────

    def initialize(self) -> None:
        """Initialize the relationship intelligence runtime.

        No-op for in-memory mode. Subclasses/persistent adapters
        should override to open databases, connect to AI services, etc.
        """
        logger.info("RelationshipIntelligenceRuntime initialized")

    def shutdown(self) -> None:
        """Gracefully shut down the runtime.

        Clears in-memory state. Subclasses should override for
        connection cleanup and flush operations.
        """
        self._profiles.clear()
        self._reality_listeners.clear()
        logger.info("RelationshipIntelligenceRuntime shut down")

    def health_check(self) -> dict[str, Any]:
        """Return health status of the runtime."""
        return {
            "status": "healthy",
            "runtime": "relationship_intelligence",
            "profile_count": len(self._profiles),
            "listener_count": len(self._reality_listeners),
        }

    def handle_event(self, event: Any) -> None:
        """Process a runtime event dispatched by the kernel.

        Delegates to notify() for Reality integration.
        """
        if isinstance(event, dict):
            self.notify(event)

    def get_capabilities(self) -> list[str]:
        """Return the list of capabilities this runtime provides."""
        return [
            "relationship.profile",
            "relationship.trust",
            "relationship.sentiment",
            "relationship.communication",
            "relationship.interaction",
            "relationship.journey",
            "relationship.document",
            "relationship.creative_asset",
            "relationship.commitment",
            "relationship.health",
            "relationship.insights",
            "relationship.recommendations",
            "relationship.reality_integration",
            "relationship.execution_integration",
        ]

    # ── Internal ────────────────────────────────────────────────────────

    def _resolve_profile_id(self, source_id: str, target_id: str) -> str:
        """Generate a deterministic profile ID from entity pair."""
        import hashlib
        key = "|".join(sorted([source_id, target_id]))
        return f"rel_{hashlib.md5(key.encode()).hexdigest()[:12]}"

    def _notify(self, notification: dict[str, Any]) -> None:
        """Emit a Reality notification.

        This is the runtime's own notify method — it calls registered
        handlers and any connected event bus. The contract is:
        unknown types are silently ignored by consumers.
        """
        # In-memory: fire to registered Reality listeners
        for listener in self._reality_listeners:
            try:
                listener(notification)
            except Exception:
                logger.exception("Reality listener failed for notification")

    # ── Reality Listener Registration ───────────────────────────────────

    def register_reality_listener(self, listener: Callable[[dict[str, Any]], None]) -> None:
        """Register a Reality listener for notifications."""
        self._reality_listeners.append(listener)

    def unregister_reality_listener(self, listener: Callable[[dict[str, Any]], None]) -> None:
        """Remove a Reality listener."""
        if listener in self._reality_listeners:
            self._reality_listeners.remove(listener)


# ── Role-to-Type mapping ──────────────────────────────────────────────────

_ROLE_TYPE_MAP: dict[str, str] = {
    "customer": "relates_to",
    "prospect": "relates_to",
    "employee": "works_at",
    "candidate": "relates_to",
    "supplier": "relates_to",
    "partner": "relates_to",
    "investor": "relates_to",
    "advisor": "relates_to",
    "mentor": "mentor",
    "student": "member_of",
    "teacher": "member_of",
    "doctor": "relates_to",
    "patient": "relates_to",
    "family": "family",
    "friend": "friend",
    "government": "relates_to",
    "community": "member_of",
    "organization": "member_of",
}


def role_to_type(role: str) -> RelationshipType:
    """Map a relationship role to the canonical RelationshipType."""
    mapped = _ROLE_TYPE_MAP.get(role, "relates_to")
    try:
        return RelationshipType(mapped)
    except ValueError:
        return RelationshipType.RELATED_TO