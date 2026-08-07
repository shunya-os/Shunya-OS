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


def check_overdue(commitment):
    if commitment.due_at and commitment.status != "completed":
        now = datetime.now(timezone.utc)
        due = commitment.due_at
        # SQLite drops tzinfo on round-trip; normalize to UTC for comparison.
        if due.tzinfo is None:
            due = due.replace(tzinfo=timezone.utc)
        if now > due:
            commitment.status = "failed"
            db.session.commit()
    return commitment


def retry_commitment(commitment):
    if commitment.status == "failed":
        commitment.status = "pending"
        db.session.commit()
    return commitment


def apply_decision(commitment: Commitment, decision: dict):
    if decision["type"] != "update_commitment":
        return commitment

    payload = decision.get("payload", {})

    if "status" in payload:
        commitment.status = payload["status"]

    db.session.commit()
    return commitment