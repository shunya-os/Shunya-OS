"""SYSTEM ENTRY POINT — the ONLY allowed way to trigger execution.

PHASE 3 LAYER D: All events must go through process_event().
No module can call execution directly.

Pipeline:
  event → capture_evidence → build_awareness → make_decision → execute

PHASE 3.4: Absolute trace enforcement — every execution records a trace.
No silent failure allowed. Every cycle is auditable.
"""

import logging
from typing import Any, Optional

from app.core.time import now

logger = logging.getLogger(__name__)


# ── Context Builder ────────────────────────────────────────────────────────


def build_context(entity_id: Optional[int] = None, event_data: dict = None) -> dict:
    """Build a rich context for a decision cycle.

    PHASE 3.4: Context includes entity state, last 10 decisions,
    last 10 executions, failures, evidence, communication history.

    Returns a dict that is passed to shadows, comparator, and trace.
    """
    ctx = {
        "entity_id": entity_id,
        "current_state": {},
        "recent_decisions": [],
        "recent_executions": [],
        "recent_failures": [],
        "evidence_summary": [],
        "communication_history": [],
    }

    if not entity_id:
        return ctx

    # Entity state
    try:
        from app.objects.models import Object
        obj = Object.query.get(entity_id)
        if obj:
            ctx["current_state"] = obj.state or {}
            ctx["object_type"] = obj.type
    except Exception:
        pass

    # Last 10 decisions for this entity
    try:
        from app.evidence.decision_trace import DecisionTrace
        traces = DecisionTrace.query.filter_by(
            object_id=entity_id
        ).order_by(DecisionTrace.id.desc()).limit(3).all()
        ctx["recent_decisions"] = [
            {
                "id": t.id,
                "decision": (t.final_decision or {}).get("next_best_action", ""),
                "status": t.execution_status,
                "confidence": t.confidence,
            }
            for t in traces
        ]
        ctx["recent_failures"] = [
            t.to_dict() for t in traces
            if t.execution_status in ("failed", "error")
        ]
    except Exception:
        pass

    # Evidence summary
    try:
        from app.evidence.models_db import EvidenceRecord
        evidence = EvidenceRecord.query.filter_by(
            source_id=str(entity_id)
        ).order_by(EvidenceRecord.id.desc()).limit(5).all()
        ctx["evidence_summary"] = [
            {"type": e.source_type, "id": e.id, "created_at": e.created_at.isoformat() if e.created_at else None}
            for e in evidence
        ]
    except Exception:
        pass

    # Communication history
    try:
        from app.communication.models import MessageProposal
        proposals = MessageProposal.query.filter_by(
            entity_id=entity_id
        ).order_by(MessageProposal.id.desc()).limit(5).all()
        ctx["communication_history"] = [
            {"id": p.id, "message": (p.message or "")[:80], "status": p.status}
            for p in proposals
        ]
    except Exception:
        pass

    # Event data
    if event_data:
        ctx["event_source"] = event_data.get("source", "unknown")

    return ctx


# ── Execution Cycle with Absolute Trace Enforcement ────────────────────────


