"""Stream H — Launch Readiness Verification."""
from __future__ import annotations
from typing import Any
from core.launch_readiness import LaunchReadiness, introduce_sample_data


def test_readiness_checks() -> dict[str, Any]:
    lr = LaunchReadiness()
    lr.add_check("Python version", lambda: True)
    lr.add_check("All modules", lambda: True)
    results = lr.run_checks()
    assert len(results) == 2
    assert all(r["passed"] for r in results)
    return {"scenario": "Readiness Checks", "passed": True}


def test_deployment_config() -> dict[str, Any]:
    lr = LaunchReadiness()
    lr.configure(mode="production", port=8080, workers=4)
    config = lr.get_config()
    assert config["mode"] == "production"
    assert config["port"] == 8080
    return {"scenario": "Deployment Config", "passed": True}


def test_docker_generation() -> dict[str, Any]:
    lr = LaunchReadiness()
    dockerfile = lr.generate_dockerfile()
    assert "FROM python:3.12-slim" in dockerfile
    compose = lr.generate_docker_compose()
    assert "shunya:" in compose
    return {"scenario": "Docker Generation", "passed": True}


def test_sample_data() -> dict[str, Any]:
    data = introduce_sample_data()
    assert "sample_data" in data
    assert "identities" in data["sample_data"]
    assert len(data["sample_data"]["identities"]) == 3
    assert len(data["sample_data"]["organizations"]) == 3
    return {"scenario": "Sample Data", "identities": 3, "organizations": 3, "passed": True}


def test_monitoring() -> dict[str, Any]:
    lr = LaunchReadiness()
    checks = lr.monitoring_checks()
    assert len(checks) == 5
    assert all(c["status"] == "ok" for c in checks)
    return {"scenario": "Monitoring", "passed": True}


def test_health() -> dict[str, Any]:
    lr = LaunchReadiness()
    health = lr.health_check()
    assert health["status"] == "healthy"
    return {"scenario": "Health Check", "passed": True}


def run_all() -> list[dict[str, Any]]:
    tests = [("Readiness Checks", test_readiness_checks),
             ("Deployment Config", test_deployment_config),
             ("Docker Generation", test_docker_generation),
             ("Sample Data", test_sample_data),
             ("Monitoring", test_monitoring),
             ("Health", test_health)]
    results = []
    for n, fn in tests:
        try:
            r = fn(); r["test_name"] = n; r["status"] = "PASS"
        except Exception as e:
            r = {"test_name": n, "status": "FAIL", "error": str(e), "passed": False}
        results.append(r)
    return results


if __name__ == "__main__":
    print("STREAM H — Launch Readiness: Verification Report")
    results = run_all()
    passed = [r for r in results if r.get("passed")]
    failed = [r for r in results if not r.get("passed")]
    for r in results:
        s = "✅ PASS" if r.get("passed") else "❌ FAIL"
        print(f"  {s} | {r.get('test_name', '?')}")
    print(f"\n  Total: {len(results)} | Passed: {len(passed)} | Failed: {len(failed)}")