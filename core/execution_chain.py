"""
SHUNYAAI Execution Chain — Governed bridge between SHUNYAAI processing
and durable execution/decision/evidence/observation/outcome records.

Every query processed by ask() that is recognized as an action produces:
  DecisionTrace → Execution → EvidenceRecord → Observation → Outcome

Read-only queries produce: EvidenceRecord + Observation (for auditability).

This is the canonical P0 remediation of the broken evidence chain.
"""

from __future__ import annotations

import uuid
import json
import logging
from datetime import datetime, timezone
from typing import Any

from app import db
from app.evidence.models_db import EvidenceRecord
from app.execution_engine.models import Execution, ExecutionLog
from app.execution.models import Outcome
from app.shunya.observer_learning import Observation

logger = logging.getLogger(__name__)


def _now() -> datetime:
    return datetime.now(timezone.utc)


def record_decision_trace(
    decision_text: str,
    source: str = "shunyaai",
    confidence: float = 0.0,
    object_id: int | None = None,
) -> int | None:
    """Record a decision in decision_traces. Returns the trace ID."""
    try:
        from app.evidence.decision_trace import DecisionTrace
        trace = DecisionTrace(
            object_id=object_id or 0,
            main_decision={"text": decision_text[:500], "source": source},
            source=source,
            confidence=confidence,
            execution_status="pending",
            created_at=_now(),
        )
        db.session.add(trace)
        db.session.flush()
        trace_id = trace.id
        db.session.commit()
        return trace_id
    except Exception as e:
        db.session.rollback()
        logger.warning(f"record_decision_trace failed: {e}")
        return None


def record_execution(
    action_type: str = "shunyaai_action",
    object_id: int | None = None,
    identity_id: str | None = None,
) -> int | None:
    """Record an execution. Returns the execution ID."""
    try:
        exec_record = Execution(
            object_id=object_id or 0,
            decision=action_type[:255],
            status="completed",
            created_at=_now(),
            updated_at=_now(),
        )
        db.session.add(exec_record)
        db.session.flush()
        exec_id = exec_record.id

        # Also log to execution_logs
        log = ExecutionLog(
            object_id=object_id or 0,
            action_type=action_type[:255],
            payload={"action": action_type[:255], "identity_id": identity_id or ""},
            state_before={},
            state_after={"status": "completed"},
            created_at=_now(),
        )
        db.session.add(log)
        db.session.commit()
        return exec_id
    except Exception as e:
        db.session.rollback()
        logger.warning(f"record_execution failed: {e}")
        return None


def record_evidence(
    source_type: str = "ai",
    source_id: str | None = None,
    content: dict | None = None,
    tenant_id: int | None = None,
    identity_id: str | None = None,
) -> int | None:
    """Record evidence. Returns the evidence record ID."""
    try:
        ev = EvidenceRecord(
            source_type=source_type,
            source_id=source_id or "",
            raw_reference=content or {"text": ""},
            created_at=_now(),
        )
        db.session.add(ev)
        db.session.flush()
        ev_id = ev.id
        db.session.commit()
        return ev_id
    except Exception as e:
        db.session.rollback()
        logger.warning(f"record_evidence failed: {e}")
        return None


