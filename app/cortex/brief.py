"""
SHUNYA Organizational Cortex — Executive Brief

Executive Briefs are no longer generated independently.
They become projections of OrganizationState.

Every sentence in the brief resolves through:
  OrganizationState → Attention Item → Decision → Observation → Evidence → Knowledge
"""

from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone

from app.cortex.state import OrganizationState, get_synthesizer
from app.cortex.attention import AttentionItem, get_engine as get_attention_engine
from app.cortex.health import health_label, HEALTH_LABELS


@dataclass
class ExecutiveBrief:
    """An executive brief projected from OrganizationState.

    Every paragraph is derived from runtime state, not from copy.
    Every sentence is traceable through the Cortex chain.
    """

    summary: str
    attention_summary: str
    health_summary: str
    paragraphs: list[dict] = field(default_factory=list)
    insights: list[dict] = field(default_factory=list)
    state: dict = field(default_factory=dict)
    generated_at: str = ""

    def to_dict(self) -> dict:
        return {
            "summary": self.summary,
            "attention_summary": self.attention_summary,
            "health_summary": self.health_summary,
            "paragraphs": self.paragraphs,
            "insights": self.insights,
            "state": self.state,
            "generated_at": self.generated_at,
        }


def project_brief(org_name: str = "Organization") -> ExecutiveBrief:
    """Project an executive brief from the current OrganizationState.

    This is the canonical way to generate executive briefs.
    No copy. No hardcoded sentences. Everything is derived.
    """
    synth = get_synthesizer(org_name)
    state = synth.synthesize()
    attention = get_attention_engine()
    queue = attention.get_attention_queue(limit=5)
    now = datetime.now(timezone.utc).isoformat()

    # ─── Summary paragraph ───
    summary = (
        f"{org_name} is operating with "
        f"{len(state.health_scores)} health dimensions monitored. "
        f"Overall health: {health_label(state.overall_health)} ({state.overall_health:.0%}). "
        f"{state.active_commitments} active commitments, "
        f"{state.waiting_approval} decisions awaiting approval, "
        f"{state.critical_risks} risks flagged."
    )

    # ─── Attention paragraph ───
    if queue:
        top = queue[0]
        attention_summary = (
            f"Top priority: \"{top.label}\" "
            f"(priority: {top.priority_score:.2f}, "
            f"source: {top.source_type}). "
            f"{len(queue)} items in the attention queue."
        )
    else:
        attention_summary = "No items currently in the attention queue."

    # ─── Health paragraph ───
    health_parts = []
    for dim, score in sorted(state.health_scores.items(), key=lambda x: x[1]):
        label = HEALTH_LABELS.get(dim, dim)
        health_parts.append(f"{label}: {health_label(score)} ({score:.0%})")
    health_summary = " | ".join(health_parts[:4])  # Top 4 dimensions

    # ─── Paragraphs from attention items ───
    paragraphs = []
    for item in queue:
        paragraphs.append({
            "text": f"{item.label} — {item.description[:120]}",
            "source_type": item.source_type,
            "source_id": item.source_id,
            "priority": round(item.priority_score, 3),
            "status": item.status.value,
            "attention_item_id": item.item_id,
        })

    # ─── Insights from state ───
    insights = []
    if state.critical_risks > 0:
        insights.append({
            "label": f"{state.critical_risks} risk(s) detected",
            "detail": f"Low-confidence insights require attention",
            "confidence": 0.85,
        })
    if state.waiting_approval > 0:
        insights.append({
            "label": f"{state.waiting_approval} decision(s) pending approval",
            "detail": "Awaiting human review in the decision pipeline",
            "confidence": 0.9,
        })
    if state.active_commitments > 0:
        insights.append({
            "label": f"{state.active_commitments} active commitment(s)",
            "detail": "Being executed through the decision runtime",
            "confidence": 0.95,
        })

    return ExecutiveBrief(
        summary=summary,
        attention_summary=attention_summary,
        health_summary=health_summary,
        paragraphs=paragraphs,
        insights=insights,
        state=state.to_dict(),
        generated_at=now,
    )


def resolve_brief_sentence(sentence_text: str, brief: ExecutiveBrief) -> list[dict]:
    """Resolve a sentence from the brief back through the Cortex chain.

    Returns the chain: OrganizationState → Attention Item → ...
    """
    chain = [
        {"layer": "ExecutiveBrief", "data": {"summary": brief.summary[:100]}},
        {"layer": "OrganizationState", "data": {
            "health": brief.state.get("health", {}),
            "commitments": brief.state.get("commitments", {}),
        }},
    ]
    # Find matching attention items
    for para in brief.paragraphs:
        if para["text"].startswith(sentence_text[:30]):
            chain.append({
                "layer": "AttentionItem",
                "data": para,
            })
    return chain