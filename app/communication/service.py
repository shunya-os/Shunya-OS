from app.communication.models import Message
from app import db


class MessageService:

    @staticmethod
    def create(entity_id, content, direction="outbound", channel="system"):
        msg = Message(
            entity_id=entity_id,
            content=content,
            direction=direction,
            channel=channel,
            status="pending",
            metadata_json={}
        )
        db.session.add(msg)
        db.session.commit()
        return msg

    @staticmethod
    def mark_sent(message):
        message.status = "sent"
        db.session.commit()
        return message