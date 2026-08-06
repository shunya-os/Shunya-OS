"""UCP-08 Verification — Universal Initiative Intelligence.

Verifies 8 scenarios through the same capability:
1. Startup launch
2. Product launch
3. Personal life goal
4. Construction initiative
5. Research initiative
6. Event planning
7. Marketing campaign
8. Initiative disruption with adaptive execution
"""

from __future__ import annotations
from typing import Any
from core.initiative_intelligence import (
    InitiativeIntelligenceRuntime, InitiativeType, InitiativeStatus, MilestoneStatus,
)


def _m(title: str, status: str = "pending", due: str = "", deps: list[str] | None = None) -> dict:
    return {"title": title, "status": status, "due_date": due, "dependencies": deps or []}


def test_startup_launch() -> dict[str, Any]:
    r = InitiativeIntelligenceRuntime()
    r.get_or_create_profile("founder_raj", "Raj — Startup Launch")

    ini = r.create_initiative("founder_raj", InitiativeType.COMPANY_LAUNCH.value,
        "Launch TechFlow SaaS", "Build and launch a B2B SaaS platform",
        "10 paying customers in first 3 months", "MVP + launch + initial traction",
        participants=[{"name": "Raj", "role": "CEO"}, {"name": "Anita", "role": "CTO"}],
        milestones=[
            _m("Market research", "completed", "2026-04-01"),
            _m("MVP development", "in_progress", "2026-08-15"),
            _m("Beta testing", "pending", "2026-09-01", ["MVP development"]),
            _m("Public launch", "pending", "2026-10-01", ["Beta testing"]),
            _m("First 10 customers", "pending", "2026-12-31", ["Public launch"]),
        ], budget=2000000)
    assert ini is not None, "Startup launch creation failed"
    assert len(ini.milestones) == 5
    assert ini.progress_pct > 0

    r.update_milestone("founder_raj", ini.initiative_id, ini.milestones[0].milestone_id, "completed")

    analysis = r.analyze("founder_raj", ini.initiative_id)
    assert analysis is not None
    return {"scenario": "1. Startup Launch", "entity": "Raj — TechFlow SaaS",
            "milestones": len(ini.milestones), "progress": ini.progress_pct, "passed": True}


def test_product_launch() -> dict[str, Any]:
    r = InitiativeIntelligenceRuntime()
    r.get_or_create_profile("org_product", "Product Team")
    ini = r.create_initiative("org_product", InitiativeType.PRODUCT_LAUNCH.value,
        "Launch AI Assistant v2", "Major product update with AI features",
        "50% existing users upgrade within 30 days", "Q4 product launch",
        milestones=[
            _m("Feature development", "in_progress", "2026-08-01"),
            _m("QA testing", "pending", "2026-09-01", ["Feature development"]),
            _m("Beta program", "pending", "2026-09-15", ["QA testing"]),
            _m("Marketing prep", "in_progress", "2026-09-30"),
            _m("Launch day", "pending", "2026-10-15", ["Beta program", "Marketing prep"]),
        ])
    assert ini is not None
    recs = r.get_recommendations("org_product", ini.initiative_id)
    assert recs is not None
    return {"scenario": "2. Product Launch", "entity": "Product Team — AI Assistant v2",
            "milestones": len(ini.milestones), "recommendations": len(recs), "passed": True}


def test_personal_life_goal() -> dict[str, Any]:
    r = InitiativeIntelligenceRuntime()
    r.get_or_create_profile("person_meera", "Meera — Personal Goal")
    ini = r.create_initiative("person_meera", InitiativeType.PERSONAL_GOAL.value,
        "Run a marathon in 6 months", "Complete a full marathon (42.2 km)",
        "Finish under 5 hours", "6-month training programme",
        milestones=[
            _m("Run 5K consistently", "completed", "2026-05-01"),
            _m("Run 10K", "completed", "2026-06-01"),
            _m("Run half marathon", "in_progress", "2026-07-15"),
            _m("Run 30K", "pending", "2026-08-15", ["Run half marathon"]),
            _m("Full marathon", "pending", "2026-10-01", ["Run 30K"]),
        ])
    assert ini is not None
    analysis = r.analyze("person_meera", ini.initiative_id)
    assert analysis is not None
    assert "health" in analysis
    return {"scenario": "3. Personal Life Goal", "entity": "Meera — Marathon",
            "milestones": len(ini.milestones), "health": analysis["health"]["level"], "passed": True}


