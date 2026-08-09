"""Intelligence Runtime API — Flask surface for every SHUNYA consumer.

All surfaces call through this shared API. No alternative path exists.
Uses the Integration layer for provider wiring and telemetry.
"""

from __future__ import annotations

from flask import Blueprint, jsonify, request, session

from core.intelligence_runtime.integration import (
    ask, explain_last, get_history, health, navigate, store_memory, suggest,
)

intelligence_bp = Blueprint("intelligence_runtime", __name__, url_prefix="/api/intelligence")


def _session_id() -> str:
    uid = session.get("user_id") or session.get("identity_id") or "anonymous"
    return f"session_{uid}"


def _context() -> dict:
    """Extract common context from request args/body."""
    data = request.get_json(silent=True) or request.args.to_dict() or {}
    return {
        "module_key": data.get("module") or session.get("current_module", ""),
        "workspace": data.get("workspace", ""),
        "object_type": data.get("object_type", ""),
        "object_id": data.get("object_id", ""),
    }


# ── Primary Query Endpoints ──────────────────────────────────────────────


@intelligence_bp.route("/ask", methods=["POST"])
def api_ask():
    """Single entry point for every intelligence query across all surfaces.
    
    Executive Home, Search, Chat, Documents, Dashboards — all use this.
    """
    data = request.get_json(silent=True) or {}
    query = data.get("query", "").strip()
    if not query:
        return jsonify({"error": "query is required"}), 400

    ctx = _context()
    result = ask(
        query=query,
        session_id=_session_id(),
        module_key=ctx["module_key"],
        workspace=data.get("workspace", ctx["workspace"]),
        object_type=data.get("object_type", ctx["object_type"]),
        object_id=data.get("object_id", ctx["object_id"]),
        explain=data.get("explain", False),
    )
    return jsonify(result)


# ── Context & Navigation ─────────────────────────────────────────────────


@intelligence_bp.route("/context", methods=["GET"])
def api_get_context():
    runtime = _get_runtime()
    ctx = runtime.context.get(_session_id())
    return jsonify({"data": ctx.to_dict()})


@intelligence_bp.route("/context", methods=["POST"])
def api_set_context():
    data = request.get_json(silent=True) or {}
    result = navigate(
        session_id=_session_id(),
        workspace=data.get("workspace", ""),
        module=data.get("module", ""),
        object_type=data.get("object_type", ""),
        object_id=data.get("object_id", ""),
    )
    return jsonify(result)


@intelligence_bp.route("/navigate", methods=["POST"])
def api_navigate():
    """Notify runtime of surface navigation for context continuity."""
    data = request.get_json(silent=True) or {}
    result = navigate(
        session_id=_session_id(),
        workspace=data.get("workspace", ""),
        module=data.get("module", ""),
        object_type=data.get("object_type", ""),
        object_id=data.get("object_id", ""),
    )
    return jsonify(result)


# ── Conversation ─────────────────────────────────────────────────────────


@intelligence_bp.route("/conversation", methods=["GET"])
def api_conversation():
    """Get conversation history (used by Chat, Executive Home, all surfaces)."""
    limit = request.args.get("limit", 20, type=int)
    history = get_history(_session_id(), limit)
    return jsonify({"data": history, "count": len(history)})


# ── Suggestions ──────────────────────────────────────────────────────────


@intelligence_bp.route("/suggestions", methods=["GET"])
def api_suggestions():
    """Get context-aware suggestions (used by Automation Suggestions, Dashboard, Executive Home)."""
    ctx = _context()
    suggestions = suggest(
        session_id=_session_id(),
        module_key=ctx["module_key"],
        object_type=request.args.get("object_type", ctx["object_type"]) or "",
        object_id=request.args.get("object_id", ctx["object_id"]) or "",
    )
    return jsonify({"data": suggestions})


# ── Memory ───────────────────────────────────────────────────────────────


@intelligence_bp.route("/memory", methods=["GET"])
def api_get_memory():
    runtime = _get_runtime()
    memories = runtime.memory.recall_recent(limit=20)
    return jsonify({"data": [m.to_dict() for m in memories]})


