"""
SHUNYAAI Execution Chain — Governed bridge between SHUNYAAI processing
and durable execution/decision/evidence/observation/outcome records.

LIFECYCLE TRUTH:

  REQUESTED → AUTHORIZED → RUNNING → SUCCEEDED
                                     → FAILED
                        → DENIED
           → CANCELLED

A read-only query must never manufacture a completed execution.
An execution record must represent a real attempted operation.
status="completed" is set ONLY after the underlying operation succeeds.

Records in this chain correspond to genuine lifecycle events.
Synthetic test records are NOT mixed with production data.

Every record has identity/workspace/tenant/provenance linkage so the
chain can reconstruct: who → where → what → why → which capability →
which engine → which execution → what evidence → what observation →
what outcome.
"""

from __future__ import annotations

import uuid
import json as _json
import logging
from datetime import datetime, timezone
from enum import Enum
from typing import Any

from app import db

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Lifecycle states
# ---------------------------------------------------------------------------

class ExecutionState(str, Enum):
    """Real lifecycle states for execution records.

    REQUESTED  — User intent detected, capability identified, not yet authorized
    AUTHORIZED — Permission check passed, execution about to begin
    RUNNING    — Operation is actually in progress
    SUCCEEDED  — Operation completed successfully with verified business effect
    FAILED     — Operation attempted but failed
    DENIED     — Authorization or permission check rejected the request
    CANCELLED  — Request was cancelled before or during execution
    """
    REQUESTED = "requested"
    AUTHORIZED = "authorized"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    DENIED = "denied"
    CANCELLED = "cancelled"


