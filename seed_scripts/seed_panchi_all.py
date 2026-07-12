#!/usr/bin/env python3
"""Seed ALL Shunya OS modules with realistic Panchi Club (travel agency) sample data.

Run:
    cd ~/shunya_os && python3 seed_scripts/seed_panchi_all.py

What this seeds:
    1. RELATIONSHIPS — Amit Sharma (full 6yr lifecycle) if not already present
    2. HR — 3 departments, 8 employees, leaves, attendance, reviews
    3. MARKETING — campaigns, email campaigns, social posts, landing pages, analytics reports
    4. SUPPORT — tickets, knowledge articles, FAQs, feedback, SLA policies
    5. SUPPLY CHAIN — suppliers, products, purchase orders, warehouses
    6. FIELD SERVICES — subcontractors (guides/drivers), work orders, estimates
    7. LEGAL — contracts, document templates, compliance items
    8. SALES CRM — leads, accounts, contacts, opportunities, quotes, target lists
    9. FINANCE — invoices and payments (entity + direct models)
"""

import sys, os
sys.path.insert(0, os.path.expanduser("~/shunya_os"))
from datetime import datetime, timedelta, date

from app import create_app, db
from app.models import (
    Tenant, TeamMember, EntityDefinition, Entity,
    Person, Relationship, RelationshipPreference, Household,
    Opportunity, OpportunityActivity, Experience, Observation, Outcome, LearningCandidate,
    Payment, Invoice, Supplier,
)

app = create_app("production")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _now():
    return datetime.utcnow()


def _today():
    return date.today()


def _def(tenant_id, etype):
    """Get EntityDefinition by type, or None."""
    return db.session.query(EntityDefinition).filter_by(
        tenant_id=tenant_id, type=etype
    ).first()


def _get_or_create_def(tenant_id, etype, config):
    """Get existing or create new EntityDefinition from config dict."""
    existing = _def(tenant_id, etype)
    if existing:
        return existing
    definition = EntityDefinition(
        tenant_id=tenant_id,
        type=etype,
        label=config["label"],
        label_plural=config.get("label_plural", f"{config['label']}s"),
        icon=config.get("icon", "📋"),
        schema=config.get("schema", []),
        statuses=config.get("statuses", []),
        layout=config.get("layout", "table"),
        searchable_fields=config.get("searchable_fields", []),
        primary_field=config["schema"][0]["name"] if config.get("schema") else "name",
    )
    db.session.add(definition)
    db.session.flush()
    return definition


def _make_entity(tenant_id, etype, code, status, data, user_id=None):
    """Create and flush an Entity record."""
    edef = _def(tenant_id, etype)
    if not edef:
        print(f"  ⚠️  EntityDefinition '{etype}' not found — skipping")
        return None
    ent = Entity(
        tenant_id=tenant_id,
        definition_id=edef.id,
        code=code,
        status=status,
        data=data,
        created_by=user_id,
    )
    db.session.add(ent)
    db.session.flush()
    return ent


# ---------------------------------------------------------------------------
# Seeding functions
# ---------------------------------------------------------------------------

