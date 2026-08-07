"""UCP-10 Verification — Universal Health Intelligence.

Verifies 8 scenarios through the same capability:
1. Personal health tracking
2. Family wellness
3. Organizational health
4. Team health
5. Mental wellbeing
6. Preventive care
7. Chronic condition management
8. Health disruption with adaptive execution

Pattern follows UCP-08 (verify_ucp08.py) exactly.
"""

from __future__ import annotations
from typing import Any

from core.health_intelligence import (
    HealthIntelligenceRuntime,
    HealthDimension,
    HealthMetricType,
    HealthSeverity,
    HealthStatus,
)


def test_personal_health_tracking() -> dict[str, Any]:
    """Scenario 1: Personal health tracking for an individual."""
    r = HealthIntelligenceRuntime()
    r.get_or_create_profile("person_ananya", "Ananya — Personal Health", "individual")

    # Add metrics across dimensions
    r.add_metric("person_ananya", HealthMetricType.STEPS.value, 8500, "steps", "Daily walk")
    r.add_metric("person_ananya", HealthMetricType.SLEEP_HOURS.value, 7.5, "hours", "Night sleep")
    r.add_metric("person_ananya", HealthMetricType.HEART_RATE.value, 72, "bpm", "Resting heart rate")
    r.add_metric("person_ananya", HealthMetricType.WATER_INTAKE.value, 2.0, "liters", "Daily water")
    r.add_metric("person_ananya", HealthMetricType.EXERCISE_MINUTES.value, 45, "minutes", "Morning run")

    # Add wellness activities
    r.add_activity("person_ananya", "Morning jog", "exercise", HealthDimension.WELLNESS.value, 30, "moderate")
    r.add_activity("person_ananya", "Yoga session", "exercise", HealthDimension.WELLNESS.value, 20, "light")
    r.add_activity("person_ananya", "Meditation", "mindfulness", HealthDimension.MENTAL_WELLBEING.value, 15, "light")

    # Link compositions
    r.link_knowledge("person_ananya", "knw_001")
    r.link_decision("person_ananya", "dec_001")
    r.link_initiative("person_ananya", "ini_001")

    # Analyze
    analysis = r.analyze("person_ananya")
    assert analysis is not None, "Personal health analysis failed"
    assert "health" in analysis, "Missing health assessment"
    assert len(analysis["metrics"]) == 5, f"Expected 5 metrics, got {len(analysis['metrics'])}"
    assert len(analysis["activities"]) == 3, f"Expected 3 activities, got {len(analysis['activities'])}"

    return {
        "scenario": "1. Personal Health Tracking",
        "entity": "Ananya",
        "metrics": len(analysis["metrics"]),
        "activities": len(analysis["activities"]),
        "health": analysis["health"]["status"],
        "recommendations": len(analysis["recommendations"]),
        "passed": True,
    }


