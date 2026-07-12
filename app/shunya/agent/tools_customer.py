"""Bird AI — Customer & Communication Tools (14 tools).

Registered via register_tool() into the Bird Agent ToolRegistry.
Each tool handler receives (params: dict, agent: Agent) and returns ToolResult.
Uses flask.g for tenant/user context and app.models for data access.
"""

import json
import logging
import re
from datetime import datetime, timedelta
from flask import g

from app.shunya.agent import (
    register_tool,
    ToolDef,
    ToolResult,
    ToolCategory,
    ToolPermission,
)

logger = logging.getLogger("shunya.tools.customer")

# ---------------------------------------------------------------------------
# Helper utilities
# ---------------------------------------------------------------------------


def _get_tenant_id() -> int:
    """Get the current tenant ID from Flask g."""
    tenant = getattr(g, "tenant", None)
    if tenant:
        return tenant.id
    # Fallback for agent context
    agent = getattr(g, "agent", None)
    if agent:
        return agent.tenant_id
    return 0


def _get_user_id() -> int:
    """Get the current user ID from Flask g."""
    user = getattr(g, "user", None)
    if user:
        return user.id
    agent = getattr(g, "agent", None)
    if agent:
        return agent.user_id
    return 0


def _get_user_role() -> str:
    """Get the current user role."""
    user = getattr(g, "user", None)
    if user:
        return getattr(user, "role", "agent")
    agent = getattr(g, "agent", None)
    if agent:
        return getattr(agent, "user_role", "agent")
    return "agent"


def _find_entity_def(tenant_id: int, entity_type: str):
    """Find EntityDefinition by type for this tenant."""
    from app.models import EntityDefinition
    return EntityDefinition.query.filter_by(
        tenant_id=tenant_id, type=entity_type
    ).first()


def _log_activity(tenant_id: int, entity_id: int, user_id: int,
                  action: str, detail: str = "", metadata: dict = None):
    """Create an activity log entry."""
    from app import db
    from app.models import ActivityLog
    activity = ActivityLog(
        tenant_id=tenant_id,
        entity_id=entity_id,
        user_id=user_id,
        action=action,
        detail=detail,
        metadata_json=metadata or {},
        governance_level="auto",
    )
    db.session.add(activity)
    db.session.commit()


# ---------------------------------------------------------------------------
# 1. find_customer — Search customers by name, phone, email, passport
# ---------------------------------------------------------------------------

def _find_customer(params: dict, agent=None) -> ToolResult:
    """Search customers by name, phone, email, or passport.

    Searches both 'lead' Entity records and 'customer' Entity records,
    plus Person and Relationship tables for richer identity matching.
    """
    from app import db
    from app.models import Entity, EntityDefinition, Person, Relationship

    tenant_id = _get_tenant_id()
    user_id = _get_user_id()

    query = (params.get("query") or params.get("q") or
             params.get("name") or params.get("phone") or
             params.get("email") or params.get("passport") or "").strip()

    if not query:
        return ToolResult(
            success=False,
            message="Please provide a name, phone, email, or passport number to search.",
            error="missing_query",
        )

    results = []
    seen_ids = set()

    # 1. Search Person table (canonical identity)
    person_filters = []
    if re.match(r'^[\w\.\+\-]+@[\w\-]+\.[\w\.\-]+$', query):
        person_filters.append(Person.email.ilike(f"%{query}%"))
    if re.match(r'^\+?\d{7,15}$', query.replace(" ", "").replace("-", "")):
        clean = query.replace(" ", "").replace("-", "")
        person_filters.append(Person.phone.ilike(f"%{clean}"))
    if len(query) >= 3 and query.isupper():
        person_filters.append(Person.passport.ilike(f"%{query}%"))
    # Always search by name
    person_filters.append(Person.name.ilike(f"%{query}%"))

    persons = Person.query.filter(
        db.or_(*person_filters)
    ).limit(20).all()

    for p in persons:
        seen_ids.add(f"person_{p.id}")
        results.append({
            "type": "person",
            "id": p.id,
            "name": p.name,
            "email": p.email or "",
            "phone": p.phone or "",
            "passport": p.passport or "",
            "tags": p.tags or [],
        })

    # 2. Search Relationship table
    rel_filters = []
    rel_filters.append(Relationship.tenant_id == tenant_id)
    if re.match(r'^[\w\.\+\-]+@[\w\-]+\.[\w\.\-]+$', query):
        rel_filters.append(Relationship.email.ilike(f"%{query}%"))
    if re.match(r'^\+?\d{7,15}$', query.replace(" ", "").replace("-", "")):
        clean = query.replace(" ", "").replace("-", "")
        rel_filters.append(Relationship.phone.ilike(f"%{clean}"))
    rel_filters.append(Relationship.display_name.ilike(f"%{query}%"))

    rels = Relationship.query.filter(db.or_(
        Relationship.display_name.ilike(f"%{query}%"),
        Relationship.email.ilike(f"%{query}%"),
        Relationship.phone.ilike(f"%{query}%"),
    ), Relationship.tenant_id == tenant_id).limit(20).all()

    for r in rels:
        key = f"rel_{r.id}"
        if key not in seen_ids:
            seen_ids.add(key)
            results.append({
                "type": "relationship",
                "id": r.id,
                "name": r.display_name or (r.person.name if r.person else ""),
                "email": r.email or "",
                "phone": r.phone or "",
                "health": r.health,
                "status": r.status,
                "tags": r.tags or [],
            })

    # 3. Search Entity records for 'lead' and 'customer' types
    for etype in ("lead", "customer"):
        defn = _find_entity_def(tenant_id, etype)
        if not defn:
            continue

        entities = Entity.query.filter(
            Entity.tenant_id == tenant_id,
            Entity.definition_id == defn.id,
            Entity.is_archived == False,
            db.or_(
                Entity.data["name"].as_string().ilike(f"%{query}%"),
                Entity.data["phone"].as_string().ilike(f"%{query}%"),
                Entity.data["email"].as_string().ilike(f"%{query}%"),
                Entity.data["passport"].as_string().ilike(f"%{query}%"),
            ),
        ).limit(20).all()

        for e in entities:
            key = f"entity_{e.id}"
            if key not in seen_ids:
                seen_ids.add(key)
                results.append({
                    "type": etype,
                    "id": e.id,
                    "code": e.code or "",
                    "name": e.data.get("name", e.display_name),
                    "phone": e.data.get("phone", ""),
                    "email": e.data.get("email", ""),
                    "passport": e.data.get("passport", ""),
                    "status": e.status,
                    "tags": e.tags or [],
                    "created_at": e.created_at.isoformat() if e.created_at else "",
                })

    if not results:
        return ToolResult(
            success=True,
            message=f"No customers found matching '{query}'.",
            data={"query": query, "results": []},
        )

    return ToolResult(
        success=True,
        message=f"Found {len(results)} customer(s) matching '{query}'.",
        data={"query": query, "results": results},
    )


register_tool(ToolDef(
    id="find_customer",
    name="Find Customer",
    description="Search customers by name, phone, email, or passport number. Searches across Person, Relationship, Lead, and Customer records.",
    category=ToolCategory.CUSTOMER,
    permission=ToolPermission.READ,
    tier=1,
    handler=_find_customer,
    parameters={
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "Search query — name, phone, email, or passport number",
            },
            "name": {"type": "string", "description": "Customer name to search"},
            "phone": {"type": "string", "description": "Phone number to search"},
            "email": {"type": "string", "description": "Email address to search"},
            "passport": {"type": "string", "description": "Passport number to search"},
        },
    },
    examples=[
        "find customer Sharma",
        "search customer +919876543210",
        "find by email john@example.com",
        "lookup passport AB123456",
    ],
))

# ---------------------------------------------------------------------------
# 2. create_lead — Create a new lead from inquiry
# ---------------------------------------------------------------------------

