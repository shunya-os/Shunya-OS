"""
Tests for SHUNYA Temporal Intelligence — Phase Z6.

Validates:
  - Snapshot creation and immutability
  - Trajectory computation
  - Trend detection
  - Forecast generation
  - Timeline recording
  - Temporal inspection
  - Business agnosticism
"""

import pytest


@pytest.fixture(autouse=True)
def _app_context(app):
    """Provide Flask app context for tests that access DB."""
    pass
from app.temporal.snapshot import (
    TemporalSnapshot, SnapshotStore, capture_snapshot, get_store, reset_store,
)
from app.temporal.trajectory import (
    Trajectory, ChangeRecord, compute_trajectory, get_store as get_traj_store,
    reset_store as reset_traj_store,
)
from app.temporal.timeline import Timeline, TimelineEvent, get_timeline, reset_timeline
from app.temporal.trend import detect_trend, Trend, get_store as get_trend_store, reset_store as reset_trend_store
from app.temporal.forecast import forecast_metric, forecast_all, get_store as get_forecast_store, reset_store as reset_forecast_store


# ══════════════════════════════════════════════════════════════
# Snapshot Tests
# ══════════════════════════════════════════════════════════════


class TestTemporalSnapshot:
    def test_snapshot_creation(self):
        snap = TemporalSnapshot(
            snapshot_id="snap_001", timestamp="2026-07-24T00:00:00",
            organization_name="TestOrg",
            overall_health=0.85, total_decisions=10, active_commitments=5,
        )
        assert snap.snapshot_id == "snap_001"
        assert snap.overall_health == 0.85
        assert snap.total_decisions == 10

    def test_snapshot_immutability(self):
        snap = TemporalSnapshot(
            snapshot_id="snap_001", timestamp="2026-07-24T00:00:00",
        )
        with pytest.raises(Exception):  # Frozen dataclass
            snap.overall_health = 0.9

    def test_snapshot_to_dict(self):
        snap = TemporalSnapshot(
            snapshot_id="snap_001", timestamp="2026-07-24T00:00:00",
            organization_name="TestOrg", overall_health=0.85,
        )
        d = snap.to_dict()
        assert d["snapshot_id"] == "snap_001"
        assert d["overall_health"] == 0.85
        assert "metrics" in d


class TestSnapshotStore:
    def setup_method(self):
        reset_store()

    def test_add_and_get(self):
        store = get_store()
        snap = TemporalSnapshot(snapshot_id="s1", timestamp="now")
        store.add(snap)
        assert store.get("s1") is snap
        assert store.count == 1

    def test_duplicate_rejected(self):
        store = get_store()
        store.add(TemporalSnapshot(snapshot_id="s1", timestamp="now"))
        with pytest.raises(ValueError, match="already exists"):
            store.add(TemporalSnapshot(snapshot_id="s1", timestamp="later"))

    def test_latest(self):
        store = get_store()
        store.add(TemporalSnapshot(snapshot_id="s1", timestamp="t1"))
        store.add(TemporalSnapshot(snapshot_id="s2", timestamp="t2"))
        assert store.latest.snapshot_id == "s2"

    def test_get_latest_n(self):
        store = get_store()
        store.add(TemporalSnapshot(snapshot_id="s1", timestamp="t1"))
        store.add(TemporalSnapshot(snapshot_id="s2", timestamp="t2"))
        store.add(TemporalSnapshot(snapshot_id="s3", timestamp="t3"))
        latest = store.get_latest(2)
        assert len(latest) == 2
        assert latest[0].snapshot_id == "s2"
        assert latest[1].snapshot_id == "s3"

    def test_clear(self):
        store = get_store()
        store.add(TemporalSnapshot(snapshot_id="s1", timestamp="now"))
        store.clear()
        assert store.count == 0


# ══════════════════════════════════════════════════════════════
# Trajectory Tests
# ══════════════════════════════════════════════════════════════


