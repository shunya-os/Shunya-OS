"""SHUNYA Phase A1 — Space API Routes.

RESTful API for the Universal SHUNYA Space.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from flask import Blueprint, jsonify, request, g

from app.space.store import get_store, reset_store
from app.space.renderer import get_renderer
from app.space.navigation import get_navigator
from app.space.context import get_context_manager
from app.space.commands import get_executor
from app.space.timeline import get_timeline_manager
from app.space.knowledge import get_knowledge_manager
from app.space.relationships import get_relationship_manager
from app.space.models import SpaceTimelineEvent, SpaceKnowledgeItem, SpacePlanRef

# =========================================================================
# Blueprint
# =========================================================================

space_bp = Blueprint("space", __name__, url_prefix="/api/v1/space")


# =========================================================================
# Space CRUD
# =========================================================================


@space_bp.route("", methods=["POST"])
def create_space():
    """Create a new Space for an entity."""
    data = request.get_json(silent=True) or {}
    entity_id = data.get("entity_id", "")
    entity_type = data.get("entity_type", "generic")
    name = data.get("name", "Untitled Space")
    parent_space_id = data.get("parent_space_id", "")

    if not entity_id:
        entity_id = f"ent_{uuid.uuid4().hex[:24]}"

    store = get_store()
    space = store.create(
        entity_id=entity_id,
        entity_type=entity_type,
        name=name,
        parent_space_id=parent_space_id,
        metadata=data.get("metadata"),
    )
    return jsonify({"success": True, "space": space.to_summary()}), 201


@space_bp.route("/<space_id>", methods=["GET"])
def get_space(space_id):
    """Get a Space by ID with all panels."""
    store = get_store()
    space = store.get(space_id)
    if not space:
        return jsonify({"error": "Space not found"}), 404

    renderer = get_renderer()
    render_context = {"user_id": getattr(g, "user_id", "")}
    rendered = renderer.render(space, context=render_context)
    return jsonify({"success": True, "space": rendered})


@space_bp.route("/<space_id>", methods=["PUT"])
def update_space(space_id):
    """Update a Space."""
    data = request.get_json(silent=True) or {}
    store = get_store()
    space = store.update(space_id, **data)
    if not space:
        return jsonify({"error": "Space not found"}), 404
    return jsonify({"success": True, "space": space.to_summary()})


@space_bp.route("/<space_id>", methods=["DELETE"])
def delete_space(space_id):
    """Delete a Space."""
    store = get_store()
    if not store.delete(space_id):
        return jsonify({"error": "Space not found"}), 404
    return jsonify({"success": True, "message": "Space deleted"})


# =========================================================================
# Summary / List
# =========================================================================


@space_bp.route("/<space_id>/summary", methods=["GET"])
def get_space_summary(space_id):
    """Get a lightweight summary of a Space."""
    store = get_store()
    space = store.get(space_id)
    if not space:
        return jsonify({"error": "Space not found"}), 404
    return jsonify({"success": True, "summary": space.to_summary()})


@space_bp.route("", methods=["GET"])
def list_spaces():
    """List all Spaces with optional type filter."""
    store = get_store()
    entity_type = request.args.get("type", "")
    status = request.args.get("status", "")

    if entity_type:
        spaces = store.list_by_type(entity_type)
    elif status:
        from app.space.models import SpaceStatus
        try:
            spaces = store.list_by_status(SpaceStatus(status))
        except ValueError:
            spaces = store.list_all()
    else:
        spaces = store.list_all()

    return jsonify({
        "success": True,
        "spaces": [s.to_summary() for s in spaces],
        "total": len(spaces),
    })


# =========================================================================
# Navigation
# =========================================================================


@space_bp.route("/search", methods=["GET"])
def search_spaces():
    """Search across all Spaces."""
    query = request.args.get("q", "")
    navigator = get_navigator()
    results = navigator.search(query)
    return jsonify({
        "success": True,
        "results": results,
        "total": len(results),
    })


@space_bp.route("/navigate", methods=["POST"])
def navigate_to_space():
    """Navigate to a Space. Creates it if it doesn't exist."""
    data = request.get_json(silent=True) or {}
    entity_id = data.get("entity_id", "")
    entity_type = data.get("entity_type", "generic")
    name = data.get("name", "Untitled")
    parent_space_id = data.get("parent_space_id", "")

    navigator = get_navigator()
    result = navigator.open_or_create(
        entity_id=entity_id,
        entity_type=entity_type,
        name=name,
        parent_space_id=parent_space_id,
    )
    return jsonify({
        "success": True,
        "navigation": result.to_dict(),
    })


