from app.communication.inbound import InboundEvent
from app.communication.models import Message
from app import db


def process_inbound():
    events = InboundEvent.query.filter_by(processed=False).all()

    for e in events:
        # naive mapping (will evolve later)
        entity_id = e.payload.get("entity_id")

        if entity_id:
            msg = Message(
                entity_id=entity_id,
                content=str(e.payload),
                direction="inbound",
                channel=e.source,
                status="received"
            )
            db.session.add(msg)

        e.processed = True

    db.session.commit()