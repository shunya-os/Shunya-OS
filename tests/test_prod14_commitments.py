def test_commitment_lifecycle(app, client):
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

    # create
    res = client.post("/api/v1/commitments/", json={
        "title": "Send itinerary",
        "owner": "agent_1"
    })
    data = res.get_json()
    cid = data["id"]

    assert data["status"] == "pending"

    # update
    res2 = client.patch(f"/api/v1/commitments/{cid}", json={
        "status": "completed"
    })

    assert res2.get_json()["status"] == "completed"