class TestTrajectory:
    def test_change_record(self):
        cr = ChangeRecord(metric_name="health", current_value=0.9, previous_value=0.8,
                          absolute_change=0.1, percentage_change=0.125, direction="up")
        assert cr.is_significant
        assert cr.direction == "up"

    def test_trajectory_computation(self):
        prev = TemporalSnapshot(snapshot_id="s1", timestamp="2026-07-24T00:00:00",
                                overall_health=0.7, total_decisions=5, active_commitments=3)
        curr = TemporalSnapshot(snapshot_id="s2", timestamp="2026-07-24T01:00:00",
                                overall_health=0.85, total_decisions=8, active_commitments=5)
        traj = compute_trajectory(prev, curr)
        assert traj.overall_health_direction == "up"
        assert traj.growth is True
        assert traj.decline is False
        assert len(traj.changes) >= 5

    def test_trajectory_decline(self):
        prev = TemporalSnapshot(snapshot_id="s1", timestamp="2026-07-24T00:00:00",
                                overall_health=0.85, active_commitments=10)
        curr = TemporalSnapshot(snapshot_id="s2", timestamp="2026-07-24T01:00:00",
                                overall_health=0.6, active_commitments=3)
        traj = compute_trajectory(prev, curr)
        assert traj.overall_health_direction == "down"
        assert traj.decline is True

    def test_trajectory_recovery(self):
        prev = TemporalSnapshot(snapshot_id="s1", timestamp="2026-07-24T00:00:00",
                                overall_health=0.3)
        curr = TemporalSnapshot(snapshot_id="s2", timestamp="2026-07-24T01:00:00",
                                overall_health=0.7)
        traj = compute_trajectory(prev, curr)
        assert traj.recovery is True

    def test_trajectory_to_dict(self):
        prev = TemporalSnapshot(snapshot_id="s1", timestamp="now", overall_health=0.5)
        curr = TemporalSnapshot(snapshot_id="s2", timestamp="later", overall_health=0.6)
        traj = compute_trajectory(prev, curr)
        d = traj.to_dict()
        assert "changes" in d
        assert "momentum" in d
        assert "volatility" in d


# ══════════════════════════════════════════════════════════════
# Timeline Tests
# ══════════════════════════════════════════════════════════════


class TestTimeline:
    def setup_method(self):
        reset_timeline()

    def test_record_event(self):
        tl = get_timeline()
        evt = tl.record("snapshot_captured", "temporal", "Test event", "Description")
        assert evt.event_id is not None
        assert evt.event_type == "snapshot_captured"
        assert tl.count == 1

    def test_get_events_by_source(self):
        tl = get_timeline()
        tl.record("type_a", "source_a", "Event A")
        tl.record("type_b", "source_b", "Event B")
        events = tl.get_by_source("source_a")
        assert len(events) == 1
        assert events[0].label == "Event A"

    def test_get_events_by_type(self):
        tl = get_timeline()
        tl.record("decision", "src", "Decision made")
        tl.record("snapshot", "src", "Snapshot taken")
        events = tl.get_events(event_type="decision")
        assert len(events) == 1

    def test_timeline_clear(self):
        tl = get_timeline()
        tl.record("test", "test", "Test")
        tl.clear()
        assert tl.count == 0


# ══════════════════════════════════════════════════════════════
# Trend Detection Tests
# ══════════════════════════════════════════════════════════════


class TestTrend:
    def test_improving_trend(self):
        trend = detect_trend("health", [0.5, 0.6, 0.7, 0.8, 0.9])
        assert trend.direction == "improving"
        assert trend.slope > 0
        assert trend.confidence >= 0.5

    def test_declining_trend(self):
        trend = detect_trend("health", [0.9, 0.8, 0.7, 0.6, 0.5])
        assert trend.direction == "declining"
        assert trend.slope < 0

    def test_stable_trend(self):
        trend = detect_trend("health", [0.7, 0.71, 0.69, 0.7, 0.71])
        # These values oscillate around a stable mean
        assert trend.direction in ("stable", "oscillating")

    def test_oscillating_trend(self):
        trend = detect_trend("health", [0.9, 0.3, 0.8, 0.4, 0.85])
        assert trend.direction == "oscillating"

    def test_recovered_trend(self):
        trend = detect_trend("health", [0.3, 0.35, 0.4, 0.6, 0.75])
        assert trend.direction in ("recovered", "improving")

    def test_single_value(self):
        trend = detect_trend("health", [0.8])
        assert trend.direction == "stable"
        assert trend.confidence == 0.3

    def test_empty_values(self):
        trend = detect_trend("health", [])
        assert trend.direction == "stable"
        assert trend.confidence == 0.0

    def test_trend_to_dict(self):
        trend = detect_trend("health", [0.5, 0.6, 0.7])
        d = trend.to_dict()
        assert "metric_name" in d
        assert "direction" in d
        assert "slope" in d


# ══════════════════════════════════════════════════════════════
# Forecast Tests
# ══════════════════════════════════════════════════════════════


