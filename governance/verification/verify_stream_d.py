"""Stream D — Identity Intelligence Verification."""
from __future__ import annotations
from typing import Any
from core.identity_engine import IdentityEngine, DecisionStyle, CommunicationStyle


def test_create_identity() -> dict[str, Any]:
    e = IdentityEngine()
    identity = e.create("user_raj", "Raj", "person")
    assert identity.identity_id == "user_raj"
    assert identity.name == "Raj"
    return {"scenario": "Create Identity", "passed": True}


def test_update_identity() -> dict[str, Any]:
    e = IdentityEngine()
    e.create("user_1", "Test User")
    updated = e.update("user_1", bio="Software engineer", values=["honesty", "quality"])
    assert updated is not None
    assert "quality" in updated.values
    assert updated.bio == "Software engineer"
    return {"scenario": "Update Identity", "passed": True}


def test_styles() -> dict[str, Any]:
    e = IdentityEngine()
    identity = e.create("user_styles", "Stylish User")
    identity.decision_style = DecisionStyle.INTUITIVE.value
    identity.communication_style = CommunicationStyle.DIRECT.value
    identity.working_style = "focused"
    identity.learning_style = "visual"
    stored = e.get("user_styles")
    assert stored is not None
    assert stored.decision_style == "intuitive"
    assert stored.communication_style == "direct"
    return {"scenario": "Communication & Decision Styles", "passed": True}


def test_goals() -> dict[str, Any]:
    e = IdentityEngine()
    e.create("user_goals", "Goal Setter")
    goal = e.add_goal("user_goals", "Learn Rust", "Become proficient in Rust", "high")
    assert goal is not None
    assert goal.title == "Learn Rust"
    assert e.update_goal("user_goals", goal.goal_id, progress_pct=50.0)
    updated = e.get("user_goals")
    assert updated is not None
    assert updated.goals[0].progress_pct == 50.0
    return {"scenario": "Goal Management", "passed": True}


def test_intent_search() -> dict[str, Any]:
    e = IdentityEngine()
    e.create("user_a", "Alice").intent = "Build a product company"
    e.create("user_b", "Bob").intent = "Learn machine learning"
    results = e.find_by_intent("product")
    assert len(results) == 1
    assert results[0].name == "Alice"
    return {"scenario": "Intent Search", "passed": True}


def test_responsibilities_authorities() -> dict[str, Any]:
    e = IdentityEngine()
    identity = e.create("user_lead", "Team Lead")
    identity.responsibilities = ["Lead development team", "Code review", "Architecture"]
    identity.authorities = ["Approve PRs", "Assign tasks", "Budget up to 50K"]
    stored = e.get("user_lead")
    assert stored is not None
    assert len(stored.responsibilities) == 3
    assert len(stored.authorities) == 3
    return {"scenario": "Responsibilities & Authorities", "passed": True}


def test_constraints_preferences() -> dict[str, Any]:
    e = IdentityEngine()
    identity = e.create("user_cons", "Constrained User")
    identity.constraints = ["No weekend work", "Budget < 10K", "Must review before publish"]
    identity.preferences = {"theme": "dark", "language": "en", "timezone": "IST"}
    stored = e.get("user_cons")
    assert stored is not None
    assert len(stored.constraints) == 3
    assert stored.preferences["theme"] == "dark"
    return {"scenario": "Constraints & Preferences", "passed": True}


def test_health_check() -> dict[str, Any]:
    e = IdentityEngine()
    e.create("user_1", "One")
    e.create("user_2", "Two")
    e.add_goal("user_1", "Goal A")
    e.add_goal("user_1", "Goal B")
    health = e.health_check()
    assert health["identities"] == 2
    assert health["goals"] == 2
    return {"scenario": "Health Check", "passed": True}


def run_all() -> list[dict[str, Any]]:
    tests = [
        ("Create Identity", test_create_identity),
        ("Update Identity", test_update_identity),
        ("Styles", test_styles),
        ("Goals", test_goals),
        ("Intent Search", test_intent_search),
        ("Responsibilities", test_responsibilities_authorities),
        ("Constraints", test_constraints_preferences),
        ("Health Check", test_health_check),
    ]
    results = []
    for n, fn in tests:
        try:
            r = fn(); r["test_name"] = n; r["status"] = "PASS"
        except Exception as e:
            r = {"test_name": n, "status": "FAIL", "error": str(e), "passed": False}
        results.append(r)
    return results


if __name__ == "__main__":
    print("STREAM D — Identity Intelligence: Verification Report")
    results = run_all()
    passed = [r for r in results if r.get("passed")]
    failed = [r for r in results if not r.get("passed")]
    for r in results:
        s = "✅ PASS" if r.get("passed") else "❌ FAIL"
        print(f"  {s} | {r.get('test_name', '?')}")
    print(f"\n  Total: {len(results)} | Passed: {len(passed)} | Failed: {len(failed)}")