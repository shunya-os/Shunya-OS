"""Universal Knowledge Intelligence — Runtime.

The KnowledgeIntelligenceRuntime is the canonical UCP-04 runtime.
Composes from frozen SHUNYA platform runtimes:

- Living Object Composer (core/kernel)
- Reality Runtime (core/event + notify pattern)
- Relationship Intelligence (UCP-02)
- Financial Intelligence (UCP-03)
- Universal Execution Runtime (core/execution_runtime)

No Knowledge Runtime. No Wiki Runtime. No Note Runtime.
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from typing import Any

from core.knowledge_intelligence.engine import KnowledgeIntelligenceEngine
from core.knowledge_intelligence.models import (
    ConfidenceLevel,
    Contradiction,
    Knowledge,
    KnowledgeGap,
    KnowledgeGraph,
    KnowledgeLink,
    KnowledgeProfile,
    KnowledgeRecommendation,
    KnowledgeRelationship,
    KnowledgeSource,
    KnowledgeType,
    SearchResult,
    SourceType,
    _generate_id,
    _now_iso,
)

logger = logging.getLogger(__name__)


class KnowledgeIntelligenceRuntime:
    """Universal Knowledge Intelligence — single capability runtime.

    Composes from frozen SHUNYA runtimes — never introduces a
    Knowledge Runtime, Wiki Runtime, or Note Runtime.

    Usage:
        runtime = KnowledgeIntelligenceRuntime()
        profile = runtime.get_or_create_profile(owner_id="org_001")

        # Add knowledge
        runtime.add_knowledge(profile.profile_id, "fact", "Earth orbits the Sun", ...)

        # Search
        results = runtime.search(profile.profile_id, "Earth orbit")

        # Detect contradictions
        contradictions = runtime.detect_contradictions(profile.profile_id)
    """

    def __init__(self) -> None:
        self._engine = KnowledgeIntelligenceEngine()
        self._profiles: dict[str, KnowledgeProfile] = {}
        self._reality_listeners: list[Callable[[dict[str, Any]], None]] = []

    # ── Profile Management ──────────────────────────────────────────────

    def get_or_create_profile(
        self, owner_id: str, label: str = "",
        domains: list[str] | None = None,
    ) -> KnowledgeProfile:
        if owner_id in self._profiles:
            return self._profiles[owner_id]
        profile = KnowledgeProfile(
            owner_id=owner_id,
            label=label or f"Knowledge profile for {owner_id}",
            domains=domains or [],
        )
        self._profiles[profile.profile_id] = profile
        self._notify({"type": "knowledge_intelligence.profile_created",
                       "profile_id": profile.profile_id, "owner_id": owner_id})
        return profile

    def get_profile(self, profile_id: str) -> KnowledgeProfile | None:
        return self._profiles.get(profile_id)

    # ── Knowledge Management ────────────────────────────────────────────

    def add_knowledge(
        self,
        profile_id: str,
        knowledge_type: str = KnowledgeType.FACT.value,
        title: str = "",
        statement: str = "",
        summary: str = "",
        tags: list[str] | None = None,
        domain: str = "",
        context: str = "",
        source_type: str = SourceType.HUMAN.value,
        source_name: str = "",
        source_author: str = "",
        confidence: str = ConfidenceLevel.UNVERIFIED.value,
        confidence_score: float = 0.0,
        owner_id: str = "",
    ) -> Knowledge | None:
        profile = self._profiles.get(profile_id)
        if not profile:
            return None

        source = KnowledgeSource(source_type=source_type, name=source_name, author=source_author)

        knowledge = Knowledge(
            knowledge_type=knowledge_type,
            title=title,
            statement=statement,
            summary=summary or statement[:200],
            tags=tags or [],
            domain=domain,
            context=context,
            confidence=confidence,
            confidence_score=confidence_score,
            sources=[source] if source.name else [],
            owner_id=owner_id or profile.owner_id,
        )

        # Auto-compute freshness
        knowledge.freshness_score = self._engine.compute_freshness(knowledge)

        profile.knowledge_objects.append(knowledge)
        profile.updated_at = _now_iso()

        if domain and domain not in profile.domains:
            profile.domains.append(domain)

        self._notify({"type": "knowledge_intelligence.knowledge_added",
                       "profile_id": profile_id,
                       "knowledge_id": knowledge.knowledge_id,
                       "knowledge_type": knowledge_type,
                       "title": title})
        return knowledge

    def get_knowledge(self, profile_id: str, knowledge_id: str) -> Knowledge | None:
        profile = self._profiles.get(profile_id)
        if not profile:
            return None
        for k in profile.knowledge_objects:
            if k.knowledge_id == knowledge_id:
                return k
        return None

    def link_knowledge(
        self,
        profile_id: str,
        source_id: str,
        target_id: str,
        relationship: str = KnowledgeRelationship.RELATED_TO.value,
        strength: float = 1.0,
        evidence: str = "",
    ) -> bool:
        """Link two knowledge objects with a typed relationship."""
        profile = self._profiles.get(profile_id)
        if not profile:
            return False
        source = self.get_knowledge(profile_id, source_id)
        target = self.get_knowledge(profile_id, target_id)
        if not source or not target:
            return False

        link = KnowledgeLink(
            source_knowledge_id=source_id,
            target_knowledge_id=target_id,
            relationship=relationship,
            strength=strength,
            evidence=evidence,
        )
        source.links.append(link)
        profile.updated_at = _now_iso()
        return True

    # ── Semantic Search ─────────────────────────────────────────────────

    def search(
        self,
        profile_id: str,
        query: str,
        types: list[str] | None = None,
        domains: list[str] | None = None,
        tags: list[str] | None = None,
        min_confidence: float = 0.0,
        max_results: int = 20,
    ) -> list[dict[str, Any]]:
        profile = self._profiles.get(profile_id)
        if not profile:
            return []
        results = self._engine.search(
            profile.knowledge_objects, query, types, domains, tags,
            min_confidence, max_results,
        )
        return [r.to_dict() for r in results]

    # ── Knowledge Graph ─────────────────────────────────────────────────

    def build_knowledge_graph(self, profile_id: str) -> dict[str, Any] | None:
        profile = self._profiles.get(profile_id)
        if not profile:
            return None
        graph = self._engine.build_knowledge_graph(profile.knowledge_objects)
        return graph.to_dict()

    # ── Contradiction Detection ─────────────────────────────────────────

    def detect_contradictions(self, profile_id: str) -> list[dict[str, Any]]:
        profile = self._profiles.get(profile_id)
        if not profile:
            return []
        contradictions = self._engine.detect_contradictions(profile.knowledge_objects)
        # Store contradictions in profile
        for c in contradictions:
            if c not in profile.contradictions:
                profile.contradictions.append(c)
        return [c.to_dict() for c in contradictions]

    def resolve_contradiction(self, profile_id: str, contradiction_id: str,
                              resolution: str) -> bool:
        profile = self._profiles.get(profile_id)
        if not profile:
            return False
        for c in profile.contradictions:
            if c.contradiction_id == contradiction_id:
                c.resolved = True
                c.resolution = resolution
                c.resolved_at = _now_iso()
                return True
        return False

    # ── Duplicate Detection ─────────────────────────────────────────────

    def detect_duplicates(self, profile_id: str) -> list[dict[str, Any]]:
        profile = self._profiles.get(profile_id)
        if not profile:
            return []
        return self._engine.detect_duplicates(profile.knowledge_objects)

    # ── Confidence Scoring ──────────────────────────────────────────────

    def compute_confidence(
        self, profile_id: str, knowledge_id: str,
        source_reliability: float = 0.5,
        evidence_count: int = 0,
        corroboration_count: int = 0,
    ) -> dict[str, Any] | None:
        profile = self._profiles.get(profile_id)
        if not profile:
            return None
        knowledge = self.get_knowledge(profile_id, knowledge_id)
        if not knowledge:
            return None
        result = self._engine.compute_confidence(knowledge, source_reliability,
                                                  evidence_count, corroboration_count)
        knowledge.confidence_score = result["score"]
        knowledge.confidence = result["level"]
        return result

    # ── Gap Detection ───────────────────────────────────────────────────

    def detect_gaps(
        self, profile_id: str, domain: str = "",
        known_topics: list[str] | None = None,
    ) -> list[dict[str, Any]]:
        profile = self._profiles.get(profile_id)
        if not profile:
            return []
        gaps = self._engine.detect_gaps(profile.knowledge_objects, domain, known_topics)
        for gap in gaps:
            if gap not in profile.gaps:
                profile.gaps.append(gap)
        return [g.to_dict() for g in gaps]

    # ── Knowledge Recommendations ───────────────────────────────────────

    def recommend_knowledge(
        self, profile_id: str, domain: str = "", count: int = 5,
    ) -> list[dict[str, Any]]:
        profile = self._profiles.get(profile_id)
        if not profile:
            return []
        recs = self._engine.recommend_knowledge(profile.knowledge_objects, domain, count)
        for rec in recs:
            if rec not in profile.recommendations:
                profile.recommendations.append(rec)
        return [r.to_dict() for r in recs]

    # ── Evidence Reasoning ──────────────────────────────────────────────

    def reason_with_evidence(
        self, profile_id: str, knowledge_id: str,
    ) -> dict[str, Any] | None:
        profile = self._profiles.get(profile_id)
        if not profile:
            return None
        knowledge = self.get_knowledge(profile_id, knowledge_id)
        if not knowledge:
            return None
        return self._engine.reason_with_evidence(knowledge, profile.knowledge_objects)

    # ── Source Attribution ──────────────────────────────────────────────

    def attribute_sources(self, profile_id: str) -> dict[str, Any] | None:
        profile = self._profiles.get(profile_id)
        if not profile:
            return None
        return self._engine.attribute_sources(profile.knowledge_objects)

    # ── AI Context ──────────────────────────────────────────────────────

    def get_ai_context(self, profile_id: str) -> dict[str, Any] | None:
        profile = self._profiles.get(profile_id)
        if not profile:
            return None
        return self._engine.prepare_ai_context(profile.knowledge_objects)

    # ── Reality Integration ─────────────────────────────────────────────

    def notify(self, notification: dict[str, Any]) -> None:
        notification_type = notification.get("type", "")
        if notification_type == "knowledge_intelligence.knowledge_added":
            profile_id = notification.get("profile_id", "")
            knowledge_id = notification.get("knowledge_id", "")
            if profile_id and knowledge_id:
                logger.info(f"Knowledge {knowledge_id} added to profile {profile_id}")
        elif notification_type == "execution.knowledge_acquired":
            profile_id = notification.get("profile_id", "")
            if profile_id:
                self.add_knowledge(
                    profile_id=profile_id,
                    title=notification.get("title", "Acquired knowledge"),
                    statement=notification.get("statement", ""),
                    knowledge_type=notification.get("knowledge_type", KnowledgeType.FACT.value),
                    domain=notification.get("domain", ""),
                )

    # ── Adaptive Execution Integration ──────────────────────────────────

    # ── Engine Lifecycle ────────────────────────────────────────────────

    def initialize(self) -> None:
        logger.info("KnowledgeIntelligenceRuntime initialized")

    def shutdown(self) -> None:
        self._profiles.clear()
        self._reality_listeners.clear()
        logger.info("KnowledgeIntelligenceRuntime shut down")

    def health_check(self) -> dict[str, Any]:
        return {
            "status": "healthy",
            "runtime": "knowledge_intelligence",
            "profile_count": len(self._profiles),
        }

    def handle_event(self, event: Any) -> None:
        if isinstance(event, dict):
            self.notify(event)

    def get_capabilities(self) -> list[str]:
        return [
            "knowledge.profile",
            "knowledge.add",
            "knowledge.search",
            "knowledge.graph",
            "knowledge.contradiction_detection",
            "knowledge.duplicate_detection",
            "knowledge.confidence_scoring",
            "knowledge.gap_detection",
            "knowledge.recommendations",
            "knowledge.evidence_reasoning",
            "knowledge.source_attribution",
            "knowledge.reality_integration",
            "knowledge.execution_integration",
        ]

    # ── Internal ────────────────────────────────────────────────────────

    def _notify(self, notification: dict[str, Any]) -> None:
        for listener in self._reality_listeners:
            try:
                listener(notification)
            except Exception:
                logger.exception("Reality listener failed")

    def register_reality_listener(self, listener: Callable[[dict[str, Any]], None]) -> None:
        self._reality_listeners.append(listener)

    def unregister_reality_listener(self, listener: Callable[[dict[str, Any]], None]) -> None:
        if listener in self._reality_listeners:
            self._reality_listeners.remove(listener)