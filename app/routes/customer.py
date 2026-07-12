"""Shunya Customer Routes — Relationship Dashboard, Brief, Timeline."""
from flask import Blueprint, render_template, jsonify, g, request, redirect, url_for
from datetime import datetime
from app import db
from app.models import Customer, Opportunity, CustomerPreference, OpportunityActivity
from app.routes.auth import login_required
from app.shunya.customer import RelationshipBrief

customer_bp = Blueprint("customer", __name__, url_prefix="/customers")


@customer_bp.route("")
@login_required
def customer_list():
    """List all customers for this tenant."""
    customers = db.session.query(Customer).filter(
        Customer.tenant_id == g.tenant.id,
        Customer.status != "churned",
    ).order_by(Customer.updated_at.desc()).all()

    results = []
    for c in customers:
        opp_count = db.session.query(db.func.count(Opportunity.id)).filter(
            Opportunity.customer_id == c.id,
            Opportunity.status == "open",
        ).scalar() or 0

        brief = RelationshipBrief(c)
        next_action = brief.get_suggested_next_action()

        results.append({
            "id": c.id,
            "name": c.name,
            "email": c.email,
            "phone": c.phone,
            "relationship_health": c.relationship_health,
            "total_experiences": c.total_experiences,
            "active_opportunities": opp_count,
            "last_interaction": c.last_meaningful_interaction.isoformat()[:10]
                if c.last_meaningful_interaction else None,
            "next_action": next_action["action"] if next_action else None,
        })

    return render_template("customers/list.html",
        customers=results,
        total=len(results),
    )


@customer_bp.route("/<int:customer_id>")
@login_required
def customer_detail(customer_id: int):
    """Full relationship dashboard for a single customer."""
    customer = db.session.query(Customer).filter(
        Customer.id == customer_id,
        Customer.tenant_id == g.tenant.id,
    ).first()
    if not customer:
        return "Customer not found", 404

    brief = RelationshipBrief(customer).build()

    return render_template("customers/dashboard.html",
        customer=customer,
        brief=brief,
    )


@customer_bp.route("/<int:customer_id>/brief")
@login_required
def customer_brief_api(customer_id: int):
    """API endpoint: full Relationship Brief as JSON."""
    customer = db.session.query(Customer).filter(
        Customer.id == customer_id,
        Customer.tenant_id == g.tenant.id,
    ).first()
    if not customer:
        return jsonify({"error": "Customer not found"}), 404

    return jsonify(RelationshipBrief(customer).build())


@customer_bp.route("/<int:customer_id>/timeline")
@login_required
def customer_timeline_api(customer_id: int):
    """API endpoint: lifetime journey timeline as JSON."""
    customer = db.session.query(Customer).filter(
        Customer.id == customer_id,
        Customer.tenant_id == g.tenant.id,
    ).first()
    if not customer:
        return jsonify({"error": "Customer not found"}), 404

    journey = RelationshipBrief(customer).get_lifetime_journey()
    return jsonify({"journey": journey})


@customer_bp.route("/new", methods=["GET", "POST"])
@login_required
def customer_new():
    """Create a new customer record."""
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        if not name:
            return "Name is required", 400

        customer = Customer(
            tenant_id=g.tenant.id,
            name=name,
            email=request.form.get("email", "").strip() or None,
            phone=request.form.get("phone", "").strip() or None,
            preferred_channel=request.form.get("preferred_channel", "whatsapp"),
            relationship_health="new",
            relationship_tenure_years=0,
            created_by=g.user.id,
        )
        db.session.add(customer)
        db.session.commit()

        return redirect(url_for("customer.customer_detail", customer_id=customer.id))

    return render_template("customers/form.html", customer=None, is_new=True)


@customer_bp.route("/api/summary")
@login_required
def customer_summary():
    """JSON summary of customer stats for dashboard widgets."""
    total = db.session.query(db.func.count(Customer.id)).filter(
        Customer.tenant_id == g.tenant.id,
        Customer.status != "churned",
    ).scalar() or 0

    new_customers = db.session.query(db.func.count(Customer.id)).filter(
        Customer.tenant_id == g.tenant.id,
        Customer.relationship_health == "new",
    ).scalar() or 0

    at_risk = db.session.query(db.func.count(Customer.id)).filter(
        Customer.tenant_id == g.tenant.id,
        Customer.relationship_health == "at_risk",
    ).scalar() or 0

    active_opps = db.session.query(db.func.count(Opportunity.id)).filter(
        Opportunity.tenant_id == g.tenant.id,
        Opportunity.status == "open",
    ).scalar() or 0

    total_referrals = db.session.query(db.func.coalesce(
        db.func.sum(Customer.total_referrals), 0
    )).filter(
        Customer.tenant_id == g.tenant.id,
    ).scalar() or 0

    return jsonify({
        "total_customers": total,
        "new_customers": new_customers,
        "at_risk": at_risk,
        "active_opportunities": active_opps,
        "total_referrals": total_referrals,
    })