def record_observation(
    action: str = "shunyaai_query",
    actual_outcome: str | None = None,
    success: bool = True,
    confidence: float = 1.0,
    metadata: dict | None = None,
    tenant_id: int = 0,
) -> int | None:
    """Record an observation. Uses raw SQL because the observations table
    has columns (tenant_id, subject_type, etc.) added by migration that
    the model class doesn't expose."""
    try:
        import json as _json
        result = db.session.execute(
            db.text("""
                INSERT INTO observations
                    (tenant_id, subject_type, subject_id, event, source, observer,
                     expected_state, actual_state, delta, severity, confidence,
                     metadata_json, created_at, action, channel, discrepancy, success)
                VALUES
                    (:tenant_id, :subject_type, :subject_id, :event, :source, :observer,
                     :expected_state, :actual_state, :delta, :severity, :confidence,
                     :metadata_json, :created_at, :action, :channel, :discrepancy, :success)
                RETURNING id
            """),
            {
                "tenant_id": tenant_id,
                "subject_type": "ai",
                "subject_id": 0,
                "event": action[:60],
                "source": "shunyaai",
                "observer": "shunyaai_execution_chain",
                "expected_state": "",
                "actual_state": actual_outcome or "",
                "delta": "",
                "severity": "info",
                "confidence": confidence,
                "metadata_json": _json.dumps(metadata or {}),
                "created_at": _now(),
                "action": action[:60],
                "channel": "internal",
                "discrepancy": "",
                "success": success,
            }
        )
        db.session.commit()
        obs_id = result.scalar()
        return obs_id
    except Exception as e:
        db.session.rollback()
        logger.warning(f"record_observation failed: {e}")
        return None


def record_outcome(
    identity_id: str | None = None,
    intention: str | None = None,
    state: dict | None = None,
) -> str | None:
    """Record an outcome. Returns the outcome ID."""
    try:
        outcome_id = f"o{uuid.uuid4().hex[:11]}"
        outcome = Outcome(
            outcome_id=outcome_id,
            identity_id=identity_id or "anonymous",
            intention=intention or "",
            state=state or {},
            created_at=_now(),
            updated_at=_now(),
        )
        db.session.add(outcome)
        db.session.commit()
        return outcome_id
    except Exception as e:
        db.session.rollback()
        logger.warning(f"record_outcome failed: {e}")
        return None


def record_full_chain(
    query: str,
    action_type: str | None = None,
    identity_id: str | None = None,
    tenant_id: int | None = None,
    confidence: float = 0.0,
    response_summary: str | None = None,
    success: bool = True,
) -> dict[str, Any]:
    """Record the complete execution chain for a SHUNYAAI interaction.

    For read-only queries: evidence + observation
    For action queries: decision + execution + evidence + observation + outcome

    Returns a dict with all recorded IDs so the ask() response can include them.
    """
    result: dict[str, Any] = {
        "decision_trace_id": None,
        "execution_id": None,
        "evidence_id": None,
        "observation_id": None,
        "outcome_id": None,
    }

    is_action = action_type is not None and action_type in (
        "create", "update", "delete", "execute", "send",
        "approve", "reject", "assign", "transfer",
    )

    source_type = "ai_action" if is_action else "ai_query"
    source_id = f"ask_{uuid.uuid4().hex[:8]}"

    # Evidence is always recorded
    ev_id = record_evidence(
        source_type=source_type,
        source_id=source_id,
        content={"text": (response_summary or query)[:500], "query": query[:200]},
        tenant_id=tenant_id,
        identity_id=identity_id,
    )
    result["evidence_id"] = ev_id

    # Observation is always recorded
    obs_id = record_observation(
        action=source_type,
        actual_outcome=(response_summary or query)[:200],
        success=success,
        confidence=confidence,
        metadata={"query": query[:200], "action_type": action_type, "is_action": is_action},
        tenant_id=tenant_id or 0,
    )
    result["observation_id"] = obs_id

    if is_action:
        # Record decision
        dt_id = record_decision_trace(
            decision_text=query[:500],
            source="shunyaai",
            confidence=confidence,
        )
        result["decision_trace_id"] = dt_id

        # Record execution
        exec_id = record_execution(
            action_type=action_type or query[:255],
            identity_id=identity_id,
        )
        result["execution_id"] = exec_id

        # Record outcome
        outcome_id = record_outcome(
            identity_id=identity_id,
            intention=query[:500],
            state={
                "type": "shunyaai_action",
                "action_type": action_type,
                "query": query[:200],
                "success": success,
                "evidence_id": ev_id,
                "execution_id": exec_id,
            },
        )
        result["outcome_id"] = outcome_id

    return result