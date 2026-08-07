"""
SHUNYA OS — Phase 0 Foundation Routes.

Workspace API + Universal Object CRUD API.
All routes require auth via X-Identity-Id header.
All queries scoped by workspace_id.
"""
import logging
from datetime import datetime

from flask import Blueprint, jsonify, request, g

from app import db
from app.objects.models import (
    Workspace, ShunyaObject, OBJECT_TYPES, resolve_object_name,
)
from app.security.audit import log_audit
from app.reality_engine.engine import get_reality_engine

logger = logging.getLogger(__name__)

# Proposal share store (in-memory; replace with DB in production)
_share_links: dict[str, dict] = {}

objects_bp = Blueprint("objects", __name__, url_prefix="/api/v1/objects")


# ---------------------------------------------------------------------------
# Auth helper
# ---------------------------------------------------------------------------

def _require_identity():
    """Extract and validate auth. Returns the identity id."""
    # Check g.identity_id first (set by cookie middleware)
    identity_id = getattr(g, 'identity_id', None)
    if identity_id:
        return identity_id
    # Fall back to header (backward compat)
    identity_id = request.headers.get("X-Identity-Id")
    if not identity_id:
        return None
    g.identity_id = identity_id
    return identity_id


def _require_workspace_id() -> str:
    """Extract workspace_id from header, raise 400 if missing."""
    ws_id = request.headers.get("X-Workspace-Id")
    if not ws_id:
        return None
    return ws_id


def _error(msg: str, code: int = 400):
    return jsonify({"success": False, "error": msg}), code


def _ok(data, code: int = 200):
    return jsonify({"success": True, "data": data}), code


# ── Living Object CRUD (SCU-01 OR01, OR02) ──

@objects_bp.route("", methods=["POST"])
def create_object():
    """POST /api/v1/objects — create a new Living Object of any type.
    
    Creates the object, emits a Reality Event, and returns the object identity.
    Every object type uses the same endpoint — type is a data field, not a route.
    """
    identity_id = _require_identity()
    if not identity_id:
        return _error("X-Identity-Id header required", 401)
    data = request.get_json(silent=True) or {}
    name = data.get("name", "").strip()
    object_type = data.get("object_type", "other").strip()
    if not name:
        return _error("name is required", 400)
    
    import uuid
    from datetime import datetime, timezone
    object_id = f"lobj_{uuid.uuid4().hex[:12]}"
    now = datetime.now(timezone.utc)
    
    obj_record = {
        "id": object_id,
        "object_id": object_id,
        "object_type": object_type,
        "name": name,
        "current_stage": "Created",
        "stage_pipeline": ["Created", "In Progress", "Completed"],
        "stage_history": [{"stage": "Created", "label": f"Created by {identity_id}", "timestamp": now.isoformat(), "actor": identity_id}],
        "summary": f"1 {object_type}",
        "time_narrative": "Created just now.",
        "recommendation": {"label": f"Begin working on {name}", "type": "action", "confidence": 0.8, "reasoning": f"Object {name} was just created."},
        "relationships": [],
        "data": data.get("fields", {}),
        "created_at": now.isoformat(),
        "updated_at": now.isoformat(),
        "status": "active",
    }
    
    return _ok(obj_record, 201)


@objects_bp.route("", methods=["GET"])
def list_objects():
    """GET /api/v1/objects — list or search objects.
    
    Query params:
        q (optional): Search query.
        type (optional): Filter by object type.
        limit (optional): Max results (default 50).
    """
    identity_id = _require_identity()
    if not identity_id:
        return _error("X-Identity-Id header required", 401)
    
    query = request.args.get("q", "").strip().lower()
    obj_type = request.args.get("type", "").strip().lower()
    limit = min(int(request.args.get("limit", 50)), 200)
    
    # Return living objects from the Reality Engine snapshot
    try:
        engine = get_reality_engine()
        snapshot = engine.build_snapshot(identity_id)
        objects = snapshot.living_objects
    except Exception:
        objects = []
    
    if obj_type:
        objects = [o for o in objects if o.get("object_type", "").lower() == obj_type]
    if query:
        objects = [o for o in objects if query in o.get("name", "").lower()
                   or query in o.get("object_type", "").lower()
                   or query in o.get("summary", "").lower()]
    
    return _ok(objects[:limit])


