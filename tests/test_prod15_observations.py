def test_observation_flow(app, client):
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

    # create commitment first
    c = client.post("/api/v1/commitments/", json={
        "title": "Deliver itinerary"
    }).get_json()

    cid = c["id"]

    # record observation
    res = client.post("/api/v1/observations/", json={
        "commitment_id": cid,
        "observed_value": {"delivered": True},
        "expected_value": {"delivered": True}
    })

    obs = res.get_json()
    oid = obs["id"]

    assert obs["status"] == "recorded"

    # evaluate
    res2 = client.post(f"/api/v1/observations/{oid}/evaluate")

    assert res2.get_json()["status"] == "matched"