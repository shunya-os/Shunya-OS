"""Shunya OS — Getting Started Wizard (first-run onboarding)."""
from flask import Blueprint, render_template, request, jsonify, redirect, url_for, g
from app import db
from app.models import Tenant, EntityDefinition, KnowledgeEntry, TeamMember
from app.routes.auth import login_required

onboarding_bp = Blueprint("onboarding", __name__, url_prefix="/onboarding")


# Business templates — pre-configured entity packs for common industries
BUSINESS_TEMPLATES = {
    "travel": {
        "label": "Travel Agency",
        "icon": "✈️",
        "description": "Leads, bookings, itineraries, suppliers, invoices",
        "entity_types": ["lead", "booking", "itinerary", "supplier", "invoice", "expense", "task"],
        "seed_knowledge": [
            {"q": "What is our cancellation policy?", "a": "Free cancellation up to 7 days before departure. 50% charge within 7 days. No refund after departure."},
            {"q": "What destinations do we offer?", "a": "We offer domestic and international packages including Bali, Thailand, Dubai, Europe, and Maldives."},
        ],
    },
    "healthcare": {
        "label": "Healthcare / Clinic",
        "icon": "🏥",
        "description": "Patients, appointments, prescriptions, billing, inventory",
        "entity_types": ["patient", "appointment", "prescription", "invoice", "expense", "task"],
        "seed_knowledge": [
            {"q": "What are our clinic hours?", "a": "Monday to Saturday: 9 AM to 7 PM. Sunday: 10 AM to 2 PM."},
            {"q": "What insurance providers do we accept?", "a": "We accept all major insurance providers. Please check with your provider for coverage details."},
        ],
    },
    "education": {
        "label": "School / Institute",
        "icon": "🎓",
        "description": "Students, courses, attendance, fees, staff",
        "entity_types": ["student", "course", "attendance", "invoice", "expense", "task"],
        "seed_knowledge": [
            {"q": "What is the admission process?", "a": "Submit application form, provide previous academic records, attend entrance test/interview, complete fee payment."},
            {"q": "What is the academic calendar?", "a": "The academic year runs from June to March with two semesters. Summer break in April-May."},
        ],
    },
    "retail": {
        "label": "Retail / E-Commerce",
        "icon": "🏪",
        "description": "Products, orders, customers, inventory, sales",
        "entity_types": ["product", "order", "customer", "invoice", "expense", "task"],
        "seed_knowledge": [
            {"q": "What is our return policy?", "a": "Free returns within 15 days of delivery. Items must be unused and in original packaging."},
            {"q": "What payment methods do we accept?", "a": "We accept all major credit/debit cards, UPI, net banking, and cash on delivery."},
        ],
    },
    "coworking": {
        "label": "Co-Working Space",
        "icon": "🏠",
        "description": "Members, desks, bookings, plans, invoices",
        "entity_types": ["member", "desk", "booking", "plan", "invoice", "expense", "task"],
        "seed_knowledge": [
            {"q": "What membership plans do we offer?", "a": "Hot desk: ₹5,000/month. Fixed desk: ₹8,000/month. Private cabin: ₹15,000/month. Virtual office: ₹2,000/month."},
            {"q": "What are our operating hours?", "a": "We are open 24/7 for members. Staff available 9 AM to 8 PM."},
        ],
    },
    "general": {
        "label": "General Business",
        "icon": "🏢",
        "description": "Contacts, projects, tasks, invoices, expenses",
        "entity_types": ["contact", "project", "task", "invoice", "expense", "account"],
        "seed_knowledge": [
            {"q": "How do I add a new team member?", "a": "Go to Settings → Team → Add Member. Enter their name, email, phone, and role."},
            {"q": "How do I upload company data?", "a": "Go to the Ingest page. You can upload PDFs, DOCX, images, audio, video, spreadsheets, and more."},
        ],
    },
}


@onboarding_bp.route("")
@login_required
def onboarding_page():
    """Show the onboarding wizard if not yet onboarded."""
    tenant = g.tenant
    if tenant.onboarding_completed:
        return redirect(url_for("dashboard.dashboard"))
    return render_template("onboarding.html", templates=BUSINESS_TEMPLATES)


@onboarding_bp.route("/start", methods=["POST"])
@login_required
def start_onboarding():
    """Initialize the tenant with a business template."""
    data = request.get_json(silent=True) or request.form
    template_key = data.get("template", "general")
    company_name = data.get("company_name", g.tenant.company_name or "My Company")

    template = BUSINESS_TEMPLATES.get(template_key, BUSINESS_TEMPLATES["general"])

    # Update tenant
    tenant = g.tenant
    tenant.company_name = company_name
    tenant.business_type = template_key
    tenant.theme_config = tenant.theme_config or {}
    tenant.theme_config["icon"] = template["icon"]

    # Create entity types from template
    from app.shunya.finance import FINANCE_ENTITY_TYPES, _ensure_finance_types
    from app.shunya.operations import OPS_ENTITY_TYPES, _ensure_ops_types

    for etype in template["entity_types"]:
        existing = EntityDefinition.query.filter_by(tenant_id=tenant.id, type=etype).first()
        if existing:
            continue

        # Check if it's a finance or ops type
        if etype in FINANCE_ENTITY_TYPES:
            config = FINANCE_ENTITY_TYPES[etype]
        elif etype in OPS_ENTITY_TYPES:
            config = OPS_ENTITY_TYPES[etype]
        else:
            # Generic fallback
            config = {
                "label": etype.capitalize(),
                "icon": "📋",
                "schema": [{"name": "name", "label": "Name", "type": "text", "required": True}],
                "statuses": ["active", "inactive"],
                "layout": "table",
                "searchable_fields": ["name"],
            }

        definition = EntityDefinition(
            tenant_id=tenant.id,
            type=etype,
            label=config["label"],
            label_plural=f"{config['label']}s",
            icon=config.get("icon", "📋"),
            schema=config.get("schema", []),
            statuses=config.get("statuses", ["active", "inactive"]),
            layout=config.get("layout", "table"),
            searchable_fields=config.get("searchable_fields", []),
            primary_field=config.get("schema", [{}])[0].get("name", "name") if config.get("schema") else "name",
        )
        db.session.add(definition)

    # Seed knowledge base
    for item in template.get("seed_knowledge", []):
        existing = KnowledgeEntry.query.filter_by(
            tenant_id=tenant.id, question=item["q"]
        ).first()
        if not existing:
            entry = KnowledgeEntry(
                tenant_id=tenant.id,
                question=item["q"],
                answer=item["a"],
                source="onboarding",
                confidence=0.9,
                category="company_policy",
            )
            db.session.add(entry)

    # Mark onboarding as completed
    tenant.onboarding_completed = True
    db.session.commit()

    return jsonify({
        "success": True,
        "redirect": url_for("dashboard.dashboard"),
        "template": template_key,
        "entity_types_created": len(template["entity_types"]),
        "knowledge_seeded": len(template.get("seed_knowledge", [])),
    })


@onboarding_bp.route("/skip")
@login_required
def skip_onboarding():
    """Skip onboarding and go straight to dashboard."""
    tenant = g.tenant
    tenant.onboarding_completed = True
    db.session.commit()
    return redirect(url_for("dashboard.dashboard"))