def _create_lead(params: dict, agent=None) -> ToolResult:
    """Create a new lead from customer inquiry."""
    from app import db
    from app.models import Entity, EntityDefinition, ActivityLog, next_entity_code

    tenant_id = _get_tenant_id()
    user_id = _get_user_id()

    # Required fields
    name = (params.get("name") or params.get("customer_name") or "").strip()
    phone = (params.get("phone") or params.get("mobile") or "").strip()

    if not name and not phone:
        return ToolResult(
            success=False,
            message="At least a customer name or phone number is required to create a lead.",
            error="missing_required_fields",
        )

    # Find the lead EntityDefinition
    defn = _find_entity_def(tenant_id, "lead")
    if not defn:
        return ToolResult(
            success=False,
            message="Lead entity type is not configured. Please create a Lead module first.",
            error="missing_entity_definition",
        )

    # Build data dict from params
    data = {}
    for field in ("name", "phone", "email", "destination", "passport",
                  "source", "notes", "budget", "people", "dates",
                  "preferred_channel", "city", "nationality"):
        val = params.get(field)
        if val is not None:
            data[field] = val

    # Map alternate field names
    if "customer_name" in params and "name" not in data:
        data["name"] = params["customer_name"]
    if "mobile" in params and "phone" not in data:
        data["phone"] = params["mobile"]
    if "enquiry" in params and "notes" not in data:
        data["notes"] = params["enquiry"]

    # Default status
    status = params.get("status", defn.statuses[0] if defn.statuses else "new")

    # Generate entity code
    code = next_entity_code(db.session, tenant_id, "lead")

    # Create assigned_to from params
    assigned_to = params.get("assigned_to") or params.get("assign_to") or user_id

    entity = Entity(
        tenant_id=tenant_id,
        definition_id=defn.id,
        code=code,
        status=status,
        data=data,
        assigned_to=assigned_to if isinstance(assigned_to, int) else user_id,
        tags=params.get("tags", []),
        created_by=user_id,
    )
    db.session.add(entity)
    db.session.flush()

    # Log activity
    activity = ActivityLog(
        tenant_id=tenant_id,
        entity_id=entity.id,
        user_id=user_id,
        action="created",
        detail=f"Lead created: {name or phone} ({code})",
        metadata_json={"source": "agent", "params": {k: v for k, v in params.items() if k != "raw"}},
        governance_level="auto",
    )
    db.session.add(activity)
    db.session.commit()

    return ToolResult(
        success=True,
        message=f"Lead created successfully for {name or phone} (Code: {code}).",
        data={
            "id": entity.id,
            "code": code,
            "name": name or data.get("name", ""),
            "phone": phone or data.get("phone", ""),
            "status": status,
            "target_url": f"/entities/lead/{entity.id}",
        },
        target_url=f"/entities/lead/{entity.id}",
    )


register_tool(ToolDef(
    id="create_lead",
    name="Create Lead",
    description="Create a new lead from a customer inquiry. Requires at least a name or phone number.",
    category=ToolCategory.CUSTOMER,
    permission=ToolPermission.WRITE,
    tier=2,
    handler=_create_lead,
    parameters={
        "type": "object",
        "properties": {
            "name": {"type": "string", "description": "Customer name"},
            "phone": {"type": "string", "description": "Customer phone number"},
            "email": {"type": "string", "description": "Customer email address"},
            "destination": {"type": "string", "description": "Travel destination or interest"},
            "people": {"type": "string", "description": "Number of people (e.g., '2 adults, 1 child')"},
            "dates": {"type": "string", "description": "Travel dates or timeframe"},
            "budget": {"type": "string", "description": "Budget range or amount"},
            "notes": {"type": "string", "description": "Additional notes or inquiry details"},
            "source": {"type": "string", "description": "Lead source (website, referral, walk-in, etc.)"},
            "status": {"type": "string", "description": "Initial status (defaults to 'new')"},
            "tags": {"type": "array", "description": "Tags for the lead", "items": {"type": "string"}},
        },
    },
    examples=[
        "create lead for Rajesh Sharma phone 9876543210",
        "new lead: Priya looking for Bali trip for 2, budget 1.5 lakhs",
        "add lead from website: Ananya, +919876543210, destination Dubai",
    ],
))

# ---------------------------------------------------------------------------
# 3. update_lead_status — Move lead through pipeline
# ---------------------------------------------------------------------------

def _update_lead_status(params: dict, agent=None) -> ToolResult:
    """Move a lead through the pipeline by updating its status."""
    from app import db
    from app.models import Entity, EntityDefinition, ActivityLog

    tenant_id = _get_tenant_id()
    user_id = _get_user_id()

    # Find the lead by code, id, or name
    identifier = (params.get("lead_id") or params.get("code") or
                  params.get("id") or params.get("name") or "").strip()
    new_status = (params.get("status") or params.get("new_status") or "").strip()

    if not identifier:
        return ToolResult(
            success=False,
            message="Please specify which lead to update (by ID, code, or name).",
            error="missing_identifier",
        )
    if not new_status:
        return ToolResult(
            success=False,
            message="Please specify the new status for the lead.",
            error="missing_status",
        )

    defn = _find_entity_def(tenant_id, "lead")
    if not defn:
        return ToolResult(
            success=False,
            message="Lead entity type is not configured.",
            error="missing_entity_definition",
        )

    # Find the entity
    entity = None
    # Try by code first
    if identifier.isdigit():
        entity = Entity.query.filter_by(
            id=int(identifier), tenant_id=tenant_id,
            definition_id=defn.id, is_archived=False,
        ).first()
    if not entity:
        entity = Entity.query.filter_by(
            code=identifier, tenant_id=tenant_id,
            definition_id=defn.id, is_archived=False,
        ).first()
    if not entity:
        # Try by name in data
        entity = Entity.query.filter(
            Entity.tenant_id == tenant_id,
            Entity.definition_id == defn.id,
            Entity.is_archived == False,
            Entity.data["name"].as_string().ilike(f"%{identifier}%"),
        ).first()

    if not entity:
        return ToolResult(
            success=False,
            message=f"Could not find a lead matching '{identifier}'.",
            error="not_found",
        )

    old_status = entity.status
    entity.status = new_status
    entity.updated_at = datetime.utcnow()

    # Log the status change
    activity = ActivityLog(
        tenant_id=tenant_id,
        entity_id=entity.id,
        user_id=user_id,
        action="status_changed",
        detail=f"Lead status changed: {old_status} → {new_status}",
        metadata_json={"old_status": old_status, "new_status": new_status},
        governance_level="auto",
    )
    db.session.add(activity)
    db.session.commit()

    return ToolResult(
        success=True,
        message=f"Lead '{entity.display_name}' moved from '{old_status}' to '{new_status}'.",
        data={
            "id": entity.id,
            "code": entity.code,
            "name": entity.display_name,
            "old_status": old_status,
            "new_status": new_status,
            "target_url": f"/entities/lead/{entity.id}",
        },
        target_url=f"/entities/lead/{entity.id}",
    )


register_tool(ToolDef(
    id="update_lead_status",
    name="Update Lead Status",
    description="Move a lead through the pipeline by updating its status (e.g., new → contacted → qualified → proposal → booked → lost).",
    category=ToolCategory.CUSTOMER,
    permission=ToolPermission.WRITE,
    tier=2,
    handler=_update_lead_status,
    parameters={
        "type": "object",
        "properties": {
            "lead_id": {"type": "string", "description": "Lead ID, code, or name to identify the lead"},
            "code": {"type": "string", "description": "Lead code (e.g., PC11072601)"},
            "status": {"type": "string", "description": "New status value"},
            "new_status": {"type": "string", "description": "Alias for status"},
        },
    },
    examples=[
        "move lead PC11072601 to contacted",
        "update status of Sharma to qualified",
        "mark lead 42 as lost",
    ],
))

# ---------------------------------------------------------------------------
# 4. merge_duplicate_customers — Find and merge duplicates
# ---------------------------------------------------------------------------

def _merge_duplicate_customers(params: dict, agent=None) -> ToolResult:
    """Find and merge duplicate customer records."""
    from app import db
    from app.models import Entity, EntityDefinition, ActivityLog

    tenant_id = _get_tenant_id()
    user_id = _get_user_id()

    # Accept explicit primary and secondary IDs, or auto-detect duplicates
    primary_id = params.get("primary_id")
    secondary_ids = params.get("secondary_ids", [])

    if isinstance(secondary_ids, str):
        try:
            secondary_ids = json.loads(secondary_ids)
        except (json.JSONDecodeError, TypeError):
            secondary_ids = [s.strip() for s in secondary_ids.split(",") if s.strip()]

    if primary_id and secondary_ids:
        # Manual merge — merge specified records
        return _do_merge(tenant_id, user_id, int(primary_id),
                         [int(s) for s in secondary_ids])

    # Auto-detect duplicates across lead and customer entities
    etype = params.get("entity_type", "lead")
    defn = _find_entity_def(tenant_id, etype)
    if not defn:
        return ToolResult(
            success=False,
            message=f"No '{etype}' entity type configured.",
            error="missing_entity_definition",
        )

    entities = Entity.query.filter(
        Entity.tenant_id == tenant_id,
        Entity.definition_id == defn.id,
        Entity.is_archived == False,
    ).all()

    # Group by phone and email for duplicate detection
    phone_groups = {}
    email_groups = {}
    for e in entities:
        phone = e.data.get("phone", "").strip()
        if phone:
            clean = phone.replace(" ", "").replace("-", "").replace("+91", "")
            phone_groups.setdefault(clean, []).append(e)
        email = e.data.get("email", "").strip().lower()
        if email:
            email_groups.setdefault(email, []).append(e)

    duplicates = []
    for key, group in phone_groups.items():
        if len(group) > 1:
            duplicates.append({
                "match_on": f"phone: {key}",
                "ids": [e.id for e in group],
                "names": [e.data.get("name", e.display_name) for e in group],
            })
    for key, group in email_groups.items():
        if len(group) > 1:
            # Check if already caught by phone
            ids = {e.id for e in group}
            already = any(set(d["ids"]) == ids for d in duplicates)
            if not already:
                duplicates.append({
                    "match_on": f"email: {key}",
                    "ids": [e.id for e in group],
                    "names": [e.data.get("name", e.display_name) for e in group],
                })

    if not duplicates:
        return ToolResult(
            success=True,
            message=f"No duplicate {etype} records found.",
            data={"entity_type": etype, "duplicates": []},
        )

    return ToolResult(
        success=True,
        message=f"Found {len(duplicates)} potential duplicate group(s).",
        data={
            "entity_type": etype,
            "duplicates": duplicates,
            "instruction": "To merge, call with primary_id and secondary_ids. E.g., merge_duplicate_customers(primary_id=1, secondary_ids=[2,3])",
        },
    )


