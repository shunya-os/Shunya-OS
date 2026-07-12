"""Admin routes for Webhook management."""
import json
from datetime import datetime
from flask import Blueprint, render_template, request, jsonify, g, current_app
from app import db
from app.models import Webhook, WebhookLog, EntityDefinition
from app.routes.auth import login_required, admin_required
from app.shunya.webhooks import fire_webhook

webhooks_bp = Blueprint("webhooks", __name__, url_prefix="/admin")

STATIC_EVENTS = [
    "entity.created", "entity.updated", "entity.deleted", "entity.status_changed",
    "opportunity.created", "opportunity.updated", "opportunity.status_changed",
    "invoice.created", "invoice.updated", "invoice.paid",
    "experience.created", "experience.updated",
]


def _get_available_events():
    """Get all available events from static list + entity definitions."""
    defs = (
        db.session.query(EntityDefinition)
        .filter_by(tenant_id=g.tenant.id, is_active=True)
        .all()
    )
    events = set(STATIC_EVENTS)
    for d in defs:
        t = d.type
        events.add(f"{t}.created")
        events.add(f"{t}.updated")
        events.add(f"{t}.deleted")
        events.add(f"{t}.status_changed")
    return sorted(events)


# ── UI Pages ──

@webhooks_bp.route("/webhooks")
@login_required
@admin_required
def webhooks_page():
    hooks = (
        db.session.query(Webhook)
        .filter_by(tenant_id=g.tenant.id)
        .order_by(Webhook.created_at.desc())
        .all()
    )
    webhook_configs = []
    for h in hooks:
        webhook_configs.append({
            "id": h.id,
            "name": h.name,
            "url": h.url,
            "event": h.event,
            "entity_type": h.entity_type,
            "headers": h.headers,
            "is_active": h.is_active,
            "last_sent_at": h.last_sent_at,
            "last_status": h.last_status,
            "failure_count": h.failure_count,
            "created_at": h.created_at,
        })
    return render_template(
        "admin/webhooks.html",
        webhooks=webhook_configs,
        entity_events=_get_available_events(),
    )


@webhooks_bp.route("/webhooks/log")
@login_required
def webhooks_log_page():
    webhook_id = request.args.get("webhook_id", type=int)
    query = db.session.query(WebhookLog).filter_by(tenant_id=g.tenant.id)
    if webhook_id:
        query = query.filter_by(webhook_id=webhook_id)
    logs = query.order_by(WebhookLog.created_at.desc()).limit(200).all()

    hooks = (
        db.session.query(Webhook)
        .filter_by(tenant_id=g.tenant.id)
        .all()
    )
    return render_template("admin/webhooks_log.html", logs=logs, webhooks=hooks, selected_id=webhook_id)


# ── API ──

@webhooks_bp.route("/api/webhooks", methods=["GET"])
@login_required
def list_webhooks():
    hooks = (
        db.session.query(Webhook)
        .filter_by(tenant_id=g.tenant.id)
        .order_by(Webhook.created_at.desc())
        .all()
    )
    return jsonify([h.to_dict() for h in hooks])


@webhooks_bp.route("/api/webhooks", methods=["POST"])
@login_required
@admin_required
def create_webhook():
    data = request.get_json(silent=True) or {}
    name = (data.get("name") or "").strip()
    url = (data.get("url") or "").strip()
    event = (data.get("event") or "").strip()
    entity_type = (data.get("entity_type") or "*").strip()
    headers = data.get("headers", {}) or {}
    secret = (data.get("secret") or "").strip()

    if not name or not url:
        return jsonify({"error": "Name and URL are required"}), 400
    if not url.startswith("https://"):
        return jsonify({"error": "Only HTTPS URLs are allowed"}), 400
    if not event:
        return jsonify({"error": "An event is required"}), 400

    wh = Webhook(
        tenant_id=g.tenant.id,
        name=name,
        url=url,
        event=event,
        entity_type=entity_type,
        headers=headers if isinstance(headers, dict) else {},
        secret=secret,
        is_active=True,
    )
    db.session.add(wh)
    db.session.commit()

    return jsonify({"success": True, "webhook": wh.to_dict()}), 201


@webhooks_bp.route("/api/webhooks/<int:wh_id>", methods=["GET"])
@login_required
def get_webhook(wh_id):
    wh = db.session.query(Webhook).filter_by(id=wh_id, tenant_id=g.tenant.id).first()
    if not wh:
        return jsonify({"error": "Not found"}), 404
    return jsonify(wh.to_dict())


@webhooks_bp.route("/api/webhooks/<int:wh_id>", methods=["PUT"])
@login_required
@admin_required
def update_webhook(wh_id):
    wh = db.session.query(Webhook).filter_by(id=wh_id, tenant_id=g.tenant.id).first()
    if not wh:
        return jsonify({"error": "Not found"}), 404

    data = request.get_json(silent=True) or {}
    if "name" in data:
        wh.name = data["name"].strip()
    if "url" in data:
        url = data["url"].strip()
        if not url.startswith("https://"):
            return jsonify({"error": "Only HTTPS URLs are allowed"}), 400
        wh.url = url
    if "event" in data:
        wh.event = data["event"].strip()
    if "entity_type" in data:
        wh.entity_type = data["entity_type"].strip()
    if "headers" in data:
        wh.headers = data["headers"] if isinstance(data["headers"], dict) else {}
    if "secret" in data:
        wh.secret = (data["secret"] or "").strip()
    if "is_active" in data:
        wh.is_active = bool(data["is_active"])

    db.session.commit()
    return jsonify({"success": True, "webhook": wh.to_dict()})


@webhooks_bp.route("/api/webhooks/<int:wh_id>", methods=["DELETE"])
@login_required
@admin_required
def delete_webhook(wh_id):
    wh = db.session.query(Webhook).filter_by(id=wh_id, tenant_id=g.tenant.id).first()
    if not wh:
        return jsonify({"error": "Not found"}), 404
    db.session.query(WebhookLog).filter_by(webhook_id=wh.id).delete()
    db.session.delete(wh)
    db.session.commit()
    return jsonify({"success": True})


@webhooks_bp.route("/api/webhooks/<int:wh_id>/test", methods=["POST"])
@login_required
@admin_required
def test_webhook(wh_id):
    wh = db.session.query(Webhook).filter_by(id=wh_id, tenant_id=g.tenant.id).first()
    if not wh:
        return jsonify({"error": "Not found"}), 404

    test_payload = {
        "type": "test",
        "message": "This is a test event from Shunya OS",
        "tenant": g.tenant.slug,
        "triggered_by": getattr(g, "user", None).email if hasattr(g, "user") and g.user else "unknown",
    }

    try:
        fire_webhook(wh, "test.ping", test_payload, db.session, WebhookLog)
        return jsonify({
            "success": True,
            "status": wh.last_status,
            "message": "Test webhook sent",
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@webhooks_bp.route("/api/events", methods=["GET"])
@login_required
def list_events():
    return jsonify({"events": _get_available_events()})