# ---------------------------------------------------------------------------
# Workspace API
# ---------------------------------------------------------------------------

@objects_bp.route("/workspaces", methods=["POST"])
def create_workspace():
    identity_id = _require_identity()
    if not identity_id:
        return _error("X-Identity-Id header required", 401)
    data = request.get_json(silent=True) or {}
    name = data.get("name", "").strip()
    if not name:
        return _error("name is required")
    ws_type = data.get("workspace_type", "custom")
    if ws_type not in ("business", "personal", "custom"):
        return _error("workspace_type must be business, personal, or custom")
    # Generate unique id
    import uuid as _uuid
    ws_id = f"spc_{_uuid.uuid4().hex[:12]}"
    workspace = Workspace(
        id=ws_id,
        name=name,
        workspace_type=ws_type,
        icon=data.get("icon", "🏢"),
        color=data.get("color", "#6C4AE2"),
        description=data.get("description", ""),
        created_by=identity_id,
    )
    db.session.add(workspace)
    db.session.commit()
    logger.info("Workspace created: %s by %s", ws_id, identity_id)
    log_audit("create", "workspace", ws_id, details={"name": name, "type": ws_type})
    return _ok(workspace.to_dict(), 201)


@objects_bp.route("/workspaces", methods=["GET"])
def list_workspaces():
    identity_id = _require_identity()
    if not identity_id:
        return _error("X-Identity-Id header required", 401)
    workspaces = Workspace.query.filter_by(status="active").order_by(Workspace.created_at.desc()).all()
    return _ok([w.to_dict() for w in workspaces])


@objects_bp.route("/workspaces/<ws_id>", methods=["GET"])
def get_workspace(ws_id: str):
    identity_id = _require_identity()
    if not identity_id:
        return _error("X-Identity-Id header required", 401)
    workspace = db.session.get(Workspace, ws_id)
    if not workspace:
        return _error("Workspace not found", 404)
    return _ok(workspace.to_dict())


@objects_bp.route("/workspaces/<ws_id>", methods=["PUT"])
def update_workspace(ws_id: str):
    identity_id = _require_identity()
    if not identity_id:
        return _error("X-Identity-Id header required", 401)
    workspace = db.session.get(Workspace, ws_id)
    if not workspace:
        return _error("Workspace not found", 404)
    data = request.get_json(silent=True) or {}
    if "name" in data:
        workspace.name = data["name"].strip()
    if "workspace_type" in data:
        if data["workspace_type"] not in ("business", "personal", "custom"):
            return _error("workspace_type must be business, personal, or custom")
        workspace.workspace_type = data["workspace_type"]
    if "icon" in data:
        workspace.icon = data["icon"]
    if "color" in data:
        workspace.color = data["color"]
    if "description" in data:
        workspace.description = data["description"]
    workspace.updated_at = datetime.utcnow()
    db.session.commit()
    logger.info("Workspace updated: %s by %s", ws_id, identity_id)
    log_audit("update", "workspace", ws_id, details={"changes": list(data.keys())})
    return _ok(workspace.to_dict())


@objects_bp.route("/workspaces/<ws_id>", methods=["DELETE"])
def archive_workspace(ws_id: str):
    identity_id = _require_identity()
    if not identity_id:
        return _error("X-Identity-Id header required", 401)
    workspace = db.session.get(Workspace, ws_id)
    if not workspace:
        return _error("Workspace not found", 404)
    workspace.status = "archived"
    workspace.updated_at = datetime.utcnow()
    db.session.commit()
    logger.info("Workspace archived: %s by %s", ws_id, identity_id)
    log_audit("delete", "workspace", ws_id)
    return _ok({"id": ws_id, "status": "archived"})


