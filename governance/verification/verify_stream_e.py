"""Stream E — Experience Verification."""
from __future__ import annotations
from typing import Any
from core.experience_engine import ExperienceEngine


def test_notifications() -> dict[str, Any]:
    e = ExperienceEngine()
    n = e.notify("user_1", "Test notification", "Body text", "info", "test")
    assert n.title == "Test notification"
    assert not n.read
    ns = e.get_notifications("user_1")
    assert len(ns) == 1
    e.mark_read(n.notification_id)
    unread = e.get_notifications("user_1", unread_only=True)
    assert len(unread) == 0
    return {"scenario": "Notifications", "passed": True}


def test_timeline() -> dict[str, Any]:
    e = ExperienceEngine()
    e.add_timeline_entry("user_1", "Created project", "New project initialized", "event", "initiative")
    e.add_timeline_entry("user_1", "Signed agreement", "Partnership signed", "agreement", "agreement")
    timeline = e.get_timeline("user_1")
    assert len(timeline) == 2
    return {"scenario": "Timeline", "passed": True}


def test_themes() -> dict[str, Any]:
    e = ExperienceEngine()
    themes = e.list_themes()
    assert "dark" in themes
    assert "light" in themes
    assert e.set_theme("light")
    theme = e.get_theme()
    assert theme["name"] == "light"
    assert not e.set_theme("nonexistent")
    return {"scenario": "Themes", "passed": True}


def test_localization() -> dict[str, Any]:
    e = ExperienceEngine()
    assert e.translate("welcome") == "Welcome"
    assert e.set_locale("hi-IN")
    assert e.translate("welcome") == "स्वागत है"
    assert e.set_locale("ta-IN")
    assert e.translate("search") == "தேடு"
    locales = e.list_locales()
    assert len(locales) >= 3
    return {"scenario": "Localization", "passed": True}


def test_presence() -> dict[str, Any]:
    e = ExperienceEngine()
    e.update_presence("user_1", "online", "desktop")
    e.update_presence("user_2", "online", "mobile")
    e.update_presence("user_3", "offline", "tablet")
    online = e.get_online_users()
    assert len(online) == 2
    presence = e.get_presence("user_1")
    assert presence is not None
    assert presence["device"] == "desktop"
    return {"scenario": "Presence", "passed": True}


def test_health() -> dict[str, Any]:
    e = ExperienceEngine()
    health = e.health_check()
    assert health["status"] == "healthy"
    return {"scenario": "Health Check", "passed": True}


def run_all() -> list[dict[str, Any]]:
    tests = [("Notifications", test_notifications), ("Timeline", test_timeline),
             ("Themes", test_themes), ("Localization", test_localization),
             ("Presence", test_presence), ("Health", test_health)]
    results = []
    for n, fn in tests:
        try:
            r = fn(); r["test_name"] = n; r["status"] = "PASS"
        except Exception as e:
            r = {"test_name": n, "status": "FAIL", "error": str(e), "passed": False}
        results.append(r)
    return results


if __name__ == "__main__":
    print("STREAM E — Experience: Verification Report")
    results = run_all()
    passed = [r for r in results if r.get("passed")]
    failed = [r for r in results if not r.get("passed")]
    for r in results:
        s = "✅ PASS" if r.get("passed") else "❌ FAIL"
        print(f"  {s} | {r.get('test_name', '?')}")
    print(f"\n  Total: {len(results)} | Passed: {len(passed)} | Failed: {len(failed)}")