def _do_merge(tenant_id: int, user_id: int, primary_id: int,
              secondary_ids: list[int]) -> ToolResult:
    """Merge secondary entities into the primary entity."""
    from app import db
    from app.models import Entity, EntityDefinition, ActivityLog, Message, File

    primary = Entity.query.filter_by(
        id=primary_id, tenant_id=tenant_id, is_archived=False,
    ).first()
    if not primary:
        return ToolResult(
            success=False,
            message=f"Primary entity #{primary_id} not found.",
            error="not_found",
        )

    merged_data = dict(primary.data)
    merged_tags = set(primary.tags or [])
    merged_count = 0

    for sid in secondary_ids:
        secondary = Entity.query.filter_by(
            id=sid, tenant_id=tenant_id, is_archived=False,
        ).first()
        if not secondary or secondary.id == primary_id:
            continue

        # Merge data (secondary fields fill gaps in primary)
        for k, v in secondary.data.items():
            if k not in merged_data or not merged_data.get(k):
                merged_data[k] = v
        merged_tags.update(secondary.tags or [])

        # Reassign messages to primary
        Message.query.filter_by(entity_id=secondary.id).update(
            {"entity_id": primary.id}
        )

        # Reassign files to primary
        File.query.filter_by(entity_id=secondary.id).update(
            {"entity_id": primary.id}
        )

        # Archive secondary
        secondary.is_archived = True
        secondary.data = {"merged_into": primary_id, "merged_at": datetime.utcnow().isoformat()}

        # Log merge activity
        activity = ActivityLog(
            tenant_id=tenant_id,
            entity_id=primary.id,
            user_id=user_id,
            action="merged",
            detail=f"Merged entity #{sid} into #{primary_id}",
            metadata_json={"source_entity_id": sid, "target_entity_id": primary_id},
        )
        db.session.add(activity)

        merged_count += 1

    # Update primary with merged data
    primary.data = merged_data
    primary.tags = list(merged_tags) if merged_tags else primary.tags
    primary.updated_at = datetime.utcnow()

    # Log the merge completion
    merge_activity = ActivityLog(
        tenant_id=tenant_id,
        entity_id=primary.id,
        user_id=user_id,
        action="merged",
        detail=f"Merged {merged_count} duplicate(s) into {primary.display_name}",
        metadata_json={"merged_count": merged_count, "secondary_ids": secondary_ids},
    )
    db.session.add(merge_activity)
    db.session.commit()

    return ToolResult(
        success=True,
        message=f"Successfully merged {merged_count} record(s) into {primary.display_name}.",
        data={
            "primary_id": primary.id,
            "primary_name": primary.display_name,
            "merged_count": merged_count,
            "merged_ids": secondary_ids,
            "target_url": f"/entities/{primary.definition.type if primary.definition else 'lead'}/{primary.id}",
        },
    )


register_tool(ToolDef(
    id="merge_duplicate_customers",
    name="Merge Duplicate Customers",
    description="Find and merge duplicate customer records. Auto-detects duplicates by phone/email, or merges specified records.",
    category=ToolCategory.CUSTOMER,
    permission=ToolPermission.ADMIN,
    tier=3,
    handler=_merge_duplicate_customers,
    parameters={
        "type": "object",
        "properties": {
            "primary_id": {"type": "number", "description": "ID of the primary record to keep"},
            "secondary_ids": {
                "type": "array",
                "description": "IDs of duplicate records to merge into the primary",
                "items": {"type": "number"},
            },
            "entity_type": {
                "type": "string",
                "description": "Entity type to check for duplicates (default: lead)",
                "enum": ["lead", "customer"],
            },
        },
    },
    examples=[
        "merge duplicate customers",
        "merge_duplicate_customers primary_id=10 secondary_ids=[11,12]",
        "find and merge duplicate leads",
    ],
))

# ---------------------------------------------------------------------------
# 5. add_customer_note — Add internal note to customer
# ---------------------------------------------------------------------------

def _add_customer_note(params: dict, agent=None) -> ToolResult:
    """Add an internal note to a customer record."""
    from app import db
    from app.models import Entity, EntityDefinition, ActivityLog

    tenant_id = _get_tenant_id()
    user_id = _get_user_id()

    note = (params.get("note") or params.get("notes") or params.get("text") or "").strip()
    identifier = (params.get("customer_id") or params.get("lead_id") or
                  params.get("code") or params.get("name") or "").strip()

    if not note:
        return ToolResult(
            success=False,
            message="Please provide the note text.",
            error="missing_note",
        )
    if not identifier:
        return ToolResult(
            success=False,
            message="Please specify which customer to add the note to.",
            error="missing_identifier",
        )

    # Find the entity across lead and customer types
    entity = None
    for etype in ("lead", "customer"):
        defn = _find_entity_def(tenant_id, etype)
        if not defn:
            continue

        if identifier.isdigit():
            entity = Entity.query.filter_by(
                id=int(identifier), tenant_id=tenant_id,
                definition_id=defn.id, is_archived=False,
            ).first()
        if not entity:
            entity = Entity.query.filter_by(
                code=identifier, tenant_id=tenant_id,
                definition_id=defn.id, is_archived=False,
            ).first()
        if not entity:
            entity = Entity.query.filter(
                Entity.tenant_id == tenant_id,
                Entity.definition_id == defn.id,
                Entity.is_archived == False,
                Entity.data["name"].as_string().ilike(f"%{identifier}%"),
            ).first()
        if entity:
            break

    if not entity:
        return ToolResult(
            success=False,
            message=f"Could not find a customer matching '{identifier}'.",
            error="not_found",
        )

    # Append note to existing notes or create a notes array
    existing_notes = entity.data.get("notes", "")
    if existing_notes:
        timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M")
        entity.data["notes"] = f"{existing_notes}\n[{timestamp}] {note}"
    else:
        entity.data["notes"] = note
    entity.updated_at = datetime.utcnow()

    # Also store as a structured note in the notes field
    if "notes_log" not in entity.data:
        entity.data["notes_log"] = []
    entity.data["notes_log"].append({
        "text": note,
        "added_by": user_id,
        "added_at": datetime.utcnow().isoformat(),
    })

    # Log activity
    activity = ActivityLog(
        tenant_id=tenant_id,
        entity_id=entity.id,
        user_id=user_id,
        action="note_added",
        detail=f"Note added to {entity.display_name}: {note[:200]}",
        metadata_json={"note_preview": note[:200]},
    )
    db.session.add(activity)
    db.session.commit()

    return ToolResult(
        success=True,
        message=f"Note added to {entity.display_name}.",
        data={
            "customer_id": entity.id,
            "customer_name": entity.display_name,
            "note_preview": note[:200],
        },
    )


register_tool(ToolDef(
    id="add_customer_note",
    name="Add Customer Note",
    description="Add an internal note to a customer record for team reference.",
    category=ToolCategory.CUSTOMER,
    permission=ToolPermission.WRITE,
    tier=2,
    handler=_add_customer_note,
    parameters={
        "type": "object",
        "properties": {
            "customer_id": {"type": "string", "description": "Customer ID, code, or name"},
            "note": {"type": "string", "description": "The note text to add"},
            "notes": {"type": "string", "description": "Alias for note"},
        },
    },
    examples=[
        "add note to customer PC11072601: Called and confirmed interest in Bali package",
        "note for Sharma: prefers WhatsApp communication",
        "add note to lead 42: requested callback tomorrow",
    ],
))

# ---------------------------------------------------------------------------
# 6. view_customer_history — Full timeline of customer
# ---------------------------------------------------------------------------

