"""Basic Learning Loop — adjusts confidence based on execution outcomes.

PHASE 3.3: If execution fails, reduce confidence for similar decisions.
If success, increase confidence. Simple weight-based system.

PHASE 3.4: Uses persistent memory_store for weights.
Learning affects future decisions automatically.
"""

import json
import logging
from typing import Any, Optional

from app.intelligence.memory_store import get_weight, record_success, record_failure

logger = logging.getLogger(__name__)


def adjust_confidence(decision: dict, execution_result: dict) -> float:
    """Adjust decision confidence based on learned weights AND per-object history.

    PHASE 3.4: Differentiates between objects by their OWN execution history.
    Object with failure history gets lower confidence than one with success history.

    Args:
        decision: The decision dict (must include entity_id)
        execution_result: dict with 'status' ('success'|'failed') and 'error'

    Returns:
        Adjusted confidence score (0.0-1.0)
    """
    base_conf = decision.get("confidence", 0.5)
    signal_type = decision.get("signal_type", "unknown")
    entity_type = decision.get("entity_type", "unknown")
    entity_id = decision.get("entity_id")

    # Load learned weights from persistent memory_store (global signal weights)
    signal_weight = get_weight(f"signal:{signal_type}")
    entity_weight = get_weight(f"entity:{entity_type}")

    # Per-object history weight (differentiates objects)
    object_weight = 0.5
    if entity_id:
        try:
            from app.evidence.decision_trace import DecisionTrace
            traces = DecisionTrace.query.filter_by(object_id=entity_id).order_by(DecisionTrace.id.desc()).limit(10).all()
            if traces:
                successes = sum(1 for t in traces if t.execution_status == "success")
                failures = sum(1 for t in traces if t.execution_status in ("failed", "error"))
                total = successes + failures
                if total > 0:
                    # Object success ratio: 0.0 (all fail) to 1.0 (all succeed)
                    object_weight = successes / total
                # Recent failure heavily penalizes
                if traces and traces[0].execution_status in ("failed", "error"):
                    object_weight = min(object_weight, 0.3)
                elif traces and traces[0].execution_status == "success":
                    object_weight = max(object_weight, 0.7)
        except Exception:
            pass

    # Blend all three weights
    adjusted = base_conf * ((signal_weight + entity_weight + object_weight) / 3)
    adjusted = max(0.0, min(1.0, adjusted))

    logger.debug(
        "Learning: %s base=%.2f signal=%.2f entity=%.2f object=%.2f -> adjusted=%.2f",
        signal_type, base_conf, signal_weight, entity_weight, object_weight, adjusted,
    )
    return round(adjusted, 3)


def record_outcome(decision: dict, execution_status: str, error_message: str = None):
    """Record an execution outcome to inform future learning.

    Uses persistent memory_store. Success boosts confidence,
    failure reduces it. Patterns are tagged for failure analysis.
    """
    signal_type = decision.get("signal_type", "unknown")
    entity_type = decision.get("entity_type", "unknown")

    if execution_status == "success":
        record_success(signal_type, entity_type)
    elif execution_status in ("failed", "error"):
        pattern = decision.get("signal_type", "unknown")
        record_failure(signal_type, entity_type, pattern=pattern)

    # Also update the decision trace if available
    try:
        from app.evidence.decision_trace import DecisionTrace
        from app.core.db import get_session
        entity_id = decision.get("entity_id")
        if entity_id:
            trace = DecisionTrace.query.filter_by(
                object_id=entity_id
            ).order_by(DecisionTrace.id.desc()).first()
            if trace:
                trace.execution_status = execution_status
                trace.error_message = error_message
                get_session().flush()
    except Exception as e:
        logger.debug("Learning: could not record outcome: %s", e)