def test_construction_initiative() -> dict[str, Any]:
    r = InitiativeIntelligenceRuntime()
    r.get_or_create_profile("buildcorp", "BuildCorp Construction")
    ini = r.create_initiative("buildcorp", InitiativeType.CONSTRUCTION.value,
        "Build Green Valley Towers", "Construction of 2 residential towers",
        "Complete handover by Dec 2027", "Phase 1 — Tower A",
        participants=[{"name": "Suresh", "role": "PM"}, {"name": "Ramesh", "role": "Architect"}],
        milestones=[
            _m("Foundation", "completed", "2026-03-01"),
            _m("Structural framing", "in_progress", "2026-07-01", ["Foundation"]),
            _m("Roofing", "pending", "2026-09-01", ["Structural framing"]),
            _m("Interior work", "pending", "2026-11-01", ["Roofing"]),
            _m("Handover", "pending", "2027-06-01", ["Interior work"]),
        ], budget=50000000)
    assert ini is not None
    analysis = r.analyze("buildcorp", ini.initiative_id)
    assert analysis is not None
    assert "bottlenecks" in analysis
    return {"scenario": "4. Construction Initiative", "entity": "BuildCorp — Green Valley",
            "milestones": len(ini.milestones), "bottlenecks": len(analysis["bottlenecks"]), "passed": True}


def test_research_initiative() -> dict[str, Any]:
    r = InitiativeIntelligenceRuntime()
    r.get_or_create_profile("lab_quantum", "Quantum Computing Lab")
    ini = r.create_initiative("lab_quantum", InitiativeType.RESEARCH.value,
        "Quantum Error Correction Study", "Research novel error correction codes",
        "Published paper in top-tier journal", "9-month research programme",
        participants=[{"name": "Dr. Sharma", "role": "PI"}, {"name": "PhD Student", "role": "Researcher"}],
        milestones=[
            _m("Literature review", "completed", "2026-04-01"),
            _m("Model development", "in_progress", "2026-07-01"),
            _m("Simulation runs", "pending", "2026-09-01", ["Model development"]),
            _m("Paper writing", "pending", "2026-11-01", ["Simulation runs"]),
            _m("Journal submission", "pending", "2026-12-15", ["Paper writing"]),
        ])
    assert ini is not None
    outcome = r._engine.predict_outcome(ini)
    assert outcome is not None
    return {"scenario": "5. Research Initiative", "entity": "Quantum Lab",
            "milestones": len(ini.milestones), "outcome": outcome["prediction"], "passed": True}


def test_event_planning() -> dict[str, Any]:
    r = InitiativeIntelligenceRuntime()
    r.get_or_create_profile("events_team", "Events Team")
    ini = r.create_initiative("events_team", InitiativeType.EVENT.value,
        "Annual Tech Conference 2026", "500-attendee technology conference",
        "90% satisfaction score, 200K revenue", "Full event lifecycle",
        participants=[{"name": "Priya", "role": "Event Manager"}],
        milestones=[
            _m("Venue booking", "completed", "2026-05-01"),
            _m("Speaker lineup", "in_progress", "2026-07-01"),
            _m("Ticket sales open", "in_progress", "2026-07-15"),
            _m("Event day", "pending", "2026-10-15", ["Speaker lineup", "Venue booking"]),
            _m("Post-event report", "pending", "2026-10-30", ["Event day"]),
        ], budget=5000000)
    assert ini is not None
    health = r._engine.compute_health(ini)
    assert health is not None
    return {"scenario": "6. Event Planning", "entity": "Events Team — Tech Conference",
            "milestones": len(ini.milestones), "health": health["level"], "passed": True}


def test_marketing_campaign() -> dict[str, Any]:
    r = InitiativeIntelligenceRuntime()
    r.get_or_create_profile("marketing_team", "Marketing Team")
    ini = r.create_initiative("marketing_team", InitiativeType.MARKETING_CAMPAIGN.value,
        "Q4 Holiday Campaign", "Seasonal marketing campaign for holiday season",
        "500 leads, 50 conversions, 2Cr revenue", "Oct-Dec campaign",
        milestones=[
            _m("Campaign strategy", "completed", "2026-09-01"),
            _m("Creative production", "in_progress", "2026-09-30"),
            _m("Campaign launch", "pending", "2026-10-01", ["Creative production"]),
            _m("Mid-campaign optimization", "pending", "2026-11-01", ["Campaign launch"]),
            _m("Campaign wrap", "pending", "2026-12-31", ["Mid-campaign optimization"]),
        ], budget=3000000)
    assert ini is not None
    deps = r._engine.analyze_dependencies(ini)
    assert deps is not None
    return {"scenario": "7. Marketing Campaign", "entity": "Marketing — Q4 Campaign",
            "milestones": len(ini.milestones), "dependencies": len(deps), "passed": True}


