from app import db
from app.execution_engine.models import Execution, ExecutionLog


class ExecutionService:

    @staticmethod
    def create_execution(object_id: int, decision: str):
        exe = Execution(
            object_id=object_id,
            decision=decision
        )
        db.session.add(exe)
        db.session.commit()
        return exe

    @staticmethod
    def update_status(exe: Execution, status: str):
        exe.status = status
        db.session.commit()
        return exe


def log_execution(
    object_id: int,
    action_type: str,
    payload: dict | None = None,
    state_before: dict | None = None,
    state_after: dict | None = None,
) -> ExecutionLog:
    """Record a structural execution log entry — pure history, no business logic.

    Safe to call after every state mutation. Each entry is an immutable time-
    stamped record of what changed, before, and after.

    Args:
        object_id: The object whose state changed.
        action_type: Machine-readable action label (e.g. 'update', 'activate').
        payload: The action payload that drove the change.
        state_before: Snapshot of object state before the action.
        state_after: Snapshot of object state after the action.

    Returns:
        The persisted ExecutionLog record.
    """
    entry = ExecutionLog(
        object_id=object_id,
        action_type=action_type,
        payload=payload or {},
        state_before=state_before or {},
        state_after=state_after or {},
    )
    db.session.add(entry)
    db.session.commit()
    return entry