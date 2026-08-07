def test_loop_runs(app, client):
    c = client.post("/api/v1/commitments/", json={"title": "Test"}).get_json()

    from app.runtime.loop import run_cycle
    run_cycle()

    assert True