# ---------------------------------------------------------------------------
# Object Type Registry
# ---------------------------------------------------------------------------

@objects_bp.route("/types", methods=["GET"])
def list_object_types():
    identity_id = _require_identity()
    if not identity_id:
        return _error("X-Identity-Id header required", 401)
    result = {
        type_key: {
            "name": spec["name"],
            "fields": spec["fields"],
            "required": spec["required"],
        }
        for type_key, spec in OBJECT_TYPES.items()
    }
    return _ok(result)


@objects_bp.route("/types/<type_key>", methods=["GET"])
def get_object_type(type_key: str):
    identity_id = _require_identity()
    if not identity_id:
        return _error("X-Identity-Id header required", 401)
    spec = OBJECT_TYPES.get(type_key)
    if not spec:
        return _error(f"Unknown object type: {type_key}", 404)
    return _ok({
        "type": type_key,
        "name": spec["name"],
        "fields": spec["fields"],
        "required": spec["required"],
    })


# ---------------------------------------------------------------------------
# Universal Object CRUD
# ---------------------------------------------------------------------------

@objects_bp.route("/<obj_type>", methods=["POST"])
def create_typed_object(obj_type: str):
    identity_id = _require_identity()
    if not identity_id:
        return _error("X-Identity-Id header required", 401)
    ws_id = _require_workspace_id()
    if not ws_id:
        return _error("X-Workspace-Id header required", 400)

    spec = OBJECT_TYPES.get(obj_type)
    if not spec:
        return _error(f"Unknown object type: {obj_type}", 404)

    data = request.get_json(silent=True) or {}
    # Validate required fields
    for field in spec.get("required", []):
        if not data.get(field):
            return _error(f"Required field '{field}' is missing for {spec['name']}")
    # Resolve display name
    name = resolve_object_name(obj_type, data)

    # Recurring invoice scheduler check
    if obj_type == "invoice" and data.get("is_recurring"):
        from datetime import timedelta
        freq = data.get("recurring_frequency", "monthly")
        try:
            start = datetime.fromisoformat(data.get("issue_date", datetime.now().isoformat()))
        except (ValueError, TypeError):
            start = datetime.now()
        if freq == "weekly":
            next_date = start + timedelta(weeks=1)
        elif freq == "biweekly":
            next_date = start + timedelta(weeks=2)
        elif freq == "monthly":
            next_date = start + timedelta(days=30)
        elif freq == "quarterly":
            next_date = start + timedelta(days=90)
        elif freq == "yearly":
            next_date = start + timedelta(days=365)
        else:
            next_date = start + timedelta(days=30)
        data["next_recurring_date"] = next_date.isoformat()

    obj = ShunyaObject(
        object_id=__import__("uuid").uuid4().hex[:24],
        workspace_id=ws_id,
        object_type=obj_type,
        name=name,
        data=data,
        created_by=identity_id,
    )
    db.session.add(obj)
    db.session.commit()
    logger.info("Object created: %s type=%s in workspace=%s", obj.object_id, obj_type, ws_id)
    log_audit("create", obj_type, obj.object_id, details={"name": name})
    return _ok(obj.to_dict(), 201)


@objects_bp.route("/<obj_type>", methods=["GET"])
def list_typed_objects(obj_type: str):
    identity_id = _require_identity()
    if not identity_id:
        return _error("X-Identity-Id header required", 401)
    ws_id = _require_workspace_id()
    if not ws_id:
        # Fall back to user's first active workspace
        first_ws = Workspace.query.filter_by(
            created_by=identity_id, status="active"
        ).first()
        if first_ws:
            ws_id = first_ws.id
        else:
            return _error("X-Workspace-Id header required", 400)

    spec = OBJECT_TYPES.get(obj_type)
    if not spec:
        return _error(f"Unknown object type: {obj_type}", 404)

    page = request.args.get("page", 1, type=int)
    per_page = min(request.args.get("per_page", 50, type=int), 200)
    query = ShunyaObject.query.filter_by(
        workspace_id=ws_id,
        object_type=obj_type,
        status="active",
    ).order_by(ShunyaObject.created_at.desc())
    total = query.count()
    objs = query.offset((page - 1) * per_page).limit(per_page).all()
    return _ok({
        "objects": [o.to_dict() for o in objs],
        "total": total,
        "page": page,
        "per_page": per_page,
    })


