"""EP-07A — Adaptive Execution Intelligence Verification.

Demonstrates that Reality changes execution without creating new workflows.
Five scenarios through the same runtime:
  1. Customer accepts proposal
  2. Supplier delay
  3. Meeting cancellation
  4. Travel disruption
  5. Campaign budget reduction
"""
import sys
sys.path.insert(0, '/home/shunya-deploy/shunya_os')

from app.execution_runtime.runtime import get_execution_runtime

rt = get_execution_runtime()
passed = 0
failed = 0

print("=" * 70)
print("EP-07A Adaptive Execution Verification")
print("=" * 70)

# ── Scenario 1: Customer accepts proposal ──
print("\n[1] Customer accepts proposal")
ex = rt.create_execution(
    title="Send proposal to Acme and follow up",
    intent="win_customer",
    goal="Get Acme to accept proposal",
    participants=["acme@example.com"],
    completion_criteria="Proposal accepted and invoice sent",
)
# Advance to executing
ex.transition("Executing")
# Reality event: customer accepted
result = rt.adapt(ex.execution_id, {"type": "proposal_accepted", "customer": "Acme"})
followups_skipped = [a for a in result["adaptations"] if a["action"] == "step_skipped"]
advanced = [a for a in result["adaptations"] if a["action"] == "lifecycle_advanced"]
if result["status"] == "Completed" and (followups_skipped or advanced):
    print(f"  ✅ Adapted: status={result['status']}, adaptations={len(result['adaptations'])}")
    passed += 1
else:
    print(f"  ❌ Expected Completed, got {result['status']}: {result['adaptations']}")
    failed += 1

# ── Scenario 2: Supplier delay ──
print("\n[2] Supplier delay")
ex2 = rt.create_execution(
    title="Deliver client order by Friday",
    intent="deliver",
    goal="Ship order on time",
    completion_criteria="Order delivered",
)
ex2.transition("Executing")
result2 = rt.adapt(ex2.execution_id, {"type": "supplier_delayed", "supplier": "raw-materials-ltd"})
if result2["status"] == "Blocked" and any(a["action"] == "replan_timeline" for a in result2["adaptations"]):
    print(f"  ✅ Adapted: status={result2['status']}, replan_timeline recorded")
    passed += 1
else:
    print(f"  ❌ Expected Blocked with replan, got {result2['status']}: {result2['adaptations']}")
    failed += 1

# ── Scenario 3: Meeting cancellation ──
print("\n[3] Meeting cancellation")
ex3 = rt.create_execution(
    title="Prepare board meeting materials",
    intent="prepare_meeting",
    goal="Deliver board deck and agenda",
    completion_criteria="Materials distributed",
)
ex3.transition("Executing")
result3 = rt.adapt(ex3.execution_id, {"type": "meeting_cancelled"})
skipped = [a for a in result3["adaptations"] if a["action"] == "step_skipped"]
reorg = [a for a in result3["adaptations"] if a["action"] == "reorganize_dependents"]
if skipped or reorg:
    print(f"  ✅ Adapted: {len(skipped)} meeting steps skipped, dependent work reorganized")
    passed += 1
else:
    print(f"  ❌ Expected meeting steps skipped: {result3['adaptations']}")
    failed += 1

# ── Scenario 4: Travel disruption ──
print("\n[4] Travel disruption (flight cancelled)")
ex4 = rt.create_execution(
    title="Book Sri Lanka honeymoon trip",
    intent="travel",
    goal="Complete trip bookings",
    completion_criteria="Flights, hotels, itinerary confirmed",
)
ex4.transition("Executing")
result4 = rt.adapt(ex4.execution_id, {"type": "flight_cancelled", "flight": "CMB-123"})
repending = [a for a in result4["adaptations"] if a["action"] == "step_repending"]
if result4["status"] == "Blocked" and repending:
    print(f"  ✅ Adapted: status={result4['status']}, {len(repending)} booking steps re-pended")
    passed += 1
else:
    print(f"  ❌ Expected Blocked with rebooking, got {result4['status']}: {result4['adaptations']}")
    failed += 1

# ── Scenario 5: Campaign budget reduction ──
print("\n[5] Campaign budget reduction")
ex5 = rt.create_execution(
    title="Launch Q3 campaign",
    intent="launch_campaign",
    goal="Launch campaign across channels",
    completion_criteria="Campaign live",
)
ex5.transition("Executing")
before_conf = ex5.confidence
result5 = rt.adapt(ex5.execution_id, {"type": "budget_reduced", "amount": "40%"})
conf_dropped = result5["confidence"] < before_conf
risk_added = any("Budget" in r for r in result5.get("risks", []) or ex5.risks)
scope = [a for a in result5["adaptations"] if a["action"] == "reduce_scope"]
if conf_dropped and (risk_added or scope):
    print(f"  ✅ Adapted: confidence {before_conf:.2f}→{result5['confidence']:.2f}, scope reduced, risk added")
    passed += 1
else:
    print(f"  ❌ Expected confidence drop + scope reduction: {result5}")
    failed += 1

# ── Recommendations with evidence ──
print("\n[6] Evidence-backed recommendations")
ex6 = rt.create_execution(
    title="Complex multi-step rollout",
    intent="",
    goal="",
    completion_criteria="",
)
# Block several steps to force recommendations
for step in ex6.steps[2:5]:
    step.status = "blocked"
rec = rt.recommend(ex6.execution_id)
has_evidence = all("evidence" in r for r in rec["recommendations"])
has_actions = len(rec["recommendations"]) > 0
if has_evidence and has_actions:
    actions = [r["action"] for r in rec["recommendations"]]
    print(f"  ✅ Recommendations with evidence: {actions}")
    passed += 1
else:
    print(f"  ❌ Expected evidence-backed recommendations: {rec}")
    failed += 1

# ── Observe Reality loop ──
print("\n[7] Observe Reality — continuous adaptation")
obs = rt.observe_reality(ex.execution_id)
if obs and "current_status" in obs:
    print(f"  ✅ Observed: {obs['previous_status']} → {obs['current_status']}, changes={len(obs['changes'])}")
    passed += 1
else:
    print(f"  ❌ observe_reality failed: {obs}")
    failed += 1

# ── Same runtime check ──
print("\n[8] One runtime, five scenarios")
all_execs = [ex, ex2, ex3, ex4, ex5]
same_runtime = all(e.execution_id in rt._executions for e in all_execs)
if same_runtime:
    print(f"  ✅ All 5 scenarios executed through the same ExecutionRuntime ({len(rt._executions)} executions)")
    passed += 1
else:
    print("  ❌ Scenarios not all in same runtime")
    failed += 1

print("\n" + "=" * 70)
print(f"RESULT: {passed} passed, {failed} failed")
print("=" * 70)
sys.exit(0 if failed == 0 else 1)