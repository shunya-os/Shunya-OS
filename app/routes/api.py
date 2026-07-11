"""Shunya OS — Public API."""
from flask import Blueprint, request, jsonify, g
from app import db
from app.models import Entity, EntityDefinition, ActivityLog, KnowledgeEntry, TeamMember
from app.routes.auth import login_required
from datetime import datetime

api_bp = Blueprint("api", __name__)


# ---------------------------------------------------------------------------
# Entity CRUD API
# ---------------------------------------------------------------------------

@api_bp.route("/entities/<entity_type>", methods=["GET"])
@login_required
def api_list_entities(entity_type):
    definition = EntityDefinition.query.filter_by(
        tenant_id=g.tenant.id, type=entity_type, is_active=True
    ).first()
    if not definition:
        return jsonify({"error": f"Entity type '{entity_type}' not found"}), 404

    entities = Entity.query.filter_by(
        tenant_id=g.tenant.id, definition_id=definition.id, is_archived=False
    ).order_by(Entity.created_at.desc()).limit(100).all()

    return jsonify({"entities": [e.to_dict() for e in entities]})


@api_bp.route("/entities/<entity_type>", methods=["POST"])
@login_required
def api_create_entity(entity_type):
    definition = EntityDefinition.query.filter_by(
        tenant_id=g.tenant.id, type=entity_type, is_active=True
    ).first()
    if not definition:
        return jsonify({"error": f"Entity type '{entity_type}' not found"}), 404

    data = request.get_json(silent=True) or {}
    from app.models import next_entity_code
    code = next_entity_code(db.session, g.tenant.id)

    entity_data = {}
    for field in definition.schema:
        fname = field["name"]
        if fname in data:
            entity_data[fname] = data[fname]

    entity = Entity(
        tenant_id=g.tenant.id,
        definition_id=definition.id,
        code=code,
        status=data.get("status", "new"),
        data=entity_data,
        created_by=g.user.id,
    )
    db.session.add(entity)
    db.session.flush()

    activity = ActivityLog(
        tenant_id=g.tenant.id,
        entity_id=entity.id,
        user_id=g.user.id,
        action="created",
        detail=f"Created via API",
        governance_level="auto",
    )
    db.session.add(activity)
    db.session.commit()

    return jsonify({"success": True, "entity": entity.to_dict()}), 201


@api_bp.route("/entities/<entity_type>/<int:entity_id>", methods=["GET"])
@login_required
def api_get_entity(entity_type, entity_id):
    entity = Entity.query.filter_by(id=entity_id, tenant_id=g.tenant.id).first()
    if not entity:
        return jsonify({"error": "Not found"}), 404
    return jsonify({"entity": entity.to_dict()})


@api_bp.route("/entities/<entity_type>/<int:entity_id>", methods=["PUT"])
@login_required
def api_update_entity(entity_type, entity_id):
    entity = Entity.query.filter_by(id=entity_id, tenant_id=g.tenant.id).first()
    if not entity:
        return jsonify({"error": "Not found"}), 404

    data = request.get_json(silent=True) or {}
    if "data" in data and isinstance(data["data"], dict):
        entity.data.update(data["data"])
    if "status" in data:
        entity.status = data["status"]

    activity = ActivityLog(
        tenant_id=g.tenant.id,
        entity_id=entity.id,
        user_id=g.user.id,
        action="updated",
        detail="Updated via API",
    )
    db.session.add(activity)
    db.session.commit()
    return jsonify({"success": True, "entity": entity.to_dict()})


@api_bp.route("/entities/<entity_type>/<int:entity_id>", methods=["DELETE"])
@login_required
def api_delete_entity(entity_type, entity_id):
    entity = Entity.query.filter_by(id=entity_id, tenant_id=g.tenant.id).first()
    if not entity:
        return jsonify({"error": "Not found"}), 404
    entity.is_archived = True

    activity = ActivityLog(
        tenant_id=g.tenant.id,
        entity_id=entity.id,
        user_id=g.user.id,
        action="archived",
        detail="Deleted via API",
    )
    db.session.add(activity)
    db.session.commit()
    return jsonify({"success": True})