def _view_customer_history(params: dict, agent=None) -> ToolResult:
    """View the full timeline/history of a customer."""
    from app.models import Entity, EntityDefinition, ActivityLog, Message

    tenant_id = _get_tenant_id()

    identifier = (params.get("customer_id") or params.get("lead_id") or
                  params.get("code") or params.get("name") or "").strip()

    if not identifier:
        return ToolResult(
            success=False,
            message="Please specify a customer by ID, code, or name.",
            error="missing_identifier",
        )

    # Find the entity
    entity = None
    for etype in ("lead", "customer"):
        defn = _find_entity_def(tenant_id, etype)
        if not defn:
            continue
        if identifier.isdigit():
            entity = Entity.query.filter_by(
                id=int(identifier), tenant_id=tenant_id,
                definition_id=defn.id,
            ).first()
        if not entity:
            entity = Entity.query.filter_by(
                code=identifier, tenant_id=tenant_id,
                definition_id=defn.id,
            ).first()
        if not entity:
            entity = Entity.query.filter(
                Entity.tenant_id == tenant_id,
                Entity.definition_id == defn.id,
                Entity.data["name"].as_string().ilike(f"%{identifier}%"),
            ).first()
        if entity:
            break

    if not entity:
        return ToolResult(
            success=False,
            message=f"No customer found matching '{identifier}'.",
            error="not_found",
        )

    # Gather timeline entries
    timeline = []

    # Entity creation
    timeline.append({
        "type": "created",
        "timestamp": entity.created_at.isoformat() if entity.created_at else "",
        "detail": f"Record created (Code: {entity.code or 'N/A'}, Status: {entity.status})",
    })

    # Activity logs
    activities = ActivityLog.query.filter_by(
        tenant_id=tenant_id, entity_id=entity.id,
    ).order_by(ActivityLog.created_at.desc()).limit(100).all()

    for act in activities:
        timeline.append({
            "type": act.action,
            "timestamp": act.created_at.isoformat() if act.created_at else "",
            "detail": act.detail or "",
            "user_id": act.user_id,
        })

    # Messages
    messages = Message.query.filter_by(
        tenant_id=tenant_id, entity_id=entity.id,
    ).order_by(Message.created_at.desc()).limit(100).all()

    for msg in messages:
        timeline.append({
            "type": "message",
            "channel": msg.channel,
            "timestamp": msg.created_at.isoformat() if msg.created_at else "",
            "detail": msg.content[:300],
            "sender_type": msg.sender_type,
            "is_from_client": msg.is_from_client,
        })

    # Sort by timestamp descending
    timeline.sort(key=lambda x: x.get("timestamp", ""), reverse=True)

    return ToolResult(
        success=True,
        message=f"Customer history for {entity.display_name} ({entity.code or f'#{entity.id}'})",
        data={
            "customer": {
                "id": entity.id,
                "code": entity.code,
                "name": entity.display_name,
                "status": entity.status,
                "data": entity.data,
                "tags": entity.tags or [],
                "created_at": entity.created_at.isoformat() if entity.created_at else "",
                "updated_at": entity.updated_at.isoformat() if entity.updated_at else "",
            },
            "timeline": timeline,
            "total_events": len(timeline),
            "target_url": f"/entities/{entity.definition.type if entity.definition else 'lead'}/{entity.id}",
        },
    )


register_tool(ToolDef(
    id="view_customer_history",
    name="View Customer History",
    description="View the full timeline of a customer: creation, status changes, notes, messages, and all activities.",
    category=ToolCategory.CUSTOMER,
    permission=ToolPermission.READ,
    tier=1,
    handler=_view_customer_history,
    parameters={
        "type": "object",
        "properties": {
            "customer_id": {"type": "string", "description": "Customer ID, code, or name"},
            "lead_id": {"type": "string", "description": "Alias for customer_id"},
            "code": {"type": "string", "description": "Entity code (e.g., PC11072601)"},
            "name": {"type": "string", "description": "Customer name to search"},
        },
    },
    examples=[
        "show history for customer PC11072601",
        "view timeline of Sharma",
        "customer history for lead 42",
    ],
))

# ---------------------------------------------------------------------------
# 7. add_customer_tag — Tag customers (VIP, repeat, honeymoon, etc.)
# ---------------------------------------------------------------------------

def _add_customer_tag(params: dict, agent=None) -> ToolResult:
    """Add tags to a customer record."""
    from app import db
    from app.models import Entity, EntityDefinition, ActivityLog

    tenant_id = _get_tenant_id()
    user_id = _get_user_id()

    identifier = (params.get("customer_id") or params.get("lead_id") or
                  params.get("code") or params.get("name") or "").strip()
    tags = params.get("tags", [])

    if isinstance(tags, str):
        tags = [t.strip() for t in tags.split(",") if t.strip()]

    tag = params.get("tag", "")
    if tag and tag not in tags:
        tags.append(tag)

    if not identifier:
        return ToolResult(
            success=False,
            message="Please specify a customer by ID, code, or name.",
            error="missing_identifier",
        )
    if not tags:
        return ToolResult(
            success=False,
            message="Please provide at least one tag (e.g., VIP, repeat, honeymoon).",
            error="missing_tags",
        )

    # Find the entity
    entity = None
    for etype in ("lead", "customer"):
        defn = _find_entity_def(tenant_id, etype)
        if not defn:
            continue
        if identifier.isdigit():
            entity = Entity.query.filter_by(
                id=int(identifier), tenant_id=tenant_id,
                definition_id=defn.id, is_archived=False,
            ).first()
        if not entity:
            entity = Entity.query.filter_by(
                code=identifier, tenant_id=tenant_id,
                definition_id=defn.id, is_archived=False,
            ).first()
        if not entity:
            entity = Entity.query.filter(
                Entity.tenant_id == tenant_id,
                Entity.definition_id == defn.id,
                Entity.is_archived == False,
                Entity.data["name"].as_string().ilike(f"%{identifier}%"),
            ).first()
        if entity:
            break

    if not entity:
        return ToolResult(
            success=False,
            message=f"No customer found matching '{identifier}'.",
            error="not_found",
        )

    # Add tags (deduplicate)
    existing_tags = set(entity.tags or [])
    added = []
    for t in tags:
        clean = t.strip().lower().replace(" ", "_")
        if clean and clean not in existing_tags:
            existing_tags.add(clean)
            added.append(clean)

    if not added:
        return ToolResult(
            success=True,
            message=f"Customer already has all requested tags: {', '.join(tags)}.",
            data={"customer_id": entity.id, "tags": list(existing_tags)},
        )

    entity.tags = list(existing_tags)
    entity.updated_at = datetime.utcnow()

    # Log activity
    activity = ActivityLog(
        tenant_id=tenant_id,
        entity_id=entity.id,
        user_id=user_id,
        action="tagged",
        detail=f"Tags added to {entity.display_name}: {', '.join(added)}",
        metadata_json={"added_tags": added, "all_tags": list(existing_tags)},
    )
    db.session.add(activity)
    db.session.commit()

    return ToolResult(
        success=True,
        message=f"Tags added to {entity.display_name}: {', '.join(added)}.",
        data={
            "customer_id": entity.id,
            "customer_name": entity.display_name,
            "added_tags": added,
            "all_tags": list(existing_tags),
        },
    )


register_tool(ToolDef(
    id="add_customer_tag",
    name="Add Customer Tag",
    description="Tag customers with labels like VIP, repeat, honeymoon, high_value, etc. for segmentation and filtering.",
    category=ToolCategory.CUSTOMER,
    permission=ToolPermission.WRITE,
    tier=2,
    handler=_add_customer_tag,
    parameters={
        "type": "object",
        "properties": {
            "customer_id": {"type": "string", "description": "Customer ID, code, or name"},
            "tags": {
                "type": "array",
                "description": "Tag names to add (e.g., ['VIP', 'repeat', 'honeymoon'])",
                "items": {"type": "string"},
            },
            "tag": {"type": "string", "description": "Single tag to add (alternative to tags array)"},
        },
    },
    examples=[
        "tag customer PC11072601 as VIP",
        "add tags to Sharma: repeat, honeymoon",
        "tag lead 42 as high_value, referral",
    ],
))

# ---------------------------------------------------------------------------
# 8. parse_inquiry — Take raw text inquiry and extract fields
# ---------------------------------------------------------------------------

