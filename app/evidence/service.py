"""Evidence service — structured observability for execution, proposals, and AI.

PHASE 2A: Attach to run_cycle(), MessageProposal creation, and AI responses.
This is the trust layer — every action is traceable to its source.
"""

import json
import logging
from datetime import datetime, timezone
from typing import Any, Optional

logger = logging.getLogger(__name__)


def log_evidence(
    action: str,
    source: str,
    confidence: str,
    entity_id: Optional[int] = None,
    inputs: Optional[dict] = None,
    outputs: Optional[dict] = None,
    metadata: Optional[dict] = None,
) -> dict:
    """Log a structured evidence record.

    Args:
        action: What was done (e.g., "run_cycle", "create_proposal", "ai_response")
        source: Where it came from (e.g., "rule_engine", "effect_engine", "mixed_intelligence")
        confidence: How confident (high/medium/low)
        entity_id: Optional entity this relates to
        inputs: What went into the decision
        outputs: What came out
        metadata: Additional context

    Returns:
        The evidence record as a dict.
    """
    record = {
        "action": action,
        "source": source,
        "confidence": confidence,
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
        "EVIDENCE: action=%s source=%s confidence=%s entity=%s",
        action, source, confidence, entity_id,
    )

    return record