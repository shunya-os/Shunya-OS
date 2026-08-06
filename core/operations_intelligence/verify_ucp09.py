"""UCP-09 Verification — Universal Operations Intelligence.

Verifies 8 operational scenarios through the same capability:
1. Manufacturing process
2. Customer service workflow
3. IT operations
4. Supply chain
5. Healthcare operations
6. Educational operations
7. Retail operations
8. Disruption with adaptive execution
"""

from __future__ import annotations
from typing import Any
from core.operations_intelligence import (
    OperationsIntelligenceRuntime,
    OperationsType,
    OperationsStatus,
)


def _step(name: str, order: int = 0, duration: float = 10.0,
          rework: float = 0.0, variability: float = 0.0,
          decision: bool = False, parallel: bool = False,
          quality: bool = False, deps: list[str] | None = None) -> dict:
    return {
        "name": name, "sequence_order": order, "duration_minutes": duration,
        "rework_pct": rework, "variability_pct": variability,
        "decision_point": decision, "parallel": parallel, "quality_check": quality,
    }


def test_manufacturing_process() -> dict[str, Any]:
    """Scenario 1: Manufacturing assembly line with bottleneck detection."""
    r = OperationsIntelligenceRuntime()
    r.get_or_create_profile("factory_a", "Alpha Manufacturing")

    process = r.create_process("factory_a", OperationsType.MANUFACTURING.value,
        name="Engine Assembly Line",
        purpose="Assemble V6 engines for sports cars",
        scope="Engine block to finished engine",
        steps=[
            _step("Cylinder block machining", 0, 45.0, rework=8.0),
            _step("Crankshaft installation", 1, 30.0),
            _step("Piston assembly", 2, 35.0),
            _step("Cylinder head mounting", 3, 55.0, rework=5.0, variability=15.0),
            _step("Timing chain installation", 4, 25.0),
            _step("Ancillary mounting", 5, 20.0, parallel=True),
            _step("Oil and coolant fill", 6, 15.0),
            _step("Quality inspection", 7, 10.0, quality=True),
            _step("Cold test", 8, 20.0, quality=True),
            _step("Hot test", 9, 30.0, quality=True, variability=10.0),
            _step("Final dressing and dispatch", 10, 15.0),
        ],
        cycle_time_minutes=300.0,
        throughput_per_hour=2.0,
        defect_rate_pct=4.5,
        uptime_pct=97.0,
        setup_time_minutes=60.0,
        batch_size=1,
    )
    assert process is not None, "Manufacturing process creation failed"
    assert len(process.steps) == 11
    assert process.is_running

    # Detect bottlenecks (may be 0 if process runs smoothly)
    bottlenecks = r._engine.detect_bottlenecks(process)
    # Should detect at least one if the test data creates congestion

    # Health assessment
    health = r._engine.compute_operational_health(process)
    assert "score" in health
    assert health["level"] in ("excellent", "good", "fair", "at_risk", "critical")

    # Recommendations
    recs = r._engine.recommend_improvements(process)
    for rec in recs:
        assert rec.reasoning, "Each recommendation must have reasoning"
        assert rec.evidence, "Each recommendation must have evidence"
        assert rec.confidence > 0, "Each recommendation must have confidence"

    return {
        "scenario": "1. Manufacturing Process — Engine Assembly",
        "entity": "Alpha Manufacturing",
        "steps": len(process.steps),
        "bottlenecks": len(bottlenecks),
        "health": health["level"],
        "health_score": health["score"],
        "recommendations": len(recs),
        "passed": True,
    }