def _parse_inquiry(params: dict, agent=None) -> ToolResult:
    """Parse a raw text inquiry and extract structured fields."""
    text = (params.get("text") or params.get("inquiry") or
            params.get("message") or "").strip()

    if not text:
        return ToolResult(
            success=False,
            message="Please provide the inquiry text to parse.",
            error="missing_text",
        )

    extracted = {
        "raw": text,
        "name": None,
        "phone": None,
        "email": None,
        "destination": None,
        "people": None,
        "dates": None,
        "budget": None,
        "source": "inquiry",
    }

    text_lower = text.lower()

    # Extract name — words after "I am", "this is", "my name is"
    name_patterns = [
        r"(?:I am|I'm|this is|my name is|myself)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)",
        r"name\s+(?:is\s+)?([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)",
    ]
    for pat in name_patterns:
        m = re.search(pat, text)
        if m:
            extracted["name"] = m.group(1).strip()
            break

    # Extract phone number
    phone_patterns = [
        r"(\+?\d{1,3}[-.\s]?\d{6,14})",
        r"(\d{10})",
    ]
    for pat in phone_patterns:
        m = re.search(pat, text)
        if m:
            candidate = m.group(1).strip()
            digits = re.sub(r"\D", "", candidate)
            if 10 <= len(digits) <= 15:
                extracted["phone"] = candidate
                break

    # Extract email
    m = re.search(r"[\w\.\+\-]+@[\w\-]+\.[\w\.\-]+", text)
    if m:
        extracted["email"] = m.group(0)

    # Extract destination — after "to", "for", "in"
    dest_keywords = [
        r"(?:trip to|travel to|going to|visit|tour to|headed to)\s+([A-Z][a-zA-Z\s]+?)(?:\.|,|for|in|with|\d|$)",
        r"(?:interested in|looking for|want to go to)\s+([A-Z][a-zA-Z\s]+?)(?:\.|,|for|in|with|\d|$)",
    ]
    for pat in dest_keywords:
        m = re.search(pat, text)
        if m:
            extracted["destination"] = m.group(1).strip().rstrip("., ")
            break

    # Extract number of people
    people_patterns = [
        r"(\d+)\s*(?:adults?|people|pax|persons?|travellers?|guests?)",
        r"(?:for|group of)\s*(\d+)\s*(?:people|pax|members?)",
    ]
    for pat in people_patterns:
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            extracted["people"] = m.group(1)
            break

    # Extract dates / timeframe
    date_patterns = [
        r"(?:in\s+)?(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2}(?:st|nd|rd|th)?(?:\s*\d{4})?",
        r"(?:this|next|coming)\s+(?:month|week|year|summer|winter|spring|autumn|fall)",
        r"\d{1,2}[-/]\d{1,2}[-/]\d{2,4}",
        r"(?:from\s+)?\d{1,2}(?:st|nd|rd|th)?\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{4}",
        r"\d{1,2}\s+days?\s+(?:trip|tour|package|holiday|vacation)",
        r"(?:for\s+)?(\d+)\s*(?:days?|nights?|weeks?)",
    ]
    for pat in date_patterns:
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            extracted["dates"] = m.group(0).strip()
            break

    # Extract budget
    budget_patterns = [
        r"(?:budget|cost|spend|spending|around|approximately|approx)\s*(?:of\s*)?(?:Rs\.?|INR|₹|USD|\$)?\s*([\d,]+(?:\.\d{1,2})?)\s*(?:k|K|lakh|lacs?|crore|cr)?",
        r"(?:Rs\.?|INR|₹|USD|\$)\s*([\d,]+(?:\.\d{1,2})?)\s*(?:k|K|lakh|lacs?|crore|cr)?",
    ]
    for pat in budget_patterns:
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            budget_val = m.group(0).strip()
            extracted["budget"] = budget_val
            break

    # Detect source
    source_keywords = {
        "website": ["website", "online", "web", "form"],
        "instagram": ["instagram", "insta", "ig"],
        "facebook": ["facebook", "fb"],
        "referral": ["referral", "referred", "reference", "friend"],
        "walk_in": ["walk", "walk-in", "office"],
        "phone": ["phone call", "called", "ring"],
        "whatsapp": ["whatsapp"],
    }
    for source, keywords in source_keywords.items():
        if any(kw in text_lower for kw in keywords):
            extracted["source"] = source
            break

    return ToolResult(
        success=True,
        message="Inquiry parsed successfully.",
        data={
            "extracted": extracted,
            "confidence": sum(1 for v in extracted.values() if v is not None and v != "inquiry") / 8,
        },
    )


register_tool(ToolDef(
    id="parse_inquiry",
    name="Parse Inquiry",
    description="Take raw text from a customer inquiry and extract structured fields: name, phone, email, destination, people, dates, budget, source.",
    category=ToolCategory.CUSTOMER,
    permission=ToolPermission.READ,
    tier=1,
    handler=_parse_inquiry,
    parameters={
        "type": "object",
        "properties": {
            "text": {"type": "string", "description": "Raw inquiry text to parse"},
            "inquiry": {"type": "string", "description": "Alias for text"},
            "message": {"type": "string", "description": "Alias for text"},
        },
    },
    examples=[
        "parse: I am Rajesh, looking for a trip to Bali for 2 adults in December, budget around 1.5 lakhs",
        "extract fields from this inquiry: Hi, I'm Priya +919876543210. Want to go to Dubai next month",
        "parse inquiry: need 4 people Thailand trip July 2025 for 2 lakhs",
    ],
))

# ---------------------------------------------------------------------------
# 9. send_whatsapp — Send WhatsApp message to customer
# ---------------------------------------------------------------------------

def _send_whatsapp(params: dict, agent=None) -> ToolResult:
    """Send a WhatsApp message to a customer."""
    from app import db
    from app.models import Entity, ActivityLog, Message

    tenant_id = _get_tenant_id()
    user_id = _get_user_id()

    recipient = (params.get("to") or params.get("recipient") or
                 params.get("phone") or params.get("customer_id") or "").strip()
    message_text = (params.get("message") or params.get("text") or "").strip()

    if not recipient:
        return ToolResult(
            success=False,
            message="Please specify a recipient (phone number or customer name).",
            error="missing_recipient",
        )
    if not message_text:
        return ToolResult(
            success=False,
            message="Please provide the message content.",
            error="missing_message",
        )

    # Try to resolve recipient to a phone number
    phone = recipient
    entity_id = None
    entity = None

    # If recipient looks like a name or ID, look up in Entity
    if not re.match(r'^\+?\d{7,15}$', recipient.replace(" ", "").replace("-", "")):
        for etype in ("lead", "customer"):
            defn = _find_entity_def(tenant_id, etype)
            if not defn:
                continue
            if recipient.isdigit():
                entity = Entity.query.filter_by(
                    id=int(recipient), tenant_id=tenant_id,
                    definition_id=defn.id,
                ).first()
            if not entity:
                entity = Entity.query.filter(
                    Entity.tenant_id == tenant_id,
                    Entity.definition_id == defn.id,
                    Entity.data["name"].as_string().ilike(f"%{recipient}%"),
                ).first()
            if entity:
                phone = entity.data.get("phone", recipient)
                entity_id = entity.id
                break

    # Try to send via WhatsApp integration
    sent = False
    provider_response = None
    try:
        # Check if tenant has WhatsApp config
        tenant = getattr(g, "tenant", None)
        if not tenant:
            from app.models import Tenant
            tenant = Tenant.query.get(tenant_id)

        ai_config = getattr(tenant, "ai_config", {}) or {}
        whatsapp_config = ai_config.get("whatsapp", {})

        if whatsapp_config.get("enabled") or whatsapp_config.get("provider"):
            # Use the WhatsApp channel if available
            from app.shunya.whatsapp import WhatsAppChannel
            provider_response = WhatsAppChannel.send_text(phone, message_text)
            sent = True
        else:
            # Log as queued — actual sending happens via webhook
            sent = False
    except ImportError:
        # WhatsApp module not installed
        sent = False
    except Exception as e:
        logger.warning("WhatsApp send failed: %s", e)
        sent = False

    # Store the message
    if entity_id:
        msg = Message(
            tenant_id=tenant_id,
            entity_id=entity_id,
            sender_type="team",
            sender_id=user_id,
            channel="whatsapp",
            content=message_text,
            is_from_client=False,
        )
        db.session.add(msg)

    # Log activity
    activity = ActivityLog(
        tenant_id=tenant_id,
        entity_id=entity_id,
        user_id=user_id,
        action="message_sent",
        detail=f"WhatsApp to {phone}: {message_text[:200]}",
        metadata_json={
            "channel": "whatsapp", "recipient": phone,
            "sent": sent, "preview": message_text[:200],
        },
    )
    db.session.add(activity)
    db.session.commit()

    if sent:
        return ToolResult(
            success=True,
            message=f"WhatsApp message sent to {phone}.",
            data={"channel": "whatsapp", "recipient": phone, "sent": True},
        )
    else:
        return ToolResult(
            success=True,
            message=f"WhatsApp message queued for {phone}. It will be sent when the WhatsApp channel is configured.",
            data={"channel": "whatsapp", "recipient": phone, "sent": False, "queued": True},
        )