@intelligence_bp.route("/memory", methods=["POST"])
def api_store_memory():
    data = request.get_json(silent=True) or {}
    key = data.get("key", "")
    content = data.get("content", "")
    if not key or not content:
        return jsonify({"error": "key and content required"}), 400
    store_memory(key, content, source="user")
    return jsonify({"status": "stored"})


# ── Explainability ───────────────────────────────────────────────────────


@intelligence_bp.route("/explain", methods=["POST"])
def api_explain():
    """Get explanation for a specific response (identical format across all surfaces)."""
    data = request.get_json(silent=True) or {}
    message_index = data.get("index", -1)
    result = explain_last(_session_id(), message_index)
    return jsonify(result)


# ── Business Discovery ───────────────────────────────────────────────────


@intelligence_bp.route("/discover", methods=["POST"])
def api_discover():
    """Business Discovery via the Intelligence Runtime.
    
    Uses the runtime to analyze a business description and generate a module.
    """
    data = request.get_json(silent=True) or {}
    description = data.get("description", "")
    business_name = data.get("business_name", "")

    if not description:
        return jsonify({"error": "description is required"}), 400

    # Use the runtime to analyze the business description
    query = f"Analyze this business description and identify all entities, relationships, workflows, and metrics: {description}"
    result = ask(query=query, session_id=_session_id(), explain=True)

    # Generate the ontology and module via UBME
    from app.ubme.ontology_gen import generate_ontology
    from app.ubme.ontology_to_module import ontology_to_module
    from app.ubme.business_graph import register_graph
    from app.ubme import engine as ubme_engine

    answers = {
        "business_name": business_name or description[:50],
        "business_description": description,
        "entities": description,
        "has_customers": data.get("has_customers", "Customers"),
        "products": data.get("products", "Products and services"),
    }
    ontology = generate_ontology(answers)
    module = ontology_to_module(ontology)
    ubme_engine.register_module(module)
    register_graph(module.key, ontology)

    return jsonify({
        "status": "discovered",
        "module": module.to_dict(),
        "ontology": ontology.to_dict(),
        "analysis": result,
    })


# ── Health & Telemetry ───────────────────────────────────────────────────


@intelligence_bp.route("/health", methods=["GET"])
def api_health():
    """Runtime health with operational telemetry."""
    return jsonify(health())


# ── PHASE 2C.1: Awareness Surface ─────────────────────────────────────


@intelligence_bp.route("/awareness", methods=["GET"])
def api_awareness():
    """Return awareness signals sorted by severity + recency.
    
    PHASE 2C.1: Read-only intelligence surface.
    Each signal includes type, severity, entity_id, reason, suggested_action, timestamp.
    """
    try:
        from app.intelligence.awareness import scan
        signals = scan()

        # Sort: high > medium > low, then newest first
        severity_order = {"high": 0, "medium": 1, "low": 2}
        signals.sort(key=lambda s: (severity_order.get(s["severity"], 9), -abs(hash(s.get("reason", "")))))

        return jsonify({
            "signals": signals,
            "total": len(signals),
            "priorities": {
                "high": len([s for s in signals if s["severity"] == "high"]),
                "medium": len([s for s in signals if s["severity"] == "medium"]),
                "low": len([s for s in signals if s["severity"] == "low"]),
            },
        })
    except Exception as e:
        return jsonify({"signals": [], "total": 0, "priorities": {}, "error": str(e)})


# ── PHASE 2A: Evidence Surface ────────────────────────────────────────


@intelligence_bp.route("/evidence", methods=["GET"])
def api_evidence():
    """Return evidence logs for a given entity or type.
    
    Query params:
        entity_id: int (optional)
        type: str (execution_summary|proposal|ai|awareness_signal)
        limit: int (default 20)
    """
    try:
        entity_id = request.args.get("entity_id", type=int)
        obs_type = request.args.get("type") or None
        limit = request.args.get("limit", 20, type=int)

        from app.cortex.state_log import query
        records = query(
            observation_type=obs_type,
            entity_id=entity_id,
            limit=limit,
        )
        return jsonify({"records": records, "total": len(records)})
    except Exception as e:
        return jsonify({"records": [], "total": 0, "error": str(e)})


# ── Internal ─────────────────────────────────────────────────────────────


def _get_runtime():
    from core.intelligence_runtime import get_runtime
    return get_runtime()