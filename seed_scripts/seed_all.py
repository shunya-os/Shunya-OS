"""Seed the default business ontologies for Shunya OS."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

os.environ.setdefault("FLASK_ENV", "development")
from app import create_app, db
from app.models import Tenant, TeamMember, EntityDefinition

app = create_app("development")

with app.app_context():
    db.create_all()

    # Check if admin already exists
    admin_user = TeamMember.query.filter_by(email="admin@shunya.io").first()
    if admin_user:
        print("Admin already seeded. Skipping.")
        sys.exit(0)

    # Create Shunya admin tenant
    shunya = Tenant(
        company_name="Shunya OS",
        slug="shunya",
        business_type="multi_brand",
        plan="enterprise",
        max_team_members=1000,
        max_storage_mb=100000,
        max_ai_calls_daily=10000,
    )
    db.session.add(shunya)
    db.session.flush()

    # Create admin user
    admin = TeamMember(
        tenant_id=shunya.id,
        name="Admin",
        email="admin@shunya.io",
        role="admin",
    )
    admin.set_password("admin123")
    db.session.add(admin)

    # Create demo tenant
    demo = Tenant(
        company_name="Panchi Club",
        slug="panchi-club",
        business_type="travel",
        theme_config={"primary_color": "#2563eb", "accent_color": "#7c3aed", "icon": "✈️"},
    )
    db.session.add(demo)
    db.session.flush()

    # Team member for demo
    demo_user = TeamMember(
        tenant_id=demo.id,
        name="Rajat",
        email="rajat@panchi.club",
        role="admin",
    )
    demo_user.set_password("demo123")
    db.session.add(demo_user)

    # =========================================================================
    # Seed Default Entity Definitions for Demo Tenant (Travel)
    # =========================================================================

    travel_defs = [
        EntityDefinition(
            tenant_id=demo.id, type="lead", label="Lead", label_plural="Leads", icon="📋",
            layout="kanban",
            primary_field="customer_name",
            searchable_fields=["customer_name", "destination", "phone"],
            statuses=["new", "proposal", "negotiation", "booked", "completed", "cancelled"],
            schema=[
                {"name": "customer_name", "label": "Customer Name", "type": "text", "required": True},
                {"name": "phone", "label": "Phone", "type": "text"},
                {"name": "email", "label": "Email", "type": "text"},
                {"name": "destination", "label": "Destination", "type": "text"},
                {"name": "pax", "label": "Pax", "type": "text"},
                {"name": "dates", "label": "Travel Dates", "type": "text"},
                {"name": "budget", "label": "Budget (₹)", "type": "number"},
                {"name": "assigned_to", "label": "Assigned To", "type": "text"},
                {"name": "notes", "label": "Notes", "type": "textarea"},
            ]
        ),
        EntityDefinition(
            tenant_id=demo.id, type="booking", label="Booking", label_plural="Bookings", icon="🎫",
            layout="table",
            primary_field="customer_name",
            searchable_fields=["customer_name", "booking_ref"],
            statuses=["confirmed", "in_progress", "completed", "cancelled"],
            schema=[
                {"name": "customer_name", "label": "Customer Name", "type": "text", "required": True},
                {"name": "booking_ref", "label": "Booking Ref", "type": "text"},
                {"name": "destination", "label": "Destination", "type": "text"},
                {"name": "check_in", "label": "Check In", "type": "date"},
                {"name": "check_out", "label": "Check Out", "type": "date"},
                {"name": "total_amount", "label": "Total Amount", "type": "number"},
            ]
        ),
        EntityDefinition(
            tenant_id=demo.id, type="itinerary", label="Itinerary", label_plural="Itineraries", icon="🗺️",
            layout="cards",
            primary_field="title",
            searchable_fields=["title", "destination"],
            statuses=["draft", "sent", "approved", "final"],
            schema=[
                {"name": "title", "label": "Title", "type": "text", "required": True},
                {"name": "destination", "label": "Destination", "type": "text"},
                {"name": "duration", "label": "Duration (days)", "type": "number"},
                {"name": "content", "label": "Itinerary Content", "type": "textarea"},
            ]
        ),
        EntityDefinition(
            tenant_id=demo.id, type="supplier", label="Supplier", label_plural="Suppliers", icon="🏢",
            layout="table",
            primary_field="name",
            searchable_fields=["name", "category", "city"],
            statuses=["active", "inactive"],
            schema=[
                {"name": "name", "label": "Name", "type": "text", "required": True},
                {"name": "category", "label": "Category", "type": "dropdown", "options": ["hotel", "flight", "transport", "activity", "visa", "venue"]},
                {"name": "contact", "label": "Contact Person", "type": "text"},
                {"name": "email", "label": "Email", "type": "text"},
                {"name": "phone", "label": "Phone", "type": "text"},
                {"name": "city", "label": "City", "type": "text"},
                {"name": "gstin", "label": "GSTIN", "type": "text"},
            ]
        ),
    ]

    for d in travel_defs:
        db.session.add(d)

    # =========================================================================
    # Seed Default Entity Definitions for Healthcare
    # =========================================================================

    health_defs = [
        EntityDefinition(
            tenant_id=demo.id, type="patient", label="Patient", label_plural="Patients", icon="👤",
            layout="kanban",
            primary_field="patient_name",
            searchable_fields=["patient_name", "phone"],
            statuses=["new", "consultation", "diagnosis", "treatment", "follow_up", "recovered"],
            schema=[
                {"name": "patient_name", "label": "Patient Name", "type": "text", "required": True},
                {"name": "age", "label": "Age", "type": "number"},
                {"name": "blood_group", "label": "Blood Group", "type": "dropdown",
                 "options": ["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"]},
                {"name": "phone", "label": "Phone", "type": "text"},
                {"name": "symptoms", "label": "Symptoms", "type": "textarea"},
                {"name": "assigned_doctor", "label": "Doctor", "type": "text"},
            ]
        ),
        EntityDefinition(
            tenant_id=demo.id, type="appointment", label="Appointment", label_plural="Appointments", icon="📅",
            layout="calendar",
            primary_field="patient_name",
            searchable_fields=["patient_name"],
            statuses=["scheduled", "in_progress", "completed", "missed"],
            schema=[
                {"name": "patient_name", "label": "Patient Name", "type": "text", "required": True},
                {"name": "doctor", "label": "Doctor", "type": "text"},
                {"name": "date", "label": "Date", "type": "date"},
                {"name": "time", "label": "Time", "type": "text"},
                {"name": "reason", "label": "Reason", "type": "textarea"},
            ]
        ),
    ]

    for d in health_defs:
        db.session.add(d)

    # =========================================================================
    # Seed Default Entity Definitions for Customer Support
    # =========================================================================

    from app.shunya.support import SUPPORT_ENTITY_TYPES

    for etype, config in SUPPORT_ENTITY_TYPES.items():
        existing = EntityDefinition.query.filter_by(tenant_id=demo.id, type=etype).first()
        if existing:
            continue
        definition = EntityDefinition(
            tenant_id=demo.id,
            type=etype,
            label=config["label"],
            label_plural=f"{config['label']}s",
            icon=config["icon"],
            schema=config["schema"],
            statuses=config["statuses"],
            layout=config["layout"],
            searchable_fields=config["searchable_fields"],
            primary_field=config["schema"][0]["name"] if config["schema"] else "name",
        )
        db.session.add(definition)

    db.session.commit()
    print("✅ Seed complete!")
    print(f"   Admin tenant: {shunya.slug} (admin@shunya.io / admin123)")
    print(f"   Demo tenant: {demo.slug} (rajat@panchi.club / demo123)")
    print(f"   Entity types created: {EntityDefinition.query.count()}")