register_tool(ToolDef(
    id="send_whatsapp",
    name="Send WhatsApp",
    description="Send a WhatsApp message to a customer. Recipient can be a phone number, customer name, or customer ID.",
    category=ToolCategory.COMMUNICATION,
    permission=ToolPermission.WRITE,
    tier=2,
    handler=_send_whatsapp,
    parameters={
        "type": "object",
        "properties": {
            "to": {"type": "string", "description": "Recipient phone number or customer name/ID"},
            "recipient": {"type": "string", "description": "Alias for 'to'"},
            "phone": {"type": "string", "description": "Phone number to send to"},
            "message": {"type": "string", "description": "The message text to send"},
            "text": {"type": "string", "description": "Alias for message"},
        },
    },
    examples=[
        "send WhatsApp to +919876543210: Your Bali package is confirmed!",
        "WhatsApp Sharma: Please share the passport copies for booking",
        "send message to customer PC11072601: Your itinerary is ready for review",
    ],
))

# ---------------------------------------------------------------------------
# 10. send_email — Send email with attachment
# ---------------------------------------------------------------------------

def _send_email(params: dict, agent=None) -> ToolResult:
    """Send an email to a customer, optionally with an attachment."""
    from app import db
    from app.models import Entity, ActivityLog, Message

    tenant_id = _get_tenant_id()
    user_id = _get_user_id()

    to = (params.get("to") or params.get("recipient") or
          params.get("email") or "").strip()
    subject = (params.get("subject") or "").strip()
    body = (params.get("body") or params.get("message") or params.get("text") or "").strip()
    attachment_path = params.get("attachment") or params.get("file") or ""

    if not to:
        return ToolResult(
            success=False,
            message="Please specify a recipient email address.",
            error="missing_recipient",
        )
    if not subject:
        return ToolResult(
            success=False,
            message="Please provide an email subject.",
            error="missing_subject",
        )
    if not body:
        return ToolResult(
            success=False,
            message="Please provide the email body.",
            error="missing_body",
        )

    # Try to resolve recipient to an entity
    entity_id = None
    entity = None
    if not re.match(r'^[\w\.\+\-]+@[\w\-]+\.[\w\.\-]+$', to):
        # Looks like a name/ID, look up
        for etype in ("lead", "customer"):
            defn = _find_entity_def(tenant_id, etype)
            if not defn:
                continue
            if to.isdigit():
                entity = Entity.query.filter_by(
                    id=int(to), tenant_id=tenant_id,
                    definition_id=defn.id,
                ).first()
            if not entity:
                entity = Entity.query.filter(
                    Entity.tenant_id == tenant_id,
                    Entity.definition_id == defn.id,
                    db.or_(
                        Entity.data["name"].as_string().ilike(f"%{to}%"),
                        Entity.data["email"].as_string().ilike(f"%{to}%"),
                    ),
                ).first()
            if entity:
                to = entity.data.get("email", to)
                entity_id = entity.id
                break

    # Send email
    sent = False
    error_msg = None
    try:
        from app.shunya.utils import send_email as send_email_util
        result = send_email_util(
            to=to,
            subject=subject,
            body=body,
            attachment=attachment_path if attachment_path else None,
            tenant_id=tenant_id,
        )
        sent = result.get("success", False)
        if not sent:
            error_msg = result.get("error", "Unknown error")
    except Exception as e:
        error_msg = str(e)
        logger.warning("Email send failed: %s", e)

    # Store message if entity found
    if entity_id:
        msg = Message(
            tenant_id=tenant_id,
            entity_id=entity_id,
            sender_type="team",
            sender_id=user_id,
            channel="email",
            content=f"Subject: {subject}\n\n{body[:500]}",
            is_from_client=False,
        )
        db.session.add(msg)

    # Log activity
    activity = ActivityLog(
        tenant_id=tenant_id,
        entity_id=entity_id,
        user_id=user_id,
        action="email_sent",
        detail=f"Email to {to}: {subject}",
        metadata_json={
            "channel": "email", "to": to, "subject": subject,
            "has_attachment": bool(attachment_path), "sent": sent,
        },
    )
    db.session.add(activity)
    db.session.commit()

    if sent:
        return ToolResult(
            success=True,
            message=f"Email sent to {to} with subject '{subject}'.",
            data={"channel": "email", "to": to, "subject": subject, "sent": True},
        )
    else:
        return ToolResult(
            success=True,
            message=f"Email queued for {to}. It will be sent when the email service is configured. ({error_msg or 'queued'})",
            data={"channel": "email", "to": to, "subject": subject, "sent": False, "error": error_msg},
        )


register_tool(ToolDef(
    id="send_email",
    name="Send Email",
    description="Send an email to a customer. Recipient can be an email address or a customer name/ID. Supports optional file attachment.",
    category=ToolCategory.COMMUNICATION,
    permission=ToolPermission.WRITE,
    tier=2,
    handler=_send_email,
    parameters={
        "type": "object",
        "properties": {
            "to": {"type": "string", "description": "Recipient email address or customer name/ID"},
            "recipient": {"type": "string", "description": "Alias for 'to'"},
            "email": {"type": "string", "description": "Email address to send to"},
            "subject": {"type": "string", "description": "Email subject line"},
            "body": {"type": "string", "description": "Email body content"},
            "attachment": {"type": "string", "description": "File path or URL of attachment"},
            "file": {"type": "string", "description": "Alias for attachment"},
        },
    },
    examples=[
        "send email to sharma@email.com subject: Bali Package Confirmation body: Your Bali trip is confirmed!",
        "email customer PC11072601 with itinerary attachment",
        "send email to lead with quote PDF",
    ],
))

# ---------------------------------------------------------------------------
# 11. send_telegram — Send Telegram message
# ---------------------------------------------------------------------------

def _send_telegram(params: dict, agent=None) -> ToolResult:
    """Send a Telegram message to a customer."""
    from app import db
    from app.models import Entity, ActivityLog, Message

    tenant_id = _get_tenant_id()
    user_id = _get_user_id()

    recipient = (params.get("to") or params.get("recipient") or
                 params.get("chat_id") or params.get("customer_id") or "").strip()
    message_text = (params.get("message") or params.get("text") or "").strip()

    if not recipient:
        return ToolResult(
            success=False,
            message="Please specify a recipient (Telegram chat ID or customer name).",
            error="missing_recipient",
        )
    if not message_text:
        return ToolResult(
            success=False,
            message="Please provide the message content.",
            error="missing_message",
        )

    # Try to resolve recipient
    chat_id = recipient
    entity_id = None
    entity = None

    # If recipient looks like a name/ID, look up
    if not recipient.lstrip("-").isdigit():
        for etype in ("lead", "customer"):
            defn = _find_entity_def(tenant_id, etype)
            if not defn:
                continue
            if recipient.isdigit():
                entity = Entity.query.filter_by(
                    id=int(recipient), tenant_id=tenant_id,
                    definition_id=defn.id,
                ).first()
            if not entity:
                entity = Entity.query.filter(
                    Entity.tenant_id == tenant_id,
                    Entity.definition_id == defn.id,
                    Entity.data["name"].as_string().ilike(f"%{recipient}%"),
                ).first()
            if entity:
                chat_id = entity.data.get("telegram_chat_id", entity.data.get("phone", recipient))
                entity_id = entity.id
                break

    # Try to send via Telegram
    sent = False
    try:
        from app.shunya.utils import send_telegram as send_telegram_util
        result = send_telegram_util(chat_id=chat_id, text=message_text, tenant_id=tenant_id)
        sent = result.get("success", False)
    except ImportError:
        pass
    except Exception as e:
        logger.warning("Telegram send failed: %s", e)

    if entity_id:
        msg = Message(
            tenant_id=tenant_id,
            entity_id=entity_id,
            sender_type="team",
            sender_id=user_id,
            channel="telegram",
            content=message_text,
            is_from_client=False,
        )
        db.session.add(msg)

    activity = ActivityLog(
        tenant_id=tenant_id,
        entity_id=entity_id,
        user_id=user_id,
        action="message_sent",
        detail=f"Telegram to {chat_id}: {message_text[:200]}",
        metadata_json={"channel": "telegram", "recipient": chat_id, "sent": sent},
    )
    db.session.add(activity)
    db.session.commit()

    if sent:
        return ToolResult(
            success=True,
            message=f"Telegram message sent.",
            data={"channel": "telegram", "recipient": chat_id, "sent": True},
        )
    else:
        return ToolResult(
            success=True,
            message=f"Telegram message queued for {chat_id}.",
            data={"channel": "telegram", "recipient": chat_id, "sent": False, "queued": True},
        )