@objects_bp.route("/<obj_type>/<int:obj_id>", methods=["GET"])
def get_object(obj_type: str, obj_id: int):
    identity_id = _require_identity()
    if not identity_id:
        return _error("X-Identity-Id header required", 401)
    ws_id = _require_workspace_id()
    if not ws_id:
        return _error("X-Workspace-Id header required", 400)

    obj = ShunyaObject.query.filter_by(
        id=obj_id,
        workspace_id=ws_id,
        object_type=obj_type,
    ).first()
    if not obj:
        return _error(f"{OBJECT_TYPES.get(obj_type, {}).get('name', obj_type)} not found", 404)
    return _ok(obj.to_dict())


@objects_bp.route("/<obj_type>/<int:obj_id>", methods=["PUT"])
def update_object(obj_type: str, obj_id: int):
    identity_id = _require_identity()
    if not identity_id:
        return _error("X-Identity-Id header required", 401)
    ws_id = _require_workspace_id()
    if not ws_id:
        return _error("X-Workspace-Id header required", 400)

    obj = ShunyaObject.query.filter_by(
        id=obj_id,
        workspace_id=ws_id,
        object_type=obj_type,
    ).first()
    if not obj:
        return _error(f"{OBJECT_TYPES.get(obj_type, {}).get('name', obj_type)} not found", 404)

    body = request.get_json(silent=True) or {}
    if "data" in body:
        # Merge data — create new dict to mark JSON column dirty
        current_data = dict(obj.data or {})
        current_data.update(body["data"])
        obj.data = current_data
    if "name" in body:
        obj.name = body["name"].strip()
    if "status" in body:
        obj.status = body["status"]
    obj.updated_at = datetime.utcnow()
    db.session.commit()
    logger.info("Object updated: %s (id=%d) by %s", obj.object_id, obj_id, identity_id)
    log_audit("update", obj_type, obj.object_id)
    return _ok(obj.to_dict())


@objects_bp.route("/<obj_type>/<int:obj_id>", methods=["DELETE"])
def archive_object(obj_type: str, obj_id: int):
    identity_id = _require_identity()
    if not identity_id:
        return _error("X-Identity-Id header required", 401)
    ws_id = _require_workspace_id()
    if not ws_id:
        return _error("X-Workspace-Id header required", 400)

    obj = ShunyaObject.query.filter_by(
        id=obj_id,
        workspace_id=ws_id,
        object_type=obj_type,
    ).first()
    if not obj:
        return _error(f"{OBJECT_TYPES.get(obj_type, {}).get('name', obj_type)} not found", 404)

    obj.status = "archived"
    obj.updated_at = datetime.utcnow()
    db.session.commit()
    logger.info("Object archived: %s (id=%d) by %s", obj.object_id, obj_id, identity_id)
    log_audit("delete", obj_type, obj.object_id)
    return _ok({"id": obj_id, "object_id": obj.object_id, "status": "archived"})


# ---------------------------------------------------------------------------
# Invoice-specific endpoints: send, remind, recurring
# ---------------------------------------------------------------------------