def test_family_wellness() -> dict[str, Any]:
    """Scenario 2: Family wellness profile with multiple members."""
    r = HealthIntelligenceRuntime()

    # Parent 1
    r.get_or_create_profile("parent_arun", "Arun — Father", "individual")
    r.add_metric("parent_arun", HealthMetricType.STEPS.value, 6000, "steps", "Daily walk")
    r.add_metric("parent_arun", HealthMetricType.STRESS_LEVEL.value, 6, "/10", "Work stress")
    r.add_condition("parent_arun", "Hypertension", "Mild hypertension, diagnosed 2024",
                    HealthDimension.MEDICAL_HISTORY.value, HealthSeverity.MODERATE.value,
                    HealthStatus.FAIR.value, "2024-06-15", managed=True)
    r.add_activity("parent_arun", "Evening walk", "exercise", HealthDimension.WELLNESS.value, 20, "light")

    # Parent 2
    r.get_or_create_profile("parent_priya", "Priya — Mother", "individual")
    r.add_metric("parent_priya", HealthMetricType.STEPS.value, 8000, "steps", "Daily activity")
    r.add_metric("parent_priya", HealthMetricType.MOOD_SCORE.value, 8, "/10", "Feeling great")
    r.add_activity("parent_priya", "Swimming", "exercise", HealthDimension.WELLNESS.value, 45, "moderate")

    # Child
    r.get_or_create_profile("child_ravi", "Ravi — Child", "individual")
    r.add_metric("child_ravi", HealthMetricType.EXERCISE_MINUTES.value, 60, "minutes", "Sports practice")
    r.add_metric("child_ravi", HealthMetricType.SLEEP_HOURS.value, 9, "hours", "Sleep well")

    # Create family meta profile
    family = r.get_or_create_profile("family_singh", "Singh Family Wellness", "family")
    family.journey_ids = ["journey_arun", "journey_priya", "journey_ravi"]

    analysis_arun = r.analyze("parent_arun")
    analysis_priya = r.analyze("parent_priya")
    analysis_ravi = r.analyze("child_ravi")

    assert analysis_arun is not None
    assert analysis_priya is not None
    assert analysis_ravi is not None

    return {
        "scenario": "2. Family Wellness",
        "entity": "Singh Family (3 members)",
        "members": 3,
        "profiles_analyzed": 3,
        "arun_health": analysis_arun["health"]["status"],
        "priya_health": analysis_priya["health"]["status"],
        "ravi_health": analysis_ravi["health"]["status"],
        "passed": True,
    }


def test_organizational_health() -> dict[str, Any]:
    """Scenario 3: Organizational health assessment."""
    r = HealthIntelligenceRuntime()
    r.get_or_create_profile("org_innotek", "InnoTek Inc — Organizational Health", "organization")

    # Organizational metrics
    r.add_metric("org_innotek", HealthMetricType.BURNOUT_RISK.value, 7.5, "/10", "Q3 survey")
    r.add_metric("org_innotek", HealthMetricType.TEAM_SATISFACTION.value, 6.2, "/10", "Employee survey")
    r.add_metric("org_innotek", HealthMetricType.ABSENTEEISM.value, 8.5, "%", "Monthly average")
    r.add_metric("org_innotek", HealthMetricType.TURNOVER_RISK.value, 7.0, "/10", "HR assessment")

    # Link compositions
    r.link_financial_profile("org_innotek", "fin_org_001")
    r.link_initiative("org_innotek", "ini_org_001")
    r.link_relationship("org_innotek", "rel_org_001")

    analysis = r.analyze("org_innotek")
    assert analysis is not None, "Organizational health analysis failed"
    assert len(analysis["organizational_recs"]) > 0, "Expected organizational health recommendations"
    assert analysis["health"]["status"] != HealthStatus.EXCELLENT.value, "Org health should show issues"

    return {
        "scenario": "3. Organizational Health",
        "entity": "InnoTek Inc",
        "metrics": len(analysis["metrics"]),
        "health": analysis["health"]["status"],
        "org_recs": len(analysis["organizational_recs"]),
        "passed": True,
    }


def test_team_health() -> dict[str, Any]:
    """Scenario 4: Team health assessment."""
    r = HealthIntelligenceRuntime()
    r.get_or_create_profile("team_alpha", "Team Alpha — Engineering", "team")

    # Team metrics
    r.add_metric("team_alpha", HealthMetricType.TEAM_SATISFACTION.value, 4.5, "/10", "Sprint retro")
    r.add_metric("team_alpha", HealthMetricType.WORK_LIFE_BALANCE.value, 5.0, "/10", "Team feedback")
    r.add_metric("team_alpha", HealthMetricType.BURNOUT_RISK.value, 8.0, "/10", "1:1 check-ins")
    r.add_metric("team_alpha", HealthMetricType.SOCIAL_INTERACTIONS.value, 3, "/week", "Team events")

    r.add_condition("team_alpha", "Low team morale", "Team morale affected by tight deadlines",
                    HealthDimension.TEAM.value, HealthSeverity.HIGH.value,
                    HealthStatus.AT_RISK.value, "2026-07-01", managed=False)

    analysis = r.analyze("team_alpha")
    assert analysis is not None, "Team health analysis failed"
    assert len(analysis["recommendations"]) > 0, "Expected team health recommendations"

    return {
        "scenario": "4. Team Health",
        "entity": "Team Alpha — Engineering",
        "metrics": len(analysis["metrics"]),
        "conditions": len(analysis["conditions"]),
        "health": analysis["health"]["status"],
        "recommendations": len(analysis["recommendations"]),
        "passed": True,
    }


