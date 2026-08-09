"""Awareness Engine — detects signals from cortex observations.

PHASE 2C: Read-only intelligence layer. Detects patterns and generates
structured awareness signals. Does NOT trigger execution or modify proposals.

Signals detected:
- Idle entities (no activity in X time)
- Failed execution cycles
- Repeated noops (entity stuck in same state)
- High AI fallback usage
- Unexecuted proposals (pending > X time)
"""

import logging
from datetime import datetime, timezone, timedelta
from typing import Any, Optional

logger = logging.getLogger(__name__)


def _get_observations() -> dict:
    """Get observations from the cortex state log."""
    try:
        from app.cortex.state_log import query

        return {
            "executions": query(observation_type="execution_summary", limit=20),
            "proposals": query(observation_type="proposal", limit=20),
            "ai_responses": query(observation_type="ai", limit=20),
        }
    except Exception as e:
        logger.debug("Awareness: could not fetch observations: %s", e)
        return {"executions": [], "proposals": [], "ai_responses": []}


def _detect_idle_entities() -> list:
    """Detect entities with no recent activity."""
    signals = []
    try:
        from app.objects.models import Object
        from app import db

        # Find entities with no updates in the last 2 hours
        cutoff = datetime.now(timezone.utc) - timedelta(hours=2)
        idle = Object.query.filter(
            Object.updated_at < cutoff
        ).limit(10).all()

        for entity in idle:
            state = entity.state or {}
            signals.append({
                "type": "idle_entity",
                "severity": "medium",
                "entity_id": entity.id,
                "entity_name": state.get("name", f"Entity #{entity.id}"),
                "reason": f"No activity since {entity.updated_at.strftime('%H:%M UTC') if entity.updated_at else 'unknown'}",
                "suggested_action": "Run loop or check entity status",
            })
    except Exception as e:
        logger.debug("Awareness: idle detection failed: %s", e)
    return signals


def _detect_failed_cycles(observations: dict) -> list:
    """Detect execution cycles with errors."""
    signals = []
    try:
        executions = observations.get("executions", [])
        failed = [e for e in executions if e.get("data", {}).get("status") == "partial"]
        if failed:
            last = failed[0]
            errors = last.get("data", {}).get("errors", 0)
            signals.append({
                "type": "failed_cycle",
                "severity": "high" if errors > 3 else "medium",
                "reason": f"{errors} errors in last execution cycle",
                "suggested_action": "Investigate execution logs",
                "count": len(failed),
            })
    except Exception as e:
        logger.debug("Awareness: failed cycle detection failed: %s", e)
    return signals


def _detect_stuck_entities(observations: dict) -> list:
    """Detect entities stuck in the same state (repeated noops)."""
    signals = []
    try:
        executions = observations.get("executions", [])
        total_noops = sum(e.get("data", {}).get("noops", 0) for e in executions[:5])
        if total_noops > 10:
            signals.append({
                "type": "stuck_entities",
                "severity": "medium",
                "reason": f"{total_noops} consecutive noops — entities may be stuck",
                "suggested_action": "Check entity states and decision rules",
                "noop_count": total_noops,
            })
    except Exception as e:
        logger.debug("Awareness: stuck entity detection failed: %s", e)
    return signals


def _detect_high_fallback(observations: dict) -> list:
    """Detect high AI fallback usage (LLM provider chain)."""
    signals = []
    try:
        ai_responses = observations.get("ai_responses", [])
        fallback_count = sum(1 for a in ai_responses if a.get("data", {}).get("fallback_used"))
        if fallback_count > 3:
            signals.append({
                "type": "high_ai_fallback",
                "severity": "medium",
                "reason": f"{fallback_count} AI responses used fallback providers",
                "suggested_action": "Check LLM provider API keys",
                "fallback_count": fallback_count,
            })
    except Exception as e:
        logger.debug("Awareness: fallback detection failed: %s", e)
    return signals


def _detect_unexecuted_proposals(observations: dict) -> list:
    """Detect proposals that have been pending for too long."""
    signals = []
    try:
        from app.communication.models import MessageProposal

        pending = MessageProposal.query.filter_by(status="pending").all()
        for p in pending:
            if p.created_at and (datetime.now(timezone.utc) - p.created_at).total_seconds() > 3600:
                signals.append({
                    "type": "unexecuted_proposal",
                    "severity": "high",
                    "proposal_id": p.id,
                    "entity_id": p.entity_id,
                    "reason": f"Proposal #{p.id} pending for >1 hour",
                    "suggested_action": "Review and approve/reject in workspace",
                })
    except Exception as e:
        logger.debug("Awareness: unexecuted proposal detection failed: %s", e)
    return signals


def scan() -> list:
    """Run all awareness detectors and return structured signals.

    Returns:
        List of awareness signal dicts, each with:
        - type: str
        - severity: 'low'|'medium'|'high'
        - reason: str
        - suggested_action: str
        - additional fields per type
    """
    observations = _get_observations()
    signals = []

    try:
        signals.extend(_detect_idle_entities())
        signals.extend(_detect_failed_cycles(observations))
        signals.extend(_detect_stuck_entities(observations))
        signals.extend(_detect_high_fallback(observations))
        signals.extend(_detect_unexecuted_proposals(observations))

        # Store awareness signals in state_log
        try:
            from app.cortex.state_log import store
            for signal in signals:
                store(
                    observation_type="awareness_signal",
                    data=signal,
                    entity_id=signal.get("entity_id"),
                )
        except Exception:
            pass

        if signals:
            logger.info(
                "Awareness scan: %d signals (idle=%d, failed=%d, stuck=%d, fallback=%d, unexecuted=%d)",
                len(signals),
                len([s for s in signals if s["type"] == "idle_entity"]),
                len([s for s in signals if s["type"] == "failed_cycle"]),
                len([s for s in signals if s["type"] == "stuck_entities"]),
                len([s for s in signals if s["type"] == "high_ai_fallback"]),
                len([s for s in signals if s["type"] == "unexecuted_proposal"]),
            )

    except Exception as e:
        logger.error("Awareness scan failed: %s", e)

    return signals