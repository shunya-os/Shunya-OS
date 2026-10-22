"""G1.28 — /metrics must not report database health it has not observed.

The defect: the JSON fallback (used when ``prometheus_client`` is unavailable)
hardcoded ``shunya_db_up: 1``, so a dead database still reported healthy.

The fallback is only reachable by making the import fail; that is what these tests
do (``sys.modules['prometheus_client'] = None`` makes the import raise
ImportError), then they drive a healthy probe and a broken engine.
"""
import os

import pytest

from app import db


@pytest.fixture
def fallback_metrics(monkeypatch):
    """Force the JSON fallback path."""
    monkeypatch.setitem(__import__("sys").modules, "prometheus_client", None)
    return monkeypatch


def _get(client):
    token = os.environ.get("HEALTH_TOKEN") or ""
    url = "/metrics" + (f"?token={token}" if token else "")
    return client.get(url)


def test_fallback_reports_an_observed_healthy_database(client, fallback_metrics):
    resp = _get(client)
    assert resp.status_code == 200
    body = resp.get_json()
    assert body is not None, "fallback must return JSON"
    assert body["shunya_db_check"] == "ok"
    assert body["shunya_db_up"] == 1


def test_fallback_reports_a_failed_database_instead_of_healthy(client, fallback_metrics):
    from unittest.mock import patch

    def _raise(self):
        raise RuntimeError("database is down")

    # ``SQLAlchemy.engine`` is a read-only property, so break the engine's connect
    # for the duration of the request only — patching it via `monkeypatch` keeps
    # it active during fixture teardown and breaks the session cleanup.
    with patch("sqlalchemy.engine.Engine.connect", _raise):
        resp = _get(client)
    assert resp.status_code == 200, "the metrics endpoint itself stays available"
    body = resp.get_json()
    assert body["shunya_db_check"] == "error"
    assert body["shunya_db_up"] == 0, "a down database must never report up"
