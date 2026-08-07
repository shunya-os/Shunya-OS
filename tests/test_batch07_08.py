"""BATCH-07-08 tests: PROD-46 through PROD-54."""


def test_entity_api(client):
    res = client.get("/api/v1/entities/")
    assert res.status_code == 200


def test_timeline(client):
    res = client.get("/api/v1/entities/1/timeline")
    assert res.status_code in [200, 404]