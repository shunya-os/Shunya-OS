def test_overdue(app, client):
    from datetime import datetime, timedelta, timezone

    c = client.post("/api/v1/commitments/", json={
        "title": "Late",
        "owner": "x",
        "due_at": (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()
    }).get_json()

    from app.commitments.models import Commitment
    from app.commitments.service import check_overdue

    obj = Commitment.query.get(c["id"])
    updated = check_overdue(obj)

    assert updated.status == "failed"