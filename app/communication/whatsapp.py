"""WhatsApp — real Meta Cloud API send. Falls back to log when unconfigured."""

import json
import logging
import os
from urllib.request import Request, urlopen
from urllib.error import URLError

logger = logging.getLogger(__name__)

_API_VERSION = os.environ.get("WHATSAPP_API_VERSION", "v22.0")
_TOKEN = os.environ.get("WHATSAPP_TOKEN", "")
_PHONE_ID = os.environ.get("WHATSAPP_PHONE_ID", "")
_BASE = "https://graph.facebook.com"


def send_whatsapp(to: str, message: str):
    """Send a WhatsApp message via Meta Cloud API. Falls back to log."""
    if not _TOKEN or not _PHONE_ID:
        logger.warning("WHATSAPP_TOKEN/PHONE_ID not set — logging instead")
        msg = f"[WHATSAPP] To: {to} | Message: {message[:200]}"
        logger.info(msg)
        print(msg)
        return {"status": "logged", "to": to, "channel": "whatsapp", "note": "no credentials"}

    url = f"{_BASE}/{_API_VERSION}/{_PHONE_ID}/messages"
    payload = json.dumps({
        "messaging_product": "whatsapp",
        "to": to,
        "type": "text",
        "text": {"body": message},
    }).encode()
    headers = {
        "Authorization": f"Bearer {_TOKEN}",
        "Content-Type": "application/json",
    }

    try:
        req = Request(url, data=payload, headers=headers, method="POST")
        with urlopen(req, timeout=15) as resp:
            body = resp.read().decode()
        logger.info("WhatsApp sent to %s: %s", to, message[:80])
        print(f"[WHATSAPP SENT] To: {to}")
        return {"status": "sent", "to": to, "channel": "whatsapp", "response": json.loads(body)}

    except URLError as e:
        logger.error("WhatsApp send failed to %s: %s", to, e)
        print(f"[WHATSAPP FAILED] To: {to} | Error: {e}")
        return {"status": "failed", "to": to, "error": str(e), "channel": "whatsapp"}
    except Exception as e:
        logger.error("WhatsApp unexpected error: %s", e)
        return {"status": "failed", "to": to, "error": str(e), "channel": "whatsapp"}