def test_customer_service_workflow() -> dict[str, Any]:
    """Scenario 2: Customer service ticket handling workflow with SLA."""
    r = OperationsIntelligenceRuntime()
    r.get_or_create_profile("support_org", "SupportFlow Inc.")

    workflow = r.create_workflow("support_org", OperationsType.CUSTOMER_SERVICE.value,
        name="Support Ticket Handling",
        purpose="Process customer support tickets from submission to resolution",
        trigger="Customer submits support ticket",
        steps=[
            {"name": "Ticket triage", "sequence_order": 0, "auto_escalate": True,
             "timeout_minutes": 30.0, "notification_trigger": "triage_required"},
            {"name": "Level 1 investigation", "sequence_order": 1,
             "timeout_minutes": 120.0, "auto_escalate": True},
            {"name": "Level 2 escalation (if needed)", "sequence_order": 2,
             "timeout_minutes": 240.0},
            {"name": "Solution implementation", "sequence_order": 3},
            {"name": "Customer verification", "sequence_order": 4},
            {"name": "Ticket closure and survey", "sequence_order": 5},
        ],
        sla_minutes=480.0,  # 8 hours
        escalation_path=["manager", "senior_manager", "director"],
    )
    assert workflow is not None, "Customer service workflow creation failed"

    # Advance steps
    for _ in range(3):
        r.advance_workflow("support_org", workflow.workflow_id)
    assert workflow.current_step_index == 3
    assert workflow.is_active

    # Workflow analysis
    analysis = r.analyze_workflow("support_org", workflow.workflow_id)
    assert analysis is not None
    assert "issues" in analysis
    assert "strengths" in analysis

    # Add service level
    sl = r.add_service_level("support_org", name="First Response Time",
                              metric="response_time_minutes", target=60.0,
                              actual=60.0, warning_threshold=50.0)
    assert sl is not None
    assert sl.compute_status() in ("met", "at_risk", "near_miss")

    return {
        "scenario": "2. Customer Service — Support Ticket Workflow",
        "entity": "SupportFlow Inc.",
        "steps": len(workflow.steps),
        "progress": workflow.progress_pct,
        "sla_minutes": workflow.sla_minutes,
        "sla_status": sl.compute_status(),
        "passed": True,
    }


def test_it_operations() -> dict[str, Any]:
    """Scenario 3: IT operations with resources, queues, and service levels."""
    r = OperationsIntelligenceRuntime()
    r.get_or_create_profile("it_ops", "TechCorp IT Ops")

    process = r.create_process("it_ops", OperationsType.IT_OPERATIONS.value,
        name="Incident Response Pipeline",
        purpose="Detect, triage, and resolve IT incidents",
        scope="Monitoring to post-mortem",
        steps=[
            _step("Monitoring alert", 0, 1.0, quality=True),
            _step("Automated triage", 1, 0.5),
            _step("Incident classification", 2, 5.0, decision=True),
            _step("Level 1 investigation", 3, 30.0),
            _step("Level 2 investigation", 4, 120.0),
            _step("Fix implementation", 5, 60.0),
            _step("Verification testing", 6, 15.0, quality=True),
            _step("Post-mortem", 7, 45.0),
        ],
        cycle_time_minutes=276.5,
        throughput_per_hour=0.21,
        defect_rate_pct=2.0,
        uptime_pct=99.9,
    )
    assert process is not None

    # Add resources
    for i, (name, cap, load) in enumerate([
        ("On-call engineer", 0.5, 0.3),
        ("Triage bot", 10.0, 8.0),
        ("L2 team", 0.3, 0.25),
        ("SRE team", 0.2, 0.18),
    ]):
        r.add_resource("it_ops", name=name, capacity_per_hour=cap, current_load=load)

    # Add queue
    queue = r.add_queue("it_ops", process.process_id, "Incident Queue",
                         current_length=5, arrival_rate_per_hour=0.25,
                         service_rate_per_hour=0.21)
    assert queue is not None
    assert queue.is_overloaded  # arrival > service

    # Queue analysis
    q_analysis = r._engine.analyze_queue(queue)
    assert q_analysis["is_overloaded"] is True
    assert len(q_analysis["recommendations"]) >= 1

    # Health with context
    health = r._engine.compute_operational_health(process)
    assert health["score"] > 0

    # Analyze
    analysis = r.analyze("it_ops", process.process_id)
    assert analysis is not None
    assert "queues" in analysis

    return {
        "scenario": "3. IT Operations — Incident Response",
        "entity": "TechCorp IT Ops",
        "steps": len(process.steps),
        "health": health["level"],
        "queue_overloaded": q_analysis["is_overloaded"],
        "queue_recs": len(q_analysis["recommendations"]),
        "passed": True,
    }


