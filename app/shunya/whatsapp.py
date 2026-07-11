"""Shunya WhatsApp Integration — two-way communication layer.

WhatsApp is Bird's primary outbound channel. Bird becomes a team member
in the user's chat list — proactive, context-aware, action-oriented.
"""
import os, json, logging, hmac, hashlib
from typing import Optional, Callable
from flask import request, jsonify, Blueprint
from app import db
from app.models import Entity, EntityDefinition, Message, ActivityLog, Notification, TeamMember
from datetime import datetime

logger = logging.getLogger("app.shunya.whatsapp")

WHATSAPP_API_URL = os.getenv("WHATSAPP_API_URL", "")
WHATSAPP_TOKEN = os.getenv("WHATSAPP_TOKEN", "")
WHATSAPP_PHONE_ID = os.getenv("WHATSAPP_PHONE_ID", "")
WHATSAPP_WEBHOOK_SECRET = os.getenv("WHATSAPP_WEBHOOK_SECRET", "")

whatsapp_bp = Blueprint("whatsapp", __name__, url_prefix="/whatsapp")


class WhatsAppChannel:
    """Manages outbound WhatsApp messages via Business API."""

    @staticmethod
    def send(to: str, message: str, tenant_id: Optional[int] = None,
             entity_id: Optional[int] = None) -> dict:
        """Send a WhatsApp message. Returns response."""
        if not WHATSAPP_API_URL or not WHATSAPP_TOKEN:
            logger.warning("WhatsApp not configured")
            return {"error": "WhatsApp not configured"}

        try:
            import requests
            url = f"{WHATSAPP_API_URL}/{WHATSAPP_PHONE_ID}/messages"
            headers = {
                "Authorization": f"Bearer {WHATSAPP_TOKEN}",
                "Content-Type": "application/json",
            }
            payload = {
                "messaging_product": "whatsapp",
                "to": to,
                "type": "text",
                "text": {"body": message},
            }
            resp = requests.post(url, headers=headers, json=payload, timeout=10)
            result = resp.json()

            # Log
            if tenant_id and entity_id:
                msg = Message(
                    tenant_id=tenant_id,
                    entity_id=entity_id,
                    sender_type="ai",
                    sender_id=None,
                    channel="whatsapp",
                    content=message,
                    is_from_client=False,
                )
                db.session.add(msg)
                db.session.commit()

            return result

        except Exception as e:
            logger.error("WhatsApp send failed: %s", e)
            return {"error": str(e)}

    @staticmethod
    def send_template(to: str, template_name: str, params: list,
                      tenant_id: Optional[int] = None,
                      entity_id: Optional[int] = None) -> dict:
        """Send a WhatsApp template message."""
        if not WHATSAPP_API_URL or not WHATSAPP_TOKEN:
            return {"error": "WhatsApp not configured"}
        try:
            import requests
            components = [{
                "type": "body",
                "parameters": [{"type": "text", "text": p} for p in params],
            }]
            payload = {
                "messaging_product": "whatsapp",
                "to": to,
                "type": "template",
                "template": {"name": template_name, "language": {"code": "en"}, "components": components},
            }
            headers = {"Authorization": f"Bearer {WHATSAPP_TOKEN}", "Content-Type": "application/json"}
            resp = requests.post(f"{WHATSAPP_API_URL}/{WHATSAPP_PHONE_ID}/messages",
                                 headers=headers, json=payload, timeout=10)
            return resp.json()
        except Exception as e:
            logger.error("WhatsApp template send failed: %s", e)
            return {"error": str(e)}

    @staticmethod
    def send_bird_message(to: str, bird_message: dict, tenant_id: int,
                          entity_id: Optional[int] = None) -> dict:
        """Send a structured Bird message via WhatsApp with context."""
        text = f"🧠 *{bird_message.get('title', 'Shunya AI')}*\n\n"
        text += f"{bird_message.get('observation', '')}\n\n"
        text += f"*Recommendation:* {bird_message.get('recommendation', '')}\n"
        if bird_message.get('reason'):
            text += f"*Why:* {bird_message['reason']}\n"
        if bird_message.get('next_action'):
            text += f"\n→ {bird_message['next_action']}"

        return WhatsAppChannel.send(to, text, tenant_id, entity_id)

    @staticmethod
    def send_bird_proactive(to: str, user_name: str, insights: list,
                            tenant_id: int) -> dict:
        """Send a proactive Bird message without being asked."""
        if not insights:
            return {"skipped": True}
        text = f"🧠 *Good morning, {user_name}!*\n\n"
        text += "Here's what needs your attention:\n\n"
        for i, insight in enumerate(insights[:3], 1):
            text += f"{i}. *{insight.get('title')}*\n   {insight.get('description')}\n"
        text += f"\nReply with the number to take action, or ask me anything."

        return WhatsAppChannel.send(to, text, tenant_id)


# ---------------------------------------------------------------------------
# Webhook receiver
# ---------------------------------------------------------------------------

