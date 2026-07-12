"""Shunya OS — Public API.

This module uses db.session.query(Model) — never Model.query.
"""
import re
from datetime import datetime
from flask import Blueprint, request, jsonify, g
from app import db
from app.models import (
    Entity, EntityDefinition, ActivityLog, KnowledgeEntry,
    TeamMember, Opportunity, Relationship
)
from app.routes.auth import login_required

api_bp = Blueprint("api", __name__)


# ---------------------------------------------------------------------------
# Entity CRUD API
# ---------------------------------------------------------------------------

@api_bp.route("/entities/<entity_type>", methods=["GET"])
@login_required
def api_list_entities(entity_type):
    definition = db.session.query(EntityDefinition).filter_by(
        tenant_id=g.tenant.id, type=entity_type, is_active=True
    ).first()
    if not definition:
        return jsonify({"error": f"Entity type '{entity_type}' not found"}), 404

    entities = db.session.query(Entity).filter_by(
        tenant_id=g.tenant.id, definition_id=definition.id, is_archived=False
    ).order_by(Entity.created_at.desc()).limit(100).all()

    return jsonify({"entities": [e.to_dict() for e in entities]})


@api_bp.route("/entities/<entity_type>", methods=["POST"])
@login_required
def api_create_entity(entity_type):
    definition = db.session.query(EntityDefinition).filter_by(
        tenant_id=g.tenant.id, type=entity_type, is_active=True
    ).first()
    if not definition:
        return jsonify({"error": f"Entity type '{entity_type}' not found"}), 404

    data = request.get_json(silent=True) or {}
    from app.models import next_entity_code
    code = next_entity_code(db.session, g.tenant.id, entity_type)

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
        detail="Created via API",
        governance_level="auto",
    )
    db.session.add(activity)
    db.session.commit()

    return jsonify({"success": True, "entity": entity.to_dict()}), 201


@api_bp.route("/entities/<entity_type>/<int:entity_id>", methods=["GET"])
@login_required
def api_get_entity(entity_type, entity_id):
    entity = db.session.query(Entity).filter_by(
        id=entity_id, tenant_id=g.tenant.id
    ).first()
    if not entity:
        return jsonify({"error": "Not found"}), 404
    return jsonify({"entity": entity.to_dict()})


@api_bp.route("/entities/<entity_type>/<int:entity_id>", methods=["PUT"])
@login_required
def api_update_entity(entity_type, entity_id):
    entity = db.session.query(Entity).filter_by(
        id=entity_id, tenant_id=g.tenant.id
    ).first()
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
    entity = db.session.query(Entity).filter_by(
        id=entity_id, tenant_id=g.tenant.id
    ).first()
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
# Real AI Query Engine  —  /api/agent/chat
# ---------------------------------------------------------------------------