register_tool(ToolDef(
    id="send_telegram",
    name="Send Telegram",
    description="Send a Telegram message to a customer. Recipient can be a Telegram chat ID or customer name.",
    category=ToolCategory.COMMUNICATION,
    permission=ToolPermission.WRITE,
    tier=2,
    handler=_send_telegram,
    parameters={
        "type": "object",
        "properties": {
            "to": {"type": "string", "description": "Recipient Telegram chat ID or customer name"},
            "chat_id": {"type": "string", "description": "Telegram chat ID"},
            "message": {"type": "string", "description": "Message text to send"},
            "text": {"type": "string", "description": "Alias for message"},
        },
    },
    examples=[
        "send Telegram to 123456789: Your booking is confirmed!",
        "Telegram Sharma: Here is your invoice",
    ],
))

# ---------------------------------------------------------------------------
# 12. send_bulk_whatsapp — Broadcast to tagged customers (admin only)
# ---------------------------------------------------------------------------

def _send_bulk_whatsapp(params: dict, agent=None) -> ToolResult:
    """Send a broadcast WhatsApp message to all customers with specific tags."""
    from app import db
    from app.models import Entity, EntityDefinition, ActivityLog

    tenant_id = _get_tenant_id()
    user_id = _get_user_id()
    user_role = _get_user_role()

    # Admin check
    if user_role != "admin":
        return ToolResult(
            success=False,
            message="Only admins can send bulk WhatsApp messages.",
            error="permission_denied",
        )

    message_text = (params.get("message") or params.get("text") or "").strip()
    tags = params.get("tags", [])

    if isinstance(tags, str):
        tags = [t.strip() for t in tags.split(",") if t.strip()]

    entity_type = params.get("entity_type", "lead")

    if not message_text:
        return ToolResult(
            success=False,
            message="Please provide the broadcast message content.",
            error="missing_message",
        )
    if not tags:
        return ToolResult(
            success=False,
            message="Please specify tags to filter recipients (e.g., VIP, repeat).",
            error="missing_tags",
        )

    defn = _find_entity_def(tenant_id, entity_type)
    if not defn:
        return ToolResult(
            success=False,
            message=f"Entity type '{entity_type}' not configured.",
            error="missing_entity_definition",
        )

    # Find entities with matching tags AND a phone number
    matched = []
    entities = Entity.query.filter(
        Entity.tenant_id == tenant_id,
        Entity.definition_id == defn.id,
        Entity.is_archived == False,
    ).all()

    for e in entities:
        entity_tags = set(t.lower() for t in (e.tags or []))
        if any(t.lower() in entity_tags for t in tags):
            phone = e.data.get("phone", "").strip()
            if phone:
                matched.append({
                    "id": e.id,
                    "name": e.display_name,
                    "phone": phone,
                    "tags": e.tags or [],
                })

    if not matched:
        return ToolResult(
            success=True,
            message=f"No customers with tags {tags} and a phone number found.",
            data={"tags": tags, "entity_type": entity_type, "recipients": []},
        )

    # Send to each (or queue)
    sent_count = 0
    failed_count = 0
    results = []

    for recipient in matched:
        try:
            from app.shunya.whatsapp import WhatsAppChannel
            WhatsAppChannel.send_text(recipient["phone"], message_text)
            sent_count += 1
            results.append({"phone": recipient["phone"], "sent": True})
        except Exception as e:
            failed_count += 1
            results.append({"phone": recipient["phone"], "sent": False, "error": str(e)})

    # Log the broadcast
    activity = ActivityLog(
        tenant_id=tenant_id,
        user_id=user_id,
        action="bulk_whatsapp",
        detail=f"Bulk WhatsApp sent to {len(matched)} recipients with tags: {', '.join(tags)}",
        metadata_json={
            "tags": tags, "total": len(matched), "sent": sent_count,
            "failed": failed_count, "entity_type": entity_type,
        },
    )
    db.session.add(activity)
    db.session.commit()

    return ToolResult(
        success=True,
        message=f"Bulk WhatsApp sent to {sent_count} of {len(matched)} recipients (tags: {', '.join(tags)}).",
        data={
            "tags": tags,
            "total_recipients": len(matched),
            "sent_count": sent_count,
            "failed_count": failed_count,
            "recipients": results,
        },
    )


register_tool(ToolDef(
    id="send_bulk_whatsapp",
    name="Send Bulk WhatsApp",
    description="Send a broadcast WhatsApp message to all customers with specific tags. Admin only.",
    category=ToolCategory.COMMUNICATION,
    permission=ToolPermission.ADMIN,
    tier=3,
    handler=_send_bulk_whatsapp,
    parameters={
        "type": "object",
        "properties": {
            "message": {"type": "string", "description": "Broadcast message text"},
            "text": {"type": "string", "description": "Alias for message"},
            "tags": {
                "type": "array",
                "description": "Filter by customer tags (e.g., ['VIP', 'repeat'])",
                "items": {"type": "string"},
            },
            "entity_type": {
                "type": "string",
                "description": "Entity type to broadcast to (default: lead)",
                "enum": ["lead", "customer"],
            },
        },
    },
    examples=[
        "send bulk WhatsApp to all VIP customers: Exclusive Diwali offer!",
        "broadcast to repeat customers: Thank you for your continued trust",
        "send bulk message to all honeymoon tagged leads",
    ],
))

# ---------------------------------------------------------------------------
# 13. send_feedback_request — Auto-send feedback after trip
# ---------------------------------------------------------------------------

def _send_feedback_request(params: dict, agent=None) -> ToolResult:
    """Send a feedback request to a customer after their trip."""
    from app import db
    from app.models import Entity, EntityDefinition, ActivityLog, Message

    tenant_id = _get_tenant_id()
    user_id = _get_user_id()

    identifier = (params.get("customer_id") or params.get("lead_id") or
                  params.get("code") or params.get("name") or "").strip()
    channel = params.get("channel", "whatsapp")
    custom_message = params.get("message", "")

    if not identifier:
        return ToolResult(
            success=False,
            message="Please specify a customer by ID, code, or name.",
            error="missing_identifier",
        )

    # Find the entity
    entity = None
    for etype in ("lead", "customer"):
        defn = _find_entity_def(tenant_id, etype)
        if not defn:
            continue
        if identifier.isdigit():
            entity = Entity.query.filter_by(
                id=int(identifier), tenant_id=tenant_id,
                definition_id=defn.id,
            ).first()
        if not entity:
            entity = Entity.query.filter_by(
                code=identifier, tenant_id=tenant_id,
                definition_id=defn.id,
            ).first()
        if not entity:
            entity = Entity.query.filter(
                Entity.tenant_id == tenant_id,
                Entity.definition_id == defn.id,
                Entity.data["name"].as_string().ilike(f"%{identifier}%"),
            ).first()
        if entity:
            break

    if not entity:
        return ToolResult(
            success=False,
            message=f"No customer found matching '{identifier}'.",
            error="not_found",
        )

    # Get customer contact info
    phone = entity.data.get("phone", "")
    email = entity.data.get("email", "")
    name = entity.display_name

    # Build feedback message
    if custom_message:
        feedback_text = custom_message
    else:
        feedback_text = (
            f"Hi {name}! 🌟 We hope you had a wonderful experience. "
            f"We'd love to hear your feedback! Please take a moment to share your thoughts:\n\n"
            f"1. How was your overall experience? (1-5)\n"
            f"2. What did you enjoy most?\n"
            f"3. Any suggestions for improvement?\n\n"
            f"Your feedback helps us serve you better! 🙏"
        )

    # Send via the specified channel
    sent = False
    if channel == "whatsapp" and phone:
        try:
            from app.shunya.whatsapp import WhatsAppChannel
            WhatsAppChannel.send_text(phone, feedback_text)
            sent = True
        except Exception as e:
            logger.warning("Feedback WhatsApp send failed: %s", e)
    elif channel == "email" and email:
        try:
            from app.shunya.utils import send_email as send_email_util
            result = send_email_util(
                to=email,
                subject="We'd love your feedback! 🌟",
                body=feedback_text,
                tenant_id=tenant_id,
            )
            sent = result.get("success", False)
        except Exception as e:
            logger.warning("Feedback email send failed: %s", e)

    # Store message
    msg = Message(
        tenant_id=tenant_id,
        entity_id=entity.id,
        sender_type="system",
        channel=channel,
        content=f"Feedback request: {feedback_text[:300]}",
        is_from_client=False,
    )
    db.session.add(msg)

    # Log activity
    # Update entity status to reflect feedback sent
    entity.data["feedback_requested"] = True
    entity.data["feedback_requested_at"] = datetime.utcnow().isoformat()
    entity.updated_at = datetime.utcnow()

    activity = ActivityLog(
        tenant_id=tenant_id,
        entity_id=entity.id,
        user_id=user_id,
        action="feedback_requested",
        detail=f"Feedback request sent to {name} via {channel}",
        metadata_json={"channel": channel, "sent": sent},
    )
    db.session.add(activity)
    db.session.commit()

    return ToolResult(
        success=True,
        message=f"Feedback request sent to {name} via {channel}.",
        data={
            "customer_id": entity.id,
            "customer_name": name,
            "channel": channel,
            "sent": sent,
        },
    )


