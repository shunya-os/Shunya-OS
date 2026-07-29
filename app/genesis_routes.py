"""
SHUNYA OS — Genesis Protection Routes

Provides API endpoints for:
- Querying the immutable audit log
- Restoring soft-deleted records
- Confirming destructive actions

These are Genesis Preparation safeguards — not new features.
"""

from datetime import datetime, timezone
from flask import Blueprint, request, jsonify

from app import db
from app.genesis_protection import (
    AuditLog,
    record_audit_event,
    check_founder_protection,
    check_org_deletion_protection,
    require_confirmation,
)

genesis_bp = Blueprint("genesis", __name__, url_prefix="/api/v1/genesis")


# =========================================================================
# Audit Log — Read-Only Queries
# =========================================================================


@genesis_bp.route("/audit", methods=["GET"])
def list_audit_events():
    """List audit events with optional filtering.

    Query params:
    - actor_id: filter by actor
    - entity_type: filter by entity type (organization, workspace, identity, etc.)
    - operation: filter by operation name
    - limit: max results (default 50, max 200)
    - offset: pagination offset
    """
    query = AuditLog.query.order_by(AuditLog.occurred_at.desc())

    actor_id = request.args.get("actor_id")
    if actor_id:
        query = query.filter(AuditLog.actor_id == actor_id)

    entity_type = request.args.get("entity_type")
    if entity_type:
        query = query.filter(AuditLog.entity_type == entity_type)

    operation = request.args.get("operation")
    if operation:
        query = query.filter(AuditLog.operation == operation)

    limit = min(int(request.args.get("limit", 50)), 200)
    offset = int(request.args.get("offset", 0))

    total = query.count()
    events = query.offset(offset).limit(limit).all()

    return jsonify({
        "success": True,
        "data": [e.to_dict() for e in events],
        "pagination": {
            "total": total,
            "limit": limit,
            "offset": offset,
        },
    })


@genesis_bp.route("/audit/<event_id>", methods=["GET"])
def get_audit_event(event_id: str):
    """Get a single audit event by its event_id."""
    event = AuditLog.query.filter_by(event_id=event_id).first()
    if not event:
        return jsonify({"success": False, "error": "Audit event not found"}), 404
    return jsonify({"success": True, "data": event.to_dict()})


# =========================================================================
# Protection Checks
# =========================================================================


@genesis_bp.route("/protect/check-identity/<identity_id>", methods=["GET"])
def api_check_founder_protection(identity_id: str):
    """Check if a given identity can be safely removed or deactivated.

    Returns a protection block or confirms it's safe.
    """
    block = check_founder_protection(identity_id)
    if block:
        return jsonify({
            "success": False,
            "blocked": True,
            "data": block,
        })
    return jsonify({
        "success": True,
        "data": {"protected": False, "message": "Identity can be safely removed."},
    })


@genesis_bp.route("/protect/check-org-deletion/<int:org_id>", methods=["GET"])
def api_check_org_deletion(org_id: int):
    """Check the implications of deleting an organization."""
    actor_id = request.args.get("actor_id", "unknown")
    check = check_org_deletion_protection(org_id, actor_id)
    return jsonify({"success": True, "data": check})


# =========================================================================
# Confirmation Endpoint
# =========================================================================


@genesis_bp.route("/confirm", methods=["POST"])
def api_confirm_action():
    """Confirm a destructive action by providing the required input.

    Request body:
    {
        "prompt": "The confirmation prompt shown to the user",
        "user_input": "The user's typed response"
    }

    Returns {"confirmed": true/false}
    """
    data = request.get_json(silent=True) or {}
    prompt = data.get("prompt", "")
    user_input = data.get("user_input", "")
    result = require_confirmation(prompt, user_input)
    return jsonify({"success": result["confirmed"], "data": result})


# =========================================================================
# Soft Delete & Restore Endpoints
# =========================================================================


def _get_model_by_table(table_name: str):
    """Resolve a SQLAlchemy model class by table name."""
    for mapper in db.Model.registry.mappers:
        if mapper.class_.__tablename__ == table_name:
            return mapper.class_
    return None


