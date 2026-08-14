"""EP-02 — Living Object Composer API.

Single canonical creation endpoint: POST /api/v1/composer

All creation requests — Command Surface, Modal, AI, API, Import, Automation —
eventually reach this endpoint. No duplicated creation logic.
"""

from flask import Blueprint, jsonify, request, g
import json

from app.object_composer.composer import (
    get_composer, ComposerIntent, ObjectType,
)

composer_bp = Blueprint("composer", __name__, url_prefix="/api/v1/composer")


def _require_identity():
    identity_id = getattr(g, 'identity_id', None)
    if identity_id:
        return identity_id
    identity_id = request.headers.get("X-Identity-Id")
    return identity_id


@composer_bp.route("", methods=["POST"])
def compose():
    """POST /api/v1/composer — create any Living Object.

    The single canonical creation endpoint for SHUNYA.

    Accepts:
      Structured JSON: { object_type, name, description, fields, ... }
      Natural language: { raw: "Create proposal for Acme Corp" }
      Form data: multipart form with named fields

    Returns the canonical Living Object with identity, relationships,
    commitments, and reality event reference.
    """
    identity_id = _require_identity()
    if not identity_id:
        return jsonify({"success": False, "error": "Authentication required"}), 401

    data = request.get_json(silent=True) or {}
    composer = get_composer()
    source = data.get("source", "manual")

    # Determine input type
    raw = data.get("raw", "").strip()
    structured = data.get("object_type", "").strip()

    if raw:
        # Natural language input
        result = composer.compose_from_text(raw, source=source)
    elif structured:
        # Structured form input
        intent = ComposerIntent(
            raw_input=json.dumps(data),
            object_type=ObjectType(data["object_type"]),
            name=data.get("name", "").strip(),
            description=data.get("description", ""),
            related_object_ids=data.get("related_object_ids", []),
            related_entity_names=data.get("related_entity_names", []),
            commitments=data.get("commitments", []),
            fields=data.get("fields", {}),
            source=source,
        )
        result = composer.compose(intent)
    else:
        return jsonify({"success": False, "error": "Provide 'raw' (natural language) or 'object_type' + 'name'"}), 400

    if not result.success:
        return jsonify({"success": False, "error": result.error}), 500

    return jsonify({
        "success": True,
        "data": {
            "object_id": result.object_id,
            "object_type": result.object_type,
            "name": result.name,
            "relationships": result.relationship_ids,
            "commitments": result.commitment_ids,
            "event_id": result.event_id,
        },
    }), 201


@composer_bp.route("/parse", methods=["POST"])
def parse_intent():
    """POST /api/v1/composer/parse — parse natural language without creating.

    Returns the parsed intent for preview/confirmation before creation.
    """
    data = request.get_json(silent=True) or {}
    raw = data.get("raw", "").strip()
    if not raw:
        return jsonify({"success": False, "error": "'raw' field required"}), 400

    composer = get_composer()
    intent = composer._parser.parse(raw)

    return jsonify({
        "success": True,
        "data": {
            "object_type": intent.object_type.value,
            "name": intent.name,
            "description": intent.description,
            "has_relationships": len(intent.related_object_ids) > 0,
        },
    })