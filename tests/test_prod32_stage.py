def test_stage_transition_attempted(app, client):
    """Stage progression is driven by the canonical CRM pipeline, not run_cycle."""
    from app import db
    from app.models import Lead, next_inquiry_code, set_lead_tenant_id
    from app.tenant import Tenant
    with app.app_context():
        t = Tenant(company_name="TransitionCo", slug="transitionco", business_type="tech", is_active=True)
        db.session.add(t)
        db.session.commit()
        set_lead_tenant_id(t.id)
        code = next_inquiry_code(db.session)
        lead = Lead(source="test", code=code)
        db.session.add(lead)
        db.session.commit()
        # A new lead starts at stage "new"
        assert lead.stage == "new"
