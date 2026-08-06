"""Stream C — Execution Engine Verification."""
from __future__ import annotations
from typing import Any
from core.execution_engine import ExecutionEngine


def test_register_action() -> dict[str, Any]:
    e = ExecutionEngine()
    action = e.register("test.action", "Test", "A test action")
    assert action.action_id == "test.action"
    assert len(e.list_actions()) == 1
    return {"scenario": "Register Action", "passed": True}


def test_execute_action() -> dict[str, Any]:
    e = ExecutionEngine()
    e.register("test.greet", "Greet", "Say hello",
               handler=lambda name="World": f"Hello, {name}!")
    result = e.execute("test.greet", {"name": "SHUNYA"})
    assert result["success"]
    assert result["output"] == "Hello, SHUNYA!"
    return {"scenario": "Execute Action", "result": result["output"], "passed": True}


def test_execute_unknown() -> dict[str, Any]:
    e = ExecutionEngine()
    result = e.execute("does.not.exist")
    assert not result["success"]
    assert "Unknown" in result["error"]
    return {"scenario": "Unknown Action", "passed": True}


def test_execute_error_handling() -> dict[str, Any]:
    e = ExecutionEngine()
    def failing(**kwargs):
        raise ValueError("Something went wrong")
    e.register("test.fail", "Failing", "Always fails", handler=failing)
    result = e.execute("test.fail")
    assert not result["success"]
    assert "error" in result
    return {"scenario": "Error Handling", "passed": True}


def test_scheduling() -> dict[str, Any]:
    e = ExecutionEngine()
    e.register("test.job", "Job", "A scheduled job")
    job_id = e.schedule("test.job", "0 9 * * *", name="Daily report")
    assert job_id is not None
    schedules = e.list_schedules()
    assert len(schedules) == 1
    assert schedules[0]["cron"] == "0 9 * * *"
    assert e.cancel_schedule(job_id)
    assert not e.list_schedules()[0]["active"]
    return {"scenario": "Scheduling", "passed": True}


def test_history() -> dict[str, Any]:
    e = ExecutionEngine()
    e.register("test.hist", "History", "History test")
    e.execute("test.hist")
    e.execute("test.hist")
    hist = e.history()
    assert len(hist) == 2
    return {"scenario": "Execution History", "count": len(hist), "passed": True}


def test_builtins() -> dict[str, Any]:
    e = ExecutionEngine()
    e.register_builtins()
    actions = e.list_actions()
    action_ids = [a["id"] for a in actions]
    assert "system.notify" in action_ids
    assert "system.log" in action_ids
    assert "system.sleep" in action_ids
    return {"scenario": "Built-in Actions", "count": len(actions), "passed": True}


def test_health_check() -> dict[str, Any]:
    e = ExecutionEngine()
    health = e.health_check()
    assert health["status"] == "healthy"
    return {"scenario": "Health Check", "passed": True}


def run_all() -> list[dict[str, Any]]:
    tests = [
        ("Register Action", test_register_action),
        ("Execute Action", test_execute_action),
        ("Unknown Action", test_execute_unknown),
        ("Error Handling", test_execute_error_handling),
        ("Scheduling", test_scheduling),
        ("Execution History", test_history),
        ("Built-in Actions", test_builtins),
        ("Health Check", test_health_check),
    ]
    results = []
    for n, fn in tests:
        try:
            r = fn(); r["test_name"] = n; r["status"] = "PASS"
        except Exception as e:
            import traceback
            r = {"test_name": n, "status": "FAIL", "error": str(e), "passed": False}
        results.append(r)
    return results


if __name__ == "__main__":
    print("STREAM C — Execution Engine: Verification Report")
    results = run_all()
    passed = [r for r in results if r.get("passed")]
    failed = [r for r in results if not r.get("passed")]
    for r in results:
        s = "✅ PASS" if r.get("passed") else "❌ FAIL"
        print(f"  {s} | {r.get('test_name', '?')}")
    print(f"\n  Total: {len(results)} | Passed: {len(passed)} | Failed: {len(failed)}")