@space_bp.route("/<space_id>/breadcrumb", methods=["GET"])
def get_breadcrumb(space_id):
    """Get breadcrumb trail for a Space."""
    navigator = get_navigator()
    trail = navigator.breadcrumb(space_id)
    return jsonify({"success": True, "breadcrumb": trail})


@space_bp.route("/<space_id>/tree", methods=["GET"])
def get_space_tree(space_id):
    """Get the nested Space tree for a root Space."""
    navigator = get_navigator()
    tree = navigator.space_tree(space_id)
    return jsonify({"success": True, "tree": tree})


# =========================================================================
# Context
# =========================================================================


@space_bp.route("/<space_id>/context", methods=["GET"])
def get_space_context(space_id):
    """Get the saved context for a Space."""
    manager = get_context_manager()
    ctx = manager.restore(space_id)
    if not ctx:
        return jsonify({"error": "Space not found"}), 404
    return jsonify({"success": True, "context": ctx})


@space_bp.route("/<space_id>/context", methods=["PUT"])
def update_space_context(space_id):
    """Update the context for a Space."""
    data = request.get_json(silent=True) or {}
    manager = get_context_manager()
    if not manager.update_context(space_id, **data):
        return jsonify({"error": "Space not found"}), 404
    return jsonify({"success": True, "message": "Context updated"})


# =========================================================================
# Timeline
# =========================================================================


@space_bp.route("/<space_id>/timeline", methods=["GET"])
def get_space_timeline(space_id):
    """Get the timeline for a Space."""
    limit = request.args.get("limit", 50, type=int)
    category = request.args.get("category", "")
    manager = get_timeline_manager()
    events = manager.get_timeline(space_id, limit=limit, category=category)
    return jsonify({
        "success": True,
        "events": [e.to_dict() for e in events],
        "total": len(events),
    })


@space_bp.route("/<space_id>/timeline", methods=["POST"])
def add_timeline_event(space_id):
    """Add an event to the Space timeline."""
    data = request.get_json(silent=True) or {}
    manager = get_timeline_manager()
    event = manager.add_event(
        space_id,
        event_type=data.get("event_type", "observation"),
        title=data.get("title", ""),
        description=data.get("description", ""),
        actor=data.get("actor", getattr(g, "user_id", "")),
        importance=data.get("importance", 0.5),
        category=data.get("category", ""),
        payload=data.get("payload"),
    )
    if not event:
        return jsonify({"error": "Space not found"}), 404
    return jsonify({"success": True, "event": event.to_dict()}), 201


# =========================================================================
# Knowledge
# =========================================================================


@space_bp.route("/<space_id>/knowledge", methods=["GET"])
def get_space_knowledge(space_id):
    """Get knowledge items for a Space."""
    item_type = request.args.get("item_type", "")
    manager = get_knowledge_manager()
    items = manager.get_items(space_id, item_type)
    return jsonify({
        "success": True,
        "items": [i.to_dict() for i in items],
        "total": len(items),
    })


@space_bp.route("/<space_id>/knowledge", methods=["POST"])
def add_knowledge_item(space_id):
    """Add a knowledge item to a Space."""
    data = request.get_json(silent=True) or {}
    manager = get_knowledge_manager()
    item = manager.add_item(
        space_id,
        item_type=data.get("item_type", "document"),
        title=data.get("title", ""),
        content_summary=data.get("content_summary", ""),
        source=data.get("source", ""),
        metadata=data.get("metadata"),
    )
    if not item:
        return jsonify({"error": "Space not found"}), 404
    return jsonify({"success": True, "item": item.to_dict()}), 201


