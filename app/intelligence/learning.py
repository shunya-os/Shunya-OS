"""Basic Learning Loop — adjusts confidence based on execution outcomes.

PHASE 3.3: If execution fails, reduce confidence for similar decisions.
If success, increase confidence. Simple weight-based system.
"""

import json
import logging
from typing import Any, Optional

logger = logging.getLogger(__name__)


def _load_weights() -> dict:
    """Load learning weights from the execution log."""
    weights = {"signal_type": {}, "entity_type": {}, "default": 0.5}
    try:
        from app.evidence.decision_trace import DecisionTrace
        traces = DecisionTrace.query.order_by(DecisionTrace.id.desc()).limit(50).all()
        for t in traces:
            fd = t.final_decision or {}
            sig_type = fd.get("signal_type", "unknown")
            entity_type = fd.get("entity_type", "unknown")
            status = t.execution_status
            if status == "success":
                weights["signal_type"][sig_type] = weights["signal_type"].get(sig_type, 0.5) + 0.05
                weights["entity_type"][entity_type] = weights["entity_type"].get(entity_type, 0.5) + 0.05
            elif status == "failed":
                weights["signal_type"][sig_type] = max(0.0, weights["signal_type"].get(sig_type, 0.5) - 0.1)
                weights["entity_type"][entity_type] = max(0.0, weights["entity_type"].get(entity_type, 0.5) - 0.1)
    except Exception as e:
        logger.debug("Learning: could not load weights: %s", e)
    return weights


def adjust_confidence(decision: dict, execution_result: dict) -> float:
    """Adjust decision confidence based on learned weights.

    Args:
        decision: The decision dict
        execution_result: dict with 'status' ('success'|'failed') and 'error'

    Returns:
        Adjusted confidence score (0.0-1.0)
    """
    base_conf = decision.get("confidence", 0.5)
    signal_type = decision.get("signal_type", "unknown")

    weights = _load_weights()
    signal_weight = weights["signal_type"].get(signal_type, weights["default"])
    entity_weight = weights.get("entity_type", {}).get(decision.get("entity_type", ""), weights["default"])

    # Blend: base * (signal_weight + entity_weight) / 2
    adjusted = base_conf * ((signal_weight + entity_weight) / 2)
    adjusted = max(0.0, min(1.0, adjusted))

    logger.debug(
        "Learning: %s base=%.2f signal=%.2f entity=%.2f -> adjusted=%.2f",
        signal_type, base_conf, signal_weight, entity_weight, adjusted,
    )
    return round(adjusted, 3)


def record_outcome(decision: dict, execution_status: str, error_message: str = None):
    """Record an execution outcome to inform future learning.

    This is called after execution completes.
    """
    try:
        from app.evidence.decision_trace import DecisionTrace
        # Find the most recent trace for this decision's entity
        entity_id = decision.get("entity_id")
        if entity_id:
            trace = DecisionTrace.query.filter_by(
                object_id=entity_id
            ).order_by(DecisionTrace.id.desc()).first()
            if trace:
                trace.execution_status = execution_status
                trace.error_message = error_message
                from app.core.db import get_session
                get_session().flush()
                logger.info(
                    "Learning: recorded outcome for entity %d: %s",
                    entity_id, execution_status,
                )
    except Exception as e:
        logger.debug("Learning: could not record outcome: %s", e)
