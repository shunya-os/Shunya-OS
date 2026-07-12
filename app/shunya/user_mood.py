"""Shunya OS — User Mood / Health Check-in Tracker.

Provides endpoints for team members to log their daily mood and energy,
view trends, and integrate with the dashboard greeting widget.

Uses db.session.query(Model) — never Model.query.
"""
from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify, g
from app import db
from app.models import UserMoodCheckin
from app.routes.auth import login_required

mood_bp = Blueprint("mood", __name__, url_prefix="/api/checkin")

VALID_MOODS = {"great", "good", "okay", "rough", "tough"}


@mood_bp.route("", methods=["POST"])
@login_required
def checkin_create():
    """Log a mood/energy check-in for the current user.

    Accepts: {mood: str, energy: int, notes: str}
    """
    data = request.get_json(silent=True) or {}
    mood = (data.get("mood") or "").strip().lower()
    energy = data.get("energy")

    # Validation
    if mood not in VALID_MOODS:
        return jsonify({
            "error": f"Invalid mood. Choose from: {', '.join(sorted(VALID_MOODS))}"
        }), 400

    if not isinstance(energy, int) or energy < 1 or energy > 5:
        return jsonify({"error": "Energy must be an integer 1-5"}), 400

    notes = (data.get("notes") or "").strip()[:500]

    checkin = UserMoodCheckin(
        tenant_id=g.tenant.id,
        user_id=g.user.id,
        mood=mood,
        energy=energy,
        notes=notes,
    )
    db.session.add(checkin)
    db.session.commit()

    return jsonify({
        "success": True,
        "checkin": checkin.to_dict(),
        "message": f"Logged: feeling {mood}, energy {energy}/5",
    }), 201


@mood_bp.route("/trend", methods=["GET"])
@login_required
def checkin_trend():
    """Return the last 30 check-ins for the current user (for graphing)."""
    checkins = db.session.query(UserMoodCheckin).filter_by(
        tenant_id=g.tenant.id,
        user_id=g.user.id,
    ).order_by(UserMoodCheckin.created_at.desc()).limit(30).all()

    # Calculate summary stats
    mood_counts = {}
    energy_total = 0
    for c in checkins:
        mood_counts[c.mood] = mood_counts.get(c.mood, 0) + 1
        energy_total += c.energy

    count = len(checkins)
    avg_energy = round(energy_total / count, 1) if count > 0 else 0
    most_common_mood = max(mood_counts, key=mood_counts.get) if mood_counts else None

    return jsonify({
        "checkins": [c.to_dict() for c in checkins],
        "count": count,
        "summary": {
            "average_energy": avg_energy,
            "mood_distribution": mood_counts,
            "most_common_mood": most_common_mood,
        },
    })


@mood_bp.route("/status", methods=["GET"])
@login_required
def checkin_status():
    """Return today's check-in for the current user, or null."""
    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    today_end = today_start + timedelta(days=1)

    checkin = db.session.query(UserMoodCheckin).filter(
        UserMoodCheckin.tenant_id == g.tenant.id,
        UserMoodCheckin.user_id == g.user.id,
        UserMoodCheckin.created_at >= today_start,
        UserMoodCheckin.created_at < today_end,
    ).order_by(UserMoodCheckin.created_at.desc()).first()

    if checkin:
        return jsonify({"checked_in": True, "checkin": checkin.to_dict()})
    return jsonify({"checked_in": False, "checkin": None})


@mood_bp.route("/streak", methods=["GET"])
@login_required
def checkin_streak():
    """Return the user's consecutive check-in streak."""
    checkins = db.session.query(UserMoodCheckin).filter_by(
        tenant_id=g.tenant.id,
        user_id=g.user.id,
    ).order_by(UserMoodCheckin.created_at.desc()).all()

    if not checkins:
        return jsonify({"streak": 0})

    streak = 0
    today = datetime.utcnow().date()
    for c in checkins:
        c_date = c.created_at.date()
        if streak == 0 and c_date == today:
            streak = 1
        elif streak > 0 and c_date == today - timedelta(days=streak):
            streak += 1
        elif c_date < today - timedelta(days=streak):
            break

    return jsonify({"streak": streak, "checked_in_today": checkins[0].created_at.date() == today})