# =========================================================================
# Relationships
# =========================================================================


@space_bp.route("/<space_id>/relationships", methods=["GET"])
def get_space_relationships(space_id):
    """Get relationships for a Space."""
    manager = get_relationship_manager()
    rels = manager.get_relationships(space_id)
    return jsonify({
        "success": True,
        "relationships": [r.to_dict() for r in rels],
        "total": len(rels),
    })


@space_bp.route("/<space_id>/relationships/graph", methods=["GET"])
def get_space_relationship_graph(space_id):
    """Get the relationship graph for a Space."""
    manager = get_relationship_manager()
    graph = manager.get_graph(space_id)
    return jsonify({"success": True, "graph": graph})


@space_bp.route("/<space_id>/relationships", methods=["POST"])
def add_space_relationship(space_id):
    """Add a relationship to a Space."""
    data = request.get_json(silent=True) or {}
    manager = get_relationship_manager()
    success = manager.add_relationship(
        space_id,
        rel_id=data.get("rel_id", f"rel_{uuid.uuid4().hex[:16]}"),
        target_entity_id=data.get("target_entity_id", ""),
        target_entity_name=data.get("target_entity_name", ""),
        target_entity_type=data.get("target_entity_type", ""),
        rel_type=data.get("rel_type", "related_to"),
        direction=data.get("direction", "outgoing"),
        confidence=data.get("confidence", 1.0),
        metadata=data.get("metadata"),
    )
    if not success:
        return jsonify({"error": "Space not found"}), 404
    return jsonify({"success": True, "message": "Relationship added"}), 201


# =========================================================================
# Commands
# =========================================================================


@space_bp.route("/<space_id>/commands", methods=["GET"])
def get_space_commands(space_id):
    """Get available commands for a Space."""
    store = get_store()
    space = store.get(space_id)
    if not space:
        return jsonify({"error": "Space not found"}), 404
    executor = get_executor()
    commands = executor.get_available_commands(space)
    return jsonify({"success": True, "commands": commands})


@space_bp.route("/<space_id>/commands/<command_name>", methods=["POST"])
def execute_space_command(space_id, command_name):
    """Execute a command on a Space."""
    store = get_store()
    space = store.get(space_id)
    if not space:
        return jsonify({"error": "Space not found"}), 404
    params = request.get_json(silent=True) or {}
    executor = get_executor()
    result = executor.execute(space, command_name, params)
    return jsonify({"success": result.get("success", False), "result": result})


# =========================================================================
# Plans
# =========================================================================


@space_bp.route("/<space_id>/plans", methods=["GET"])
def get_space_plans(space_id):
    """Get plans for a Space."""
    store = get_store()
    space = store.get(space_id)
    if not space:
        return jsonify({"error": "Space not found"}), 404
    return jsonify({
        "success": True,
        "plans": [p.to_dict() for p in space.plans],
        "total": len(space.plans),
    })


@space_bp.route("/<space_id>/plans", methods=["POST"])
def add_space_plan(space_id):
    """Add a plan to a Space."""
    data = request.get_json(silent=True) or {}
    store = get_store()
    plan = SpacePlanRef(
        plan_id=data.get("plan_id", f"pln_{uuid.uuid4().hex[:16]}"),
        title=data.get("title", "Untitled Plan"),
        state=data.get("state", "proposed"),
        priority=data.get("priority", "normal"),
        metadata=data.get("metadata"),
    )
    if not store.add_plan(space_id, plan):
        return jsonify({"error": "Space not found"}), 404
    return jsonify({"success": True, "plan": plan.to_dict()}), 201


# =========================================================================
# Metrics
# =========================================================================


@space_bp.route("/<space_id>/metrics", methods=["GET"])
def get_space_metrics(space_id):
    """Get metrics for a Space."""
    from app.space.models import SpaceMetric
    store = get_store()
    space = store.get(space_id)
    if not space:
        return jsonify({"error": "Space not found"}), 404
    return jsonify({
        "success": True,
        "metrics": [m.to_dict() for m in space.metrics],
        "total": len(space.metrics),
    })


