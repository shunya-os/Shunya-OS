import time
import random
from datetime import datetime, timedelta
from app.communication.models import MessageProposal
from app import db

MIN_DELAY_SECONDS = 3
MAX_DELAY_SECONDS = 8
MAX_MESSAGES_PER_MINUTE = 5


def can_send(to):
    one_min_ago = datetime.utcnow() - timedelta(minutes=1)

    recent = MessageProposal.query.filter(
        MessageProposal.to == to,
        MessageProposal.created_at >= one_min_ago
    ).count()

    if recent >= MAX_MESSAGES_PER_MINUTE:
        return False

    return True


def human_delay():
    delay = random.randint(MIN_DELAY_SECONDS, MAX_DELAY_SECONDS)
    time.sleep(delay)


def safe_send(provider, to, message):
    if not to:
        return {"status": "skipped", "reason": "no_recipient"}

    if not can_send(to):
        return {"status": "blocked", "reason": "rate_limit"}

    human_delay()

    result = provider.send(to, message)

    log = MessageProposal(to=to, message=message)
    db.session.add(log)

    return result


def send_proposal(provider, proposal):
    if proposal.status != "approved":
        return {"status": "blocked", "reason": "not_approved"}

    result = provider.send(proposal.to, proposal.message)

    proposal.status = "sent"
    return result