# ---------------------------------------------------------------------------
# AI Query API
# ---------------------------------------------------------------------------

@api_bp.route("/ai/query", methods=["POST"])
@login_required
def ai_query():
    """Ask the AI a question — searches internal data first, then web.
    
    Returns structured context with source attribution so the frontend
    can show whether the answer came from company knowledge or the web.
    """
    data = request.get_json(silent=True) or {}
    query = data.get("query", "").strip()
    if not query:
        return jsonify({"error": "Query required"}), 400

    from app.shunya.knowledge import KnowledgePipeline

    # Search internal data AND web, then compare
    context = KnowledgePipeline.get_context_for_ai(query, g.tenant.id)

    # Build a conversational response
    response_parts = []

    if context["internal_sources"]:
        for src in context["internal_sources"]:
            content = src.get("content", "")
            label = src.get("label", "Company Knowledge")
            response_parts.append(f"📚 *From {label}*\n{content[:500]}")

    if context["web_sources"]:
        for src in context["web_sources"]:
            title = src.get("title", "")
            url = src.get("url", "")
            snippet = src.get("snippet", "")
            response_parts.append(f"🌐 *From the web: {title}*\n{snippet[:300]}\n_{url}_")

    if not response_parts:
        response_parts.append("I searched your company data and the web but couldn't find a clear answer. "
                              "Could you tell me more about what you're looking for? "
                              "If you have a document with this information, upload it on the **Ingest** page and I'll learn from it.")

    needs_verify = context.get("needs_verification", False)
    verify_reason = context.get("verification_reason", "")

    response_text = "\n\n".join(response_parts[:3])
    if needs_verify:
        response_text += f"\n\n⚠️ *Note:* {verify_reason}"

    return jsonify({
        "query": query,
        "response": response_text,
        "context": context,
        "has_internal_data": context["has_internal_data"],
        "has_web_data": context["has_web_data"],
        "needs_verification": needs_verify,
        "verification_reason": verify_reason,
    })


# ---------------------------------------------------------------------------
# Webhook receiver (for integrations)
# ---------------------------------------------------------------------------

@api_bp.route("/ai/action", methods=["POST"])
@login_required
def ai_action():
    """Parse intent from natural language and execute or return confirmation card.
    
    Detects if a query is an action (create/update/delete/send) or a question.
    For actions: returns structured intent with parsed data for confirmation.
    For questions: falls through to the existing knowledge pipeline.
    """
    data = request.get_json(silent=True) or {}
    query = data.get("query", "").strip()
    confirmed = data.get("confirmed", False)
    intent_data = data.get("intent_data")  # Passed on confirm step
    
    if not query:
        return jsonify({"error": "Query required"}), 400
    
    # If this is a confirmation of a previous intent
    if confirmed and intent_data:
        return _execute_intent(intent_data, g.tenant.id, g.user.id, g.user.name)
    
    # Detect action intent
    intent = _detect_intent(query, g.tenant.id)
    
    if intent["type"] == "question":
        # Fall through to existing knowledge pipeline
        from app.shunya.knowledge import KnowledgePipeline
        context = KnowledgePipeline.get_context_for_ai(query, g.tenant.id)
        return jsonify({
            "intent": {"type": "question"},
            "query": query,
            "response": _build_knowledge_response(context),
            "has_internal_data": context.get("has_internal_data", False),
            "has_web_data": context.get("has_web_data", False),
            "needs_verification": context.get("needs_verification", False),
        })
    
    # For action intents, return the confirmation card
    return jsonify({
        "intent": intent,
        "query": query,
        "confirmation_card": intent.get("confirmation_card"),
        "missing_required": intent.get("missing_required", []),
    })


@api_bp.route("/ai/action/execute", methods=["POST"])
@login_required
def ai_execute():
    """Execute a confirmed action intent."""
    data = request.get_json(silent=True) or {}
    intent_data = data.get("intent_data", {})
    if not intent_data:
        return jsonify({"error": "Intent data required"}), 400
    result = _execute_intent(intent_data, g.tenant.id, g.user.id, g.user.name)
    return jsonify(result)


