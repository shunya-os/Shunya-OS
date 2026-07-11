"""Shunya Personal Agent — Tool Registry, SafeTool, and all tools.

Every capability the agent has is registered as a Tool with a schema.
The agent introspects the registry to know what it can do.
"""
from __future__ import annotations
from typing import Any, Callable, Optional
from dataclasses import dataclass, field
from enum import Enum
from flask import g


class ToolGovernance(str, Enum):
    AUTO = "auto"      # Executes immediately
    DRAFT = "draft"    # Needs user confirmation
    GOVERN = "govern"  # Needs admin approval


@dataclass
class ToolParam:
    name: str
    type: str          # string, number, boolean, array, object
    description: str
    required: bool = False
    enum: list[str] | None = None


@dataclass
class ToolSpec:
    name: str
    description: str   # LLM reads this to decide when to use
    parameters: list[ToolParam]
    governance: ToolGovernance = ToolGovernance.AUTO
    auth_required: str = "any"  # any, admin, manager
    handler: Callable = lambda **kw: {"result": "not implemented"}


@dataclass
class ToolResult:
    success: bool
    data: Any = None
    error: str = ""
    message: str = ""          # User-facing message
    suggested_fix: dict | None = None  # What the agent can try next


class SafeTool:
    """Wraps every tool with graceful fallback chains."""

    def __init__(self, spec: ToolSpec):
        self.spec = spec

    def execute(self, params: dict, user_role: str = "agent") -> ToolResult:
        try:
            if not self._check_auth(user_role):
                return ToolResult(
                    success=False,
                    message="This action needs higher permissions. I've noted what you wanted.",
                    suggested_fix={"action": "queue_for_approval", "tool": self.spec.name, "params": params},
                )
            result = self.spec.handler(**params)
            return ToolResult(success=True, data=result, message="")
        except MissingParamError as e:
            return ToolResult(
                success=False,
                message=f"I need the {e.param} to continue.",
                suggested_fix={"action": "ask_user", "question": f"Please provide the {e.param}."},
            )
        except AuthError:
            return ToolResult(
                success=False,
                message="This needs admin approval. I've queued it for review.",
                suggested_fix={"action": "queue_for_approval", "tool": self.spec.name, "params": params},
            )
        except DataError as e:
            return ToolResult(
                success=False,
                message=f"I found the data but it has an issue: {e}",
                suggested_fix={"action": "offer_alternative", "reason": str(e)},
            )
        except Exception as e:
            return ToolResult(
                success=False,
                message="I hit an unexpected issue. Let me try a different approach.",
                suggested_fix={"action": "retry_different", "error": str(e)},
            )

    def _check_auth(self, role: str) -> bool:
        if self.spec.auth_required == "any":
            return True
        if self.spec.auth_required == "admin" and role != "admin":
            return False
        if self.spec.auth_required == "manager" and role not in ("admin", "manager"):
            return False
        return True


class MissingParamError(Exception):
    def __init__(self, param: str):
        self.param = param
        super().__init__(f"Missing param: {param}")


class AuthError(Exception):
    pass


class DataError(Exception):
    pass


# ---------------------------------------------------------------------------
# Tool Handlers — actual implementations
# ---------------------------------------------------------------------------

def _create_entity(entity_type: str = "", **kwargs) -> dict:
    """Create a record of the given type."""
    from app import db
    from app.models import Entity, EntityDefinition, ActivityLog, next_entity_code

    if not entity_type:
        raise MissingParamError("entity_type")

    tenant_id = g.tenant.id
    user_id = g.user.id

    definition = EntityDefinition.query.filter_by(tenant_id=tenant_id, type=entity_type).first()
    if not definition:
        raise DataError(f"No entity type '{entity_type}'. Create one in Modules or Settings.")

    code = next_entity_code(db.session, tenant_id, g.tenant.theme_config.get("code_prefix", "PC"))
    
    # Only keep fields that exist in the schema
    schema_names = {f["name"] for f in definition.schema}
    entity_data = {k: v for k, v in kwargs.items() if k in schema_names}

    entity = Entity(
        tenant_id=tenant_id,
        definition_id=definition.id,
        code=code,
        status=kwargs.get("status", definition.statuses[0] if definition.statuses else "new"),
        data=entity_data,
        created_by=user_id,
    )
    db.session.add(entity)
    db.session.flush()

    activity = ActivityLog(
        tenant_id=tenant_id, entity_id=entity.id, user_id=user_id,
        action="created", detail=f"Created via Personal Agent: {definition.label} ({code})",
        governance_level="auto",
    )
    db.session.add(activity)
    db.session.commit()

    return {
        "id": entity.id, "code": code, "type": entity_type, "label": definition.label,
        "icon": definition.icon, "target": f"/entities/{entity_type}/{entity.id}",
    }


