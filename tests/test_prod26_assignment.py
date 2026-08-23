def test_lead_assigned_default(app, client):
    from app import db
    from app.models import Lead, next_inquiry_code, set_lead_tenant_id
    from app.tenant import Tenant
    with app.app_context():
        t = Tenant(company_name="AssignCo", slug="assignco", business_type="tech", is_active=True)
        db.session.add(t)
        db.session.commit()
        set_lead_tenant_id(t.id)
        code = next_inquiry_code(db.session)
        lead = Lead(source="test", code=code)
        db.session.add(lead)
        db.session.commit()
        assert lead.assigned_to is None
