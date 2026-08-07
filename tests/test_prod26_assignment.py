def test_lead_assigned_default(app, client):
    from app import db
    from app.models import Lead, next_inquiry_code
    code = next_inquiry_code(db.session)
    lead = Lead(source="test", code=code)
    db.session.add(lead)
    db.session.commit()
    assert lead.assigned_to is None