@api_bp.route("/agent/query", methods=["POST"])
@login_required
def agent_query():
    """A real AI query endpoint that parses NL, queries entities + knowledge,
    and returns structured responses with verification badges.

    Accepts:
      {query: str, channel: str}

    Returns:
      {response: str, intent: str, verification_badge: str, ...}
    """
    data = request.get_json(silent=True) or {}
    query = (data.get("query") or "").strip()
    channel = (data.get("channel") or "app").strip()

    if not query:
        return jsonify({"error": "Query required"}), 400

    q = query.lower().strip()

    # --- Detect intent ---
    intent = _detect_chat_intent(q)

    # --- Handle by intent ---
    if intent == "create":
        # Redirect to entity form — return structured redirect
        entity_type = _extract_target_type(q, g.tenant.id)
        return jsonify({
            "response": f"I'll help you create a new {'record' if not entity_type else entity_type.replace('_', ' ')}. "
                        f"Click the button below to open the form.",
            "intent": "create",
            "verification_badge": "action",
            "redirect_url": f"/entities/{entity_type}/new" if entity_type else "/entities",
            "entity_type": entity_type,
            "channel": channel,
        })

    if intent in ("show", "list", "count"):
        entity_type = _extract_target_type(q, g.tenant.id)
        if entity_type:
            definition = db.session.query(EntityDefinition).filter_by(
                tenant_id=g.tenant.id, type=entity_type, is_active=True
            ).first()
            if definition:
                count = db.session.query(Entity).filter_by(
                    tenant_id=g.tenant.id, definition_id=definition.id,
                    is_archived=False
                ).count()
                entities = db.session.query(Entity).filter_by(
                    tenant_id=g.tenant.id, definition_id=definition.id,
                    is_archived=False
                ).order_by(Entity.created_at.desc()).limit(5).all()

                lines = []
                for e in entities:
                    label = e.display_name
                    status = f" [{e.status}]" if e.status and e.status != "new" else ""
                    lines.append(f"• **{label}**{status}")

                response = (f"I found **{count}** {definition.label_plural or definition.label}."
                           if count > 0 else f"No {definition.label_plural or definition.label} found.")
                if lines:
                    response += "\n\nRecent:\n" + "\n".join(lines)

                return jsonify({
                    "response": response,
                    "intent": intent,
                    "entity_type": entity_type,
                    "count": count,
                    "verification_badge": "data" if count > 0 else "empty",
                    "channel": channel,
                })

        # Count everything
        counts = _count_all_types(g.tenant.id)
        if counts:
            lines = [f"• {c['icon']} **{c['label']}**: {c['count']}" for c in counts[:10]]
            return jsonify({
                "response": "Here's a summary of your data:\n\n" + "\n".join(lines),
                "intent": "summary",
                "counts": counts,
                "verification_badge": "data",
                "channel": channel,
            })

    if intent == "search":
        # Search entities + knowledge
        entity_results = _search_all_entities(q, g.tenant.id)
        knowledge_results = _search_knowledge_base(q, g.tenant.id)

        parts = []
        if knowledge_results:
            parts.append("📚 **From Knowledge Base**")
            for k in knowledge_results[:3]:
                parts.append(f"• {k['question'][:100]}")
            parts.append("")

        if entity_results:
            parts.append(f"📋 **Records** ({len(entity_results)} found)")
            for e in entity_results[:5]:
                parts.append(f"• {e['display_name']} ({e['entity_type']})")
            parts.append("")

        if parts:
            return jsonify({
                "response": "\n".join(parts).strip(),
                "intent": "search",
                "entities_found": len(entity_results),
                "knowledge_found": len(knowledge_results),
                "verification_badge": "data" if entity_results or knowledge_results else "no_results",
                "channel": channel,
            })

        # Fallback to web search
        try:
            from app.shunya.web_search import search_web as _search_web
            web_results = _search_web(q, 3)
            if web_results:
                lines = [f"• [{r['title']}]({r.get('url', '#')})" for r in web_results]
                return jsonify({
                    "response": "I couldn't find that in your data. Here's what I found on the web:\n\n" + "\n".join(lines),
                    "intent": "web_search",
                    "web_results": web_results,
                    "verification_badge": "web",
                    "channel": channel,
                })
        except Exception:
            pass

        return jsonify({
            "response": "I searched your records but couldn't find a match. Try asking differently, "
                        "or upload a document on the **Ingest** page and I'll learn from it.",
            "intent": "no_match",
            "verification_badge": "no_results",
            "channel": channel,
        })

    # Default: search everything
    return jsonify({
        "response": "I'm ready to help. Try asking 'show me leads', 'how many tickets', "
                    "'search for something', or 'create a new lead'.",
        "intent": "greeting",
        "verification_badge": "info",
        "channel": channel,
    })


def _detect_chat_intent(q: str) -> str:
    """Detect the user's intent from natural language."""
    create_patterns = [
        r"^(?:create|add|new|make|register|record|track)\s",
        r"\b(?:create|add)\s+(?:a|an|the|new)\s",
    ]
    show_patterns = [
        r"^(?:show|list|get|find|display|view)\s",
        r"\bshow\s+me\b",
    ]
    count_patterns = [
        r"^(?:how many|count|total|number of)\s",
        r"\bhow many\b",
    ]
    search_patterns = [
        r"^(?:search|look)\s+(?:for|up)\s",
        r"\bsearch for\b",
        r"\blook for\b",
        r"\bfind\s+.+\b(?:in|about|regarding)\b",
    ]

    for pat in create_patterns:
        if re.search(pat, q):
            return "create"
    for pat in count_patterns:
        if re.search(pat, q):
            return "count"
    for pat in show_patterns:
        if re.search(pat, q):
            return "show"
    for pat in search_patterns:
        if re.search(pat, q):
            return "search"

    # Default: treat as search
    return "search"


def _extract_target_type(q: str, tenant_id: int):
    """Try to match a known entity type from the query."""
    definitions = db.session.query(EntityDefinition).filter_by(
        tenant_id=tenant_id, is_active=True
    ).all()

    for d in definitions:
        if d.type in q or d.label.lower() in q:
            return d.type

    # Check common keywords
    common_types = {
        "lead": "lead", "leads": "lead",
        "ticket": "ticket", "tickets": "ticket",
        "invoice": "invoice", "invoices": "invoice",
        "order": "order", "orders": "order",
        "booking": "booking", "bookings": "booking",
        "patient": "patient", "patients": "patient",
        "student": "student", "students": "student",
        "contact": "contact", "contacts": "contact",
        "deal": "deal", "deals": "deal",
        "opportunity": "opportunity", "opportunities": "opportunity",
        "project": "project", "projects": "project",
        "task": "task", "tasks": "task",
        "supplier": "supplier", "suppliers": "supplier",
    }
    for word in q.split():
        if word in common_types:
            return common_types[word]

    return None


