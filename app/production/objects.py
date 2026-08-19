"""SHUNYA — Object CRUD endpoints for the SPA create-object-modal.

Handles POST /api/v1/objects/<type> — creates typed business objects.
Routes are registered on production_bp (url_prefix = /api/v1).
"""

import uuid
from datetime import datetime

from flask import jsonify, request, g, session
from app import db
from app.production import production_bp
from app.auth_routes import login_required
from app.founder.models import FounderObject, FounderSpace


OBJECT_TYPES = {
    'customer': {
        'fields': ['company_name', 'contact_person', 'email', 'phone', 'address', 'gst_number', 'segment', 'preferred_channel'],
        'required': ['company_name'],
        'display_name': 'Customer',
    },
    'supplier': {
        'fields': ['company_name', 'contact_person', 'email', 'phone', 'address', 'gst_number'],
        'required': ['company_name'],
        'display_name': 'Supplier',
    },
    'lead': {
        'fields': ['company_name', 'contact_person', 'email', 'phone', 'source', 'status', 'budget'],
        'required': ['company_name'],
        'display_name': 'Lead',
    },
    'invoice': {
        'fields': ['company_name', 'invoice_number', 'amount', 'status', 'due_date', 'description'],
        'required': ['company_name', 'invoice_number'],
        'display_name': 'Invoice',
    },
    'task': {
        'fields': ['title', 'description', 'assignee', 'due_date', 'priority', 'status'],
        'required': ['title'],
        'display_name': 'Task',
    },
    'proposal': {
        'fields': ['company_name', 'proposal_title', 'amount', 'status', 'valid_until', 'description'],
        'required': ['company_name', 'proposal_title'],
        'display_name': 'Proposal',
    },
    'employee': {
        'fields': ['name', 'email', 'phone', 'department', 'role', 'start_date'],
        'required': ['name'],
        'display_name': 'Employee',
    },
    'meeting': {
        'fields': ['title', 'date', 'time', 'location', 'attendees', 'notes'],
        'required': ['title'],
        'display_name': 'Meeting',
    },
    'note': {
        'fields': ['title', 'content', 'related_to', 'tags'],
        'required': ['title'],
        'display_name': 'Note',
    },
    'document': {
        'fields': ['title', 'file_type', 'description', 'tags'],
        'required': ['title'],
        'display_name': 'Document',
    },
    'opportunity': {
        'fields': ['company_name', 'contact_person', 'value', 'stage', 'probability', 'expected_close'],
        'required': ['company_name'],
        'display_name': 'Opportunity',
    },
    'quote': {
        'fields': ['company_name', 'quote_number', 'amount', 'valid_until', 'terms'],
        'required': ['company_name', 'quote_number'],
        'display_name': 'Quote',
    },
    'email': {
        'fields': ['to', 'from', 'subject', 'body', 'status'],
        'required': ['subject'],
        'display_name': 'Email',
    },
    'whatsapp': {
        'fields': ['to', 'message', 'status', 'sent_at'],
        'required': ['message'],
        'display_name': 'WhatsApp',
    },
    'product': {
        'fields': ['name', 'description', 'price', 'category', 'sku'],
        'required': ['name'],
        'display_name': 'Product',
    },
    'payment': {
        'fields': ['amount', 'method', 'reference', 'status', 'paid_at'],
        'required': ['amount'],
        'display_name': 'Payment',
    },
    'expense': {
        'fields': ['description', 'amount', 'category', 'date', 'receipt'],
        'required': ['description', 'amount'],
        'display_name': 'Expense',
    },
    'campaign': {
        'fields': ['name', 'type', 'budget', 'start_date', 'end_date', 'status'],
        'required': ['name'],
        'display_name': 'Campaign',
    },
    'project': {
        'fields': ['name', 'description', 'start_date', 'end_date', 'status', 'budget'],
        'required': ['name'],
        'display_name': 'Project',
    },
    'reminder': {
        'fields': ['title', 'date', 'priority', 'status'],
        'required': ['title'],
        'display_name': 'Reminder',
    },
}


