"""SHUNYA — Metrics Collection.

Prometheus-compatible metrics collection with support for counters,
histograms, gauges, and per-engine metric namespacing.

Architectural authority: INFR-005 (SHUNYA_IMPLEMENTATION_PROGRAM.md)
"""

from __future__ import annotations

import time
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, Generator, List, Optional


@dataclass
class MetricLabel:
    """A key-value label for metric identification."""
    name: str
    value: str


@dataclass
class MetricSample:
    """A single metric sample for Prometheus exposition format."""
    name: str
    value: float
    labels: List[MetricLabel] = field(default_factory=list)
    timestamp: Optional[float] = None
    help_text: str = ""
    type_name: str = "untyped"


class Counter:
    """A monotonically increasing counter.

    Use for: request counts, error counts, event counts.
    """

    def __init__(self, name: str, help_text: str = "", labels: Optional[Dict[str, str]] = None) -> None:
        self._name = name
        self._help = help_text
        self._labels = list((MetricLabel(k, v) for k, v in (labels or {}).items()))
        self._value: float = 0.0

    def inc(self, value: float = 1.0, labels: Optional[Dict[str, str]] = None) -> None:
        """Increment the counter by the given value."""
        self._value += value

    def reset(self) -> None:
        """Reset the counter to zero. Useful for testing."""
        self._value = 0.0

    def collect(self) -> MetricSample:
        """Return a metric sample for exposition."""
        return MetricSample(
            name=self._name,
            value=self._value,
            labels=self._labels,
            type_name="counter",
            help_text=self._help,
        )


class Gauge:
    """A gauge that can go up and down.

    Use for: current queue depth, memory usage, active connections.
    """

    def __init__(self, name: str, help_text: str = "", labels: Optional[Dict[str, str]] = None) -> None:
        self._name = name
        self._help = help_text
        self._labels = list((MetricLabel(k, v) for k, v in (labels or {}).items()))
        self._value: float = 0.0

    def set(self, value: float) -> None:
        """Set the gauge to the given value."""
        self._value = value

    def inc(self, value: float = 1.0) -> None:
        """Increase the gauge by the given value."""
        self._value += value

    def dec(self, value: float = 1.0) -> None:
        """Decrease the gauge by the given value."""
        self._value -= value

    def reset(self) -> None:
        """Reset the gauge to zero. Useful for testing."""
        self._value = 0.0

    def collect(self) -> MetricSample:
        return MetricSample(
            name=self._name,
            value=self._value,
            labels=self._labels,
            type_name="gauge",
            help_text=self._help,
        )


class Histogram:
    """A histogram that records observations in configurable buckets.

    Use for: latency distributions, request sizes, batch sizes.
    """

    def __init__(
        self,
        name: str,
        help_text: str = "",
        labels: Optional[Dict[str, str]] = None,
        buckets: Optional[List[float]] = None,
    ) -> None:
        self._name = name
        self._help = help_text
        self._labels = list((MetricLabel(k, v) for k, v in (labels or {}).items()))
        self._buckets = buckets or [0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0]
        self._counts: Dict[float, float] = {b: 0.0 for b in self._buckets}
        self._counts[float("inf")] = 0.0
        self._total_count: float = 0.0
        self._total_sum: float = 0.0

    def observe(self, value: float) -> None:
        """Record an observation."""
        self._total_count += 1.0
        self._total_sum += value
        for bucket in self._buckets:
            if value <= bucket:
                self._counts[bucket] += 1.0
        self._counts[float("inf")] += 1.0

    def reset(self) -> None:
        """Reset all buckets and totals."""
        self._counts = {b: 0.0 for b in self._buckets}
        self._counts[float("inf")] = 0.0
        self._total_count = 0.0
        self._total_sum = 0.0

    def collect(self) -> List[MetricSample]:
        """Return metric samples for exposition (one per bucket + sum + count)."""
        samples: List[MetricSample] = []
        for bucket, count in sorted(self._counts.items()):
            bucket_label = str(bucket) if bucket != float("inf") else "+Inf"
            samples.append(MetricSample(
                name=f"{self._name}_bucket",
                value=count,
                labels=self._labels + [MetricLabel("le", bucket_label)],
                type_name="histogram",
                help_text=self._help,
            ))
        samples.append(MetricSample(
            name=f"{self._name}_count",
            value=self._total_count,
            labels=self._labels,
            type_name="histogram",
            help_text=self._help,
        ))
        samples.append(MetricSample(
            name=f"{self._name}_sum",
            value=self._total_sum,
            labels=self._labels,
            type_name="histogram",
            help_text=self._help,
        ))
        return samples


