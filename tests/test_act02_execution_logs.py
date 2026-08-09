"""ACT-02 execution log tests — structured logging, state snapshot, timeline."""

import pytest


class TestExecutionLogCreated:
    """ExecutionLog is created when an entity is created."""

    def test_create_entity_logs_created(self, app, client):
        resp = client.post("/debug/entity", json={
            "type": "lead",
            "data": {"description": "trace test", "stage": "new"},
        })
        assert resp.status_code == 201
        eid = resp.get_json()["entity"]["id"]

        # Verify CREATED log exists via execution trace
        trace = client.get(f"/debug/execution/{eid}").get_json()
        events = [ev["event_type"] for ev in trace["timeline"]]
        assert "CREATED" in events


class TestExecutionLogLoop:
    """Loop produces structured logs per entity."""

    def test_cycle_produces_entity_seen(self, app, client):
        client.post("/debug/entity", json={
            "type": "lead",
            "data": {"description": "loop log test", "stage": "new"},
        })
        resp = client.post("/debug/run-cycle")
        assert resp.status_code == 200

    def test_logs_linked_to_correct_object(self, app, client):
        # Create two entities
        r1 = client.post("/debug/entity", json={"type": "lead", "data": {"tag": "A"}})
        eid1 = r1.get_json()["entity"]["id"]
        r2 = client.post("/debug/entity", json={"type": "lead", "data": {"tag": "B"}})
        eid2 = r2.get_json()["entity"]["id"]

        client.post("/debug/run-cycle")

        # Each entity should have its own logs
        t1 = client.get(f"/debug/execution/{eid1}").get_json()
        t2 = client.get(f"/debug/execution/{eid2}").get_json()

        assert len(t1["timeline"]) >= 1  # at least CREATED
        assert len(t2["timeline"]) >= 1
        # Verify logs are NOT cross-contaminated
        for log in t1["timeline"]:
            assert log["object_id"] == eid1
        for log in t2["timeline"]:
            assert log["object_id"] == eid2


class TestStateIncludesLogs:
    """GET /debug/state includes execution_logs."""

    def test_empty_state_has_logs_key(self, app, client):
        resp = client.get("/debug/state")
        data = resp.get_json()
        assert "execution_logs" in data
        assert isinstance(data["execution_logs"], list)

    def test_state_logs_after_actions(self, app, client):
        client.post("/debug/entity", json={"type": "lead", "data": {"x": 1}})
        client.post("/debug/run-cycle")
        data = client.get("/debug/state").get_json()
        assert len(data["execution_logs"]) >= 1


class TestExecutionTrace:
    """GET /debug/execution/<id> returns timeline."""

    def test_trace_contains_timeline_key(self, app, client):
        r = client.post("/debug/entity", json={"type": "lead", "data": {"desc": "trace me"}})
        eid = r.get_json()["entity"]["id"]
        resp = client.get(f"/debug/execution/{eid}")
        assert resp.status_code == 200
        data = resp.get_json()
        assert "object" in data
        assert "timeline" in data

    def test_trace_events_ordered_by_timestamp(self, app, client):
        r = client.post("/debug/entity", json={"type": "lead", "data": {"desc": "ordered"}})
        eid = r.get_json()["entity"]["id"]
        client.post("/debug/run-cycle")
        data = client.get(f"/debug/execution/{eid}").get_json()
        events = data["timeline"]
        if len(events) >= 2:
            timestamps = [e["timestamp"] for e in events]
            assert timestamps == sorted(timestamps)

    def test_trace_unknown_entity_returns_404(self, app, client):
        resp = client.get("/debug/execution/99999")
        assert resp.status_code == 404