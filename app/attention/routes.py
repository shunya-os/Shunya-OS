"""Attention API — tenant-scoped persistent operating intelligence endpoints.

All endpoints require authentication and are scoped by organization_id and
workspace_id extracted from the session or headers.

Endpoints:
    GET    /api/v1/attention/           — list active items
    GET    /api/v1/attention/<id>       — get single item with explanation
    POST   /api/v1/attention/<id>/dismiss — dismiss (with reason)
    POST   /api/v1/attention/<id>/resolve — mark resolved
"""
from flask import Blueprint, jsonify, session, request, g
from app.attention.models import AttentionItem, AttentionState
from app.attention import service as attention_service
from app.authz.decorators import require_permission

attention_bp = Blueprint("attention", __name__, url_prefix="/api/v1/attention")


def _resolve_org_id() -> int | None:
    """Resolve the current org id from session or g."""
    org_id = session.get("current_org_id") or getattr(g, "current_org_id", None)
    if org_id is not None:
        try:
            return int(org_id)
        except (ValueError, TypeError):
            return None
    return None


def _resolve_identity_id() -> str | None:
    """Resolve the current identity id."""
    return (
        session.get("identity_id")
        or session.get("user_id")
        or getattr(g, "identity_id", None)
        or request.headers.get("X-Identity-Id")
    )


def _resolve_workspace_id() -> str | None:
    """Resolve the current workspace id."""
    ws = (
        request.headers.get("X-Workspace-Id")
        or getattr(g, "workspace_id", None)
    )
    return str(ws) if ws else None


@attention_bp.route("/", methods=["GET"])
@require_permission("ai.use")
def list_attention():
    """List active attention items scoped to the current tenant."""
    org_id = _resolve_org_id()
    if not org_id:
        return jsonify({"error": "No organization context", "detail": "User must have an active organization"}), 403

    identity_id = _resolve_identity_id()
    workspace_id = _resolve_workspace_id()

    items = attention_service.list_active(
        organization_id=org_id,
        identity_id=identity_id,
        workspace_id=workspace_id,
    )
    return jsonify({
        "success": True,
        "data": [item.to_dict() for item in items],
        "count": len(items),
    })


@attention_bp.route("/<int:item_id>", methods=["GET"])
@require_permission("ai.use")
def get_attention(item_id: int):
    """Get a single attention item with explanation."""
    org_id = _resolve_org_id()
    if not org_id:
        return jsonify({"error": "No organization context"}), 403

    item = attention_service.get(item_id)
    if not item:
        return jsonify({"error": "Not found", "detail": f"Attention item {item_id} not found"}), 404

    # Tenant scope check
    if item.organization_id != org_id:
        return jsonify({"error": "Forbidden", "detail": "Item belongs to a different organization"}), 403

    result = item.to_dict()
    # Add human-readable explanation
    result["explanation"] = _build_explanation(item)

    return jsonify({"success": True, "data": result})


@attention_bp.route("/<int:item_id>/dismiss", methods=["POST"])
@require_permission("ai.use")
def dismiss_attention(item_id: int):
    """Dismiss an active attention item."""
    org_id = _resolve_org_id()
    if not org_id:
        return jsonify({"error": "No organization context"}), 403

    identity_id = _resolve_identity_id()
    if not identity_id:
        return jsonify({"error": "Authentication required"}), 401

    # Verify tenant scope
    item = attention_service.get(item_id)
    if not item:
        return jsonify({"error": "Not found", "detail": f"Attention item {item_id} not found"}), 404
    if item.organization_id != org_id:
        return jsonify({"error": "Forbidden", "detail": "Item belongs to a different organization"}), 403

    body = request.get_json(silent=True) or {}
    reason = body.get("reason", "")

    updated = attention_service.dismiss(item_id, dismissed_by=identity_id, reason=reason)
    if not updated:
        return jsonify({"error": "Not found"}), 404

    return jsonify({"success": True, "data": updated.to_dict()})


@attention_bp.route("/<int:item_id>/resolve", methods=["POST"])
@require_permission("ai.use")
def resolve_attention(item_id: int):
    """Resolve an active attention item."""
    org_id = _resolve_org_id()
    if not org_id:
        return jsonify({"error": "No organization context"}), 403

    identity_id = _resolve_identity_id()
    if not identity_id:
        return jsonify({"error": "Authentication required"}), 401

    # Verify tenant scope
    item = attention_service.get(item_id)
    if not item:
        return jsonify({"error": "Not found", "detail": f"Attention item {item_id} not found"}), 404
    if item.organization_id != org_id:
        return jsonify({"error": "Forbidden", "detail": "Item belongs to a different organization"}), 403

    updated = attention_service.resolve(item_id, resolved_by=identity_id)
    if not updated:
        return jsonify({"error": "Not found"}), 404

    return jsonify({"success": True, "data": updated.to_dict()})


def _build_explanation(item: AttentionItem) -> str:
    """Build a human-readable explanation for an attention item."""
    parts = []
    if item.reason:
        parts.append(item.reason)
    parts.append(
        f"Source: {item.source} | "
        f"Priority: {item.priority}/5"
        + (f" | Confidence: {item.confidence:.0%}" if item.confidence is not None else "")
    )
    if item.related_object_type and item.related_object_id:
        parts.append(f"Related: {item.related_object_type} #{item.related_object_id}")
    return " | ".join(parts)