register_tool(ToolDef(
    id="send_feedback_request",
    name="Send Feedback Request",
    description="Send a feedback request to a customer after their trip. Message is sent via WhatsApp or email.",
    category=ToolCategory.CUSTOMER,
    permission=ToolPermission.WRITE,
    tier=2,
    handler=_send_feedback_request,
    parameters={
        "type": "object",
        "properties": {
            "customer_id": {"type": "string", "description": "Customer ID, code, or name"},
            "channel": {
                "type": "string",
                "description": "Channel to send feedback on (default: whatsapp)",
                "enum": ["whatsapp", "email"],
            },
            "message": {"type": "string", "description": "Optional custom feedback message"},
        },
    },
    examples=[
        "send feedback request to Sharma after his Bali trip",
        "request feedback from customer PC11072601 via email",
        "send feedback to lead 42",
    ],
))

# ---------------------------------------------------------------------------
# 14. schedule_message — Schedule message for future delivery
# ---------------------------------------------------------------------------

def _schedule_message(params: dict, agent=None) -> ToolResult:
    """Schedule a message for future delivery to a customer."""
    from app import db
    from app.models import Entity, ActivityLog

    tenant_id = _get_tenant_id()
    user_id = _get_user_id()

    recipient = (params.get("to") or params.get("recipient") or
                 params.get("customer_id") or params.get("phone") or "").strip()
    message_text = (params.get("message") or params.get("text") or "").strip()
    channel = params.get("channel", "whatsapp")
    schedule_at_raw = (params.get("schedule_at") or params.get("at") or
                       params.get("time") or "").strip()

    if not recipient:
        return ToolResult(
            success=False,
            message="Please specify a recipient.",
            error="missing_recipient",
        )
    if not message_text:
        return ToolResult(
            success=False,
            message="Please provide the message content.",
            error="missing_message",
        )
    if not schedule_at_raw:
        return ToolResult(
            success=False,
            message="Please specify when to send the message (e.g., 'tomorrow 10am', '2025-07-15 14:00').",
            error="missing_schedule_time",
        )

    # Parse the schedule time
    scheduled_dt = _parse_datetime(schedule_at_raw)
    if not scheduled_dt:
        return ToolResult(
            success=False,
            message=f"Could not parse the schedule time '{schedule_at_raw}'. Try formats like 'tomorrow 10am', 'July 15 2pm', or '2025-07-15 14:00'.",
            error="invalid_datetime",
        )

    if scheduled_dt <= datetime.utcnow():
        return ToolResult(
            success=False,
            message="Schedule time must be in the future.",
            error="past_datetime",
        )

    # Resolve entity
    entity_id = None
    entity = None
    if not re.match(r'^\+?\d{7,15}$', recipient.replace(" ", "").replace("-", "")):
        for etype in ("lead", "customer"):
            defn = _find_entity_def(tenant_id, etype)
            if not defn:
                continue
            if recipient.isdigit():
                entity = Entity.query.filter_by(
                    id=int(recipient), tenant_id=tenant_id,
                    definition_id=defn.id,
                ).first()
            if not entity:
                entity = Entity.query.filter(
                    Entity.tenant_id == tenant_id,
                    Entity.definition_id == defn.id,
                    Entity.data["name"].as_string().ilike(f"%{recipient}%"),
                ).first()
            if entity:
                entity_id = entity.id
                break

    # Store the scheduled message in entity data or create a schedule record
    # Using entity data's scheduled_messages field for persistence
    if entity_id:
        entity = Entity.query.get(entity_id)
        if entity:
            scheduled = entity.data.get("scheduled_messages", [])
            scheduled.append({
                "id": len(scheduled) + 1,
                "channel": channel,
                "recipient": recipient,
                "message": message_text,
                "scheduled_at": scheduled_dt.isoformat(),
                "created_by": user_id,
                "created_at": datetime.utcnow().isoformat(),
                "status": "pending",
            })
            entity.data["scheduled_messages"] = scheduled
            db.session.add(entity)

    # Log the scheduled message
    activity = ActivityLog(
        tenant_id=tenant_id,
        entity_id=entity_id,
        user_id=user_id,
        action="message_scheduled",
        detail=f"Message scheduled for {recipient} via {channel} at {scheduled_dt.isoformat()}",
        metadata_json={
            "channel": channel,
            "recipient": recipient,
            "scheduled_at": scheduled_dt.isoformat(),
            "message_preview": message_text[:200],
        },
    )
    db.session.add(activity)
    db.session.commit()

    return ToolResult(
        success=True,
        message=f"Message scheduled for {recipient} via {channel} at {scheduled_dt.strftime('%Y-%m-%d %H:%M UTC')}.",
        data={
            "channel": channel,
            "recipient": recipient,
            "scheduled_at": scheduled_dt.isoformat(),
            "message_preview": message_text[:200],
            "status": "pending",
        },
    )


def _parse_datetime(raw: str):
    """Parse a datetime string from natural language or ISO format."""
    raw = raw.strip().lower()

    # ISO format: 2025-07-15 14:00 or 2025-07-15T14:00
    iso_patterns = [
        r"(\d{4}-\d{2}-\d{2})[T ](\d{2}:\d{2})",
        r"(\d{4}-\d{2}-\d{2})",
    ]
    for pat in iso_patterns:
        m = re.search(pat, raw)
        if m:
            try:
                if len(m.groups()) == 2:
                    return datetime.strptime(f"{m.group(1)} {m.group(2)}", "%Y-%m-%d %H:%M")
                else:
                    return datetime.strptime(m.group(1), "%Y-%m-%d")
            except ValueError:
                pass

    # "tomorrow at 10am", "today at 2pm"
    now = datetime.utcnow()
    base = now

    if "tomorrow" in raw:
        base = now + timedelta(days=1)
    elif "next week" in raw:
        base = now + timedelta(days=7)
    elif "next month" in raw:
        # Approximate: 30 days
        base = now + timedelta(days=30)
    elif "today" in raw:
        base = now

    # Extract time
    time_match = re.search(r"(\d{1,2})(?::(\d{2}))?\s*(am|pm)", raw)
    if time_match:
        hour = int(time_match.group(1))
        minute = int(time_match.group(2)) if time_match.group(2) else 0
        ampm = time_match.group(3)
        if ampm == "pm" and hour < 12:
            hour += 12
        elif ampm == "am" and hour == 12:
            hour = 0
        return base.replace(hour=hour, minute=minute, second=0, microsecond=0)

    # "in 2 hours", "in 30 minutes"
    in_match = re.search(r"in\s+(\d+)\s*(hour|minute|hr|min)s?", raw)
    if in_match:
        amount = int(in_match.group(1))
        unit = in_match.group(2)
        if unit in ("hour", "hr"):
            return now + timedelta(hours=amount)
        elif unit in ("minute", "min"):
            return now + timedelta(minutes=amount)

    return None


register_tool(ToolDef(
    id="schedule_message",
    name="Schedule Message",
    description="Schedule a message for future delivery to a customer via WhatsApp, Telegram, or email.",
    category=ToolCategory.COMMUNICATION,
    permission=ToolPermission.WRITE,
    tier=2,
    handler=_schedule_message,
    parameters={
        "type": "object",
        "properties": {
            "to": {"type": "string", "description": "Recipient phone number, chat ID, or customer name"},
            "recipient": {"type": "string", "description": "Alias for 'to'"},
            "message": {"type": "string", "description": "The message text to send"},
            "text": {"type": "string", "description": "Alias for message"},
            "channel": {
                "type": "string",
                "description": "Channel to send on (default: whatsapp)",
                "enum": ["whatsapp", "telegram", "email"],
            },
            "schedule_at": {"type": "string", "description": "When to send (e.g., 'tomorrow 10am', '2025-07-15 14:00', 'in 2 hours')"},
            "at": {"type": "string", "description": "Alias for schedule_at"},
            "time": {"type": "string", "description": "Alias for schedule_at"},
        },
    },
    examples=[
        "schedule WhatsApp message to Sharma tomorrow 10am: Your Bali trip starts tomorrow!",
        "schedule email to lead 42 at 2025-07-15 14:00 with itinerary",
        "schedule message in 2 hours to +919876543210: Ready for your call?",
    ],
))