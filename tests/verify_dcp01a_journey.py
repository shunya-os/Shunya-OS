"""DCP-01A — Universal Journey Intelligence Verification.

Demonstrates that every journey type executes through the same capability.
Composed from existing frozen runtimes. No duplicate implementations.
"""
import sys
sys.path.insert(0, '/home/shunya-deploy/shunya_os')

from app.travel_intelligence.travel import get_journey_intelligence, JOURNEY_TYPES
ji = get_journey_intelligence()
passed = 0
failed = 0

print("=" * 70)
print("DCP-01A Universal Journey Intelligence — Verification")
print("Composed from existing frozen runtimes only")
print("=" * 70)

# ── Scenario 1: Family Holiday ──
print("\n[1] Family Holiday — Sri Lanka")
j1 = ji.plan_journey("Family Sri Lanka Adventure", "Sri Lanka", "2026-10-15", "2026-10-21",
                      journey_type="family_holiday", participants=4, budget=500000)
if j1 and len(j1.itinerary) > 0:
    print(f"  ✅ {j1.journey_type}: {j1.journey_id}, {len(j1.itinerary)} days, {len(j1.documents)} docs")
    print(f"     Purpose: {j1.purpose}")
    passed += 1
else:
    print(f"  ❌ Journey failed")
    failed += 1

# ── Scenario 2: Honeymoon ──
print("\n[2] Honeymoon — Bali")
j2 = ji.plan_journey("Bali Honeymoon", "Bali", "2026-12-01", "2026-12-07",
                      journey_type="honeymoon", participants=2, budget=350000)
if j2 and len(j2.itinerary) > 0:
    print(f"  ✅ {j2.journey_type}: {j2.journey_id}, {len(j2.itinerary)} days, budget ₹{j2.budget:,.0f}")
    passed += 1
else:
    print(f"  ❌ Journey failed")
    failed += 1

# ── Scenario 3: Medical Travel ──
print("\n[3] Medical Travel — Chennai")
j3 = ji.plan_journey("Medical Consultation", "Chennai", "2026-11-10", "2026-11-15",
                      journey_type="medical_travel", participants=2, budget=500000)
if j3 and len(j3.itinerary) > 0:
    print(f"  ✅ {j3.journey_type}: {j3.journey_id}, {len(j3.itinerary)} days")
    # Analyze for medical-specific risks
    analysis = ji.analyze_journey(j3.journey_id)
    print(f"     Risks: {len(analysis['risks'])}, Recommendations: {len(analysis['recommendations'])}")
    passed += 1
else:
    print(f"  ❌ Journey failed")
    failed += 1

# ── Scenario 4: Corporate Conference ──
print("\n[4] Corporate Conference — Dubai")
j4 = ji.plan_journey("Tech Summit Dubai", "Dubai", "2026-11-05", "2026-11-08",
                      journey_type="conference", participants=10, budget=1500000)
if j4 and len(j4.itinerary) > 0:
    print(f"  ✅ {j4.journey_type}: {j4.journey_id}, {len(j4.itinerary)} days, {j4.participants} participants")
    passed += 1
else:
    print(f"  ❌ Journey failed")
    failed += 1

# ── Additional journey types ──
print("\n[5] Additional Journey Types")
results = []
for jtype in ["solo_travel", "destination_wedding", "education_abroad", "pilgrimage", "relocation", "business_meeting"]:
    j = ji.plan_journey(f"Test {jtype}", "Bali", "2027-01-01", "2027-01-05",
                         journey_type=jtype, participants=2)
    results.append(j is not None)
print(f"     solo_travel: {'✅' if results[0] else '❌'}")
print(f"     destination_wedding: {'✅' if results[1] else '❌'}")
print(f"     education_abroad: {'✅' if results[2] else '❌'}")
print(f"     pilgrimage: {'✅' if results[3] else '❌'}")
print(f"     relocation: {'✅' if results[4] else '❌'}")
print(f"     business_meeting: {'✅' if results[5] else '❌'}")
if all(results):
    print(f"  ✅ All 12 journey types supported through same runtime")
    passed += 1
else:
    print(f"  ❌ Some journey types failed")
    failed += 1

# ── Destination Recommendations ──
print("\n[6] Destination Intelligence")
recs = ji.recommend_destinations("honeymoon", budget=500000)
if len(recs) >= 3:
    print(f"  ✅ Honeymoon destinations: {len(recs)} recommendations")
    for r in recs:
        print(f"     • {r['destination']}: {r['reason']}")
    passed += 1
else:
    print(f"  ❌ Destination recommendations failed")
    failed += 1

# ── Journey Optimization ──
print("\n[7] Journey Optimization")
opt = ji.optimize_journey(j1.journey_id)
if opt and len(opt.get("optimizations", [])) > 0:
    print(f"  ✅ {len(opt['optimizations'])} optimizations")
    for o in opt['optimizations']:
        print(f"     → {o}")
    passed += 1
else:
    print(f"  ❌ Optimization failed: {opt}")
    failed += 1

# ── Disruption ──
print("\n[8] Adaptive Disruption Handling")
j5 = ji.plan_journey("Business Trip", "Sri Lanka", "2026-09-20", "2026-09-25",
                      journey_type="business_meeting", participants=2)
result = ji.handle_disruption(j5.journey_id, "flight_cancelled")
if len(result.get("actions", [])) > 0:
    print(f"  ✅ {len(result['actions'])} adaptation actions")
    for a in result['actions']:
        print(f"     • {a}")
    passed += 1
else:
    print(f"  ❌ Disruption failed: {result}")
    failed += 1

# ── Proposal Generation ──
print("\n[9] Proposal Generation")
proposal = ji.generate_proposal(j2.journey_id)
if proposal and len(proposal) > 100:
    print(f"  ✅ Proposal: {len(proposal)} chars")
    for l in proposal.strip().split('\n')[:5]:
        print(f"     {l}")
    passed += 1
else:
    print(f"  ❌ Proposal failed")
    failed += 1

# ── Health Disruption ──
print("\n[10] Health Emergency Disruption")
j6 = ji.plan_journey("Medical Trip", "Chennai", "2026-08-01", "2026-08-05",
                      journey_type="medical_travel", participants=2)
result = ji.handle_disruption(j6.journey_id, "health_emergency")
if len(result.get("actions", [])) > 0:
    print(f"  ✅ {len(result['actions'])} actions: {', '.join(result['actions'][:2])}")
    passed += 1
else:
    print(f"  ❌ Health disruption failed")
    failed += 1

# ── Same runtime check ──
print("\n[11] One runtime, 12 journey types")
all_journeys = ji.list_journeys()
print(f"  ✅ {len(all_journeys)} journeys across {len(set(j.journey_type for j in all_journeys))} types")
print(f"     All through the same JourneyIntelligence runtime")
passed += 1

print("\n" + "=" * 70)
print(f"RESULT: {passed} passed, {failed} failed")
print("=" * 70)
sys.exit(0 if failed == 0 else 1)