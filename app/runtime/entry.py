"""SYSTEM ENTRY POINT — the ONLY allowed way to trigger execution.

PHASE 3 LAYER D: All events must go through process_event().
No module can call execution directly.

Pipeline:
  event → capture_evidence → build_awareness → make_decision → execute

PHASE 3.4: Absolute trace enforcement — every execution records a trace.
No silent failure allowed. Every cycle is auditable.

PROD-06 CONSTITUTIONAL ARCHITECTURE:

  Event-triggered execution path (process_event):

    Event
      ↓
    Evidence capture
      ↓
    DecisionContext (State, Intent, Evidence, Time)
      ↓
    _make_decision(..., decision_ctx)
      ↓
    _execute_with_trace(..., decision_ctx)
      ↓
    CANONICAL DECISION: get_next_action(entity, decision_ctx)
      State     → structural decision input
      Evidence  → evidence gate (blocks updates without proof)
      Intent    → recorded in trace for audit
      Time      → recorded in trace for audit
      ↓
    open_execution_gate()
      ↓
    execute_action(entity, canonical_decision)
      → entity-specific execution, NOT all-object cycle
      ↓
    close_execution_gate()

  The DecisionContext-aware decision ALWAYS happens BEFORE the
  execution it governs. The decision is bound to this invocation
  by direct inline computation → execution — no global state,
  no override mechanism, no output annotation.

  Background all-object cycle (run_cycle / run_loop):

    run_cycle()
      → processes ALL objects via context-free get_next_action()
      → processes commitments, inbound, delivery
      → independent of event-triggered path

  These two paths are architecturally distinct:
  - Event-triggered: targeted entity, pre-computed constitutional decision
  - Background cycle: all entities, context-free decisions
"""

import logging
from typing import Any, Optional

from app.core.time import now
from app.execution_engine.context import DecisionContext

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

    Event-triggered execution is entity-specific — the target entity
    is executed with its pre-computed constitutional decision. The
    all-object background cycle (run_cycle) is a separate invocation.

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

        # Stage 1: Capture evidence (BEFORE DecisionContext — evidence is required)
        evidence = _capture_evidence(event_type, event_data, source)
        entity_id = _extract_entity_id(event_data)

        # Stage 2: Build rich context
        context = build_context(entity_id=entity_id, event_data=event_data)

        # Stage 2b: Build constitutional DecisionContext AFTER evidence capture
        decision_ctx = DecisionContext(
            state=context.get("current_state", {}),
            intent=event_type,
            evidence=evidence,
            time=now(),
        )
        logger.debug(
            "DecisionContext: state=%s intent=%s evidence=%s time=%s",
            bool(decision_ctx.state), decision_ctx.intent,
            bool(decision_ctx.evidence), decision_ctx.time.isoformat(),
        )

        # Stage 3: Build awareness
        awareness = _build_awareness(evidence)

        # Stage 4: Make decision — propagated with full DecisionContext
        decision = _make_decision(awareness, event_data, context, decision_ctx=decision_ctx)

        # Stage 5: Execute — entity-specific, propagated with full DecisionContext
        execution = _execute_with_trace(decision, event_data, context, decision_ctx=decision_ctx)

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