def _detect_intent(query: str, tenant_id: int) -> dict:
    """Detect whether a query is an action or a question, parse it."""
    from app.models import EntityDefinition
    import re
    
    q = query.lower().strip()
    
    # ── Detect action types ──
    create_patterns = [r"^(?:create|add|new|make|register|record|track)\s+(?:a\s+|an\s+|the\s+)?(.+)"]
    search_patterns = [r"^(?:search|find|look\s*up|google|web)\s+(.+)"]
    show_patterns = [r"^(?:show|list|get|find|display|view)\s+(?:me\s+)?(.+)"]
    update_patterns = [r"^(?:update|change|edit|modify|set)\s+(?:the\s+)?(.+)"]
    
    # Check create patterns first
    for pat in create_patterns:
        m = re.search(pat, q)
        if m:
            rest = m.group(1).strip()
            # Try to match entity type
            return _parse_create_intent(rest, query, tenant_id)
    
    # Check show/list patterns (these could be queries OR data requests)
    for pat in show_patterns:
        m = re.search(pat, q)
        if m:
            rest = m.group(1).strip()
            # Check if it's a known entity type
            entity_type = _match_entity_type(rest, tenant_id)
            if entity_type:
                return {
                    "type": "show",
                    "entity_type": entity_type,
                    "display": f"Show {entity_type.replace('_', ' ')}s",
                    "target": f"/entities/{entity_type}",
                    "confirmation_card": {
                        "icon": "📊",
                        "title": f"Show {entity_type.replace('_', ' ').title()}s",
                        "action": "redirect",
                        "url": f"/entities/{entity_type}",
                    }
                }
    
    # Check search patterns (web search)
    for pat in search_patterns:
        m = re.search(pat, q)
        if m:
            search_term = m.group(1).strip()
            return {
                "type": "question",
                "hint": "web_search",
                "query": search_term,
            }
    
    # Default: question
    return {"type": "question"}


def _parse_create_intent(rest: str, full_query: str, tenant_id: int) -> dict:
    """Parse a 'create X for...' intent into structured data."""
    from app.models import EntityDefinition
    from app.conversational import ConversationalEngine
    from app.models import next_entity_code
    
    q = full_query
    entity_type = _extract_entity_type_from_query(q, tenant_id)
    
    if not entity_type:
        # Try to find the entity type from the first word of rest
        first_word = rest.split()[0].rstrip("s")
        definition = EntityDefinition.query.filter(
            EntityDefinition.tenant_id == tenant_id,
            EntityDefinition.is_active == True,
            EntityDefinition.type.ilike(first_word)
        ).first()
        if not definition:
            # Try broader match
            definitions = EntityDefinition.query.filter_by(
                tenant_id=tenant_id, is_active=True
            ).all()
            for d in definitions:
                if d.type in rest or d.label.lower() in rest:
                    entity_type = d.type
                    break
        
        if not entity_type:
            return {
                "type": "question",
                "hint": "unknown_entity",
                "message": "I'm not sure what to create. Try 'create a lead for...' or check your entity types in Settings."
            }
    
    definition = EntityDefinition.query.filter_by(
        tenant_id=tenant_id, type=entity_type
    ).first()
    
    # Parse fields using conversational engine
    parsed = ConversationalEngine.parse_and_fill(full_query, entity_type, tenant_id)
    
    if "error" in parsed:
        return {"type": "question", "hint": "error", "message": parsed["error"]}
    
    code = next_entity_code(__import__("flask").current_app.extensions["sqlalchemy"].session, tenant_id)
    
    confirmation_card = ConversationalEngine.build_confirmation_card(
        parsed["parsed_data"], definition, code
    )
    
    return {
        "type": "create",
        "entity_type": entity_type,
        "parsed_data": parsed["parsed_data"],
        "missing_required": parsed["missing_required"],
        "confidence": parsed["confidence"],
        "suggested_status": parsed["suggested_status"],
        "code": code,
        "entity_type_label": definition.label,
        "entity_type_icon": definition.icon,
        "confirmation_card": confirmation_card,
    }


