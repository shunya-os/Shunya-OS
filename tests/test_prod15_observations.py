def test_observation_flow(app, client):
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