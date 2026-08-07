def test_full_flow(app, client):
    res = client.post("/api/v1/leads/", json={"source": "instagram"})
    lead_id = res.get_json()["id"]

    from app.runtime.loop import run_cycle
    from app.models import Lead

    for _ in range(5):
        run_cycle()

    lead = Lead.query.get(lead_id)

    assert lead.stage in ["contacted", "quoted", "closed"]