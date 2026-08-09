"""WhatsApp communication stub — logs intent, no real send."""

import logging

logger = logging.getLogger(__name__)


def send_whatsapp(to: str, message: str):
    """Log WhatsApp message intent. No real API integration yet."""
    msg = f"[WHATSAPP] To: {to} | Message: {message[:200]}"
    logger.info(msg)
    print(msg)
    return {"status": "logged", "to": to, "message": message[:200], "channel": "whatsapp"}