def test_mental_wellbeing() -> dict[str, Any]:
    """Scenario 5: Mental wellbeing assessment."""
    r = HealthIntelligenceRuntime()
    r.get_or_create_profile("person_kiran", "Kiran — Mental Wellbeing", "individual")

    # Stress metrics — high values
    r.add_metric("person_kiran", HealthMetricType.STRESS_LEVEL.value, 8.5, "/10", "Work deadline week")
    r.add_metric("person_kiran", HealthMetricType.STRESS_LEVEL.value, 7.8, "/10", "Mid-week check")
    r.add_metric("person_kiran", HealthMetricType.STRESS_LEVEL.value, 8.0, "/10", "End of week")

    # Mood metrics — low values
    r.add_metric("person_kiran", HealthMetricType.MOOD_SCORE.value, 3.5, "/10", "Monday")
    r.add_metric("person_kiran", HealthMetricType.MOOD_SCORE.value, 4.0, "/10", "Wednesday")
    r.add_metric("person_kiran", HealthMetricType.MOOD_SCORE.value, 3.0, "/10", "Friday")

    # No mindfulness recorded
    r.add_metric("person_kiran", HealthMetricType.SLEEP_HOURS.value, 5.5, "hours", "Poor sleep")

    analysis = r.analyze("person_kiran")
    assert analysis is not None, "Mental wellbeing analysis failed"
    assert len(analysis["mental_recs"]) > 0, "Expected mental wellbeing recommendations"

    return {
        "scenario": "5. Mental Wellbeing",
        "entity": "Kiran",
        "metrics": len(analysis["metrics"]),
        "health": analysis["health"]["status"],
        "mental_recs": len(analysis["mental_recs"]),
        "passed": True,
    }


def test_preventive_care() -> dict[str, Any]:
    """Scenario 6: Preventive care recommendations."""
    r = HealthIntelligenceRuntime()
    r.get_or_create_profile("person_leela", "Leela — Preventive Care", "individual")

    # Add metrics but no screening or vaccination
    r.add_metric("person_leela", HealthMetricType.STEPS.value, 7000, "steps", "Walking")
    r.add_metric("person_leela", HealthMetricType.WEIGHT.value, 65, "kg", "Morning weight")
    r.add_metric("person_leela", HealthMetricType.BMI.value, 22.5, "kg/m2", "Calculated BMI")
    r.add_metric("person_leela", HealthMetricType.CHOLESTEROL.value, 180, "mg/dL", "Blood test")
    r.add_metric("person_leela", HealthMetricType.BLOOD_PRESSURE.value, 120, "mmHg", "Systolic")

    analysis = r.analyze("person_leela")
    assert analysis is not None, "Preventive care analysis failed"
    assert len(analysis["preventive_recs"]) > 0, "Expected preventive care recommendations"

    return {
        "scenario": "6. Preventive Care",
        "entity": "Leela",
        "metrics": len(analysis["metrics"]),
        "preventive_recs": len(analysis["preventive_recs"]),
        "health": analysis["health"]["status"],
        "passed": True,
    }