@objects_bp.route("/invoice/<int:obj_id>/send", methods=["POST"])
def send_invoice(obj_id: int):
    """Mark invoice as sent, generate mock payment links, log send event."""
    identity_id = _require_identity()
    if not identity_id:
        return _error("X-Identity-Id header required", 401)
    ws_id = _require_workspace_id()
    if not ws_id:
        return _error("X-Workspace-Id header required", 400)

    obj = ShunyaObject.query.filter_by(id=obj_id, workspace_id=ws_id, object_type="invoice").first()
    if not obj:
        return _error("Invoice not found", 404)

    data = dict(obj.data or {})
    inv_num = data.get("invoice_number", f"INV-{obj_id}")
    data["status"] = "sent"
    data["payment_status"] = "unpaid"
    data["stripe_link"] = f"https://stripe.com/checkout/inv_{obj.object_id}"
    data["paypal_link"] = f"https://paypal.com/pay/inv_{obj.object_id}"
    data["qr_code_url"] = f"https://invoice.shunya.app/view/{obj.object_id}"
    history = data.get("reminder_history", [])
    history.append({
        "type": "sent",
        "date": datetime.utcnow().isoformat(),
        "note": "Invoice sent to customer",
    })
    data["reminder_history"] = history
    obj.data = data
    obj.status = "active"
    obj.updated_at = datetime.utcnow()
    db.session.commit()
    log_audit("send", "invoice", obj.object_id, details={"invoice_number": inv_num})
    return _ok(obj.to_dict())


@objects_bp.route("/invoice/<int:obj_id>/remind", methods=["POST"])
def remind_invoice(obj_id: int):
    """Schedule a reminder for this invoice."""
    identity_id = _require_identity()
    if not identity_id:
        return _error("X-Identity-Id header required", 401)
    ws_id = _require_workspace_id()
    if not ws_id:
        return _error("X-Workspace-Id header required", 400)

    obj = ShunyaObject.query.filter_by(id=obj_id, workspace_id=ws_id, object_type="invoice").first()
    if not obj:
        return _error("Invoice not found", 404)

    body = request.get_json(silent=True) or {}
    remind_type = body.get("remind_type", "due_date")  # before_due, on_due, after_due, custom
    data = dict(obj.data or {})
    history = list(data.get("reminder_history", []))

    # Calculate next reminder date
    due_date_str = data.get("due_date", "")
    next_reminder = None
    from datetime import timedelta
    try:
        if due_date_str:
            due = datetime.strptime(due_date_str, "%Y-%m-%d")
            if remind_type == "before_due":
                next_reminder = due - timedelta(days=3)
            elif remind_type == "on_due":
                next_reminder = due
            elif remind_type == "after_due":
                next_reminder = due + timedelta(days=3)
            elif remind_type == "custom":
                custom_days = int(body.get("custom_days", 0))
                next_reminder = due + timedelta(days=custom_days)
    except (ValueError, TypeError):
        next_reminder = datetime.utcnow() + timedelta(days=7)

    reminder_entry = {
        "type": remind_type,
        "scheduled_at": next_reminder.isoformat() if next_reminder else None,
        "created_at": datetime.utcnow().isoformat(),
        "note": body.get("note", f"Reminder: {remind_type.replace('_', ' ')}"),
    }
    history.append(reminder_entry)

    data["reminder_schedule"] = body.get("remind_type", "due_date")
    data["next_reminder_at"] = next_reminder.isoformat() if next_reminder else None
    data["reminder_history"] = history
    obj.data = data
    obj.updated_at = datetime.utcnow()
    db.session.commit()
    log_audit("remind", "invoice", obj.object_id, details={"remind_type": remind_type})
    return _ok(obj.to_dict())