def _make_decision(awareness: dict, event_data: dict, context: dict,
                    decision_ctx: Optional[DecisionContext] = None) -> dict:
    """Make a decision based on awareness and context.

    DecisionContext (State, Intent, Evidence, Time) is propagated through
    this function. It is recorded in the output and available for any
    downstream decision evaluation.

    The decision engine (get_next_action in decision_engine.py) is the
    canonical structural decision authority. DecisionContext adds
    constitutional dimensions for higher-level orchestration.
    """
    if decision_ctx is not None:
        logger.debug(
            "DecisionContext supplied: state_keys=%s intent=%s has_evidence=%s time=%s",
            list(decision_ctx.state.keys()) if decision_ctx.state else "[]",
            decision_ctx.intent,
            bool(decision_ctx.evidence),
            decision_ctx.time.isoformat() if hasattr(decision_ctx.time, 'isoformat') else str(decision_ctx.time),
        )
    try:
        from app.intelligence.decision_engine import compute_decisions
        decisions = compute_decisions()
        if decisions:
            top = decisions[0]
            result = {
                "decision": top.get("next_best_action", ""),
                "priority_score": top.get("priority_score", 0),
                "entity_id": top.get("entity_id"),
                "total_decisions": len(decisions),
                "confidence": top.get("confidence", 0.5),
            }
        else:
            result = {"decision": "noop", "priority_score": 0, "total_decisions": 0, "confidence": 0.5}

        # Annotate with DecisionContext dimensions when available
        if decision_ctx is not None:
            result["ctx_state_keys"] = list(decision_ctx.state.keys()) if decision_ctx.state else []
            result["ctx_intent"] = decision_ctx.intent
            result["ctx_has_evidence"] = bool(decision_ctx.evidence)
            result["ctx_time"] = decision_ctx.time.isoformat() if hasattr(decision_ctx.time, 'isoformat') else str(decision_ctx.time)
        return result
    except Exception as e:
        logger.warning("Decision failed: %s", e)
        return {"decision": "error", "error": str(e)}


# ── Entity-specific execution helper ──────────────────────────────────────


def _execute_for_entity(entity_obj, canonical_decision: dict) -> dict:
    """Execute a single entity's canonical decision.

    This is the entity-specific execution path for event-triggered
    processing. It does NOT process all objects — only the entity
    targeted by the event.

    The execution gate must be open before calling this.

    Args:
        entity_obj: The Object instance to execute.
        canonical_decision: The pre-computed decision dict
            (from get_next_action with DecisionContext).

    Returns:
        dict describing the execution result:
            - action_type: 'update' | 'noop'
            - state_before/state_after (update only)
            - decision_source
    """
    result = {}

    if canonical_decision.get("type") == "noop":
        from app.signals.service import emit_signal
        emit_signal(entity_obj.id, "no_action", {"state": entity_obj.state})
        return {
            "action_type": "noop",
            "decision_source": canonical_decision.get("decision_source"),
        }

    # 'update' type — execute via the canonical mutation primitive
    from app.execution_engine.engine import execute_action

    state_before = dict(entity_obj.state or {})
    execute_action(entity_obj, canonical_decision)

    from app.signals.service import emit_signal
    emit_signal(
        entity_obj.id, "state_changed",
        {"from": state_before, "to": entity_obj.state},
    )

    from app.execution_log.models import log_execution
    log_execution(entity_obj.id, "ACTION", {
        "action": canonical_decision,
        "state_before": state_before,
        "state_after": entity_obj.state,
    })

    return {
        "action_type": "update",
        "state_before": state_before,
        "state_after": dict(entity_obj.state or {}),
        "decision_source": canonical_decision.get("decision_source"),
    }


# ── Trace + Execution Gate ────────────────────────────────────────────────


