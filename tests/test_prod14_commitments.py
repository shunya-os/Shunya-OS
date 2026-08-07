def test_commitment_lifecycle(app, client):
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