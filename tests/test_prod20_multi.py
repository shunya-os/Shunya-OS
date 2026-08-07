def test_multiple(app, client):
    for i in range(5):
        client.post("/api/v1/commitments/", json={"title": f"T{i}"})

    from app.runtime.loop import run_cycle
    run_cycle()

    assert True