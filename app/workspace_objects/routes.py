"""FDA16-FDA19 — Unified Workspace Routes.

Single API surface for all workspace interactions:
- FDA16: Unified object workspace context
- FDA17: Unified timeline across all canonical sources
- FDA18: Contextual AI copilot
- FDA19: Commitment fulfillment workflow
"""

from __future__ import annotations

from flask import Blueprint, jsonify, request, session, g

workspace_api = Blueprint("workspace_api", __name__, url_prefix="/api/v1/workspace")

# ── Auth helpers ────────────────────────────────────────────────────


def _tenant_id() -> int:
    """Get the current tenant_id from session."""
    return session.get("current_org_id") or session.get("tenant_id", 0)


def _identity_id() -> str:
    """Get the current identity_id from session or header."""
    return (
        g.get("identity_id")
        or session.get("identity_id")
        or session.get("user_id", "anonymous")
    )


def _require_auth() -> bool:
    """Check if the user is authenticated."""
    return bool(_identity_id() and _tenant_id())


# ── FDA16: Unified Object Workspace ────────────────────────────────


@workspace_api.route("/objects/<object_id>", methods=["GET"])
def get_object_workspace(object_id: str):
    """Get the unified workspace context for any object.

    Query params:
        type: Optional type hint ('lead', 'customer', 'campaign', 'commitment', 'relationship')
    """
    if not _require_auth():
        return jsonify({"success": False, "error": "Authentication required"}), 401

    object_type = request.args.get("type", "")
    tenant = _tenant_id()

    try:
        from app.workspace_objects.service import get_unified_workspace
        workspace = get_unified_workspace(object_id, object_type, tenant)
        return jsonify({"success": True, "data": workspace})
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"Failed to load workspace: {str(e)}",
        }), 500


# ── FDA17: Unified Timeline ────────────────────────────────────────


@workspace_api.route("/timeline", methods=["GET"])
def get_unified_timeline():
    """Get unified timeline across all canonical sources for a context.

    Query params:
        object_type: Type of the context object
        object_id: ID of the context object
        relationship_id: Optional relationship ID to scope timeline
    """
    if not _require_auth():
        return jsonify({"success": False, "error": "Authentication required"}), 401

    object_type = request.args.get("object_type", "")
    object_id = request.args.get("object_id", "")
    relationship_id = request.args.get("relationship_id", type=int)
    tenant = _tenant_id()

    try:
        from app.workspace_objects.service import _get_timeline
        events = _get_timeline(object_type, object_id, relationship_id, tenant)
        return jsonify({"success": True, "data": events})
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"Failed to load timeline: {str(e)}",
        }), 500


# ── FDA17: Memory Timeline ─────────────────────────────────────────


@workspace_api.route("/timeline/memory", methods=["GET"])
def get_memory_timeline():
    """Get memory timeline with truth classifications."""
    if not _require_auth():
        return jsonify({"success": False, "error": "Authentication required"}), 401

    relationship_id = request.args.get("relationship_id", type=int)
    if not relationship_id:
        return jsonify({"success": False, "error": "relationship_id is required"}), 400

    try:
        from app import db
        from app.memory.models import MemoryRecord
        from app.relationship.models import RelationshipMemory

        memories = (
            db.session.query(MemoryRecord)
            .filter_by(relationship_id=relationship_id, status="active")
            .order_by(MemoryRecord.created_at.desc())
            .limit(50)
            .all()
        )

        data = []
        for m in memories:
            data.append({
                "id": m.id,
                "memory_key": m.memory_key,
                "value": m.value,
                "memory_type": m.memory_type,
                "truth_classification": m.truth_classification,
                "source": m.scope_type,
                "confidence": None,  # derived from truth classification
                "created_at": m.created_at.isoformat() if m.created_at else None,
            })

        return jsonify({"success": True, "data": data})
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e),
        }), 500


# ── FDA18: Contextual AI Copilot ───────────────────────────────────


@workspace_api.route("/copilot/ask", methods=["POST"])
def copilot_ask():
    """Ask SHUNYA a contextual question about the current object.

    Body:
        query: The user's question
        object_type: Type of the context object
        object_id: ID of the context object
        relationship_id: Optional relationship ID
    """
    if not _require_auth():
        return jsonify({"success": False, "error": "Authentication required"}), 401

    data = request.get_json(silent=True) or {}
    query = (data.get("query") or "").strip()
    if not query:
        return jsonify({"success": False, "error": "query is required"}), 400

    object_type = data.get("object_type", "")
    object_id = data.get("object_id", "")
    relationship_id = data.get("relationship_id")
    tenant = _tenant_id()

    try:
        from app.workspace_objects.copilot import answer_contextual
        result = answer_contextual(query, object_type, object_id, relationship_id, tenant)
        return jsonify({
            "success": True,
            "data": result,
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e),
        }), 500


