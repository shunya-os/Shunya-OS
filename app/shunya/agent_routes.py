"""Shunya Personal Agent — API endpoints.

Chat with your personal agent, get traces, manage profile.
"""
from flask import Blueprint, render_template, request, jsonify, g
from app import db
from app.routes.auth import login_required
from app.shunya.agent import AgentLoop, get_trace_store, Turn
from app.shunya.agent.user import ProfileStore, CorrectionEngine
from app.shunya.agent.search import SourceDecisionTree

agent_bp = Blueprint("agent", __name__, url_prefix="/api/agent")


@agent_bp.route("/chat", methods=["POST"])
@login_required
def chat():
    """Main chat endpoint — the personal agent."""
    data = request.get_json(silent=True) or {}
    query = data.get("query", "").strip()
    channel = data.get("channel", "web")
    correction = data.get("correction", False)
    original_query = data.get("original_query", "")
    correction_text = data.get("correction_text", "")

    if not query:
        return jsonify({"error": "Query required"}), 400

    # Handle correction
    if correction and original_query:
        CorrectionEngine.ingest(
            g.user.id, g.tenant.id, original_query, correction_text or query, {}
        )

    # Run the agent loop
    agent = AgentLoop(g.user.id, g.tenant.id, channel)
    result = agent.process(query)

    return jsonify({
        "response": result.get("response", ""),
        "intent": result.get("intent", {}),
        "verification_badge": result.get("verification_badge", ""),
        "confidence": result.get("confidence", 0),
        "domain": result.get("domain", ""),
        "tool_calls": result.get("tool_calls", []),
        "profile": result.get("profile", {}),
    })


@agent_bp.route("/traces", methods=["GET"])
@login_required
def get_traces():
    """Get recent agent traces (observability)."""
    limit = request.args.get("limit", 20, type=int)
    traces = get_trace_store().get_by_user(g.user.id, limit)
    return jsonify({"traces": traces, "count": len(traces)})


@agent_bp.route("/profile", methods=["GET"])
@login_required
def get_profile():
    """Get the current user's agent profile."""
    profile = ProfileStore.load(g.user.id, g.tenant.id)
    return jsonify({"profile": profile.to_dict()})


@agent_bp.route("/profile/update", methods=["POST"])
@login_required
def update_profile():
    """Update profile preferences."""
    data = request.get_json(silent=True) or {}
    profile = ProfileStore.load(g.user.id, g.tenant.id)

    if "communication_style" in data:
        profile.communication_style = data["communication_style"]
    if "verbosity" in data:
        profile.verbosity = data["verbosity"]
    if "emoji_style" in data:
        profile.emoji_style = data["emoji_style"]
    if "preferred_persona" in data:
        profile.preferred_persona = data["preferred_persona"]

    ProfileStore.save(profile)
    return jsonify({"success": True, "profile": profile.to_dict()})


@agent_bp.route("/tools", methods=["GET"])
@login_required
def list_tools():
    """List available agent tools (for introspection/debug)."""
    from app.shunya.agent.tools import get_registry
    registry = get_registry()
    return jsonify({"tools": registry.list_tools(), "count": len(registry.list_tools())})


@agent_bp.route("/classify", methods=["POST"])
@login_required
def classify_query():
    """Classify a query without executing it (for frontend hints)."""
    data = request.get_json(silent=True) or {}
    query = data.get("query", "").strip()
    if not query:
        return jsonify({"error": "Query required"}), 400

    plan = SourceDecisionTree.get_search_plan(query)
    return jsonify({
        "query": query,
        "domain": plan["domain"],
        "will_search_internal": plan.get("internal", False),
        "will_search_web": plan.get("web", False),
        "search_order": plan.get("order", []),
    })


# ---------------------------------------------------------------------------
# Proactive Engine
# ---------------------------------------------------------------------------

@agent_bp.route("/proactive", methods=["GET"])
@login_required
def get_proactive():
    """Get proactive messages for the current user."""
    from app.shunya.agent.proactive import ProactiveEngine
    engine = ProactiveEngine(g.user.id, g.tenant.id)
    messages = engine.get_messages(5)
    suggestions = engine.get_suggestions()
    return jsonify({
        "messages": [{
            "id": m.id,
            "title": m.title,
            "body": m.body,
            "icon": m.icon,
            "priority": m.priority,
            "action_url": m.action_url,
            "action_label": m.action_label,
        } for m in messages],
        "suggestions": suggestions,
    })


@agent_bp.route("/greeting", methods=["GET"])
@login_required
def get_greeting():
    """Get a personalized greeting with proactive context."""
    from app.shunya.agent.proactive import ProactiveEngine
    engine = ProactiveEngine(g.user.id, g.tenant.id)
    greeting = engine.get_greeting(g.user.name)
    suggestions = engine.get_suggestions()
    return jsonify({
        "greeting": greeting.title,
        "message": greeting.body,
        "icon": greeting.icon,
        "suggestions": suggestions,
        "proactive_count": len(engine.get_messages(5)),
    })


@agent_bp.route("/patterns", methods=["GET"])
@login_required
def get_patterns():
    """Get learned user behavior patterns."""
    from app.shunya.agent.proactive import PatternLearner
    patterns = PatternLearner.learn(g.user.id, g.tenant.id)
    return jsonify({
        "patterns": [{
            "pattern_type": p.pattern_type,
            "trigger_hour": p.trigger_hour,
            "action_count": p.action_count,
            "is_active": p.is_active,
        } for p in patterns],
        "count": len(patterns),
    })