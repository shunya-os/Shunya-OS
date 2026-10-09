"""Tool Registry — wires real business actions into the Intelligence Runtime's ToolExecutionLayer.

Each handler: validates input → calls service → persists outcome → emits event → returns result.
"""
from __future__ import annotations

import uuid
import logging
from typing import Any

from app import db
from app.models import Supplier
from app.objects.models import Object
from app.execution.models import Outcome
from app.shunya.infrastructure.event_bus import CanonicalEvent, get_event_bus

logger = logging.getLogger(__name__)


def _generate_outcome_id() -> str:
    """Generate a short, unique outcome ID."""
    return uuid.uuid4().hex[:12].upper()


def register_tool_handlers() -> None:
    """Register all business action handlers on the Intelligence Runtime singleton."""
    from core.intelligence_runtime import get_runtime

    runtime = get_runtime()

    runtime.wire_action("create_customer", _handle_create_customer)
    runtime.wire_action("create_supplier", _handle_create_supplier)
    runtime.wire_action("search_objects", _handle_search_objects)

    logger.info(
        "Registered AI tool handlers: create_customer, create_supplier, search_objects"
    )


# ── Helpers ───────────────────────────────────────────────────────────────


def _persist_outcome(
    identity_id: str, intention: str, state: dict
) -> Outcome:
    """Create and persist an Outcome record."""
    outcome = Outcome(
        outcome_id=_generate_outcome_id(),
        identity_id=identity_id or "system",
        intention=intention,
        state=state,
    )
    db.session.add(outcome)
    db.session.commit()
    return outcome


def _emit_action_event(
    action: str,
    result: dict,
    outcome_id: str,
    identity_id: str = "",
    tenant_id: int | None = None,
) -> None:
    """Emit an event on the event bus for the executed action."""
    bus = get_event_bus()
    event = CanonicalEvent(
        event_type=f"ai.action.{action}",
        actor_id=identity_id or "system",
        actor_type="ai_runtime",
        object_id=outcome_id,
        object_type="outcome",
        tenant_id=tenant_id,
        payload={
            "action": action,
            "outcome_id": outcome_id,
            "result": result,
        },
    )
    bus.publish(event)
    logger.debug("Emitted event: %s for outcome %s", event.event_type, outcome_id)


# ── Handlers ──────────────────────────────────────────────────────────────


def _handle_create_customer(params: dict) -> dict:
    """Create a customer as a canonical relationship.

    The legacy ``customer`` table (app.customers.models.Customer) is
    vestigial: production carries zero rows and no product surface reads it —
    the customer store is ``rel_relationships`` (CanonicalRelationship,
    organization-scoped). Writing anywhere else would create a customer that
    never appears in the product. Duplicate name in the org: return the
    existing record truthfully, create nothing.
    """
    identity_id = params.get("identity_id", params.get("_identity_id", "ai_runtime"))
    org_id = params.get("organization_id") or params.get("tenant_id")

    name = (params.get("name") or "").strip()
    if not name:
        return {"error": "Customer name is required", "status": "error"}

    try:
        org_id = int(org_id) if org_id not in (None, "") else None
    except (TypeError, ValueError):
        org_id = None
    if not org_id:
        return {"error": "An organization context is required to create a customer", "status": "error"}

    from app.relationship.models import CanonicalRelationship

    existing = (
        CanonicalRelationship.query.filter(
            CanonicalRelationship.organization_id == org_id,
            db.func.lower(CanonicalRelationship.display_name) == name.lower(),
            CanonicalRelationship.status != "archived",
        ).first()
    )
    if existing is not None:
        return {
            "status": "duplicate",
            "result": {
                "action": "create_customer",
                "customer_id": existing.id,
                "name": existing.display_name,
                "note": "a customer with this name already exists",
            },
            "outcome_id": None,
        }

    rel = CanonicalRelationship(
        organization_id=org_id,
        display_name=name,
        relationship_type="customer",
        email=(params.get("email") or "").strip(),
        phone=(params.get("phone") or "").strip(),
        source="ai_chat",
        created_by=identity_id or "",
        status=params.get("status", "active"),
    )
    db.session.add(rel)
    db.session.commit()

    result = {
        "action": "create_customer",
        "customer_id": rel.id,
        "name": rel.display_name,
        "email": rel.email,
    }

    outcome = _persist_outcome(
        identity_id=identity_id,
        intention=f"Create customer: {name}",
        state={
            "action": "create_customer",
            "customer_id": rel.id,
            "relationship_id": rel.id,
            "name": name,
        },
    )

    _emit_action_event(
        "create_customer", result, outcome.outcome_id, identity_id, org_id
    )

    return {
        "status": "success",
        "result": result,
        "outcome_id": outcome.outcome_id,
    }


