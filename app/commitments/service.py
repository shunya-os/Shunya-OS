from datetime import datetime, timezone
from app import db
from app.commitments.models import Commitment


def create_commitment(title: str, owner: str = None, due_at=None):
    c = Commitment(
        title=title,
        owner=owner,
        due_at=due_at,
        status="pending",
    )
    db.session.add(c)
    db.session.commit()
    return c


def update_status(commitment: Commitment, status: str):
    commitment.status = status
    db.session.commit()
    return commitment


def is_overdue(commitment: Commitment) -> bool:
    if not commitment.due_at:
        return False
    return (
        commitment.status != "completed"
        and datetime.now(timezone.utc) > commitment.due_at
    )