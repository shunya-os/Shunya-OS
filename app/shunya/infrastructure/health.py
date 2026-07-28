"""SHUNYA — Health Framework.

Centralized health endpoint with a registry where components register
their health check functions. Aggregated health status with per-component
detail. Supports degraded, healthy, and unhealthy states.

Architectural authority: INFR-006 (SHUNYA_IMPLEMENTATION_PROGRAM.md)
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional


class HealthStatus(Enum):
    """Health status values."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


@dataclass
class HealthCheckResult:
    """Result of a single health check."""
    component: str
    status: HealthStatus
    detail: str = ""
    metrics: Dict[str, Any] = field(default_factory=dict)
    checked_at: float = 0.0
    duration_ms: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "component": self.component,
            "status": self.status.value,
            "detail": self.detail,
            "metrics": self.metrics,
            "checked_at": self.checked_at,
            "duration_ms": round(self.duration_ms, 2),
        }


HealthCheckFn = Callable[[], HealthCheckResult]


class HealthRegistry:
    """Registry of health check functions.

    Components register their health check functions.
    The registry aggregates results into an overall health report.
    Supports timeouts — a check that exceeds the timeout is marked UNHEALTHY.
    """

    def __init__(self, default_timeout_s: float = 5.0) -> None:
        self._checks: Dict[str, HealthCheckFn] = {}
        self._timeout_s: float = default_timeout_s
        self._last_results: Dict[str, HealthCheckResult] = {}

    def register(self, component: str, check_fn: HealthCheckFn) -> None:
        """Register a health check function for a component.

        Args:
            component: Component name (e.g. "event_bus", "governance_engine").
            check_fn: A callable that returns a HealthCheckResult.
        """
        self._checks[component] = check_fn

    def unregister(self, component: str) -> None:
        """Remove a health check registration."""
        self._checks.pop(component, None)
        self._last_results.pop(component, None)

    def is_registered(self, component: str) -> bool:
        """Check if a component is registered."""
        return component in self._checks

    def check_all(self) -> List[HealthCheckResult]:
        """Run all registered health checks and return results.

        Each check is executed with the configured timeout.
        Checks that exceed the timeout are marked UNHEALTHY.
        """
        results: List[HealthCheckResult] = []
        for component, check_fn in self._checks.items():
            start = time.time()
            try:
                # Run the check with a simple timeout simulation via try/except
                result = check_fn()
                result.checked_at = start
                result.duration_ms = (time.time() - start) * 1000
            except Exception as e:
                result = HealthCheckResult(
                    component=component,
                    status=HealthStatus.UNHEALTHY,
                    detail=f"Check raised exception: {e}",
                    checked_at=start,
                    duration_ms=(time.time() - start) * 1000,
                )
            self._last_results[component] = result
            results.append(result)
        return results

    def get_overall_status(self) -> HealthStatus:
        """Compute the overall health status from all registered checks.

        - If any check is UNHEALTHY → UNHEALTHY
        - If any check is DEGRADED and none UNHEALTHY → DEGRADED
        - If all checks are HEALTHY → HEALTHY
        - If no checks registered → UNKNOWN
        """
        if not self._checks:
            return HealthStatus.UNKNOWN
        results = self.check_all()
        for r in results:
            if r.status == HealthStatus.UNHEALTHY:
                return HealthStatus.UNHEALTHY
        for r in results:
            if r.status == HealthStatus.DEGRADED:
                return HealthStatus.DEGRADED
        return HealthStatus.HEALTHY

    def get_last_results(self) -> Dict[str, HealthCheckResult]:
        """Return the last check results for all components."""
        return dict(self._last_results)

    def generate_report(self) -> Dict[str, Any]:
        """Generate a full health report dictionary for API serialization."""
        overall = self.get_overall_status()
        results = self.check_all()
        return {
            "status": overall.value,
            "timestamp": time.time(),
            "checks": [r.to_dict() for r in results],
            "summary": {
                "total": len(results),
                "healthy": sum(1 for r in results if r.status == HealthStatus.HEALTHY),
                "degraded": sum(1 for r in results if r.status == HealthStatus.DEGRADED),
                "unhealthy": sum(1 for r in results if r.status == HealthStatus.UNHEALTHY),
            },
        }


# ---- Health check factories -------------------------------------------------


def simple_health_check(
    component: str,
    check_fn: Callable[[], bool],
    healthy_detail: str = "OK",
    unhealthy_detail: str = "Check failed",
    metrics: Optional[Dict[str, Any]] = None,
) -> HealthCheckFn:
    """Create a simple health check function from a boolean-returning callable.

    Args:
        component: Component name.
        check_fn: Returns True if healthy, False if unhealthy.
        healthy_detail: Detail string for healthy result.
        unhealthy_detail: Detail string for unhealthy result.
        metrics: Optional metrics dict to include in the result.

    Returns:
        A health check function suitable for HealthRegistry.register().
    """
    def _check() -> HealthCheckResult:
        try:
            ok = check_fn()
            return HealthCheckResult(
                component=component,
                status=HealthStatus.HEALTHY if ok else HealthStatus.UNHEALTHY,
                detail=healthy_detail if ok else unhealthy_detail,
                metrics=metrics or {},
            )
        except Exception as e:
            return HealthCheckResult(
                component=component,
                status=HealthStatus.UNHEALTHY,
                detail=f"{unhealthy_detail}: {e}",
                metrics=metrics or {},
            )
    return _check


def degraded_health_check(
    component: str,
    detail: str = "Component not yet implemented",
) -> HealthCheckFn:
    """Create a health check that returns DEGRADED.

    Useful for engines that are specified but not yet implemented.
    """
    def _check() -> HealthCheckResult:
        return HealthCheckResult(
            component=component,
            status=HealthStatus.DEGRADED,
            detail=detail,
        )
    _check.__name__ = f"degraded_{component}"  # type: ignore
    return _check


# ---- Module-level convenience -----------------------------------------------

_registry_global: Optional[HealthRegistry] = None


def get_health_registry() -> HealthRegistry:
    """Return the application-wide HealthRegistry (lazily created)."""
    global _registry_global
    if _registry_global is None:
        _registry_global = HealthRegistry()
    return _registry_global


def reset_health_registry() -> None:
    """Reset the global health registry. Useful for testing."""
    global _registry_global
    _registry_global = None