def _execute_intent(intent_data: dict, tenant_id: int, user_id: int, user_name: str) -> dict:
    """Execute a confirmed action intent."""
    from app import db
    from app.models import Entity, EntityDefinition, ActivityLog, next_entity_code
    from datetime import datetime
    
    intent_type = intent_data.get("type")
    
    if intent_type == "create":
        entity_type = intent_data.get("entity_type")
        parsed_data = intent_data.get("parsed_data", {})
        status = intent_data.get("suggested_status", "new")
        code = intent_data.get("code")
        
        definition = EntityDefinition.query.filter_by(
            tenant_id=tenant_id, type=entity_type
        ).first()
        if not definition:
            return {"success": False, "error": f"Entity type '{entity_type}' not found"}
        
        if not code:
            code = next_entity_code(db.session, tenant_id)
        
        entity = Entity(
            tenant_id=tenant_id,
            definition_id=definition.id,
            code=code,
            status=status,
            data=parsed_data,
            created_by=user_id,
        )
        db.session.add(entity)
        db.session.flush()
        
        activity = ActivityLog(
            tenant_id=tenant_id,
            entity_id=entity.id,
            user_id=user_id,
            action="created",
            detail=f"Created via Bird AI: {definition.label} ({code})",
            governance_level="auto",
        )
        db.session.add(activity)
        db.session.commit()
        
        return {
            "success": True,
            "action": "created",
            "entity_type": entity_type,
            "entity_id": entity.id,
            "code": code,
            "label": definition.label,
            "icon": definition.icon,
            "message": f"✅ **{definition.label} created** ({code})",
            "target": f"/entities/{entity_type}/{entity.id}",
        }
    
    return {"success": False, "error": f"Unknown action type: {intent_type}"}


def _match_entity_type(text: str, tenant_id: int) -> str:
    """Try to match text to an entity type slug."""
    from app.models import EntityDefinition
    definitions = EntityDefinition.query.filter_by(
        tenant_id=tenant_id, is_active=True
    ).all()
    text_lower = text.lower().rstrip("s")
    for d in definitions:
        if d.type in text_lower or d.label.lower() in text_lower:
            return d.type
    return None


def _extract_entity_type_from_query(query: str, tenant_id: int) -> str:
    """Extract the entity type from a query string."""
    from app.models import EntityDefinition
    definitions = EntityDefinition.query.filter_by(
        tenant_id=tenant_id, is_active=True
    ).all()
    q = query.lower()
    
    # Score each definition by how many of its keywords appear in the query
    best_match = None
    best_score = 0
    for d in definitions:
        keywords = [d.type, d.label.lower()] + [d.label.lower().rstrip("s")]
        score = sum(1 for kw in keywords if kw in q)
        if score > best_score:
            best_score = score
            best_match = d.type
    
    return best_match if best_score > 0 else None


def _build_knowledge_response(context: dict) -> str:
    """Build a conversational response from knowledge context."""
    parts = []
    for src in context.get("internal_sources", []):
        content = src.get("content", "")
        label = src.get("label", "Company Knowledge")
        parts.append(f"📚 *From {label}*\n{content[:500]}")
    
    for src in context.get("web_sources", []):
        title = src.get("title", "")
        url = src.get("url", "")
        snippet = src.get("snippet", "")
        parts.append(f"🌐 *From the web: {title}*\n{snippet[:300]}\n_{url}_")
    
    if not parts:
        return ("I searched your company data but couldn't find a clear answer. "
                "Try asking differently, or upload a document on the **Ingest** page "
                "and I'll learn from it.")
    
    return "\n\n".join(parts[:3])


@api_bp.route("/webhook/<integration>", methods=["POST"])
def webhook_receiver(integration):
    """Generic webhook receiver for external integrations."""
    payload = request.get_json(silent=True) or {}
    # TODO: Route to integration handler based on `integration` param
    return jsonify({"success": True, "integration": integration})