class MetricsRegistry:
    """Registry of all metrics, organized by engine namespace."""

    def __init__(self) -> None:
        self._metrics: Dict[str, Any] = {}

    def counter(
        self, name: str, help_text: str = "", labels: Optional[Dict[str, str]] = None
    ) -> Counter:
        """Get or create a counter metric."""
        key = f"counter:{name}"
        if key not in self._metrics:
            self._metrics[key] = Counter(name, help_text, labels)
        return self._metrics[key]

    def gauge(
        self, name: str, help_text: str = "", labels: Optional[Dict[str, str]] = None
    ) -> Gauge:
        """Get or create a gauge metric."""
        key = f"gauge:{name}"
        if key not in self._metrics:
            self._metrics[key] = Gauge(name, help_text, labels)
        return self._metrics[key]

    def histogram(
        self, name: str, help_text: str = "", labels: Optional[Dict[str, str]] = None,
        buckets: Optional[List[float]] = None,
    ) -> Histogram:
        """Get or create a histogram metric."""
        key = f"histogram:{name}"
        if key not in self._metrics:
            self._metrics[key] = Histogram(name, help_text, labels, buckets)
        return self._metrics[key]

    def collect_all(self) -> List[MetricSample]:
        """Collect all registered metrics."""
        samples: List[MetricSample] = []
        for metric in self._metrics.values():
            collected = metric.collect()
            if isinstance(collected, list):
                samples.extend(collected)
            else:
                samples.append(collected)
        return samples

    def generate_exposition(self) -> str:
        """Generate Prometheus exposition format text."""
        lines: List[str] = []
        seen_help: set = set()
        seen_type: set = set()
        for sample in self.collect_all():
            # HELP line (once per metric base name)
            base_name = sample.name.replace("_bucket", "").replace("_count", "").replace("_sum", "")
            if sample.help_text and base_name not in seen_help:
                lines.append(f"# HELP {sample.name} {sample.help_text}")
                seen_help.add(base_name)
            # TYPE line (once per metric base name)
            if sample.type_name and base_name not in seen_type:
                lines.append(f"# TYPE {base_name} {sample.type_name}")
                seen_type.add(base_name)
            # Sample line
            labels_str = ",".join(
                f'{l.name}="{l.value}"' for l in sample.labels
            )
            if labels_str:
                line = f'{sample.name}{{{labels_str}}} {sample.value}'
            else:
                line = f'{sample.name} {sample.value}'
            if sample.timestamp:
                line = f"{line} {int(sample.timestamp * 1000)}"
            lines.append(line)
        return "\n".join(lines) + "\n"

    def reset_all(self) -> None:
        """Reset all metrics. Useful for testing."""
        self._metrics.clear()


# ---- Per-engine namespace helpers -------------------------------------------

def engine_namespace(engine_name: str, metric_name: str) -> str:
    """Create a namespaced metric name for an engine.

    Example:
        engine_namespace("governance", "requests_total")
        -> "governance_requests_total"
    """
    return f"{engine_name}_{metric_name}"


# ---- Module-level convenience -----------------------------------------------

_registry: Optional[MetricsRegistry] = None


def get_registry() -> MetricsRegistry:
    """Return the application-wide MetricsRegistry (lazily created)."""
    global _registry
    if _registry is None:
        _registry = MetricsRegistry()
    return _registry


def reset_registry() -> None:
    """Reset the global metrics registry. Useful for testing."""
    global _registry
    _registry = None