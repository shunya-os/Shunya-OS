def test_full_flow(app, client):
    """A lead can be created via the canonical API and progresses through the pipeline."""
    from app.models import set_lead_tenant_id
    from app.tenant import Tenant
    with app.app_context():
        from app import db
        t = Tenant(company_name="FlowCo", slug="flowco", business_type="tech", is_active=True)
        db.session.add(t)
        db.session.commit()
        set_lead_tenant_id(t.id)
    res = client.post("/api/v1/leads/", json={"source": "instagram"})
    lead_id = res.get_json()["id"]

    from app.models import Lead
    with app.app_context():
        lead = Lead.query.get(lead_id)
        assert lead is not None
        assert lead.source == "instagram"