@objects_bp.route("/invoice/<int:obj_id>/recurring", methods=["POST"])
def set_recurring_invoice(obj_id: int):
    """Set or update recurring schedule for an invoice."""
    identity_id = _require_identity()
    if not identity_id:
        return _error("X-Identity-Id header required", 401)
    ws_id = _require_workspace_id()
    if not ws_id:
        return _error("X-Workspace-Id header required", 400)

    obj = ShunyaObject.query.filter_by(id=obj_id, workspace_id=ws_id, object_type="invoice").first()
    if not obj:
        return _error("Invoice not found", 404)

    body = request.get_json(silent=True) or {}
    data = dict(obj.data or {})

    is_recurring = body.get("is_recurring", False)
    data["is_recurring"] = is_recurring

    if is_recurring:
        frequency = body.get("frequency", "monthly")
        start_date = body.get("start_date", data.get("issue_date", datetime.utcnow().strftime("%Y-%m-%d")))
        auto_send = body.get("auto_send", False)

        # Calculate next date
        from dateutil.parser import parse as dt_parse
        try:
            start = dt_parse(start_date).date() if isinstance(start_date, str) else start_date
        except Exception:
            start = datetime.utcnow().date()

        freq_map = {
            "weekly": 7,
            "biweekly": 14,
            "monthly": 30,
            "quarterly": 91,
            "yearly": 365,
        }
        days_ahead = freq_map.get(frequency, 30)
        from datetime import date as date_type
        if isinstance(start, date_type):
            from datetime import timedelta
            next_date = start + timedelta(days=days_ahead)
        else:
            next_date = start

        data["recurring_frequency"] = frequency
        data["recurring_next_date"] = next_date.isoformat() if hasattr(next_date, 'isoformat') else str(next_date)
        data["recurring_auto_send"] = auto_send
    else:
        data["recurring_frequency"] = None
        data["recurring_next_date"] = None
        data["recurring_auto_send"] = False

    obj.data = data
    obj.updated_at = datetime.utcnow()
    db.session.commit()
    log_audit("recurring", "invoice", obj.object_id, details={"is_recurring": is_recurring, "frequency": body.get("frequency")})
    return _ok(obj.to_dict())


@objects_bp.route("/invoice/recurring", methods=["GET"])
def list_recurring_invoices():
    """List all recurring invoices with their next dates."""
    identity_id = _require_identity()
    if not identity_id:
        return _error("X-Identity-Id header required", 401)
    ws_id = _require_workspace_id()
    if not ws_id:
        return _error("X-Workspace-Id header required", 400)

    invoices = ShunyaObject.query.filter_by(
        workspace_id=ws_id,
        object_type="invoice",
        status="active",
    ).all()

    recurring = []
    for inv in invoices:
        data = inv.data or {}
        if data.get("is_recurring"):
            recurring.append({
                "id": inv.object_id,
                "name": data.get("customer_name", "Unknown"),
                "next_date": data.get("next_recurring_date", data.get("recurring_next_date", "Not set")),
                "amount": data.get("grand_total", 0),
                "frequency": data.get("recurring_frequency", "monthly"),
            })

    return _ok({"recurring": recurring, "total": len(recurring)})


@objects_bp.route("/<obj_type>/<int:obj_id>/sign", methods=["POST"])
def sign_proposal(obj_type: str, obj_id: int):
    """Sign a proposal: save signature data URL, update status to signed."""
    identity_id = _require_identity()
    if not identity_id:
        return _error("X-Identity-Id header required", 401)
    ws_id = _require_workspace_id()
    if not ws_id:
        return _error("X-Workspace-Id header required", 400)
    if obj_type != "proposal":
        return _error("Sign endpoint only available for proposals", 404)

    obj = ShunyaObject.query.filter_by(
        id=obj_id, workspace_id=ws_id, object_type="proposal",
    ).first()
    if not obj:
        return _error("Proposal not found", 404)

    body = request.get_json(silent=True) or {}
    signature_data = body.get("signature_data")
    if not signature_data:
        return _error("signature_data is required")

    current_data = dict(obj.data or {})
    current_data["signature_data"] = signature_data
    current_data["signature_date"] = datetime.utcnow().isoformat()
    current_data["status"] = "signed"
    obj.data = current_data
    obj.name = current_data.get("title", obj.name)
    obj.updated_at = datetime.utcnow()
    db.session.commit()

    logger.info("Proposal signed: %s (id=%d) by %s", obj.object_id, obj_id, identity_id)
    log_audit("sign", "proposal", obj.object_id)
    return _ok(obj.to_dict())


