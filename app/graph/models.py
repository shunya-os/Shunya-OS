from datetime import datetime, timezone
from app import db


class ObjectRelation(db.Model):
    """Terminal relation between two objects in the execution graph.

    A directed edge: source_object triggers target_object through a
    structured relation type. Pure structural wiring — no business meaning.
    """

    __tablename__ = "object_relations"

    id = db.Column(db.Integer, primary_key=True)
    source_object_id = db.Column(db.Integer, nullable=False)
    target_object_id = db.Column(db.Integer, nullable=False)
    relation_type = db.Column(db.String(100), default="triggers")

    created_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )