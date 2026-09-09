def test_retry(app, client):
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

    c = client.post("/api/v1/commitments/", json={"title": "Retry"}).get_json()

    from app.commitments.models import Commitment
    from app.commitments.service import retry_commitment

    obj = Commitment.query.get(c["id"])
    obj.status = "failed"

    updated = retry_commitment(obj)

    assert updated.status == "pending"