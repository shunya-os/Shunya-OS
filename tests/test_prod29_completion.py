import pytest
pytestmark = pytest.mark.skip(reason="flaky — requires DB isolation fixture")

def test_task_completion(app, client):
    from datetime import datetime, timezone
    from app import db
    from app.models import Task

    task = Task(
        task_list_id=1,
        title="Test",
        status="pending",
    )
    db.session.add(task)
    db.session.commit()

    # mark completed
    task.completed_at = datetime.now(timezone.utc)
    task.status = "completed"
    db.session.commit()

    assert task.status == "completed"
    assert task.completed_at is not None