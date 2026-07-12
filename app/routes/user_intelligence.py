"""Shunya OS — User Intelligence API routes."""
from flask import Blueprint, request, jsonify, g
from app import db
from app.routes.auth import login_required
from app.shunya.user_intelligence import UserIntelligence

user_intel_bp = Blueprint("user_intel", __name__, url_prefix="/api/user-intel")


@user_intel_bp.route("/log", methods=["POST"])
@login_required
def log_activity():
    """Log a user activity event."""
    data = request.get_json(silent=True) or {}
    activity_type = (data.get("activity_type") or "").strip()
    if not activity_type:
        return jsonify({"error": "activity_type required"}), 400

    result = UserIntelligence.log_activity(
        tenant_id=g.tenant.id,
        user_id=g.user.id,
        activity_type=activity_type,
        page_path=data.get("page_path", ""),
        page_title=data.get("page_title", ""),
        session_id=data.get("session_id", ""),
        duration=int(data.get("duration", 0)),
        metadata=data.get("metadata"),
        device_info=data.get("device_info", ""),
        ip_address=request.remote_addr or "",
    )
    return jsonify(result), 201 if result.get("success") else 200


@user_intel_bp.route("/today", methods=["GET"])
@login_required
def today_stats():
    """Return today's user stats."""
    stats = UserIntelligence.get_user_today_stats(g.tenant.id, g.user.id)
    return jsonify(stats)


@user_intel_bp.route("/trend", methods=["GET"])
@login_required
def activity_trend():
    """Return activity trend for last N days."""
    days = request.args.get("days", 7, type=int)
    days = min(max(days, 1), 60)
    trend = UserIntelligence.get_user_activity_trend(g.tenant.id, g.user.id, days)
    return jsonify({"days": days, "trend": trend})


@user_intel_bp.route("/focus", methods=["GET"])
@login_required
def focus_score():
    """Return focus score."""
    score = UserIntelligence.get_user_focus_score(g.tenant.id, g.user.id)
    return jsonify(score)


@user_intel_bp.route("/relationship-score", methods=["GET"])
@login_required
def relationship_score():
    """Return relationship building score."""
    days = request.args.get("days", 30, type=int)
    score = UserIntelligence.get_relationship_building_score(g.tenant.id, g.user.id, days)
    return jsonify(score)


@user_intel_bp.route("/mood-correlation", methods=["GET"])
@login_required
def mood_correlation():
    """Return mood vs activity correlation."""
    days = request.args.get("days", 7, type=int)
    corr = UserIntelligence.get_mood_trend_with_activity(g.tenant.id, g.user.id, days)
    return jsonify(corr)


@user_intel_bp.route("/report/weekly", methods=["GET"])
@login_required
def weekly_report():
    """Return weekly health report."""
    report = UserIntelligence.get_weekly_health_report(g.tenant.id, g.user.id)
    return jsonify(report)
