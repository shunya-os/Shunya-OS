"""Evidence service — structured observability for execution, proposals, and AI.

PHASE 2A: Attach to run_cycle(), MessageProposal creation, and AI responses.
PHASE 2A-FIX: confidence is now float 0.0-1.0 with confidence_label for display.
Added evidence_type for filtering (execution|ai|proposal).
"""

import logging
from datetime import datetime, timezone
from typing import Any, Optional

logger = logging.getLogger(__name__)


def _float_confidence(value: Any) -> float:
    """Normalize confidence to float 0.0-1.0."""
    if isinstance(value, (int, float)):
        return max(0.0, min(1.0, float(value)))
    if isinstance(value, str):
        mapping = {"high": 0.92, "medium": 0.65, "low": 0.35}
        return mapping.get(value.lower(), 0.5)
    return 0.5


def _label_from_confidence(confidence: float) -> str:
    """Convert float confidence to human label."""
    if confidence >= 0.8:
        return "high"
    if confidence >= 0.5:
        return "medium"
    return "low"


def log_evidence(
    action: str,
    source: str,
    confidence: Any = 0.5,
    evidence_type: str = "execution",
    entity_id: Optional[int] = None,
    inputs: Optional[dict] = None,
    outputs: Optional[dict] = None,
    metadata: Optional[dict] = None,
) -> dict:
    """Log a structured evidence record.

    Args:
        action: What was done (e.g., "run_cycle", "create_proposal", "ai_response")
        source: Where it came from (e.g., "rule_engine", "effect_engine", "mixed_intelligence")
        confidence: Float 0.0-1.0. Accepts string ("high"/"medium"/"low") for backward compat.
        evidence_type: Category for filtering — "execution" | "ai" | "proposal"
        entity_id: Optional entity this relates to
        inputs: What went into the decision
        outputs: What came out
        metadata: Additional context

    Returns:
        The evidence record as a dict.
    """
    confidence_float = _float_confidence(confidence)

    record = {
        "action": action,
        "source": source,
        "confidence": confidence_float,
        "confidence_label": _label_from_confidence(confidence_float),
        "evidence_type": evidence_type,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "entity_id": entity_id,
        "inputs": inputs or {},
        "outputs": outputs or {},
        "metadata": metadata or {},
    }

    # Store in execution log for persistence
    try:
        from app.execution_log.models import log_execution as log_to_db
        log_to_db(
            object_id=entity_id or 0,
            event_type="EVIDENCE",
            payload=record,
        )
    except Exception as e:
        logger.debug("Could not persist evidence: %s", e)

    # Also log to Python logger
    logger.info(
        "EVIDENCE: action=%s source=%s confidence=%.2f (%s) type=%s entity=%s",
        action, source, confidence_float, record["confidence_label"],
        evidence_type, entity_id,
    )

    return record