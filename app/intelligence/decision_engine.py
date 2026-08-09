"""Decision Intelligence Engine — generates structured decisions from awareness signals.

PHASE 2C.2: For each awareness signal, computes:
- next_best_action (clear, human-readable)
- priority_score (0–100)
- impact (revenue / risk / system health)

Enriches with entity name, last interaction, related proposals.
Does NOT auto-execute — outputs are read-only guidance.
"""

import logging
from datetime import datetime, timezone
from typing import Any, Optional

logger = logging.getLogger(__name__)


def _get_entity_context(entity_id: Optional[int]) -> dict:
    """Fetch entity context: name, state, last interaction, related proposals."""
    ctx = {}
    if not entity_id:
        return ctx

    try:
        from app.objects.models import Object
        obj = Object.query.get(entity_id)
        if obj:
            state = obj.state or {}
            ctx["entity_name"] = state.get("name", state.get("description", f"Entity #{entity_id}"))
            ctx["entity_type"] = obj.type
            ctx["entity_stage"] = state.get("stage", "unknown")
            ctx["last_activity"] = obj.updated_at.isoformat() if obj.updated_at else None
    except Exception:
        ctx["entity_name"] = f"Entity #{entity_id}"

    # Fetch related proposals
    try:
        from app.communication.models import MessageProposal
        proposals = MessageProposal.query.filter_by(
            entity_id=entity_id, status="pending"
        ).order_by(MessageProposal.id.desc()).limit(3).all()
        if proposals:
            ctx["pending_proposals"] = [
                {"id": p.id, "message": p.message[:80]}
                for p in proposals
            ]
    except Exception:
        pass

    return ctx


def _generate_action(signal: dict, ctx: dict) -> dict:
    """Generate a structured decision from a signal + entity context."""
    signal_type = signal.get("type", "unknown")
    severity = signal.get("severity", "low")
    entity_id = signal.get("entity_id")

    # Base priority score
    priority_map = {"high": 80, "medium": 50, "low": 20}
    priority_score = priority_map.get(severity, 20)

    # Impact assessment
    impact_map = {
        "idle_entity": "revenue",
        "failed_cycle": "system_health",
        "stuck_entities": "system_health",
        "high_ai_fallback": "system_health",
        "unexecuted_proposal": "revenue",
    }
    impact = impact_map.get(signal_type, "system_health")

    # Build human-readable next best action
    entity_name = ctx.get("entity_name", "this entity")
    entity_stage = ctx.get("entity_stage", "")

    action_templates = {
        "idle_entity": f"Contact {entity_name} — no activity detected in stage '{entity_stage}'",
        "failed_cycle": f"Check execution logs for {entity_name} — errors detected in last cycle",
        "stuck_entities": f"Review stage progression for {entity_name} — stuck in '{entity_stage}'",
        "high_ai_fallback": "Verify LLM provider API keys — AI fallback chain being used excessively",
        "unexecuted_proposal": f"Review and approve pending proposal for {entity_name}",
    }
    next_best_action = action_templates.get(
        signal_type,
        f"Investigate {entity_name} — {signal.get('reason', 'unknown issue')}",
    )

    # Boost priority if entity has pending proposals
    if ctx.get("pending_proposals"):
        priority_score = min(100, priority_score + 15)
        if signal_type == "idle_entity":
            next_best_action = f"Follow up with {entity_name} — has {len(ctx['pending_proposals'])} pending proposal(s)"

    # Boost priority for high severity
    if severity == "high":
        priority_score = max(priority_score, 70)

    return {
        "signal_type": signal_type,
        "severity": severity,
        "entity_id": entity_id,
        "entity_name": entity_name,
        "next_best_action": next_best_action,
        "priority_score": priority_score,
        "impact": impact,
        "reason": signal.get("reason", ""),
        "suggested_action": signal.get("suggested_action", ""),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


def compute_decisions() -> list:
    """Compute structured decisions from all current awareness signals.

    Returns:
        List of decision dicts, sorted by priority_score descending.
    """
    try:
        from app.intelligence.awareness import scan
        signals = scan()
    except Exception as e:
        logger.debug("Decision engine: could not scan awareness: %s", e)
        return []

    # PHASE 2C.4: Consistency assertion — log warning if signal count is suspicious
    try:
        from app.objects.models import Object
        obj_count = Object.query.count()
        if obj_count > 0 and len(signals) == 0:
            logger.warning(
                "STATE INCONSISTENCY: %d objects exist but 0 awareness signals. "
                "Check DB connection isolation (SQLite in-memory?)",
                obj_count,
            )
        elif obj_count == 0 and len(signals) > 0:
            logger.warning(
                "STATE INCONSISTENCY: 0 objects but %d awareness signals. Stale cache?",
                len(signals),
            )
    except Exception:
        pass

    decisions = []
    for signal in signals:
        try:
            ctx = _get_entity_context(signal.get("entity_id"))
            decision = _generate_action(signal, ctx)
            decisions.append(decision)
        except Exception as e:
            logger.debug("Decision engine: error processing signal: %s", e)
            continue

    # Sort by priority_score descending
    decisions.sort(key=lambda d: -d.get("priority_score", 0))
    return decisions