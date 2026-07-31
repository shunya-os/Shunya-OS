"""SHUNYA — Communication Drafting Routes.

POST /draft/email     — Generate a template email draft
POST /draft/whatsapp  — Generate a template WhatsApp message draft
POST /draft/sms       — Generate a template SMS draft
"""
from datetime import datetime

from flask import request, jsonify
from werkzeug.exceptions import BadRequest

from app.auth_routes import login_required
from app.production.communication import communication_bp


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _require_json() -> dict:
    """Extract JSON body or raise 400."""
    data = request.get_json(silent=True)
    if data is None:
        raise BadRequest("Request body must be valid JSON")
    return data


def _require_field(data: dict, field: str, label: str = "") -> str:
    """Require a non-empty string field."""
    label = label or field
    value = data.get(field)
    if not value or not str(value).strip():
        raise BadRequest(f"'{label}' is required")
    return str(value).strip()


# ---------------------------------------------------------------------------
# Draft templates
# ---------------------------------------------------------------------------

def _draft_email(to: str, subject: str, body: str, cc: str = "", bcc: str = "") -> dict:
    """Build a template email draft."""
    return {
        "channel": "email",
        "to": to,
        "cc": cc,
        "bcc": bcc,
        "subject": subject,
        "body": body,
        "drafted_at": datetime.utcnow().isoformat() + "Z",
        "status": "draft",
    }


def _draft_whatsapp(to: str, message: str) -> dict:
    """Build a template WhatsApp message draft."""
    return {
        "channel": "whatsapp",
        "to": to,
        "message": message,
        "drafted_at": datetime.utcnow().isoformat() + "Z",
        "status": "draft",
    }


def _draft_sms(to: str, message: str) -> dict:
    """Build a template SMS draft."""
    return {
        "channel": "sms",
        "to": to,
        "message": message,
        "drafted_at": datetime.utcnow().isoformat() + "Z",
        "status": "draft",
    }


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------


@communication_bp.route("/draft/email", methods=["POST"])
@login_required
def draft_email():
    """Draft an email from the provided intent fields."""
    data = _require_json()

    to = _require_field(data, "to", "recipient email")
    subject = _require_field(data, "subject", "subject")
    body = _require_field(data, "body", "email body")
    cc = data.get("cc", "")
    bcc = data.get("bcc", "")

    draft = _draft_email(to=to, subject=subject, body=body, cc=cc, bcc=bcc)

    return jsonify({"success": True, "draft": draft}), 201


@communication_bp.route("/draft/whatsapp", methods=["POST"])
@login_required
def draft_whatsapp():
    """Draft a WhatsApp message from the provided intent fields."""
    data = _require_json()

    to = _require_field(data, "to", "recipient phone")
    message = _require_field(data, "message", "message content")

    draft = _draft_whatsapp(to=to, message=message)

    return jsonify({"success": True, "draft": draft}), 201


@communication_bp.route("/draft/sms", methods=["POST"])
@login_required
def draft_sms():
    """Draft an SMS from the provided intent fields."""
    data = _require_json()

    to = _require_field(data, "to", "recipient phone")
    message = _require_field(data, "message", "message content")

    draft = _draft_sms(to=to, message=message)

    return jsonify({"success": True, "draft": draft}), 201