@space_bp.route("/<space_id>/metrics", methods=["POST"])
def add_space_metric(space_id):
    """Add a metric to a Space."""
    from app.space.models import SpaceMetric
    data = request.get_json(silent=True) or {}
    store = get_store()
    metric = SpaceMetric(
        metric_id=data.get("metric_id", f"met_{uuid.uuid4().hex[:16]}"),
        name=data.get("name", ""),
        value=data.get("value"),
        unit=data.get("unit", ""),
        trend=data.get("trend", "stable"),
        confidence=data.get("confidence", 1.0),
        metadata=data.get("metadata"),
    )
    if not store.add_metric(space_id, metric):
        return jsonify({"error": "Space not found"}), 404
    return jsonify({"success": True, "metric": metric.to_dict()}), 201


# =========================================================================
# AI Understanding
# =========================================================================


@space_bp.route("/<space_id>/ai-understanding", methods=["GET"])
def get_ai_understanding(space_id):
    """Get the AI understanding for a Space."""
    store = get_store()
    space = store.get(space_id)
    if not space:
        return jsonify({"error": "Space not found"}), 404
    return jsonify({
        "success": True,
        "ai_understanding": space.ai_understanding.to_dict(),
    })


@space_bp.route("/<space_id>/ai-understanding", methods=["PUT"])
def update_ai_understanding(space_id):
    """Update the AI understanding for a Space."""
    from app.space.models import SpaceAIUnderstanding
    data = request.get_json(silent=True) or {}
    store = get_store()
    space = store.get(space_id)
    if not space:
        return jsonify({"error": "Space not found"}), 404

    understanding = SpaceAIUnderstanding(
        summary=data.get("summary", space.ai_understanding.summary),
        goals=data.get("goals", space.ai_understanding.goals),
        current_plans=data.get("current_plans",
                               space.ai_understanding.current_plans),
        current_communications=data.get(
            "current_communications",
            space.ai_understanding.current_communications,
        ),
        current_responsibilities=data.get(
            "current_responsibilities",
            space.ai_understanding.current_responsibilities,
        ),
        current_risks=data.get("current_risks",
                               space.ai_understanding.current_risks),
        current_opportunities=data.get(
            "current_opportunities",
            space.ai_understanding.current_opportunities,
        ),
        current_knowledge=data.get("current_knowledge",
                                   space.ai_understanding.current_knowledge),
        metadata=data.get("metadata", space.ai_understanding.metadata),
    )
    store.update_ai_understanding(space_id, understanding)
    return jsonify({"success": True, "ai_understanding": understanding.to_dict()})


# =========================================================================
# Children / Nesting
# =========================================================================


@space_bp.route("/<space_id>/children", methods=["GET"])
def get_space_children(space_id):
    """Get child Spaces."""
    store = get_store()
    children = store.list_children(space_id)
    return jsonify({
        "success": True,
        "children": [c.to_summary() for c in children],
        "total": len(children),
    })


@space_bp.route("/<space_id>/children", methods=["POST"])
def add_space_child(space_id):
    """Add a child Space."""
    data = request.get_json(silent=True) or {}
    child_entity_id = data.get("child_entity_id", "")
    child_entity_type = data.get("child_entity_type", "generic")
    child_name = data.get("child_name", "Untitled")

    store = get_store()
    navigator = get_navigator()
    result = navigator.open_or_create(
        entity_id=child_entity_id,
        entity_type=child_entity_type,
        name=child_name,
        parent_space_id=space_id,
    )
    if not result.space:
        return jsonify({"error": "Could not create child Space"}), 400

    store.add_child(space_id, result.space.space_id)
    return jsonify({
        "success": True,
        "child": result.space.to_summary(),
        "navigation": result.to_dict(),
    }), 201


# =========================================================================
# Capabilities
# =========================================================================


