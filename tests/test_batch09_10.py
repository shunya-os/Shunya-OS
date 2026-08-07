"""BATCH-09-10 tests: PROD-55 through PROD-61."""


def test_webhook(client):
    res = client.post("/api/v1/webhook/", json={"entity_id": 1})
    assert res.status_code == 200