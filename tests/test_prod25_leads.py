def test_create_lead(app, client):
    res = client.post("/api/v1/leads/", json={"source": "instagram"})
    data = res.get_json()

    assert "id" in data