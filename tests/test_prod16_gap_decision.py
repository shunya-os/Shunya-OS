def test_gap_decision_flow(app, client):
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

    # create commitment
    c = client.post("/api/v1/commitments/", json={
        "title": "Send invoice"
    }).get_json()

    cid = c["id"]

    # record deviation
    obs = client.post("/api/v1/observations/", json={
        "commitment_id": cid,
        "observed_value": {"sent": False},
        "expected_value": {"sent": True}
    }).get_json()

    oid = obs["id"]

    # evaluate → deviated
    client.post(f"/api/v1/observations/{oid}/evaluate")

    # fetch commitment object from DB layer
    from app.commitments.models import Commitment
    from app.runtime.decision_engine import decide_next_from_commitment
    from app.commitments.service import apply_decision

    commitment = Commitment.query.get(cid)

    decision = decide_next_from_commitment(commitment)

    updated = apply_decision(commitment, decision)

    assert updated.status == "failed"