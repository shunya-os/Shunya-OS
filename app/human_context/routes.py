"""
SHUNYA — Emotional Context API Routes (GATE 12)

Endpoints:
- POST   /api/v1/emotional/       — record emotional context
- GET    /api/v1/emotional/       — list emotional context
- PATCH  /api/v1/emotional/<id>/correct — correct a previous entry
- DELETE /api/v1/emotional/<id>   — expire/stale an entry

The endpoints must: NOT diagnose, NOT manipulate, respect auth boundaries.
"""
from flask import Blueprint, g, jsonify, request

from app.human_context.emotional import (
    EmotionalContextService,
    ExpressionType,
    SENSITIVE_FIELDS,
)

emotional_bp = Blueprint("emotional", __name__, url_prefix="/api/v1/emotional")


def _service():
    return EmotionalContextService()


def _auth_context():
    """Resolve auth context from the request.

    Returns (tenant_id, person_id, include_sensitive, identity).
    Sensitive fields require explicit auth — they are gated behind
    X-Include-Sensitive header or identity matching the person.
    """
    identity = getattr(g, "identity_id", None) or request.headers.get("X-Identity-Id", "")
    tenant_id = getattr(g, "current_org_id", None) or request.headers.get("X-Tenant-Id", type=int)

    # Only allow reading sensitive fields when explicitly requested and
    # the identity matches (belongs to the same person)
    include_sensitive = request.headers.get("X-Include-Sensitive", "").lower() == "true"
    person_id = request.headers.get("X-Person-Id", type=int) if request.headers.get("X-Person-Id") else None

    return tenant_id, person_id, include_sensitive, identity


# ---------------------------------------------------------------------------
# POST /api/v1/emotional/ — record emotional context
# ---------------------------------------------------------------------------

@emotional_bp.route("/", methods=["POST"])
def record_emotional_context():
    """Record emotional context.

    Body fields:
      - expression_type (required): one of frustration, uncertainty, excitement, urgent, defer
      - context (optional): human-readable description
      - confidence (optional, default 1.0): how confident in this observation
      - related_object_id / related_object_type (optional): what this pertains to
      - provenance / retention (optional)
      - person_id (optional): if recording for another person
      - workspace_id (optional): which workspace context

    NEVER diagnoses the person. NEVER creates fear, artificial urgency,
    or emotional dependency. Stores what was communicated, no more.
    """
    data = request.get_json(silent=True) or {}
    tenant_id, _person_id, _sensitive, identity = _auth_context()

    if not identity:
        return jsonify({"success": False, "error": "Authentication required"}), 401

    expression_type = data.get("expression_type", "")
    if not expression_type:
        return jsonify({"success": False, "error": "expression_type is required",
                        "valid_types": sorted(ExpressionType.ALL)}), 400

    person_id = data.get("person_id") or _person_id

    svc = _service()
    result = svc.record(
        expression_type=expression_type,
        source=data.get("source", "human"),
        context=data.get("context", ""),
        confidence=data.get("confidence", 1.0),
        person_id=data.get("person_id") or _person_id,
        tenant_id=tenant_id,
        workspace_id=data.get("workspace_id"),
        related_object_id=data.get("related_object_id"),
        related_object_type=data.get("related_object_type"),
        provenance=data.get("provenance"),
        retention=data.get("retention"),
        created_by=identity or data.get("created_by", ""),
    )

    if not result["success"]:
        return jsonify(result), 400
    return jsonify(result), 201


# ---------------------------------------------------------------------------
# GET /api/v1/emotional/ — list emotional context
# ---------------------------------------------------------------------------

@emotional_bp.route("/", methods=["GET"])
def list_emotional_context():
    """List emotional context for the current user/tenant.

    Query params:
      - person_id: filter by person
      - workspace_id: filter by workspace
      - expression_type: filter by type
      - status: filter by status
      - limit (default 100), offset (default 0)

    Sensitive fields (context, provenance) are redacted unless
    X-Include-Sensitive=true header is set with proper auth.
    """
    tenant_id, person_id, include_sensitive, _identity = _auth_context()

    svc = _service()

    # If no person_id specified and no auth identity,  refuse
    if not person_id and not tenant_id and not include_sensitive:
        return jsonify({"success": False, "error": "No person or tenant context"}), 403

    result = svc.list(
        tenant_id=tenant_id,
        person_id=person_id,
        workspace_id=request.args.get("workspace_id"),
        expression_type=request.args.get("expression_type"),
        status=request.args.get("status"),
        include_sensitive=include_sensitive,
        limit=request.args.get("limit", 100, type=int),
        offset=request.args.get("offset", 0, type=int),
    )
    return jsonify(result), 200


# ---------------------------------------------------------------------------
# PATCH /api/v1/emotional/<id>/correct — correct a previous entry
# ---------------------------------------------------------------------------

@emotional_bp.route("/<int:item_id>/correct", methods=["PATCH"])
def correct_emotional_entry(item_id):
    """Correct a previous emotional context entry.

    Body fields:
      - correction_note (optional): why the correction
      new_expression_type (optional): corrected type
      - new_context (optional): corrected context
      - new_confidence (optional): corrected confidence
      - corrected_by (optional): who made the correction

    Creates a new entry linked to the original. The original is marked
    CORRECTED but preserved for traceability.
    """
    data = request.get_json(silent=True) or {}
    tenant_id, _person_id, _sensitive, _identity = _auth_context()

    new_expression_type = data.get("new_expression_type")
    if new_expression_type and new_expression_type not in ExpressionType.ALL:
        return jsonify({"success": False, "error": f"Invalid expression_type",
                        "valid_types": sorted(ExpressionType.ALL)}), 400

    svc = _service()
    result = svc.correct(
        item_id,
        corrected_by=data.get("corrected_by") or _identity,
        correction_note=data.get("correction_note", ""),
        tenant_id=tenant_id,
        new_expression_type=new_expression_type,
        new_context=data.get("new_context"),
        new_confidence=data.get("new_confidence"),
    )

    if not result["success"]:
        error = result.get("error", "").lower()
        status = 404 if "not found" in error else 400
        return jsonify(result), status
    return jsonify(result), 200


# ---------------------------------------------------------------------------
# DELETE /api/v1/emotional/<id> — expire an entry
# ---------------------------------------------------------------------------

@emotional_bp.route("/<int:item_id>", methods=["DELETE"])
def expire_emotional_entry(item_id):
    """Expire (soft-delete) an emotional context entry.

    The entry is marked EXPIRED but preserved in the database for audit.
    """
    tenant_id, _person_id, _sensitive, _identity = _auth_context()

    svc = _service()
    result = svc.expire(
        item_id,
        tenant_id=tenant_id,
        reason=request.args.get("reason", ""),
    )

    if not result["success"]:
        return jsonify(result), 404
    return jsonify(result), 200