"""System alert endpoints — operator surface for E1 alerting."""
from flask import Blueprint, jsonify, request

from app.alerting.models import AlertEvent
from app.alerting.service import get_alert_engine
from app.authz.decorators import require_permission

alert_bp = Blueprint("alerts", __name__, url_prefix="/api/v1/system/alerts")


@alert_bp.route("", methods=["GET"])
@require_permission("admin.view_audit")
def list_alerts():
    """List recent alert events (active first, then latest 50)."""
    events = (
        AlertEvent.query
        .order_by(AlertEvent.status.asc(), AlertEvent.id.desc())
        .limit(50)
        .all()
    )
    return jsonify({"alerts": [{
        "id": e.id,
        "rule": e.rule,
        "alert_key": e.alert_key,
        "severity": e.severity,
        "status": e.status,
        "subject": e.subject,
        "first_seen": e.first_seen.isoformat() if e.first_seen else None,
        "last_seen": e.last_seen.isoformat() if e.last_seen else None,
        "recovered_at": e.recovered_at.isoformat() if e.recovered_at else None,
        "occurrences": e.occurrences,
        "delivery_state": e.delivery_state,
        "delivered_at": e.delivered_at.isoformat() if e.delivered_at else None,
    } for e in events]})


@alert_bp.route("/test", methods=["POST"])
@require_permission("admin.view_audit")
def send_test_alert():
    """Fire a real test alert through the full delivery path (E1 e2e proof)."""
    data = request.get_json() or {}
    recipient = data.get("recipient") or ""
    subject = data.get("subject") or "SHUNYA test alert"
    result = get_alert_engine().fire_test_alert(recipient=recipient, subject=subject)
    code = 200 if result.get("fired") or result.get("alert_id") else 500
    return jsonify(result), code


@alert_bp.route("/simulate", methods=["POST"])
@require_permission("admin.view_audit")
def simulate_failures():
    """Simulate N failure crumbs to exercise the flood detection path.

    Does not generate real 500s; only drives the alert engine's detection,
    dedup, delivery and recovery lifecycle deterministically.
    """
    data = request.get_json() or {}
    count = int(data.get("count", 3))
    path = data.get("path", "/api/v1/simulated/failure")
    exc_type = data.get("exc_type", "SimulatedFailure")
    engine = get_alert_engine()
    for _ in range(max(count, 1)):
        engine.ingest_failure(path=path, exc_type_name=exc_type, request_id="simulated")
    active = AlertEvent.query.filter_by(rule="http_5xx", status="active").count()
    return jsonify({"simulated": count, "active_alerts": active})