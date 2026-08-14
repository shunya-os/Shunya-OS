"""WhatsApp Adapter — GUARDRAILED: No direct sends allowed.

ACTIVATION-08B: This adapter is BLOCKED for direct use.
All outbound communication must go through MessageProposal → human approval → send.

Callers MUST use the proposal system in app/execution/effects.py instead.
Direct calls to whatsapp_adapter.send() will fail loudly.
"""

import logging

logger = logging.getLogger(__name__)

GUARDRAIL_MESSAGE = (
    "BLOCKED: Direct WhatsApp send via whatsapp_adapter.send() is DISABLED. "
    "ACTIVATION-08B: All outbound communication must go through "
    "MessageProposal -> human approval -> send. "
    "Use create_proposal() in app/execution/effects.py instead."
)


def send(effect: dict) -> dict:
    """BLOCKED by ACTIVATION-08B guardrail. Use proposal system instead."""
    logger.error(GUARDRAIL_MESSAGE)
    return {
        "status": "blocked",
        "reason": GUARDRAIL_MESSAGE,
        "channel": "whatsapp",
    }