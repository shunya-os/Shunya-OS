def test_lead_outcome(app, client):
    from app import db
    from app.models import Lead, next_inquiry_code
    from app.runtime.loop import run_cycle

    code = next_inquiry_code(db.session)
    lead = Lead(source="test", code=code)
    db.session.add(lead)
    db.session.commit()

    run_cycle()

    db.session.refresh(lead)
    assert lead.outcome is not None