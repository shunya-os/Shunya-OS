def test_task_creation(app, client):
    from app import db
    from app.models import Task

    task = Task(
        task_list_id=1,
        title="Call customer",
        description="Follow up on lead",
    )
    db.session.add(task)
    db.session.commit()

    assert task.status == "pending"