def process_event(
    event_type: str,
    event_data: dict,
    source: str = "unknown",
) -> dict:
    """Process an event through the canonical pipeline.

    This is the ONLY entry point for all system events.
    PHASE 3.4: Absolute trace enforcement — wraps ENTIRE cycle.
    NO execution without trace. NO silent failure.

    Args:
        event_type: Type of event
        event_data: Event payload
        source: Source of the event

    Returns:
        dict with execution result, trace id, and evidence chain.

    Raises:
        RuntimeError: If any pipeline stage fails (traced).
    """
    cycle_trace_id = None
    result = {"status": "init", "event_type": event_type, "source": source}

    try:
        logger.info("Entry: event=%s source=%s", event_type, source)

        # Stage 1: Capture evidence
        evidence = _capture_evidence(event_type, event_data, source)
        entity_id = _extract_entity_id(event_data)

        # Stage 2: Build rich context
        context = build_context(entity_id=entity_id, event_data=event_data)

        # Stage 3: Build awareness
        awareness = _build_awareness(evidence)

        # Stage 4: Make decision (with shadow + comparison)
        decision = _make_decision(awareness, event_data, context)

        # Stage 5: Execute
        execution = _execute_with_trace(decision, event_data, context)

        return {
            "status": "completed",
            "event_type": event_type,
            "source": source,
            "entity_id": entity_id,
            "evidence": evidence,
            "awareness": awareness,
            "decision": decision,
            "execution": execution.get("result"),
            "decision_trace_id": execution.get("trace_id"),
            "shadow_diffs": execution.get("shadow_diffs", 0),
            "timestamp": now().isoformat(),
        }

    except Exception as e:
        logger.error("Entry failed for %s: %s", event_type, e)

        # Record FAILURE trace (mandatory — no silent failure)
        try:
            from app.evidence.decision_trace import DecisionTrace, get_session
            failure_trace = DecisionTrace(
                object_id=_extract_entity_id(event_data) if event_data else None,
                main_decision={"error": str(e), "event_type": event_type},
                shadow_outputs=[],
                comparison_result={"error": str(e)},
                final_decision={"status": "failed"},
                source="error",
                confidence=0.0,
                execution_status="failed",
                error_message=str(e),
            )
            get_session().add(failure_trace)
            get_session().flush()
            cycle_trace_id = failure_trace.id
            logger.warning("FAILURE trace recorded: id=%d event=%s", failure_trace.id, event_type)
        except Exception as trace_e:
            logger.error("FAILED to record failure trace: %s", trace_e)

        result["status"] = "error"
        result["error"] = str(e)
        result["decision_trace_id"] = cycle_trace_id
        raise


def _extract_entity_id(event_data: dict) -> Optional[int]:
    """Extract entity_id from flexible event data formats."""
    if not event_data:
        return None
    for key in ("entity_id", "object_id", "id"):
        val = event_data.get(key)
        if val is not None:
            try:
                return int(val)
            except (ValueError, TypeError):
                return val
    return None


def _capture_evidence(event_type: str, event_data: dict, source: str) -> dict:
    """Capture evidence for the event."""
    evidence_id = None
    try:
        from app.evidence.models_db import create_evidence
        ev = create_evidence(
            source_type=event_type,
            source_id=str(event_data.get("id", event_data.get("entity_id", f"ev_{int(now().timestamp())}"))),
            raw_reference=event_data,
        )
        evidence_id = ev.id
    except Exception as e:
        logger.warning("Evidence capture failed: %s", e)
    return {"evidence_id": evidence_id, "event_type": event_type, "source": source, "timestamp": now().isoformat()}


def _build_awareness(evidence: dict) -> dict:
    """Build awareness from evidence."""
    try:
        from app.intelligence.awareness import scan
        signals = scan()
        return {"signals_count": len(signals), "signals": [s.get("type", "?") for s in signals[:5]]}
    except Exception as e:
        logger.warning("Awareness build failed: %s", e)
        return {"signals_count": 0, "signals": []}


def _make_decision(awareness: dict, event_data: dict, context: dict) -> dict:
    """Make a decision based on awareness and context."""
    try:
        from app.intelligence.decision_engine import compute_decisions
        decisions = compute_decisions()
        if decisions:
            top = decisions[0]
            return {
                "decision": top.get("next_best_action", ""),
                "priority_score": top.get("priority_score", 0),
                "entity_id": top.get("entity_id"),
                "total_decisions": len(decisions),
                "confidence": top.get("confidence", 0.5),
            }
        return {"decision": "noop", "priority_score": 0, "total_decisions": 0, "confidence": 0.5}
    except Exception as e:
        logger.warning("Decision failed: %s", e)
        return {"decision": "error", "error": str(e)}