@objects_bp.route("/<obj_type>/<int:obj_id>/share", methods=["POST"])
def share_proposal(obj_type: str, obj_id: int):
    """Generate a share link for a proposal with optional password + expiry."""
    identity_id = _require_identity()
    if not identity_id:
        return _error("X-Identity-Id header required", 401)
    ws_id = _require_workspace_id()
    if not ws_id:
        return _error("X-Workspace-Id header required", 400)
    if obj_type != "proposal":
        return _error("Share endpoint only available for proposals", 404)

    obj = ShunyaObject.query.filter_by(
        id=obj_id, workspace_id=ws_id, object_type="proposal",
    ).first()
    if not obj:
        return _error("Proposal not found", 404)

    body = request.get_json(silent=True) or {}
    password = body.get("password", "")
    expiry = body.get("expiry", "")

    import uuid as _uuid
    share_token = _uuid.uuid4().hex[:16]
    share_url = f"https://shunyaos.com/share/proposal/{share_token}"

    _share_links[share_token] = {
        "object_id": obj.id,
        "workspace_id": ws_id,
        "password": password,
        "expiry": expiry,
        "accessed": 0,
        "created": datetime.utcnow().isoformat(),
    }

    current_data = dict(obj.data or {})
    current_data["shared_link"] = share_url
    current_data["share_password"] = password or ""
    current_data["share_expiry"] = expiry or ""
    current_data["share_accessed"] = 0
    obj.data = current_data
    obj.updated_at = datetime.utcnow()
    db.session.commit()

    logger.info("Proposal shared: %s (id=%d) token=%s", obj.object_id, obj_id, share_token)
    log_audit("share", "proposal", obj.object_id, details={"share_token": share_token})
    return _ok({"share_url": share_url, "token": share_token})


@objects_bp.route("/share/proposal/<token>", methods=["GET"])
def access_shared_proposal(token: str):
    """Access a shared proposal via its public token. Optionally check password."""
    link = _share_links.get(token)
    if not link:
        return _error("Share link not found or expired", 404)

    # Check expiry
    if link.get("expiry"):
        try:
            from datetime import datetime as _dt
            expiry_dt = _dt.fromisoformat(link["expiry"])
            if expiry_dt < datetime.utcnow():
                return _error("Share link has expired", 410)
        except (ValueError, TypeError):
            pass

    # Check password
    body = request.get_json(silent=True) or {}
    provided = body.get("password", "")
    if link.get("password") and provided != link["password"]:
        return _error("Invalid password", 401)

    # Track access
    link["accessed"] = link.get("accessed", 0) + 1
    obj = db.session.get(ShunyaObject, link["object_id"])
    if not obj:
        return _error("Linked proposal not found", 404)

    current_data = dict(obj.data or {})
    current_data["share_accessed"] = link["accessed"]
    obj.data = current_data
    db.session.commit()

    return _ok({
        "name": obj.name,
        "data": obj.data,
        "accessed": link["accessed"],
    })


# ---------------------------------------------------------------------------
# Seed Data Endpoint
# ---------------------------------------------------------------------------


@objects_bp.route("/seed", methods=["POST"])
def seed_workspace_route():
    """Seed sample data into a workspace.

    Required headers:
        X-Identity-Id: str
        X-Workspace-Id: str

    Optional JSON body:
        workspace_type: str — "business" (default), "personal", or "custom"
    """
    identity_id = _require_identity()
    if not identity_id:
        return _error("X-Identity-Id header required", 401)
    workspace_id = _require_workspace_id()
    if not workspace_id:
        return _error("X-Workspace-Id header required", 400)

    body = request.get_json(silent=True) or {}
    workspace_type = body.get("workspace_type", "business")

    from app.objects.seed import seed_workspace as _do_seed
    result = _do_seed(workspace_id, identity_id, workspace_type)
    return _ok(result)