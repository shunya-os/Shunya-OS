"""Universal Business Discovery — API Routes."""

from flask import jsonify, request, session
from datetime import datetime, timezone
from app import db
from app.onboarding import onboarding_bp
from app.onboarding.engine import (
    get_or_create_session, reset_session,
    get_day_one_dashboard,
)


@onboarding_bp.route("/start", methods=["POST"])
def api_start_onboarding():
    """Begin or resume the onboarding conversation."""
    uid = session.get("identity_id") or session.get("user_id") or ""
    org_id = session.get("current_org_id")
    if not uid or not org_id:
        return jsonify({"error": "Not authenticated"}), 401

    session_eng = get_or_create_session(org_id, uid)
    first_q = session_eng.current_question()

    return jsonify({
        "status": "started",
        "stage": session_eng.stage,
        "completed_stages": sorted(session_eng.completed_stages),
        "question": first_q,
        "dashboard": get_day_one_dashboard(org_id),
    })


@onboarding_bp.route("/answer", methods=["POST"])
def api_onboarding_answer():
    """Answer the current onboarding question."""
    uid = session.get("identity_id") or session.get("user_id") or ""
    org_id = session.get("current_org_id")
    if not uid or not org_id:
        return jsonify({"error": "Not authenticated"}), 401

    data = request.get_json(silent=True) or {}
    key = data.get("key", "")
    value = data.get("value", "")

    session_eng = get_or_create_session(org_id, uid)
    result = session_eng.answer(key, value)

    return jsonify({
        "status": "progress",
        "stage": result["stage"],
        "completed_stages": result["completed_stages"],
        "next_question": result["next_question"],
        "built": result.get("built", {}),
        "dashboard": get_day_one_dashboard(org_id),
    })


@onboarding_bp.route("/reset", methods=["POST"])
def api_reset_onboarding():
    """Reset onboarding progress."""
    uid = session.get("identity_id") or session.get("user_id") or ""
    org_id = session.get("current_org_id")
    reset_session(org_id, uid)
    return jsonify({"status": "reset"})


@onboarding_bp.route("/dashboard", methods=["GET"])
def api_onboarding_dashboard():
    """Get the day-one dashboard — never empty, always shows progress."""
    uid = session.get("identity_id") or session.get("user_id") or ""
    org_id = session.get("current_org_id")
    if not uid or not org_id:
        return jsonify({"error": "Not authenticated"}), 401

    return jsonify({
        "dashboard": get_day_one_dashboard(org_id),
        "onboarding": {
            "in_progress": _is_onboarding_in_progress(org_id, uid),
        },
    })


@onboarding_bp.route("/complete", methods=["POST"])
def api_onboarding_complete():
    """Mark onboarding as complete and send confirmation email."""
    uid = session.get("identity_id") or session.get("user_id") or ""
    org_id = session.get("current_org_id")
    if not uid or not org_id:
        return jsonify({"error": "Not authenticated"}), 401

    from app.email_service import build_onboarding_complete_email, send_email
    from app.auth import TeamMember
    member = TeamMember.query.get(uid) if uid.isdigit() else TeamMember.query.filter_by(email=uid).first()
    if member:
        subject, body = build_onboarding_complete_email(
            member.email,
            f"Your Personal SHUNYA"
        )
        send_email(to=member.email, subject=subject, body=body,
                   notification_type="onboarding_complete",
                   business_event_id=f"onboarding:{member.id}",
                   category="operational")

    return jsonify({"status": "completed", "email_sent": True})


def _is_onboarding_in_progress(org_id, uid):
    """Check if onboarding is still in progress (not all stages complete)."""
    from app.onboarding.engine import get_or_create_session
    s = get_or_create_session(org_id, uid)
    return len(s.completed_stages) < 3