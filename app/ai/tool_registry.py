"""Tool Registry — wires real business actions into the Intelligence Runtime's ToolExecutionLayer.

Each handler: validates input → calls service → persists outcome → emits event → returns result.
"""
from __future__ import annotations

import uuid
import logging
from typing import Any

from app import db
from app.customers.models import Customer
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
    """Create a customer from AI action parameters.

    Expected params:
        name (str): Customer name (required)
        email (str): Email address
        phone (str): Phone number
        tenant_id (int, optional): Tenant/organisation ID
    """
    identity_id = params.get("identity_id", params.get("_identity_id", "ai_runtime"))
    tenant_id = params.get("tenant_id")

    name = (params.get("name") or "").strip()
    if not name:
        return {"error": "Customer name is required", "status": "error"}

    customer = Customer(
        name=name,
        phone=(params.get("phone") or "").strip(),
        email=(params.get("email") or "").strip(),
        tenant_id=tenant_id,
        status=params.get("status", "active"),
    )
    db.session.add(customer)
    db.session.commit()

    result = {
        "action": "create_customer",
        "customer_id": customer.id,
        "name": customer.name,
        "email": customer.email,
    }

    outcome = _persist_outcome(
        identity_id=identity_id,
        intention=f"Create customer: {name}",
        state={
            "action": "create_customer",
            "customer_id": customer.id,
            "name": name,
        },
    )

    _emit_action_event(
        "create_customer", result, outcome.outcome_id, identity_id, tenant_id
    )

    return {
        "status": "success",
        "result": result,
        "outcome_id": outcome.outcome_id,
    }


def _handle_create_supplier(params: dict) -> dict:
    """Create a supplier from AI action parameters.

    Expected params:
        name (str): Supplier name (required)
        category (str): Supplier category
        contact (str): Contact person
        email (str): Email address
        phone (str): Phone number
        city (str): City
        tenant_id (int, optional): Tenant/organisation ID
    """
    identity_id = params.get("identity_id", params.get("_identity_id", "ai_runtime"))
    tenant_id = params.get("tenant_id")

    name = (params.get("name") or "").strip()
    if not name:
        return {"error": "Supplier name is required", "status": "error"}

    supplier = Supplier(
        name=name,
        category=(params.get("category") or "").strip(),
        contact=(params.get("contact") or "").strip(),
        email=(params.get("email") or "").strip(),
        phone=(params.get("phone") or "").strip(),
        city=(params.get("city") or "").strip(),
        tenant_id=tenant_id,
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
        "create_supplier", result, outcome.outcome_id, identity_id, tenant_id
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