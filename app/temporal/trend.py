"""
SHUNYA Temporal Intelligence — Trend Detection

Universal trend detection from a series of metric values.
Deterministic computation. No business assumptions.

Trends: Improving, Stable, Declining, Accelerating, Decelerating,
         Oscillating, Anomalous, Recovered, Recovered After Failure
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Optional


@dataclass
class Trend:
    """A computed trend for a single metric over a series of snapshots."""

    metric_name: str
    values: list[float]
    direction: str
    """'improving', 'stable', 'declining', 'accelerating', 'decelerating',
       'oscillating', 'anomalous', 'recovered', 'recovered_after_failure'"""

    confidence: float
    """0.0 to 1.0 — how confident the trend detection is."""

    slope: float = 0.0
    """Linear regression slope."""

    mean: float = 0.0
    std_dev: float = 0.0

    def to_dict(self) -> dict:
        return {
            "metric_name": self.metric_name,
            "direction": self.direction,
            "confidence": round(self.confidence, 4),
            "slope": round(self.slope, 4),
            "mean": round(self.mean, 4),
            "std_dev": round(self.std_dev, 4),
            "values": [round(v, 4) for v in self.values],
        }


def detect_trend(metric_name: str, values: list[float]) -> Trend:
    """Detect the trend from a series of metric values.

    Pure mathematical analysis. No business assumptions.
    Requires at least 3 values for meaningful trend detection.
    """
    n = len(values)
    if n == 0:
        return Trend(metric_name=metric_name, values=[], direction="stable", confidence=0.0)
    if n == 1:
        return Trend(metric_name=metric_name, values=values, direction="stable", confidence=0.3)

    # ─── Basic statistics ───
    mean = sum(values) / n
    variance = sum((v - mean) ** 2 for v in values) / n if n > 1 else 0.0
    std_dev = variance ** 0.5

    # ─── Linear regression ───
    x_mean = (n - 1) / 2.0
    numerator = sum((i - x_mean) * (v - mean) for i, v in enumerate(values))
    denominator = sum((i - x_mean) ** 2 for i in range(n))
    slope = numerator / denominator if denominator != 0 else 0.0

    # ─── Oscillation detection ───
    if n >= 3:
        direction_changes = 0
        for i in range(1, n - 1):
            if (values[i] - values[i - 1]) * (values[i + 1] - values[i]) < 0:
                direction_changes += 1
        oscillation_ratio = direction_changes / max(n - 2, 1)
    else:
        oscillation_ratio = 0.0

    # ─── Recovery detection ───
    recovered = False
    recovered_after_failure = False
    if n >= 3:
        first_half = values[:n // 2]
        second_half = values[n // 2:]
        first_mean = sum(first_half) / len(first_half)
        second_mean = sum(second_half) / len(second_half)
        recovered = first_mean < 0.5 and second_mean > 0.5 and slope > 0
        recovered_after_failure = first_mean < 0.3 and second_mean > 0.5 and slope > 0

    # ─── Trend classification ───
    if oscillation_ratio > 0.5:
        direction = "oscillating"
        confidence = min(0.8, oscillation_ratio)
    elif recovered_after_failure:
        direction = "recovered_after_failure"
        confidence = 0.8
    elif recovered:
        direction = "recovered"
        confidence = 0.75
    elif abs(slope) < 0.01:
        direction = "stable"
        confidence = 0.6 if std_dev < 0.1 else 0.3
    elif slope > 0.05:
        # Check if accelerating
        if n >= 4:
            first_half_slope = (values[n // 2] - values[0]) / max(n // 2, 1)
            second_half_slope = (values[-1] - values[n // 2]) / max(n - n // 2, 1)
            if second_half_slope > first_half_slope * 1.5:
                direction = "accelerating"
                confidence = 0.8
            else:
                direction = "improving"
                confidence = min(0.9, abs(slope) * 5)
        else:
            direction = "improving"
            confidence = min(0.7, abs(slope) * 5)
    elif slope < -0.05:
        if n >= 4:
            first_half_slope = (values[n // 2] - values[0]) / max(n // 2, 1)
            second_half_slope = (values[-1] - values[n // 2]) / max(n - n // 2, 1)
            if second_half_slope < first_half_slope * 1.5:
                direction = "accelerating"
                confidence = 0.8
            else:
                direction = "declining"
                confidence = min(0.9, abs(slope) * 5)
        else:
            direction = "declining"
            confidence = min(0.7, abs(slope) * 5)
    else:
        direction = "stable"
        confidence = 0.5

    # ─── Anomaly detection ───
    if std_dev > 0.5 and n >= 3:
        direction = "anomalous"
        confidence = min(0.9, std_dev)

    return Trend(
        metric_name=metric_name,
        values=values,
        direction=direction,
        confidence=min(confidence, 1.0),
        slope=slope,
        mean=mean,
        std_dev=std_dev,
    )


class TrendStore:
    def __init__(self):
        self._trends: dict[str, Trend] = {}

    def add(self, trend: Trend) -> None:
        self._trends[trend.metric_name] = trend

    def get(self, metric_name: str) -> Optional[Trend]:
        return self._trends.get(metric_name)

    def get_all(self) -> list[Trend]:
        return list(self._trends.values())

    @property
    def count(self) -> int:
        return len(self._trends)

    def clear(self) -> None:
        self._trends.clear()


_store: Optional[TrendStore] = None


def get_store() -> TrendStore:
    global _store
    if _store is None:
        _store = TrendStore()
    return _store


def reset_store() -> None:
    global _store
    _store = None