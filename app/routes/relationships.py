"""Shunya Relationship Routes — Relationship Dashboard, Brief, Timeline, Seed."""
from flask import Blueprint, render_template, jsonify, g, request, redirect, url_for
from datetime import datetime
from app import db
from app.models import (
    Person, Relationship, RelationshipPreference, Household,
    Opportunity, OpportunityActivity, Experience, Observation, Outcome, LearningCandidate
)
from app.routes.auth import login_required
from app.shunya.advisory import AdvisoryContext

relationships_bp = Blueprint("relationships", __name__, url_prefix="/relationships")


# ---------------------------------------------------------------------------
# List
# ---------------------------------------------------------------------------

@relationships_bp.route("")
@login_required
def relationship_list():
    """List all relationships for this tenant."""
    rels = db.session.query(Relationship).filter(
        Relationship.tenant_id == g.tenant.id,
        Relationship.status != "churned",
    ).order_by(Relationship.updated_at.desc()).all()

    results = []
    for r in rels:
        active_opps = db.session.query(db.func.count(Opportunity.id)).filter(
            Opportunity.relationship_id == r.id,
            Opportunity.status == "open",
        ).scalar() or 0

        next_action = AdvisoryContext.suggest_next_for_relationship(r.id)
        person = r.person

        results.append({
            "id": r.id,
            "person_id": person.id if person else None,
            "name": r.display_name or (person.name if person else "Unknown"),
            "email": r.email or (person.email if person else ""),
            "phone": r.phone or (person.phone if person else ""),
            "health": r.health,
            "total_experiences": r.total_experiences,
            "total_referrals": r.total_referrals,
            "active_opportunities": active_opps,
            "last_interaction": r.last_meaningful_interaction.isoformat()[:10]
                if r.last_meaningful_interaction else None,
            "next_action": next_action["action"] if next_action else None,
        })

    return render_template("relationships/list.html",
        relationships=results,
        total=len(results),
    )


# ---------------------------------------------------------------------------
# Detail — Full Relationship Dashboard
# ---------------------------------------------------------------------------

@relationships_bp.route("/<int:rel_id>")
@login_required
def relationship_detail(rel_id: int):
    """Full relationship dashboard with Advisory Context."""
    rel = db.session.query(Relationship).filter(
        Relationship.id == rel_id,
        Relationship.tenant_id == g.tenant.id,
    ).first()
    if not rel:
        return "Relationship not found", 404

    advice = AdvisoryContext.for_relationship(rel.id)

    return render_template("relationships/dashboard.html",
        relationship=rel,
        person=rel.person,
        advice=advice,
    )


# ---------------------------------------------------------------------------
# API Endpoints
# ---------------------------------------------------------------------------

@relationships_bp.route("/<int:rel_id>/advice")
@login_required
def relationship_advice_api(rel_id: int):
    """API: full Advisory Context as JSON."""
    rel = db.session.query(Relationship).filter(
        Relationship.id == rel_id,
        Relationship.tenant_id == g.tenant.id,
    ).first()
    if not rel:
        return jsonify({"error": "Relationship not found"}), 404
    return jsonify(AdvisoryContext.for_relationship(rel.id))


@relationships_bp.route("/<int:rel_id>/journey")
@login_required
def relationship_journey_api(rel_id: int):
    """API: lifetime journey as JSON."""
    journey = AdvisoryContext.lifetime_journey(rel_id)
    return jsonify({"journey": journey})


@relationships_bp.route("/api/summary")
@login_required
def relationship_summary():
    """JSON summary of relationship stats."""
    total = db.session.query(db.func.count(Relationship.id)).filter(
        Relationship.tenant_id == g.tenant.id,
        Relationship.status != "churned",
    ).scalar() or 0

    new = db.session.query(db.func.count(Relationship.id)).filter(
        Relationship.tenant_id == g.tenant.id,
        Relationship.health == "new",
    ).scalar() or 0

    at_risk = db.session.query(db.func.count(Relationship.id)).filter(
        Relationship.tenant_id == g.tenant.id,
        Relationship.health == "at_risk",
    ).scalar() or 0

    active_opps = db.session.query(db.func.count(Opportunity.id)).filter(
        Opportunity.tenant_id == g.tenant.id,
        Opportunity.status == "open",
    ).scalar() or 0

    return jsonify({
        "total_relationships": total,
        "new": new,
        "at_risk": at_risk,
        "active_opportunities": active_opps,
    })


