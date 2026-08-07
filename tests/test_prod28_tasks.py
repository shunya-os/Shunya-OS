def test_lead_task_decision(app, client):
    from app import db
    from app.models import Lead, next_inquiry_code
    from app.runtime.decision_engine import decide_lead_task

    code = next_inquiry_code(db.session)
    lead = Lead(source="test", code=code)
    db.session.add(lead)
    db.session.commit()

    decision = decide_lead_task(lead)
    # lead has no tasks → returns update with task
    assert decision["type"] == "update"
    assert "task" in decision.get("payload", {})