def test_chronic_condition_management() -> dict[str, Any]:
    """Scenario 7: Chronic condition management."""
    r = HealthIntelligenceRuntime()
    r.get_or_create_profile("person_deepak", "Deepak — Chronic Condition Management", "individual")

    # Chronic conditions
    r.add_condition("person_deepak", "Type 2 Diabetes", "Diagnosed 2023, managed with diet and medication",
                    HealthDimension.MEDICAL_HISTORY.value, HealthSeverity.MODERATE.value,
                    HealthStatus.FAIR.value, "2023-03-10", managed=True)
    r.add_condition("person_deepak", "High Cholesterol", "On statins, regular monitoring",
                    HealthDimension.MEDICAL_HISTORY.value, HealthSeverity.MODERATE.value,
                    HealthStatus.GOOD.value, "2023-03-10", managed=True)
    r.add_condition("person_deepak", "Knee Osteoarthritis", "Mild, managed with exercise",
                    HealthDimension.MEDICAL_HISTORY.value, HealthSeverity.LOW.value,
                    HealthStatus.GOOD.value, "2024-01-15", managed=True)

    # Relevant metrics
    r.add_metric("person_deepak", HealthMetricType.BLOOD_SUGAR.value, 140, "mg/dL", "Fasting")
    r.add_metric("person_deepak", HealthMetricType.BLOOD_SUGAR.value, 155, "mg/dL", "Post-meal")
    r.add_metric("person_deepak", HealthMetricType.CHOLESTEROL.value, 190, "mg/dL", "Latest panel")
    r.add_metric("person_deepak", HealthMetricType.EXERCISE_MINUTES.value, 30, "minutes", "Daily walk")

    # Wellness activities
    r.add_activity("person_deepak", "Morning walk", "exercise", HealthDimension.WELLNESS.value, 30, "moderate")

    # Link compositions
    r.link_agreement("person_deepak", "ins_health_001")
    r.link_decision("person_deepak", "dec_diet_001")
    r.link_knowledge("person_deepak", "knw_diabetes_001")
    r.link_initiative("person_deepak", "ini_health_goal_001")

    analysis = r.analyze("person_deepak")
    assert analysis is not None, "Chronic condition analysis failed"
    assert len(analysis["conditions"]) == 3, f"Expected 3 conditions, got {len(analysis['conditions'])}"
    assert any(c["managed"] for c in analysis["conditions"] if c["name"] == "Type 2 Diabetes"), "Diabetes should be managed"

    return {
        "scenario": "7. Chronic Condition Management",
        "entity": "Deepak",
        "conditions": len(analysis["conditions"]),
        "managed": sum(1 for c in analysis["conditions"] if c.get("managed")),
        "health": analysis["health"]["status"],
        "recommendations": len(analysis["recommendations"]),
        "passed": True,
    }


def test_health_disruption() -> dict[str, Any]:
    """Scenario 8: Health disruption with adaptive execution."""
    r = HealthIntelligenceRuntime()
    r.get_or_create_profile("person_fatima", "Fatima — Health Disruption", "individual")

    # Existing conditions
    r.add_condition("person_fatima", "Asthma", "Exercise-induced, well managed",
                    HealthDimension.MEDICAL_HISTORY.value, HealthSeverity.MODERATE.value,
                    HealthStatus.FAIR.value, "2020-05-01", managed=True)
    r.add_condition("person_fatima", "Seasonal Allergies", "Mild, managed with antihistamines",
                    HealthDimension.MEDICAL_HISTORY.value, HealthSeverity.LOW.value,
                    HealthStatus.GOOD.value, "2021-03-01", managed=True)

    # Good health metrics
    r.add_metric("person_fatima", HealthMetricType.STEPS.value, 10000, "steps", "Active day")
    r.add_metric("person_fatima", HealthMetricType.SLEEP_HOURS.value, 8, "hours", "Regular sleep")
    r.add_metric("person_fatima", HealthMetricType.EXERCISE_MINUTES.value, 40, "minutes", "Cardio")

    r.add_activity("person_fatima", "Running", "exercise", HealthDimension.WELLNESS.value, 30, "vigorous")

    # Add a disruption — new condition appears
    r.add_condition("person_fatima", "Respiratory Infection", "Acute bronchitis, triggered by pollution spike",
                    HealthDimension.MEDICAL_HISTORY.value, HealthSeverity.HIGH.value,
                    HealthStatus.AT_RISK.value, "2026-08-10", managed=False)

    r.add_metric("person_fatima", HealthMetricType.STRESS_LEVEL.value, 8, "/10", "Health anxiety")
    r.add_metric("person_fatima", HealthMetricType.HEART_RATE.value, 88, "bpm", "Elevated while sick")

    # Adaptive health response
    adaptive_recs = r.adaptive_health_response(
        "person_fatima",
        "Acute respiratory infection complicating existing asthma. Pollution levels at critical."
    )
    assert len(adaptive_recs) >= 1, "Expected adaptive recommendations"

    analysis = r.analyze("person_fatima")
    assert analysis is not None, "Disruption analysis failed"
    assert analysis["health"]["status"] != HealthStatus.EXCELLENT.value, "Health should be impacted by disruption"

    return {
        "scenario": "8. Health Disruption + Adaptive Execution",
        "entity": "Fatima",
        "conditions": len(analysis["conditions"]),
        "active_conditions": analysis["profile"]["active_conditions"],
        "health": analysis["health"]["status"],
        "adaptive_recs": len(adaptive_recs),
        "all_recs": len(analysis["recommendations"]),
        "passed": True,
    }


