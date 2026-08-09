"""Debug control API — first human operating surface for SHUNYA runtime."""

from app.core.time import now

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


# ---------------------------------------------------------------------------
# 6. Update entity (name, phone, email, stage)
# ---------------------------------------------------------------------------


@debug_bp.route("/entity/<int:entity_id>", methods=["PUT"])
def update_entity(entity_id):
    """Update entity state fields."""
    entity = db.session.get(Object, entity_id)
    if entity is None:
        return jsonify({"error": "Entity not found"}), 404

    data = request.get_json(silent=True) or {}
    updates = data.get("state", data)

    # Merge state updates
    current_state = dict(entity.state or {})
    for k, v in updates.items():
        if v is not None:
            current_state[k] = v
    entity.state = current_state

    log_execution(entity.id, "UPDATED", {"state_updates": updates})
    db.session.commit()

    return jsonify({"entity": _serialize(entity)})


# ---------------------------------------------------------------------------
# 7. List tasks for an entity
# ---------------------------------------------------------------------------


@debug_bp.route("/tasks", methods=["GET"])
def list_tasks():
    """Return tasks, optionally filtered by entity_id."""
    from app.models import Task

    entity_id = request.args.get("entity_id", type=int)
    query = Task.query
    if entity_id:
        query = query.filter_by(entity_id=entity_id)
    tasks = query.order_by(Task.created_at.desc()).all()
    return jsonify({"tasks": [_serialize(t) for t in tasks]})


# ---------------------------------------------------------------------------
# 8. Complete a task
# ---------------------------------------------------------------------------


@debug_bp.route("/tasks/<int:task_id>/complete", methods=["POST"])
def complete_task(task_id):
    """Mark a task as completed."""
    from app.models import Task

    task = db.session.get(Task, task_id)
    if task is None:
        return jsonify({"error": "Task not found"}), 404

    task.status = "completed"
    task.completed_at = now()
    db.session.commit()

    return jsonify({"task": _serialize(task)})


# ---------------------------------------------------------------------------
# 9. Notes on entity (stored in entity context JSON)
# ---------------------------------------------------------------------------


@debug_bp.route("/entity/<int:entity_id>/notes", methods=["GET"])
def get_entity_notes(entity_id):
    """Get notes stored on an entity's context."""
    entity = db.session.get(Object, entity_id)
    if entity is None:
        return jsonify({"error": "Entity not found"}), 404

    ctx = entity.context or {}
    notes = ctx.get("notes", "")
    return jsonify({"notes": notes, "entity_id": entity_id})


@debug_bp.route("/entity/<int:entity_id>/notes", methods=["POST"])
def save_entity_notes(entity_id):
    """Save notes on an entity's context."""
    entity = db.session.get(Object, entity_id)
    if entity is None:
        return jsonify({"error": "Entity not found"}), 404

    data = request.get_json(silent=True) or {}
    notes = data.get("notes", "")

    ctx = dict(entity.context or {})
    ctx["notes"] = notes
    entity.context = ctx

    log_execution(entity.id, "NOTES_SAVED", {"notes_length": len(notes)})
    db.session.commit()

    return jsonify({"notes": notes, "entity_id": entity_id})