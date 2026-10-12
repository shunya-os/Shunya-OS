"""Outcome Routes — API endpoints for the Outcome Runtime.

Thin persistence layer. The canonical execution authority is
runtime/entry.py → execution_engine; outcomes created here are dispatched
through it so the returned status is truthful (executed / failed).
"""
import logging
from flask import Blueprint, jsonify, request, session
from app.authz.decorators import require_permission
from app.execution.runtime import get_runtime

logger = logging.getLogger(__name__)

execution_bp = Blueprint("execution_outcomes", __name__, url_prefix="/api/v1/outcomes")


def _get_identity() -> str | None:
    """Extract identity from session or header."""
    return (
        session.get("identity_id")
        or session.get("user_id")
        or request.headers.get("X-Identity-Id")
    )


@execution_bp.route("", methods=["POST"])
@require_permission("task.create")
def create_outcome():
    """Accept a new outcome and dispatch it through the canonical execution authority.

    Returns immediately with the outcome ID. The outcome's state records the
    truthful dispatch result: 'executed' when process_event succeeded,
    'failed' (with last_error) when the execution authority could not run it.
    """
    identity_id = _get_identity()
    if not identity_id:
        return jsonify({"success": False, "error": "Authentication required"}), 401

    data = request.get_json(silent=True) or {}
    intention = data.get("intention", "").strip()
    if not intention:
        return jsonify({"success": False, "error": "intention is required"}), 400

    runtime = get_runtime()
    outcome = runtime.accept(identity_id, intention)

    # Dispatch through the canonical execution authority (runtime/entry.py).
    # The outcome must never claim 'executed' without a real execution.
    result = _dispatch_outcome(outcome, identity_id, intention)

    return jsonify({
        "success": True,
        "data": outcome.to_dict(),
        "execution": result,
    }), 201


def _dispatch_outcome(outcome, identity_id: str, intention: str) -> dict:
    """Run the outcome through runtime/entry.process_event and persist the result.

    On failure the outcome is marked 'failed' truthfully (with the error),
    never left claiming execution.
    """
    from app import db

    try:
        from app.runtime.entry import process_event

        exec_result = process_event(
            "outcome_accepted",
            {
                "id": outcome.outcome_id,
                "intention": intention,
                "identity_id": identity_id,
            },
            source="outcome_route",
        )
        state = dict(outcome.state or {})
        state.update({
            "stage": "executed",
            "execution_status": exec_result.get("status", "completed"),
            "execution_trace_id": exec_result.get("decision_trace_id"),
            "execution_result": {
                "status": exec_result.get("status"),
                "entity_id": exec_result.get("entity_id"),
                "decision_trace_id": exec_result.get("decision_trace_id"),
            },
        })
        outcome.state = state
        db.session.commit()
        logger.info("Outcome %s executed via canonical authority", outcome.outcome_id)
        return {"status": "executed",
                "execution_status": exec_result.get("status"),
                "decision_trace_id": exec_result.get("decision_trace_id")}
    except Exception as e:  # noqa: BLE001 — truthful failure recording
        db.session.rollback()
        state = dict(outcome.state or {})
        state.update({
            "stage": "failed",
            "execution_status": "failed",
            "last_error": str(e),
        })
        outcome.state = state
        db.session.commit()
        logger.warning("Outcome %s failed to dispatch: %s", outcome.outcome_id, e)
        return {"status": "failed", "error": str(e)}


@execution_bp.route("/<outcome_id>", methods=["GET"])
@require_permission("task.view")
def get_outcome(outcome_id: str):
    """Get outcome status by ID."""
    runtime = get_runtime()
    outcome = runtime.get(outcome_id)
    if not outcome:
        return jsonify({"success": False, "error": "Outcome not found"}), 404
    return jsonify({
        "success": True,
        "data": outcome.to_dict(),
    })


@execution_bp.route("", methods=["GET"])
@require_permission("task.view")
def list_outcomes():
    """List recent outcomes for the current user."""
    identity_id = _get_identity()
    if not identity_id:
        return jsonify({"success": False, "error": "Authentication required"}), 401

    limit = request.args.get("limit", 20, type=int)
    runtime = get_runtime()
    outcomes = runtime.get_by_identity(identity_id, limit)

    return jsonify({
        "success": True,
        "data": [o.to_dict() for o in outcomes],
    })


@execution_bp.route("/search", methods=["GET"])
@require_permission("task.view")
def search_outcomes():
    """Search outcomes by intention text."""
    identity_id = _get_identity()
    if not identity_id:
        return jsonify({"success": False, "error": "Authentication required"}), 401

    query = request.args.get("q", "").strip()
    if not query:
        return jsonify({"success": False, "error": "q is required"}), 400

    runtime = get_runtime()
    outcomes = runtime.search_intention(identity_id, query)

    return jsonify({
        "success": True,
        "data": [o.to_dict() for o in outcomes],
    })