# ---------------------------------------------------------------------------
# Global Search (Cmd+K)
# ---------------------------------------------------------------------------

@api_bp.route("/search", methods=["GET"])
@login_required
def global_search():
    """Search across all data sources — entities, knowledge, customer memory."""
    query = request.args.get("q", "").strip()
    if not query or len(query) < 2:
        return jsonify({"results": []})

    from app.shunya.command_palette import CommandPalette
    results = CommandPalette.search(query, g.tenant.id, g.user.id, g.user.role)
    return jsonify({"results": results, "query": query})


# ---------------------------------------------------------------------------
# Data export
# ---------------------------------------------------------------------------

@api_bp.route("/export", methods=["GET"])
@login_required
def export_data():
    import json
    from app.models import Entity, EntityDefinition

    entity_type = request.args.get("type")
    export = {}

    definitions = EntityDefinition.query.filter_by(tenant_id=g.tenant.id).all()
    for d in definitions:
        if entity_type and d.type != entity_type:
            continue
        entities = Entity.query.filter_by(
            tenant_id=g.tenant.id, definition_id=d.id, is_archived=False
        ).all()
        export[d.type] = {
            "definition": d.to_dict(),
            "entities": [e.to_dict() for e in entities],
        }

    return jsonify({"export": export, "exported_at": datetime.utcnow().isoformat()})


# ---------------------------------------------------------------------------
# Learning Engine API
# ---------------------------------------------------------------------------

@api_bp.route("/learning/proposals", methods=["GET"])
@login_required
def get_learning_proposals():
    """Get learning proposals for the current tenant."""
    from app.shunya.learning import LearningEngine
    status = request.args.get("status")
    proposals = LearningEngine.get_proposals(g.tenant.id, status)
    return jsonify({"proposals": proposals})


@api_bp.route("/learning/scan", methods=["POST"])
@login_required
def scan_for_learning():
    """Run pattern scan and create learning proposals."""
    from app.shunya.learning import LearningEngine
    result = LearningEngine.run_auto_scan(g.tenant.id, g.user.id)
    return jsonify(result)


@api_bp.route("/learning/review", methods=["POST"])
@login_required
def review_learning():
    """Review a learning proposal (approve/reject/request_more)."""
    from app.shunya.learning import LearningEngine
    data = request.get_json(silent=True) or {}
    proposal_id = data.get("proposal_id")
    decision = data.get("decision", "")
    feedback = data.get("feedback")
    
    if not proposal_id or not decision:
        return jsonify({"error": "proposal_id and decision required"}), 400
    
    result = LearningEngine.review_proposal(proposal_id, g.tenant.id, g.user.id, decision, feedback)
    return jsonify({"success": result.success, "data": result.data})


# ---------------------------------------------------------------------------
# Orchestrator API
# ---------------------------------------------------------------------------

@api_bp.route("/orchestrate", methods=["POST"])
@login_required
def orchestrate():
    """Route a query through the multi-agent orchestrator."""
    data = request.get_json(silent=True) or {}
    query = data.get("query", "").strip()
    capabilities = data.get("capabilities")
    entity_id = data.get("entity_id")
    
    if not query:
        return jsonify({"error": "Query required"}), 400
    
    from app.shunya.orchestrator import get_orchestrator
    orchestrator = get_orchestrator()
    result = orchestrator.route(
        query=query,
        tenant_id=g.tenant.id,
        user_id=g.user.id,
        user_role=g.user.role,
        entity_id=entity_id,
        capabilities=capabilities,
    )
    return jsonify(result)


@api_bp.route("/orchestrate/agents", methods=["GET"])
@login_required
def list_agents():
    """List all registered specialist agents."""
    from app.shunya.orchestrator import get_orchestrator
    orchestrator = get_orchestrator()
    agents = orchestrator.list_agents()
    return jsonify({"agents": agents, "count": len(agents)})