def seed_relationships(tenant, user):
    """Seed Amit Sharma full cycle — same logic as seed_full_cycle.py, skipped if exists."""
    existing = db.session.query(Person).filter_by(email="amit@sharma.co").first()
    if existing:
        print("    Amit Sharma already seeded — skipping RELATIONSHIPS")
        return

    now = _now()
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
            "children": [
                {"name": "Riya Sharma", "birthdate": "2015-03-20"},
                {"name": "Arjun Sharma", "birthdate": "2018-07-11"},
            ],
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
                      {"opportunity": "Dubai 2024", "action": "selected Downtown Dubai hotel"}]),
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
            evidence=[{"opportunity": "Dubai 2024", "action": "explicitly requested private transfer"}],
            last_confirmed=now - timedelta(days=365)),
        RelationshipPreference(tenant_id=tenant.id, relationship_id=rel.id,
            preference_type="budget_range", value="premium_mid", confidence="medium", source="observed",
            evidence=[{"opportunity": "Europe 2023", "action": "selected 4-star hotels, not luxury"},
                      {"opportunity": "Dubai 2024", "action": "said 'good value over flashy'"}],
            contradictions=[{"opportunity": "Kerala 2021", "note": "selected boutique heritage (higher per night)"}]),
        RelationshipPreference(tenant_id=tenant.id, relationship_id=rel.id,
            preference_type="airline", value="prefers_direct", confidence="medium", source="inferred",
            evidence=[{"opportunity": "Europe 2023", "action": "chose Air India direct over cheaper transit"},
                      {"opportunity": "Dubai 2024", "action": "chose direct flight — 'kids get restless'"}],
            notes="Prioritizes direct flights over cost savings with children"),
    ]
    for p in prefs:
        db.session.add(p)
    db.session.flush()

    # --- OPPORTUNITIES ---
    opp1 = Opportunity(tenant_id=tenant.id, relationship_id=rel.id, code="OPP-SH-001",
        title="Kerala Family Holiday", destination="Kerala",
        stage="closed", status="won", experience_mood="relaxing + nature",
        estimated_budget=120000, actual_cost=135000, traveller_count=3,
        participants=[{"role": "traveller", "name": "Amit"}, {"role": "traveller", "name": "Neha"},
                      {"role": "traveller", "name": "Riya"}],
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
        delivered_reality={"hotels": "Boutique hotel (heritage upgrade)", "flights": "On time",
                          "transfers": "Private car — driver Babu was excellent"},
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

    db.session.commit()
    print("    ✅ RELATIONSHIPS — Amit Sharma seeded (6yr, 5 opportunities, 3 experiences)")


def seed_hr(tenant, user):
    """Seed HR module: departments, employees, leaves, attendance, reviews, positions."""
    from app.shunya.hr import HR_ENTITY_TYPES
    for etype, config in HR_ENTITY_TYPES.items():
        _get_or_create_def(tenant.id, etype, config)
    db.session.commit()

    now = _now()

    # --- Departments ---
    dept_sales = _make_entity(tenant.id, "department", "DEPT-SALES", "active", {
        "name": "Sales & Advisory", "code": "SALES",
        "description": "Handles travel sales, customer advisory, and itinerary planning",
        "budget": 5000000, "location": "Delhi HQ",
    }, user.id)
    dept_ops = _make_entity(tenant.id, "department", "DEPT-OPS", "active", {
        "name": "Travel Operations", "code": "OPS",
        "description": "Manages bookings, logistics, vendor coordination, and on-ground execution",
        "budget": 3500000, "location": "Mumbai Operations",
    }, user.id)
    dept_fin = _make_entity(tenant.id, "department", "DEPT-FIN", "active", {
        "name": "Finance & Admin", "code": "FINADMIN",
        "description": "Accounting, payments, HR administration, and office management",
        "budget": 2000000, "location": "Delhi HQ",
    }, user.id)

    # --- Positions ---
    positions = [
        dict(title="Senior Sales Advisor", department="Sales & Advisory", reports_to="CEO",
             salary_range_min=600000, salary_range_max=900000, head_count=1, filled_positions=1,
             job_description="Lead travel advisor handling high-value clients and corporate accounts"),
        dict(title="Sales Advisor", department="Sales & Advisory", reports_to="Senior Sales Advisor",
             salary_range_min=350000, salary_range_max=550000, head_count=2, filled_positions=2,
             job_description="Assist clients with travel planning and package selection"),
        dict(title="Operations Manager", department="Travel Operations", reports_to="CEO",
             salary_range_min=700000, salary_range_max=1000000, head_count=1, filled_positions=1,
             job_description="Oversee all travel operations, vendor management, and logistics"),
        dict(title="Operations Executive", department="Travel Operations", reports_to="Operations Manager",
             salary_range_min=300000, salary_range_max=450000, head_count=1, filled_positions=1,
             job_description="Coordinate bookings, visas, and travel documentation"),
        dict(title="Finance Manager", department="Finance & Admin", reports_to="CEO",
             salary_range_min=500000, salary_range_max=750000, head_count=1, filled_positions=1,
             job_description="Manage accounting, invoicing, payroll, and financial reporting"),
        dict(title="Admin Executive", department="Finance & Admin", reports_to="Finance Manager",
             salary_range_min=250000, salary_range_max=350000, head_count=1, filled_positions=1,
             job_description="Office administration, records management, and support"),
        dict(title="Marketing Executive", department="Sales & Advisory", reports_to="Senior Sales Advisor",
             salary_range_min=300000, salary_range_max=500000, head_count=1, filled_positions=1,
             job_description="Digital marketing, social media, and campaign management"),
        dict(title="Junior Travel Advisor", department="Sales & Advisory", reports_to="Senior Sales Advisor",
             salary_range_min=250000, salary_range_max=400000, head_count=1, filled_positions=1,
             job_description="Support senior advisors with research, quotes, and client follow-ups"),
    ]
    for p in positions:
        _make_entity(tenant.id, "position", f"POS-{p['title'][:4].upper()}", "active", p, user.id)

    # --- Employees ---
    employees = [
        dict(employee_name="Mitesh Yadav", employee_code="EMP001", email="mitesh@panchi.club",
             phone="+91-9876543001", department="Sales & Advisory", position="Senior Sales Advisor",
             date_of_joining="2019-06-01", date_of_birth="1988-03-15",
             employment_type="full_time", work_location="Delhi HQ", salary=850000,
             bank_account="HDFC12345678901", emergency_contact="+91-9876543099 (Spouse)",
             skills="Travel consulting, itinerary design, client relationship management, Hindi/English",
             notes="Top performer 2024 — closed ₹85L in bookings"),
        dict(employee_name="Chaya Devi", employee_code="EMP002", email="chaya@panchi.club",
             phone="+91-9876543002", department="Travel Operations", position="Operations Manager",
             date_of_joining="2020-01-15", date_of_birth="1985-07-22",
             employment_type="full_time", work_location="Mumbai Operations", salary=950000,
             bank_account="ICICI98765432101", emergency_contact="+91-9876543098 (Brother)",
             skills="Operations management, vendor negotiation, logistics, crisis management",
             notes="Managed 200+ group tours successfully"),
        dict(employee_name="Priya Sharma", employee_code="EMP003", email="priya@panchi.club",
             phone="+91-9876543003", department="Finance & Admin", position="Finance Manager",
             date_of_joining="2020-03-01", date_of_birth="1990-11-08",
             employment_type="full_time", work_location="Delhi HQ", salary=700000,
             bank_account="SBI11111111101", emergency_contact="+91-9876543097 (Father)",
             skills="Accounting, Tally, GST compliance, payroll management",
             notes="Chartered Accountant with 6 years experience"),
        dict(employee_name="Vikram Singh", employee_code="EMP004", email="vikram@panchi.club",
             phone="+91-9876543004", department="Sales & Advisory", position="Sales Advisor",
             date_of_joining="2021-06-15", date_of_birth="1992-09-30",
             employment_type="full_time", work_location="Delhi HQ", salary=500000,
             bank_account="AXIS22222222201", emergency_contact="+91-9876543096 (Mother)",
             skills="Sales, lead conversion, destination knowledge, customer service",
             notes="Strong performer — converted 45 leads last year"),
        dict(employee_name="Ananya Kapoor", employee_code="EMP005", email="ananya@panchi.club",
             phone="+91-9876543005", department="Sales & Advisory", position="Junior Travel Advisor",
             date_of_joining="2023-09-01", date_of_birth="1998-04-12",
             employment_type="probation", work_location="Delhi HQ", salary=300000,
             bank_account="HDFC33333333301", emergency_contact="+91-9876543095 (Father)",
             skills="Research, itinerary drafting, client communication",
             notes="Recent hire — completing training program"),
        dict(employee_name="Rajesh Kumar", employee_code="EMP006", email="rajesh@panchi.club",
             phone="+91-9876543006", department="Finance & Admin", position="Admin Executive",
             date_of_joining="2021-01-10", date_of_birth="1991-12-05",
             employment_type="full_time", work_location="Delhi HQ", salary=320000,
             bank_account="PNB44444444401", emergency_contact="+91-9876543094 (Spouse)",
             skills="Office management, document handling, vendor coordination",
             notes="Manages office supplies and travel documentation"),
        dict(employee_name="Sneha Roy", employee_code="EMP007", email="sneha@panchi.club",
             phone="+91-9876543007", department="Sales & Advisory", position="Marketing Executive",
             date_of_joining="2022-02-20", date_of_birth="1994-08-18",
             employment_type="full_time", work_location="Delhi HQ", salary=420000,
             bank_account="ICICI55555555501", emergency_contact="+91-9876543093 (Mother)",
             skills="Digital marketing, social media management, content creation, SEO",
             notes="Grew social following by 300% in 2024"),
        dict(employee_name="Arjun Nair", employee_code="EMP008", email="arjun@panchi.club",
             phone="+91-9876543008", department="Travel Operations", position="Operations Executive",
             date_of_joining="2022-08-01", date_of_birth="1995-05-27",
             employment_type="full_time", work_location="Mumbai Operations", salary=380000,
             bank_account="SBI66666666601", emergency_contact="+91-9876543092 (Spouse)",
             skills="Booking systems, visa processing, itinerary operations",
             notes="Handled 150+ visa applications last year with 100% success rate"),
    ]
    emp_entities = []
    for emp in employees:
        e = _make_entity(tenant.id, "employee", emp["employee_code"], "active", emp, user.id)
        if e:
            emp_entities.append(e)

    # --- Leave Requests ---
    leaves = [
        dict(employee_id=emp_entities[0].id, employee_name="Mitesh Yadav",
             leave_type="annual", start_date=str(_today() - timedelta(days=45)), end_date=str(_today() - timedelta(days=40)),
             total_days=6, reason="Family wedding in Jaipur", approved_by=user.id,
             approval_notes="Approved — coverage arranged with Vikram"),
        dict(employee_id=emp_entities[1].id, employee_name="Chaya Devi",
             leave_type="sick", start_date=str(_today() - timedelta(days=10)), end_date=str(_today() - timedelta(days=8)),
             total_days=3, reason="Viral fever", approved_by=user.id,
             approval_notes="Approved — rest recommended"),
        dict(employee_id=emp_entities[3].id, employee_name="Vikram Singh",
             leave_type="personal", start_date=str(_today() + timedelta(days=14)), end_date=str(_today() + timedelta(days=15)),
             total_days=2, reason="Personal errand"),
        dict(employee_id=emp_entities[4].id, employee_name="Ananya Kapoor",
             leave_type="annual", start_date=str(_today() + timedelta(days=30)), end_date=str(_today() + timedelta(days=33)),
             total_days=4, reason="Trip to Goa with friends"),
        dict(employee_id=emp_entities[6].id, employee_name="Sneha Roy",
             leave_type="sick", start_date=str(_today() - timedelta(days=20)), end_date=str(_today() - timedelta(days=19)),
             total_days=2, reason="Migraine", approved_by=user.id,
             approval_notes="Approved"),
        dict(employee_id=emp_entities[5].id, employee_name="Rajesh Kumar",
             leave_type="unpaid", start_date=str(_today() - timedelta(days=90)), end_date=str(_today() - timedelta(days=85)),
             total_days=6, reason="Emergency at home town", approved_by=user.id,
             approval_notes="Approved as unpaid — policy applied"),
        dict(employee_id=emp_entities[2].id, employee_name="Priya Sharma",
             leave_type="annual", start_date=str(_today() + timedelta(days=60)), end_date=str(_today() + timedelta(days=65)),
             total_days=6, reason="International trip to Singapore"),
    ]
    for i, lv in enumerate(leaves):
        status = "approved" if lv.get("approved_by") else "pending"
        _make_entity(tenant.id, "leave_request", f"LEAVE{100+i}", status, lv, user.id)

    # --- Attendance (last 30 days for each employee) ---
    for emp in emp_entities:
        emp_name = emp.data.get("employee_name", "Unknown")
        for day_offset in range(30):
            att_date = _today() - timedelta(days=29 - day_offset)
            # Skip weekends for simplicity
            if att_date.weekday() >= 5:
                continue
            # Skip the ones on leave
            is_on_leave = False
            for lv in leaves:
                if emp.data.get("employee_code") and lv["employee_name"] == emp_name:
                    try:
                        sd = date.fromisoformat(lv["start_date"])
                        ed = date.fromisoformat(lv["end_date"])
                        if sd <= att_date <= ed:
                            is_on_leave = True
                            break
                    except (ValueError, KeyError):
                        pass
            if is_on_leave:
                continue
            # Random-ish attendance pattern
            import random
            r = random.Random(f"{emp_name}_{att_date}")
            if r.random() < 0.85:
                status = "present"
                check_in = f"09:{r.randint(0,30):02d}"
                check_out = f"18:{r.randint(0,45):02d}"
                late_mins = max(0, r.randint(0, 20))
                ot_hrs = r.randint(0, 2) if r.random() < 0.3 else 0
            elif r.random() < 0.4:
                status = "late"
                check_in = f"09:{r.randint(31,59):02d}"
                check_out = f"18:{r.randint(0,30):02d}"
                late_mins = r.randint(15, 60)
                ot_hrs = 0
            elif r.random() < 0.5:
                status = "wfh"
                check_in = "08:00"
                check_out = "17:00"
                late_mins = 0
                ot_hrs = 0
            else:
                status = "absent"
                check_in = ""
                check_out = ""
                late_mins = 0
                ot_hrs = 0
            total_hrs = 0
            if check_in and check_out:
                try:
                    hi, mi = map(int, check_in.split(":"))
                    ho, mo = map(int, check_out.split(":"))
                    total_hrs = (ho * 60 + mo - hi * 60 - mi) / 60
                except ValueError:
                    total_hrs = 0
            _make_entity(tenant.id, "attendance", f"ATT{emp.id}_{att_date.strftime('%d%m%y')}",
                         status, {
                             "employee_id": emp.id,
                             "employee_name": emp_name,
                             "date": str(att_date),
                             "check_in": check_in,
                             "check_out": check_out,
                             "total_hours": round(total_hrs, 1),
                             "late_minutes": late_mins,
                             "overtime_hours": ot_hrs,
                         }, user.id)

    # --- Performance Reviews ---
    reviews = [
        dict(employee_id=emp_entities[0].id, employee_name="Mitesh Yadav",
             review_period="H2 2025", reviewer_id=user.id, reviewer_name="Admin",
             rating="5", technical_skills=5, communication=4, teamwork=4, leadership=4,
             achievements="Closed ₹85L in bookings. Won 'Best Travel Advisor' award.",
             areas_for_improvement="Delegation — tends to hold too much personally",
             goals_next_period="Mentor 2 junior advisors. Target ₹1Cr bookings.",
             review_date=str(_today() - timedelta(days=60))),
        dict(employee_id=emp_entities[1].id, employee_name="Chaya Devi",
             review_period="H2 2025", reviewer_id=user.id, reviewer_name="Admin",
             rating="5", technical_skills=5, communication=5, teamwork=5, leadership=5,
             achievements="Zero operational failures in 200+ tours. Reduced vendor costs by 12%.",
             areas_for_improvement="Documentation of SOPs",
             goals_next_period="Create ops playbook. Expand vendor network to 5 new cities.",
             review_date=str(_today() - timedelta(days=55))),
        dict(employee_id=emp_entities[2].id, employee_name="Priya Sharma",
             review_period="H2 2025", reviewer_id=user.id, reviewer_name="Admin",
             rating="4", technical_skills=5, communication=4, teamwork=4, leadership=3,
             achievements="Timely GST filings. Reduced expense processing time by 30%.",
             areas_for_improvement="Cross-team communication",
             goals_next_period="Implement automated expense tracking.",
             review_date=str(_today() - timedelta(days=50))),
        dict(employee_id=emp_entities[3].id, employee_name="Vikram Singh",
             review_period="H2 2025", reviewer_id=emp_entities[0].id, reviewer_name="Mitesh Yadav",
             rating="4", technical_skills=4, communication=5, teamwork=4, leadership=3,
             achievements="Converted 45 leads. Highest conversion rate in team (32%).",
             areas_for_improvement="Destination knowledge — Europe packages need work",
             goals_next_period="Complete destination training for Japan. Target 55 conversions.",
             review_date=str(_today() - timedelta(days=45))),
        dict(employee_id=emp_entities[6].id, employee_name="Sneha Roy",
             review_period="H2 2025", reviewer_id=emp_entities[0].id, reviewer_name="Mitesh Yadav",
             rating="3", technical_skills=4, communication=4, teamwork=3, leadership=2,
             achievements="Grew Instagram following by 300%. 15 campaigns executed.",
             areas_for_improvement="Analytics reporting. Cross-team collaboration.",
             goals_next_period="Learn Google Analytics. Generate 200 qualified leads.",
             review_date=str(_today() - timedelta(days=40))),
        dict(employee_id=emp_entities[7].id, employee_name="Arjun Nair",
             review_period="H2 2025", reviewer_id=emp_entities[1].id, reviewer_name="Chaya Devi",
             rating="4", technical_skills=4, communication=4, teamwork=5, leadership=3,
             achievements="150+ visa applications processed with 100% success. 0 booking errors.",
             areas_for_improvement="Take initiative on process improvements",
             goals_next_period="Learn supplier negotiation. Train visa processing SOP.",
             review_date=str(_today() - timedelta(days=35))),
    ]
    for r in reviews:
        status = "completed"
        _make_entity(tenant.id, "performance_review",
                     f"PR-{r['employee_name'][:4].upper()}-{r['review_period'].replace(' ','')}",
                     status, r, user.id)

    db.session.commit()
    print(f"    ✅ HR — 3 departments, 8 employees, {len(leaves)} leaves, 30d attendance, {len(reviews)} reviews")


def seed_marketing(tenant, user):
    """Seed Marketing module."""
    from app.shunya.marketing import MARKETING_ENTITY_TYPES

    # Add supplemental types that the task requires but aren't in MARKETING_ENTITY_TYPES
    extra_mkt_types = {
        "lead_form": {
            "label": "Lead Form",
            "icon": "📋",
            "schema": [
                {"name": "form_name", "label": "Form Name", "type": "text", "required": True},
                {"name": "description", "label": "Description", "type": "textarea"},
                {"name": "source_url", "label": "Source URL", "type": "text"},
                {"name": "submissions", "label": "Submissions", "type": "number"},
                {"name": "conversion_rate", "label": "Conversion Rate (%)", "type": "number"},
                {"name": "fields", "label": "Form Fields", "type": "textarea"},
                {"name": "campaign", "label": "Campaign", "type": "text"},
                {"name": "notes", "label": "Notes", "type": "textarea"},
            ],
            "statuses": ["active", "paused", "archived"],
            "layout": "table",
            "searchable_fields": ["form_name", "campaign"],
        },
        "analytics_report": {
            "label": "Analytics Report",
            "icon": "📊",
            "schema": [
                {"name": "report_name", "label": "Report Name", "type": "text", "required": True},
                {"name": "report_type", "label": "Report Type", "type": "select",
                 "options": ["campaign_performance", "website_analytics", "social_media", "email_marketing", "lead_analysis", "custom"]},
                {"name": "period_start", "label": "Period Start", "type": "date"},
                {"name": "period_end", "label": "Period End", "type": "date"},
                {"name": "key_findings", "label": "Key Findings", "type": "textarea"},
                {"name": "metrics", "label": "Metrics", "type": "json"},
                {"name": "generated_by", "label": "Generated By", "type": "text"},
                {"name": "notes", "label": "Notes", "type": "textarea"},
            ],
            "statuses": ["draft", "published", "archived"],
            "layout": "table",
            "searchable_fields": ["report_name", "report_type", "generated_by"],
        },
        "landing_page": {
            "label": "Landing Page",
            "icon": "🖥️",
            "schema": [
                {"name": "page_name", "label": "Page Name", "type": "text", "required": True},
                {"name": "url", "label": "Page URL", "type": "text"},
                {"name": "campaign", "label": "Campaign", "type": "text"},
                {"name": "views", "label": "Views", "type": "number"},
                {"name": "conversions", "label": "Conversions", "type": "number"},
                {"name": "cta", "label": "Call to Action", "type": "text"},
                {"name": "notes", "label": "Notes", "type": "textarea"},
            ],
            "statuses": ["draft", "published", "archived"],
            "layout": "table",
            "searchable_fields": ["page_name", "url", "campaign"],
        },
    }

    all_mkt_types = {**MARKETING_ENTITY_TYPES, **extra_mkt_types}
    for etype, config in all_mkt_types.items():
        _get_or_create_def(tenant.id, etype, config)
    db.session.commit()

    now = _now()

    # --- Campaigns ---
    campaigns = [
        dict(name="Summer Escape 2026", description="Exclusive summer holiday packages to hill stations and beaches",
             goal="lead_generation", target_audience="Families and young couples", budget=500000, spent=320000,
             channels="email, social, paid_ads",
             start_date=str(_today() - timedelta(days=15)), end_date=str(_today() + timedelta(days=75)),
             kpis="Target: 200 leads, 50 bookings, ₹40L revenue",
             notes="Focusing on Manali, Goa, and Kerala packages"),
        dict(name="Japan Explorer Launch", description="Launching new Japan tour packages for premium travelers",
             goal="brand_awareness", target_audience="Premium travelers aged 30-55", budget=800000, spent=450000,
             channels="email, social, events, content",
             start_date=str(_today() - timedelta(days=30)), end_date=str(_today() + timedelta(days=60)),
             kpis="Target: 100 leads, 20 bookings, ₹25L revenue",
             notes="Partnering with Japan Tourism Board"),
        dict(name="Family Holiday Special", description="Curated family packages for Diwali and Christmas holidays",
             goal="sales", target_audience="Families with children aged 4-16", budget=350000, spent=180000,
             channels="email, social, referral",
             start_date=str(_today() - timedelta(days=60)), end_date=str(_today() + timedelta(days=30)),
             kpis="Target: 150 leads, 60 bookings, ₹30L revenue",
             notes="Early bird discount of 15%"),
    ]
    for c in campaigns:
        _make_entity(tenant.id, "campaign",
                     f"CAMP-{c['name'][:8].upper().replace(' ','')}",
                     "active" if c == campaigns[0] else "active",
                     c, user.id)

    # --- Email Campaigns ---
    email_campaigns = [
        dict(name="Summer Sale Announcement", subject_line="☀️ Escape the Heat with Panchi Club! Up to 30% Off",
             preview_text="Discover our hottest summer deals on hill station and beach packages",
             sender_name="Panchi Club", sender_email="offers@panchi.club",
             recipient_list="All subscribers (4,500)", sent_count=4500, open_count=2340, click_count=680,
             bounce_count=45, unsubscribe_count=23,
             scheduled_at=str(now - timedelta(days=14)),
             content="Summer is here! Explore our exclusive summer packages with up to 30% discount...",
             notes="High open rate — 52%"),
        dict(name="Japan Explorer Newsletter", subject_line="🗾 Discover Japan: Cherry Blossoms & Samurai History",
             preview_text="Our curated Japan experience — limited group departure this November",
             sender_name="Panchi Club", sender_email="explore@panchi.club",
             recipient_list="Premium segment (1,200)", sent_count=1200, open_count=720, click_count=245,
             bounce_count=8, unsubscribe_count=5,
             scheduled_at=str(now - timedelta(days=7)),
             content="Japan awaits! Join our exclusive 10-day Japan Explorer tour...",
             notes="60% open rate — strong interest"),
        dict(name="Diwali Family Getaway", subject_line="🪔 Book Your Diwali Family Holiday & Get 15% Off",
             preview_text="Limited period offer on family packages for Diwali and Christmas",
             sender_name="Panchi Club", sender_email="family@panchi.club",
             recipient_list="Family segment (2,800)", sent_count=2800, open_count=1512, click_count=420,
             bounce_count=28, unsubscribe_count=12,
             scheduled_at=str(now - timedelta(days=21)),
             content="Celebrate Diwali with your loved ones at these magical destinations...",
             notes="15% conversion rate from clicks"),
        dict(name="Weekend Getaway Deals", subject_line="🏕️ Quick Weekend Getaways — Starting at ₹4,999",
             preview_text="Short trips perfect for that much-needed break",
             sender_name="Panchi Club", sender_email="deals@panchi.club",
             recipient_list="City segment (3,200)", sent_count=3200, open_count=1600, click_count=550,
             bounce_count=32, unsubscribe_count=18,
             scheduled_at=str(now - timedelta(days=30)),
             content="Need a break? Check out our handpicked weekend getaways...",
             notes="Best click-through rate in Q1"),
        dict(name="Customer Referral Program", subject_line="🤝 Refer a Friend & Both Get ₹2,000 Off!",
             preview_text="Share the joy of travel — earn rewards for every successful referral",
             sender_name="Panchi Club", sender_email="refer@panchi.club",
             recipient_list="Past customers (3,500)", sent_count=3500, open_count=1575, click_count=490,
             bounce_count=35, unsubscribe_count=15,
             scheduled_at=str(now - timedelta(days=45)),
             content="You loved traveling with us. Now share the experience...",
             notes="Generated 85 referrals so far"),
    ]
    for ec in email_campaigns:
        _make_entity(tenant.id, "email_campaign",
                     f"EMAIL-{ec['name'][:6].upper()}",
                     "sent",
                     ec, user.id)

    # --- Social Posts ---
    social_posts = [
        dict(content="☀️ Beat the heat this summer! Our curated Manali and Shimla packages start at just ₹8,999 per person. Tap to explore! 📍 #SummerEscape #Manali #TravelIndia",
             platform="instagram", scheduled_at=str(now - timedelta(days=5)), published_at=str(now - timedelta(days=5)),
             post_url="https://instagram.com/p/panchi-summer1", engagement_likes=1240, engagement_shares=340,
             engagement_comments=89, reach=45000, hashtags="#SummerEscape #Manali #TravelIndia #PanchiClub",
             campaign="Summer Escape 2026"),
        dict(content="🇯🇵 Japan is calling! Our 10-day Japan Explorer tour includes Tokyo, Kyoto, Osaka, and a bullet train experience. Limited to 12 travelers. Book now!",
             platform="facebook", scheduled_at=str(now - timedelta(days=3)), published_at=str(now - timedelta(days=3)),
             post_url="https://facebook.com/panchi/japan", engagement_likes=890, engagement_shares=210,
             engagement_comments=67, reach=28000, hashtags="#JapanTravel #ExploreJapan #PanchiClub",
             campaign="Japan Explorer Launch"),
        dict(content="Family time is the best time! 🏖️ Check out our Goa family packages with kids' clubs, beach resorts, and curated activities for all ages.",
             platform="instagram", scheduled_at=str(now - timedelta(days=7)), published_at=str(now - timedelta(days=7)),
             post_url="https://instagram.com/p/panchi-family1", engagement_likes=1560, engagement_shares=420,
             engagement_comments=120, reach=52000, hashtags="#FamilyTravel #GoaWithKids #PanchiClub",
             campaign="Family Holiday Special"),
        dict(content="Did you know? Panchi Club has served 5,000+ happy travelers since 2019. Here's what Rajesh from Mumbai had to say about his Kerala experience...",
             platform="facebook", scheduled_at=str(now - timedelta(days=10)), published_at=str(now - timedelta(days=10)),
             post_url="https://facebook.com/panchi/testimonial", engagement_likes=670, engagement_shares=180,
             engagement_comments=45, reach=22000, hashtags="#Testimonial #HappyTravelers #PanchiClub",
             campaign="Summer Escape 2026"),
        dict(content="Introducing our Winter 2026 collection! 🏔️ Kashmir houseboats, Himachal snow trails, and Rajasthan desert safaris. Early bird discounts available!",
             platform="instagram", scheduled_at=str(now + timedelta(days=14)),
             hashtags="#WinterTravel #Kashmir #Rajasthan #PanchiClub",
             campaign="Summer Escape 2026"),
        dict(content="Travel tip Tuesday! 🗺️ Always keep digital copies of your passport, visa, and travel insurance. Store them in a secure cloud folder accessible offline.",
             platform="facebook", scheduled_at=str(now - timedelta(days=12)), published_at=str(now - timedelta(days=12)),
             post_url="https://facebook.com/panchi/tip1", engagement_likes=430, engagement_shares=320,
             engagement_comments=28, reach=18000, hashtags="#TravelTips #TuesdayTips #PanchiClub",
             campaign="Family Holiday Special"),
    ]
    for sp in social_posts:
        status = "published" if sp.get("published_at") else "scheduled"
        _make_entity(tenant.id, "social_post", f"SOC-{sp['platform'][:3].upper()}-{_today().strftime('%d%m')}",
                     status, sp, user.id)

    # --- Landing Pages ---
    landing_pages = [
        dict(page_name="Summer Escape 2026", url="https://panchi.club/summer-escape-2026",
             campaign="Summer Escape 2026", views=12500, conversions=380,
             cta="Book Your Summer Escape",
             notes="Conversion rate: 3.04% — above industry average"),
        dict(page_name="Japan Explorer", url="https://panchi.club/japan-explorer",
             campaign="Japan Explorer Launch", views=8400, conversions=175,
             cta="Explore Japan",
             notes="Premium segment — higher AOV. Conversion rate: 2.08%"),
    ]
    for lp in landing_pages:
        _make_entity(tenant.id, "landing_page", f"LP-{lp['page_name'][:6].upper()}",
                     "published", lp, user.id)

    # --- Lead Forms ---
    lead_forms = [
        dict(form_name="Summer Escape Inquiry", description="Lead capture for summer package inquiries",
             source_url="https://panchi.club/summer-escape-2026", submissions=680, conversion_rate=12.5,
             fields="name, email, phone, destination, budget, travel_dates",
             campaign="Summer Escape 2026",
             notes="Highest performing form — 12.5% conversion"),
        dict(form_name="Japan Interest Form", description="Interest form for Japan Explorer tours",
             source_url="https://panchi.club/japan-explorer", submissions=320, conversion_rate=8.2,
             fields="name, email, phone, group_size, preferred_month",
             campaign="Japan Explorer Launch",
             notes="Premium inquiries — avg budget ₹1.5L"),
        dict(form_name="Newsletter Signup", description="General newsletter subscription",
             source_url="https://panchi.club", submissions=1200, conversion_rate=3.5,
             fields="name, email, interests",
             campaign="Summer Escape 2026",
             notes="Bulk subscribers — nurture campaign needed"),
    ]
    for lf in lead_forms:
        _make_entity(tenant.id, "lead_form", f"FORM-{lf['form_name'][:6].upper()}",
                     "active", lf, user.id)

    # --- Analytics Reports ---
    analytics_reports = [
        dict(report_name="Summer Campaign Performance — Week 3",
             report_type="campaign_performance",
             period_start=str(_today() - timedelta(days=21)), period_end=str(_today() - timedelta(days=14)),
             key_findings="Email open rate 52%, social engagement up 35% week-over-week",
             metrics={"email_opens": 2340, "email_clicks": 680, "social_reach": 125000, "leads_generated": 128},
             generated_by="Sneha Roy",
             notes="Summer campaign tracking well against KPIs"),
        dict(report_name="Q2 2025 Social Media Analytics",
             report_type="social_media",
             period_start=str(_today() - timedelta(days=120)), period_end=str(_today() - timedelta(days=30)),
             key_findings="Instagram engagement tripled. Facebook reach steady. Best posting time: 7-9pm",
             metrics={"instagram_followers": 8500, "facebook_followers": 4200, "total_engagement": 45600, "top_post_impressions": 52000},
             generated_by="Sneha Roy",
             notes="Instagram Reels driving highest engagement"),
        dict(report_name="Lead Source Analysis — June 2025",
             report_type="lead_analysis",
             period_start=str(_today() - timedelta(days=60)), period_end=str(_today() - timedelta(days=30)),
             key_findings="Website direct (32%), Referrals (28%), Social Media (22%), Paid Ads (18%)",
             metrics={"total_leads": 450, "website_leads": 144, "referral_leads": 126, "social_leads": 99, "paid_leads": 81},
             generated_by="Vikram Singh",
             notes="Referral program ROI is 4.5x — scaling up"),
    ]
    for ar in analytics_reports:
        _make_entity(tenant.id, "analytics_report", f"REP-{ar['report_name'][:6].upper()}",
                     "published", ar, user.id)

    db.session.commit()
    print(f"    ✅ MARKETING — {len(campaigns)} campaigns, {len(email_campaigns)} emails, {len(social_posts)} posts, "
          f"{len(landing_pages)} landing pages, {len(lead_forms)} forms, {len(analytics_reports)} reports")


def seed_support(tenant, user):
    """Seed Support module."""
    from app.shunya.support import SUPPORT_ENTITY_TYPES
    for etype, config in SUPPORT_ENTITY_TYPES.items():
        _get_or_create_def(tenant.id, etype, config)
    db.session.commit()

    # --- Support Tickets ---
    tickets = [
        dict(subject="Billing discrepancy — charged twice for Kerala package",
             customer_name="Rahul Verma", customer_email="rahul.verma@gmail.com", customer_phone="+91-9876543111",
             category="billing", priority="high",
             description="I was charged ₹1,35,000 twice for the Kerala family package booking ref PC-2024-001. Please refund the duplicate charge.",
             assigned_to="Priya Sharma", channel="email",
             resolution="Identified duplicate payment processing error. Refund initiated via Razorpay."),
        dict(subject="Need urgent visa appointment for Japan trip",
             customer_name="Anita Desai", customer_email="anita.desai@outlook.com", customer_phone="+91-9876543222",
             category="technical", priority="urgent",
             description="Our Japan trip is in 3 weeks and we haven't received visa appointment confirmation yet. Need immediate assistance.",
             assigned_to="Arjun Nair", channel="phone",
             resolution="Expedited visa processing. Appointment secured at VFS Mumbai for next week."),
        dict(subject="Reschedule hotel booking — Goa trip dates changed",
             customer_name="Meera Joshi", customer_email="meera.joshi@yahoo.com", customer_phone="+91-9876543333",
             category="account", priority="medium",
             description="We need to move our Goa trip from June 10-15 to June 20-25 due to school schedule change.",
             assigned_to="Mitesh Yadav", channel="email",
             resolution="Hotel dates shifted successfully. No cancellation charges as within 30-day policy."),
        dict(subject="Feature request: WhatsApp booking updates",
             customer_name="Sandeep Kumar", customer_email="sandeep.k@gmail.com", customer_phone="+91-9876543444",
             category="feature_request", priority="low",
             description="It would be great to get booking confirmations and updates via WhatsApp instead of email.",
             assigned_to="", channel="portal",
             resolution=""),
        dict(subject="Complaint: Airport transfer did not show up",
             customer_name="Kavita Reddy", customer_email="kavita.reddy@hotmail.com", customer_phone="+91-9876543555",
             category="complaint", priority="high",
             description="At Goa airport, the pre-booked private transfer did not show up. We waited 45 minutes and had to take a prepaid taxi. Very poor experience.",
             assigned_to="Chaya Devi", channel="phone",
             resolution="Apologized. Refunded transfer amount + provided 20% discount on next booking."),
        dict(subject="Need help with travel insurance claim",
             customer_name="Deepak Patel", customer_email="deepak.patel@gmail.com", customer_phone="+91-9876543666",
             category="technical", priority="medium",
             description="My baggage was lost during our return from Bangkok. Insurance company needs a letter from Panchi confirming our travel dates.",
             assigned_to="Rajesh Kumar", channel="email",
             resolution="Provided confirmation letter within 24 hours. Insurance claim filed."),
    ]
    ticket_entities = []
    for i, t in enumerate(tickets):
        statuses = ["new", "in_progress", "in_progress", "new", "in_progress", "resolved"]
        e = _make_entity(tenant.id, "ticket", f"TKT-{100+i}", statuses[i], t, user.id)
        if e:
            ticket_entities.append(e)

    # --- Knowledge Articles ---
    articles = [
        dict(title="Complete Guide to Indian Visa Types", category="how_to",
             content="""# Indian Visa Guide
## Types:
1. e-Tourist Visa (30 days) — Best for short trips
2. Regular Tourist Visa (1-5 years) — For frequent travelers
3. Business Visa — For business purposes

## Requirements:
- Valid passport (6+ months validity)
- Recent passport-size photographs
- Completed online application
- Proof of accommodation
- Return flight booking

## Processing Time:
- e-Visa: 3-5 working days
- Regular: 7-15 working days
""",
             tags="visa, travel documents, india visa, passport",
             author="Arjun Nair", related_articles="Visa Requirements by Country",
             article_type="public"),
        dict(title="Packing List for International Travel", category="how_to",
             content="""# Essential Packing Checklist
## Documents:
- Passport (with 6+ months validity)
- Visa printouts
- Travel insurance certificate
- Flight & hotel confirmations
- Emergency contacts list

## Electronics:
- Universal travel adapter
- Power bank (under 20,000 mAh for flight)
- Phone charger & cable
- Camera

## Health:
- Prescription medicines (with doctor's note)
- Basic first-aid kit
- Hand sanitizer & masks

## Clothing:
- Weather-appropriate outfits
- Comfortable walking shoes
- Light jacket/sweater
- Swimsuit (if applicable)
""",
             tags="packing, travel tips, checklist, preparation",
             author="Mitesh Yadav", related_articles="Travel Tips for First-Time Flyers",
             article_type="public"),
        dict(title="How to Book Group Tours with Panchi Club", category="how_to",
             content="""# Group Tour Booking Process
1. **Contact us** — Call or email with group size, preferred destination, and dates
2. **Custom quote** — We prepare a tailored itinerary within 48 hours
3. **Review & modify** — Adjust itinerary, hotels, activities as needed
4. **Confirm booking** — Pay 25% advance to secure dates
5. **Pre-trip briefing** — Receive detailed itinerary, travel documents, and tips
6. **Travel!** — Dedicated support throughout your journey

## Group Discounts:
- 10-15 people: 5% off
- 16-25 people: 10% off
- 25+ people: 15% off + free tour manager
""",
             tags="groups, tours, booking process, packages",
             author="Chaya Devi", related_articles="",
             article_type="public"),
        dict(title="Travel Insurance — What's Covered and Why You Need It", category="faq",
             content="""# Travel Insurance Guide
## What's Covered:
- Trip cancellation/interruption
- Medical emergencies (₹5L - ₹20L coverage)
- Baggage loss/delay
- Flight delays (4+ hours)
- Personal accident

## Why Panchi Recommends:
- Medical evacuation can cost ₹10L+
- Trip cancellation due to illness
- Lost baggage compensation
- Peace of mind for ₹500-2000

## How to Claim:
1. Inform us within 24 hours of incident
2. Collect documentation (police report, medical report, etc.)
3. Submit claim form with supporting documents
4. Track claim status via our portal
""",
             tags="insurance, travel insurance, coverage, claims",
             author="Rajesh Kumar", related_articles="Complete Guide to Indian Visa Types",
             article_type="public"),
        dict(title="Top 10 Destinations for First-Time International Travelers from India", category="faq",
             content="""# Best First International Destinations
1. **Thailand** (Bangkok, Phuket) — Budget-friendly, great food, easy visa
2. **Dubai** — Luxury on a budget, direct flights, no visa for Indians
3. **Sri Lanka** — Close, affordable, beautiful beaches
4. **Nepal** — No visa required, spiritual, adventure
5. **Maldives** — Stunning resorts, good for honeymoons
6. **Singapore** — Clean, safe, amazing food scene
7. **Malaysia** — Cultural diversity, great value
8. **Vietnam** — Incredible food, landscapes, budget-friendly
9. **Indonesia (Bali)** — Surf, culture, yoga, retreats
10. **Mauritius** — Beach paradise, Indian food, easy visa
""",
             tags="destinations, first time, international, travel tips",
             author="Vikram Singh", related_articles="Packing List for International Travel",
             article_type="public"),
    ]
    for i, art in enumerate(articles):
        _make_entity(tenant.id, "knowledge_article", f"KA-{100+i}",
                     "published", art, user.id)

    # --- FAQ entries as knowledge_articles with category=faq ---
    faqs = [
        dict(title="What payment methods do you accept?", category="faq",
             content="We accept all major credit/debit cards (Visa, Mastercard, RuPay), UPI (Google Pay, PhonePe, Paytm), NEFT/IMPS bank transfers, and EMI options on select cards.",
             tags="payment, modes, upi, card",
             author="Priya Sharma", article_type="public"),
        dict(title="What is your cancellation policy?", category="faq",
             content="Cancellation policy varies by package. Standard policy: 30+ days before trip — 90% refund. 15-30 days — 75% refund. 7-14 days — 50% refund. Less than 7 days — no refund. Non-refundable components (flights, visa fees) excluded.",
             tags="cancellation, refund, policy",
             author="Priya Sharma", article_type="public"),
        dict(title="Do you offer customized itineraries?", category="faq",
             content="Yes! We specialize in customized itineraries. Share your preferences, budget, and travel style, and our advisors will create a tailor-made itinerary within 48 hours.",
             tags="customization, itinerary, personalization",
             author="Mitesh Yadav", article_type="public"),
        dict(title="Is travel insurance mandatory?", category="faq",
             content="Travel insurance is mandatory for all international bookings through Panchi Club. For domestic trips, it's highly recommended but optional. We partner with ICICI Lombard and Tata AIG for comprehensive coverage.",
             tags="insurance, mandatory, travel insurance",
             author="Rajesh Kumar", article_type="public"),
    ]
    for i, faq in enumerate(faqs):
        _make_entity(tenant.id, "knowledge_article", f"FAQ-{100+i}",
                     "published", faq, user.id)

    # --- Customer Feedback ---
    feedbacks = [
        dict(customer_name="Rahul Verma", customer_email="rahul.verma@gmail.com",
             rating="4", category="service",
             feedback_text="Overall great experience with Panchi Club. The Kerala package was well-organized. Minor issue with billing which was resolved quickly.",
             source="email", ticket_id="TKT-100",
             action_taken="Billing issue resolved. Refund processed."),
        dict(customer_name="Kavita Reddy", customer_email="kavita.reddy@hotmail.com",
             rating="3", category="support",
             feedback_text="Trip was good but the airport transfer issue was very stressful. The team resolved it and compensated us, but the initial experience was poor.",
             source="phone", ticket_id="TKT-105",
             action_taken="Issue acknowledged. Compensation provided."),
        dict(customer_name="Priyanka Mehta", customer_email="priyanka.mehta@gmail.com",
             rating="5", category="service",
             feedback_text="Absolutely amazing Japan trip! Everything was perfectly organized. Our travel advisor Ananya was incredibly helpful. Will definitely book again!",
             source="survey",
             action_taken="Added to testimonials page."),
    ]
    for i, fb in enumerate(feedbacks):
        _make_entity(tenant.id, "feedback", f"FB-{100+i}",
                     "closed" if fb.get("action_taken") else "new", fb, user.id)

    # --- SLA Policies ---
    sla_policies = [
        dict(name="Urgent SLA", priority="urgent",
             response_time_hours=1, resolution_time_hours=4,
             escalation_after_hours=2, business_hours_only=False,
             penalty_if_breached="Full refund on service fees + 20% discount on next booking",
             notes="For emergencies — no response in 1hr = automatic escalation to ops manager"),
        dict(name="High Priority SLA", priority="high",
             response_time_hours=4, resolution_time_hours=24,
             escalation_after_hours=8, business_hours_only=True,
             penalty_if_breached="50% refund on service fees",
             notes="Business hours: 9am-7pm Mon-Sat"),
    ]
    for sl in sla_policies:
        _make_entity(tenant.id, "sla", f"SLA-{sl['priority'].upper()}",
                     "active", sl, user.id)

    db.session.commit()
    print(f"    ✅ SUPPORT — {len(tickets)} tickets, {len(articles)+len(faqs)} articles/FAQs, "
          f"{len(feedbacks)} feedbacks, {len(sla_policies)} SLAs")


def seed_supply_chain(tenant, user):
    """Seed Supply Chain module."""
    from app.shunya.supply_chain import SC_ENTITY_TYPES
    for etype, config in SC_ENTITY_TYPES.items():
        _get_or_create_def(tenant.id, etype, config)
    db.session.commit()

    # --- Suppliers (also seed the direct models.Supplier table) ---
    supplier_data = [
        dict(company_name="Taj Hotels", contact_person="Rajiv Menon", email="rajiv.menon@tajhotels.com",
             phone="+91-22-66651000", category="services", payment_terms="Net 30",
             rating=5, address="Taj Mahal Palace, Mumbai, Maharashtra 400001",
             notes="Premium hotel partner — preferred for luxury packages"),
        dict(company_name="Marriott International", contact_person="Anika Singh", email="anika.singh@marriott.com",
             phone="+91-124-4567890", category="services", payment_terms="Net 45",
             rating=4, address="Marriott India, Gurugram, Haryana 122002",
             notes="Mid-premium segment — good for business and family travelers"),
        dict(company_name="Hyatt Hotels", contact_person="Vivek Kapoor", email="vivek.kapoor@hyatt.com",
             phone="+91-80-45129000", category="services", payment_terms="Net 30",
             rating=4, address="Hyatt Regency, Bengaluru, Karnataka 560001",
             notes="Expanding partnership — preferred for city-center properties"),
        dict(company_name="Abercrombie & Kent India", contact_person="Sunil Mehta", email="sunil@abercrombiekent.in",
             phone="+91-11-45679999", category="services", payment_terms="Net 30",
             rating=5, address="Defence Colony, New Delhi 110024",
             notes="Luxury DMC partner — high-end customized tours"),
        dict(company_name="SOTC Travel Services", contact_person="Deepa Nair", email="deepa.nair@sotc.in",
             phone="+91-22-61162200", category="services", payment_terms="Net 45",
             rating=4, address="Churchgate, Mumbai 400020",
             notes="Mass-market DMC — good for group tours and FIT"),
        dict(company_name="Emirates Airlines", contact_person="Ahmed Al Maktoum", email="corporate@emirates.com",
             phone="+971-4-7088888", category="services", payment_terms="Net 15",
             rating=5, address="Emirates Group HQ, Dubai, UAE",
             notes="Preferred airline for international — direct flights from major Indian cities"),
        dict(company_name="IndiGo Airlines", contact_person="Rahul Bhatia", email="corporate@goindigo.in",
             phone="+91-124-4352500", category="services", payment_terms="Net 15",
             rating=4, address="IndiGo, Gurugram, Haryana 122016",
             notes="Domestic partner — best coverage of Indian cities"),
        dict(company_name="Savaari Car Rentals", contact_person="Karan Jain", email="karan@savaari.com",
             phone="+91-80-61666666", category="services", payment_terms="Net 30",
             rating=4, address="Savaari HQ, Bengaluru, Karnataka",
             notes="Pan-India car rental partner — airport transfers and sightseeing"),
    ]

    # Create entity-based suppliers
    supplier_entities = []
    for sd in supplier_data:
        e = _make_entity(tenant.id, "supplier", f"SUPP-{sd['company_name'][:5].upper()}",
                         "active", sd, user.id)
        if e:
            supplier_entities.append(e)

    # Also seed the direct Supplier model
    for s in supplier_data:
        existing = db.session.query(Supplier).filter_by(
            tenant_id=tenant.id, name=s["company_name"]
        ).first()
        if not existing:
            supp = Supplier(
                tenant_id=tenant.id,
                name=s["company_name"],
                category=s.get("contact_person", ""),
                contact=s.get("contact_person", ""),
                email=s.get("email", ""),
                phone=s.get("phone", ""),
                city=s.get("address", "").split(",")[-2].strip() if s.get("address") else "",
                gstin=f"27{s['company_name'][:3].upper()}P{_today().year}1Z1",
                payment_terms=s.get("payment_terms", ""),
                notes=s.get("notes", ""),
                rating=s.get("rating", 0),
            )
            db.session.add(supp)
    db.session.flush()

    # --- Products (travel packages and services) ---
    products = [
        dict(sku="PC-PKG-001", name="Kerala Family Delight", description="6D/5N Kerala family package — Munnar, Thekkady, Alleppey, Kochi",
             category="finished_good", unit_price=35000, unit="pack", min_stock=50, current_stock=200, warehouse="Delhi HQ",
             supplier_id="Taj Hotels"),
        dict(sku="PC-PKG-002", name="Goa Beach Retreat", description="4D/3N Goa package — Beach resort, water sports, sunset cruise",
             category="finished_good", unit_price=22000, unit="pack", min_stock=50, current_stock=180, warehouse="Mumbai Operations",
             supplier_id=""),
        dict(sku="PC-PKG-003", name="Japan Explorer Tour", description="10D/9N Japan tour — Tokyo, Hakone, Kyoto, Osaka with bullet train",
             category="finished_good", unit_price=185000, unit="pack", min_stock=20, current_stock=45, warehouse="Delhi HQ",
             supplier_id=""),
        dict(sku="PC-PKG-004", name="Manali Winter Special", description="5D/4N Manali package — Snow activities, hot springs, sightseeing",
             category="finished_good", unit_price=18000, unit="pack", min_stock=30, current_stock=120, warehouse="Delhi HQ",
             supplier_id=""),
        dict(sku="PC-SVC-001", name="Hotel Night — Taj (Standard)", description="Standard room night at Taj properties across India",
             category="service", unit_price=8500, unit="pcs", min_stock=100, current_stock=500, warehouse="Delhi HQ",
             supplier_id="Taj Hotels"),
        dict(sku="PC-SVC-002", name="Hotel Night — Marriott", description="Standard room night at Marriott properties in India",
             category="service", unit_price=6500, unit="pcs", min_stock=100, current_stock=400, warehouse="Delhi HQ",
             supplier_id="Marriott International"),
        dict(sku="PC-SVC-003", name="Airport Transfer Service", description="One-way airport transfer — sedan car with driver",
             category="service", unit_price=1500, unit="pcs", min_stock=200, current_stock=800, warehouse="Mumbai Operations",
             supplier_id="Savaari Car Rentals"),
        dict(sku="PC-SVC-004", name="Tour Guide Service (Full Day)", description="Professional English-speaking tour guide for 8 hours",
             category="service", unit_price=3000, unit="pcs", min_stock=30, current_stock=90, warehouse="Delhi HQ",
             supplier_id=""),
        dict(sku="PC-SVC-005", name="Visa Processing (Thailand)", description="eVisa processing for Thailand — includes form filling and submission",
             category="service", unit_price=3500, unit="pcs", min_stock=50, current_stock=150, warehouse="Delhi HQ",
             supplier_id=""),
        dict(sku="PC-SVC-006", name="Travel Insurance (International)", description="Comprehensive travel insurance up to ₹20L coverage",
             category="service", unit_price=1500, unit="pcs", min_stock=100, current_stock=500, warehouse="Delhi HQ",
             supplier_id=""),
    ]
    for p in products:
        _make_entity(tenant.id, "product", p["sku"], "active", p, user.id)

    # --- Purchase Orders ---
    purchase_orders = [
        dict(po_number="PO-2026-001", supplier_name="Taj Hotels",
             items=[{"item": "Hotel Night — Taj (Standard)", "qty": 100, "unit_price": 7500, "total": 750000}],
             total_amount=750000,
             order_date=str(_today() - timedelta(days=20)), expected_date=str(_today() + timedelta(days=10)),
             payment_terms="Net 30", notes="Q3 inventory — bulk booking for Diwali season"),
        dict(po_number="PO-2026-002", supplier_name="Emirates Airlines",
             items=[{"item": "DEL-DXB round trip tickets", "qty": 40, "unit_price": 15000, "total": 600000}],
             total_amount=600000,
             order_date=str(_today() - timedelta(days=15)), expected_date=str(_today() + timedelta(days=45)),
             payment_terms="Net 15", notes="Blocked seats for Dubai packages"),
        dict(po_number="PO-2026-003", supplier_name="Savaari Car Rentals",
             items=[{"item": "Airport Transfer Service", "qty": 200, "unit_price": 1200, "total": 240000}],
             total_amount=240000,
             order_date=str(_today() - timedelta(days=30)), expected_date=str(_today() - timedelta(days=5)),
             payment_terms="Net 30", notes="Q2 transfer bookings"),
        dict(po_number="PO-2026-004", supplier_name="Abercrombie & Kent India",
             items=[{"item": "Japan DMC services — tour package coordination", "qty": 10, "unit_price": 50000, "total": 500000}],
             total_amount=500000,
             order_date=str(_today() - timedelta(days=10)), expected_date=str(_today() + timedelta(days=20)),
             payment_terms="Net 30", notes="Japan Explorer — DMC coordination fees"),
        dict(po_number="PO-2026-005", supplier_name="SOTC Travel Services",
             items=[{"item": "Group tour coordination — Rajasthan circuit", "qty": 25, "unit_price": 15000, "total": 375000}],
             total_amount=375000,
             order_date=str(_today() - timedelta(days=45)), expected_date=str(_today() + timedelta(days=15)),
             payment_terms="Net 45", notes="Rajasthan group tour — June departure"),
    ]
    for po in purchase_orders:
        statuses = ["confirmed", "sent", "received", "confirmed", "confirmed"]
        _make_entity(tenant.id, "purchase_order", po["po_number"], statuses[purchase_orders.index(po)], po, user.id)

    # --- Warehouses ---
    warehouses = [
        dict(name="Delhi HQ", location="Connaught Place, New Delhi", capacity=10000, utilized=3500,
             manager="Rajesh Kumar",
             notes="Primary office and inventory hub. Handles all package materials and documentation."),
        dict(name="Mumbai Operations", location="Andheri East, Mumbai", capacity=8000, utilized=2800,
             manager="Chaya Devi",
             notes="West India operations base. Manages Goa, Maharashtra, Gujarat packages."),
        dict(name="Goa Desk", location="Panaji, Goa", capacity=3000, utilized=1200,
             manager="Chaya Devi",
             notes="On-ground support for Goa operations. Manages local transfers and excursions."),
    ]
    for wh in warehouses:
        _make_entity(tenant.id, "warehouse", f"WH-{wh['name'][:4].upper()}", "active", wh, user.id)

    db.session.commit()
    print(f"    ✅ SUPPLY CHAIN — {len(supplier_data)} suppliers, {len(products)} products, "
          f"{len(purchase_orders)} POs, {len(warehouses)} warehouses")


def seed_field_services(tenant, user):
    """Seed Field Services module."""
    from app.shunya.field_services import FS_ENTITY_TYPES
    for etype, config in FS_ENTITY_TYPES.items():
        _get_or_create_def(tenant.id, etype, config)
    db.session.commit()

    # --- Subcontractors (travel guides, drivers, photographers) ---
    subcontractors = [
        dict(company_name="Mountain Trekkers India", contact_person="Ravi Thapa", phone="+91-9876544001",
             email="ravi@mountaintrekkers.in", specialty="roofing",  # Maps to landscape/hiking
             license_number="TG-2024-001", insurance_expiry="2026-12-31",
             rating=5, contract_amount=250000,
             notes="Expert hiking guides for Himachal and Uttarakhand treks"),
        dict(company_name="Goa Beach Services", contact_person="Carlos Fernandes", phone="+91-9876544002",
             email="carlos@goabeach.in", specialty="general",
             license_number="GA-2024-015", insurance_expiry="2026-09-30",
             rating=4, contract_amount=180000,
             notes="Water sports and beach activity operators"),
        dict(company_name="PhotoWala Travel", contact_person="Amit Trivedi", phone="+91-9876544003",
             email="amit@photowala.in", specialty="general",
             license_number="PH-2025-002", insurance_expiry="2026-06-30",
             rating=5, contract_amount=300000,
             notes="Professional travel photographers for tours"),
        dict(company_name="Rajasthan Heritage Guides", contact_person="Bhanwar Singh", phone="+91-9876544004",
             email="bhanwar@rajasthanheritage.in", specialty="general",
             license_number="RJ-2023-088", insurance_expiry="2026-03-31",
             rating=4, contract_amount=150000,
             notes="Certified heritage walk guides for Jaipur, Jodhpur, Udaipur"),
        dict(company_name="Safe Wheels India", contact_person="Harpreet Singh", phone="+91-9876544005",
             email="harpreet@safewheels.in", specialty="general",
             license_number="DL-2025-050", insurance_expiry="2026-11-30",
             rating=4, contract_amount=400000,
             notes="Fleet of AC sedans and SUVs for airport transfers and sightseeing"),
        dict(company_name="Kerala Backwaters Crew", contact_person="Saji Varghese", phone="+91-9876544006",
             email="saji@keralabackwaters.in", specialty="general",
             license_number="KL-2024-022", insurance_expiry="2026-08-31",
             rating=5, contract_amount=200000,
             notes="Houseboat and backwater tour operators"),
        dict(company_name="Cultural Connect India", contact_person="Meena Iyer", phone="+91-9876544007",
             email="meena@culturalconnect.in", specialty="general",
             license_number="TN-2025-010", insurance_expiry="2026-10-31",
             rating=4, contract_amount=120000,
             notes="Cultural tour guides for South Indian heritage sites"),
        dict(company_name="Himalayan Drivers Collective", contact_person="Tashi Dorje", phone="+91-9876544008",
             email="tashi@himalayandrivers.in", specialty="general",
             license_number="HP-2024-101", insurance_expiry="2026-07-31",
             rating=5, contract_amount=350000,
             notes="Experienced drivers for Leh-Ladakh and Spiti valley tours"),
    ]
    subcontractor_entities = []
    for sc in subcontractors:
        e = _make_entity(tenant.id, "subcontractor", f"SUB-{sc['company_name'][:5].upper()}",
                         "active" if "2025" in sc.get("license_number", "") else "active", sc, user.id)
        if e:
            subcontractor_entities.append(e)

    # --- Work Orders ---
    work_orders = [
        dict(title="Goa Airport Transfers — June Batch", description="Coordinate airport transfers for 12 arriving guests across 3 flights",
             customer_name="Panchi Club Operations", customer_phone="+91-9876543002",
             customer_address="Goa International Airport, Dabolim",
             technician="Safe Wheels India", scheduled_date=str(_today() + timedelta(days=5)),
             estimated_hours=8, actual_hours=0, total_charge=18000,
             notes="3 vehicles needed. Drivers to hold name boards."),
        dict(title="Kerala Houseboat Experience — Family Trip", description="Coordinate houseboat cruise and dinner for Sharma family (4 pax)",
             customer_name="Amit Sharma", customer_phone="+91-9876543222",
             customer_address="Houseboat Jetty, Alleppey",
             technician="Kerala Backwaters Crew", scheduled_date=str(_today() + timedelta(days=12)),
             estimated_hours=6, actual_hours=0, total_charge=15000,
             notes="Sunset cruise with traditional Kerala dinner. Welcome drink on arrival."),
        dict(title="Delhi — Heritage Walk Photography", description="Photography coverage for Japanese tourist group heritage walk",
             customer_name="Japan Explorer Group", customer_phone="+91-9876543007",
             customer_address="Chandni Chowk, Old Delhi",
             technician="PhotoWala Travel", scheduled_date=str(_today() + timedelta(days=8)),
             estimated_hours=4, actual_hours=0, total_charge=12000,
             notes="2 photographers needed. Deliver edited photos within 48 hours."),
        dict(title="Rajasthan Guide Assignment — Jaipur Leg", description="Heritage guide for 3-day Jaipur itinerary for corporate group",
             customer_name="TechCorp India Offsite", customer_phone="+91-9876543001",
             customer_address="Amer Fort, Jaipur",
             technician="Rajasthan Heritage Guides", scheduled_date=str(_today() + timedelta(days=20)),
             estimated_hours=24, actual_hours=0, total_charge=36000,
             notes="Guide needed for Amer Fort, Hawa Mahal, City Palace, and Chokhi Dhani."),
        dict(title="Ladakh Road Trip — Driver Support", description="Experienced driver for 10-day Leh-Manali road trip",
             customer_name="Adventure Club India", customer_phone="+91-9876543008",
             customer_address="Leh Airport, Ladakh",
             technician="Himalayan Drivers Collective", scheduled_date=str(_today() + timedelta(days=30)),
             estimated_hours=80, actual_hours=0, total_charge=85000,
             notes="High-altitude driving experience required. 4x4 vehicle needed."),
    ]
    for i, wo in enumerate(work_orders):
        statuses = ["scheduled", "scheduled", "in_progress", "pending", "pending"]
        _make_entity(tenant.id, "work_order", f"WO-{200+i}", statuses[i], wo, user.id)

    # --- Estimates ---
    estimates = [
        dict(project_name="Corporate Offsite — Jim Corbett", customer_name="TechCorp India",
             items=[{"item": "Resort booking (3 nights)", "qty": 1, "rate": 125000, "total": 125000},
                    {"item": "Bus transfer (Delhi-Corbett)", "qty": 1, "rate": 45000, "total": 45000},
                    {"item": "Team building activities", "qty": 1, "rate": 35000, "total": 35000}],
             subtotal=205000, tax=36900, total=241900,
             valid_until=str(_today() + timedelta(days=15)),
             notes="Pricing valid for 15 days. Group of 25 people."),
        dict(project_name="Honeymoon Package — Andamans", customer_name="Priya & Arjun Nair",
             items=[{"item": "Hotel (5 nights beach resort)", "qty": 1, "rate": 85000, "total": 85000},
                    {"item": "Flight tickets (round trip)", "qty": 2, "rate": 12000, "total": 24000},
                    {"item": "Scuba diving experience", "qty": 2, "rate": 5000, "total": 10000}],
             subtotal=119000, tax=21420, total=140420,
             valid_until=str(_today() + timedelta(days=20)),
             notes="Romantic package with candlelight dinner included."),
        dict(project_name="Group Tour — Rajasthan Cultural Circuit", customer_name="Heritage Society of India",
             items=[{"item": "Hotel (7 nights)", "qty": 1, "rate": 175000, "total": 175000},
                    {"item": "AC Bus (Jaipur-Jodhpur-Udaipur)", "qty": 1, "rate": 65000, "total": 65000},
                    {"item": "Heritage guides (3 cities)", "qty": 3, "rate": 5000, "total": 15000},
                    {"item": "Monument entry fees", "qty": 30, "rate": 600, "total": 18000}],
             subtotal=273000, tax=49140, total=322140,
             valid_until=str(_today() + timedelta(days=30)),
             notes="Group of 30 senior citizens. Special accessibility arrangements needed."),
    ]
    for i, est in enumerate(estimates):
        _make_entity(tenant.id, "estimate", f"EST-{300+i}", "sent", est, user.id)

    db.session.commit()
    print(f"    ✅ FIELD SERVICES — {len(subcontractors)} subcontractors, {len(work_orders)} work orders, {len(estimates)} estimates")


def seed_legal(tenant, user):
    """Seed Legal module."""
    from app.shunya.legal import LEGAL_ENTITY_TYPES
    for etype, config in LEGAL_ENTITY_TYPES.items():
        _get_or_create_def(tenant.id, etype, config)
    db.session.commit()

    # --- Contracts ---
    contracts = [
        dict(title="Hotel Partner Agreement — Taj Hotels", contract_type="vendor",
             party_a="Panchi Club Private Limited", party_b="Taj Hotels Resorts & Palaces",
             start_date="2024-01-01", end_date="2026-12-31",
             value=5000000, auto_renew=True, renewal_alert_days=60,
             signed_by="Mitesh Yadav (Panchi) + Rajiv Menon (Taj)", signed_date="2023-12-15",
             notes="Preferred partner agreement. 15% commission on all bookings. Net 30 payment terms."),
        dict(title="Hotel Partner Agreement — Marriott International", contract_type="vendor",
             party_a="Panchi Club Private Limited", party_b="Marriott International India",
             start_date="2024-03-01", end_date="2025-12-31",
             value=3500000, auto_renew=True, renewal_alert_days=45,
             signed_by="Chaya Devi (Panchi) + Anika Singh (Marriott)", signed_date="2024-02-20",
             notes="Standard partnership. 12% commission. Quarterly business reviews."),
        dict(title="DMC Partnership — Abercrombie & Kent", contract_type="vendor",
             party_a="Panchi Club Private Limited", party_b="Abercrombie & Kent India",
             start_date="2024-06-01", end_date="2027-05-31",
             value=2000000, auto_renew=False, renewal_alert_days=90,
             signed_by="Mitesh Yadav (Panchi) + Sunil Mehta (A&K)", signed_date="2024-05-15",
             notes="Exclusive DMC partnership for premium India tours. Revenue share: 20%."),
        dict(title="Airline Corporate Agreement — Emirates", contract_type="vendor",
             party_a="Panchi Club Private Limited", party_b="Emirates Airlines",
             start_date="2024-04-01", end_date="2025-12-31",
             value=8000000, auto_renew=True, renewal_alert_days=60,
             signed_by="Chaya Devi (Panchi) + Ahmed Al Maktoum (Emirates)", signed_date="2024-03-20",
             notes="Corporate fare agreement. Discounted rates for group bookings. Net 15 payment."),
        dict(title="Transport Partner Agreement — Savaari", contract_type="vendor",
             party_a="Panchi Club Private Limited", party_b="Savaari Car Rentals Private Limited",
             start_date="2024-02-01", end_date="2026-01-31",
             value=1500000, auto_renew=True, renewal_alert_days=30,
             signed_by="Chaya Devi (Panchi) + Karan Jain (Savaari)", signed_date="2024-01-25",
             notes="Pan-India car rental services. 10% discount on bulk bookings."),
        dict(title="DMC Partnership — SOTC Travel", contract_type="vendor",
             party_a="Panchi Club Private Limited", party_b="SOTC Travel Services",
             start_date="2024-09-01", end_date="2026-08-31",
             value=1000000, auto_renew=False, renewal_alert_days=60,
             signed_by="Mitesh Yadav (Panchi) + Deepa Nair (SOTC)", signed_date="2024-08-15",
             notes="Mass-market tour coordination. Commission: 10% standard, 15% on sell-out."),
        dict(title="Employee Agreement — Mitesh Yadav", contract_type="employment",
             party_a="Panchi Club Private Limited", party_b="Mitesh Yadav",
             start_date="2019-06-01", end_date="",
             value=850000, auto_renew=True, renewal_alert_days=30,
             signed_by="Admin (Panchi) + Mitesh Yadav", signed_date="2019-06-01",
             notes="Senior Sales Advisor. Annual review in June. Performance bonus: up to 20%."),
        dict(title="Office Lease — Connaught Place", contract_type="lease",
             party_a="Panchi Club Private Limited", party_b="DLF Commercial Properties",
             start_date="2023-04-01", end_date="2028-03-31",
             value=6000000, auto_renew=True, renewal_alert_days=90,
             signed_by="Admin (Panchi) + DLF Rep", signed_date="2023-03-15",
             notes="Delhi HQ. 1500 sq ft. Monthly rent: ₹1,00,000. Lock-in: 3 years."),
    ]
    for i, c in enumerate(contracts):
        status_map = {"active": 0, "active": 1, "active": 2, "active": 3, "active": 4,
                      "pending_signature": 5, "active": 6, "active": 7}
        statuses = ["active", "active", "active", "active", "active", "pending_signature", "active", "active"]
        _make_entity(tenant.id, "contract", f"CON-{100+i}", statuses[i], c, user.id)

    # --- Document Templates ---
    templates = [
        dict(name="Booking Voucher", category="form",
             content="Booking Voucher — {{customer_name}}\nReference: {{booking_ref}}\nDates: {{check_in}} to {{check_out}}\nDestination: {{destination}}\nHotel: {{hotel_name}}\nRoom: {{room_type}}\nMeals: {{meal_plan}}\nTransfers: {{transfer_type}}\nTotal Amount: ₹{{total_amount}}\n\nTerms: Please present this voucher at check-in.",
             variables="customer_name, booking_ref, check_in, check_out, destination, hotel_name, room_type, meal_plan, transfer_type, total_amount",
             version="v2.1", notes="Standard booking voucher template"),
        dict(name="Invoice Template", category="form",
             content="INVOICE\nInvoice #: {{invoice_number}}\nDate: {{invoice_date}}\nCustomer: {{customer_name}}\n\nItems:\n{{items}}\n\nSubtotal: ₹{{subtotal}}\nGST (18%): ₹{{tax}}\nTotal: ₹{{total}}\n\nPayment Terms: {{payment_terms}}\n\nThank you for choosing Panchi Club!",
             variables="invoice_number, invoice_date, customer_name, items, subtotal, tax, total, payment_terms",
             version="v1.3", notes="GST-compliant invoice template"),
        dict(name="Detailed Itinerary Template", category="proposal",
             content="# {{trip_title}}\n\n**Destination:** {{destination}}\n**Duration:** {{duration}}\n**Travelers:** {{travelers}}\n\n## Day {{day_number}} — {{date}}\n{{day_description}}\n\n---\n\n**Inclusions:** {{inclusions}}\n**Exclusions:** {{exclusions}}\n**Total Cost:** ₹{{total_cost}} per person\n\n*This is a proposed itinerary subject to availability.*",
             variables="trip_title, destination, duration, travelers, day_number, date, day_description, inclusions, exclusions, total_cost",
             version="v3.0", notes="Standard itinerary template for client proposals"),
    ]
    for i, t in enumerate(templates):
        _make_entity(tenant.id, "document_template", f"TMPL-{100+i}", "active", t, user.id)

    # --- Compliance Items ---
    compliance = [
        dict(regulation="Travel Insurance Mandate — International Packages",
             description="All international tour packages must include mandatory travel insurance covering minimum ₹10L medical expenses and trip cancellation.",
             category="industry", due_date=str(_today() + timedelta(days=30)),
             assigned_to="Chaya Devi",
             notes="Ensure all international booking contracts include insurance clause"),
        dict(regulation="GST Compliance — Tour Package Taxation",
             description="Verify correct GST rates (5% without accommodation, 12% with accommodation) on all tour packages and invoices.",
             category="tax", due_date=str(_today() + timedelta(days=15)),
             assigned_to="Priya Sharma",
             notes="Monthly GST filing due by 20th. Verify HSN codes."),
        dict(regulation="Data Privacy — Customer Information Protection",
             description="Ensure all customer data (passport copies, addresses, payment info) is stored encrypted and access is role-based.",
             category="gdpr", due_date=str(_today() + timedelta(days=45)),
             assigned_to="Rajesh Kumar",
             notes="Annual data audit. Check access logs for unauthorized entries."),
        dict(regulation="IATA Accreditation Renewal",
             description="Renew IATA accreditation for international flight booking capability. Submit annual financial statements.",
             category="industry", due_date=str(_today() + timedelta(days=90)),
             assigned_to="Mitesh Yadav",
             notes="IATA #: 14-3 1234 5. Submit by March 31."),
        dict(regulation="Employee Background Verification — New Hires",
             description="All new employees must undergo background verification including police clearance, education verification, and previous employment check.",
             category="labor", due_date=str(_today() + timedelta(days=60)),
             assigned_to="Priya Sharma",
             notes="Pending verification for Ananya Kapoor."),
    ]
    for i, c in enumerate(compliance):
        statuses = ["in_progress", "in_progress", "pending", "pending", "non_compliant"]
        _make_entity(tenant.id, "compliance_item", f"COMP-{100+i}", statuses[i], c, user.id)

    db.session.commit()
    print(f"    ✅ LEGAL — {len(contracts)} contracts, {len(templates)} templates, {len(compliance)} compliance items")


def seed_sales_crm(tenant, user):
    """Seed Sales CRM module."""
    from app.shunya.sales_crm import SALES_ENTITY_TYPES
    for etype, config in SALES_ENTITY_TYPES.items():
        _get_or_create_def(tenant.id, etype, config)
    db.session.commit()

    # --- Leads ---
    leads = [
        dict(first_name="Rohan", last_name="Mehta", email="rohan.mehta@gmail.com", phone="+91-9876545001",
             company="Self-employed", job_title="Business Owner", lead_source="referral",
             industry="Retail", lead_score=85, estimated_value=350000,
             assigned_to="Mitesh Yadav",
             notes="Referred by Amit Sharma. Interested in Europe family trip. Budget: ₹3-4L."),
        dict(first_name="Sneha", last_name="Patel", email="sneha.patel@techcorp.in", phone="+91-9876545002",
             company="TechCorp India", job_title="HR Manager", lead_source="website",
             industry="Technology", lead_score=65, estimated_value=500000,
             assigned_to="Vikram Singh",
             notes="Enquired about corporate offsite. Group of 25 people."),
        dict(first_name="Arun", last_name="Krishnan", email="arun.krishnan@yahoo.com", phone="+91-9876545003",
             company="Accenture", job_title="Senior Manager", lead_source="email_campaign",
             industry="Technology", lead_score=70, estimated_value=280000,
             assigned_to="Mitesh Yadav",
             notes="Responded to Japan Explorer email. Interested in Nov 2026 departure."),
        dict(first_name="Pooja", last_name="Deshmukh", email="pooja.d@outlook.com", phone="+91-9876545004",
             company="ThinkDesign Studio", job_title="Creative Director", lead_source="social_media",
             industry="Media", lead_score=45, estimated_value=150000,
             assigned_to="Vikram Singh",
             notes="Instagram inquiry. Looking for Goa honeymoon package."),
        dict(first_name="Vijay", last_name="Malhotra", email="vijay.m@hotmail.com", phone="+91-9876545005",
             company="Malhotra Group", job_title="Director", lead_source="referral",
             industry="Real Estate", lead_score=90, estimated_value=1200000,
             assigned_to="Mitesh Yadav",
             notes="VIP referral from existing client. Wants luxury Europe tour for family of 6."),
        dict(first_name="Neha", last_name="Gupta", email="neha.gupta@gmail.com", phone="+91-9876545006",
             company="Freelancer", job_title="Content Writer", lead_source="website",
             industry="Media", lead_score=30, estimated_value=80000,
             assigned_to="Ananya Kapoor",
             notes="Solo traveler. Budget trip to Thailand."),
        dict(first_name="Dr. Sanjay", last_name="Verma", email="sanjay.verma@apollohospitals.com", phone="+91-9876545007",
             company="Apollo Hospitals", job_title="Chief of Staff", lead_source="event",
             industry="Healthcare", lead_score=75, estimated_value=600000,
             assigned_to="Mitesh Yadav",
             notes="Met at Travel & Hospitality Expo. Interested in medical tourism coordination."),
        dict(first_name="Kiran", last_name="Reddy", email="kiran.reddy@gmail.com", phone="+91-9876545008",
             company="Reddy Constructions", job_title="Owner", lead_source="cold_call",
             industry="Real Estate", lead_score=35, estimated_value=200000,
             assigned_to="Vikram Singh",
             notes="Called from lead list. Moderate interest in Kashmir package."),
        dict(first_name="Fatima", last_name="Sheikh", email="fatima.sheikh@gmail.com", phone="+91-9876545009",
             company="Sheikh & Co.", job_title="Partner", lead_source="partner",
             industry="Finance", lead_score=80, estimated_value=450000,
             assigned_to="Ananya Kapoor",
             notes="Partner referral from travel agent network. Interested in Malaysia-Singapore."),
        dict(first_name="Ravi", last_name="Joshi", email="ravi.joshi@tatamotors.com", phone="+91-9876545010",
             company="Tata Motors", job_title="VP Operations", lead_source="inbound",
             industry="Manufacturing", lead_score=55, estimated_value=350000,
             assigned_to="Vikram Singh",
             notes="Inbound inquiry via website. Looking for family trip to Sri Lanka."),
    ]
    lead_statuses = ["new", "contacted", "qualified", "new", "new", "new", "contacted", "contacted", "qualified", "new"]
    lead_entities = []
    for i, ld in enumerate(leads):
        e = _make_entity(tenant.id, "lead", f"LEAD-{100+i}", lead_statuses[i], ld, user.id)
        if e:
            lead_entities.append(e)

    # --- Accounts ---
    accounts = [
        dict(account_name="TechCorp India", website="https://techcorp.in", phone="+91-80-45671234",
             email="corporate@techcorp.in", industry="technology", account_type="customer",
             annual_revenue=50000000, employee_count=500,
             billing_address="12, MG Road, Bengaluru, Karnataka", city="Bengaluru", state="Karnataka",
             country="India", pincode="560001", gstin="29AABCU1234D1Z5",
             owner="Mitesh Yadav",
             description="Enterprise technology company. Regular corporate travel bookings."),
        dict(account_name="Heritage Society of India", website="https://heritagesociety.in", phone="+91-11-23456789",
             email="info@heritagesociety.in", industry="education", account_type="customer",
             annual_revenue=5000000, employee_count=150,
             billing_address="15, Janpath, New Delhi", city="New Delhi", state="Delhi",
             country="India", pincode="110001", gstin="07HERS1234F1Z0",
             owner="Mitesh Yadav",
             description="Cultural organization. Organizes heritage tours for members."),
        dict(account_name="Travel Partners Network", website="https://travelpartners.in", phone="+91-22-34567890",
             email="partners@travelpartners.in", industry="hospitality", account_type="partner",
             annual_revenue=20000000, employee_count=50,
             billing_address="5, Linking Road, Bandra West, Mumbai", city="Mumbai", state="Maharashtra",
             country="India", pincode="400050", gstin="27TRAV1234D1Z1",
             owner="Chaya Devi",
             description="Travel agent network. Refers clients to Panchi Club."),
        dict(account_name="Global MedTours", website="https://globalmedtours.com", phone="+91-124-4567890",
             email="info@globalmedtours.com", industry="healthcare", account_type="partner",
             annual_revenue=15000000, employee_count=30,
             billing_address="42, Golf Course Road, Gurugram", city="Gurugram", state="Haryana",
             country="India", pincode="122002", gstin="06GLOB5678E1Z2",
             owner="Mitesh Yadav",
             description="Medical tourism facilitator. Coordinates travel for international patients."),
        dict(account_name="Malhotra Group", website="https://malhotragroup.com", phone="+91-11-45661234",
             email="info@malhotragroup.com", industry="real_estate", account_type="customer",
             annual_revenue=100000000, employee_count=200,
             billing_address="78, Rajendra Place, New Delhi", city="New Delhi", state="Delhi",
             country="India", pincode="110008", gstin="07MALH9012H1Z4",
             owner="Mitesh Yadav",
             description="High-value real estate group. VIP travel arrangements."),
    ]
    account_entities = []
    for acct in accounts:
        e = _make_entity(tenant.id, "account", f"ACC-{acct['account_name'][:5].upper()}", "active", acct, user.id)
        if e:
            account_entities.append(e)

    # --- Contacts ---
    contacts = [
        dict(first_name="Neha", last_name="Sharma", email="neha.sharma@techcorp.in",
             phone="+91-9876546001", mobile="+91-9876546001",
             account_id=str(account_entities[0].id) if account_entities else "",
             account_name="TechCorp India", job_title="HR Executive", department="Human Resources",
             source="website", assigned_to="Mitesh Yadav",
             notes="Primary contact for corporate bookings."),
        dict(first_name="Vikram", last_name="Rao", email="vikram.rao@techcorp.in",
             phone="+91-9876546002", mobile="+91-9876546002",
             account_id=str(account_entities[0].id) if account_entities else "",
             account_name="TechCorp India", job_title="VP Operations", department="Operations",
             source="referral", assigned_to="Mitesh Yadav",
             notes="Decision maker for corporate offsites."),
        dict(first_name="Prof. Ashok", last_name="Sharma", email="ashok.sharma@heritagesociety.in",
             phone="+91-9876546003", mobile="+91-9876546003",
             account_id=str(account_entities[1].id) if account_entities else "",
             account_name="Heritage Society of India", job_title="Secretary", department="Programs",
             birthdate="1965-08-12", source="event", assigned_to="Mitesh Yadav",
             notes="Coordinates all heritage tours."),
        dict(first_name="Rekha", last_name="Mishra", email="rekha@travelpartners.in",
             phone="+91-9876546004", mobile="+91-9876546004",
             account_id=str(account_entities[2].id) if account_entities else "",
             account_name="Travel Partners Network", job_title="Partnership Manager", department="Partnerships",
             source="partner", assigned_to="Chaya Devi",
             notes="Main point of contact for partner referrals."),
        dict(first_name="Dr. Arun", last_name="Pillai", email="arun@globalmedtours.com",
             phone="+91-9876546005", mobile="+91-9876546005",
             account_id=str(account_entities[3].id) if account_entities else "",
             account_name="Global MedTours", job_title="Director", department="Operations",
             source="event", assigned_to="Mitesh Yadav",
             notes="Met at healthcare tourism conference."),
        dict(first_name="Priyanka", last_name="Malhotra", email="priyanka@malhotragroup.com",
             phone="+91-9876546006", mobile="+91-9876546006",
             account_id=str(account_entities[4].id) if account_entities else "",
             account_name="Malhotra Group", job_title="Executive Assistant to Director", department="Administration",
             source="referral", assigned_to="Mitesh Yadav",
             notes="Coordinates all travel for the Malhotra family."),
        dict(first_name="Siddharth", last_name="Malhotra", email="sid@malhotragroup.com",
             phone="+91-9876546007", mobile="+91-9876546007",
             account_id=str(account_entities[4].id) if account_entities else "",
             account_name="Malhotra Group", job_title="Director", department="Management",
             source="referral", assigned_to="Mitesh Yadav",
             notes="Decision maker. Wants luxury travel."),
        dict(first_name="Rahul", last_name="Verma", email="rahul.verma@outlook.com",
             phone="+91-9876546008", mobile="+91-9876546008",
             account_name="Individual", job_title="Marketing Consultant", department="",
             source="referral", assigned_to="Vikram Singh",
             notes="Existing customer — previously booked Kerala package."),
    ]
    for ct in contacts:
        _make_entity(tenant.id, "contact", f"CONT-{ct['first_name'][:4].upper()}",
                     "active", ct, user.id)

    # --- Opportunities ---
    opportunities = [
        dict(name="TechCorp Q3 Offsite — Jim Corbett", account_id=str(account_entities[0].id) if account_entities else "",
             account_name="TechCorp India", amount=500000, expected_close_date=str(_today() + timedelta(days=30)),
             probability=85, lead_source="referral", sales_stage="negotiation",
             assigned_to="Mitesh Yadav",
             description="Corporate offsite for 25 people. 3 nights at Jim Corbett. Team building activities included.",
             competitors="MakeMyTrip for Business", win_notes="Strong relationship with HR team."),
        dict(name="Malhotra Family Europe Tour", account_id=str(account_entities[4].id) if account_entities else "",
             account_name="Malhotra Group", amount=1200000, expected_close_date=str(_today() + timedelta(days=60)),
             probability=70, lead_source="referral", sales_stage="proposal",
             assigned_to="Mitesh Yadav",
             description="Luxury Europe tour for family of 6. Paris, Swiss Alps, Rome. 14 days.",
             competitors="Kulinari Travels", win_notes="Need to propose exclusive butler-serviced options."),
        dict(name="Heritage Society Rajasthan Tour", account_id=str(account_entities[1].id) if account_entities else "",
             account_name="Heritage Society of India", amount=322140, expected_close_date=str(_today() + timedelta(days=15)),
             probability=90, lead_source="event", sales_stage="negotiation",
             assigned_to="Mitesh Yadav",
             description="Group tour for 30 senior citizens. 7 nights. Jaipur-Jodhpur-Udaipur.",
             competitors="", win_notes="Almost finalized. Price negotiation in progress."),
    ]
    for opp in opportunities:
        _make_entity(tenant.id, "opportunity", f"OPP-{opp['name'][:6].upper().replace(' ','')}",
                     "in_progress", opp, user.id)

    # --- Quotes ---
    quotes = [
        dict(quote_number="QT-2026-001", account_id=str(account_entities[0].id) if account_entities else "",
             account_name="TechCorp India", contact_id="",
             opportunity_id="", valid_until=str(_today() + timedelta(days=30)),
             subtotal=205000, discount=0, tax_rate=18, tax_amount=36900, total_amount=241900,
             currency="INR", payment_terms="50% advance, 50% on completion",
             delivery_terms="Inclusive of all taxes", assigned_to="Mitesh Yadav",
             notes="Corporate offsite — Jim Corbett",
             terms_and_conditions="Cancellation: 50% refund 15+ days before, no refund within 7 days"),
        dict(quote_number="QT-2026-002", account_id=str(account_entities[1].id) if account_entities else "",
             account_name="Heritage Society of India", contact_id="",
             opportunity_id="", valid_until=str(_today() + timedelta(days=30)),
             subtotal=273000, discount=15000, tax_rate=18, tax_amount=46440, total_amount=304440,
             currency="INR", payment_terms="Full payment 30 days before departure",
             delivery_terms="Inclusive of all applicable taxes", assigned_to="Mitesh Yadav",
             notes="Senior citizen group — Rajasthan heritage tour. 10% discount applied.",
             terms_and_conditions="Group size minimum 25 pax. Free cancellation up to 30 days."),
        dict(quote_number="QT-2026-003", account_name="Priya & Arjun Nair", contact_id="",
             opportunity_id="", valid_until=str(_today() + timedelta(days=20)),
             subtotal=119000, discount=5000, tax_rate=18, tax_amount=20520, total_amount=134520,
             currency="INR", payment_terms="100% payment at booking",
             delivery_terms="Honeymoon package — special inclusions: candlelight dinner, couple spa",
             assigned_to="Ananya Kapoor",
             notes="Honeymoon package — Andaman Islands. Early bird discount applied.",
             terms_and_conditions="Romance package add-ons non-refundable."),
    ]
    for qt in quotes:
        _make_entity(tenant.id, "quote", qt["quote_number"], "sent", qt, user.id)

    # --- Target Lists ---
    target_lists = [
        dict(name="Corporate Travel Managers — Bengaluru", description="HR and admin contacts at Bengaluru-based companies",
             list_type="dynamic", target_type="contacts", member_count=150,
             campaign="Corporate Travel Program", assigned_to="Mitesh Yadav",
             filter_criteria="city=Bengaluru & job_title contains (HR, Admin, Operations)",
             notes="For corporate travel program launch"),
        dict(name="Premium Travelers — Luxury Segment", description="High net worth individuals with ₹5L+ travel budget",
             list_type="static", target_type="leads", member_count=85,
             campaign="Luxury Collection Launch", assigned_to="Mitesh Yadav",
             filter_criteria="lead_score > 80 & estimated_value > 500000",
             notes="For luxury package promotions"),
    ]
    for tl in target_lists:
        _make_entity(tenant.id, "target_list", f"TLIST-{tl['name'][:6].upper()}",
                     "active", tl, user.id)

    db.session.commit()
    print(f"    ✅ SALES CRM — {len(leads)} leads, {len(accounts)} accounts, {len(contacts)} contacts, "
          f"{len(opportunities)} opportunities, {len(quotes)} quotes, {len(target_lists)} target lists")


def seed_finance(tenant, user):
    """Seed Finance module: EntityDefinitions, invoice entities, payment entities, direct Payment/Invoice models."""
    from app.shunya.finance import FINANCE_ENTITY_TYPES

    # Add 'payment' entity type if not present
    finance_types = dict(FINANCE_ENTITY_TYPES)
    finance_types["payment"] = {
        "label": "Payment",
        "icon": "💳",
        "schema": [
            {"name": "payment_ref", "label": "Payment Ref", "type": "text", "required": True},
            {"name": "customer_name", "label": "Customer/Supplier", "type": "text", "required": True},
            {"name": "amount", "label": "Amount", "type": "number", "required": True},
            {"name": "type", "label": "Type", "type": "select",
             "options": ["guest_payment", "supplier_payment", "refund", "advance"]},
            {"name": "payment_mode", "label": "Payment Mode", "type": "select",
             "options": ["bank_transfer", "upi", "card", "cash", "cheque"]},
            {"name": "reference", "label": "Reference", "type": "text"},
            {"name": "notes", "label": "Notes", "type": "textarea"},
        ],
        "statuses": ["pending", "completed", "failed", "refunded"],
        "layout": "table",
        "searchable_fields": ["payment_ref", "customer_name"],
    }

    for etype, config in finance_types.items():
        _get_or_create_def(tenant.id, etype, config)
    db.session.commit()

    now = _now()

    # --- Invoice entities ---
    invoices_data = [
        dict(invoice_number="INV-2026-001", customer_name="Amit Sharma",
             customer_email="amit@sharma.co", customer_phone="+91-9876543222",
             items=[{"item": "Dubai Family Holiday Package", "qty": 1, "rate": 280000, "total": 280000}],
             subtotal=280000, tax=50400, total=330400, currency="INR",
             due_date=str(_today() + timedelta(days=15)), paid_amount=330400,
             notes="Dubai trip (Mar 2024) — Fully paid"),
        dict(invoice_number="INV-2026-002", customer_name="TechCorp India",
             customer_email="corporate@techcorp.in", customer_phone="+91-80-45671234",
             items=[{"item": "Jim Corbett Corporate Offsite", "qty": 1, "rate": 500000, "total": 500000},
                    {"item": "Bus Transfers", "qty": 2, "rate": 45000, "total": 90000}],
             subtotal=590000, tax=106200, total=696200, currency="INR",
             due_date=str(_today() + timedelta(days=30)), paid_amount=348100,
             notes="50% advance received. Balance due before departure."),
        dict(invoice_number="INV-2026-003", customer_name="Heritage Society of India",
             customer_email="info@heritagesociety.in", customer_phone="+91-11-23456789",
             items=[{"item": "Rajasthan Heritage Tour (30 pax)", "qty": 1, "rate": 322140, "total": 322140}],
             subtotal=322140, tax=57985, total=380125, currency="INR",
             due_date=str(_today() + timedelta(days=45)), paid_amount=0,
             notes="Invoice sent. Awaiting payment."),
        dict(invoice_number="INV-2026-004", customer_name="Sneha Patel",
             customer_email="sneha.patel@gmail.com", customer_phone="+91-9876545002",
             items=[{"item": "Goa Honeymoon Package", "qty": 1, "rate": 150000, "total": 150000}],
             subtotal=150000, tax=27000, total=177000, currency="INR",
             due_date=str(_today() + timedelta(days=60)), paid_amount=0,
             notes="Package being finalized."),
    ]
    for inv in invoices_data:
        _make_entity(tenant.id, "invoice", inv["invoice_number"],
                     "paid" if inv["paid_amount"] == inv["total"] else ("sent" if inv["paid_amount"] else "draft"),
                     inv, user.id)

    # --- Payment Entities ---
    payments_entity = [
        dict(payment_ref="PAY-2026-001", customer_name="Amit Sharma", amount=330400,
             type="guest_payment", payment_mode="bank_transfer", reference="NEFT HDFC230456",
             notes="Full payment for Dubai Family Holiday"),
        dict(payment_ref="PAY-2026-002", customer_name="TechCorp India", amount=348100,
             type="guest_payment", payment_mode="bank_transfer", reference="NEFT ICICI789012",
             notes="50% advance payment for Jim Corbett offsite"),
        dict(payment_ref="PAY-2026-003", customer_name="Taj Hotels", amount=750000,
             type="supplier_payment", payment_mode="bank_transfer", reference="NEFT HDFC998877",
             notes="Bulk booking payment — Q3 inventory"),
        dict(payment_ref="PAY-2026-004", customer_name="Emirates Airlines", amount=600000,
             type="supplier_payment", payment_mode="bank_transfer", reference="NEFT SBI445566",
             notes="Blocked seats for Dubai packages"),
    ]
    for pay in payments_entity:
        _make_entity(tenant.id, "payment", pay["payment_ref"],
                     "completed", pay, user.id)

    # --- Direct Payment model records ---
    direct_payments = [
        Payment(tenant_id=tenant.id, amount=330400, currency="INR",
                type="guest_payment", gateway="Razorpay", gateway_ref="RP-2024-001",
                status="completed", notes="Dubai Family Holiday — full payment", paid_at=now - timedelta(days=350)),
        Payment(tenant_id=tenant.id, amount=348100, currency="INR",
                type="guest_payment", gateway="Razorpay", gateway_ref="RP-2026-001",
                status="completed", notes="TechCorp — 50% advance", paid_at=now - timedelta(days=10)),
        Payment(tenant_id=tenant.id, amount=750000, currency="INR",
                type="supplier_payment", gateway="NEFT", gateway_ref="NEFT-HDFC-998877",
                status="completed", notes="Taj Hotels — Q3 bulk booking", paid_at=now - timedelta(days=18)),
        Payment(tenant_id=tenant.id, amount=600000, currency="INR",
                type="supplier_payment", gateway="NEFT", gateway_ref="NEFT-SBI-445566",
                status="completed", notes="Emirates — seat blocking", paid_at=now - timedelta(days=12)),
        Payment(tenant_id=tenant.id, amount=135000, currency="INR",
                type="guest_payment", gateway="PhonePe", gateway_ref="PP-2024-002",
                status="completed", notes="Amit Sharma — Kerala trip payment", paid_at=now - timedelta(days=1720)),
    ]
    for dp in direct_payments:
        db.session.add(dp)

    # --- Direct Invoice model records ---
    direct_invoices = [
        Invoice(tenant_id=tenant.id, invoice_number="INV-2024-001", total_amount=135000,
                tax_rate=18, tax=24300, discount=0, grand_total=159300,
                currency="INR", status="paid", due_date=now - timedelta(days=1750),
                paid_at=now - timedelta(days=1755)),
        Invoice(tenant_id=tenant.id, invoice_number="INV-2024-002", total_amount=520000,
                tax_rate=18, tax=93600, discount=0, grand_total=613600,
                currency="INR", status="paid", due_date=now - timedelta(days=830),
                paid_at=now - timedelta(days=835)),
        Invoice(tenant_id=tenant.id, invoice_number="INV-2024-003", total_amount=295000,
                tax_rate=18, tax=53100, discount=0, grand_total=348100,
                currency="INR", status="paid", due_date=now - timedelta(days=360),
                paid_at=now - timedelta(days=365)),
        Invoice(tenant_id=tenant.id, invoice_number="INV-2026-005", total_amount=500000,
                tax_rate=18, tax=90000, discount=0, grand_total=590000,
                currency="INR", status="pending", due_date=now + timedelta(days=25)),
    ]
    for di in direct_invoices:
        db.session.add(di)

    db.session.commit()
    print(f"    ✅ FINANCE — {len(invoices_data)} invoice entities, {len(payments_entity)} payment entities, "
          f"{len(direct_payments)} Payment records, {len(direct_invoices)} Invoice records")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    with app.app_context():
        db.create_all()
        print("\n" + "=" * 72)
        print("  🌴 PANCHI CLUB — MASTER SEED SCRIPT")
        print("=" * 72)
        print()

        # Find shunya tenant + admin user
        tenant = db.session.query(Tenant).filter_by(slug="shunya").first()
        if not tenant:
            print("❌ Tenant 'shunya' not found. Run seed_all.py first.")
            sys.exit(1)

        user = db.session.query(TeamMember).filter_by(
            tenant_id=tenant.id, email="admin@shunya.io"
        ).first()
        if not user:
            print("❌ Admin user (admin@shunya.io) not found on 'shunya' tenant.")
            sys.exit(1)

        print(f"  Tenant: {tenant.company_name} (slug={tenant.slug}, id={tenant.id})")
        print(f"  User:   {user.email} (id={user.id})")
        print()

        modules = [
            ("1. RELATIONSHIPS", seed_relationships),
            ("2. HR", seed_hr),
            ("3. MARKETING", seed_marketing),
            ("4. SUPPORT", seed_support),
            ("5. SUPPLY CHAIN", seed_supply_chain),
            ("6. FIELD SERVICES", seed_field_services),
            ("7. LEGAL", seed_legal),
            ("8. SALES CRM", seed_sales_crm),
            ("9. FINANCE", seed_finance),
        ]

        for name, func in modules:
            print(f"── {name} ──")
            try:
                func(tenant, user)
            except Exception as e:
                print(f"  ❌ Error seeding {name}: {e}")
                db.session.rollback()
                import traceback
                traceback.print_exc()
        print()

        # Summary
        print("=" * 72)
        print("  📊 SEED COMPLETE — SUMMARY")
        print("=" * 72)

        # Count entities by definition type
        def_counts = db.session.query(
            EntityDefinition.type, db.func.count(Entity.id)
        ).join(Entity, Entity.definition_id == EntityDefinition.id, isouter=True
        ).filter(
            EntityDefinition.tenant_id == tenant.id
        ).group_by(EntityDefinition.type).order_by(EntityDefinition.type).all()

        total_entities = 0
        for etype, count in def_counts:
            print(f"    {etype:25s} → {count:4d}")
            total_entities += count
        print(f"    {'─' * 35}")
        print(f"    {'TOTAL ENTITIES':25s} → {total_entities:4d}")

        # Also count Relationship models
        rel_count = db.session.query(Relationship).filter_by(tenant_id=tenant.id).count()
        opp_count = db.session.query(Opportunity).filter_by(tenant_id=tenant.id).count()
        exp_count = db.session.query(Experience).filter_by(tenant_id=tenant.id).count()
        payment_count = db.session.query(Payment).filter_by(tenant_id=tenant.id).count()
        invoice_count = db.session.query(Invoice).filter_by(tenant_id=tenant.id).count()
        supplier_count = db.session.query(Supplier).filter_by(tenant_id=tenant.id).count()

        print(f"    {'Relationships (direct)':25s} → {rel_count:4d}")
        print(f"    {'Opportunities (direct)':25s} → {opp_count:4d}")
        print(f"    {'Experiences (direct)':25s} → {exp_count:4d}")
        print(f"    {'Payments (direct)':25s} → {payment_count:4d}")
        print(f"    {'Invoices (direct)':25s} → {invoice_count:4d}")
        print(f"    {'Suppliers (direct)':25s} → {supplier_count:4d}")
        print()
        print("  ✅ All modules seeded successfully!")


if __name__ == "__main__":
    main()