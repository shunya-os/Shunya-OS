"""Cortex Observer Bridge — feeds execution data INTO Cortex for observation.

PHASE 2B: Observer mode ONLY.
PHASE 2C: Uses persistent state_log (DB-backed) instead of in-memory storage.

Cortex reads runtime state, execution summaries, proposals, and AI evidence.
It does NOT modify decisions, inject outputs, or override any system.
All observations are stored in app/cortex/state_log.py (DB-backed).
"""

import logging
from datetime import datetime, timezone
from typing import Any, Optional

logger = logging.getLogger(__name__)


def observe_execution_summary(summary: dict) -> dict:
    """Feed a run_cycle() summary to Cortex for observation.

    Persisted to state_log. No outputs injected back into execution.
    """
    try:
        from app.cortex.state_log import store

        store(
            observation_type="execution_summary",
            data={
                "actions_taken": summary.get("actions_taken", 0),
                "noops": summary.get("noops", 0),
                "errors": len(summary.get("errors", [])),
                "status": summary.get("status", "unknown"),
            },
        )
        return {"observed": True}
    except Exception as e:
        logger.debug("Cortex observe_execution_summary skipped: %s", e)
        return {"observed": False, "reason": str(e)}


def observe_proposal(
    proposal_id: int,
    entity_id: Optional[int] = None,
    source: str = "effect_engine",
    reason: str = "",
) -> dict:
    """Feed a proposal creation event to Cortex for observation."""
    try:
        from app.cortex.state_log import store

        store(
            observation_type="proposal",
            data={
                "proposal_id": proposal_id,
                "source": source,
                "reason": reason,
            },
            entity_id=entity_id,
        )
        return {"observed": True}
    except Exception as e:
        logger.debug("Cortex observe_proposal skipped: %s", e)
        return {"observed": False, "reason": str(e)}


def observe_ai_response(
    provider: str,
    model: str,
    confidence: float,
    fallback_used: bool = False,
) -> dict:
    """Feed an AI response event to Cortex for observation."""
    try:
        from app.cortex.state_log import store

        store(
            observation_type="ai",
            data={
                "provider": provider,
                "model": model,
                "confidence": confidence,
                "fallback_used": fallback_used,
            },
        )
        return {"observed": True}
    except Exception as e:
        logger.debug("Cortex observe_ai_response skipped: %s", e)
        return {"observed": False, "reason": str(e)}


def get_cortex_insights() -> dict:
    """Read Cortex's current observations from the state log."""
    try:
        from app.cortex.state_log import query, count_by_type

        return {
            "counts": count_by_type(),
            "recent_executions": query(observation_type="execution_summary", limit=5),
            "recent_proposals": query(observation_type="proposal", limit=5),
            "recent_ai": query(observation_type="ai", limit=5),
        }
    except Exception as e:
        return {"error": str(e)}