"""
SHUNYA Temporal Intelligence — Forecast Engine

Forecast only from observed trajectory. Never hallucinate.

Produces: Expected Future Value, Prediction Confidence, Prediction Horizon,
          Required Assumptions. Predictions explain themselves.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional

from app.temporal.trend import detect_trend, Trend
from app.temporal.snapshot import TemporalSnapshot
from app.temporal.trajectory import Trajectory


@dataclass
class Forecast:
    """A forecast for a single metric, derived from observed trajectory."""

    metric_name: str
    current_value: float
    predicted_value: float
    confidence: float
    """0.0 to 1.0 — how confident in this prediction."""

    horizon_steps: int
    """How many steps into the future this prediction extends."""

    slope: float = 0.0
    trend_direction: str = "stable"
    assumptions: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "metric_name": self.metric_name,
            "current_value": round(self.current_value, 4),
            "predicted_value": round(self.predicted_value, 4),
            "confidence": round(self.confidence, 4),
            "horizon_steps": self.horizon_steps,
            "slope": round(self.slope, 4),
            "trend_direction": self.trend_direction,
            "assumptions": self.assumptions,
        }


def forecast_metric(
    metric_name: str,
    values: list[float],
    horizon_steps: int = 3,
) -> Forecast:
    """Forecast a metric from its observed values.

    Pure mathematical extrapolation. No business assumptions.
    Never hallucinates. If insufficient data, returns current value with low confidence.
    """
    n = len(values)

    if n == 0:
        return Forecast(
            metric_name=metric_name, current_value=0.0, predicted_value=0.0,
            confidence=0.0, horizon_steps=horizon_steps,
        )

    current = values[-1]

    if n < 2:
        return Forecast(
            metric_name=metric_name, current_value=current, predicted_value=current,
            confidence=0.1, horizon_steps=horizon_steps,
            assumptions=["Insufficient data for prediction"],
        )

    # Detect trend
    trend = detect_trend(metric_name, values)

    # Simple linear extrapolation
    if abs(trend.slope) < 0.001:
        predicted = current
        confidence = 0.3
        assumptions = ["Metric is stable or oscillating"]
    else:
        predicted = current + trend.slope * horizon_steps
        confidence = trend.confidence * 0.8  # Discount for extrapolation
        # Confidence decays with horizon
        confidence *= max(0.3, 1.0 - horizon_steps * 0.1)
        assumptions = [
            f"Linear extrapolation from {n} data points",
            f"Trend slope: {trend.slope:.4f} per step",
            f"Trend direction: {trend.direction}",
        ]

    # Clamp to reasonable range
    min_val = min(values) * 0.5 if values else 0.0
    max_val = max(values) * 1.5 if values else 1.0
    predicted = max(min_val, min(max_val, predicted))

    # If oscillating, predict mean
    if trend.direction == "oscillating":
        predicted = trend.mean
        confidence = 0.3
        assumptions = ["Metric is oscillating — predicting mean value"]

    return Forecast(
        metric_name=metric_name,
        current_value=current,
        predicted_value=predicted,
        confidence=min(confidence, 1.0),
        horizon_steps=horizon_steps,
        slope=trend.slope,
        trend_direction=trend.direction,
        assumptions=assumptions,
    )


def forecast_all(snapshots: list[TemporalSnapshot], horizon: int = 3) -> list[Forecast]:
    """Forecast all key metrics from a series of snapshots."""
    if not snapshots:
        return []

    # Extract metric series
    metric_series: dict[str, list[float]] = {
        "overall_health": [],
        "total_decisions": [],
        "active_commitments": [],
        "active_observations": [],
        "total_insights": [],
        "learning_signals": [],
        "waiting_approval": [],
        "critical_risks": [],
    }

    for snap in snapshots:
        d = snap.to_dict()
        metrics = d.get("metrics", {})
        metric_series["overall_health"].append(snap.overall_health)
        for key in ["total_decisions", "active_commitments", "active_observations",
                     "total_insights", "learning_signals", "waiting_approval", "critical_risks"]:
            metric_series[key].append(float(metrics.get(key, 0)))

    forecasts = []
    for name, values in metric_series.items():
        if values:
            forecasts.append(forecast_metric(name, values, horizon))

    return forecasts


class ForecastStore:
    def __init__(self):
        self._forecasts: list[Forecast] = []

    def add(self, forecast: Forecast) -> None:
        self._forecasts.append(forecast)

    def get_all(self) -> list[Forecast]:
        return list(self._forecasts)

    def get_by_metric(self, metric_name: str) -> Optional[Forecast]:
        for f in self._forecasts:
            if f.metric_name == metric_name:
                return f
        return None

    @property
    def count(self) -> int:
        return len(self._forecasts)

    def clear(self) -> None:
        self._forecasts.clear()


_store: Optional[ForecastStore] = None


def get_store() -> ForecastStore:
    global _store
    if _store is None:
        _store = ForecastStore()
    return _store


def reset_store() -> None:
    global _store
    _store = None