def _search_knowledge(query: str = "") -> dict:
    """Search the company knowledge base."""
    from app.shunya.knowledge import KnowledgePipeline
    if not query:
        raise MissingParamError("query")
    result = KnowledgePipeline.search(query, g.tenant.id, g.user.id)
    return {
        "results": result.get("results", []),
        "count": len(result.get("results", [])),
        "has_data": result.get("has_internal_data", False),
    }


def _search_web(query: str = "", depth: str = "normal") -> dict:
    """Search the internet."""
    from app.shunya.web_search import web_search
    if not query:
        raise MissingParamError("query")
    results = web_search(query, limit=5)
    return {"results": results, "count": len(results) if results else 0}


def _list_entities(entity_type: str = "", status: str = "", limit: int = 20) -> dict:
    """List records of a given type, optionally filtered by status."""
    from app.models import Entity, EntityDefinition
    tenant_id = g.tenant.id
    
    query = Entity.query.filter_by(tenant_id=tenant_id, is_archived=False)
    
    if entity_type:
        definition = EntityDefinition.query.filter_by(tenant_id=tenant_id, type=entity_type).first()
        if not definition:
            raise DataError(f"No entity type '{entity_type}'.")
        query = query.filter(Entity.definition_id == definition.id)
    
    if status:
        query = query.filter(Entity.status == status)
    
    entities = query.order_by(Entity.created_at.desc()).limit(limit).all()
    return {
        "count": len(entities),
        "entities": [{"id": e.id, "code": e.code, "status": e.status, "data": e.data,
                       "display": e.display_name} for e in entities],
    }


def _get_entity(entity_type: str = "", entity_id: int = 0) -> dict:
    """Get a single record by type and ID."""
    from app.models import Entity, EntityDefinition
    definition = EntityDefinition.query.filter_by(tenant_id=g.tenant.id, type=entity_type).first()
    if not definition:
        raise DataError(f"No entity type '{entity_type}'.")
    entity = Entity.query.filter_by(id=entity_id, tenant_id=g.tenant.id, definition_id=definition.id).first()
    if not entity:
        raise DataError(f"No {entity_type} with ID {entity_id}.")
    return {"id": entity.id, "code": entity.code, "status": entity.status,
            "data": entity.data, "display": entity.display_name}


def _update_entity(entity_type: str = "", entity_id: int = 0, **fields) -> dict:
    """Update fields on an existing record."""
    from app import db
    from app.models import Entity, EntityDefinition, ActivityLog
    definition = EntityDefinition.query.filter_by(tenant_id=g.tenant.id, type=entity_type).first()
    if not definition:
        raise DataError(f"No entity type '{entity_type}'.")
    entity = Entity.query.filter_by(id=entity_id, tenant_id=g.tenant.id, definition_id=definition.id).first()
    if not entity:
        raise DataError(f"No {entity_type} with ID {entity_id}.")
    
    changes = []
    for key, val in fields.items():
        if key in ("entity_type", "entity_id"):
            continue
        entity.data[key] = val
        changes.append(f"{key}={val}")
    
    if changes:
        activity = ActivityLog(
            tenant_id=g.tenant.id, entity_id=entity.id, user_id=g.user.id,
            action="updated", detail=f"Updated via Personal Agent: {'; '.join(changes[:5])}",
        )
        db.session.add(activity)
    db.session.commit()
    return {"id": entity.id, "code": entity.code, "updated_fields": changes}


def _send_message(channel: str = "", recipient: str = "", message: str = "") -> dict:
    """Send a message via WhatsApp, Telegram, or internal."""
    from app import db
    from app.models import ActivityLog
    if not recipient or not message:
        raise MissingParamError("recipient and message required")
    activity = ActivityLog(
        tenant_id=g.tenant.id, user_id=g.user.id,
        action=f"message_{channel}", detail=f"To {recipient}: {message[:200]}",
    )
    db.session.add(activity)
    db.session.commit()
    return {"channel": channel, "recipient": recipient, "status": "queued"}


def _run_report(report_type: str = "", **filters) -> dict:
    """Generate a business report (finance, operations, analytics)."""
    from app.shunya.analytics import AnalyticsEngine
    if report_type == "finance":
        data = AnalyticsEngine.get_overview(g.tenant.id)
    elif report_type == "insights":
        data = AnalyticsEngine.get_founder_insights(g.tenant.id)
    else:
        data = AnalyticsEngine.get_overview(g.tenant.id)
    return {"report_type": report_type, "data": data}


# ---------------------------------------------------------------------------
# Tool Registry
# ---------------------------------------------------------------------------