@workspace_api.route("/copilot/context", methods=["GET"])
def copilot_context():
    """Get the current copilot context for an object."""
    if not _require_auth():
        return jsonify({"success": False, "error": "Authentication required"}), 401

    object_type = request.args.get("object_type", "")
    object_id = request.args.get("object_id", "")
    tenant = _tenant_id()

    try:
        from app.workspace_objects.service import get_unified_workspace
        workspace = get_unified_workspace(object_id, object_type, tenant)
        return jsonify({"success": True, "data": workspace})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# ── FDA19: Commitment Fulfilment ───────────────────────────────────


@workspace_api.route("/commitments/<int:commitment_id>", methods=["GET"])
def get_commitment_detail(commitment_id: int):
    """Get full commitment detail with execution history."""
    if not _require_auth():
        return jsonify({"success": False, "error": "Authentication required"}), 401

    try:
        from app import db
        from app.commitments.models import Commitment

        c = db.session.query(Commitment).filter_by(id=commitment_id).first()
        if not c:
            return jsonify({"success": False, "error": "Commitment not found"}), 404

        data = {
            "id": c.id,
            "title": c.title,
            "owner": c.owner,
            "status": c.status,
            "due_at": c.due_at.isoformat() if c.due_at else None,
            "issue_type": c.issue_type,
            "relationship_id": c.relationship_id,
            "campaign_id": c.campaign_id,
            "meta": c.meta or {},
            "created_at": c.created_at.isoformat() if c.created_at else None,
            "updated_at": c.updated_at.isoformat() if c.updated_at else None,
        }

        # Get related timeline events
        from app.relationship.models import TimelineEntry
        timeline = (
            db.session.query(TimelineEntry)
            .filter_by(relationship_id=c.relationship_id)
            .order_by(TimelineEntry.event_time.desc())
            .limit(20)
            .all()
        )
        data["timeline"] = [
            {
                "id": t.id,
                "event_type": t.event_type,
                "title": t.title,
                "event_time": t.event_time.isoformat() if t.event_time else None,
            }
            for t in timeline
        ]

        return jsonify({"success": True, "data": data})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@workspace_api.route("/commitments/<int:commitment_id>/transition", methods=["POST"])
def transition_commitment(commitment_id: int):
    """Transition a commitment to a new state.

    Body:
        status: New status (pending → in_progress → completed → failed)
        evidence: Optional evidence description
    """
    if not _require_auth():
        return jsonify({"success": False, "error": "Authentication required"}), 401

    data = request.get_json(silent=True) or {}
    new_status = data.get("status", "").strip()
    valid_states = ["pending", "in_progress", "completed", "failed", "blocked", "cancelled"]

    if new_status not in valid_states:
        return jsonify({"success": False, "error": f"Invalid status. Valid: {', '.join(valid_states)}"}), 400

    try:
        from app import db
        from app.commitments.models import Commitment

        c = db.session.query(Commitment).filter_by(id=commitment_id).first()
        if not c:
            return jsonify({"success": False, "error": "Commitment not found"}), 404

        # Valid state transitions
        transitions = {
            "pending": ["in_progress", "cancelled"],
            "in_progress": ["completed", "failed", "blocked"],
            "blocked": ["in_progress", "cancelled"],
            "completed": [],
            "failed": [],
            "cancelled": [],
        }

        allowed = transitions.get(c.status, [])
        if new_status not in allowed:
            return jsonify({
                "success": False,
                "error": f"Cannot transition from '{c.status}' to '{new_status}'. Allowed: {allowed}"
            }), 400

        old_status = c.status
        c.status = new_status
        db.session.commit()

        # Log timeline entry
        evidence = data.get("evidence", "")
        title = f"Commitment '{c.title}' changed from {old_status} → {new_status}"
        if evidence:
            title += f": {evidence}"

        from app.relationship.models import TimelineEntry
        from datetime import datetime, timezone
        entry = TimelineEntry(
            organization_id=_tenant_id(),
            relationship_id=c.relationship_id or 0,
            event_type=f"commitment.{new_status}",
            event_time=datetime.now(timezone.utc),
            title=title,
            description=evidence,
            reference_type="commitment",
            reference_id=c.id,
            created_by=_identity_id(),
        )
        db.session.add(entry)
        db.session.commit()

        return jsonify({
            "success": True,
            "data": {
                "id": c.id,
                "title": c.title,
                "status": c.status,
                "old_status": old_status,
                "transition": f"{old_status} → {new_status}",
            }
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "error": str(e)}), 500


