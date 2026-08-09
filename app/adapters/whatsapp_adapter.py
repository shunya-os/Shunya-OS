"""WhatsApp Adapter — free web mode (print/log) with future API path.

ACTIVATION-04: Outbound message adapter. Switches MODE to "api"
when Meta Business API credentials are configured.
"""

import logging

logger = logging.getLogger(__name__)

MODE = "free"  # switch to "api" when credentials configured


def send(effect: dict) -> dict:
    """Send a WhatsApp message. Mode-switchable between free and API."""
    to = effect.get("to", "")
    message = effect.get("message", "")

    if not to or not message:
        return {"status": "skipped", "reason": "missing to/message"}

    if MODE == "free":
        return send_whatsapp_web(to, message)
    else:
        return send_whatsapp_api(to, message)


def send_whatsapp_web(to: str, message: str) -> dict:
    """Free web mode — print/log only. Replace with Playwright later."""
    logger.info("[WhatsApp-Web] -> %s: %s", to, message[:100])
    print(f"[WhatsApp-Web] -> {to}: {message[:120]}")
    return {"status": "sent", "channel": "whatsapp_web"}


def send_whatsapp_api(to: str, message: str) -> dict:
    """Future Meta Business API integration."""
    return {"status": "not_implemented", "channel": "whatsapp_api"}