def run_all() -> list[dict[str, Any]]:
    tests = [
        ("Personal Health Tracking", test_personal_health_tracking),
        ("Family Wellness", test_family_wellness),
        ("Organizational Health", test_organizational_health),
        ("Team Health", test_team_health),
        ("Mental Wellbeing", test_mental_wellbeing),
        ("Preventive Care", test_preventive_care),
        ("Chronic Condition Management", test_chronic_condition_management),
        ("Health Disruption + Adaptive Execution", test_health_disruption),
    ]
    results = []
    for n, fn in tests:
        try:
            r = fn()
            r["test_name"] = n
            r["status"] = "PASS"
            r["error"] = None
        except Exception as e:
            import traceback
            r = {
                "test_name": n,
                "scenario": n,
                "status": "FAIL",
                "error": str(e),
                "traceback": traceback.format_exc(),
                "passed": False,
            }
        results.append(r)
    return results


if __name__ == "__main__":
    print("UCP-10 — Universal Health Intelligence: Verification Report")
    print("=" * 60)
    results = run_all()
    passed = [r for r in results if r["passed"]]
    failed = [r for r in results if not r["passed"]]

    for r in results:
        s = "✅ PASS" if r["passed"] else "❌ FAIL"
        print(f"\n  {s} | {r.get('test_name', r['scenario'])}")
        print(f"         Entity: {r.get('entity', 'N/A')}")
        if r.get("metrics") is not None:
            print(f"         Metrics: {r['metrics']}")
        if r.get("health"):
            print(f"         Health: {r['health']}")
        if r.get("conditions") is not None:
            print(f"         Conditions: {r['conditions']}")
        if r.get("recommendations") is not None:
            print(f"         Recommendations: {r['recommendations']}")
        if r.get("activities"):
            print(f"         Activities: {r['activities']}")
        if r.get("adaptive_recs") is not None:
            print(f"         Adaptive Recs: {r['adaptive_recs']}")
        if r.get("org_recs") is not None:
            print(f"         Org Recs: {r['org_recs']}")
        if r.get("mental_recs") is not None:
            print(f"         Mental Recs: {r['mental_recs']}")
        if r.get("preventive_recs") is not None:
            print(f"         Preventive Recs: {r['preventive_recs']}")
        if r.get("error"):
            print(f"         ERROR: {r['error']}")

    print(f"\n{'=' * 60}")
    print(f"  Total: {len(results)} | Passed: {len(passed)} | Failed: {len(failed)}")
    if not failed:
        print(f"\n  ✅ UCP-10 VERIFICATION PASSED: All 8 health scenarios through one capability.")
        print(f"  No Health Runtime. No Medical Runtime. No Wellness Runtime.")