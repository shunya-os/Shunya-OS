"""Cortex State Log — persistent storage for all cortex observations.

PHASE 2C: Stores execution summaries, proposals, and AI responses.
Persisted via ExecutionLog with event_type='CORTEX_OBSERVATION'.
Queryable by type, time range, and entity.
"""

import json
import logging
from datetime import datetime, timezone, timedelta
from typing import Any, Optional

logger = logging.getLogger(__name__)


def store(
    observation_type: str,
    data: dict,
    entity_id: Optional[int] = None,
) -> dict:
    """Persist a cortex observation to the execution log.

    Args:
        observation_type: 'execution_summary' | 'proposal' | 'ai'
        data: The observation data dict
        entity_id: Optional entity this relates to

    Returns:
        The stored record with timestamp.
    """
    record = {
        "type": observation_type,
        "data": data,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "entity_id": entity_id,
    }

    try:
        from app.execution_log.models import log_execution as log_to_db
        log_to_db(
            object_id=entity_id or 0,
            event_type="CORTEX_OBSERVATION",
            payload=record,
        )
    except Exception as e:
        logger.debug("Cortex state_log store failed: %s", e)

    return record


def query(
    observation_type: Optional[str] = None,
    since_minutes: Optional[int] = None,
    entity_id: Optional[int] = None,
    limit: int = 50,
) -> list:
    """Query cortex observations from the execution log.

    Args:
        observation_type: Filter by type ('execution_summary'|'proposal'|'ai')
        since_minutes: Only observations from last N minutes
        entity_id: Filter by entity
        limit: Max results

    Returns:
        List of observation records, newest first.
    """
    try:
        from app.execution_log.models import ExecutionLog
        from app import db

        q = ExecutionLog.query.filter_by(event_type="CORTEX_OBSERVATION")

        if entity_id is not None:
            q = q.filter(ExecutionLog.object_id == entity_id)
        if since_minutes is not None:
            cutoff = datetime.now(timezone.utc) - timedelta(minutes=since_minutes)
            q = q.filter(ExecutionLog.timestamp >= cutoff)

        results = q.order_by(ExecutionLog.timestamp.desc()).limit(limit).all()

        parsed = []
        for r in results:
            payload = r.payload or {}
            # Filter by observation_type if specified
            if observation_type and payload.get("type") != observation_type:
                continue
            parsed.append(payload)

        return parsed

    except Exception as e:
        logger.debug("Cortex state_log query failed: %s", e)
        return []


def get_latest(
    observation_type: str,
    entity_id: Optional[int] = None,
) -> Optional[dict]:
    """Get the most recent observation of a given type."""
    results = query(observation_type=observation_type, entity_id=entity_id, limit=1)
    return results[0] if results else None


def count_by_type() -> dict:
    """Count observations by type for a quick dashboard."""
    try:
        from app.execution_log.models import ExecutionLog
        from app import db
        from sqlalchemy import text

        # Use raw SQL for efficient counting
        results = db.session.execute(
            text("""
                SELECT payload->>'type' as obs_type, COUNT(*) as count
                FROM act_execution_logs
                WHERE event_type = 'CORTEX_OBSERVATION'
                GROUP BY obs_type
                ORDER BY count DESC
            """)
        ).fetchall()

        return {r[0] or "unknown": r[1] for r in results}
    except Exception as e:
        logger.debug("Cortex state_log count_by_type failed: %s", e)
        return {}