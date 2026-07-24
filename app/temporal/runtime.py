"""
SHUNYA Temporal Intelligence — Runtime Bootstrap and Middleware

Wires temporal intelligence into the Flask app.
No new routes. No new UI. Extends ?inspect= for temporal chain.
"""

from flask import request, jsonify
from datetime import datetime, timezone

from app.temporal.snapshot import capture_snapshot, get_store as get_snap_store
from app.temporal.trajectory import compute_trajectory, get_store as get_traj_store
from app.temporal.timeline import get_timeline, TimelineEvent
from app.temporal.trend import detect_trend, get_store as get_trend_store
from app.temporal.forecast import forecast_metric, forecast_all, get_store as get_forecast_store


def register_temporal_middleware(app) -> None:
    """Register temporal middleware on the Flask app.

    Extends ?inspect= for temporal chain.
    Adds ?inspect_temporal=1 for full temporal system state.
    """

    @app.before_request
    def _check_temporal_inspect():
        if request.args.get("inspect_temporal"):
            return jsonify(_inspect_temporal())
        if request.args.get("inspect_history"):
            return jsonify(_inspect_history())
        return None


def _inspect_temporal() -> dict:
    """Inspect the full temporal system state."""
    snap_store = get_snap_store()
    traj_store = get_traj_store()
    timeline = get_timeline()
    trend_store = get_trend_store()
    forecast_store = get_forecast_store()

    return {
        "snapshots": {
            "total": snap_store.count,
            "latest": snap_store.latest.to_dict() if snap_store.latest else None,
        },
        "trajectories": {
            "total": traj_store.count,
            "latest": traj_store.get_latest().to_dict() if traj_store.get_latest() else None,
        },
        "timeline": {
            "total": timeline.count,
            "recent": [e.to_dict() for e in timeline.get_events(limit=10)],
        },
        "trends": {
            "total": trend_store.count,
            "items": [t.to_dict() for t in trend_store.get_all()],
        },
        "forecasts": {
            "total": forecast_store.count,
            "items": [f.to_dict() for f in forecast_store.get_all()],
        },
        "inspection_timestamp": datetime.now(timezone.utc).isoformat(),
    }


def _inspect_history() -> dict:
    """Inspect the full snapshot history with trajectory."""
    snap_store = get_snap_store()
    snapshots = snap_store.get_all(limit=20)
    traj_store = get_traj_store()

    # Compute trends from snapshot series
    if snapshots:
        health_values = [s.overall_health for s in snapshots]
        trend = detect_trend("overall_health", health_values)
        forecasts = forecast_all(snapshots, horizon=3)
    else:
        trend = None
        forecasts = []

    return {
        "snapshots": [s.to_dict() for s in snapshots],
        "trajectories": [t.to_dict() for t in traj_store.get_all(limit=10)],
        "trend": trend.to_dict() if trend else None,
        "forecasts": [f.to_dict() for f in forecasts],
        "inspection_timestamp": datetime.now(timezone.utc).isoformat(),
    }


def load_temporal_data() -> None:
    """Load temporal data. Captures initial snapshot and computes baseline.

    Called once at startup. Creates the first snapshot for baseline comparison.
    """
    snap_store = get_snap_store()
    traj_store = get_traj_store()
    timeline = get_timeline()
    trend_store = get_trend_store()
    forecast_store = get_forecast_store()

    # Capture initial snapshot
    sn1 = capture_snapshot("Organization")
    snap_store.add(sn1)

    timeline.record(
        event_type="snapshot_captured", source="temporal",
        label="Initial snapshot captured",
        description="Baseline organizational state recorded",
        metadata={"snapshot_id": sn1.snapshot_id},
    )

    # Capture a second snapshot (slightly different data for trajectory)
    # In production, snapshots would be captured on a schedule
    sn2 = capture_snapshot("Organization")
    snap_store.add(sn2)

    timeline.record(
        event_type="snapshot_captured", source="temporal",
        label="Second snapshot captured",
        description="Comparison snapshot for baseline trajectory",
        metadata={"snapshot_id": sn2.snapshot_id},
    )

    # Compute trajectory
    if snap_store.count >= 2:
        snaps = snap_store.get_latest(2)
        traj = compute_trajectory(snaps[0], snaps[1])
        traj_store.add(traj)

        timeline.record(
            event_type="trajectory_computed", source="temporal",
            label="Baseline trajectory computed",
            description=f"Overall health: {traj.overall_health_direction}",
            metadata={
                "from": traj.snapshot_previous_id,
                "to": traj.snapshot_current_id,
            },
        )

    # Compute trends
    snapshots = snap_store.get_all()
    if snapshots:
        health_values = [s.overall_health for s in snapshots]
        trend = detect_trend("overall_health", health_values)
        trend_store.add(trend)

        # Forecast
        forecasts = forecast_all(snapshots, horizon=3)
        for f in forecasts:
            forecast_store.add(f)