def _create_typed_object_raw(object_type: str, request_data: dict, identity_id: str) -> dict:
    """Create a typed business object without Flask route decorators.
    
    Used by both the API endpoint and the Outcome Engine (Z-07 Article III).
    Emits a canonical event through the EventBus for real-time awareness.
    """
    # Case-insensitive type lookup
    type_lower = object_type.lower()
    type_config = OBJECT_TYPES.get(type_lower)
    if not type_config:
        return {"success": False, "error": f"Unknown object type: {object_type}"}

    data = request_data
    
    # Validate required fields
    for field in type_config['required']:
        if not data.get(field):
            return {"success": False, "error": f"'{field}' is required."}

    # Build object name from first available field
    name_field = 'company_name' if 'company_name' in type_config['required'] else type_config['required'][0]
    name = data.get(name_field, '').strip()
    if not name:
        return {"success": False, "error": f"'{name_field}' is required."}

    # Find or create a default space
    space = FounderSpace.query.filter_by(identity_id=identity_id).first()
    if not space:
        space = FounderSpace(
            space_id=f"space_{uuid.uuid4().hex[:16]}",
            name="My Workspace",
            identity_id=identity_id,
            space_type="personal",
            status="active",
            member_count=1,
        )
        db.session.add(space)
        db.session.flush()

    obj_id = f"obj_{uuid.uuid4().hex[:16]}"
    obj = FounderObject(
        object_id=obj_id,
        space_id=space.space_id,
        name=name,
        object_type=type_config['display_name'],
        content=str({k: data.get(k, '') for k in type_config['fields']}),
        status="active",
        created_by=identity_id[:12],
    )
    db.session.add(obj)
    db.session.commit()

    # Emit canonical event through EventBus for real-time awareness
    try:
        from app.shunya.infrastructure.event_bus import CanonicalEvent, get_event_bus
        import json
        event = CanonicalEvent(
            event_type='object_created',
            tenant_id=0,  # Set by caller; 0 = unknown tenant
            workspace_id=None,
            actor_id=identity_id,
            actor_type='identity',
            actor_name='',
            object_id=obj_id,
            object_type=type_config['display_name'],
            payload={
                'name': name,
                'object_type': type_lower,
                'source': 'api_create',
            },
            confidence=1.0,
        )
        get_event_bus().publish(event)
    except Exception:
        pass  # Event emission is advisory — never break object creation

    return {
        "success": True,
        "data": {
            "id": obj.object_id,
            "object_id": obj.object_id,
            "name": obj.name,
            "company_name": data.get('company_name', ''),
            "type": type_config['display_name'],
        },
        "object_id": obj.object_id,
    }


@production_bp.route("/objects/<object_type>", methods=["POST"])
def create_typed_object(object_type: str):
    """Create a typed business object (customer, supplier, etc.)."""
    identity_id = session.get("identity_id") or session.get("user_id") or ""
    if not identity_id:
        return jsonify({"error": "Not authenticated"}), 401
    data = request.get_json(silent=True) or {}
    result = _create_typed_object_raw(object_type, data, str(identity_id))
    if result.get("success"):
        return jsonify(result), 201
    return jsonify(result), 400


@production_bp.route("/objects/<object_type>/<object_id>", methods=["PUT"])
def update_typed_object(object_type: str, object_id: str):
    """Update a typed business object."""
    identity_id = session.get("identity_id") or session.get("user_id") or ""
    if not identity_id:
        return jsonify({"error": "Not authenticated"}), 401
    data = request.get_json(silent=True) or {}
    
    obj = FounderObject.query.filter_by(object_id=object_id).first()
    if not obj:
        return jsonify({"error": "Object not found"}), 404
    
    type_lower = object_type.lower()
    type_config = OBJECT_TYPES.get(type_lower)
    if type_config:
        field_updates = {k: data.get(k, '') for k in type_config['fields']}
        # Update the content with merged fields
        import ast
        try:
            current = ast.literal_eval(obj.content) if obj.content else {}
        except:
            current = {}
        current.update({k: v for k, v in field_updates.items() if v})
        obj.content = str(current)
    
    if data.get('name'):
        obj.name = data['name']
    
    db.session.commit()
    return jsonify({"success": True, "data": {"object_id": obj.object_id, "name": obj.name}})


@production_bp.route("/objects/<object_type>/<object_id>", methods=["GET"])
def get_typed_object(object_type: str, object_id: str):
    """Get a typed business object."""
    identity_id = session.get("identity_id") or session.get("user_id") or ""
    if not identity_id:
        return jsonify({"error": "Not authenticated"}), 401
    
    obj = FounderObject.query.filter_by(object_id=object_id).first()
    if not obj:
        return jsonify({"success": False, "error": "Object not found"}), 404
    
    return jsonify({
        "success": True,
        "data": {
            "object_id": obj.object_id,
            "name": obj.name,
            "object_type": obj.object_type,
            "content": obj.content,
            "status": obj.status,
            "created_at": obj.created_at.isoformat() if obj.created_at else None,
            "updated_at": obj.updated_at.isoformat() if obj.updated_at else None,
        }
    })