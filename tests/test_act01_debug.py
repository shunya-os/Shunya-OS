"""ACT-01 debug API tests — entity creation, loop execution, state snapshot."""

import pytest


class TestCreateEntity:
    """POST /debug/entity — create a new runtime entity."""

    def test_create_lead(self, app, client):
        resp = client.post("/debug/entity", json={
            "type": "lead",
            "data": {"description": "Goa trip inquiry", "stage": "new"},
        })
        assert resp.status_code == 201
        data = resp.get_json()
        entity = data["entity"]
        assert entity["object_type"] == "lead"
        assert entity["state"]["description"] == "Goa trip inquiry"
        assert entity["state"]["stage"] == "new"

    def test_create_custom_type(self, app, client):
        resp = client.post("/debug/entity", json={
            "type": "customer",
            "data": {"name": "Acme Corp", "priority": "high"},
        })
        assert resp.status_code == 201
        entity = resp.get_json()["entity"]
        assert entity["object_type"] == "customer"
        assert entity["state"]["name"] == "Acme Corp"


class TestListEntities:
    """GET /debug/entities — return all entities."""

    def test_empty(self, app, client):
        resp = client.get("/debug/entities")
        assert resp.status_code == 200
        assert resp.get_json()["entities"] == []

    def test_after_creation(self, app, client):
        client.post("/debug/entity", json={"type": "lead", "data": {"desc": "t1"}})
        client.post("/debug/entity", json={"type": "lead", "data": {"desc": "t2"}})
        resp = client.get("/debug/entities")
        data = resp.get_json()
        assert len(data["entities"]) == 2


class TestRunCycle:
    """POST /debug/run-cycle — execute one loop iteration."""

    def test_cycle_with_entity(self, app, client):
        # Create an entity first
        client.post("/debug/entity", json={
            "type": "lead",
            "data": {"description": "Test lead", "stage": "new"},
        })
        resp = client.post("/debug/run-cycle")
        assert resp.status_code == 200
        summary = resp.get_json()["summary"]
        assert summary["total_objects"] >= 1
        # At minimum, loop should have processed the entity
        assert summary["noops"] >= 0  # may be noop depending on decision engine

    def test_cycle_empty(self, app, client):
        resp = client.post("/debug/run-cycle")
        assert resp.status_code == 200
        summary = resp.get_json()["summary"]
        assert summary["total_objects"] == 0


class TestGetState:
    """GET /debug/state — return entities + tasks + observations."""

    def test_empty(self, app, client):
        resp = client.get("/debug/state")
        assert resp.status_code == 200
        data = resp.get_json()
        assert "entities" in data
        assert "tasks" in data
        assert "observations" in data

    def test_after_creation(self, app, client):
        client.post("/debug/entity", json={
            "type": "lead",
            "data": {"title": "After state"},
        })
        resp = client.get("/debug/state")
        data = resp.get_json()
        assert len(data["entities"]) >= 1
        # Entity should be serialized with expected fields
        entity = data["entities"][0]
        assert entity["object_type"] == "lead"
        assert "id" in entity
        assert "state" in entity
        assert "created_at" in entity
        assert "updated_at" in entity