def test_initiative_disruption() -> dict[str, Any]:
    r = InitiativeIntelligenceRuntime()
    r.get_or_create_profile("startup_rocky", "Rocky Startup")
    ini = r.create_initiative("startup_rocky", InitiativeType.SOFTWARE_DEVELOPMENT.value,
        "Build Mobile App v1", "First version of mobile app",
        "Launch on App Store with 5 core features", "6-month dev cycle",
        milestones=[
            _m("Sprint 1-2: Auth & Profile", "completed", "2026-06-01"),
            _m("Sprint 3-4: Core features", "completed", "2026-07-01"),
            _m("Sprint 5-6: Payments", "delayed", "2026-08-01", ["Sprint 3-4: Core features"]),
            _m("Sprint 7: Testing", "blocked", "2026-08-15", ["Sprint 5-6: Payments"]),
            _m("App Store submission", "pending", "2026-09-01", ["Sprint 7: Testing"]),
        ])
    assert ini is not None
    assert len(ini.delayed_milestones) >= 1
    assert len(ini.blocked_milestones) >= 1

    analysis = r.analyze("startup_rocky", ini.initiative_id)
    assert analysis is not None
    assert len(analysis["bottlenecks"]) >= 1
    assert analysis["health"]["level"] != "healthy"

    # Adaptive replanning
    recs = r.adaptive_replan("startup_rocky", ini.initiative_id,
                              "Payment integration delayed by 3rd party API")
    assert len(recs) >= 1
    for rec in recs:
        assert "reasoning" in rec
        assert "evidence" in rec

    return {"scenario": "8. Initiative Disruption + Adaptive Execution",
            "entity": "Rocky Startup — Mobile App",
            "delayed": len(ini.delayed_milestones), "blocked": len(ini.blocked_milestones),
            "bottlenecks": len(analysis["bottlenecks"]),
            "health": analysis["health"]["level"],
            "replan_recs": len(recs),
            "passed": True}


def run_all() -> list[dict[str, Any]]:
    tests = [
        ("Startup Launch", test_startup_launch),
        ("Product Launch", test_product_launch),
        ("Personal Life Goal", test_personal_life_goal),
        ("Construction", test_construction_initiative),
        ("Research Initiative", test_research_initiative),
        ("Event Planning", test_event_planning),
        ("Marketing Campaign", test_marketing_campaign),
        ("Disruption + Adaptive Replan", test_initiative_disruption),
    ]
    results = []
    for n, fn in tests:
        try:
            r = fn()
            r["test_name"] = n; r["status"] = "PASS"; r["error"] = None
        except Exception as e:
            import traceback
            r = {"test_name": n, "scenario": n, "status": "FAIL",
                 "error": str(e), "traceback": traceback.format_exc(), "passed": False}
        results.append(r)
    return results


if __name__ == "__main__":
    print("UCP-08 — Universal Initiative Intelligence: Verification Report")
    results = run_all()
    passed = [r for r in results if r["passed"]]
    failed = [r for r in results if not r["passed"]]
    for r in results:
        s = "✅ PASS" if r["passed"] else "❌ FAIL"
        print(f"\n  {s} | {r.get('test_name', r['scenario'])}")
        print(f"         Entity: {r.get('entity', 'N/A')}")
        if r.get("milestones"): print(f"         Milestones: {r['milestones']}")
        if r.get("health"): print(f"         Health: {r['health']}")
        if r.get("bottlenecks") is not None: print(f"         Bottlenecks: {r['bottlenecks']}")
        if r.get("replan_recs") is not None: print(f"         Replan recs: {r['replan_recs']}")
        if r.get("error"): print(f"         ERROR: {r['error']}")
    print(f"\n  Total: {len(results)} | Passed: {len(passed)} | Failed: {len(failed)}")
    if not failed:
        print("\n  ✅ UCP-08 VERIFICATION PASSED: All 8 initiative scenarios through one capability.")
        print("  No Project Runtime. No Task Runtime. No Portfolio Runtime.")