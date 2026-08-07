"""Universal Relationship Intelligence — Provider Adapter.

Abstract provider interface for AI-powered understanding of relationships.
Allows plugging in any AI provider (OpenAI, Claude, local LLM, etc.)
without changing the core engine.

Follows the SHUNYA Provider Adapter ABC pattern.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from core.relationship_intelligence.engine import (
    RelationshipIntelligenceEngine,
)
from core.relationship_intelligence.models import (
    RelationshipProfile,
)


class RelationshipAIProvider(ABC):
    """Abstract provider for AI understanding in Relationship Intelligence.

    Implementations connect to LLMs, analysis services, or local models
    to generate natural-language understanding of relationships.
    """

    @abstractmethod
    def generate_insights(self, profile: RelationshipProfile,
                          context: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        """Generate AI-powered insights from relationship context.

        Returns a list of insight dicts with at least:
            - category: str (pattern, risk, opportunity, observation, alert)
            - title: str
            - description: str
            - confidence: float (0-1)
            - actionable: bool
            - action_suggestion: str
        """
        ...

    @abstractmethod
    def analyze_communication(self, text: str, context: dict[str, Any] | None = None) -> dict[str, Any]:
        """Analyze communication text for sentiment, intent, and key points.

        Returns:
            {
                "sentiment_score": float,  # -1 to 1
                "sentiment_magnitude": float,  # 0 to 1
                "key_topics": list[str],
                "summary": str,
                "intent": str,
            }
        """
        ...

    @abstractmethod
    def generate_recommendations(
        self,
        profile: RelationshipProfile,
        context: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        """Generate AI-powered recommendations from relationship context.

        Returns a list of recommendation dicts with at least:
            - priority: str (critical, high, medium, low)
            - category: str
            - title: str
            - description: str
            - expected_impact: str
            - effort: str (low, medium, high)
        """
        ...


class DefaultAIProvider(RelationshipAIProvider):
    """Default AI provider using heuristic rules.

    Uses the engine's built-in analytical methods rather than an external AI.
    Suitable for testing, offline use, and as a fallback.
    """

    def __init__(self, engine: RelationshipIntelligenceEngine | None = None) -> None:
        """Create a DefaultAIProvider.

        Args:
            engine: Optional shared engine instance. When omitted, a new
                engine is created. Passing a shared engine avoids duplicating
                the analytical core when the provider is used with a runtime.
        """
        self._engine = engine or RelationshipIntelligenceEngine()

    def generate_insights(self, profile: RelationshipProfile,
                          context: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        insights = self._engine.generate_insights(profile)
        return [i.to_dict() for i in insights]

    def analyze_communication(
        self, text: str, context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Basic heuristic communication analysis."""
        # Simple word-level sentiment heuristic
        positive_words = {
            "good", "great", "excellent", "thank", "thanks", "appreciate",
            "pleased", "happy", "delighted", "wonderful", "fantastic",
            "amazing", "awesome", "love", "perfect", "agree", "yes",
            "absolutely", "certainly", "brilliant", "outstanding",
        }
        negative_words = {
            "bad", "terrible", "awful", "poor", "unfortunately", "sorry",
            "disappointed", "frustrated", "angry", "upset", "worried",
            "concerned", "issue", "problem", "fail", "failure", "wrong",
            "mistake", "error", "delay", "missed", "cannot", "can't",
        }

        words = set(text.lower().split())
        positive_count = len(words & positive_words)
        negative_count = len(words & negative_words)
        total = positive_count + negative_count

        sentiment = 0.0
        if total > 0:
            sentiment = (positive_count - negative_count) / max(total, 1)

        return {
            "sentiment_score": round(max(-1.0, min(1.0, sentiment)), 4),
            "sentiment_magnitude": round(min(1.0, total / 20), 4),
            "key_topics": [],
            "summary": text[:200] if text else "",
            "intent": "inquiry" if "?" in text else "statement",
        }

    def generate_recommendations(
        self,
        profile: RelationshipProfile,
        context: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        recommendations = self._engine.generate_recommendations(profile)
        return [r.to_dict() for r in recommendations]