def _handle_create_supplier(params: dict) -> dict:
    """Create a supplier in the organization's supplier store.

    ``suppliers`` IS the product's supplier store (its tenancy FK was
    retargeted to organizations in M6). Duplicate name in the org: return the
    existing record truthfully, create nothing.
    """
    identity_id = params.get("identity_id", params.get("_identity_id", "ai_runtime"))
    org_id = params.get("organization_id") or params.get("tenant_id")

    name = (params.get("name") or "").strip()
    if not name:
        return {"error": "Supplier name is required", "status": "error"}

    try:
        org_id = int(org_id) if org_id not in (None, "") else None
    except (TypeError, ValueError):
        org_id = None
    if not org_id:
        return {"error": "An organization context is required to create a supplier", "status": "error"}

    existing = (
        Supplier.query.filter(
            Supplier.tenant_id == org_id,
            db.func.lower(Supplier.name) == name.lower(),
        ).first()
    )
    if existing is not None:
        return {
            "status": "duplicate",
            "result": {
                "action": "create_supplier",
                "supplier_id": existing.id,
                "name": existing.name,
                "note": "a supplier with this name already exists",
            },
            "outcome_id": None,
        }

    supplier = Supplier(
        name=name,
        category=(params.get("category") or "").strip(),
        contact=(params.get("contact") or "").strip(),
        email=(params.get("email") or "").strip(),
        phone=(params.get("phone") or "").strip(),
        city=(params.get("city") or "").strip(),
        tenant_id=org_id,
        status=params.get("status", "active"),
    )
    db.session.add(supplier)
    db.session.commit()

    result = {
        "action": "create_supplier",
        "supplier_id": supplier.id,
        "name": supplier.name,
        "category": supplier.category,
    }

    outcome = _persist_outcome(
        identity_id=identity_id,
        intention=f"Create supplier: {name}",
        state={
            "action": "create_supplier",
            "supplier_id": supplier.id,
            "name": name,
        },
    )

    _emit_action_event(
        "create_supplier", result, outcome.outcome_id, identity_id, org_id
    )

    return {
        "status": "success",
        "result": result,
        "outcome_id": outcome.outcome_id,
    }


def _handle_search_objects(params: dict) -> dict:
    """Search objects across the system.

    Expected params:
        query (str): Search text
        object_type (str, optional): Filter by object type
        tenant_id (int, optional): Tenant/organisation ID
    """
    identity_id = params.get("identity_id", params.get("_identity_id", "ai_runtime"))
    tenant_id = params.get("tenant_id")

    query = (params.get("query") or "").strip()
    object_type = params.get("object_type", "")

    if not query and not object_type:
        return {
            "error": "Search query or object_type is required",
            "status": "error",
        }

    q = Object.query
    if object_type:
        q = q.filter(Object.type == object_type)
    if tenant_id:
        q = q.filter(Object.tenant_id == tenant_id)
    if query:
        like = f"%{query}%"
        q = q.filter(Object.state.cast(db.String).ilike(like))

    objects = q.order_by(Object.created_at.desc()).limit(20).all()

    result = {
        "action": "search_objects",
        "object_type": object_type or "any",
        "query": query,
        "count": len(objects),
        "results": [
            {"id": o.id, "type": o.type, "state": o.state} for o in objects
        ],
    }

    outcome = _persist_outcome(
        identity_id=identity_id,
        intention=f"Search objects: {query or object_type}",
        state={"action": "search_objects", "count": len(objects)},
    )

    _emit_action_event(
        "search_objects", result, outcome.outcome_id, identity_id, tenant_id
    )

    return {
        "status": "success",
        "result": result,
        "outcome_id": outcome.outcome_id,
    }