@whatsapp_bp.route("/webhook", methods=["GET", "POST"])
def webhook():
    """WhatsApp Business API webhook — receive incoming messages."""
    # GET = webhook verification
    if request.method == "GET":
        verify_token = request.args.get("hub.verify_token", "")
        challenge = request.args.get("hub.challenge", "")
        expected_token = os.getenv("WHATSAPP_VERIFY_TOKEN", "shunya-verify-2026")
        if verify_token == expected_token:
            return challenge, 200
        return "Verification failed", 403

    # POST = incoming message
    data = request.get_json(silent=True) or {}
    logger.info("WhatsApp webhook received: %s", json.dumps(data)[:500])

    try:
        entries = data.get("entry", [])
        for entry in entries:
            changes = entry.get("changes", [])
            for change in changes:
                value = change.get("value", {})
                messages = value.get("messages", [])
                metadata = value.get("metadata", {})

                for msg in messages:
                    from_number = msg.get("from", "")
                    msg_type = msg.get("type", "text")
                    text_body = ""

                    if msg_type == "text":
                        text_body = msg.get("text", {}).get("body", "")
                    elif msg_type == "interactive":
                        interactive = msg.get("interactive", {})
                        if interactive.get("type") == "button_reply":
                            text_body = interactive.get("button_reply", {}).get("id", "")
                        elif interactive.get("type") == "list_reply":
                            text_body = interactive.get("list_reply", {}).get("id", "")

                    if text_body:
                        _process_incoming_message(from_number, text_body, msg.get("id", ""))

    except Exception as e:
        logger.error("WhatsApp webhook processing error: %s", e)

    return jsonify({"status": "ok"}), 200


def _process_incoming_message(from_number: str, text: str, msg_id: str):
    """Process an incoming WhatsApp message through the Personal Agent."""
    from app.shunya.agent.channels import get_router
    from app.shunya.next_best_action import NextBestActionEngine

    # Find the tenant/entity for this phone number
    entity = Entity.query.filter(
        Entity.data["phone"].as_string() == from_number,
        Entity.is_archived == False,
    ).order_by(Entity.created_at.desc()).first()

    team_member = TeamMember.query.filter_by(phone=from_number).first()

    if entity:
        # Client message — log and notify team
        msg = Message(
            tenant_id=entity.tenant_id,
            entity_id=entity.id,
            sender_type="client",
            channel="whatsapp",
            content=text,
            is_from_client=True,
        )
        db.session.add(msg)

        activity = ActivityLog(
            tenant_id=entity.tenant_id,
            entity_id=entity.id,
            action="message_received",
            detail=f"WhatsApp: {text[:200]}",
        )
        db.session.add(activity)
        db.session.commit()

        # Acknowledge
        from app.shunya.whatsapp import WhatsAppChannel
        WhatsAppChannel.send(from_number,
            "Thanks! Your message has been received. Our team will get back to you shortly.",
            entity.tenant_id, entity.id)

    elif team_member:
        # Team member message — route through Personal Agent
        router = get_router()
        payload = {"from": from_number, "text": text, "msg_id": msg_id}
        result = router.process_message("whatsapp", payload)

        if result:
            response = result.get("text", "")
        else:
            # Fallback
            bird = __import__("app.shunya.bird", fromlist=["Bird"]).Bird(
                team_member.tenant_id, team_member.id, team_member.role, team_member.name
            )
            q_result = bird.handle_query(text)
            response = "Let me check on that for you."
            if q_result.get("context") and q_result["context"].get("results"):
                for r in q_result["context"]["results"][:2]:
                    response = f"• {r.get('summary', r.get('answer', ''))[:200]}"

        from app.shunya.whatsapp import WhatsAppChannel
        WhatsAppChannel.send(from_number, response, team_member.tenant_id)

    else:
        # Unknown number — Bird treats as new lead inquiry
        from app.shunya.whatsapp import WhatsAppChannel
        WhatsAppChannel.send(from_number,
            "👋 Welcome! I'm Shunya AI. How can I help you today? "
            "Tell me about your requirements and I'll get things started.",
            None)


# ---------------------------------------------------------------------------
# Outbound proactive AI (cron-ready)
# ---------------------------------------------------------------------------

class ProactiveOutbound:
    """Sends proactive Bird messages via WhatsApp at configured intervals."""

    @staticmethod
    def send_daily_briefing(tenant_id: int):
        """Send a daily briefing to all team members."""
        from app.shunya.next_best_action import NextBestActionEngine

        team = TeamMember.query.filter_by(tenant_id=tenant_id, is_active=True).all()
        for member in team:
            if not member.phone:
                continue
            actions = NextBestActionEngine.get_for_user(tenant_id, member.id, member.role)
            if actions:
                WhatsAppChannel.send_bird_proactive(
                    member.phone, member.name,
                    [{"title": a.title, "description": a.description} for a in actions[:5]],
                    tenant_id
                )

    @staticmethod
    def send_entity_alert(tenant_id: int, entity_id: int, alert_type: str,
                          message: str, team_phone: str):
        """Send an alert about a specific entity to a team member."""
        WhatsAppChannel.send(team_phone,
            f"🚨 *Alert: {alert_type}*\n\n{message}\n\nReply to take action.",
            tenant_id, entity_id)