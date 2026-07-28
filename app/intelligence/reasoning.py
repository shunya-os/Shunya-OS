"""
SHUNYA Explainable Intelligence — Reasoning Engine

The reasoning engine takes observations, evaluates them against
the relationship graph, and produces insights with provenance chains.

Every insight must be traceable back through the reasoning that produced it.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional

from app.intelligence.provenance import (
    ProvenanceNode, ProvenanceChain, ProvenanceStore, get_store as get_prov_store,
    NODE_SOURCE, NODE_EVENT, NODE_EVIDENCE, NODE_OBSERVATION,
    NODE_RELATIONSHIP, NODE_REASONING, NODE_INSIGHT, NODE_RECOMMENDATION,
)
from app.intelligence.confidence import (
    ConfidenceInput, compute_confidence, confidence_label,
)
from app.intelligence.observation import Observation, ObservationStore, get_store as get_obs_store


@dataclass
class ReasoningStep:
    """A single step in a reasoning chain."""

    label: str
    content: str
    confidence: float = 0.0
    evidence_ids: list[str] = field(default_factory=list)
    observation_ids: list[str] = field(default_factory=list)


@dataclass
class Insight:
    """A produced insight with full provenance."""

    insight_id: str
    label: str
    detail: str
    confidence: float
    confidence_label: str
    chain_id: str
    reasoning_steps: list[ReasoningStep] = field(default_factory=list)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> dict:
        return {
            "insight_id": self.insight_id,
            "label": self.label,
            "detail": self.detail,
            "confidence": self.confidence,
            "confidence_label": self.confidence_label,
            "chain_id": self.chain_id,
            "reasoning_steps": [
                {
                    "label": s.label,
                    "content": s.content,
                    "confidence": s.confidence,
                    "evidence_ids": s.evidence_ids,
                    "observation_ids": s.observation_ids,
                }
                for s in self.reasoning_steps
            ],
            "created_at": self.created_at.isoformat(),
        }


class ReasoningEngine:
    """The reasoning engine transforms observations into insights.

    It is business-agnostic. Scenario providers supply the data;
    the engine applies universal reasoning logic.
    """

    def __init__(
        self,
        provenance_store: Optional[ProvenanceStore] = None,
        observation_store: Optional[ObservationStore] = None,
    ):
        self.provenance = provenance_store or get_prov_store()
        self.observations = observation_store or get_obs_store()

    def evaluate_observation(self, observation: Observation) -> list[Insight]:
        """Evaluate a single observation and produce insights.

        This is where the reasoning engine processes an observation
        and produces one or more insights. Each insight has a full
        provenance chain.
        """
        chain = ProvenanceChain(f"chain_{observation.observation_id}")

        # Build the provenance chain
        source_node = ProvenanceNode(
            node_id=f"src_{observation.object_id}",
            node_type=NODE_SOURCE,
            label=f"Object: {observation.object_id}",
            content=observation.description,
            confidence=observation.confidence,
        )
        chain.add_node(source_node)

        event_node = ProvenanceNode(
            node_id=f"evt_{observation.event_id}",
            node_type=NODE_EVENT,
            label=f"Event: {observation.label}",
            content=observation.description,
            parent_id=source_node.node_id,
            confidence=observation.confidence,
        )
        chain.add_node(event_node)

        for i, evid in enumerate(observation.evidence_ids):
            evidence_node = ProvenanceNode(
                node_id=f"evid_{observation.observation_id}_{i}",
                node_type=NODE_EVIDENCE,
                label=f"Evidence: {evid}",
                content=f"Evidence reference: {evid}",
                parent_id=event_node.node_id if i == 0 else f"evid_{observation.observation_id}_{i-1}",
                confidence=observation.confidence,
            )
            chain.add_node(evidence_node)

        obs_node = ProvenanceNode(
            node_id=f"obs_{observation.observation_id}",
            node_type=NODE_OBSERVATION,
            label=observation.label,
            content=observation.description,
            parent_id=f"evid_{observation.observation_id}_{len(observation.evidence_ids) - 1}" if observation.evidence_ids else event_node.node_id,
            confidence=observation.confidence,
        )
        chain.add_node(obs_node)

        # Reasoning step
        reasoning_node = ProvenanceNode(
            node_id=f"rsn_{observation.observation_id}",
            node_type=NODE_REASONING,
            label="Reasoning evaluation",
            content=f"Evaluated observation: {observation.label}",
            parent_id=obs_node.node_id,
            confidence=observation.confidence,
        )
        chain.add_node(reasoning_node)

        # Produce insight
        insight_id = f"insight_{observation.observation_id}"
        insight_node = ProvenanceNode(
            node_id=insight_id,
            node_type=NODE_INSIGHT,
            label=f"Insight: {observation.label}",
            content=f"Based on observation of {observation.object_id}",
            parent_id=reasoning_node.node_id,
            confidence=observation.confidence,
        )
        chain.add_node(insight_node)

        # Compute confidence
        confidence_inputs = ConfidenceInput(
            evidence_completeness=0.8 if observation.evidence_ids else 0.3,
            observation_freshness=max(0.0, 1.0 - observation.age_hours / 168.0),  # Decay over 7 days
            source_reliability=0.85,
            relationship_consistency=0.8,
            conflict_detected=False,
            recency_hours=observation.age_hours,
            missing_information_ratio=0.1 if observation.evidence_ids else 0.5,
        )
        conf = compute_confidence(confidence_inputs)

        self.provenance.add_chain(chain)

        insight = Insight(
            insight_id=insight_id,
            label=observation.label,
            detail=observation.description,
            confidence=conf,
            confidence_label=confidence_label(conf),
            chain_id=chain.chain_id,
            reasoning_steps=[
                ReasoningStep(
                    label="Observation evaluation",
                    content=f"Observation {observation.observation_id} evaluated against {len(observation.evidence_ids)} evidence sources",
                    confidence=conf,
                    evidence_ids=observation.evidence_ids,
                    observation_ids=[observation.observation_id],
                ),
            ],
        )

        return [insight]

    def evaluate_object(self, object_id: str) -> list[Insight]:
        """Evaluate all active observations for an object."""
        active_obs = self.observations.get_active_by_object(object_id)
        insights: list[Insight] = []
        for obs in active_obs:
            insights.extend(self.evaluate_observation(obs))
        return insights

    def evaluate_all_active(self) -> list[Insight]:
        """Evaluate all active observations across all objects."""
        active_obs = self.observations.get_active()
        insights: list[Insight] = []
        for obs in active_obs:
            insights.extend(self.evaluate_observation(obs))
        return insights


# ─── Global engine ───
_engine: Optional[ReasoningEngine] = None


def get_engine() -> ReasoningEngine:
    global _engine
    if _engine is None:
        _engine = ReasoningEngine()
    return _engine


def reset_engine() -> None:
    global _engine
    _engine = None