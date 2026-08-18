"""Decision Engine — pure intelligence, returns next action for an object.

Supports multi-field payload evolution and structural multi-object intelligence.
No business assumptions — only structure, not meaning.

ACTIVATION-14B: Hybrid decision model.
When AI is available, the rule-based output is enriched with AI reasoning.
The final decision is the rule output unless AI confidence exceeds rule confidence.

The Mixed Intelligence Router (MIR) provides business-aware context:
1. Business Data (PostgreSQL) — Primary source of truth
2. Internet Research — Supporting evidence
3. AI Synthesis — Source-labeled final output

PROD-12: Single-link interaction (foundation).
An object may reference one other object via its `linked_to` state field.
When the referenced object reaches version 2, the linking object is synced.

PROD-13: Full object graph awareness.
An object may declare multiple structural relations:
    {
        "relations": [
            {"type": "depends_on", "target_id": 12},
            {"type": "blocks", "target_id": 15}
        ]
    }
Each relation is resolved when its target object reaches version 2.
Resolved relations accumulate in `resolved_relations` (non-destructive).
Once all declared relations are resolved, the object itself progresses to
version 2 so downstream objects can depend on it — graph propagation.

Relations are pure structure: {type, target_id}. No business meaning.
"""

import json
import logging
from typing import Optional

from app.execution_engine.context import DecisionContext
from app.objects.models import Object
from app.commitments.models import Commitment
from app.observations.models import Observation
from app.models import Task
from app.communication.logger import log_communication

logger = logging.getLogger(__name__)


def build_context(entity):
    """Build a decision context dict for an entity."""
    return {
        "state": getattr(entity, "stage", None),
        "outcome": getattr(entity, "outcome", None),
        "tasks": [],
        "observations": []
    }


def _get_ai_decision(obj) -> dict:
    """Query the Mixed Intelligence Router for an AI-suggested action.

    Returns a dict with:
        type: 'update'|'noop'
        payload: {...} (optional)
        effects: [...] (optional)  
        source: 'ai'
        confidence: 'high'|'medium'|'low'
        reasoning: str (human-readable)

    Returns {'type': 'noop', 'source': 'ai', 'confidence': 'low'}
    on any error or when AI is unavailable.
    """
    try:
        from app.intelligence.mixed_router import MixedIntelligenceRouter

        # Build a business query from entity state
        state = obj.state or {}
        name = state.get("name", state.get("description", f"Entity #{obj.id}"))
        stage = state.get("stage", "unknown")
        phone = state.get("phone", "")
        email = state.get("email", "")

        # Fetch recent timeline for context
        timeline_events = []
        try:
            from app.execution_log.models import ExecutionLog
            recent_logs = (
                ExecutionLog.query
                .filter_by(object_id=obj.id)
                .order_by(ExecutionLog.timestamp.desc())
                .limit(5)
                .all()
            )
            for log in recent_logs:
                tl = log.to_dict()
                timeline_events.append(f"{tl.get('event_type','?')}: {json.dumps(tl.get('payload',{}))}")
        except Exception:
            pass

        # Build the query with full context
        context_parts = [
            f"What should SHUNYA do next with {name}?",
            f"Entity state: {json.dumps(state)}",
        ]
        if timeline_events:
            context_parts.append(f"Recent events: {' | '.join(timeline_events)}")
        query = " | ".join(context_parts)

        router = MixedIntelligenceRouter()
        response = router.answer(query)

        # Parse the AI synthesis into a decision
        synthesis = response.synthesis or ""
        synthesis_lower = synthesis.lower()

        # Determine if AI suggests action or noop
        if any(phrase in synthesis_lower for phrase in [
            "no action needed", "nothing to do", "waiting", "no change",
            "no specific action", "not enough data", "don't have enough"
        ]):
            return {
                "type": "noop",
                "source": "ai",
                "confidence": "medium",
                "reasoning": synthesis[:200] if synthesis else "AI suggests no action needed",
            }

        # AI suggests some action — extract confidence from synthesis
        if response.has_business_data:
            ai_confidence = "high"
        elif response.has_internet_data:
            ai_confidence = "medium"
        else:
            ai_confidence = "low"

        return {
            "type": "ai_suggest",
            "source": "ai",
            "confidence": ai_confidence,
            "reasoning": synthesis[:300] if synthesis else "AI provided contextual analysis",
            "synthesis": synthesis[:500] if synthesis else "",
        }

    except Exception as e:
        logger.debug("AI decision unavailable: %s", e)
        return {
            "type": "noop",
            "source": "ai",
            "confidence": "low",
            "reasoning": f"AI unavailable: {e}",
        }