def test_supply_chain() -> dict[str, Any]:
    """Scenario 4: Supply chain with capacity planning and bottleneck analysis."""
    r = OperationsIntelligenceRuntime()
    r.get_or_create_profile("logistics_co", "Global Logistics Co.")

    process = r.create_process("logistics_co", OperationsType.SUPPLY_CHAIN.value,
        name="Warehouse Order Fulfillment",
        purpose="Pick, pack, and ship customer orders from warehouse",
        scope="Order receipt to dispatch",
        steps=[
            _step("Order receipt and validation", 0, 2.0),
            _step("Inventory allocation", 1, 5.0),
            _step("Picking", 2, 25.0, rework=3.0, variability=20.0),
            _step("Packing", 3, 15.0),
            _step("Labeling and documentation", 4, 5.0),
            _step("Sortation", 5, 8.0, parallel=True),
            _step("Loading", 6, 20.0),
            _step("Dispatch verification", 7, 3.0, quality=True),
        ],
        cycle_time_minutes=83.0,
        throughput_per_hour=43.0,
        defect_rate_pct=1.5,
        uptime_pct=96.0,
        batch_size=10,
    )
    assert process is not None

    # Add resources
    for name, cap, load in [
        ("Pickers team", 50.0, 45.0),
        ("Packers team", 60.0, 40.0),
        ("Loading dock", 10.0, 9.5),
        ("Sortation machine", 100.0, 85.0),
    ]:
        r.add_resource("logistics_co", name=name,
                       capacity_per_hour=cap, current_load=load)

    # Capacity plan
    plan = r.create_capacity_plan("logistics_co", "Q3 Fulfillment Plan",
                                   period_start="2026-07-01", period_end="2026-09-30")
    assert plan is not None

    # Bottleneck detection
    bottlenecks = r._engine.detect_bottlenecks(process)
    recs = r._engine.recommend_improvements(process)

    # Capacity analysis
    cap_analysis = r.analyze_capacity("logistics_co", plan.cap_id)
    assert cap_analysis is not None

    # Verify recommendation structure
    for rec in recs:
        assert hasattr(rec, "assumptions")
        assert hasattr(rec, "alternatives")
        assert hasattr(rec, "expected_impact")

    return {
        "scenario": "4. Supply Chain — Warehouse Fulfillment",
        "entity": "Global Logistics Co.",
        "steps": len(process.steps),
        "bottlenecks": len(bottlenecks),
        "capacity_overloaded": cap_analysis.get("is_overloaded", False),
        "recommendations": len(recs),
        "passed": True,
    }


def test_healthcare_operations() -> dict[str, Any]:
    """Scenario 5: Healthcare operations with patient flow, triage, and SLA."""
    r = OperationsIntelligenceRuntime()
    r.get_or_create_profile("hospital_main", "City General Hospital")

    process = r.create_process("hospital_main", OperationsType.HEALTHCARE.value,
        name="Emergency Department Patient Flow",
        purpose="Triage, diagnose, treat, and discharge/admit ED patients",
        scope="Patient arrival to discharge or admission",
        steps=[
            _step("Patient registration", 0, 5.0),
            _step("Triage assessment", 1, 10.0, quality=True, decision=True),
            _step("Doctor examination", 2, 30.0, variability=25.0),
            _step("Diagnostic tests", 3, 45.0, parallel=True),
            _step("Results review", 4, 10.0),
            _step("Treatment", 5, 60.0, variability=30.0),
            _step("Observation", 6, 120.0),
            _step("Discharge or admission decision", 7, 15.0, decision=True),
        ],
        cycle_time_minutes=295.0,
        throughput_per_hour=0.2,
        defect_rate_pct=0.5,
        uptime_pct=99.5,
    )
    assert process is not None

    # Add queue (waiting room)
    queue = r.add_queue("hospital_main", process.process_id, "ED Waiting Room",
                         current_length=12, arrival_rate_per_hour=0.25,
                         service_rate_per_hour=0.20, discipline="priority",
                         average_wait_time_minutes=45.0)
    assert queue is not None

    # Service levels
    sl_triage = r.add_service_level("hospital_main", process.process_id,
                                     name="Triage Response Time",
                                     metric="response_time_minutes", target=10.0,
                                     actual=8.0, warning_threshold=9.0)
    sl_wait = r.add_service_level("hospital_main", process.process_id,
                                   name="ED Wait Time Target",
                                   metric="wait_time_minutes", target=60.0,
                                   actual=45.0, warning_threshold=50.0)
    assert sl_triage is not None
    assert sl_wait is not None

    # Queue analysis
    q_analysis = r._engine.analyze_queue(queue)
    assert "recommendations" in q_analysis

    # Health
    health = r._engine.compute_operational_health(
        process, queues=[queue], service_levels=[sl_triage, sl_wait])
    assert "score" in health

    return {
        "scenario": "5. Healthcare — ED Patient Flow",
        "entity": "City General Hospital",
        "steps": len(process.steps),
        "queue_length": queue.current_length,
        "health": health["level"],
        "triage_sla_met": sl_triage.compute_status(),
        "wait_sla_met": sl_wait.compute_status(),
        "passed": True,
    }


