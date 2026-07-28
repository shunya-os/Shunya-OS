"""Tests for INFR-005: Metrics Collection."""

import pytest
from app.shunya.infrastructure.metrics import (
    Counter, Gauge, Histogram, MetricsRegistry, get_registry, reset_registry,
)


class TestCounter:
    def test_initial_value(self) -> None:
        c = Counter("test_counter")
        assert c.collect().value == 0.0

    def test_increment(self) -> None:
        c = Counter("test_counter")
        c.inc()
        assert c.collect().value == 1.0

    def test_increment_by_value(self) -> None:
        c = Counter("test_counter")
        c.inc(5.0)
        assert c.collect().value == 5.0

    def test_reset(self) -> None:
        c = Counter("test_counter")
        c.inc(10)
        c.reset()
        assert c.collect().value == 0.0

    def test_metric_name(self) -> None:
        c = Counter("requests_total")
        assert c.collect().name == "requests_total"

    def test_metric_type(self) -> None:
        c = Counter("test_counter")
        assert c.collect().type_name == "counter"


class TestGauge:
    def test_initial_value(self) -> None:
        g = Gauge("test_gauge")
        assert g.collect().value == 0.0

    def test_set(self) -> None:
        g = Gauge("test_gauge")
        g.set(42.0)
        assert g.collect().value == 42.0

    def test_inc(self) -> None:
        g = Gauge("test_gauge")
        g.inc()
        assert g.collect().value == 1.0

    def test_dec(self) -> None:
        g = Gauge("test_gauge")
        g.set(10.0)
        g.dec(3.0)
        assert g.collect().value == 7.0

    def test_metric_type(self) -> None:
        g = Gauge("test_gauge")
        assert g.collect().type_name == "gauge"


class TestHistogram:
    def test_observe_increments_bucket(self) -> None:
        h = Histogram("test_histogram", buckets=[0.1, 0.5, 1.0])
        h.observe(0.3)
        samples = h.collect()
        # 0.3 <= 0.5 and 0.3 <= 1.0 and 0.3 <= +Inf
        for s in samples:
            if s.labels and s.labels[0].value == "0.5":
                assert s.value == 1.0
                break
        else:
            pytest.fail("No bucket sample found")

    def test_total_count(self) -> None:
        h = Histogram("test_histogram")
        h.observe(0.1)
        h.observe(0.2)
        h.observe(0.3)
        samples = h.collect()
        for s in samples:
            if s.name == "test_histogram_count":
                assert s.value == 3.0
                break
        else:
            pytest.fail("No count sample found")

    def test_total_sum(self) -> None:
        h = Histogram("test_histogram")
        h.observe(1.0)
        h.observe(2.0)
        samples = h.collect()
        for s in samples:
            if s.name == "test_histogram_sum":
                assert s.value == 3.0
                break
        else:
            pytest.fail("No sum sample found")

    def test_reset(self) -> None:
        h = Histogram("test_histogram")
        h.observe(1.0)
        h.reset()
        samples = h.collect()
        for s in samples:
            if s.name == "test_histogram_count":
                assert s.value == 0.0
                break


class TestMetricsRegistry:
    def test_counter_get_or_create(self) -> None:
        reg = MetricsRegistry()
        c1 = reg.counter("req_total")
        c2 = reg.counter("req_total")
        assert c1 is c2

    def test_gauge_get_or_create(self) -> None:
        reg = MetricsRegistry()
        g1 = reg.gauge("queue_depth")
        g2 = reg.gauge("queue_depth")
        assert g1 is g2

    def test_histogram_get_or_create(self) -> None:
        reg = MetricsRegistry()
        h1 = reg.histogram("latency")
        h2 = reg.histogram("latency")
        assert h1 is h2

    def test_collect_all(self) -> None:
        reg = MetricsRegistry()
        reg.counter("test_count").inc()
        reg.gauge("test_gauge").set(42)
        samples = reg.collect_all()
        assert len(samples) > 0

    def test_exposition_format_contains_metrics(self) -> None:
        reg = MetricsRegistry()
        reg.counter("http_requests_total", help_text="Total HTTP requests")
        reg.counter("http_requests_total").inc(3)
        output = reg.generate_exposition()
        assert "http_requests_total" in output
        assert "3" in output

    def test_exposition_format_type_and_help(self) -> None:
        reg = MetricsRegistry()
        reg.counter("test_counter", help_text="A test counter")
        output = reg.generate_exposition()
        assert "# HELP" in output
        assert "# TYPE" in output

    def test_reset_all(self) -> None:
        reg = MetricsRegistry()
        reg.counter("test_count").inc(5)
        reg.reset_all()
        samples = reg.collect_all()
        assert len(samples) == 0

    def test_registry_per_engine_namespace(self) -> None:
        from app.shunya.infrastructure.metrics import engine_namespace
        name = engine_namespace("governance", "requests_total")
        assert name == "governance_requests_total"

    def test_module_level_get_registry(self) -> None:
        reset_registry()
        r1 = get_registry()
        r2 = get_registry()
        assert r1 is r2