@genesis_bp.route("/restore/<entity_type>/<entity_id>", methods=["POST"])
def api_restore_entity(entity_type: str, entity_id: str):
    """Restore a soft-deleted entity.

    Request body:
    {
        "restored_by": "identity_id of the person restoring"
    }
    """
    actor_id = request.args.get("actor_id", "") or (request.get_json(silent=True) or {}).get("restored_by", "")

    # Map entity types to their primary key column
    table_map = {
        "organization": "organizations",
        "workspace": "workspaces",
        "space": "founder_spaces",
        "object": "founder_objects",
        "relationship": "founder_relationships",
    }

    table_name = table_map.get(entity_type)
    if not table_name:
        return jsonify({"success": False, "error": f"Unknown entity type: {entity_type}"}), 400

    # Find the model and the record
    from app import db
    from sqlalchemy import text

    # Try to find by id (integer) first, then by string ID column
    try:
        entity_id_int = int(entity_id)
        result = db.session.execute(
            text(f'SELECT * FROM "{table_name}" WHERE id = :eid'),
            {"eid": entity_id_int},
        ).mappings().first()
    except ValueError:
        # String-based ID
        id_column = {"founder_spaces": "space_id", "founder_objects": "object_id",
                     "founder_relationships": "rel_id"}.get(table_name, "id")
        result = db.session.execute(
            text(f'SELECT * FROM "{table_name}" WHERE "{id_column}" = :eid'),
            {"eid": entity_id},
        ).mappings().first()

    if not result:
        return jsonify({"success": False, "error": f"{entity_type} not found"}), 404

    if not result.get("deleted_at"):
        return jsonify({"success": False, "error": f"{entity_type} is not deleted"}), 400

    # Restore by setting deleted_at to NULL
    now = datetime.now(timezone.utc)
    id_col = "id"
    record_id = result["id"]
    db.session.execute(
        text(f'UPDATE "{table_name}" SET deleted_at = NULL, deleted_by = NULL, '
             f'restored_at = :now, restored_by = :actor WHERE id = :eid'),
        {"now": now, "actor": actor_id, "eid": record_id},
    )

    # Also restore status if it was set to "deleted"
    if "status" in result and result.get("status") == "deleted":
        db.session.execute(
            text(f'UPDATE "{table_name}" SET status = \'active\' WHERE id = :eid'),
            {"eid": record_id},
        )

    db.session.commit()

    # Record the restoration in the audit log
    record_audit_event(
        actor_id=actor_id,
        entity_type=entity_type,
        entity_id=str(record_id),
        entity_name=result.get("name", result.get("space_id", "")),
        operation="restore",
        outcome="success",
        explanation=f"Restored {entity_type} #{record_id} from soft deletion.",
        restoration_status="restored",
    )

    return jsonify({
        "success": True,
        "data": {
            "entity_type": entity_type,
            "entity_id": entity_id,
            "restored": True,
            "restored_at": now.isoformat(),
            "restored_by": actor_id,
        },
    })

# Genesis Report Pages (public, no auth required)
import os as _os
import html as _html

_genesis_reports = {
    "preparation": "GENESIS_PREPARATION_REPORT.md",
    "backup": "DATABASE_BACKUP_REPORT.md",
    "reset": "GENESIS_RESET_REPORT.md",
    "protection": "FOUNDER_PROTECTION_REPORT.md",
    "data-protection": "DATA_PROTECTION_REPORT.md",
    "verification": "GENESIS_VERIFICATION_REPORT.md",
}

@genesis_bp.route("/report/<name>")
def genesis_report(name):
    filename = _genesis_reports.get(name)
    if not filename:
        return jsonify({"success": False, "error": "Report not found"}), 404
    repo_path = _os.path.join(_os.path.dirname(__file__), "..", filename)
    try:
        with open(repo_path) as f:
            content = f.read()
        escaped = _html.escape(content)
        return (
            f"""<!doctype html><html lang="en"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{name.replace('-',' ').title()} — SHUNYA Genesis</title>
<style>
body {{ font-family: system-ui, sans-serif; max-width: 800px; margin: 0 auto; padding: 2rem 1.5rem; line-height: 1.6; color: #191b1c; background: #fafaf8; }}
h1 {{ font-size: 1.8rem; font-weight: 300; }}
.nav {{ font-size: 0.8rem; color: rgba(0,0,0,.35); margin-bottom: 1.5rem; }}
.nav a {{ color: #aa8964; text-decoration: none; }}
pre {{ white-space: pre-wrap; word-wrap: break-word; font-family: 'JetBrains Mono', 'SF Mono', monospace; font-size: 0.85rem; line-height: 1.5; }}
</style></head><body>
<div class="nav"><a href="/genesis/">Genesis</a> / {name.replace('-',' ').title()}</div>
<pre>{escaped}</pre>
</body></html>"""
        )
    except Exception:
        return jsonify({"success": False, "error": "Report not found"}), 404