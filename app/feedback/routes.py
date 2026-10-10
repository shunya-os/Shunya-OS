"""Feedback Routes — API endpoint for user feedback on recommendations.

Phase 5.4: POST /api/v1/feedback to record accepted/rejected recommendations.
"""

from __future__ import annotations

import logging

from flask import Blueprint, jsonify, request

from .models import Feedback

logger = logging.getLogger(__name__)

feedback_bp = Blueprint("feedback", __name__, url_prefix="/api/v1/feedback")


def _resolve_identity() -> dict:
    """Extract identity and tenant from the request context."""
    from flask import g, session

    identity_id = (
        session.get("identity_id")
        or session.get("user_id")
        or getattr(g, "identity_id", None)
        or request.headers.get("X-Identity-Id", "")
    )
    tenant_id = (
        session.get("current_org_id")
        or session.get("tenant_id")
        or getattr(g, "current_org_id", None)
        or request.headers.get("X-Tenant-Id", "")
    )
    return {
        "identity_id": str(identity_id) if identity_id else "",
        "tenant_id": str(tenant_id) if tenant_id else "",
    }


@feedback_bp.route("", methods=["POST"])
def api_create_feedback():
    """Record user feedback on a recommendation.

    Request body:
        signal_id (str, required): The proactive signal being rated.
        accepted (bool, required): True if accepted, False if rejected.
        comment (str, optional): Optional qualitative feedback text.

    Returns:
        201: Feedback recorded successfully.
        400: Missing required fields.
    """
    data = request.get_json(silent=True) or {}
    signal_id = (data.get("signal_id") or "").strip()
    accepted = data.get("accepted")

    if not signal_id:
        return jsonify({"success": False, "error": "signal_id is required"}), 400
    if accepted is None:
        return jsonify({"success": False, "error": "accepted (bool) is required"}), 400
    if not isinstance(accepted, bool):
        return jsonify({"success": False, "error": "accepted must be a boolean"}), 400

    identity = _resolve_identity()
    comment = (data.get("comment") or "").strip()

    feedback = Feedback(
        signal_id=signal_id,
        accepted=accepted,
        comment=comment,
        identity_id=identity["identity_id"],
        tenant_id=identity["tenant_id"],
    )

    from app import db
    db.session.add(feedback)
    db.session.commit()

    # Also feed back into the learning loop for continuous improvement
    try:
        from core.intelligence_runtime.learning import get_feedback_loop
        loop = get_feedback_loop()
        loop._loop.process_observation(
            observation=f"user_feedback:{signal_id}",
            expected_outcome="accepted",
            actual_outcome="accepted" if accepted else "rejected",
            identity_id=identity["identity_id"],
            tenant_id=identity["tenant_id"],
            source="user_feedback",
            metadata={"signal_id": signal_id, "comment": comment[:200]},
        )
    except Exception as exc:
        logger.debug("Feedback → learning loop bridge failed: %s", exc)

    logger.info(
        "Feedback recorded: signal=%s accepted=%s identity=%s",
        signal_id, accepted, identity.get("identity_id", "?"),
    )

    return jsonify({"success": True, "data": feedback.to_dict()}), 201


@feedback_bp.route("", methods=["GET"])
def api_list_feedback():
    """List feedback entries for a signal or all feedback."""
    signal_id = request.args.get("signal_id", "").strip()

    query = Feedback.query.order_by(Feedback.created_at.desc())
    if signal_id:
        query = query.filter_by(signal_id=signal_id)

    limit = min(int(request.args.get("limit", 50)), 200)
    feedback_list = query.limit(limit).all()

    return jsonify({
        "success": True,
        "data": [f.to_dict() for f in feedback_list],
        "count": len(feedback_list),
    })