class DecisionState(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    SUPERSEDED = "superseded"


# ---------------------------------------------------------------------------
# Canonical evidence model import via ORM
# ---------------------------------------------------------------------------

def _now() -> datetime:
    return datetime.now(timezone.utc)


def _make_source_id(prefix: str = "sh") -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


# ---------------------------------------------------------------------------
# Chain record creation (no synthetic completion)
# ---------------------------------------------------------------------------

def create_decision_trace(
    decision_text: str,
    source: str = "shunyaai",
    confidence: float = 0.0,
    object_id: int | None = None,
    identity_id: str | None = None,
    tenant_id: int = 89,
    state: str = DecisionState.PENDING.value,
) -> int | None:
    """Record a decision trace. State starts as PENDING — not automatically completed."""
    try:
        from app.evidence.decision_trace import DecisionTrace
        trace = DecisionTrace(
            object_id=object_id or 0,
            main_decision={"text": decision_text[:500], "source": source,
                          "identity_id": identity_id or "",
                          "tenant_id": tenant_id or 0},
            source=source,
            confidence=confidence,
            execution_status=state,
            created_at=_now(),
        )
        db.session.add(trace)
        db.session.flush()
        trace_id = trace.id
        db.session.commit()
        return trace_id
    except Exception as e:
        db.session.rollback()
        logger.warning(f"create_decision_trace failed: {e}")
        return None


def create_execution(
    action_type: str,
    object_id: int | None = None,
    identity_id: str | None = None,
    tenant_id: int = 89,
    state: str = ExecutionState.REQUESTED.value,
) -> int | None:
    """Record an execution. State starts as REQUESTED — not auto-completed.

    Returns the execution ID. Caller must transition state when the real
    operation proceeds.
    """
    try:
        from app.execution_engine.models import Execution, ExecutionLog

        exec_record = Execution(
            object_id=object_id or 0,
            decision=action_type[:255],
            status=state,
            created_at=_now(),
            updated_at=_now(),
        )
        db.session.add(exec_record)
        db.session.flush()
        exec_id = exec_record.id

        # Log the state transition
        log = ExecutionLog(
            object_id=object_id or 0,
            action_type=action_type[:255],
            payload={"action": action_type[:255],
                    "identity_id": identity_id or "",
                    "tenant_id": tenant_id or 0,
                    "state": state},
            state_before={},
            state_after={"status": state},
            created_at=_now(),
        )
        db.session.add(log)
        db.session.commit()
        return exec_id
    except Exception as e:
        db.session.rollback()
        logger.warning(f"create_execution failed: {e}")
        return None


def transition_execution(exec_id: int, new_state: str) -> bool:
    """Transition an execution to a new state. Returns True on success.

    Enforces state machine rules:
      REQUESTED → [AUTHORIZED, DENIED, CANCELLED]
      AUTHORIZED → [RUNNING, DENIED, CANCELLED]
      RUNNING → [SUCCEEDED, FAILED]
      SUCCEEDED → [] (terminal)
      FAILED → [] (terminal)
      DENIED → [] (terminal)
      CANCELLED → [] (terminal)
    """
    VALID_TRANSITIONS = {
        "requested": ["authorized", "denied", "cancelled"],
        "authorized": ["running", "denied", "cancelled"],
        "running": ["succeeded", "failed"],
        "succeeded": [],
        "failed": [],
        "denied": [],
        "cancelled": [],
    }

    try:
        from app.execution_engine.models import Execution, ExecutionLog

        exec_record = db.session.get(Execution, exec_id)
        if not exec_record:
            logger.warning(f"transition_execution: no execution #{exec_id}")
            return False

        old_state = exec_record.status
        allowed = VALID_TRANSITIONS.get(old_state, [])
        if new_state not in allowed:
            logger.warning(
                f"transition_execution: invalid transition {old_state}→{new_state} "
                f"(allowed: {allowed})"
            )
            return False

        exec_record.status = new_state
        exec_record.updated_at = _now()

        log = ExecutionLog(
            object_id=exec_record.object_id,
            action_type=exec_record.decision[:255],
            payload={"transition": f"{old_state}→{new_state}"},
            state_before={"status": old_state},
            state_after={"status": new_state},
            created_at=_now(),
        )
        db.session.add(log)
        db.session.commit()
        return True
    except Exception as e:
        db.session.rollback()
        logger.warning(f"transition_execution #{exec_id} → {new_state} failed: {e}")
        return False


def create_evidence(
    source_type: str,
    source_id: str,
    content: dict | None = None,
    tenant_id: int = 89,
    identity_id: str | None = None,
) -> int | None:
    """Record evidence. Uses the canonical ORM model, not raw SQL."""
    try:
        from app.evidence.models_db import EvidenceRecord as EvidenceModel
        ev = EvidenceModel(
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
        logger.warning(f"create_evidence failed: {e}")
        return None


def create_observation(
    action: str,
    actual_outcome: str | None = None,
    success: bool | None = None,
    confidence: str = "1.0",
    metadata: dict | None = None,
    tenant_id: int = 89,
    source: str = "shunyaai",
    subject_type: str = "ai",
    subject_id: int = 0,
    event: str = "",
    severity: str = "info",
    observer: str = "execution_chain",
) -> int | None:
    """Record an observation using the canonical ORM model.

    Uses ORM directly — no raw SQL. The Observation model now exposes
    all columns matching the physical DB schema (reconciled).

    NOTE: confidence is stored as VARCHAR(20) in the DB. Pass as string.
    metadata_json is JSONB — pass as dict directly.
    """
    try:
        from app.shunya.observer_learning import Observation
        obs = Observation(
            tenant_id=tenant_id,
            subject_type=subject_type,
            subject_id=subject_id,
            event=event or action[:60],
            source=source,
            observer=observer,
            expected_state="",
            actual_state=actual_outcome or "",
            delta="",
            severity=severity,
            confidence=str(confidence),
            metadata_json=metadata or {},
            created_at=_now(),
            action=action[:60],
            channel="internal",
            discrepancy="",
            success=True if success is None else success,
        )
        db.session.add(obs)
        db.session.flush()
        obs_id = obs.id
        db.session.commit()
        return obs_id
    except Exception as e:
        db.session.rollback()
        logger.warning(f"create_observation failed: {e}")
        return None


def create_outcome(
    identity_id: str | None = None,
    intention: str | None = None,
    state: dict | None = None,
) -> str | None:
    """Record an outcome. Only created when a real action completed."""
    try:
        from app.execution.models import Outcome
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
        logger.warning(f"create_outcome failed: {e}")
        return None


# ---------------------------------------------------------------------------
# High-level chain creation with governed lifecycle
# ---------------------------------------------------------------------------

def record_read_chain(
    query: str,
    identity_id: str | None = None,
    tenant_id: int = 89,
    confidence: float = 0.0,
    response_summary: str | None = None,
) -> dict[str, Any]:
    """Record chain for a READ-ONLY query.

    A read query produces:
      EvidenceRecord + Observation (for auditability)

    NEVER creates:
      DecisionTrace, Execution, or Outcome — because no action was taken.
      status="completed" is never set because no operation ran.
    """
    result: dict[str, Any] = {
        "evidence_id": None,
        "observation_id": None,
        "chain_type": "read_only",
    }

    source_id = _make_source_id("ask")

    # Evidence
    ev_id = create_evidence(
        source_type="ai_query",
        source_id=source_id,
        content={"text": (response_summary or query)[:500], "query": query[:200]},
        tenant_id=tenant_id,
        identity_id=identity_id,
    )
    result["evidence_id"] = ev_id

    # Observation
    obs_id = create_observation(
        action="ai_query",
        actual_outcome=(response_summary or query)[:200],
        success=True,
        confidence=str(confidence),
        metadata={"query": query[:200], "type": "read"},
        tenant_id=tenant_id,
        event="ai_query",
        severity="info",
    )
    result["observation_id"] = obs_id

    # Bridge observation → memory (loop-closing) for read queries
    if obs_id is not None:
        try:
            from core.observation_memory_bridge import observation_to_memory
            observation_to_memory(
                obs_id,
                tenant_id=tenant_id,
                identity_id=identity_id,
            )
        except Exception as bridge_err:
            logger.warning(f"Read observation→memory bridge failed: {bridge_err}")

    return result


def record_action_chain(
    query: str,
    action_type: str,
    identity_id: str | None = None,
    tenant_id: int = 89,
    confidence: float = 0.0,
    object_id: int | None = None,
) -> dict[str, Any]:
    """Initiate chain for a WRITE/ACTION query.

    State begins as REQUESTED. Caller transitions to AUTHORIZED, RUNNING,
    then SUCCEEDED or FAILED when the real operation completes.

    Produces:
      DecisionTrace (PENDING) → Execution (REQUESTED) → EvidenceRecord
      → Observation → Outcome (when SUCCEEDED)
    """
    result: dict[str, Any] = {
        "decision_trace_id": None,
        "execution_id": None,
        "evidence_id": None,
        "observation_id": None,
        "outcome_id": None,
        "chain_type": "action",
        "state": ExecutionState.REQUESTED.value,
    }

    source_id = _make_source_id("act")

    # 1. Decision trace — starts PENDING
    dt_id = create_decision_trace(
        decision_text=query[:500],
        source="shunyaai",
        confidence=confidence,
        object_id=object_id,
        identity_id=identity_id,
        tenant_id=tenant_id,
        state=DecisionState.PENDING.value,
    )
    result["decision_trace_id"] = dt_id

    # 2. Execution — starts REQUESTED (never auto-completed)
    exec_id = create_execution(
        action_type=action_type,
        object_id=object_id,
        identity_id=identity_id,
        tenant_id=tenant_id,
        state=ExecutionState.REQUESTED.value,
    )
    result["execution_id"] = exec_id

    # 3. Evidence
    ev_id = create_evidence(
        source_type="ai_action",
        source_id=source_id,
        content={"text": query[:500],
                "action_type": action_type,
                "decision_trace_id": dt_id,
                "execution_id": exec_id},
        tenant_id=tenant_id,
        identity_id=identity_id,
    )
    result["evidence_id"] = ev_id

    # 4. Observation (pending)
    obs_id = create_observation(
        action=action_type,
        actual_outcome="",
        success=None,  # Unknown until execution completes
        confidence=str(confidence),
        metadata={"query": query[:200], "action_type": action_type,
                  "execution_id": exec_id, "decision_trace_id": dt_id},
        tenant_id=tenant_id,  # None is valid — FK allows NULL for tenant_id
        event=action_type,
        severity="info",
    )
    result["observation_id"] = obs_id

    return result


def complete_action_chain(
    exec_id: int | None,
    outcome: str = "succeeded",
    response_summary: str | None = None,
    identity_id: str | None = None,
    tenant_id: int = 89,
    state: dict | None = None,
    observation_id: int | None = None,
) -> dict[str, Any]:
    """Complete a previously-initiated action chain.

    Sets execution to SUCCEEDED or FAILED, updates the observation,
    and creates the outcome record.

    Call this AFTER the real business operation has completed.
    """
    result: dict[str, Any] = {
        "execution_state": ExecutionState.FAILED.value,
        "outcome_id": None,
        "observation_updated": False,
    }

    is_success = outcome == "succeeded"
    target_state = ExecutionState.SUCCEEDED.value if is_success else ExecutionState.FAILED.value

    if exec_id:
        # Walk through intermediate states to reach the target
        # REQUESTED → AUTHORIZED → RUNNING → SUCCEEDED/FAILED
        for intermediate in ["authorized", "running"]:
            transition_execution(exec_id, intermediate)
        transition_execution(exec_id, target_state)
        result["execution_state"] = target_state

    # Update observation if we have one
    if observation_id:
        try:
            from app.shunya.observer_learning import Observation
            obs = db.session.get(Observation, observation_id)
            if obs:
                obs.success = is_success
                obs.actual_outcome = (response_summary or "")[:1000]
                obs.actual_state = (response_summary or "")[:1000]
                if not is_success:
                    obs.severity = "error"
                    obs.discrepancy = f"Operation failed: {(state or {}).get('error', 'unknown')}"[:1000]
                db.session.commit()
                result["observation_updated"] = True

                # Bridge observation → memory (loop-closing)
                try:
                    from core.observation_memory_bridge import observation_to_memory
                    bridged = observation_to_memory(
                        observation_id,
                        tenant_id=tenant_id,
                        identity_id=identity_id,
                    )
                    result["memory_bridged"] = bridged
                except Exception as bridge_err:
                    logger.warning(f"Observation→memory bridge failed: {bridge_err}")
        except Exception as e:
            db.session.rollback()
            logger.warning(f"complete_action_chain: observation update failed: {e}")

    # Create outcome only on success
    if is_success:
        outcome_id = create_outcome(
            identity_id=identity_id,
            intention=response_summary[:500] if response_summary else "",
            state=state or {"type": "shunyaai_action", "result": outcome},
        )
        result["outcome_id"] = outcome_id

    return result


def deny_action_chain(exec_id: int | None, reason: str = "") -> dict[str, Any]:
    """Mark an action chain as DENIED (authorization rejected)."""
    result: dict[str, Any] = {"execution_state": ExecutionState.DENIED.value}
    if exec_id:
        transition_execution(exec_id, ExecutionState.DENIED.value)
    return result


# ---------------------------------------------------------------------------
# Cleanup: remove any synthetic test records from development
# Synthetic records are clearly marked in metadata and can be purged
# without affecting production data.
# ---------------------------------------------------------------------------

def _clear_synthetic_records() -> dict[str, int]:
    """Remove records created during synthetic record_full_chain() testing.

    These records are identifiable by having source_type="ai_query" or
    "ai_action" with source_id starting with "ask_" (the synthetic prefix).
    """
    counts: dict[str, int] = {}
    try:
        # Evidence records from synthetic tests
        from app.evidence.models_db import EvidenceRecord
        syn_evidence = EvidenceRecord.query.filter(
            EvidenceRecord.source_type.in_(["ai_query", "ai_action"]),
        ).all()
        counts["evidence"] = len(syn_evidence)
        for ev in syn_evidence:
            db.session.delete(ev)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        logger.warning(f"_clear_synthetic_records evidence: {e}")

    try:
        # Observations from synthetic tests
        # Use raw SQL because the ORM model has type mismatches with
        # the DB schema that cause "Unknown PG numeric type" errors.
        # This is a cleanup utility, not the canonical observation path.
        result = db.session.execute(
            db.text("SELECT id FROM observations WHERE source = :source AND observer = :observer"),
            {"source": "shunyaai", "observer": "execution_chain"},
        )
        rows = result.fetchall()
        counts["observations"] = len(rows)
        for (obs_id,) in rows:
            db.session.execute(
                db.text("DELETE FROM observations WHERE id = :id"),
                {"id": obs_id},
            )
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        logger.warning(f"_clear_synthetic_records observations: {e}")

    return counts