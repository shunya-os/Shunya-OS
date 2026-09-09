def test_full_flow(app, client):
    # Set up auth context
    from tests.auth_helper import seed_rbac
    from app import db
    from app.auth import TeamMember
    with app.app_context():
        org_id = seed_rbac(db)
    admin = TeamMember.query.filter_by(email="admin@test.com").first()
    if not admin:
        admin = TeamMember(name="Admin", email="admin@test.com", role="admin", is_active=True)
        admin.set_password("test")
        db.session.add(admin)
        db.session.commit()
    with client.session_transaction() as sess:
        sess["user_id"] = admin.id
        sess["identity_id"] = "test_identity"
        sess["current_org_id"] = str(org_id)

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