@space_bp.route("/capabilities", methods=["GET"])
def list_all_capabilities():
    """List all registered capabilities."""
    from app.space.capabilities import get_registry
    registry = get_registry()
    caps = registry.list_capabilities()
    return jsonify({
        "success": True,
        "capabilities": [c.to_dict() for c in caps],
        "total": len(caps),
    })


@space_bp.route("/<space_id>/capabilities", methods=["GET"])
def get_space_capabilities(space_id):
    """Get capabilities for a Space."""
    store = get_store()
    space = store.get(space_id)
    if not space:
        return jsonify({"error": "Space not found"}), 404
    from app.space.capabilities import get_registry
    registry = get_registry()
    caps = registry.discover_capabilities(space)
    return jsonify({
        "success": True,
        "capabilities": [c.to_dict() for c in caps],
        "visible_panels": [p.value for p in registry.get_panels_for(space.entity_type)],
    })


# =========================================================================
# Lifecycle
# =========================================================================


@space_bp.route("/<space_id>/lifecycle", methods=["GET"])
def get_lifecycle(space_id):
    """Get the lifecycle state of a Space."""
    store = get_store()
    space = store.get(space_id)
    if not space:
        return jsonify({"error": "Space not found"}), 404
    return jsonify({
        "success": True,
        "lifecycle": space.lifecycle.to_dict(),
        "valid_transitions": [
            s.value for s in __import__(
                "app.space.lifecycle", fromlist=["LifecycleState"]
            ).LIFECYCLE_TRANSITIONS.get(
                space.lifecycle.state, []
            )
        ],
    })


@space_bp.route("/<space_id>/lifecycle", methods=["PUT"])
def transition_lifecycle(space_id):
    """Transition a Space to a new lifecycle state."""
    data = request.get_json(silent=True) or {}
    target = data.get("state", "")
    from app.space.lifecycle import LifecycleManager, LifecycleState
    try:
        target_state = LifecycleState(target)
    except ValueError:
        return jsonify({"error": f"Invalid lifecycle state: {target}"}), 400
    mgr = LifecycleManager()
    result = mgr.transition(space_id, target_state)
    if not result:
        return jsonify({"error": "Transition not allowed or Space not found"}), 400
    return jsonify({
        "success": True,
        "lifecycle": result.to_dict(),
    })


# =========================================================================
# AI Resident
# =========================================================================


@space_bp.route("/<space_id>/ai-resident", methods=["GET"])
def get_ai_resident(space_id):
    """Get the persistent AI resident state for a Space."""
    from app.space.resident import get_resident_manager
    mgr = get_resident_manager()
    snapshot = mgr.get_snapshot(space_id)
    if not snapshot:
        return jsonify({"error": "Space not found"}), 404
    return jsonify({"success": True, "ai_resident": snapshot})


@space_bp.route("/<space_id>/ai-resident", methods=["PUT"])
def update_ai_resident(space_id):
    """Update the AI resident state for a Space."""
    data = request.get_json(silent=True) or {}
    from app.space.resident import get_resident_manager
    mgr = get_resident_manager()

    if "understanding" in data:
        mgr.update_understanding(space_id, data["understanding"])
    if "question" in data:
        mgr.add_question(space_id, data["question"])
    if "close_question" in data:
        mgr.close_question(space_id, data["close_question"])
    if "hypothesis" in data:
        mgr.add_hypothesis(space_id, data["hypothesis"],
                           data.get("confidence", 0.5))
    if "risk" in data:
        mgr.add_risk(space_id, data["risk"],
                     data.get("severity", "medium"),
                     data.get("probability", 0.5))
    if "opportunity" in data:
        mgr.add_opportunity(space_id, data["opportunity"],
                            data.get("potential", "medium"),
                            data.get("confidence", 0.5))
    if "recommendation" in data:
        mgr.add_recommendation(space_id, data["recommendation"])
    if "observation" in data:
        mgr.add_observation(space_id, data["observation"])
    if "confidence" in data:
        mgr.update_confidence(space_id, data["confidence"])

    snapshot = mgr.get_snapshot(space_id)
    return jsonify({"success": True, "ai_resident": snapshot})