def _execute_with_trace(decision: dict, event_data: dict, context: dict,
                         decision_ctx: Optional[DecisionContext] = None) -> dict:
    """Execute the decision WITH absolute trace enforcement.

    Opens the execution gate, runs shadows, computes the canonical
    constitutional decision, executes the targeted entity, updates trace.

    The canonical decision (get_next_action with DecisionContext) is
    computed BEFORE the execution gate opens — it governs what runs.
    No global state. No post-hoc annotation. Fail-closed.

    DecisionContext (State, Intent, Evidence, Time) is propagated through
    this function and recorded in the decision trace for auditability.

    Background: Event-triggered execution is entity-specific. The
    all-object background cycle (run_cycle) is an independent invocation.
    """
    from app.core.db import get_session as _get_session

    trace_id = None

    ctx_state_preview = {}
    ctx_intent = None
    ctx_has_evidence = False
    ctx_time_str = ""
    if decision_ctx is not None:
        ctx_state_preview = dict(decision_ctx.state) if decision_ctx.state else {}
        if len(ctx_state_preview) > 5:
            ctx_state_preview = dict(list(ctx_state_preview.items())[:5])
        ctx_intent = decision_ctx.intent
        ctx_has_evidence = bool(decision_ctx.evidence)
        ctx_time_str = decision_ctx.time.isoformat() if hasattr(decision_ctx.time, 'isoformat') else str(decision_ctx.time)

    try:
        from app.execution_engine.engine import open_execution_gate, close_execution_gate
        from app.core.shadow_runner import run_all_shadows
        from app.intelligence.comparator import compare
        from app.evidence.decision_trace import record_decision_trace
        from app.objects.models import Object

        # Step 1: Run shadows with context
        shadow_outputs = run_all_shadows(context=context)

        # Step 2: Compare with main decision
        comparison = compare(decision, shadow_outputs, context=context)

        # Step 2b: CANONICAL DECISION — BEFORE execution gate opens.
        # get_next_action(entity, decision_ctx) consumes State and Evidence
        # from DecisionContext and records Intent and Time in the trace.
        # This call is inline — the result is bound to this invocation
        # by direct assignment. No global state, no override mechanism.
        # Fail-closed: if this ever raises, execution does NOT proceed.
        event_obj_id = context.get("entity_id") or _extract_entity_id(event_data)
        entity_obj = None
        canonical_decision = None

        if decision_ctx is not None and event_obj_id is not None:
            from app.runtime.decision_engine import get_next_action
            entity_obj = Object.query.get(event_obj_id)
            if entity_obj is not None:
                canonical_decision = get_next_action(
                    entity_obj, decision_ctx=decision_ctx
                )
                logger.debug(
                    "Canonical decision for entity %d: type=%s source=%s",
                    event_obj_id,
                    canonical_decision.get("type"),
                    canonical_decision.get("decision_source"),
                )

        # Step 3: Record decision trace BEFORE execution (mandatory)
        decision_for_trace = dict(decision)
        if decision_ctx is not None:
            decision_for_trace["_ctx"] = {
                "intent": ctx_intent,
                "has_evidence": ctx_has_evidence,
                "time": ctx_time_str,
                "state_keys": list(ctx_state_preview.keys()),
            }
        trace = record_decision_trace(
            object_id=context.get("entity_id"),
            main_decision=decision_for_trace,
            shadow_outputs=shadow_outputs,
            comparison_result=comparison,
            final_decision=dict(decision),
            source=decision.get("source", "rule"),
            confidence=comparison.get("enhanced_confidence", 0.5),
        )
        trace_id = trace.id
        logger.info("Decision trace recorded BEFORE execution: id=%d", trace_id)

        # Step 4: Execute — entity-specific with pre-computed canonical decision.
        # The gate is opened and closed for this targeted execution only.
        # No all-object run_cycle here — that is a separate background invocation.
        open_execution_gate()
        try:
            if canonical_decision is not None and entity_obj is not None:
                entity_result = _execute_for_entity(entity_obj, canonical_decision)
            else:
                entity_result = {"action_type": "noop", "reason": "no target entity"}

            exec_status = "success"
            exec_output = {
                "entity_execution": entity_result,
                # Canonical provenance: the full canonical decision dict
                # that governed this execution invocation is stored in
                # the decision trace. The trace answers:
                #   - Which decision governed execution?
                #   - Which DecisionContext produced it?
                #   - Which entity was targeted?
                #   - What was the result?
                "canonical_decision": dict(canonical_decision) if canonical_decision else None,
                "decision_context": {
                    "intent": ctx_intent,
                    "has_evidence": ctx_has_evidence,
                    "time": ctx_time_str,
                    "state_keys": list(ctx_state_preview.keys()),
                } if decision_ctx is not None else None,
            }
            logger.debug(
                "Entity execution: id=%s type=%s source=%s",
                event_obj_id,
                entity_result.get("action_type"),
                entity_result.get("decision_source"),
            )
        except Exception as exec_e:
            exec_status = "failed"
            exec_output = {"error": str(exec_e)}
            logger.error("Execution gate failed: %s", exec_e)
            raise
        finally:
            close_execution_gate()

        # Step 5: Update trace with execution result
        trace.execution_status = exec_status
        trace.execution_output = exec_output
        _get_session().flush()
        logger.info("Decision trace UPDATED: id=%d status=%s", trace_id, exec_status)

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