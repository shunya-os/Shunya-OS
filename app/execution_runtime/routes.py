"""EP-07 — Universal Execution Runtime API."""

from flask import Blueprint, jsonify, request, g
from typing import Optional

from .runtime import get_execution_runtime, EXECUTION_LIFECYCLE

exec_bp = Blueprint("execution", __name__, url_prefix="/api/v1/execution")


def _require_identity():
    identity_id = getattr(g, 'identity_id', None)
    if identity_id:
        return identity_id
    return request.headers.get("X-Identity-Id")


@exec_bp.route("/", defaults={"exec_id": None})
@exec_bp.route("/<exec_id>", methods=["GET"])
def get_execution(exec_id: Optional[str] = None):
    identity_id = _require_identity()
    if not identity_id:
        return jsonify({"success": False, "error": "Authentication required"}), 401
    rt = get_execution_runtime()
    if exec_id:
        ex = rt.get_execution(exec_id)
        if not ex:
            return jsonify({"success": False, "error": "Execution not found"}), 404
        return jsonify({"success": True, "data": ex.to_dict()})
    status = request.args.get("status")
    exes = [e.to_dict() for e in rt.list_executions(status=status)]
    return jsonify({"success": True, "data": exes})


@exec_bp.route("", methods=["POST"])
def create_execution():
    identity_id = _require_identity()
    if not identity_id:
        return jsonify({"success": False, "error": "Authentication required"}), 401
    data = request.get_json(silent=True) or {}
    title = data.get("title", "").strip()
    if not title:
        return jsonify({"success": False, "error": "title is required"}), 400
    rt = get_execution_runtime()
    ex = rt.create_execution(
        title=title,
        intent=data.get("intent", ""),
        goal=data.get("goal", ""),
        participants=data.get("participants"),
        completion_criteria=data.get("completion_criteria", ""),
    )
    return jsonify({"success": True, "data": ex.to_dict()}), 201


@exec_bp.route("/<exec_id>/transition", methods=["POST"])
def transition_execution(exec_id: str):
    identity_id = _require_identity()
    if not identity_id:
        return jsonify({"success": False, "error": "Authentication required"}), 401
    data = request.get_json(silent=True) or {}
    target = data.get("status", "").strip()
    if not target:
        return jsonify({"success": False, "error": "status is required"}), 400
    rt = get_execution_runtime()
    ex = rt.transition_execution(exec_id, target)
    if not ex:
        return jsonify({"success": False, "error": "Execution not found or invalid transition"}), 404
    return jsonify({"success": True, "data": ex.to_dict()})


@exec_bp.route("/<exec_id>/orchestrate", methods=["POST"])
def orchestrate_execution(exec_id: str):
    identity_id = _require_identity()
    if not identity_id:
        return jsonify({"success": False, "error": "Authentication required"}), 401
    rt = get_execution_runtime()
    results = rt.orchestrate(exec_id)
    if results is None:
        return jsonify({"success": False, "error": "Execution not found"}), 404
    return jsonify({"success": True, "data": results})


@exec_bp.route("/<exec_id>/analyze", methods=["GET"])
def analyze_execution(exec_id: str):
    identity_id = _require_identity()
    if not identity_id:
        return jsonify({"success": False, "error": "Authentication required"}), 401
    rt = get_execution_runtime()
    analysis = rt.analyze(exec_id)
    if not analysis:
        return jsonify({"success": False, "error": "Execution not found"}), 404
    return jsonify({"success": True, "data": analysis})


@exec_bp.route("/<exec_id>/step/<step_id>", methods=["PUT"])
def update_step(exec_id: str, step_id: str):
    identity_id = _require_identity()
    if not identity_id:
        return jsonify({"success": False, "error": "Authentication required"}), 401
    data = request.get_json(silent=True) or {}
    status = data.get("status", "").strip()
    if not status:
        return jsonify({"success": False, "error": "status is required"}), 400
    rt = get_execution_runtime()
    ex = rt.update_step(exec_id, step_id, status)
    if not ex:
        return jsonify({"success": False, "error": "Execution or step not found"}), 404
    return jsonify({"success": True, "data": ex.to_dict()})


@exec_bp.route("/search", methods=["GET"])
def search_executions():
    identity_id = _require_identity()
    if not identity_id:
        return jsonify({"success": False, "error": "Authentication required"}), 401
    query = request.args.get("q", "").strip()
    if not query:
        return jsonify({"success": False, "error": "q parameter required"}), 400
    rt = get_execution_runtime()
    results = rt.search(query)
    return jsonify({"success": True, "data": results})


@exec_bp.route("/<exec_id>/observe", methods=["POST"])
def observe_reality(exec_id: str):
    """Observe Reality and adapt execution if needed."""
    identity_id = _require_identity()
    if not identity_id:
        return jsonify({"success": False, "error": "Authentication required"}), 401
    rt = get_execution_runtime()
    result = rt.observe_reality(exec_id)
    if not result:
        return jsonify({"success": False, "error": "Execution not found"}), 404
    return jsonify({"success": True, "data": result})


@exec_bp.route("/<exec_id>/recommend", methods=["GET"])
def recommend_next(exec_id: str):
    """Get evidence-backed recommendations for this execution."""
    identity_id = _require_identity()
    if not identity_id:
        return jsonify({"success": False, "error": "Authentication required"}), 401
    rt = get_execution_runtime()
    result = rt.recommend(exec_id)
    if not result:
        return jsonify({"success": False, "error": "Execution not found"}), 404
    return jsonify({"success": True, "data": result})


@exec_bp.route("/<exec_id>/adapt", methods=["POST"])
def adapt_execution(exec_id: str):
    """Adapt execution in response to a reality event.
    
    POST /api/v1/execution/<id>/adapt
    { "event": { "type": "proposal_accepted", ... } }
    """
    identity_id = _require_identity()
    if not identity_id:
        return jsonify({"success": False, "error": "Authentication required"}), 401
    data = request.get_json(silent=True) or {}
    event = data.get("event", {})
    rt = get_execution_runtime()
    result = rt.adapt(exec_id, reality_event=event)
    if not result:
        return jsonify({"success": False, "error": "Execution not found"}), 404
    return jsonify({"success": True, "data": result})


@exec_bp.route("/lifecycle", methods=["GET"])
def get_lifecycle():
    return jsonify({"success": True, "data": EXECUTION_LIFECYCLE})