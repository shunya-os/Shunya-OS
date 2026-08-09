"""ACTIVATION-07: Human Command Layer — proposal decision API.

AI proposes. Only human disposes.

Endpoints:
    POST /proposals/{id}/approve  — human approves, system sends
    POST /proposals/{id}/reject   — human rejects
    POST /proposals/{id}/edit     — human edits message before approval
"""

from datetime import datetime, timezone

from flask import Blueprint, jsonify, request

from app import db
from app.communication.models import MessageProposal
from app.communication.registry import get_provider
from app.communication.safe_send import send_proposal

proposals_bp = Blueprint("proposals", __name__, url_prefix="/proposals")


def _serialize(p):
    return {
        "id": p.id,
        "to": p.to,
        "message": p.message,
        "status": p.status,
        "approved_by": p.approved_by,
        "approved_at": p.approved_at.isoformat() if p.approved_at else None,
        "sent_at": p.sent_at.isoformat() if p.sent_at else None,
        "edited_message": p.edited_message,
        "created_at": p.created_at.isoformat() if p.created_at else None,
    }


@proposals_bp.route("", methods=["GET"])
def list_proposals():
    """List all proposals, newest first."""
    proposals = MessageProposal.query.order_by(MessageProposal.id.desc()).all()
    return jsonify({"proposals": [_serialize(p) for p in proposals]})


@proposals_bp.route("/<int:proposal_id>", methods=["GET"])
def get_proposal(proposal_id):
    """Get a single proposal."""
    p = db.session.get(MessageProposal, proposal_id)
    if not p:
        return jsonify({"error": "Not found"}), 404
    return jsonify({"proposal": _serialize(p)})


@proposals_bp.route("/<int:proposal_id>/approve", methods=["POST"])
def approve_proposal(proposal_id):
    """Human approves a proposal. System sends the message immediately."""
    p = db.session.get(MessageProposal, proposal_id)
    if not p:
        return jsonify({"error": "Not found"}), 404

    if p.status != "pending":
        return jsonify({"error": f"Cannot approve — status is '{p.status}'"}), 400

    data = request.get_json(silent=True) or {}
    approved_by = data.get("approved_by", "human")

    # Use edited message if human edited it
    final_message = p.edited_message if p.edited_message else p.message

    # Mark as approved
    p.status = "approved"
    p.approved_by = approved_by
    p.approved_at = datetime.now(timezone.utc)

    # Send via the only allowed path: send_proposal()
    provider = get_provider()
    result = send_proposal(provider, p)

    # Mark sent with timestamp
    p.sent_at = datetime.now(timezone.utc)

    db.session.commit()

    return jsonify({
        "proposal": _serialize(p),
        "send_result": result,
    })


@proposals_bp.route("/<int:proposal_id>/reject", methods=["POST"])
def reject_proposal(proposal_id):
    """Human rejects a proposal. No message is sent."""
    p = db.session.get(MessageProposal, proposal_id)
    if not p:
        return jsonify({"error": "Not found"}), 404

    if p.status not in ("pending",):
        return jsonify({"error": f"Cannot reject — status is '{p.status}'"}), 400

    p.status = "rejected"
    db.session.commit()

    return jsonify({"proposal": _serialize(p)})


@proposals_bp.route("/<int:proposal_id>/edit", methods=["POST"])
def edit_proposal(proposal_id):
    """Human edits the message content of a pending proposal."""
    p = db.session.get(MessageProposal, proposal_id)
    if not p:
        return jsonify({"error": "Not found"}), 404

    if p.status != "pending":
        return jsonify({"error": f"Cannot edit — status is '{p.status}'"}), 400

    data = request.get_json(silent=True) or {}
    new_message = data.get("message", "")
    if not new_message:
        return jsonify({"error": "message is required"}), 400

    p.edited_message = new_message
    db.session.commit()

    return jsonify({"proposal": _serialize(p)})