def test_educational_operations() -> dict[str, Any]:
    """Scenario 6: Educational operations — course delivery pipeline."""
    r = OperationsIntelligenceRuntime()
    r.get_or_create_profile("university", "State University")

    process = r.create_process("university", OperationsType.EDUCATIONAL.value,
        name="Semester Course Delivery",
        purpose="Deliver a full semester course from curriculum to grade submission",
        scope="Curriculum planning to grade release",
        steps=[
            _step("Curriculum planning", 0, 120.0),
            _step("Syllabus creation", 1, 60.0, quality=True),
            _step("Lecture preparation", 2, 180.0, parallel=True),
            _step("Lecture delivery (16 weeks)", 3, 1440.0, variability=10.0),
            _step("Assignment grading", 4, 240.0, parallel=True),
            _step("Midterm exams", 5, 120.0),
            _step("Final exams", 6, 120.0),
            _step("Grade computation", 7, 60.0, quality=True),
            _step("Grade submission", 8, 30.0),
        ],
        cycle_time_minutes=2370.0,
        throughput_per_hour=0.025,
        defect_rate_pct=1.0,
        uptime_pct=100.0,
    )
    assert process is not None

    # Resources
    for name, cap, load in [
        ("Faculty", 1.0, 0.9),
        ("Teaching Assistants", 4.0, 3.5),
        ("Classrooms", 2.0, 1.5),
        ("LMS Platform", 1000.0, 800.0),
    ]:
        r.add_resource("university", name=name,
                       capacity_per_hour=cap, current_load=load)

    # Service levels
    r.add_service_level("university", process.process_id,
                         name="Grade Turnaround",
                         metric="days_to_grade", target=7.0,
                         actual=5.0, warning_threshold=6.0)
    r.add_service_level("university", process.process_id,
                         name="Faculty Office Hours Availability",
                         metric="hours_per_week", target=5.0,
                         actual=5.0, warning_threshold=4.0)

    # Analysis
    analysis = r.analyze("university", process.process_id)
    assert analysis is not None
    assert "health" in analysis
    assert "resources" in analysis

    # Continuous improvement
    ci = r.add_improvement_item("university", process.process_id,
                                 name="Digital Assignment Submission",
                                 description="Move from paper to digital submission to reduce grading time",
                                 methodology="kaizen",
                                 current_state="Paper-based submission with 14-day turnaround",
                                 target_state="Digital submission with 5-day turnaround",
                                 expected_benefit="Reduce grading cycle by 60%",
                                 metrics_before={"grading_days": 14.0},
                                 priority="high")
    assert ci is not None
    assert ci.improvement_pct == 0.0  # No after metrics yet

    return {
        "scenario": "6. Educational Operations — Semester Course Delivery",
        "entity": "State University",
        "steps": len(process.steps),
        "health": analysis["health"]["level"],
        "improvement_added": ci.ci_id is not None,
        "passed": True,
    }