# =========================================================================
# Cross-Space Reasoning
# =========================================================================


@space_bp.route("/<space_id>/reason", methods=["POST"])
def reason_about_space(space_id):
    """Run cross-Space reasoning starting from this Space."""
    data = request.get_json(silent=True) or {}
    question = data.get("question", "Why is this Space relevant?")
    max_depth = data.get("max_depth", 3)
    rel_types = data.get("relationship_types", [])

    from app.space.reasoning import (
        ReasoningQuery, get_reasoner,
    )
    query = ReasoningQuery(
        question=question,
        start_space_id=space_id,
        max_depth=max_depth,
        relationship_types=rel_types,
    )
    reasoner = get_reasoner()
    result = reasoner.answer(query)
    return jsonify({
        "success": True,
        "reasoning": result.to_dict(),
    })


@space_bp.route("/reason/path", methods=["POST"])
def find_reasoning_path():
    """Find paths between two Spaces."""
    data = request.get_json(silent=True) or {}
    from_id = data.get("from_space_id", "")
    to_id = data.get("to_space_id", "")
    max_depth = data.get("max_depth", 5)

    if not from_id or not to_id:
        return jsonify({"error": "from_space_id and to_space_id required"}), 400

    from app.space.reasoning import get_reasoner
    reasoner = get_reasoner()
    paths = reasoner.find_paths(from_id, to_id, max_depth=max_depth)
    return jsonify({
        "success": True,
        "paths": [
            [s.to_dict() for s in path] for path in paths
        ],
        "total_paths": len(paths),
    })


# =========================================================================
# Composition
# =========================================================================


@space_bp.route("/<space_id>/composition", methods=["GET"])
def get_composition(space_id):
    """Get the composition summary for a Space."""
    from app.space.composition import get_composite_manager
    mgr = get_composite_manager()
    summary = mgr.get_composition_summary(space_id)
    if not summary:
        return jsonify({"error": "Space not found"}), 404
    return jsonify({"success": True, "composition": summary})


@space_bp.route("/<space_id>/subtree", methods=["GET"])
def get_subtree(space_id):
    """Get the full subtree rooted at this Space."""
    max_depth = request.args.get("max_depth", 5, type=int)
    from app.space.composition import get_composite_manager
    mgr = get_composite_manager()
    tree = mgr.get_subtree(space_id, max_depth=max_depth)
    if not tree:
        return jsonify({"error": "Space not found"}), 404
    return jsonify({"success": True, "tree": tree})


@space_bp.route("/<space_id>/siblings", methods=["GET"])
def get_siblings(space_id):
    """Get sibling Spaces."""
    from app.space.composition import get_composite_manager
    mgr = get_composite_manager()
    siblings = mgr.get_siblings(space_id)
    return jsonify({
        "success": True,
        "siblings": [s.to_summary() for s in siblings],
        "total": len(siblings),
    })


@space_bp.route("/<space_id>/decompose/<child_id>", methods=["POST"])
def decompose_space(space_id, child_id):
    """Remove a child Space from its parent."""
    from app.space.composition import get_composite_manager
    mgr = get_composite_manager()
    if not mgr.decompose(space_id, child_id):
        return jsonify({"error": "Could not decompose"}), 400
    return jsonify({"success": True, "message": "Child removed from parent"})


# =========================================================================
# Reset (for testing)
# =========================================================================


@space_bp.route("/reset", methods=["POST"])
def reset_spaces():
    """Reset the entire Space store (testing only)."""
    reset_store()
    from app.space.renderer import reset_renderer
    from app.space.navigation import reset_navigator
    from app.space.context import reset_context_manager
    from app.space.commands import reset_executor
    from app.space.timeline import reset_timeline_manager
    from app.space.knowledge import reset_knowledge_manager
    from app.space.relationships import reset_relationship_manager

    reset_renderer()
    reset_navigator()
    reset_context_manager()
    reset_executor()
    reset_timeline_manager()
    reset_knowledge_manager()
    reset_relationship_manager()

    return jsonify({"success": True, "message": "All Space stores reset"})