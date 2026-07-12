"""Shunya OS — Bird AI Agent API.

Connects the tool-registered Agent to the frontend Bird AI widget.
"""
from flask import Blueprint, g, jsonify, request
from app.routes.auth import login_required

agent_bp = Blueprint("agent", __name__)

@agent_bp.route("/api/agent/process", methods=["POST"])
@login_required
def agent_process():
    """Process a natural language request through the Bird AI agent."""
    from app.shunya.agent import Agent, parse_intent, registry
    
    data = request.get_json() or {}
    text = data.get("text", "").strip()
    
    if not text:
        return jsonify({"error": "No text provided"}), 400
    
    agent = Agent(g.tenant.id, g.user.id, g.user.role)
    result = agent.process(text)
    
    return jsonify({
        "success": result.success,
        "message": result.message,
        "data": result.data,
        "target_url": result.target_url,
    })

@agent_bp.route("/api/agent/tools", methods=["GET"])
@login_required
def agent_tools():
    """Return all available tools for the current user."""
    from app.shunya.agent import registry, ToolPermission
    
    tools = []
    for t in registry.all():
        # Filter by permission
        if g.user.role != "admin" and t.permission == ToolPermission.ADMIN:
            continue
        tools.append({
            "id": t.id,
            "name": t.name,
            "description": t.description,
            "category": t.category.value,
            "tier": t.tier,
            "examples": t.examples[:3],
        })
    
    return jsonify({"tools": tools, "count": len(tools)})

@agent_bp.route("/api/agent/parse", methods=["POST"])
@login_required
def agent_parse():
    """Parse text into structured intent without executing."""
    from app.shunya.agent import parse_intent, registry
    
    data = request.get_json() or {}
    text = data.get("text", "").strip()
    if not text:
        return jsonify({"error": "No text"}), 400
    
    intent = parse_intent(text)
    matches = registry.match_intent(intent)
    
    return jsonify({
        "intent": {
            "action": intent.action,
            "entity_type": intent.entity_type,
            "confidence": intent.confidence,
            "parameters": {k: v for k, v in intent.parameters.items() if k != 'raw'},
        },
        "matched_tools": [
            {"id": t.id, "name": t.name, "tier": t.tier}
            for t in matches[:5]
        ],
    })