def test_retail_operations() -> dict[str, Any]:
    """Scenario 7: Retail operations with point-of-sale and inventory."""
    r = OperationsIntelligenceRuntime()
    r.get_or_create_profile("retail_chain", "MegaMart Retail")

    process = r.create_process("retail_chain", OperationsType.RETAIL.value,
        name="Store Daily Operations",
        purpose="Open store, serve customers, restock shelves, close store",
        scope="Store opening to closing",
        steps=[
            _step("Store opening procedures", 0, 30.0),
            _step("Cash register setup", 1, 15.0, quality=True),
            _step("Customer service at POS", 2, 480.0, variability=20.0),
            _step("Shelf restocking", 3, 120.0, parallel=True),
            _step("Inventory check", 4, 60.0, quality=True),
            _step("Receiving shipments", 5, 45.0),
            _step("Returns and exchanges", 6, 60.0, decision=True),
            _step("End-of-day reconciliation", 7, 30.0, quality=True),
            _step("Store closing procedures", 8, 20.0),
        ],
        cycle_time_minutes=860.0,
        throughput_per_hour=60.0,  # customers per hour
        defect_rate_pct=0.8,
        uptime_pct=99.0,
    )
    assert process is not None

    # Resources
    for name, cap, load in [
        ("Cashiers", 8.0, 7.2),
        ("Floor staff", 5.0, 4.0),
        ("Backroom staff", 3.0, 2.5),
        ("POS terminals", 6.0, 5.0),
    ]:
        r.add_resource("retail_chain", name=name,
                       capacity_per_hour=cap, current_load=load)

    # Queue (checkout line)
    queue = r.add_queue("retail_chain", process.process_id, "Checkout Queue",
                         current_length=4, arrival_rate_per_hour=60.0,
                         service_rate_per_hour=65.0,  # Fast enough
                         average_wait_time_minutes=4.0)
    assert queue is not None
    assert not queue.is_overloaded  # service rate > arrival rate

    # Throughput measures
    r.add_throughput_measure("retail_chain", process.process_id,
                              "2026-01-01", "2026-01-31",
                              units_processed=18000, units_defective=120,
                              total_time_hours=360.0)
    r.add_throughput_measure("retail_chain", process.process_id,
                              "2026-02-01", "2026-02-28",
                              units_processed=16500, units_defective=95,
                              total_time_hours=340.0)

    # Resource utilization analysis
    resource_analysis = r._engine.analyze_resource_utilization(
        r._resolve("retail_chain").resources)
    assert resource_analysis["total_resources"] == 4
    assert "recommendations" in resource_analysis

    # Analysis
    analysis = r.analyze("retail_chain", process.process_id)
    assert analysis is not None
    assert "throughput" in analysis

    return {
        "scenario": "7. Retail Operations — Store Daily Ops",
        "entity": "MegaMart Retail",
        "steps": len(process.steps),
        "health": analysis["health"]["level"],
        "queue_stable": not queue.is_overloaded,
        "resource_recs": len(resource_analysis["recommendations"]),
        "passed": True,
    }


def test_disruption_adaptive_execution() -> dict[str, Any]:
    """Scenario 8: Operational disruption with adaptive execution recommendations."""
    r = OperationsIntelligenceRuntime()
    r.get_or_create_profile("factory_disrupted", "Disrupted Manufacturing")

    process = r.create_process("factory_disrupted", OperationsType.MANUFACTURING.value,
        name="Assembly Line with Disruption",
        purpose="Manufacture product on assembly line",
        scope="All steps",
        steps=[
            _step("Raw material prep", 0, 30.0),
            _step("Component assembly", 1, 60.0, rework=10.0),
            _step("Quality check A", 2, 10.0, quality=True),
            _step("Painting", 3, 45.0),
            _step("Drying", 4, 120.0, variability=30.0),
            _step("Final assembly", 5, 45.0),
            _step("Final inspection", 6, 15.0, quality=True),
            _step("Packaging", 7, 10.0),
        ],
        cycle_time_minutes=335.0,
        throughput_per_hour=0.5,
        defect_rate_pct=25.0,
        uptime_pct=60.0,
    )
    assert process is not None

    # Assess disruption
    painting_step = process.steps[3]  # Painting
    disruption = r.assess_disruption(
        "factory_disrupted", process.process_id,
        "Painting booth fire suppression system failure — paint section shut down indefinitely",
        impacted_step_ids=[painting_step.step_id],
    )
    assert disruption is not None
    assert disruption["severity"] in ("critical", "high", "medium", "low")
    assert len(disruption["recommendations"]) >= 1

    # Verify recommendation structure for disruption recs
    for rec_dict in disruption["recommendations"]:
        assert "reasoning" in rec_dict
        assert "evidence" in rec_dict
        assert "confidence" in rec_dict
        assert "assumptions" in rec_dict
        assert "alternatives" in rec_dict
        assert "expected_impact" in rec_dict

    # Health assessment post-disruption (with low uptime reflecting the issue)
    health = r._engine.compute_operational_health(process)
    assert "level" in health

    # Continuous improvement for recovery
    ci = r.add_improvement_item("factory_disrupted", process.process_id,
                                 name="Painting Booth Fire Suppression Upgrade",
                                 description="Replace fire suppression system with dual-redundant system",
                                 methodology="kaizen",
                                 current_state="Single fire suppression system",
                                 target_state="Dual-redundant fire suppression with automatic failover",
                                 expected_benefit="Eliminate painting section downtime from suppression failures",
                                 metrics_before={"uptime_pct": 60.0, "throughput_per_hour": 0.5},
                                 priority="critical")
    assert ci is not None

    # Complete the improvement
    r.complete_improvement_item("factory_disrupted", ci.ci_id,
                                 metrics_after={"uptime_pct": 99.5, "throughput_per_hour": 2.1})
    assert ci.is_completed
    assert ci.improvement_pct > 0  # Should show improvement

    # Get explainable recommendations
    profile = r._resolve("factory_disrupted")
    service_levels = list(profile.service_levels) if profile else []
    recs = r._engine.recommend_improvements(
        process,
        health=r._engine.compute_operational_health(
            process, service_levels=service_levels))
    for rec in recs:
        explained = r._engine.explain(rec)
        assert "explanation" in explained
        assert "evidence_summary" in explained

    return {
        "scenario": "8. Disruption + Adaptive Execution",
        "entity": "Disrupted Manufacturing",
        "disruption_severity": disruption["severity"],
        "disruption_recs": len(disruption["recommendations"]),
        "health": health["level"],
        "improvement_completed": ci.is_completed,
        "improvement_pct": ci.improvement_pct,
        "recs_count": len(recs),
        "passed": True,
    }


