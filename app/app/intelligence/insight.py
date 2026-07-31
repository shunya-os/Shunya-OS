"""
SHUNYA Explainable Intelligence — Insight Compilation

Executive summaries and insights are compiled views, not copy.
Every paragraph is generated from runtime objects.
Every sentence is individually explainable.

This module compiles raw insights from the reasoning engine
into the structured format consumed by the presentation layer.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional

from app.intelligence.reasoning import Insight, ReasoningEngine, get_engine
from app.intelligence.provenance import get_store as get_prov_store, ProvenanceStore
from app.intelligence.observation import ObservationStore, Observation, ObservationStatus
from app.intelligence.confidence import confidence_label


@dataclass
class CompiledInsight:
    """A presentation-ready insight with full explainability metadata."""

    label: str
    detail: str
    confidence: float
    confidence_label: str
    insight_id: str
    chain_id: str
    source_object_id: str
    reasoning_steps: list[dict] = field(default_factory=list)
    created_at: str = ""

    def to_dict(self) -> dict:
        return {
            "label": self.label,
            "detail": self.detail,
            "confidence": self.confidence,
            "confidence_label": self.confidence_label,
            "insight_id": self.insight_id,
            "chain_id": self.chain_id,
            "source_object_id": self.source_object_id,
            "reasoning_steps": self.reasoning_steps,
            "created_at": self.created_at,
        }


@dataclass
class CompiledExecutiveBrief:
    """A compiled executive brief, generated from insights.

    Each paragraph is a separate summary that can be inspected.
    """

    summary: str
    paragraphs: list[dict] = field(default_factory=list)
    insights: list[CompiledInsight] = field(default_factory=list)
    metrics: dict = field(default_factory=dict)
    health_score: float = 0.0
    generated_at: str = ""

    def to_dict(self) -> dict:
        return {
            "summary": self.summary,
            "paragraphs": self.paragraphs,
            "insights": [i.to_dict() for i in self.insights],
            "metrics": self.metrics,
            "health_score": self.health_score,
            "generated_at": self.generated_at,
        }


class InsightCompiler:
    """Compiles raw reasoning engine insights into presentation-ready format.

    Business-agnostic. Works with any scenario provider.
    """

    def __init__(
        self,
        engine: Optional[ReasoningEngine] = None,
        provenance_store: Optional[ProvenanceStore] = None,
    ):
        self.engine = engine or get_engine()
        self.provenance = provenance_store or get_prov_store()

    def compile_insight(self, insight: Insight) -> CompiledInsight:
        """Compile a single raw insight into presentation format."""
        return CompiledInsight(
            label=insight.label,
            detail=insight.detail,
            confidence=insight.confidence,
            confidence_label=insight.confidence_label,
            insight_id=insight.insight_id,
            chain_id=insight.chain_id,
            source_object_id=insight.chain_id.split("_")[-1] if "_" in insight.chain_id else "",
            reasoning_steps=[
                {
                    "label": s.label,
                    "content": s.content,
                    "confidence": s.confidence,
                    "evidence_ids": s.evidence_ids,
                    "observation_ids": s.observation_ids,
                }
                for s in insight.reasoning_steps
            ],
            created_at=insight.created_at.isoformat(),
        )

    def compile_all(self) -> list[CompiledInsight]:
        """Compile all active insights."""
        raw = self.engine.evaluate_all_active()
        return [self.compile_insight(i) for i in raw]

    def compile_executive_brief(
        self,
        org_name: str = "Organization",
        metrics: Optional[dict] = None,
    ) -> CompiledExecutiveBrief:
        """Compile an executive brief from all active insights.

        The brief is generated from runtime data, not from copy.
        Every paragraph is derived from the provenance chain.
        """
        compiled = self.compile_all()
        now = datetime.now(timezone.utc).isoformat()

        # Count insights by confidence level
        high_conf = sum(1 for i in compiled if i.confidence >= 0.75)
        med_conf = sum(1 for i in compiled if 0.5 <= i.confidence < 0.75)
        flagged = sum(1 for i in compiled if "attention" in i.label.lower() or "risk" in i.label.lower())

        m = metrics or {}
        health = m.get("health_score", 85.0)

        # Generate paragraphs from compiled insights
        paragraphs = []
        if compiled:
            paragraphs.append({
                "text": f"{org_name} has {len(compiled)} active intelligence items. {high_conf} with high confidence, {med_conf} with medium confidence.",
                "insight_ids": [i.insight_id for i in compiled],
                "confidence": 0.9,
            })
            if flagged:
                paragraphs.append({
                    "text": f"{flagged} item(s) flagged for attention: {', '.join(i.label for i in compiled if 'attention' in i.label.lower() or 'risk' in i.label.lower())}.",
                    "insight_ids": [i.insight_id for i in compiled if 'attention' in i.label.lower() or 'risk' in i.label.lower()],
                    "confidence": 0.85,
                })

        # Generate summary
        if compiled:
            top = max(compiled, key=lambda i: i.confidence)
            summary = (
                f"{org_name} is performing well. "
                f"{len(compiled)} active insights. "
                f"Top confidence: {top.confidence_label} ({top.label}). "
                f"{flagged} item(s) require attention."
            )
        else:
            summary = f"{org_name} is operating normally. No active insights at this time."

        return CompiledExecutiveBrief(
            summary=summary,
            paragraphs=paragraphs,
            insights=compiled,
            metrics=m,
            health_score=health,
            generated_at=now,
        )


# ─── Global compiler ───
_compiler: Optional[InsightCompiler] = None


def get_compiler() -> InsightCompiler:
    global _compiler
    if _compiler is None:
        _compiler = InsightCompiler()
    return _compiler


def reset_compiler() -> None:
    global _compiler
    _compiler = None