"""Debug control API — first human operating surface for SHUNYA runtime."""

from datetime import datetime, timezone

from flask import jsonify, request

from app import db
from app.debug import debug_bp
from app.objects.models import Object
from app.runtime.loop import run_cycle
from app.execution_log.models import ExecutionLog, log_execution


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
    db.session.flush()

    log_execution(entity.id, "CREATED", {
        "object_type": obj_type,
        "state": dict(obj_data),
    })
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
    """Return current state: entities, tasks, observations, execution logs."""
    from app.models import Task
    from app.observations.models import Observation as Obs

    entities = Object.query.order_by(Object.id).all()
    tasks = Task.query.order_by(Task.id).all()
    observations = Obs.query.order_by(Obs.id).all()
    logs = ExecutionLog.query.order_by(ExecutionLog.timestamp.desc()).limit(100).all()

    return jsonify({
        "entities": [_serialize(e) for e in entities],
        "tasks": [_serialize(t) for t in tasks],
        "observations": [_serialize(o) for o in observations],
        "execution_logs": [l.to_dict() for l in logs],
    })


# ---------------------------------------------------------------------------
# 5. Execution trace for a specific object
# ---------------------------------------------------------------------------


@debug_bp.route("/execution/<int:object_id>", methods=["GET"])
def get_execution_trace(object_id):
    """Return the execution timeline for a single object."""
    entity = db.session.get(Object, object_id)
    if entity is None:
        return jsonify({"error": "Object not found"}), 404

    logs = (
        ExecutionLog.query
        .filter_by(object_id=object_id)
        .order_by(ExecutionLog.timestamp.asc())
        .all()
    )

    return jsonify({
        "object": _serialize(entity),
        "timeline": [l.to_dict() for l in logs],
    })