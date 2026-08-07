from app.models import Task
from app.observations.models import Observation
from app.communication.models import Message


def get_entity_timeline(entity_id):
    events = []

    tasks = Task.query.filter_by(entity_id=entity_id).all()
    observations = Observation.query.filter_by(entity_id=entity_id).all()
    messages = Message.query.filter_by(entity_id=entity_id).all()

    for t in tasks:
        events.append({
            "type": "task",
            "data": t.description,
            "created_at": t.created_at
        })

    for o in observations:
        events.append({
            "type": "observation",
            "data": o.status,
            "created_at": o.created_at
        })

    for m in messages:
        events.append({
            "type": "message",
            "data": m.content,
            "created_at": m.created_at
        })

    return sorted(events, key=lambda x: x["created_at"])