def _search_all_entities(q: str, tenant_id: int) -> list:
    """Search across all entity types for matching records."""
    from sqlalchemy import or_
    results = []
    defs = db.session.query(EntityDefinition).filter_by(
        tenant_id=tenant_id, is_active=True
    ).all()

    for d in defs:
        searchable = d.searchable_fields or []
        if not searchable:
            searchable = [f.get("name", "") for f in (d.schema or []) if f.get("name")]

        filters = []
        for field_name in searchable:
            if field_name in ("name", "title", "description", "email", "phone", "notes", "address"):
                filters.append(
                    Entity.data[field_name].as_string().ilike(f"%{q}%")
                )

        if not filters:
            continue

        entities = db.session.query(Entity).filter(
            Entity.tenant_id == tenant_id,
            Entity.definition_id == d.id,
            Entity.is_archived == False,
            or_(*filters)
        ).order_by(Entity.created_at.desc()).limit(5).all()

        for e in entities:
            results.append({
                "id": e.id,
                "code": e.code,
                "display_name": e.display_name,
                "entity_type": d.label,
                "status": e.status,
            })

    return results[:10]


def _search_knowledge_base(q: str, tenant_id: int) -> list:
    """Search knowledge entries by question/answer."""
    entries = db.session.query(KnowledgeEntry).filter(
        KnowledgeEntry.tenant_id == tenant_id,
        db.or_(
            KnowledgeEntry.question.ilike(f"%{q}%"),
            KnowledgeEntry.answer.ilike(f"%{q}%"),
        )
    ).order_by(KnowledgeEntry.use_count.desc()).limit(5).all()

    return [{
        "id": e.id,
        "question": e.question,
        "answer": e.answer[:300],
        "source": e.source,
    } for e in entries]


def _count_all_types(tenant_id: int) -> list:
    """Return counts for all active entity types."""
    counts = []
    defs = db.session.query(EntityDefinition).filter_by(
        tenant_id=tenant_id, is_active=True
    ).all()
    for d in defs:
        count = db.session.query(Entity).filter_by(
            tenant_id=tenant_id, definition_id=d.id, is_archived=False
        ).count()
        if count > 0:
            counts.append({
                "type": d.type,
                "label": d.label_plural or d.label,
                "icon": d.icon or "📋",
                "count": count,
            })
    counts.sort(key=lambda x: x["count"], reverse=True)
    return counts


# ---------------------------------------------------------------------------
# Legacy AI Query API (kept for backward compatibility)
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

    context = KnowledgePipeline.get_context_for_ai(query, g.tenant.id)

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
        response_parts.append(
            "I searched your company data and the web but couldn't find a clear answer. "
            "Could you tell me more about what you're looking for? "
            "If you have a document with this information, upload it on the **Ingest** page and I'll learn from it."
        )

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
# AI Action Endpoints (intent detection + execution)
# ---------------------------------------------------------------------------

@api_bp.route("/ai/action", methods=["POST"])
@login_required
def ai_action():
    """Parse intent from natural language and execute or return confirmation card."""
    data = request.get_json(silent=True) or {}
    query = data.get("query", "").strip()
    confirmed = data.get("confirmed", False)
    intent_data = data.get("intent_data")

    if not query:
        return jsonify({"error": "Query required"}), 400

    if confirmed and intent_data:
        return _execute_intent(intent_data, g.tenant.id, g.user.id, g.user.name)

    intent = _detect_intent(query, g.tenant.id)

    if intent["type"] == "question":
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


# ---------------------------------------------------------------------------
# Legacy Intent helpers (kept for backward compat)
# ---------------------------------------------------------------------------

def _detect_intent(query: str, tenant_id: int) -> dict:
    """Detect whether a query is an action or a question, parse it."""
    q = query.lower().strip()

    create_patterns = [r"^(?:create|add|new|make|register|record|track)\s+(?:a\s+|an\s+|the\s+)?(.+)"]
    search_patterns = [r"^(?:search|find|look\s*up|google|web)\s+(.+)"]
    show_patterns = [r"^(?:show|list|get|find|display|view)\s+(?:me\s+)?(.+)"]
    update_patterns = [r"^(?:update|change|edit|modify|set)\s+(?:the\s+)?(.+)"]

    for pat in create_patterns:
        m = re.search(pat, q)
        if m:
            rest = m.group(1).strip()
            return _parse_create_intent(rest, query, tenant_id)

    for pat in show_patterns:
        m = re.search(pat, q)
        if m:
            rest = m.group(1).strip()
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
                    },
                }

    for pat in search_patterns:
        m = re.search(pat, q)
        if m:
            search_term = m.group(1).strip()
            return {
                "type": "question",
                "hint": "web_search",
                "query": search_term,
            }

    return {"type": "question"}


