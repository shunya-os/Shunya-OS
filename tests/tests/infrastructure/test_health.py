"""Tests for INFR-006: Health Framework."""

import pytest
from app.shunya.infrastructure.health import (
    HealthRegistry, HealthStatus, HealthCheckResult,
    simple_health_check, degraded_health_check,
    get_health_registry, reset_health_registry,
)


class TestHealthCheckResult:
    def test_to_dict(self) -> None:
        result = HealthCheckResult(
            component="test",
            status=HealthStatus.HEALTHY,
            detail="OK",
            metrics={"uptime": 3600},
            checked_at=1000.0,
            duration_ms=5.0,
        )
        d = result.to_dict()
        assert d["component"] == "test"
        assert d["status"] == "healthy"
        assert d["detail"] == "OK"
        assert d["metrics"]["uptime"] == 3600
        assert d["duration_ms"] == 5.0


class TestHealthRegistry:
    def test_register_and_check(self) -> None:
        registry = HealthRegistry()
        registry.register("test_ok", lambda: HealthCheckResult(
            component="test_ok", status=HealthStatus.HEALTHY, detail="OK"
        ))
        results = registry.check_all()
        assert len(results) == 1
        assert results[0].status == HealthStatus.HEALTHY

    def test_unregister(self) -> None:
        registry = HealthRegistry()
        registry.register("test_del", lambda: HealthCheckResult(
            component="test_del", status=HealthStatus.HEALTHY
        ))
        registry.unregister("test_del")
        assert not registry.is_registered("test_del")

    def test_is_registered(self) -> None:
        registry = HealthRegistry()
        assert not registry.is_registered("nonexistent")
        registry.register("exists", lambda: HealthCheckResult(
            component="exists", status=HealthStatus.HEALTHY
        ))
        assert registry.is_registered("exists")

    def test_overall_status_all_healthy(self) -> None:
        registry = HealthRegistry()
        registry.register("a", lambda: HealthCheckResult("a", HealthStatus.HEALTHY))
        registry.register("b", lambda: HealthCheckResult("b", HealthStatus.HEALTHY))
        assert registry.get_overall_status() == HealthStatus.HEALTHY

    def test_overall_status_one_degraded(self) -> None:
        registry = HealthRegistry()
        registry.register("a", lambda: HealthCheckResult("a", HealthStatus.HEALTHY))
        registry.register("b", lambda: HealthCheckResult("b", HealthStatus.DEGRADED))
        assert registry.get_overall_status() == HealthStatus.DEGRADED

    def test_overall_status_one_unhealthy(self) -> None:
        registry = HealthRegistry()
        registry.register("a", lambda: HealthCheckResult("a", HealthStatus.HEALTHY))
        registry.register("b", lambda: HealthCheckResult("b", HealthStatus.UNHEALTHY))
        assert registry.get_overall_status() == HealthStatus.UNHEALTHY

    def test_overall_status_no_checks(self) -> None:
        registry = HealthRegistry()
        assert registry.get_overall_status() == HealthStatus.UNKNOWN

    def test_check_exception_returns_unhealthy(self) -> None:
        registry = HealthRegistry()
        def _failing_check() -> HealthCheckResult:
            raise RuntimeError("connection refused")
        registry.register("failing", _failing_check)
        results = registry.check_all()
        assert results[0].status == HealthStatus.UNHEALTHY
        assert "connection refused" in results[0].detail

    def test_generate_report_structure(self) -> None:
        registry = HealthRegistry()
        registry.register("ok", lambda: HealthCheckResult("ok", HealthStatus.HEALTHY))
        report = registry.generate_report()
        assert "status" in report
        assert "timestamp" in report
        assert "checks" in report
        assert "summary" in report

    def test_generate_report_summary(self) -> None:
        registry = HealthRegistry()
        registry.register("a", lambda: HealthCheckResult("a", HealthStatus.HEALTHY))
        registry.register("b", lambda: HealthCheckResult("b", HealthStatus.DEGRADED))
        report = registry.generate_report()
        assert report["summary"]["total"] == 2
        assert report["summary"]["healthy"] == 1
        assert report["summary"]["degraded"] == 1
        assert report["summary"]["unhealthy"] == 0

    def test_get_last_results(self) -> None:
        registry = HealthRegistry()
        registry.register("test", lambda: HealthCheckResult("test", HealthStatus.HEALTHY))
        registry.check_all()
        last = registry.get_last_results()
        assert "test" in last

    def test_simple_health_check_pass(self) -> None:
        check_fn = simple_health_check("simple", lambda: True)
        result = check_fn()
        assert result.status == HealthStatus.HEALTHY

    def test_simple_health_check_fail(self) -> None:
        check_fn = simple_health_check("simple", lambda: False)
        result = check_fn()
        assert result.status == HealthStatus.UNHEALTHY

    def test_simple_health_check_exception(self) -> None:
        def _fails() -> bool:
            raise ValueError("oops")
        check_fn = simple_health_check("failing", _fails)
        result = check_fn()
        assert result.status == HealthStatus.UNHEALTHY

    def test_degraded_health_check(self) -> None:
        check_fn = degraded_health_check("pending", "Not implemented yet")
        result = check_fn()
        assert result.status == HealthStatus.DEGRADED
        assert "Not implemented yet" in result.detail

    def test_module_level_get_registry(self) -> None:
        reset_health_registry()
        r1 = get_health_registry()
        r2 = get_health_registry()
        assert r1 is r2

    def test_reset_health_registry_creates_new(self) -> None:
        r1 = get_health_registry()
        reset_health_registry()
        r2 = get_health_registry()
        assert r1 is not r2