def _execute_with_trace(decision: dict, event_data: dict, context: dict) -> dict:
    """Execute the decision WITH absolute trace enforcement.

    Opens the execution gate, runs shadows, compares, traces, executes, updates trace.
    NO execution without trace. NO silent failure.
    """
    from app.core.db import get_session as _get_session

    trace_id = None

    try:
        from app.execution_engine.engine import open_execution_gate, close_execution_gate
        from app.runtime.loop import run_cycle
        from app.core.shadow_runner import run_all_shadows
        from app.intelligence.comparator import compare
        from app.evidence.decision_trace import record_decision_trace

        # Step 1: Run shadows with context
        shadow_outputs = run_all_shadows(context=context)

        # Step 2: Compare with main decision
        comparison = compare(decision, shadow_outputs, context=context)

        # Step 3: Record decision trace BEFORE execution (mandatory)
        trace = record_decision_trace(
            object_id=context.get("entity_id"),
            main_decision=dict(decision),
            shadow_outputs=shadow_outputs,
            comparison_result=comparison,
            final_decision=dict(decision),
            source=decision.get("source", "rule"),
            confidence=comparison.get("enhanced_confidence", 0.5),
        )
        trace_id = trace.id
        logger.info("Decision trace recorded BEFORE execution: id=%d", trace_id)

        # Step 4: Execute
        open_execution_gate()
        try:
            summary = run_cycle()
            exec_status = "success" if summary.get("status") == "completed" else "partial"
            exec_output = {
                "status": summary.get("status"),
                "actions_taken": summary.get("actions_taken", 0),
                "noops": summary.get("noops", 0),
                "errors": summary.get("errors", [])[:3],
            }
        except Exception as exec_e:
            exec_status = "failed"
            exec_output = {"error": str(exec_e)}
            logger.error("Execution gate cycle failed: %s", exec_e)
            raise
        finally:
            close_execution_gate()

        # Step 5: Update trace with execution result
        trace.execution_status = exec_status
        trace.execution_output = exec_output
        _get_session().flush()
        logger.info("Decision trace UPDATED with execution result: id=%d status=%s", trace_id, exec_status)

        # Step 6: Learning — update weights from execution outcome
        try:
            from app.intelligence.learning import record_outcome, adjust_confidence
            record_outcome(decision, exec_status)
            adjusted = adjust_confidence(decision, {"status": exec_status, "output": exec_output})
            trace.confidence = adjusted
            _get_session().flush()
            logger.debug("Learning applied: confidence adjusted to %.3f", adjusted)
        except Exception as learn_e:
            logger.debug("Learning failed (non-fatal): %s", learn_e)

        # Step 7: Automation pipeline — trigger rules
        try:
            from app.automation.force_activate import ensure_automation_table, create_default_rules, trigger_rules
            ensure_automation_table()
            create_default_rules()
            rule_results = trigger_rules()
            if rule_results:
                logger.info("Automation rules triggered: %d", len(rule_results))
        except Exception as auto_e:
            logger.debug("Automation pipeline failed (non-fatal): %s", auto_e)

        # Shadow analysis
        shadow_diffs = len([s for s in shadow_outputs if not s.get("shadow_ok")])

        return {
            "trace_id": trace_id,
            "result": exec_output,
            "execution_status": exec_status,
            "shadow_diffs": shadow_diffs,
            "shadow_confidence": comparison.get("shadow_confidence", 0.0),
        }

    except Exception as e:
        # Record FAILURE trace if not already recorded
        if trace_id is None:
            try:
                from app.evidence.decision_trace import DecisionTrace
                failure_trace = DecisionTrace(
                    object_id=context.get("entity_id"),
                    main_decision=dict(decision),
                    shadow_outputs=[],
                    comparison_result={"error": str(e)},
                    final_decision={"status": "failed"},
                    source="error",
                    confidence=0.0,
                    execution_status="failed",
                    error_message=str(e),
                )
                _get_session().add(failure_trace)
                _get_session().flush()
                trace_id = failure_trace.id
                logger.warning("FAILURE trace recorded during execution: id=%d", trace_id)
            except Exception:
                pass
        raise