def _parse_create_intent(rest: str, full_query: str, tenant_id: int) -> dict:
    """Parse a 'create X for...' intent into structured data."""
    from app.conversational import ConversationalEngine
    from app.models import next_entity_code

    q = full_query
    entity_type = _extract_entity_type_from_query(q, tenant_id)

    if not entity_type:
        first_word = rest.split()[0].rstrip("s")
        definition = db.session.query(EntityDefinition).filter(
            EntityDefinition.tenant_id == tenant_id,
            EntityDefinition.is_active == True,
            EntityDefinition.type.ilike(first_word)
        ).first()
        if not definition:
            definitions = db.session.query(EntityDefinition).filter_by(
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
                "message": "I'm not sure what to create. Try 'create a lead for...' or check your entity types in Settings.",
            }

    definition = db.session.query(EntityDefinition).filter_by(
        tenant_id=tenant_id, type=entity_type
    ).first()

    parsed = ConversationalEngine.parse_and_fill(full_query, entity_type, tenant_id)

    if "error" in parsed:
        return {"type": "question", "hint": "error", "message": parsed["error"]}

    code = next_entity_code(db.session, tenant_id, entity_type)

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
    from app.models import next_entity_code

    intent_type = intent_data.get("type")

    if intent_type == "create":
        entity_type = intent_data.get("entity_type")
        parsed_data = intent_data.get("parsed_data", {})
        status = intent_data.get("suggested_status", "new")
        code = intent_data.get("code")

        definition = db.session.query(EntityDefinition).filter_by(
            tenant_id=tenant_id, type=entity_type
        ).first()
        if not definition:
            return {"success": False, "error": f"Entity type '{entity_type}' not found"}

        if not code:
            code = next_entity_code(db.session, tenant_id, entity_type)

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
    definitions = db.session.query(EntityDefinition).filter_by(
        tenant_id=tenant_id, is_active=True
    ).all()
    text_lower = text.lower().rstrip("s")
    for d in definitions:
        if d.type in text_lower or d.label.lower() in text_lower:
            return d.type
    return None


def _extract_entity_type_from_query(query: str, tenant_id: int) -> str:
    """Extract the entity type from a query string."""
    definitions = db.session.query(EntityDefinition).filter_by(
        tenant_id=tenant_id, is_active=True
    ).all()
    q = query.lower()

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
        return (
            "I searched your company data but couldn't find a clear answer. "
            "Try asking differently, or upload a document on the **Ingest** page "
            "and I'll learn from it."
        )

    return "\n\n".join(parts[:3])


# ---------------------------------------------------------------------------
# Webhook Receiver
# ---------------------------------------------------------------------------

@api_bp.route("/webhook/<integration>", methods=["POST"])
def webhook_receiver(integration):
    """Generic webhook receiver for external integrations."""
    payload = request.get_json(silent=True) or {}
    return jsonify({"success": True, "integration": integration})


# ---------------------------------------------------------------------------
# Global Search (Cmd+K)
# ---------------------------------------------------------------------------

@api_bp.route("/search", methods=["GET"])
@login_required
def global_search():
    """Search across all data sources — entities, knowledge, customer memory."""
    q = request.args.get("q", "").strip()
    if not q or len(q) < 2:
        return jsonify({"results": []})

    from app.shunya.command_palette import CommandPalette
    results = CommandPalette.search(q, g.tenant.id, g.user.id, g.user.role)
    return jsonify({"results": results, "query": q})


# ---------------------------------------------------------------------------
# Data Export
# ---------------------------------------------------------------------------

@api_bp.route("/export", methods=["GET"])
@login_required
def export_data():
    """Export entities for a tenant, optionally filtered by type."""
    import json

    entity_type = request.args.get("type")
    export = {}

    definitions = db.session.query(EntityDefinition).filter_by(
        tenant_id=g.tenant.id
    ).all()
    for d in definitions:
        if entity_type and d.type != entity_type:
            continue
        entities = db.session.query(Entity).filter_by(
            tenant_id=g.tenant.id, definition_id=d.id, is_archived=False
        ).all()
        export[d.type] = {
            "definition": d.to_dict(),
            "entities": [e.to_dict() for e in entities],
        }

    return jsonify({
        "export": export,
        "exported_at": datetime.utcnow().isoformat(),
    })


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

    result = LearningEngine.review_proposal(
        proposal_id, g.tenant.id, g.user.id, decision, feedback
    )
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