class TestForecast:
    def test_forecast_improving(self):
        forecast = forecast_metric("health", [0.5, 0.6, 0.7, 0.8], horizon_steps=2)
        assert forecast.predicted_value > forecast.current_value
        assert forecast.confidence > 0.0

    def test_forecast_declining(self):
        forecast = forecast_metric("health", [0.9, 0.8, 0.7, 0.6], horizon_steps=2)
        assert forecast.predicted_value < forecast.current_value
        assert forecast.confidence > 0.0

    def test_forecast_insufficient_data(self):
        forecast = forecast_metric("health", [0.8], horizon_steps=3)
        assert forecast.predicted_value == 0.8
        assert forecast.confidence < 0.5

    def test_forecast_empty_data(self):
        forecast = forecast_metric("health", [], horizon_steps=3)
        assert forecast.predicted_value == 0.0
        assert forecast.confidence == 0.0

    def test_forecast_to_dict(self):
        forecast = forecast_metric("health", [0.5, 0.6, 0.7])
        d = forecast.to_dict()
        assert "metric_name" in d
        assert "predicted_value" in d
        assert "confidence" in d
        assert "assumptions" in d

    def test_forecast_all(self):
        from app.temporal.snapshot import TemporalSnapshot
        snaps = [
            TemporalSnapshot(snapshot_id="s1", timestamp="t1", overall_health=0.5,
                             total_decisions=5, active_commitments=3),
            TemporalSnapshot(snapshot_id="s2", timestamp="t2", overall_health=0.6,
                             total_decisions=7, active_commitments=4),
            TemporalSnapshot(snapshot_id="s3", timestamp="t3", overall_health=0.7,
                             total_decisions=9, active_commitments=5),
        ]
        forecasts = forecast_all(snaps, horizon=2)
        assert len(forecasts) == 8
        assert forecasts[0].metric_name == "overall_health"
        assert forecasts[0].predicted_value > 0.7


# ══════════════════════════════════════════════════════════════
# Business Agnosticism Tests
# ══════════════════════════════════════════════════════════════


class TestBusinessAgnosticism:
    def test_temporal_snapshot_no_industry(self):
        snap = TemporalSnapshot(snapshot_id="s1", timestamp="now")
        assert not hasattr(snap, "industry")
        assert not hasattr(snap, "vertical")

    def test_trajectory_no_industry(self):
        prev = TemporalSnapshot(snapshot_id="s1", timestamp="now")
        curr = TemporalSnapshot(snapshot_id="s2", timestamp="later")
        traj = compute_trajectory(prev, curr)
        assert not hasattr(traj, "industry")
        assert not hasattr(traj, "vertical")

    def test_trend_no_industry(self):
        trend = detect_trend("health", [0.5, 0.6, 0.7])
        assert not hasattr(trend, "industry")
        assert not hasattr(trend, "vertical")


# ══════════════════════════════════════════════════════════════
# Temporal Integration Tests
# ══════════════════════════════════════════════════════════════


class TestTemporalIntegration:
    def test_temporal_loads_with_app(self):
        from app import create_app
        app = create_app({'TESTING': True, 'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:'})
        with app.test_client() as c:
            assert c.get('/').status_code == 200
            assert c.get('/workspace/').status_code == 200

            # Verify temporal inspection
            r = c.get('/workspace/?inspect_temporal=1')
            assert r.status_code == 200
            data = r.get_json()
            assert data is not None
            assert 'snapshots' in data
            assert 'trajectories' in data
            assert 'timeline' in data
            assert 'trends' in data
            assert 'forecasts' in data

            # Verify history inspection
            r = c.get('/workspace/?inspect_history=1')
            assert r.status_code == 200
            data = r.get_json()
            assert 'snapshots' in data
            assert 'trajectories' in data
            assert 'trend' in data
            assert 'forecasts' in data

    def test_snapshots_captured_on_startup(self):
        from app import create_app
        app = create_app({'TESTING': True, 'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:'})
        with app.test_client() as c:
            r = c.get('/workspace/?inspect_temporal=1')
            data = r.get_json()
            assert data['snapshots']['total'] >= 2, "Should have at least 2 snapshots from startup"
            assert data['snapshots']['latest'] is not None

    def test_trajectory_computed_on_startup(self):
        from app import create_app
        app = create_app({'TESTING': True, 'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:'})
        with app.test_client() as c:
            r = c.get('/workspace/?inspect_temporal=1')
            data = r.get_json()
            assert data['trajectories']['total'] >= 1

    def test_timeline_has_events(self):
        from app import create_app
        app = create_app({'TESTING': True, 'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:'})
        with app.test_client() as c:
            r = c.get('/workspace/?inspect_temporal=1')
            data = r.get_json()
            assert data['timeline']['total'] >= 2