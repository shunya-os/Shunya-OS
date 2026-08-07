def test_retry(app, client):
    c = client.post("/api/v1/commitments/", json={"title": "Retry"}).get_json()

    from app.commitments.models import Commitment
    from app.commitments.service import retry_commitment

    obj = Commitment.query.get(c["id"])
    obj.status = "failed"

    updated = retry_commitment(obj)

    assert updated.status == "pending"