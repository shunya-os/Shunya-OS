"""ACTIVATION-06/07: Safe send — the ONLY allowed message delivery path.

Constitutional rule: Shunya proposes. Only human disposes.

send_proposal() is the exclusive gateway for outbound messages.
Direct provider.send() is forbidden — the hard guardrail in the
provider layer blocks any call not triggered by a human decision.
"""

from datetime import datetime, timezone

from app import db
from app.communication.models import MessageProposal


def send_proposal(provider, proposal):
    """Send an approved proposal via the provider.

    This is the ONLY allowed path for outbound messages.
    Direct provider.send() is blocked by a hard guardrail.

    Args:
        provider: A CommunicationProvider instance.
        proposal: MessageProposal with status='approved'.

    Returns:
        Result dict from the provider.
    """
    if proposal.status != "approved":
        return {"status": "blocked", "reason": "not_approved"}

    # Use human-edited message if available
    final_message = proposal.edited_message if proposal.edited_message else proposal.message

    # The hard guardrail is inside the provider — it checks is_human_triggered
    # We pass metadata indicating this IS a human-triggered send
    result = provider.send(
        proposal.to,
        final_message,
        metadata={"is_human_triggered": True},
    )

    proposal.status = "sent"
    proposal.sent_at = datetime.now(timezone.utc)
    db.session.commit()

    return result