TOOL_DEFINITIONS: list[ToolSpec] = [
    ToolSpec(
        name="create_entity",
        description="Create a new record of any type (lead, patient, order, task, etc.). "
                    "The user provides the entity type and field values in natural language.",
        parameters=[
            ToolParam("entity_type", "string", "The type of record to create (lead, patient, order, etc.)", True),
            ToolParam("status", "string", "Initial status for the record", False),
        ],
        governance=ToolGovernance.AUTO,
        handler=_create_entity,
    ),
    ToolSpec(
        name="search_knowledge",
        description="Search the company's internal knowledge base for answers. "
                    "Use this for questions about company policies, procedures, past decisions, or any internal data.",
        parameters=[
            ToolParam("query", "string", "The search query", True),
        ],
        governance=ToolGovernance.AUTO,
        handler=_search_knowledge,
    ),
    ToolSpec(
        name="search_web",
        description="Search the internet for current information. "
                    "Use this for factual queries, research, comparisons, news, or anything not in company data.",
        parameters=[
            ToolParam("query", "string", "The web search query", True),
            ToolParam("depth", "string", "Search depth: quick, normal, deep", False),
        ],
        governance=ToolGovernance.AUTO,
        handler=_search_web,
    ),
    ToolSpec(
        name="list_entities",
        description="List records of a given type. Optionally filter by status. "
                    "Use this when the user wants to see their leads, patients, orders, etc.",
        parameters=[
            ToolParam("entity_type", "string", "Type of records to list", False),
            ToolParam("status", "string", "Filter by status", False),
            ToolParam("limit", "number", "Max records to return (default 20)", False),
        ],
        governance=ToolGovernance.AUTO,
        handler=_list_entities,
    ),
    ToolSpec(
        name="get_entity",
        description="Get details of a single record by its type and ID.",
        parameters=[
            ToolParam("entity_type", "string", "Type of record", True),
            ToolParam("entity_id", "number", "Record ID", True),
        ],
        governance=ToolGovernance.AUTO,
        handler=_get_entity,
    ),
    ToolSpec(
        name="update_entity",
        description="Update one or more fields on an existing record.",
        parameters=[
            ToolParam("entity_type", "string", "Type of record to update", True),
            ToolParam("entity_id", "number", "Record ID to update", True),
        ],
        governance=ToolGovernance.DRAFT,
        handler=_update_entity,
    ),
    ToolSpec(
        name="send_message",
        description="Send a message to a client, team member, or channel via WhatsApp, Telegram, or internal.",
        parameters=[
            ToolParam("channel", "string", "Channel: whatsapp, telegram, internal", True),
            ToolParam("recipient", "string", "Recipient name, phone, or handle", True),
            ToolParam("message", "string", "Message content", True),
        ],
        governance=ToolGovernance.GOVERN,
        auth_required="manager",
        handler=_send_message,
    ),
    ToolSpec(
        name="run_report",
        description="Generate business reports: finance overview, founder insights, analytics.",
        parameters=[
            ToolParam("report_type", "string", "Report type: finance, insights, overview", False),
        ],
        governance=ToolGovernance.AUTO,
        auth_required="admin",
        handler=_run_report,
    ),
]


class ToolRegistry:
    """Registry of all tools the agent can use. The agent introspects this."""

    def __init__(self):
        self._tools: dict[str, SafeTool] = {}
        for spec in TOOL_DEFINITIONS:
            self._tools[spec.name] = SafeTool(spec)

    def get(self, name: str) -> SafeTool | None:
        return self._tools.get(name)

    def list_tools(self) -> list[dict]:
        """Return tool manifest for LLM introspection."""
        return [{
            "name": spec.name,
            "description": spec.description,
            "parameters": [{"name": p.name, "type": p.type, "description": p.description, "required": p.required,
                            "enum": p.enum} for p in spec.parameters],
            "governance": spec.governance.value,
        } for spec in TOOL_DEFINITIONS]

    def find_tools(self, intent: str, keywords: list[str]) -> list[str]:
        """Find the best tools for a given intent and query keywords."""
        q = " ".join(keywords).lower()
        scored = []
        for spec in TOOL_DEFINITIONS:
            score = 0
            desc = spec.description.lower()
            name = spec.name.lower()
            for kw in keywords:
                if kw.lower() in desc:
                    score += 2
                if kw.lower() in name:
                    score += 1
            if intent == "create" and "create" in name:
                score += 5
            if intent == "search" and "search" in name:
                score += 5
            if intent == "list" and "list" in name:
                score += 5
            if intent == "update" and "update" in name:
                score += 5
            scored.append((score, spec.name))
        scored.sort(reverse=True)
        return [name for score, name in scored if score > 0]


_default_registry: ToolRegistry | None = None


def get_registry() -> ToolRegistry:
    global _default_registry
    if _default_registry is None:
        _default_registry = ToolRegistry()
    return _default_registry