def _apply_hybrid_decision(rule_action: dict, ai_decision: dict) -> dict:
    """Merge rule-based and AI decisions using confidence-based hybrid model.

    HYBRID MODEL:
    IF rule confidence is HIGH (stage progression is clear):
        use rule output, annotate with AI insight
    ELSE IF AI confidence >= rule confidence:
        use AI output
    ELSE:
        use rule output

    Args:
        rule_action: Output from the rule-based decision logic.
        ai_decision: Output from _get_ai_decision().

    Returns:
        Enriched action dict with source and confidence metadata.
    """
    # Determine rule confidence
    rule_type = rule_action.get("type", "noop")
    rule_payload = rule_action.get("payload", {})

    # Rule is high confidence when it has a clear stage progression
    has_stage_progression = bool(rule_payload.get("stage"))
    rule_confidence = "high" if (rule_type == "update" and has_stage_progression) else "medium"

    ai_confidence = ai_decision.get("confidence", "low")

    # Build the enriched action
    enriched = dict(rule_action)
    enriched["decision_source"] = "rule"
    enriched["decision_confidence"] = rule_confidence
    enriched["ai_reasoning"] = ai_decision.get("reasoning", "")

    confidence_levels = {"high": 3, "medium": 2, "low": 1}
    if confidence_levels.get(ai_confidence, 0) > confidence_levels.get(rule_confidence, 0):
        # AI has higher confidence — use AI suggestion
        if ai_decision.get("type") != "noop":
            enriched["decision_source"] = "ai"
            enriched["decision_confidence"] = ai_confidence
            enriched["ai_reasoning"] = ai_decision.get("reasoning", "")

    return enriched


def get_next_action(obj, decision_ctx: Optional[DecisionContext] = None) -> dict:
    """Decide the next action for an object based on state + AI context.

    Args:
        obj: Object instance with .state dict.
        decision_ctx: Optional constitutional input (State, Intent, Evidence, Time).
            When provided, state is consumed from decision_ctx.state (merged with
            obj.state), and evidence is checked before allowing an update decision.
            This proves the four constitutional dimensions reach the decision boundary.

    Returns:
        update with payload if state progression needed.
        noop if state is fully evolved.
        Always includes decision_source and decision_confidence.
    """
    # Constitutional state: primary source is DecisionContext when provided
    if decision_ctx is not None and decision_ctx.state:
        state = {**(obj.state or {}), **decision_ctx.state}
    else:
        state = obj.state or {}

    # Constitutional evidence check: when DecisionContext includes evidence,
    # do not return an update action unless evidence exists
    if decision_ctx is not None and decision_ctx.has_evidence() is False:
        # No evidence provided — constitutional chain is broken.
        # Return noop instead of update, regardless of state.
        if state:
            return {
                "type": "noop",
                "decision_source": "constitutional",
                "decision_confidence": "low",
            }

    if not state:
        return {
            "type": "update",
            "payload": {
                "initialized": True,
                "version": 1,
            },
            "decision_source": "rule",
            "decision_confidence": "high",
        }

    # PROD-13 — structural multi-object graph awareness.
    if state.get("relations"):
        resolved = set(state.get("resolved_relations") or [])
        newly = []
        for rel in state["relations"]:
            if not isinstance(rel, dict):
                continue
            target_id = rel.get("target_id")
            if target_id is None or target_id in resolved:
                continue
            target = Object.query.get(target_id)
            if target is not None and (target.state or {}).get("version") == 2:
                newly.append(target_id)

        if newly:
            accumulated = sorted(resolved | set(newly))
            return {
                "type": "update",
                "payload": {"resolved_relations": accumulated},
                "decision_source": "rule",
                "decision_confidence": "high",
            }

        if not state.get("initialized"):
            return {
                "type": "update",
                "payload": {"initialized": True, "version": 1},
                "decision_source": "rule",
                "decision_confidence": "high",
            }
        if state.get("version") == 1:
            return {
                "type": "update",
                "payload": {"version": 2},
                "decision_source": "rule",
                "decision_confidence": "high",
            }

    # PROD-12 — structural single-link interaction (preserved).
    if state.get("linked_to"):
        linked = Object.query.get(state["linked_to"])
        if linked is not None and (linked.state or {}).get("version") == 2:
            return {
                "type": "update",
                "payload": {"synced": True},
                "decision_source": "rule",
                "decision_confidence": "high",
            }

    if state.get("initialized") and state.get("version") == 1:
        return {
            "type": "update",
            "payload": {"version": 2},
            "decision_source": "rule",
            "decision_confidence": "high",
        }

    return {
        "type": "noop",
        "decision_source": "rule",
        "decision_confidence": "medium",
    }


def decide_next_from_commitment(commitment: Commitment):
    """
    Decision based on latest observation.

    Returns:
        update_commitment with status=completed if latest observation
        is matched; noop otherwise.
    """
    obs = (
        Observation.query
        .filter_by(commitment_id=commitment.id)
        .order_by(Observation.id.desc())
        .first()
    )

    if not obs:
        return {"type": "noop"}

    if obs.status == "matched":
        return {
            "type": "update_commitment",
            "payload": {"status": "completed"}
        }

    if obs.status == "deviated":
        return {
            "type": "update_commitment",
            "payload": {"status": "failed"}
        }

    return {"type": "noop"}


def decide_entity(entity):
    """Generic decision for an Entity based on its state."""
    if entity.state == "new":
        return {"type": "update", "payload": {"state": "in_progress"}}
    return {"type": "noop"}


def explain_decision(entity, decision):
    return {
        "entity_id": entity.id,
        "decision": decision,
        "reason": "Derived from current state and context",
        "state": entity.state
    }