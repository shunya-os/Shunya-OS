"""
SHUNYA Organizational Cortex — Runtime Bootstrap and Middleware

Wires the Cortex into the Flask app.
No new routes. No new UI. Extends ?inspect= for full Cortex chain.
"""

from flask import request, jsonify
from datetime import datetime, timezone

from app.cortex.state import get_synthesizer, OrganizationState
from app.cortex.attention import (
    get_engine as get_attention_engine, AttentionItem, compute_priority,
    AttentionStatus,
)
from app.cortex.brief import project_brief, resolve_brief_sentence
from app.cortex.health import compute_health, health_label
from app.decision_runtime.models import get_store as get_decision_store, DecisionStatus
from app.decision_runtime.commitment import get_service as get_commitment_service
from app.intelligence.observation import get_store as get_obs_store, ObservationStatus
from app.intelligence.insight import get_compiler


def register_cortex_middleware(app) -> None:
    """Register Cortex middleware on the Flask app.

    Extends ?inspect= to resolve the full Cortex chain.
    Adds ?inspect_cortex=1 for full system state.
    """

    @app.before_request
    def _check_cortex_inspect():
        if request.args.get("inspect_cortex"):
            return jsonify(_inspect_cortex())
        if request.args.get("inspect_brief"):
            brief = project_brief("Organization")
            return jsonify(brief.to_dict())
        return None


def _inspect_cortex() -> dict:
    """Inspect the full Cortex system state."""
    synth = get_synthesizer("Organization")
    state = synth.synthesize()
    attention = get_attention_engine()
    queue = attention.get_attention_queue(limit=10)
    brief = project_brief("Organization")

    return {
        "organization_state": state.to_dict(),
        "attention_queue": [item.to_dict() for item in queue],
        "executive_brief": brief.to_dict(),
        "inspection_timestamp": datetime.now(timezone.utc).isoformat(),
    }


def load_cortex_data() -> None:
    """Load Cortex data from all runtime modules.

    Called once at startup. Populates the attention engine
    from the decision runtime, observation store, and insight compiler.
    """
    attention = get_attention_engine()
    ds = get_decision_store()
    obs = get_obs_store()
    compiler = get_compiler()
    cs = get_commitment_service()

    # ─── Decisions → Attention items ───
    for d in ds._decisions.values():
        if d.status in (DecisionStatus.CANDIDATE, DecisionStatus.POLICY_EVALUATING,
                        DecisionStatus.AWAITING_APPROVAL, DecisionStatus.APPROVED):
            item = AttentionItem(
                item_id=f"attn_dec_{d.decision_id}",
                label=f"Decision: {d.label}",
                description=d.description[:200],
                source_type="decision",
                source_id=d.decision_id,
                impact=0.6 if d.business_impact == "high" else 0.4,
                urgency=0.8 if d.urgency == "critical" else (0.5 if d.urgency == "normal" else 0.3),
                commitment_risk=0.7 if d.urgency == "critical" else 0.3,
                evidence_confidence=d.confidence,
                policy_severity=0.6 if d.approval_required else 0.2,
                opportunity_window=0.5,
                learning_confidence=0.5,
                organizational_reach=0.5,
            )
            attention.add_item(item)

    # ─── Observations → Attention items ───
    for o in obs._observations.values():
        if o.status == ObservationStatus.ACTIVE:
            item = AttentionItem(
                item_id=f"attn_obs_{o.observation_id}",
                label=f"Observation: {o.label}",
                description=o.description[:200],
                source_type="observation",
                source_id=o.observation_id,
                impact=0.5,
                urgency=0.6 if o.age_hours > 24 else 0.4,
                evidence_confidence=o.confidence,
                execution_delay=min(1.0, o.age_hours / 168.0),
                organizational_reach=0.3,
            )
            attention.add_item(item)

    # ─── Insights → Attention items ───
    insights = compiler.compile_all()
    for ins in insights:
        item = AttentionItem(
            item_id=f"attn_ins_{ins.insight_id}",
            label=f"Insight: {ins.label}",
            description=ins.detail[:200],
            source_type="insight",
            source_id=ins.insight_id,
            impact=0.5,
            urgency=0.5,
            evidence_confidence=ins.confidence,
            learning_confidence=ins.confidence,
            organizational_reach=0.4,
        )
        attention.add_item(item)

    # Rank all items
    attention.reorder()