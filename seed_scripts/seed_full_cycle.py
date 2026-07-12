#!/usr/bin/env python3
"""Seed a full-cycle relationship sample — complete lifecycle across 6 years."""
import sys, os
from datetime import datetime, timedelta
sys.path.insert(0, os.path.expanduser("~/shunya_os"))
from app import create_app, db
from app.models import (
    Person, Relationship, RelationshipPreference, Household,
    Opportunity, OpportunityActivity, Experience, Observation, Outcome, LearningCandidate
)

app = create_app('production')

with app.app_context():
    from app.models import Tenant, TeamMember
    tenant = db.session.query(Tenant).first()
    user = db.session.query(TeamMember).filter_by(tenant_id=tenant.id).first()
    if not tenant or not user:
        print("Need tenant + user first")
        sys.exit(1)

    now = datetime.utcnow()

    # =========================================================================
    # FULL CYCLE: Amit Sharma — 6-year relationship, 5 opportunities, 3 experiences
    # =========================================================================

    sharma = Person(
        name="Amit Sharma", email="amit@sharma.co", phone="+91-9876543222",
        birthdate="1980-06-15", nationality="IN", passport="Z1234567",
        preferred_language="en",
    )
    db.session.add(sharma)
    db.session.flush()

    rel = Relationship(
        tenant_id=tenant.id, person_id=sharma.id,
        display_name="Amit Sharma", email=sharma.email, phone=sharma.phone,
        tenure_years=6, health="strong", total_experiences=4, total_referrals=2,
        preferred_channel="whatsapp", communication_style="detailed",
        traveller_graph={
            "self": {"person_id": sharma.id, "name": "Amit Sharma", "birthdate": "1980-06-15"},
            "spouse": {"name": "Neha Sharma", "birthdate": "1983-11-02"},
            "children": [{"name": "Riya Sharma", "birthdate": "2015-03-20"}, {"name": "Arjun Sharma", "birthdate": "2018-07-11"}],
            "parents": [{"name": "Mr. Sharma Sr.", "needs_assistance": True}],
        },
        last_meaningful_interaction=now - timedelta(days=5),
        created_by=user.id,
    )
    db.session.add(rel)
    db.session.flush()

    prefs = [
        RelationshipPreference(tenant_id=tenant.id, relationship_id=rel.id,
            preference_type="hotel_location", value="central_walkable", confidence="high", source="observed",
            evidence=[{"opportunity": "Kerala 2021", "action": "selected Fort Kochi heritage hotel"},
                       {"opportunity": "Europe 2023", "action": "selected city centre hotels in all 4 cities"},
                       {"opportunity": "Dubai 2024", "action": "selected Downtown Dubai hotel"}],
            notes="Strongly prefers walkable central locations across all trip types"),
        RelationshipPreference(tenant_id=tenant.id, relationship_id=rel.id,
            preference_type="travel_pace", value="comfortable", confidence="high", source="observed",
            evidence=[{"opportunity": "Kerala 2021", "action": "removed 2 activities"},
                       {"opportunity": "Europe 2023", "action": "extended Paris stay, dropped Amsterdam"},
                       {"opportunity": "Dubai 2024", "action": "requested 2 activities per day max"}],
            last_confirmed=now - timedelta(days=180)),
        RelationshipPreference(tenant_id=tenant.id, relationship_id=rel.id,
            preference_type="decision_style", value="consults_family", confidence="high", source="observed",
            evidence=[{"opportunity": "Europe 2023", "action": "asked wife before every major decision"},
                       {"opportunity": "Dubai 2024", "action": "took 5 days to decide after discussing with kids"}],
            last_confirmed=now - timedelta(days=180)),
        RelationshipPreference(tenant_id=tenant.id, relationship_id=rel.id,
            preference_type="transfer_preference", value="private_transfer", confidence="high", source="stated",
            evidence=[{"opportunity": "Dubai 2024", "action": "explicitly requested private transfer — 'with kids, not shared' "}],
            last_confirmed=now - timedelta(days=365)),
        RelationshipPreference(tenant_id=tenant.id, relationship_id=rel.id,
            preference_type="budget_range", value="premium_mid", confidence="medium", source="observed",
            evidence=[{"opportunity": "Europe 2023", "action": "selected 4-star hotels, not luxury"},
                       {"opportunity": "Dubai 2024", "action": "said 'good value over flashy' "}],
            contradictions=[{"opportunity": "Kerala 2021", "note": "selected boutique heritage (higher per night)"}]),
        RelationshipPreference(tenant_id=tenant.id, relationship_id=rel.id,
            preference_type="airline", value="prefers_direct", confidence="medium", source="inferred",
            evidence=[{"opportunity": "Europe 2023", "action": "chose Air India direct over cheaper transit"},
                       {"opportunity": "Dubai 2024", "action": "chose direct flight — 'kids get restless' "}],
            notes="Prioritizes direct flights over cost savings with children"),
    ]
    for p in prefs:
        db.session.add(p)
    db.session.flush()

    # =========================================================================
    # OPPORTUNITY 1: Kerala 2021 — COMPLETED (success)
    # =========================================================================
    opp1 = Opportunity(tenant_id=tenant.id, relationship_id=rel.id, code="OPP-SH-001",
        title="Kerala Family Holiday", destination="Kerala",
        stage="closed", status="won", experience_mood="relaxing + nature",
        estimated_budget=120000, actual_cost=135000, traveller_count=3,
        participants=[{"role": "traveller", "name": "Amit"}, {"role": "traveller", "name": "Neha"}, {"role": "traveller", "name": "Riya"}],
        decision_maker="Amit Sharma", priority="high", probability=100, risk="low",
        enquiry_date=now - timedelta(days=1800), booking_date=now - timedelta(days=1760),
        experience_start=now - timedelta(days=1730), experience_end=now - timedelta(days=1723),
        closed_at=now - timedelta(days=1700), created_by=user.id)
    db.session.add(opp1)
    db.session.flush()
    for a in [
        dict(activity_type="enquiry", title="Enquiry: Kerala family trip"),
        dict(activity_type="decision", title="Confirmed: Kerala"),
        dict(activity_type="quote_sent", title="Proposal sent"),
        dict(activity_type="stage_change", title="Booking confirmed"),
        dict(activity_type="feedback", title="Post-trip: 5/5"),
    ]:
        db.session.add(OpportunityActivity(tenant_id=tenant.id, opportunity_id=opp1.id, created_by=user.id, **a))

    exp1 = Experience(tenant_id=tenant.id, relationship_id=rel.id, opportunity_id=opp1.id,
        title="Kerala Family Holiday", experience_type="trip",
        expectations={"hotels": "Fort Kochi + Munnar Resort", "flights": "Direct Kochi", "transfers": "Private car + driver"},
        delivered_reality={"hotels": "Boutique hotel (heritage upgrade)", "flights": "On time", "transfers": "Private car — driver Babu was excellent"},
        events=[{"date": "2021-06-10", "type": "checkin", "status": "smooth", "detail": "Heritage upgrade welcome"},
                {"date": "2021-06-12", "type": "activity", "status": "smooth", "detail": "Houseboat day — kids loved it"}],
        exceptions=[], feedback="Absolutely wonderful. Kids still talk about the houseboat.",
        satisfaction_signals=[{"source": "survey", "metric": "overall", "score": 5},
                              {"source": "message", "text": "best family trip ever", "sentiment": "positive"}],
        overall_rating=5, would_recommend=True,
        start_date=now - timedelta(days=1730), end_date=now - timedelta(days=1723), created_by=user.id)
    db.session.add(exp1)
    db.session.flush()
    db.session.add(Outcome(tenant_id=tenant.id, subject_type="experience", subject_id=exp1.id, experience_id=exp1.id,
        goal="First post-lockdown family trip", expected_outcome="Peaceful family holiday",
        actual_outcome="Exceeded expectations", result="success",
        lessons=[{"lesson": "Heritage properties + kids = great combination", "category": "product", "priority": "medium"}]))

    # =========================================================================
    # OPPORTUNITY 2: Europe 2023 — COMPLETED (partial — return delay)
    # =========================================================================
    opp2 = Opportunity(tenant_id=tenant.id, relationship_id=rel.id, code="OPP-SH-002",
        title="Europe Discovery — Paris + Switzerland", destination="Paris + Switzerland",
        stage="closed", status="won", experience_mood="cultural + nature",
        estimated_budget=450000, actual_cost=520000, traveller_count=4,
        participants=[{"role": "traveller", "name": "Amit"}, {"role": "traveller", "name": "Neha"},
                       {"role": "traveller", "name": "Riya"}, {"role": "traveller", "name": "Arjun"}],
        decision_maker="Amit (consults Neha)", priority="high", probability=100, risk="medium",
        decisions=[{"type": "destination", "decision": "Paris + Switzerland only", "reason": "Dropped Amsterdam — too rushed"}],
        enquiry_date=now - timedelta(days=900), booking_date=now - timedelta(days=860),
        experience_start=now - timedelta(days=820), experience_end=now - timedelta(days=808),
        closed_at=now - timedelta(days=790), created_by=user.id)
    db.session.add(opp2)
    db.session.flush()
    for a in [
        dict(activity_type="enquiry", title="Enquiry: first Europe trip"),
        dict(activity_type="decision", title="Dropped Amsterdam — customer self-corrected"),
        dict(activity_type="quote_sent", title="Itinerary shared — 12 nights"),
        dict(activity_type="stage_change", title="Booking confirmed"),
        dict(activity_type="feedback", title="Post-trip: 4/5 — return delay was hard"),
    ]:
        db.session.add(OpportunityActivity(tenant_id=tenant.id, opportunity_id=opp2.id, created_by=user.id, **a))

    exp2 = Experience(tenant_id=tenant.id, relationship_id=rel.id, opportunity_id=opp2.id,
        title="Europe 2023 — Paris + Switzerland", experience_type="trip",
        expectations={"hotels": "City centre 4-star", "flights": "Air India direct DEL-CDG", "trains": "TGV Paris-Geneva"},
        delivered_reality={"hotels": "City centre — all confirmed", "flights": "DEL-CDG on time. CDG-DEL delayed 4hr",
                          "trains": "TGV highlight for kids"},
        events=[{"date": "2023-06-15", "type": "checkin", "status": "smooth"},
                {"date": "2023-06-22", "type": "checkin", "status": "smooth", "detail": "Interlaken view stunning"},
                {"date": "2023-06-25", "type": "flight", "status": "issue", "detail": "Return delayed 4hr — kids exhausted"}],
        exceptions=[{"component": "return_flight", "issue": "4hr delay at CDG", "severity": "major",
                      "detail": "Air India CDG-DEL delayed 4hr. No lounge access. Family stranded at gate.",
                      "recovery": "Compensated with voucher + apology"}],
        recovery_actions=[{"action": "compensation voucher", "status": "accepted"}],
        feedback="Trip was beautiful but return delay was really hard with the kids.",
        satisfaction_signals=[{"source": "survey", "metric": "overall", "score": 4},
                               {"source": "survey", "metric": "itinerary", "score": 5},
                               {"source": "message", "text": "return delay was really difficult", "sentiment": "negative"}],
        overall_rating=4, would_recommend=True,
        start_date=now - timedelta(days=820), end_date=now - timedelta(days=808), created_by=user.id)
    db.session.add(exp2)
    db.session.flush()
    db.session.add(Outcome(tenant_id=tenant.id, subject_type="experience", subject_id=exp2.id, experience_id=exp2.id,
        goal="First international family trip", expected_outcome="Magical first Europe experience",
        actual_outcome="Trip content magical. Return delay impacted end experience.", result="partial",
        reason="Return flight delay (Air India) — outside Panchi control",
        customer_impact="Family exhausted. Customer noted 'would have paid extra for better airline'",
        lessons=[{"lesson": "For families with young children, recommend airlines with better delay handling", "category": "product", "priority": "high"},
                 {"lesson": "Pre-book lounge access for families on long-haul returns", "category": "ops", "priority": "high"}]))

    # =========================================================================
    # OPPORTUNITY 3: Dubai 2024 — COMPLETED (success)
    # =========================================================================
    opp3 = Opportunity(tenant_id=tenant.id, relationship_id=rel.id, code="OPP-SH-003",
        title="Dubai Family Holiday", destination="Dubai",
        stage="closed", status="won", experience_mood="relaxing + fun",
        estimated_budget=280000, actual_cost=295000, traveller_count=4,
        participants=[{"role": "traveller", "name": "Amit"}, {"role": "traveller", "name": "Neha"},
                       {"role": "traveller", "name": "Riya"}, {"role": "traveller", "name": "Arjun"}],
        decision_maker="Amit (consults family)", priority="high", probability=100, risk="low",
        decisions=[{"type": "hotel", "decision": "Downtown Dubai — walkable to Mall"},
                    {"type": "activity", "decision": "2 activities max per day"}],
        quotes=[{"version": 1, "total": 295000, "status": "accepted"}],
        bookings=[{"supplier": "Emirates", "item": "flights", "amount": 120000, "status": "confirmed"},
                   {"supplier": "JW Marriott", "item": "hotel", "amount": 135000, "status": "confirmed"}],
        enquiry_date=now - timedelta(days=400), booking_date=now - timedelta(days=370),
        experience_start=now - timedelta(days=350), experience_end=now - timedelta(days=345),
        closed_at=now - timedelta(days=330), created_by=user.id)
    db.session.add(opp3)
    db.session.flush()
    for a in [
        dict(activity_type="enquiry", title="Enquiry: quick Dubai getaway"),
        dict(activity_type="decision", title="Hotel: Downtown Dubai"),
        dict(activity_type="quote_sent", title="Quote sent — 295k all-in"),
        dict(activity_type="stage_change", title="Booking confirmed — Emirates + JW Marriott"),
        dict(activity_type="note", title="Customer noted: 'learned from Europe — keeping it simple'"),
        dict(activity_type="feedback", title="Post-trip: 5/5 glowing"),
    ]:
        db.session.add(OpportunityActivity(tenant_id=tenant.id, opportunity_id=opp3.id, created_by=user.id, **a))

    exp3 = Experience(tenant_id=tenant.id, relationship_id=rel.id, opportunity_id=opp3.id,
        title="Dubai 2024 — Family Getaway", experience_type="trip",
        expectations={"hotels": "JW Marriott Downtown", "flights": "Emirates direct", "transfers": "Private"},
        delivered_reality={"hotels": "JW Marriott (fountain view upgrade)", "flights": "On time both ways",
                          "transfers": "Smooth — driver waiting, luxury car, kids excited"},
        events=[{"date": "2024-03-10", "type": "transfer", "status": "smooth"},
                {"date": "2024-03-11", "type": "activity", "status": "smooth", "detail": "Aquaventure"},
                {"date": "2024-03-14", "type": "checkout", "status": "smooth"}],
        exceptions=[], feedback="Perfect trip. Everything was smooth. Kids already asking when we go back.",
        satisfaction_signals=[{"source": "survey", "metric": "overall", "score": 5},
                               {"source": "survey", "metric": "transfers", "score": 5},
                               {"source": "message", "text": "best trip ever", "sentiment": "positive"}],
        overall_rating=5, would_recommend=True,
        start_date=now - timedelta(days=350), end_date=now - timedelta(days=345), created_by=user.id)
    db.session.add(exp3)
    db.session.flush()
    db.session.add(Outcome(tenant_id=tenant.id, subject_type="experience", subject_id=exp3.id, experience_id=exp3.id,
        goal="Quick, smooth family getaway", expected_outcome="Relaxing Dubai trip",
        actual_outcome="Near-perfect. Customer called it 'best trip ever'", result="success",
        lessons=[{"lesson": "Private transfer for family arrivals = outsized positive impact", "category": "product", "priority": "medium"},
                 {"lesson": "Dubai works well for this family profile", "category": "sales", "priority": "low"}]))

    # =========================================================================
    # OPPORTUNITY 4: Parents' Pilgrimage (COMPLETED)
    # =========================================================================
    opp4 = Opportunity(tenant_id=tenant.id, relationship_id=rel.id, code="OPP-SH-004",
        title="Parents' Pilgrimage — Haridwar", destination="Haridwar-Rishikesh",
        stage="closed", status="won", experience_mood="spiritual + comfortable",
        estimated_budget=65000, actual_cost=72000, traveller_count=2,
        participants=[{"role": "beneficiary", "name": "Mr. Sharma Sr."}, {"role": "beneficiary", "name": "Mrs. Sharma Sr."}],
        decision_maker="Amit (for parents)", referrer="Amit Sharma",
        enquiry_date=now - timedelta(days=200), booking_date=now - timedelta(days=185),
        experience_start=now - timedelta(days=160), experience_end=now - timedelta(days=157),
        closed_at=now - timedelta(days=140), created_by=user.id)
    db.session.add(opp4)
    db.session.flush()
    for a in [
        dict(activity_type="enquiry", title="Amit enquired for parents"),
        dict(activity_type="stage_change", title="Booking confirmed"),
        dict(activity_type="feedback", title="Parents very happy"),
    ]:
        db.session.add(OpportunityActivity(tenant_id=tenant.id, opportunity_id=opp4.id, created_by=user.id, **a))

    # =========================================================================
    # OPPORTUNITY 5: ACTIVE — Nepal 2026
    # =========================================================================
    opp5 = Opportunity(tenant_id=tenant.id, relationship_id=rel.id, code="OPP-SH-005",
        title="Nepal Family Adventure", destination="Kathmandu + Pokhara",
        stage="proposal", status="open", experience_mood="adventure + cultural",
        estimated_budget=350000, traveller_count=4,
        participants=[{"role": "traveller", "name": "Amit"}, {"role": "traveller", "name": "Neha"},
                       {"role": "traveller", "name": "Riya"}, {"role": "traveller", "name": "Arjun"}],
        decision_maker="Amit (family consensus)", priority="high", probability=70, risk="low",
        decisions=[{"type": "destination", "decision": "Nepal over Bhutan", "reason": "Shorter flights, better value, light trekking"}],
        quotes=[{"version": 1, "total": 350000, "status": "sent"}],
        enquiry_date=now - timedelta(days=14), created_by=user.id)
    db.session.add(opp5)
    db.session.flush()
    for a in [
        dict(activity_type="enquiry", title="Enquiry: Nepal family adventure"),
        dict(activity_type="decision", title="Destination: Nepal over Bhutan"),
        dict(activity_type="quote_sent", title="Itinerary + quote shared — 350k"),
        dict(activity_type="note", title="Customer reviewing with family — expects decision this week"),
    ]:
        db.session.add(OpportunityActivity(tenant_id=tenant.id, opportunity_id=opp5.id, created_by=user.id, **a))

    # =========================================================================
    # OBSERVATIONS
    # =========================================================================
    db.session.add(Observation(tenant_id=tenant.id, subject_type="experience", subject_id=exp2.id,
        event="itinerary_pacing_feedback", source="human", observer="advisor",
        expected_state="Original 3-city itinerary would work",
        actual_state="Customer dropped Amsterdam — 'too rushed with kids'",
        delta="Customer self-corrected before booking", severity="info", confidence="high",
        metadata_json={"pattern": "Amit prefers 2 destinations max with children"}))

    db.session.add(Observation(tenant_id=tenant.id, subject_type="experience", subject_id=exp2.id,
        event="return_flight_delay", source="system", observer="post_trip_review",
        expected_state="On-time return, satisfied end to trip",
        actual_state="4-hour delay, no lounge, exhausted children",
        delta="Critical gap — return experience undone trip goodwill",
        severity="major", confidence="high"))

    db.session.add(Observation(tenant_id=tenant.id, subject_type="relationship", subject_id=rel.id,
        event="referral_made", source="human", observer="system",
        expected_state="Satisfied customer",
        actual_state="Referred 2 families — both converted",
        delta="High-value repeat referral pattern", severity="info", confidence="high",
        metadata_json={"referrals": [{"name": "Sharma Family", "trip": "Manali 2024", "status": "converted"},
                                      {"name": "Verma Family", "trip": "Goa 2025", "status": "converted"}],
                        "pattern": "Amit refers within 3 months of a successful trip"}))

    # =========================================================================
    # LEARNING CANDIDATES
    # =========================================================================
    db.session.add(LearningCandidate(tenant_id=tenant.id,
        pattern="Families with children under 12 on long-haul returns show lower satisfaction when delayed without lounge access",
        evidence=[{"experience": "Europe 2023", "observation": "4hr return delay, no lounge, rating dropped from 5 to 4"}],
        confidence=0.75, category="pattern",
        proposed_knowledge="Pre-book lounge access for family long-haul packages",
        proposed_rule="Lounge access included in all family long-haul packages",
        status="candidate"))

    db.session.add(LearningCandidate(tenant_id=tenant.id,
        pattern="Amit Sharma self-corrects itinerary pacing — advisor should offer 2-option pacing early",
        evidence=[{"opportunity": "Europe 2023", "observation": "Customer dropped Amsterdam"},
                   {"opportunity": "Dubai 2024", "observation": "Customer requested 2 activities max"}],
        confidence=0.85, category="customer_insight",
        proposed_workflow_change="Discovery call should include pacing preference as structured question",
        status="candidate"))

    # =========================================================================
    # COMMIT
    # =========================================================================
    db.session.commit()

    # =========================================================================
    # GENERATE ADVISORY BRIEF
    # =========================================================================
    from app.shunya.advisory import AdvisoryContext
    brief = AdvisoryContext.for_relationship(rel.id)

    print("=" * 72)
    print("✅ FULL CYCLE SAMPLE — AMIT SHARMA")
    print(f"   Relationship: {rel.tenure_years}yr · {rel.health} · {rel.total_experiences} experiences")
    print(f"   Preferences: {len(prefs)} · Observations: 3 · Learning Candidates: 2")
    print(f"   Opportunities: 5 (4 completed · 1 active at proposal)")
    print(f"   Experiences: 3 (Kerala ✅, Europe ⚠️, Dubai ✅)")
    print("=" * 72)
    print()
    print("ADVISORY BRIEF:")
    print(f"  Name:     {brief['header']['name']}")
    print(f"  Tenure:   {brief['header']['tenure_years']}yr · {brief['header']['health_label']}")
    print(f"  Channel:  {brief['header']['preferred_channel'].title()} ({brief['header']['communication_style']})")
    print()
    print("  BEFORE YOU SPEAK:")
    for b in brief['before_you_speak']:
        print(f"    • {b}")
    print()
    print(f"  ⚠️  ONE THING: {brief.get('one_thing_to_remember', 'N/A')}")
    print()
    sa = brief.get('suggested_next_action') or {}
    print(f"  🎯 NEXT ACTION: {sa.get('action', 'N/A')}")
    if sa.get('suggested_opening'):
        opening = sa['suggested_opening']
        print(f'     Opening: "{opening}"')
    print()
    print("  LIFETIME JOURNEY:")
    for j in brief.get('lifetime_journey', []):
        line = f"    {j['icon']} {j['title']}"
        if j.get('year'): line += f" ({j['year']})"
        if j.get('experience_rating'): line += f" {'⭐' * j['experience_rating']} {j['experience_rating']}/5"
        if j.get('experience_issues'): line += f" ⚠️"
        print(line)
    print()
    print("  ACTIVE OPPORTUNITY:")
    for o in brief.get('active_opportunities', []):
        budget = f" ₹{o['estimated_budget']:,.0f}" if o.get('estimated_budget') else ""
        print(f"    💎 {o['title']} · {o['stage']} · {o.get('probability', 'N/A')}%{budget}")
    print()
    print("  PREFERENCES:")
    for p in brief.get('preferences_detail', []):
        print(f"    {p['preference_type']}: {p['value']} ({p['confidence']}, {len(p.get('evidence',[]))} evidence)")