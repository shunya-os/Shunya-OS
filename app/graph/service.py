from app import db
from app.graph.models import ObjectRelation


def create_relation(source_id: int, target_id: int, relation_type: str = "triggers"):
    """Create a directed relation between two objects.

    Pure structural wiring: source triggers target on execution cycles.
    """
    relation = ObjectRelation(
        source_object_id=source_id,
        target_object_id=target_id,
        relation_type=relation_type,
    )
    db.session.add(relation)
    db.session.commit()
    return relation


def get_targets(source_id: int) -> list[ObjectRelation]:
    """Return all relations where source_id is the source."""
    return ObjectRelation.query.filter_by(
        source_object_id=source_id
    ).all()