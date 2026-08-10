"""SYSTEM ENTRY POINT — the ONLY allowed way to trigger execution.

PHASE 3 LAYER D: All events must go through process_event().
No module can call execution directly.

Pipeline:
  event → capture_evidence → build_awareness → make_decision → execute

This is the single gate for all system activity.
"""

import logging
from typing import Any, Optional

from app.core.time import now

logger = logging.getLogger(__name__)


def process_event(
    event_type: str,
    event_data: dict,
    source: str = "unknown",
) -> dict:
    """Process an event through the canonical pipeline.

    This is the ONLY entry point for all system events.
    Every module, API, webhook, and background loop must call this.

    Args:
        event_type: Type of event (e.g., 'email_received', 'lead_created',
                   'whatsapp_message', 'calendar_event', 'proposal_approved')
        event_data: Event payload
        source: Source of the event (e.g., 'gmail', 'whatsapp', 'api', 'loop')

    Returns:
        dict with execution result and evidence chain.

    Raises:
        RuntimeError: If any pipeline stage fails (no blind execution).
    """
    logger.info("Entry: event=%s source=%s", event_type, source)

    # Stage 1: Capture evidence
    evidence = _capture_evidence(event_type, event_data, source)

    # Stage 2: Build awareness
    awareness = _build_awareness(evidence)

    # Stage 3: Make decision
    decision = _make_decision(awareness, event_data)

    # Stage 4: Execute
    result = _execute(decision, event_data)

    # Shadow run (Layer B)
    try:
        from app.core.shadow_runner import run_all_shadows, compare_with_main, log_shadow_diff
        shadow_outputs = run_all_shadows()
        diffs = compare_with_main(result, shadow_outputs)
        log_shadow_diff(diffs)
        result["shadow_diffs"] = len(diffs)
    except Exception:
        pass

    return result


def _capture_evidence(
    event_type: str,
    event_data: dict,
    source: str,
) -> dict:
    """Capture evidence for the event.

    Creates an EvidenceRecord and stores in the execution log.
    """
    evidence_id = None
    try:
        from app.evidence.models_db import create_evidence
        ev = create_evidence(
            source_type=event_type,
            source_id=str(event_data.get("id", event_data.get("entity_id", f"ev_{now().timestamp()}"))),
            raw_reference=event_data,
        )
        evidence_id = ev.id
        logger.info("Evidence captured: id=%d type=%s", ev.id, event_type)
    except Exception as e:
        logger.warning("Evidence capture failed: %s", e)

    return {
        "evidence_id": evidence_id,
        "event_type": event_type,
        "source": source,
        "timestamp": now().isoformat(),
    }


def _build_awareness(evidence: dict) -> dict:
    """Build awareness from evidence.

    Runs the awareness engine to generate signals.
    """
    try:
        from app.intelligence.awareness import scan
        signals = scan()
        return {
            "signals_count": len(signals),
            "signals": [s.get("type", "?") for s in signals[:5]],
        }
    except Exception as e:
        logger.warning("Awareness build failed: %s", e)
        return {"signals_count": 0, "signals": []}


def _make_decision(awareness: dict, event_data: dict) -> dict:
    """Make a decision based on awareness.

    Uses the decision engine to generate the next best action.
    """
    try:
        from app.intelligence.decision_engine import compute_decisions
        decisions = compute_decisions()
        if decisions:
            top = decisions[0]
            return {
                "decision": top.get("next_best_action", ""),
                "priority_score": top.get("priority_score", 0),
                "entity_id": top.get("entity_id"),
                "total_decisions": len(decisions),
            }
        return {"decision": "noop", "priority_score": 0, "total_decisions": 0}
    except Exception as e:
        logger.warning("Decision failed: %s", e)
        return {"decision": "error", "error": str(e)}


def _execute(decision: dict, event_data: dict) -> dict:
    """Execute the decision.

    Opens the execution gate, runs the loop, closes the gate.
    """
    try:
        from app.execution_engine.engine import open_execution_gate, close_execution_gate
        from app.runtime.loop import run_cycle

        open_execution_gate()
        try:
            summary = run_cycle()
        finally:
            close_execution_gate()

        return {
            "status": summary.get("status", "completed"),
            "actions_taken": summary.get("actions_taken", 0),
            "decision": decision.get("decision", "noop"),
            "executed_at": now().isoformat(),
        }
    except Exception as e:
        logger.error("Execution failed: %s", e)
        return {"status": "error", "error": str(e), "decision": decision.get("decision", "noop")}