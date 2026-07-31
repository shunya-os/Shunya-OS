"""
SHUNYA Decision Runtime — Bootstrap and Middleware
"""

from flask import request, jsonify
from datetime import datetime, timezone

from app.decision_runtime.models import Decision, DecisionStatus, get_store as get_decision_store
from app.decision_runtime.policy import get_engine as get_policy_engine, PolicyAction
from app.decision_runtime.commitment import get_service as get_commitment_service
from app.decision_runtime.outcome import get_store as get_outcome_store, Outcome
from app.decision_runtime.learning import get_store as get_learning_store, LearningRecord
from app.intelligence.insight import get_compiler
from app.intelligence.inspector import get_inspector as get_intel_inspector


def register_decision_middleware(app) -> None:
    @app.before_request
    def _check_decision_inspect():
        if request.args.get("inspect_decision_system"):
            return jsonify(_inspect_decision_system())
        decision_id = request.args.get("inspect")
        if decision_id:
            ds = get_decision_store()
            d = ds.get(decision_id)
            if d:
                return jsonify(_inspect_decision_chain(d))
        return None


def _inspect_decision_chain(decision: Decision) -> dict:
    intel = get_intel_inspector()
    origin = intel.inspect_insight(decision.origin_insight_id)
    cs = get_commitment_service()
    cmt = cs.get_by_decision(decision.decision_id)
    os = get_outcome_store()
    outcome = os.get_by_decision(decision.decision_id)
    ls = get_learning_store()
    learning = ls.get_by_decision(decision.decision_id)
    execution = cs.get_execution(cmt.commitment_id) if cmt else None

    return {
        "decision": decision.to_dict(),
        "provenance": {
            "observation": origin.get("provenance", {}),
            "decision": decision.to_dict(),
            "commitment": cmt.to_dict() if cmt else None,
            "outcome": outcome.to_dict() if outcome else None,
            "learning": learning.to_dict() if learning else None,
            "execution": execution,
        },
        "chain_complete": all([
            origin.get("provenance", {}).get("chain_found", False),
            cmt is not None, outcome is not None, learning is not None,
        ]),
        "inspection_timestamp": datetime.now(timezone.utc).isoformat(),
    }


def _inspect_decision_system() -> dict:
    return {
        "decisions": {"total": get_decision_store().count, "active": len(get_decision_store().get_active())},
        "policies": {"count": get_policy_engine().policy_count},
        "commitments": {"total": get_commitment_service().count},
        "outcomes": {"total": get_outcome_store().count},
        "learning": {"total": get_learning_store().count},
        "inspection_timestamp": datetime.now(timezone.utc).isoformat(),
    }


def load_demo_decisions() -> None:
    compiler = get_compiler()
    ds = get_decision_store()
    pe = get_policy_engine()
    insights = compiler.compile_all()

    for ins in insights:
        d = Decision(
            decision_id=f"dec_{ins.insight_id}",
            origin_insight_id=ins.insight_id,
            label=ins.label,
            description=ins.detail,
            confidence=ins.confidence,
            business_impact="medium",
            urgency="normal",
            owner="default",
            approval_required=True,
            status=DecisionStatus.CANDIDATE,
        )
        ds.add(d)
        pr = pe.evaluate(d.to_dict())
        if pr is None:
            continue
        d.transition_to(DecisionStatus.POLICY_EVALUATING)
        if pr.action == PolicyAction.EXECUTE_AUTOMATICALLY:
            d.approval_required = False
            d.transition_to(DecisionStatus.APPROVED)
            cs = get_commitment_service()
            cs.create_commitment(d)
            d.transition_to(DecisionStatus.EXECUTING)
        elif pr.action == PolicyAction.REQUEST_APPROVAL:
            d.transition_to(DecisionStatus.AWAITING_APPROVAL)
        elif pr.action == PolicyAction.RECOMMEND:
            d.transition_to(DecisionStatus.APPROVED)
            cs = get_commitment_service()
            cs.create_commitment(d)
            d.transition_to(DecisionStatus.EXECUTING)
        elif pr.action == PolicyAction.ESCALATE:
            d.transition_to(DecisionStatus.AWAITING_APPROVAL)