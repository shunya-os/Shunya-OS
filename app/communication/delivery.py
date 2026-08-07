from app.communication.models import Message
from app import db


def deliver_messages():
    pending = Message.query.filter_by(status="pending").all()

    for msg in pending:
        # placeholder for real delivery
        msg.status = "sent"

    db.session.commit()