# ---------------------------------------------------------------------------
# Seed data
# ---------------------------------------------------------------------------

@customer_bp.route("/seed")
@login_required
def seed_customers():
    """Seed sample customers + opportunities for demo/testing."""
    from datetime import timedelta

    existing = db.session.query(db.func.count(Customer.id)).filter(
        Customer.tenant_id == g.tenant.id,
    ).scalar() or 0
    if existing > 5:
        return jsonify({"message": "Already seeded", "count": existing})

    now = datetime.utcnow()

    sample_customers = [
        {
            "name": "Rajat Nishesh",
            "email": "nishesh@panchi.club",
            "phone": "+91-9876543210",
            "tenure": 6,
            "experiences": 8,
            "referrals": 3,
            "health": "strong",
            "style": "concise",
            "channel": "whatsapp",
            "last_interaction": now - timedelta(days=18),
            "preferences": [
                ("hotel_location", "central_walkable", "high", "observed",
                 [{"trip": "Thailand 2022", "action": "selected city centre hotel"},
                  {"trip": "Dubai 2023", "action": "selected Downtown hotel"},
                  {"trip": "Bali 2025", "action": "selected central Ubud location"}]),
                ("travel_pace", "comfortable", "high", "observed",
                 [{"trip": "Thailand 2022", "action": "requested itinerary reduction"},
                  {"trip": "Dubai 2023", "action": "reduced activities"}]),
                ("decision_style", "quick_decision", "medium", "observed",
                 [{"trip": "Dubai 2023", "action": "decided within 3 days of proposal"}]),
                ("transfer_preference", "private_transfer", "high", "stated",
                 [{"trip": "Dubai 2023", "action": "selected private transfer"}]),
            ],
            "travellers": {
                "self": {"name": "Rajat Nishesh", "birthdate": "1992-04-15"},
                "spouse": {"name": "Ananya Nishesh", "birthdate": "1994-08-22"},
                "children": [{"name": "Aarav Nishesh", "birthdate": "2020-01-10"}],
            },
            "opportunities": [
                {"title": "Dubai Family Holiday", "destination": "Dubai",
                 "stage": "outcome", "status": "won", "budget": 350000, "actual": 385000,
                 "start": now - timedelta(days=365), "end": now - timedelta(days=350),
                 "outcome": "Great trip overall. Transfer from airport was delayed 45 minutes.",
                 "rating": 4,
                 "lessons": ["Confirm transfer in advance", "Dubai summer heat matters"]},
                {"title": "Bali Getaway", "destination": "Bali",
                 "stage": "lost", "status": "lost", "budget": 250000,
                 "start": now - timedelta(days=120),
                 "outcome": "Dates changed — customer decided to postpone.",
                 "rating": None},
                {"title": "Japan Family Holiday", "destination": "Japan",
                 "stage": "enquiry", "status": "open", "budget": 600000,
                 "start": now + timedelta(days=90),
                 "travellers": [{"role": "self", "name": "Rajat"}, {"role": "spouse", "name": "Ananya"},
                                {"role": "child", "name": "Aarav"}]},
            ],
        },
        {
            "name": "Mitesh Yadav",
            "email": "mitesh@panchi.club",
            "phone": "+91-9876543211",
            "tenure": 2,
            "experiences": 3,
            "referrals": 1,
            "health": "established",
            "style": "detailed",
            "channel": "whatsapp",
            "last_interaction": now - timedelta(days=7),
            "preferences": [
                ("hotel_location", "resort_outskirts", "medium", "observed",
                 [{"trip": "Goa 2024", "action": "selected beach resort"}],
                 [{"trip": "Manali 2025", "note": "selected city centre — reason: winter access"}]),
            ],
            "travellers": {
                "self": {"name": "Mitesh Yadav", "birthdate": "1990-11-03"},
            },
            "opportunities": [
                {"title": "Europe Backpacking", "destination": "Europe (Multiple)",
                 "stage": "planning", "status": "open", "budget": 450000,
                 "start": now + timedelta(days=60),
                 "travellers": [{"role": "self", "name": "Mitesh"}, {"role": "friend", "name": "Rahul"}]},
            ],
        },
        {
            "name": "Priya Sharma",
            "email": "priya@example.com",
            "phone": "+91-9876543212",
            "tenure": 1,
            "experiences": 1,
            "referrals": 0,
            "health": "learning",
            "style": "formal",
            "channel": "email",
            "last_interaction": now - timedelta(days=45),
            "preferences": [],
            "travellers": {
                "self": {"name": "Priya Sharma", "birthdate": "1988-06-20"},
                "spouse": {"name": "Amit Sharma", "birthdate": "1986-03-14"},
                "parents": [{"name": "Mr. Sharma Sr.", "birthdate": "1955-09-01"}],
            },
            "opportunities": [
                {"title": "Parents' Pilgrimage Trip", "destination": "Haridwar-Rishikesh",
                 "stage": "proposal", "status": "open", "budget": 85000,
                 "start": now + timedelta(days=30)},
            ],
        },
        {
            "name": "Vikram Singh",
            "email": "vikram@singh.co",
            "phone": "+91-9876543213",
            "tenure": 3,
            "experiences": 5,
            "referrals": 2,
            "health": "strong",
            "style": "concise",
            "channel": "telegram",
            "last_interaction": now - timedelta(days=90),
            "preferences": [
                ("airline", "Emirates/Indigo", "high", "observed",
                 [{"trip": "Dubai 2023", "action": "flew Emirates"},
                  {"trip": "Singapore 2024", "action": "flew Indigo"},
                  {"trip": "Thailand 2024", "action": "flew Indigo"}]),
                ("room_category", "suite", "high", "observed",
                 [{"trip": "Dubai 2023", "action": "booked suite"},
                  {"trip": "Singapore 2024", "action": "booked executive room"},
                  {"trip": "Thailand 2024", "action": "booked suite"}]),
            ],
            "travellers": {
                "self": {"name": "Vikram Singh", "birthdate": "1985-02-28"},
                "spouse": {"name": "Neha Singh", "birthdate": "1988-07-15"},
                "children": [{"name": "Karan Singh", "birthdate": "2016-12-01"},
                              {"name": "Anaya Singh", "birthdate": "2019-04-20"}],
            },
            "opportunities": [],
        },
        {
            "name": "Ananya Kapoor",
            "email": "ananya@kapoor.co",
            "phone": "+91-9876543214",
            "tenure": 0,
            "experiences": 0,
            "referrals": 0,
            "health": "new",
            "style": "casual",
            "channel": "whatsapp",
            "last_interaction": now - timedelta(days=2),
            "preferences": [],
            "travellers": {"self": {"name": "Ananya Kapoor", "birthdate": "1995-11-18"}},
            "opportunities": [
                {"title": "Honeymoon Planning", "destination": "Maldives or Bali",
                 "stage": "enquiry", "status": "open", "budget": 300000,
                 "start": now + timedelta(days=120)},
            ],
        },
    ]

    for data in sample_customers:
        customer = Customer(
            tenant_id=g.tenant.id,
            name=data["name"],
            email=data["email"],
            phone=data["phone"],
            relationship_tenure_years=data["tenure"],
            total_experiences=data.get("experiences", 0),
            total_referrals=data.get("referrals", 0),
            relationship_health=data["health"],
            communication_style=data.get("style", ""),
            preferred_channel=data.get("channel", "whatsapp"),
            last_meaningful_interaction=data["last_interaction"],
            traveller_graph=data["travellers"],
            created_by=g.user.id,
        )
        db.session.add(customer)
        db.session.flush()

        # Preferences
        for pref_data in data.get("preferences", []):
            pref = CustomerPreference(
                tenant_id=g.tenant.id,
                customer_id=customer.id,
                preference_type=pref_data[0],
                value=pref_data[1],
                confidence=pref_data[2],
                source=pref_data[3],
                evidence=pref_data[4],
                contradictions=pref_data[5] if len(pref_data) > 5 else [],
                last_confirmed=data["last_interaction"],
            )
            db.session.add(pref)

        # Opportunities
        for opp_data in data.get("opportunities", []):
            opp = Opportunity(
                tenant_id=g.tenant.id,
                customer_id=customer.id,
                code=f"OPP-{customer.id:04d}-{data['opportunities'].index(opp_data)+1:02d}",
                title=opp_data["title"],
                destination=opp_data.get("destination"),
                stage=opp_data["stage"],
                status=opp_data.get("status", "open"),
                estimated_budget=opp_data.get("budget"),
                actual_cost=opp_data.get("actual"),
                travellers=opp_data.get("travellers", []),
                traveller_count=len(opp_data.get("travellers", [{"role": "self"}])),
                outcome_notes=opp_data.get("outcome", ""),
                outcome_rating=opp_data.get("rating"),
                lessons_learned=opp_data.get("lessons", []),
                enquiry_date=opp_data.get("start") or now,
                created_by=g.user.id,
            )
            db.session.add(opp)
            db.session.flush()

            # Activity log entry
            stage_label = opp_data["stage"].replace("_", " ").title()
            if opp_data.get("status") == "won":
                activity_type = "feedback"
            elif opp_data.get("status") == "lost":
                activity_type = "stage_change"
            else:
                activity_type = "enquiry"

            act = OpportunityActivity(
                tenant_id=g.tenant.id,
                opportunity_id=opp.id,
                activity_type=activity_type,
                title=f"{'Created' if activity_type == 'enquiry' else 'Completed'} {stage_label} for {opp_data['title']}",
                description=opp_data.get("outcome", "New opportunity created"),
                created_by=g.user.id,
            )
            db.session.add(act)

    db.session.commit()

    return jsonify({"message": "Seeded", "count": len(sample_customers)})