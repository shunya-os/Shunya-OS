"""Shunya Sales & CRM Routes — Dashboard, Pipeline, Lead Management, API endpoints."""
from datetime import datetime
from flask import Blueprint, jsonify, render_template, g
from app import db
from app.models import Entity, EntityDefinition, ActivityLog, next_entity_code
from app.routes.auth import login_required
from app.shunya.sales_crm import SalesDashboard, ensure_sales_types, SALES_ENTITY_TYPES

sales_bp = Blueprint("sales", __name__, url_prefix="/sales")


# ---------------------------------------------------------------------------
# Sales & CRM Dashboard (HTML)
# ---------------------------------------------------------------------------

@sales_bp.route("/")
@sales_bp.route("/dashboard")
@login_required
def sales_dashboard():
    """Sales & CRM overview dashboard."""
    ensure_sales_types(g.tenant.id)

    overview = SalesDashboard.get_overview(g.tenant.id)

    # Entity definitions for links
    defs = {}
    for etype in SALES_ENTITY_TYPES:
        defs[etype] = db.session.query(EntityDefinition).filter_by(
            tenant_id=g.tenant.id, type=etype
        ).first()

    # Recent leads
    recent_leads = SalesDashboard.get_recent_leads(g.tenant.id, limit=10)

    # Recent opportunities
    recent_opps = SalesDashboard.get_recent_opportunities(g.tenant.id, limit=8)

    # Stage breakdown for pipeline kanban
    stage_breakdown = SalesDashboard.get_stage_breakdown(g.tenant.id)

    # Accounts summary
    account_summary = SalesDashboard.get_account_summary(g.tenant.id)[:10]

    # Status breakdown per type (for charting)
    status_breakdowns = {}
    for etype in ["lead", "opportunity", "quote"]:
        status_breakdowns[etype] = SalesDashboard.get_status_breakdown(g.tenant.id, etype)

    return render_template(
        "sales_crm/dashboard.html",
        overview=overview,
        defs=defs,
        recent_leads=recent_leads,
        recent_opps=recent_opps,
        stage_breakdown=stage_breakdown,
        account_summary=account_summary,
        status_breakdowns=status_breakdowns,
    )


# ---------------------------------------------------------------------------
# API Summary Endpoint
# ---------------------------------------------------------------------------

@sales_bp.route("/api/summary")
@login_required
def api_summary():
    """JSON summary of all Sales & CRM KPIs for dashboard widgets."""
    ensure_sales_types(g.tenant.id)

    overview = SalesDashboard.get_overview(g.tenant.id)
    recent_leads = SalesDashboard.get_recent_leads(g.tenant.id, limit=5)
    recent_opps = SalesDashboard.get_recent_opportunities(g.tenant.id, limit=5)
    stage_breakdown = SalesDashboard.get_stage_breakdown(g.tenant.id)

    # Status breakdowns
    status_breakdowns = {}
    for etype in ["lead", "opportunity", "quote"]:
        status_breakdowns[etype] = SalesDashboard.get_status_breakdown(g.tenant.id, etype)

    return jsonify({
        "overview": overview,
        "recent_leads": recent_leads,
        "recent_opportunities": recent_opps,
        "stage_breakdown": stage_breakdown,
        "status_breakdowns": status_breakdowns,
    })


# ---------------------------------------------------------------------------
# Pipeline API
# ---------------------------------------------------------------------------

@sales_bp.route("/api/pipeline")
@login_required
def pipeline_data():
    """JSON endpoint for opportunity pipeline kanban data."""
    ensure_sales_types(g.tenant.id)
    opps = SalesDashboard.get_recent_opportunities(g.tenant.id, limit=100)

    # Group by sales stage
    pipeline = {}
    for o in opps:
        stage = o.get("sales_stage", "prospecting")
        if stage not in pipeline:
            pipeline[stage] = {"opportunities": [], "count": 0, "value": 0.0}
        pipeline[stage]["opportunities"].append(o)
        pipeline[stage]["count"] += 1
        pipeline[stage]["value"] += float(o.get("amount", 0) or 0)

    return jsonify({
        "pipeline": pipeline,
        "total_opportunities": len(opps),
        "total_pipeline_value": sum(float(o.get("amount", 0) or 0) for o in opps),
    })


