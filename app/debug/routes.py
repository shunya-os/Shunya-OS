"""Debug control API — first human operating surface for SHUNYA runtime."""

from datetime import datetime, timezone

from flask import jsonify, request

from app import db
from app.debug import debug_bp
from app.objects.models import Object
from app.runtime.loop import run_cycle


def _serialize(obj):
    """Convert a SQLAlchemy model to a plain dict, filtering out internal attrs."""
    d = {}
    for col in obj.__table__.columns:
        val = getattr(obj, col.name)
        if isinstance(val, datetime):
            val = val.replace(tzinfo=timezone.utc).isoformat()
        d[col.name] = val
    return d


# ---------------------------------------------------------------------------
# 1. Create entity
# ---------------------------------------------------------------------------


@debug_bp.route("/entity", methods=["POST"])
def create_entity():
    """Create a new entity (Object)."""
    data = request.get_json(silent=True) or {}
    obj_type = data.get("type", "lead")
    obj_data = data.get("data", {})

    entity = Object(object_type=obj_type, state=dict(obj_data))
    db.session.add(entity)
    db.session.commit()

    return jsonify({"entity": _serialize(entity)}), 201


# ---------------------------------------------------------------------------
# 2. Get all entities
# ---------------------------------------------------------------------------


@debug_bp.route("/entities", methods=["GET"])
def list_entities():
    """Return all Objects."""
    entities = Object.query.order_by(Object.id).all()
    return jsonify({"entities": [_serialize(e) for e in entities]})


# ---------------------------------------------------------------------------
# 3. Run one execution cycle
# ---------------------------------------------------------------------------


@debug_bp.route("/run-cycle", methods=["POST"])
def trigger_cycle():
    """Run the runtime loop once."""
    try:
        summary = run_cycle()
        return jsonify({"summary": summary})
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


# ---------------------------------------------------------------------------
# 4. Get full state snapshot
# ---------------------------------------------------------------------------


@debug_bp.route("/state", methods=["GET"])
def get_state():
    """Return current state: entities, tasks, observations."""
    from app.models import Task
    from app.observations.models import Observation as Obs

    entities = Object.query.order_by(Object.id).all()
    tasks = Task.query.order_by(Task.id).all()
    observations = Obs.query.order_by(Obs.id).all()

    return jsonify({
        "entities": [_serialize(e) for e in entities],
        "tasks": [_serialize(t) for t in tasks],
        "observations": [_serialize(o) for o in observations],
    })