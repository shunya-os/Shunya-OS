"""Outcome Routes — API endpoints for the Outcome Runtime.

Thin persistence layer. No step-based execution, no lifecycle progression.
The canonical execution authority is the execution_engine.
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
    """Accept a new outcome. Returns immediately with outcome ID."""
    identity_id = _get_identity()
    if not identity_id:
        return jsonify({"success": False, "error": "Authentication required"}), 401

    data = request.get_json(silent=True) or {}
    intention = data.get("intention", "").strip()
    if not intention:
        return jsonify({"success": False, "error": "intention is required"}), 400

    runtime = get_runtime()
    outcome = runtime.accept(identity_id, intention)

    return jsonify({
        "success": True,
        "data": outcome.to_dict(),
    }), 201


@execution_bp.route("/<outcome_id>", methods=["GET"])
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