# ---------------------------------------------------------------------------
# Lead Metrics API
# ---------------------------------------------------------------------------

@sales_bp.route("/api/leads")
@login_required
def lead_metrics():
    """JSON endpoint for lead metrics and recent leads."""
    ensure_sales_types(g.tenant.id)
    leads = SalesDashboard.get_recent_leads(g.tenant.id, limit=50)
    metrics = SalesDashboard.get_lead_metrics(g.tenant.id)
    return jsonify({"leads": leads, "metrics": metrics})


# ---------------------------------------------------------------------------
# Account API
# ---------------------------------------------------------------------------

@sales_bp.route("/api/accounts")
@login_required
def account_list():
    """JSON list of all accounts."""
    ensure_sales_types(g.tenant.id)
    accounts = SalesDashboard.get_account_summary(g.tenant.id)
    return jsonify({"accounts": accounts, "total": len(accounts)})


# ---------------------------------------------------------------------------
# Seed data — creates sample records if none exist
# ---------------------------------------------------------------------------

@sales_bp.route("/api/seed")
@login_required
def seed_data():
    """Seed sample Sales & CRM data if no records exist yet."""
    ensure_sales_types(g.tenant.id)
    tenant_id = g.tenant.id

    # Check if we already have data
    lead_def = db.session.query(EntityDefinition).filter_by(
        tenant_id=tenant_id, type="lead"
    ).first()
    if lead_def:
        existing = db.session.query(Entity).filter(
            Entity.tenant_id == tenant_id,
            Entity.definition_id == lead_def.id,
        ).first()
        if existing:
            return jsonify({"message": "Data already seeded", "count": 0})

    seeds = []

    # Helper to create an entity
    def _seed(etype, status, data):
        edef = db.session.query(EntityDefinition).filter_by(
            tenant_id=tenant_id, type=etype
        ).first()
        if not edef:
            return
        entity = Entity(
            tenant_id=tenant_id,
            definition_id=edef.id,
            code=next_entity_code(db.session, tenant_id, "lead"),
            status=status,
            data=data,
        )
        db.session.add(entity)
        seeds.append(entity)

    # --- Leads ---
    _seed("lead", "new", {
        "first_name": "Rajesh", "last_name": "Kumar", "email": "rajesh@example.com",
        "phone": "+91-9876543210", "company": "TechVentures Ltd", "job_title": "CTO",
        "lead_source": "website", "industry": "technology", "lead_score": 85,
        "estimated_value": 500000, "assigned_to": "Amit Sharma", "notes": "Interested in enterprise plan",
    })
    _seed("lead", "contacted", {
        "first_name": "Priya", "last_name": "Singh", "email": "priya@example.com",
        "phone": "+91-9876543211", "company": "GrowthWorks", "job_title": "VP Marketing",
        "lead_source": "referral", "industry": "retail", "lead_score": 72,
        "estimated_value": 250000, "assigned_to": "Amit Sharma",
    })
    _seed("lead", "qualified", {
        "first_name": "Arun", "last_name": "Verma", "email": "arun@example.com",
        "phone": "+91-9876543212", "company": "DataFlow Inc", "job_title": "CEO",
        "lead_source": "event", "industry": "technology", "lead_score": 92,
        "estimated_value": 1200000, "assigned_to": "Sneha Patel",
        "notes": "Demo completed. Ready for proposal.",
    })
    _seed("lead", "converted", {
        "first_name": "Neha", "last_name": "Gupta", "email": "neha@example.com",
        "phone": "+91-9876543213", "company": "CloudSync Pvt Ltd", "job_title": "Head of Engineering",
        "lead_source": "partner", "industry": "technology", "lead_score": 95,
        "estimated_value": 800000, "assigned_to": "Sneha Patel",
        "converted_to": "ACC-001", "converted_at": datetime.utcnow().isoformat(),
    })
    _seed("lead", "new", {
        "first_name": "Vikram", "last_name": "Reddy", "email": "vikram@example.com",
        "phone": "+91-9876543214", "company": "InnovateTech", "job_title": "Director",
        "lead_source": "website", "industry": "manufacturing", "lead_score": 45,
        "estimated_value": 150000, "assigned_to": "Rahul Joshi",
    })
    _seed("lead", "contacted", {
        "first_name": "Ananya", "last_name": "Pillai", "email": "ananya@example.com",
        "phone": "+91-9876543215", "company": "GreenLeaf Organics", "job_title": "COO",
        "lead_source": "social_media", "industry": "retail", "lead_score": 60,
        "estimated_value": 350000, "assigned_to": "Rahul Joshi",
    })

    # --- Accounts ---
    _seed("account", "active", {
        "account_name": "TechVentures Ltd", "website": "https://techventures.example.com",
        "phone": "+91-22-45678900", "email": "info@techventures.example.com",
        "industry": "technology", "account_type": "customer", "annual_revenue": 25000000,
        "employee_count": 500, "city": "Mumbai", "state": "Maharashtra",
        "country": "India", "owner": "Amit Sharma",
        "billing_address": "BKC, Bandra East, Mumbai",
    })
    _seed("account", "active", {
        "account_name": "GrowthWorks Retail", "website": "https://growthworks.example.com",
        "phone": "+91-80-45678901", "email": "info@growthworks.example.com",
        "industry": "retail", "account_type": "customer", "annual_revenue": 15000000,
        "employee_count": 200, "city": "Bengaluru", "state": "Karnataka",
        "country": "India", "owner": "Sneha Patel",
    })
    _seed("account", "active", {
        "account_name": "DataFlow Inc", "website": "https://dataflow.example.com",
        "phone": "+91-44-45678902", "email": "contact@dataflow.example.com",
        "industry": "technology", "account_type": "partner", "annual_revenue": 40000000,
        "employee_count": 1000, "city": "Chennai", "state": "Tamil Nadu",
        "country": "India", "owner": "Sneha Patel",
    })

    # --- Contacts ---
    _seed("contact", "active", {
        "first_name": "Rajesh", "last_name": "Kumar", "email": "rajesh@techventures.example.com",
        "phone": "+91-9876543210", "mobile": "+91-9876543200",
        "account_name": "TechVentures Ltd", "job_title": "CTO",
        "department": "Engineering", "source": "website", "assigned_to": "Amit Sharma",
    })
    _seed("contact", "active", {
        "first_name": "Suresh", "last_name": "Menon", "email": "suresh@techventures.example.com",
        "phone": "+91-9876543220", "mobile": "+91-9876543221",
        "account_name": "TechVentures Ltd", "job_title": "VP Engineering",
        "department": "Engineering", "source": "referral", "assigned_to": "Amit Sharma",
    })
    _seed("contact", "active", {
        "first_name": "Priya", "last_name": "Singh", "email": "priya@growthworks.example.com",
        "phone": "+91-9876543211", "mobile": "+91-9876543222",
        "account_name": "GrowthWorks Retail", "job_title": "VP Marketing",
        "department": "Marketing", "source": "referral", "assigned_to": "Amit Sharma",
    })

    # --- Opportunities ---
    _seed("opportunity", "open", {
        "name": "TechVentures Enterprise License", "account_name": "TechVentures Ltd",
        "amount": 500000, "expected_close_date": "2026-09-30", "probability": 60,
        "lead_source": "website", "sales_stage": "proposal",
        "assigned_to": "Amit Sharma", "description": "Enterprise license renewal with expanded modules",
    })
    _seed("opportunity", "in_progress", {
        "name": "DataFlow Platform Migration", "account_name": "DataFlow Inc",
        "amount": 1200000, "expected_close_date": "2026-08-15", "probability": 75,
        "lead_source": "event", "sales_stage": "negotiation",
        "assigned_to": "Sneha Patel", "description": "Full platform migration to Shunya OS",
    })
    _seed("opportunity", "won", {
        "name": "GrowthWorks POS Integration", "account_name": "GrowthWorks Retail",
        "amount": 250000, "expected_close_date": "2026-06-30", "probability": 100,
        "lead_source": "referral", "sales_stage": "closed_won",
        "assigned_to": "Sneha Patel", "description": "POS integration with Shunya OS",
        "win_notes": "Closed deal after successful PoC. Client very satisfied.",
    })
    _seed("opportunity", "open", {
        "name": "CloudSync Annual Contract", "account_name": "CloudSync Pvt Ltd",
        "amount": 800000, "expected_close_date": "2026-10-31", "probability": 40,
        "lead_source": "partner", "sales_stage": "qualification",
        "assigned_to": "Rahul Joshi", "description": "Annual SaaS contract negotiation",
    })

    # --- Products ---
    _seed("product", "active", {
        "product_name": "Shunya OS Enterprise", "product_code": "SHU-ENT-001",
        "product_category": "software", "unit_price": 500000, "cost_price": 200000,
        "tax_rate": 18, "description": "Enterprise edition with full module access",
        "uom": "year", "stock_quantity": 999, "reorder_level": 10, "active": True,
    })
    _seed("product", "active", {
        "product_name": "Shunya OS Pro", "product_code": "SHU-PRO-001",
        "product_category": "software", "unit_price": 250000, "cost_price": 100000,
        "tax_rate": 18, "description": "Professional edition for growing businesses",
        "uom": "year", "stock_quantity": 999, "reorder_level": 10, "active": True,
    })
    _seed("product", "active", {
        "product_name": "Implementation Service", "product_code": "SHU-IMP-001",
        "product_category": "service", "unit_price": 75000, "cost_price": 30000,
        "tax_rate": 18, "description": "Onboarding and implementation consulting",
        "uom": "day", "stock_quantity": 50, "reorder_level": 5, "active": True,
    })
    _seed("product", "inactive", {
        "product_name": "Shunya OS Starter (Legacy)", "product_code": "SHU-START-001",
        "product_category": "software", "unit_price": 100000, "cost_price": 50000,
        "tax_rate": 18, "description": "Legacy starter edition (no longer sold)",
        "uom": "year", "stock_quantity": 0, "reorder_level": 0, "active": False,
    })

    # --- Quotes ---
    _seed("quote", "sent", {
        "quote_number": "Q-2026-001", "account_name": "TechVentures Ltd",
        "valid_until": "2026-08-31", "subtotal": 500000, "discount": 25000,
        "tax_rate": 18, "tax_amount": 85500, "total_amount": 560500,
        "currency": "INR", "payment_terms": "Net 30",
        "assigned_to": "Amit Sharma",
        "terms_and_conditions": "Standard license terms apply.",
    })
    _seed("quote", "accepted", {
        "quote_number": "Q-2026-002", "account_name": "GrowthWorks Retail",
        "valid_until": "2026-07-31", "subtotal": 250000, "discount": 0,
        "tax_rate": 18, "tax_amount": 45000, "total_amount": 295000,
        "currency": "INR", "payment_terms": "Net 15",
        "assigned_to": "Sneha Patel",
    })
    _seed("quote", "draft", {
        "quote_number": "Q-2026-003", "account_name": "DataFlow Inc",
        "valid_until": "2026-09-15", "subtotal": 1200000, "discount": 100000,
        "tax_rate": 18, "tax_amount": 198000, "total_amount": 1298000,
        "currency": "INR", "payment_terms": "Net 45",
        "assigned_to": "Sneha Patel",
    })

    # --- Target Lists ---
    _seed("target_list", "active", {
        "name": "Tech Industry Q3 Campaign",
        "description": "Technology companies for Q3 outbound campaign",
        "list_type": "static", "target_type": "contacts", "member_count": 3,
        "campaign": "Q3 Tech Outreach", "assigned_to": "Amit Sharma",
    })
    _seed("target_list", "active", {
        "name": "Retail Sector Leads",
        "description": "Retail industry leads from recent events",
        "list_type": "static", "target_type": "leads", "member_count": 1,
        "campaign": "Retail Expansion", "assigned_to": "Rahul Joshi",
    })

    db.session.commit()
    return jsonify({
        "message": "Sample Sales & CRM data seeded successfully",
        "count": len(seeds),
        "types_created": list(set(e.definition.type for e in seeds)),
    })
