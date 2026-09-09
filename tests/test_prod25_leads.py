def test_create_lead(app, client):
    from app.models import set_lead_tenant_id
    from app.tenant import Tenant
    from tests.auth_helper import seed_rbac
    from app import db

    with app.app_context():
        t = Tenant(company_name="LeadsCo", slug="leadsco", business_type="tech", is_active=True)
        db.session.add(t)
        db.session.commit()
        set_lead_tenant_id(t.id)
        org_id = seed_rbac(db)

    # Set up auth context — use logged_in_client via session
    with client.session_transaction() as session:
        from app.auth import TeamMember
        admin = TeamMember.query.filter_by(email="admin@test.com").first()
        if not admin:
            admin = TeamMember(name="Admin", email="admin@test.com", role="admin", is_active=True)
            admin.set_password("test")
            db.session.add(admin)
            db.session.commit()
        session["user_id"] = admin.id
        session["identity_id"] = "test_identity"
        session["current_org_id"] = org_id
        session["_fresh"] = True

    res = client.post("/api/v1/leads/", json={"source": "instagram"})
    data = res.get_json()

    assert "id" in data