# ---------------------------------------------------------------------------
# Create
# ---------------------------------------------------------------------------

@relationships_bp.route("/new", methods=["GET", "POST"])
@login_required
def relationship_new():
    """Create a new person + relationship."""
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        if not name:
            return "Name is required", 400

        email = request.form.get("email", "").strip() or None
        phone = request.form.get("phone", "").strip() or None

        # Find or create person
        person = None
        if email:
            person = db.session.query(Person).filter_by(email=email).first()
        if not person and phone:
            person = db.session.query(Person).filter_by(phone=phone).first()
        if not person:
            person = Person(name=name, email=email, phone=phone)
            db.session.add(person)
            db.session.flush()

        # Create relationship
        rel = Relationship(
            tenant_id=g.tenant.id,
            person_id=person.id,
            display_name=name,
            email=email,
            phone=phone,
            health="new",
            tenure_years=0,
            preferred_channel=request.form.get("preferred_channel", "whatsapp"),
            created_by=g.user.id,
        )
        db.session.add(rel)
        db.session.commit()

        return redirect(url_for("relationships.relationship_detail", rel_id=rel.id))

    return render_template("relationships/form.html", is_new=True)


# ---------------------------------------------------------------------------
# Seed Data
# ---------------------------------------------------------------------------

@relationships_bp.route("/seed")
@login_required
def seed_relationships():
    """Seed sample data for the new Person→Relationship→Opportunity→Experience architecture."""
    from datetime import timedelta

    existing = db.session.query(db.func.count(Relationship.id)).filter(
        Relationship.tenant_id == g.tenant.id,
    ).scalar() or 0
    if existing > 3:
        return jsonify({"message": "Already seeded", "count": existing})

    now = datetime.utcnow()

    # ----- RAJAT NISHESH -----
    raj = Person(
        name="Rajat Nishesh", email="nishesh@panchi.club", phone="+91-9876543210",
        birthdate="1992-04-15", nationality="IN",
    )
    db.session.add(raj)
    db.session.flush()

    rel_raj = Relationship(
        tenant_id=g.tenant.id, person_id=raj.id,
        display_name="Rajat Nishesh", email=raj.email, phone=raj.phone,
        tenure_years=6, health="strong", total_experiences=8, total_referrals=3,
        preferred_channel="whatsapp", communication_style="concise",
        traveller_graph={
            "self": {"person_id": raj.id, "name": "Rajat Nishesh", "birthdate": "1992-04-15"},
            "spouse": {"name": "Ananya Nishesh", "birthdate": "1994-08-22"},
            "children": [{"name": "Aarav Nishesh", "birthdate": "2020-01-10"}],
        },
        last_meaningful_interaction=now - timedelta(days=18),
        created_by=g.user.id,
    )
    db.session.add(rel_raj)
    db.session.flush()

    # Preferences
    prefs_raj = [
        RelationshipPreference(tenant_id=g.tenant.id, relationship_id=rel_raj.id,
            preference_type="hotel_location", value="central_walkable", confidence="high",
            source="observed",
            evidence=[{"opportunity": "Thailand 2022", "action": "selected city centre hotel"},
                       {"opportunity": "Dubai 2023", "action": "selected Downtown hotel"},
                       {"opportunity": "Bali 2025", "action": "selected central Ubud"}],
            note="Consistently chooses central locations"),
        RelationshipPreference(tenant_id=g.tenant.id, relationship_id=rel_raj.id,
            preference_type="travel_pace", value="comfortable", confidence="high",
            source="observed",
            evidence=[{"opportunity": "Thailand 2022", "action": "requested itinerary reduction"},
                       {"opportunity": "Dubai 2023", "action": "reduced activities from initial plan"}],
            last_confirmed=now - timedelta(days=18)),
        RelationshipPreference(tenant_id=g.tenant.id, relationship_id=rel_raj.id,
            preference_type="decision_style", value="quick_decision", confidence="medium",
            source="observed",
            evidence=[{"opportunity": "Dubai 2023", "action": "decided within 3 days of proposal"}],
            last_confirmed=now - timedelta(days=365)),
        RelationshipPreference(tenant_id=g.tenant.id, relationship_id=rel_raj.id,
            preference_type="transfer_preference", value="private_transfer", confidence="high",
            source="stated",
            evidence=[{"opportunity": "Dubai 2023", "action": "selected private transfer — had delay issue"}],
            last_confirmed=now - timedelta(days=365)),
    ]
    for p in prefs_raj:
        db.session.add(p)
    db.session.flush()

    # Opportunity: Japan Family Holiday (active — enquiry)
    opp_japan = Opportunity(
        tenant_id=g.tenant.id, relationship_id=rel_raj.id,
        code="OPP-0001-01", title="Japan Family Holiday", destination="Japan",
        stage="enquiry", status="open", intent_description="Family holiday — comfortable exploration",
        experience_mood="exploring + leisure",
        estimated_budget=600000, currency="INR", traveller_count=3,
        participants=[
            {"person_id": raj.id, "role": "traveller", "name": "Rajat"},
            {"role": "traveller", "name": "Ananya"},
            {"role": "traveller", "name": "Aarav"},
        ],
        decision_maker="Rajat Nishesh", priority="high", probability=65, risk="low",
        assigned_to=g.user.id,
        enquiry_date=now - timedelta(days=3),
        created_by=g.user.id,
    )
    db.session.add(opp_japan)
    db.session.flush()
    db.session.add(OpportunityActivity(
        tenant_id=g.tenant.id, opportunity_id=opp_japan.id,
        activity_type="enquiry", title="New enquiry: Japan Family Holiday",
        description="Customer asked about Japan in family group", created_by=g.user.id,
    ))

    # Experience: Dubai 2023 (completed)
    exp_dubai = Experience(
        tenant_id=g.tenant.id, relationship_id=rel_raj.id,
        title="Dubai Family Holiday 2023",
        experience_type="trip",
        expectations={"hotels": "Marriott Downtown", "flights": "EK507", "transfers": "Private Transfer"},
        delivered_reality={"hotels": "Marriott Downtown (upgraded)", "flights": "EK507 (on time)",
                          "transfers": "Private — driver 35min late"},
        events=[{"date": "2023-03-15", "type": "checkin", "status": "smooth"},
                {"date": "2023-03-15", "type": "transfer", "status": "issue", "detail": "35min delay at arrival"}],
        exceptions=[{"component": "transfer", "issue": "driver delay", "severity": "medium",
                     "detail": "Driver arrived 35 minutes late. Customer called twice. Child was tired.",
                     "recovery": "compensated with upgrade"}],
        feedback="Great trip overall. Transfer from airport was delayed — that was frustrating with a tired child.",
        satisfaction_signals=[
            {"source": "survey", "metric": "overall", "score": 4},
            {"source": "message", "text": "transfer was frustrating", "sentiment": "negative"},
        ],
        overall_rating=4, would_recommend=True,
        start_date=now - timedelta(days=365), end_date=now - timedelta(days=358),
        created_by=g.user.id,
    )
    db.session.add(exp_dubai)
    db.session.flush()

    # Outcome for Dubai
    db.session.add(Outcome(
        tenant_id=g.tenant.id, subject_type="experience", subject_id=exp_dubai.id,
        experience_id=exp_dubai.id,
        goal="Family holiday — comfortable, memorable, stress-free",
        expected_outcome="Smooth luxury family trip",
        actual_outcome="Great trip overall but airport transfer was frustrating",
        result="partial",
        reason="Transfer delay materially affected arrival experience",
        customer_impact="Frustration at arrival — child was tired",
        lessons=[{"lesson": "Confirm transfer logistics 24h before arrival", "category": "ops", "priority": "high"},
                 {"lesson": "Pre-book premium transfer for late arrivals with children", "category": "ops", "priority": "medium"}],
    ))

    # Experience: Thailand 2022
    exp_thai = Experience(
        tenant_id=g.tenant.id, relationship_id=rel_raj.id,
        title="Thailand Honeymoon 2022",
        experience_type="trip",
        expectations={"hotels": "City Centre Hotels", "flights": "Air Asia"},
        delivered_reality={"hotels": "City Centre (all locations)", "flights": "On time"},
        events=[{"date": "2022-06-10", "type": "checkin", "status": "smooth"}],
        overall_rating=5, would_recommend=True,
        start_date=now - timedelta(days=750), end_date=now - timedelta(days=740),
        created_by=g.user.id,
    )
    db.session.add(exp_thai)
    db.session.flush()

    db.session.add(Outcome(
        tenant_id=g.tenant.id, subject_type="experience", subject_id=exp_thai.id,
        experience_id=exp_thai.id,
        goal="First international trip together",
        expected_outcome="Memorable honeymoon",
        actual_outcome="Excellent — all smooth",
        result="success",
    ))

    # ----- MITESH YADAV -----
    mit = Person(name="Mitesh Yadav", email="mitesh@panchi.club", phone="+91-9876543211")
    db.session.add(mit)
    db.session.flush()

    rel_mit = Relationship(
        tenant_id=g.tenant.id, person_id=mit.id,
        display_name="Mitesh Yadav", email=mit.email, phone=mit.phone,
        tenure_years=2, health="established", total_experiences=3, total_referrals=1,
        preferred_channel="whatsapp", communication_style="detailed",
        traveller_graph={"self": {"person_id": mit.id, "name": "Mitesh Yadav"}},
        last_meaningful_interaction=now - timedelta(days=7),
        created_by=g.user.id,
    )
    db.session.add(rel_mit)
    db.session.flush()

    db.session.add(RelationshipPreference(
        tenant_id=g.tenant.id, relationship_id=rel_mit.id,
        preference_type="hotel_location", value="resort_outskirts", confidence="medium",
        source="observed",
        evidence=[{"opportunity": "Goa 2024", "action": "selected beach resort"}],
        contradictions=[{"opportunity": "Manali 2025", "note": "selected city centre — winter access constrained choice"}],
        last_confirmed=now - timedelta(days=7),
    ))

    opp_europe = Opportunity(
        tenant_id=g.tenant.id, relationship_id=rel_mit.id,
        code="OPP-0002-01", title="Europe Backpacking", destination="Europe (Multiple)",
        stage="planning", status="open", intent_description="Multi-city backpacking trip",
        experience_mood="adventure",
        estimated_budget=450000, traveller_count=2,
        participants=[{"role": "traveller", "name": "Mitesh"}, {"role": "traveller", "name": "Rahul"}],
        priority="medium", probability=50,
        enquiry_date=now - timedelta(days=30), created_by=g.user.id,
    )
    db.session.add(opp_europe)
    db.session.flush()
    db.session.add(OpportunityActivity(
        tenant_id=g.tenant.id, opportunity_id=opp_europe.id,
        activity_type="stage_change", title="Moved to Planning", created_by=g.user.id,
    ))

    # ----- PRIYA SHARMA -----
    pri = Person(name="Priya Sharma", email="priya@example.com", phone="+91-9876543212",
                 birthdate="1988-06-20")
    db.session.add(pri)
    db.session.flush()

    rel_pri = Relationship(
        tenant_id=g.tenant.id, person_id=pri.id,
        display_name="Priya Sharma", email=pri.email, phone=pri.phone,
        tenure_years=1, health="learning", total_experiences=1,
        preferred_channel="email", communication_style="formal",
        traveller_graph={
            "self": {"person_id": pri.id, "name": "Priya Sharma"},
            "spouse": {"name": "Amit Sharma"},
            "parents": [{"name": "Mr. Sharma Sr."}],
        },
        last_meaningful_interaction=now - timedelta(days=45),
        created_by=g.user.id,
    )
    db.session.add(rel_pri)
    db.session.flush()

    opp_pilgrim = Opportunity(
        tenant_id=g.tenant.id, relationship_id=rel_pri.id,
        code="OPP-0003-01", title="Parents' Pilgrimage Trip", destination="Haridwar-Rishikesh",
        stage="proposal", status="open", estimated_budget=85000, traveller_count=3,
        participants=[{"role": "beneficiary", "name": "Parents"}, {"role": "coordinator", "name": "Priya"}],
        priority="high", probability=75, enquiry_date=now - timedelta(days=15),
        created_by=g.user.id,
    )
    db.session.add(opp_pilgrim)
    db.session.flush()
    db.session.add(OpportunityActivity(
        tenant_id=g.tenant.id, opportunity_id=opp_pilgrim.id,
        activity_type="quote_sent", title="Proposal shared with customer",
        created_by=g.user.id,
    ))

    # ----- VIKRAM SINGH (strong, dormant) -----
    vik = Person(name="Vikram Singh", email="vikram@singh.co", phone="+91-9876543213",
                 birthdate="1985-02-28")
    db.session.add(vik)
    db.session.flush()

    rel_vik = Relationship(
        tenant_id=g.tenant.id, person_id=vik.id,
        display_name="Vikram Singh", email=vik.email, phone=vik.phone,
        tenure_years=3, health="strong", total_experiences=5, total_referrals=2,
        preferred_channel="telegram", communication_style="concise",
        traveller_graph={
            "self": {"person_id": vik.id, "name": "Vikram Singh"},
            "spouse": {"name": "Neha Singh"}, "children": [{"name": "Karan"}, {"name": "Anaya"}],
        },
        last_meaningful_interaction=now - timedelta(days=90),
        created_by=g.user.id,
    )
    db.session.add(rel_vik)
    db.session.flush()

    db.session.add(RelationshipPreference(
        tenant_id=g.tenant.id, relationship_id=rel_vik.id,
        preference_type="airline", value="Emirates/Indigo", confidence="high",
        source="observed",
        evidence=[{"opportunity": "Dubai 2023", "action": "flew Emirates"},
                   {"opportunity": "Singapore 2024", "action": "flew Indigo"},
                   {"opportunity": "Thailand 2024", "action": "flew Indigo"}],
    ))
    db.session.add(RelationshipPreference(
        tenant_id=g.tenant.id, relationship_id=rel_vik.id,
        preference_type="room_category", value="suite", confidence="high",
        source="observed",
        evidence=[{"opportunity": "Dubai 2023", "action": "booked suite"},
                   {"opportunity": "Singapore 2024", "action": "booked executive room"},
                   {"opportunity": "Thailand 2024", "action": "booked suite"}],
    ))

    # Observation for Vikram (lapsed relationship detection)
    db.session.add(Observation(
        tenant_id=g.tenant.id,
        subject_type="relationship", subject_id=rel_vik.id,
        event="prolonged_inactivity",
        source="system", observer="Doctor",
        expected_state="active relationship",
        actual_state="90+ days since last interaction",
        delta="90 days of inactivity",
        severity="medium", confidence="high",
        metadata_json={"suggested_action": "Re-engage with a check-in"},
    ))

    # ----- ANANYA KAPOOR (new) -----
    ana = Person(name="Ananya Kapoor", email="ananya@kapoor.co", phone="+91-9876543214",
                 birthdate="1995-11-18")
    db.session.add(ana)
    db.session.flush()

    rel_ana = Relationship(
        tenant_id=g.tenant.id, person_id=ana.id,
        display_name="Ananya Kapoor", email=ana.email, phone=ana.phone,
        tenure_years=0, health="new", total_experiences=0,
        preferred_channel="whatsapp", communication_style="casual",
        traveller_graph={"self": {"person_id": ana.id, "name": "Ananya Kapoor"}},
        last_meaningful_interaction=now - timedelta(days=2),
        created_by=g.user.id,
    )
    db.session.add(rel_ana)
    db.session.flush()

    opp_honeymoon = Opportunity(
        tenant_id=g.tenant.id, relationship_id=rel_ana.id,
        code="OPP-0005-01", title="Honeymoon Planning", destination="Maldives or Bali",
        stage="enquiry", status="open", experience_mood="relaxing + romantic",
        estimated_budget=300000, traveller_count=2,
        participants=[{"role": "traveller", "name": "Ananya"}, {"role": "traveller", "name": "Partner"}],
        priority="medium", probability=40, risk="low",
        enquiry_date=now - timedelta(days=2), created_by=g.user.id,
    )
    db.session.add(opp_honeymoon)
    db.session.flush()
    db.session.add(OpportunityActivity(
        tenant_id=g.tenant.id, opportunity_id=opp_honeymoon.id,
        activity_type="enquiry", title="Honeymoon enquiry", created_by=g.user.id,
    ))

    db.session.commit()

    return jsonify({
        "message": "Seeded",
        "count": 5,
        "relationships": ["Rajat Nishesh", "Mitesh Yadav", "Priya Sharma", "Vikram Singh", "Ananya Kapoor"],
        "opportunities": 5,
        "experiences": 2,
        "preferences": 6,
        "observations": 1,
    })