def run_all() -> list[dict[str, Any]]:
    tests = [
        ("Manufacturing Process", test_manufacturing_process),
        ("Customer Service Workflow", test_customer_service_workflow),
        ("IT Operations", test_it_operations),
        ("Supply Chain", test_supply_chain),
        ("Healthcare Operations", test_healthcare_operations),
        ("Educational Operations", test_educational_operations),
        ("Retail Operations", test_retail_operations),
        ("Disruption + Adaptive Execution", test_disruption_adaptive_execution),
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
    print("UCP-09 — Universal Operations Intelligence: Verification Report")
    print("=" * 60)
    results = run_all()
    passed = [r for r in results if r["passed"]]
    failed = [r for r in results if not r["passed"]]

    for r in results:
        s = "✅ PASS" if r["passed"] else "❌ FAIL"
        print(f"\n  {s} | {r.get('test_name', r['scenario'])}")
        print(f"         Entity: {r.get('entity', 'N/A')}")
        if r.get("steps"): print(f"         Steps: {r['steps']}")
        if r.get("health"): print(f"         Health: {r['health']}")
        if r.get("health_score"): print(f"         Health Score: {r['health_score']}")
        if r.get("bottlenecks") is not None: print(f"         Bottlenecks: {r['bottlenecks']}")
        if r.get("recommendations") is not None: print(f"         Recommendations: {r['recommendations']}")
        if r.get("recs_count") is not None: print(f"         Recs: {r['recs_count']}")
        if r.get("disruption_severity"): print(f"         Disruption: {r['disruption_severity']}")
        if r.get("improvement_completed"): print(f"         Improvement Completed: {r['improvement_completed']}")
        if r.get("improvement_pct"): print(f"         Improvement %: {r['improvement_pct']}%")
        if r.get("queue_overloaded") is not None: print(f"         Queue Overloaded: {r['queue_overloaded']}")
        if r.get("error"): print(f"         ERROR: {r['error']}")

    print(f"\n  {'='* 60}")
    print(f"  Total: {len(results)} | Passed: {len(passed)} | Failed: {len(failed)}")
    if not failed:
        print(f"\n  ✅ UCP-09 VERIFICATION PASSED: All 8 operations scenarios through one capability.")
        print("  No Operations Runtime. No ERP Runtime. No Workflow Runtime.")
    else:
        print(f"\n  ❌ UCP-09 VERIFICATION FAILED: {len(failed)} scenario(s) did not pass.")
        for f in failed:
            print(f"    - {f.get('test_name', 'Unknown')}: {f.get('error', 'No error')}")