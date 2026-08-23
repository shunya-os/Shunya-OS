def test_create_lead(app, client):
    from app.models import set_lead_tenant_id
    from app.tenant import Tenant
    with app.app_context():
        t = Tenant(company_name="LeadsCo", slug="leadsco", business_type="tech", is_active=True)
        from app import db
        db.session.add(t)
        db.session.commit()
        set_lead_tenant_id(t.id)
    res = client.post("/api/v1/leads/", json={"source": "instagram"})
    data = res.get_json()

    assert "id" in data