@workspace_api.route("/commitments", methods=["POST"])
def create_commitment():
    """Create a new commitment.

    Body:
        title: Required. What is being committed
        owner: Who owns the commitment
        due_at: ISO datetime for due date
        relationship_id: ID of the relationship (customer/person)
        campaign_id: Optional campaign ID
        issue_type: Type of commitment
        evidence: Optional evidence description
    """
    if not _require_auth():
        return jsonify({"success": False, "error": "Authentication required"}), 401

    data = request.get_json(silent=True) or {}
    title = (data.get("title") or "").strip()
    if not title:
        return jsonify({"success": False, "error": "title is required"}), 400

    try:
        from app import db
        from app.commitments.models import Commitment
        from datetime import datetime, timezone

        due_at = None
        if data.get("due_at"):
            try:
                due_at = datetime.fromisoformat(data["due_at"].replace("Z", "+00:00"))
            except (ValueError, AttributeError):
                pass

        c = Commitment(
            title=title,
            owner=data.get("owner", _identity_id()),
            due_at=due_at,
            status="pending",
            relationship_id=int(data["relationship_id"]) if data.get("relationship_id") and str(data["relationship_id"]).isdigit() else None,
            campaign_id=int(data["campaign_id"]) if data.get("campaign_id") and str(data["campaign_id"]).isdigit() else None,
            issue_type=data.get("issue_type", ""),
            meta=data.get("meta", {}),
        )
        db.session.add(c)
        db.session.flush()

        # Log timeline entry
        from app.relationship.models import TimelineEntry
        entry = TimelineEntry(
            organization_id=_tenant_id(),
            relationship_id=c.relationship_id or 0,
            event_type="commitment.created",
            event_time=datetime.now(timezone.utc),
            title=f"Commitment created: {title}",
            description=data.get("evidence", ""),
            reference_type="commitment",
            reference_id=c.id,
            created_by=_identity_id(),
        )
        db.session.add(entry)
        db.session.commit()

        return jsonify({
            "success": True,
            "data": {
                "id": c.id,
                "title": c.title,
                "status": c.status,
                "relationship_id": c.relationship_id,
            }
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "error": str(e)}), 500


# ── FDA16/20: Bootstrap — lightweight workspace startup payload ────


@workspace_api.route("/bootstrap", methods=["GET"])
def workspace_bootstrap():
    """Return the minimal workspace bootstrap payload.

    This is the canonical lightweight startup path for the frontend shell.
    It returns everything needed to render the initial workspace in one
    round-trip. Non-critical data (intelligence, analytics, full history)
    is loaded separately via background hydration.

    Returns:
        identity: current user identity
        org: current organization
        workspace: workspace context
        catalog: available experiences
        domains: organizational domains
    """
    if not _require_auth():
        return jsonify({"success": False, "error": "Authentication required"}), 401

    tenant = _tenant_id()
    identity = _identity_id()

    # Resolve org info
    org_name = ""
    org_created_at = ""
    from app.models import Organization
    org = Organization.query.get(tenant) if tenant else None
    if org:
        org_name = org.name
        org_created_at = org.created_at.isoformat() if org.created_at else ""

    # Lightweight catalog (no DB queries for experience data)
    from app.workspace.models import EXPERIENCE_CATALOG, CONTEXT_MODES
    catalog = [{"key": k, "label": v.get("label", k), "category": v.get("category", "")}
               for k, v in EXPERIENCE_CATALOG.items()]
    contexts = [{"key": k, "label": v.get("label", k)} for k, v in CONTEXT_MODES.items()]

    return jsonify({
        "success": True,
        "data": {
            "identity": {"id": identity},
            "org": {"id": tenant, "name": org_name, "created_at": org_created_at},
            "catalog": catalog,
            "contexts": contexts,
            "domains": [
                {"id": "people", "label": "People"},
                {"id": "conversations", "label": "Conversations"},
                {"id": "work", "label": "Work"},
                {"id": "commercial", "label": "Commercial"},
                {"id": "marketing", "label": "Marketing"},
                {"id": "sales", "label": "Sales"},
                {"id": "knowledge", "label": "Knowledge"},
                {"id": "outputs", "label": "Outputs"},
                {"id": "memory", "label": "Memory"},
                {"id": "content", "label": "Content"},
                {"id": "entities", "label": "Entities"},
            ],
        }
    })


# ── FDA16/20: Health ────────────────────────────────────────────────


@workspace_api.route("/health", methods=["GET"])
def workspace_health():
    """Health check for the workspace API."""
    return jsonify({
        "status": "ok",
        "service": "workspace-api",
        "version": "1.0.0",
        "endpoints": [
            "GET /api/v1/workspace/objects/<id>",
            "GET /api/v1/workspace/timeline",
            "GET /api/v1/workspace/timeline/memory",
            "POST /api/v1/workspace/copilot/ask",
            "GET /api/v1/workspace/copilot/context",
            "GET /api/v1/workspace/commitments/<id>",
            "POST /api/v1/workspace/commitments/<id>/transition",
            "POST /api/v1/workspace/commitments",
        ],
    })