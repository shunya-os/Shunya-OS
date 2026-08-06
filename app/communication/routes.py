"""EP-04 — Universal Communication Runtime API.

Single endpoint group: /api/v1/communication
All communication flows through the runtime — no direct provider access.
"""

import json
from flask import Blueprint, jsonify, request, g

from .runtime import get_communication_runtime
from .conversation import ChannelType

comm_bp = Blueprint("communication", __name__, url_prefix="/api/v1/communication")


def _require_identity():
    identity_id = getattr(g, 'identity_id', None)
    if identity_id:
        return identity_id
    identity_id = request.headers.get("X-Identity-Id")
    return identity_id


@comm_bp.route("/conversations", methods=["POST"])
def create_conversation():
    """POST /api/v1/communication/conversations — create a new Conversation."""
    identity_id = _require_identity()
    if not identity_id:
        return jsonify({"success": False, "error": "Authentication required"}), 401

    data = request.get_json(silent=True) or {}
    title = data.get("title", "").strip()
    if not title:
        return jsonify({"success": False, "error": "title is required"}), 400

    rt = get_communication_runtime()
    conv = rt.get_or_create_conversation(
        title=title,
        participants=data.get("participants", []),
        channel=ChannelType(data.get("channel", "email")),
        company_ids=data.get("company_ids", []),
        project_ids=data.get("project_ids", []),
    )
    return jsonify({"success": True, "data": conv.to_dict()}), 201


@comm_bp.route("/conversations", methods=["GET"])
def list_conversations():
    """GET /api/v1/communication/conversations — list all conversations."""
    identity_id = _require_identity()
    if not identity_id:
        return jsonify({"success": False, "error": "Authentication required"}), 401

    rt = get_communication_runtime()
    convs = [c.to_dict() for c in rt.list_conversations()]
    return jsonify({"success": True, "data": convs})


@comm_bp.route("/conversations/<conv_id>", methods=["GET"])
def get_conversation(conv_id: str):
    """GET /api/v1/communication/conversations/<id> — full conversation detail."""
    identity_id = _require_identity()
    if not identity_id:
        return jsonify({"success": False, "error": "Authentication required"}), 401

    rt = get_communication_runtime()
    conv = rt.get_conversation(conv_id)
    if not conv:
        return jsonify({"success": False, "error": "Conversation not found"}), 404

    return jsonify({
        "success": True,
        "data": {
            **conv.to_dict(),
            "timeline": conv.timeline(),
            "summary": rt.generate_summary(conv_id),
        },
    })


@comm_bp.route("/conversations/<conv_id>/messages", methods=["POST"])
def send_message(conv_id: str):
    """POST /api/v1/communication/conversations/<id>/messages — send a message."""
    identity_id = _require_identity()
    if not identity_id:
        return jsonify({"success": False, "error": "Authentication required"}), 401

    data = request.get_json(silent=True) or {}
    body = data.get("body", "").strip()
    if not body:
        return jsonify({"success": False, "error": "body is required"}), 400

    rt = get_communication_runtime()
    msg = rt.send_message(
        conv_id,
        body=body,
        subject=data.get("subject", ""),
        channel=ChannelType(data.get("channel")) if data.get("channel") else None,
    )
    if not msg:
        return jsonify({"success": False, "error": "Failed to send message"}), 500

    return jsonify({"success": True, "data": msg.to_dict()}), 201


@comm_bp.route("/search", methods=["GET"])
def search_conversations():
    """GET /api/v1/communication/search?q= — unified search."""
    identity_id = _require_identity()
    if not identity_id:
        return jsonify({"success": False, "error": "Authentication required"}), 401

    query = request.args.get("q", "").strip()
    if not query:
        return jsonify({"success": False, "error": "q parameter required"}), 400

    rt = get_communication_runtime()
    results = rt.search(query)
    return jsonify({"success": True, "data": results})


@comm_bp.route("/summary/<conv_id>", methods=["GET", "POST"])
def conversation_summary(conv_id: str):
    """GET/POST /api/v1/communication/summary/<id> — AI summary."""
    identity_id = _require_identity()
    if not identity_id:
        return jsonify({"success": False, "error": "Authentication required"}), 401

    rt = get_communication_runtime()
    summary = rt.generate_summary(conv_id)
    return jsonify({"success": True, "data": {"summary": summary}})