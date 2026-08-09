"""Cortex Observer Bridge — feeds execution data INTO Cortex for observation.

PHASE 2B: Observer mode ONLY.
Cortex reads runtime state, execution summaries, proposals, and AI evidence.
It does NOT modify decisions, inject outputs, or override any system.
"""

import json
import logging
from datetime import datetime, timezone
from typing import Any, Optional

logger = logging.getLogger(__name__)


def observe_execution_summary(summary: dict) -> dict:
    """Feed a run_cycle() summary to Cortex for observation.

    Cortex reads the summary and generates internal insights.
    No outputs are injected back into execution.
    """
    try:
        from app.cortex.state import get_organization_state
        state = get_organization_state()
        # Read only — no writes to execution
        state.summary = {
            "actions_taken": summary.get("actions_taken", 0),
            "noops": summary.get("noops", 0),
            "errors": len(summary.get("errors", [])),
            "status": summary.get("status", "unknown"),
            "observed_at": datetime.now(timezone.utc).isoformat(),
        }
        return {"observed": True}
    except Exception as e:
        logger.debug("Cortex observe_execution_summary skipped: %s", e)
        return {"observed": False, "reason": str(e)}


def observe_proposal(proposal: Any, proposal_id: int, entity_id: Optional[int] = None) -> dict:
    """Feed a proposal creation event to Cortex for observation."""
    try:
        from app.cortex.state import get_organization_state
        state = get_organization_state()
        # Append to read-only proposal log
        if not hasattr(state, "_proposals"):
            state._proposals = []
        state._proposals.append({
            "id": proposal_id,
            "entity_id": entity_id,
            "observed_at": datetime.now(timezone.utc).isoformat(),
        })
        return {"observed": True}
    except Exception as e:
        logger.debug("Cortex observe_proposal skipped: %s", e)
        return {"observed": False, "reason": str(e)}


def observe_ai_response(provider: str, model: str, confidence: float, fallback_used: bool) -> dict:
    """Feed an AI response event to Cortex for observation."""
    try:
        from app.cortex.state import get_organization_state
        state = get_organization_state()
        if not hasattr(state, "_ai_responses"):
            state._ai_responses = []
        state._ai_responses.append({
            "provider": provider,
            "model": model,
            "confidence": confidence,
            "fallback_used": fallback_used,
            "observed_at": datetime.now(timezone.utc).isoformat(),
        })
        return {"observed": True}
    except Exception as e:
        logger.debug("Cortex observe_ai_response skipped: %s", e)
        return {"observed": False, "reason": str(e)}


def get_cortex_insights() -> dict:
    """Read Cortex's current state observations (read-only)."""
    try:
        from app.cortex.state import get_organization_state
        state = get_organization_state()
        return {
            "summary": getattr(state, "summary", {}),
            "attention": getattr(state, "attention", None),
            "health": getattr(state, "health", None),
        }
    except Exception as e:
        return {"error": str(e)}