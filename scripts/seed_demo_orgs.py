"""
Seed 3 demo organizations with 50+ objects each in an isolated
test environment.  Idempotent: safe to re-run.

Safety: requires both DATABASE_URL containing ':memory:' or 'test' AND
FLASK_ENV=testing or SHUNYA_ENVIRONMENT=testing.  Exits with code 1
otherwise.

Usage:
  FLASK_ENV=testing DATABASE_URL=sqlite:///:memory: python scripts/seed_demo_orgs.py
"""

import os
import sys
import uuid
from datetime import datetime, timezone

# ---- Safety guards -----------------------------------------------------------
# The seed script must only run against an explicitly authorized, isolated test
# database.  Three independent checks:
#   1. SHUNYA_SEED_ALLOWED   environment variable must be exactly "true"
#   2. DATABASE_URL          must contain ":memory:" or "test"
#   3. FLASK_ENV or SHUNYA_ENVIRONMENT must be "testing" or unset
#
# After app initialization (inside seed()), the script additionally verifies the
# actual database backend via SQLAlchemy dialect inspection.  The combined
# checks prevent accidental execution against production even if a single guard
# is misconfigured.
import os as _os
_DB_URL = _os.environ.get("DATABASE_URL", "")
_FLASK_ENV = _os.environ.get("FLASK_ENV", "")
_SHUNYA_ENV = _os.environ.get("SHUNYA_ENVIRONMENT", "")
_SEED_ALLOWED = _os.environ.get("SHUNYA_SEED_ALLOWED", "")

_REJECT_REASON = None
if _SEED_ALLOWED != "true":
    _REJECT_REASON = "SHUNYA_SEED_ALLOWED is not set to 'true'"
elif not _DB_URL:
    _REJECT_REASON = "DATABASE_URL is not set"
elif "memory" not in _DB_URL and "test" not in _DB_URL:
    _REJECT_REASON = f"DATABASE_URL does not look like a test DB: {_DB_URL[:60]}..."
elif _FLASK_ENV not in ("", "testing") and _SHUNYA_ENV not in ("", "testing"):
    _REJECT_REASON = "FLASK_ENV or SHUNYA_ENVIRONMENT must be 'testing' or unset"
if _REJECT_REASON:
    print(f"ERROR: {_REJECT_REASON}. Refusing to run.", file=sys.stderr)
    sys.exit(1)

# ---- Data definitions --------------------------------------------------------

_WANDERLUST_OBJECTS = [
    {"type": "customer", "name": "Alpine Trek Club", "meta": {"industry": "sports", "country": "CH", "tier": "platinum"}},
    {"type": "customer", "name": "Summit Adventures Ltd", "meta": {"industry": "tourism", "country": "NP", "tier": "gold"}},
    {"type": "customer", "name": "Ocean Blue Diving", "meta": {"industry": "tourism", "country": "TH", "tier": "gold"}},
    {"type": "customer", "name": "Safari World Kenya", "meta": {"industry": "tourism", "country": "KE", "tier": "silver"}},
    {"type": "customer", "name": "Nordic Fjord Tours", "meta": {"industry": "tourism", "country": "NO", "tier": "silver"}},
    {"type": "customer", "name": "Andean Pathways Inc", "meta": {"industry": "tourism", "country": "PE", "tier": "silver"}},
    {"type": "customer", "name": "Mongolian Steppe Riders", "meta": {"industry": "adventure", "country": "MN", "tier": "bronze"}},
    {"type": "customer", "name": "Patagonia Wild Expeditions", "meta": {"industry": "adventure", "country": "AR", "tier": "bronze"}},
    {"type": "customer", "name": "Coral Reef Adventures", "meta": {"industry": "scuba", "country": "AU", "tier": "gold"}},
    {"type": "customer", "name": "Himalayan Trekking Co", "meta": {"industry": "tourism", "country": "BT", "tier": "silver"}},
    {"type": "customer", "name": "Desert Nomad Tours", "meta": {"industry": "tourism", "country": "MA", "tier": "bronze"}},
    {"type": "customer", "name": "Amazon River Expeditions", "meta": {"industry": "adventure", "country": "BR", "tier": "bronze"}},
    {"type": "invoice", "name": "INV-2026-001 - Alpine Trek Q1", "meta": {"amount": 12500, "currency": "CHF", "status": "paid"}},
    {"type": "invoice", "name": "INV-2026-002 - Summit Adventures", "meta": {"amount": 8750, "currency": "USD", "status": "paid"}},
    {"type": "invoice", "name": "INV-2026-003 - Ocean Blue", "meta": {"amount": 14800, "currency": "THB", "status": "pending"}},
    {"type": "invoice", "name": "INV-2026-004 - Safari World Kenya", "meta": {"amount": 6500, "currency": "USD", "status": "paid"}},
    {"type": "invoice", "name": "INV-2026-005 - Nordic Fjord", "meta": {"amount": 9200, "currency": "NOK", "status": "pending"}},
    {"type": "invoice", "name": "INV-2026-006 - Andean Pathways", "meta": {"amount": 5100, "currency": "USD", "status": "overdue"}},
    {"type": "invoice", "name": "INV-2026-007 - Patagonia Wild", "meta": {"amount": 3700, "currency": "USD", "status": "paid"}},
    {"type": "invoice", "name": "INV-2026-008 - Coral Reef Q1", "meta": {"amount": 16200, "currency": "AUD", "status": "paid"}},
    {"type": "invoice", "name": "INV-2026-009 - Himalayan Trek", "meta": {"amount": 7800, "currency": "USD", "status": "pending"}},
    {"type": "invoice", "name": "INV-2026-010 - Desert Nomad", "meta": {"amount": 3200, "currency": "EUR", "status": "paid"}},
    {"type": "invoice", "name": "INV-2026-011 - Alpine Trek Q2", "meta": {"amount": 14100, "currency": "CHF", "status": "draft"}},
    {"type": "invoice", "name": "INV-2026-012 - Amazon River", "meta": {"amount": 5600, "currency": "BRL", "status": "pending"}},
    {"type": "invoice", "name": "INV-2026-013 - Mongolian Steppe", "meta": {"amount": 2800, "currency": "USD", "status": "paid"}},
    {"type": "invoice", "name": "INV-2026-014 - Nordic Fjord Q2", "meta": {"amount": 10500, "currency": "EUR", "status": "draft"}},
    {"type": "invoice", "name": "INV-2026-015 - Coral Reef Q2", "meta": {"amount": 18900, "currency": "AUD", "status": "draft"}},
    {"type": "milestone", "name": "Q1 2026 — New Base Camp Trek", "meta": {"status": "completed", "quarter": "Q1"}},
    {"type": "milestone", "name": "Q2 2026 — Safari Partnership Launch", "meta": {"status": "in_progress", "quarter": "Q2"}},
    {"type": "milestone", "name": "Equipment upgrade for Andean routes", "meta": {"status": "completed", "quarter": "Q1"}},
    {"type": "milestone", "name": "Guide certification program launch", "meta": {"status": "completed", "quarter": "Q1"}},
    {"type": "milestone", "name": "New website with online booking", "meta": {"status": "in_progress", "quarter": "Q2"}},
    {"type": "milestone", "name": "Carbon-neutral operations certification", "meta": {"status": "planned", "quarter": "Q3"}},
    {"type": "milestone", "name": "Winter expedition gear inventory audit", "meta": {"status": "completed", "quarter": "Q1"}},
    {"type": "milestone", "name": "Trekking route safety review (Q2)", "meta": {"status": "in_progress", "quarter": "Q2"}},
    {"type": "milestone", "name": "Partnership with Bhutan Tourism Board", "meta": {"status": "planned", "quarter": "Q3"}},
    {"type": "milestone", "name": "Mobile app for field guides v2.0", "meta": {"status": "planned", "quarter": "Q4"}},
    {"type": "conversation", "name": "Alpine trek pricing discussion", "meta": {"participants": "alice, bob@alpine"}},
    {"type": "conversation", "name": "Safari Kenya itinerary planning", "meta": {"participants": "alice, carol@safari"}},
    {"type": "conversation", "name": "Ocean Blue gear requirements", "meta": {"participants": "david, erin@oceanblue"}},
    {"type": "conversation", "name": "Andean guide recruitment", "meta": {"participants": "frank, grace@andean"}},
    {"type": "conversation", "name": "Fjord marketing assets review", "meta": {"participants": "henry, ingrid@fjord"}},
    {"type": "conversation", "name": "Winter gear supplier negotiation", "meta": {"participants": "julia, kevin@gearco"}},
    {"type": "conversation", "name": "Bhutan tourism board partnership", "meta": {"participants": "alice, lama@bhutan"}},
    {"type": "conversation", "name": "Q2 revenue forecast meeting", "meta": {"participants": "team@wanderlust"}},
    {"type": "conversation", "name": "Website redesign sprint review", "meta": {"participants": "dev, design@agency"}},
    {"type": "conversation", "name": "Insurance coverage audit results", "meta": {"participants": "compliance, broker@insure"}},
    {"type": "note", "name": "Equipment vendor evaluation notes", "meta": {"author": "david", "tags": "equipment vendors Q1"}},
    {"type": "note", "name": "Nepal trek permit requirements 2026", "meta": {"author": "alice", "tags": "permits nepal"}},
    {"type": "note", "name": "Guide training session outline", "meta": {"author": "frank", "tags": "training guides"}},
    {"type": "note", "name": "Customer feedback summary Q1", "meta": {"author": "grace", "tags": "feedback Q1"}},
    {"type": "note", "name": "Sustainable tourism checklist", "meta": {"author": "henry", "tags": "sustainability operations"}},
    {"type": "note", "name": "Emergency contact update procedure", "meta": {"author": "julia", "tags": "safety procedures"}},
    {"type": "note", "name": "Peak season staffing plan", "meta": {"author": "alice", "tags": "staffing summer"}},
    {"type": "note", "name": "Social media content calendar", "meta": {"author": "ingrid", "tags": "marketing social"}},
    {"type": "note", "name": "Insurance renewal checklist", "meta": {"author": "kevin", "tags": "insurance compliance"}},
    {"type": "note", "name": "First aid kit restocking schedule", "meta": {"author": "david", "tags": "safety equipment"}},
]

_PRECISION_OBJECTS = [
    {"type": "customer", "name": "AeroTech Industries", "meta": {"industry": "aerospace", "tier": "platinum"}},
    {"type": "customer", "name": "MedForce Devices", "meta": {"industry": "medical", "tier": "gold"}},
    {"type": "customer", "name": "AutoGlobal GmbH", "meta": {"industry": "automotive", "tier": "gold"}},
    {"type": "customer", "name": "BuildRight Construction", "meta": {"industry": "construction", "tier": "silver"}},
    {"type": "customer", "name": "Helicorp Aviation", "meta": {"industry": "aerospace", "tier": "gold"}},
    {"type": "customer", "name": "RailTech Systems", "meta": {"industry": "rail", "tier": "silver"}},
    {"type": "customer", "name": "Offshore Drilling Supply", "meta": {"industry": "energy", "tier": "bronze"}},
    {"type": "customer", "name": "Quantum Robotics", "meta": {"industry": "robotics", "tier": "silver"}},
    {"type": "customer", "name": "GreenEnergy Turbines", "meta": {"industry": "wind", "tier": "bronze"}},
    {"type": "customer", "name": "DefenseSys GmbH", "meta": {"industry": "defense", "tier": "platinum"}},
    {"type": "customer", "name": "Precision Instruments Japan", "meta": {"industry": "instrumentation", "tier": "gold"}},
    {"type": "invoice", "name": "INV-2026-001 - AeroTech batch 4A", "meta": {"amount": 52000, "currency": "EUR", "status": "paid"}},
    {"type": "invoice", "name": "INV-2026-002 - MedForce prototype", "meta": {"amount": 18000, "currency": "EUR", "status": "pending"}},
    {"type": "invoice", "name": "INV-2026-003 - AutoGlobal Q1", "meta": {"amount": 34000, "currency": "EUR", "status": "overdue"}},
    {"type": "invoice", "name": "INV-2026-004 - Helicorp rotor batch", "meta": {"amount": 42000, "currency": "EUR", "status": "paid"}},
    {"type": "invoice", "name": "INV-2026-005 - RailTech signal parts", "meta": {"amount": 15000, "currency": "EUR", "status": "paid"}},
    {"type": "invoice", "name": "INV-2026-006 - Offshore Drill valves", "meta": {"amount": 8500, "currency": "USD", "status": "pending"}},
    {"type": "invoice", "name": "INV-2026-007 - Quantum servo motors", "meta": {"amount": 28000, "currency": "EUR", "status": "paid"}},
    {"type": "invoice", "name": "INV-2026-008 - DefenseSys Q1", "meta": {"amount": 67000, "currency": "EUR", "status": "paid"}},
    {"type": "invoice", "name": "INV-2026-009 - PI Japan calibration", "meta": {"amount": 22000, "currency": "JPY", "status": "pending"}},
    {"type": "invoice", "name": "INV-2026-010 - GreenEnergy gear set", "meta": {"amount": 12000, "currency": "EUR", "status": "draft"}},
    {"type": "invoice", "name": "INV-2026-011 - AutoGlobal Q2", "meta": {"amount": 36000, "currency": "EUR", "status": "draft"}},
    {"type": "invoice", "name": "INV-2026-012 - MedForce production run", "meta": {"amount": 24000, "currency": "EUR", "status": "draft"}},
    {"type": "invoice", "name": "INV-2026-013 - Helicorp Q2", "meta": {"amount": 45000, "currency": "EUR", "status": "pending"}},
    {"type": "invoice", "name": "INV-2026-014 - BuildRight structural", "meta": {"amount": 9500, "currency": "EUR", "status": "paid"}},
    {"type": "invoice", "name": "INV-2026-015 - Quantum Q2", "meta": {"amount": 31000, "currency": "EUR", "status": "pending"}},
    {"type": "milestone", "name": "ISO 13485 recertification", "meta": {"status": "completed", "quarter": "Q1"}},
    {"type": "milestone", "name": "Factory line 4 expansion", "meta": {"status": "in_progress", "quarter": "Q2"}},
    {"type": "milestone", "name": "CNC machine upgrade program", "meta": {"status": "completed", "quarter": "Q1"}},
    {"type": "milestone", "name": "Supplier quality audit Q1 cycle", "meta": {"status": "completed", "quarter": "Q1"}},
    {"type": "milestone", "name": "ERP system migration phase 1", "meta": {"status": "in_progress", "quarter": "Q2"}},
    {"type": "milestone", "name": "Workplace safety certification", "meta": {"status": "completed", "quarter": "Q1"}},
    {"type": "milestone", "name": "Lean manufacturing rollout", "meta": {"status": "planned", "quarter": "Q3"}},
    {"type": "milestone", "name": "Export compliance ITAR audit", "meta": {"status": "in_progress", "quarter": "Q2"}},
    {"type": "milestone", "name": "R&D — new alloy development", "meta": {"status": "planned", "quarter": "Q3"}},
    {"type": "milestone", "name": "Automotive TS 16949 certification", "meta": {"status": "planned", "quarter": "Q4"}},
    {"type": "conversation", "name": "AeroTech contract renewal", "meta": {"participants": "sales, procurement@aerotech"}},
    {"type": "conversation", "name": "MedForce biocompatibility report", "meta": {"participants": "qa, rnd@medforce"}},
    {"type": "conversation", "name": "AutoGlobal Q2 forecast", "meta": {"participants": "supply, demand@autoglobal"}},
    {"type": "conversation", "name": "CNC maintenance schedule", "meta": {"participants": "ops, tech@service"}},
    {"type": "conversation", "name": "Raw material price negotiation", "meta": {"participants": "procurement, supply@steel"}},
    {"type": "conversation", "name": "ITAR compliance audit prep", "meta": {"participants": "compliance, auditor@gov"}},
    {"type": "conversation", "name": "Factory line 4 layout review", "meta": {"participants": "eng, build@contractor"}},
    {"type": "conversation", "name": "Employee training program update", "meta": {"participants": "hr, leads@floor"}},
    {"type": "conversation", "name": "Shipping logistics cost review", "meta": {"participants": "logistics, carrier@freight"}},
    {"type": "conversation", "name": "Quality dashboard redesign", "meta": {"participants": "qa, it@precision"}},
    {"type": "note", "name": "Batch inspection Q1 summary", "meta": {"author": "qa_lead", "tags": "qa Q1"}},
    {"type": "note", "name": "New supplier onboarding checklist", "meta": {"author": "procurement", "tags": "suppliers procedures"}},
    {"type": "note", "name": "CNC calibration schedule 2026", "meta": {"author": "ops_mgr", "tags": "maintenance equipment"}},
    {"type": "note", "name": "Safety incident review procedures", "meta": {"author": "safety", "tags": "safety procedures"}},
    {"type": "note", "name": "Customer audit preparation guide", "meta": {"author": "qa_lead", "tags": "audit customers"}},
    {"type": "note", "name": "Tooling inventory count notes", "meta": {"author": "ops_mgr", "tags": "inventory tools"}},
    {"type": "note", "name": "Employee training matrix update", "meta": {"author": "hr", "tags": "training compliance"}},
    {"type": "note", "name": "R&D project proposal template", "meta": {"author": "rnd_lead", "tags": "rd proposals"}},
    {"type": "note", "name": "Shipping damage claim process", "meta": {"author": "logistics", "tags": "shipping claims"}},
    {"type": "note", "name": "ERP migration requirements log", "meta": {"author": "it_lead", "tags": "erp migration"}},
]

_NOVACARE_OBJECTS = [
    {"type": "customer", "name": "St. Mary's Hospital", "meta": {"industry": "hospital", "tier": "platinum"}},
    {"type": "customer", "name": "WellnessFirst Clinics", "meta": {"industry": "clinic", "tier": "gold"}},
    {"type": "customer", "name": "PharmaCorp Distribution", "meta": {"industry": "pharma", "tier": "silver"}},
    {"type": "customer", "name": "Apex Rehab Center", "meta": {"industry": "rehab", "tier": "bronze"}},
    {"type": "customer", "name": "Children's Health Alliance", "meta": {"industry": "pediatrics", "tier": "gold"}},
    {"type": "customer", "name": "ElderCare Network", "meta": {"industry": "eldercare", "tier": "silver"}},
    {"type": "customer", "name": "Surgical Specialists Group", "meta": {"industry": "surgery", "tier": "platinum"}},
    {"type": "customer", "name": "NeuroDiagnostic Labs", "meta": {"industry": "diagnostics", "tier": "silver"}},
    {"type": "customer", "name": "Regional Blood Bank", "meta": {"industry": "blood", "tier": "gold"}},
    {"type": "customer", "name": "Veterans Medical Alliance", "meta": {"industry": "govt", "tier": "platinum"}},
    {"type": "customer", "name": "HomeCare Plus", "meta": {"industry": "homecare", "tier": "bronze"}},
    {"type": "customer", "name": "Dental Implant Centers", "meta": {"industry": "dental", "tier": "bronze"}},
    {"type": "invoice", "name": "INV-2026-001 - St. Mary's Q1", "meta": {"amount": 142000, "currency": "EUR", "status": "paid"}},
    {"type": "invoice", "name": "INV-2026-002 - WellnessFirst IT", "meta": {"amount": 33000, "currency": "EUR", "status": "paid"}},
    {"type": "invoice", "name": "INV-2026-003 - PharmaCorp integration", "meta": {"amount": 25000, "currency": "EUR", "status": "pending"}},
    {"type": "invoice", "name": "INV-2026-004 - Children's Health Q1", "meta": {"amount": 88000, "currency": "EUR", "status": "paid"}},
    {"type": "invoice", "name": "INV-2026-005 - Surgical Specialists", "meta": {"amount": 65000, "currency": "EUR", "status": "paid"}},
    {"type": "invoice", "name": "INV-2026-006 - NeuroDiagnostic Q1", "meta": {"amount": 22000, "currency": "EUR", "status": "pending"}},
    {"type": "invoice", "name": "INV-2026-007 - Regional Blood Bank", "meta": {"amount": 15000, "currency": "EUR", "status": "overdue"}},
    {"type": "invoice", "name": "INV-2026-008 - ElderCare telehealth", "meta": {"amount": 28000, "currency": "EUR", "status": "paid"}},
    {"type": "invoice", "name": "INV-2026-009 - Veterans Alliance Q1", "meta": {"amount": 96000, "currency": "EUR", "status": "paid"}},
    {"type": "invoice", "name": "INV-2026-010 - Apex Rehab equipment", "meta": {"amount": 11000, "currency": "EUR", "status": "pending"}},
    {"type": "invoice", "name": "INV-2026-011 - HomeCare Plus Q1", "meta": {"amount": 8500, "currency": "EUR", "status": "draft"}},
    {"type": "invoice", "name": "INV-2026-012 - Dental Implant Centers", "meta": {"amount": 14000, "currency": "EUR", "status": "pending"}},
    {"type": "invoice", "name": "INV-2026-013 - St. Mary's Q2", "meta": {"amount": 155000, "currency": "EUR", "status": "draft"}},
    {"type": "invoice", "name": "INV-2026-014 - Surgical Q2 phase1", "meta": {"amount": 72000, "currency": "EUR", "status": "draft"}},
    {"type": "invoice", "name": "INV-2026-015 - WellnessFirst annual", "meta": {"amount": 38000, "currency": "EUR", "status": "pending"}},
    {"type": "milestone", "name": "EHR system migration", "meta": {"status": "completed", "quarter": "Q1"}},
    {"type": "milestone", "name": "Multi-site telemedicine rollout", "meta": {"status": "in_progress", "quarter": "Q2"}},
    {"type": "milestone", "name": "HIPAA compliance audit Q1", "meta": {"status": "completed", "quarter": "Q1"}},
    {"type": "milestone", "name": "New St. Mary's wing opening", "meta": {"status": "completed", "quarter": "Q1"}},
    {"type": "milestone", "name": "NovaCare mobile app launch", "meta": {"status": "in_progress", "quarter": "Q2"}},
    {"type": "milestone", "name": "Pharmacovigilance system upgrade", "meta": {"status": "completed", "quarter": "Q1"}},
    {"type": "milestone", "name": "Staff vaccination program rollout", "meta": {"status": "completed", "quarter": "Q1"}},
    {"type": "milestone", "name": "Telemedicine vendor selection", "meta": {"status": "planned", "quarter": "Q3"}},
    {"type": "milestone", "name": "HL7 interoperability certification", "meta": {"status": "in_progress", "quarter": "Q2"}},
    {"type": "milestone", "name": "New patient portal design", "meta": {"status": "planned", "quarter": "Q4"}},
    {"type": "conversation", "name": "St. Mary's SLA review", "meta": {"participants": "contracts, admin@stmarys"}},
    {"type": "conversation", "name": "EHR migration weekly sync", "meta": {"participants": "it, vendor@meditech"}},
    {"type": "conversation", "name": "WellnessFirst expansion", "meta": {"participants": "dev, ops@wellness"}},
    {"type": "conversation", "name": "PharmaCorp API integration", "meta": {"participants": "eng, api@pharma"}},
    {"type": "conversation", "name": "Telemedicine vendor shortlist", "meta": {"participants": "cto, eval@committee"}},
    {"type": "conversation", "name": "Veterans Alliance compliance", "meta": {"participants": "govt, compliance@va"}},
    {"type": "conversation", "name": "Blood bank logistics coordination", "meta": {"participants": "logistics, ops@bloodbank"}},
    {"type": "conversation", "name": "Q2 budget planning session", "meta": {"participants": "finance, dept_heads"}},
    {"type": "conversation", "name": "Mobile app UX review", "meta": {"participants": "design, dev@agency"}},
    {"type": "conversation", "name": "Insurance rates update", "meta": {"participants": "billing, payer@insure"}},
    {"type": "note", "name": "HIPAA training log Q1", "meta": {"author": "compliance", "tags": "hipaa training"}},
    {"type": "note", "name": "St. Mary's equipment inventory", "meta": {"author": "ops", "tags": "inventory stmarys"}},
    {"type": "note", "name": "Telemedicine bandwidth requirements", "meta": {"author": "it", "tags": "telemed infra"}},
    {"type": "note", "name": "Patient satisfaction survey Q1", "meta": {"author": "quality", "tags": "surveys Q1"}},
    {"type": "note", "name": "New hire onboarding checklist", "meta": {"author": "hr", "tags": "hr onboarding"}},
    {"type": "note", "name": "Pharmacy inventory count process", "meta": {"author": "pharmacy", "tags": "pharmacy inventory"}},
    {"type": "note", "name": "Emergency preparedness drill report", "meta": {"author": "safety", "tags": "safety emergency"}},
    {"type": "note", "name": "Lab equipment calibration schedule", "meta": {"author": "lab_mgr", "tags": "lab calibration"}},
    {"type": "note", "name": "Chronic care management program", "meta": {"author": "clinical", "tags": "care program"}},
    {"type": "note", "name": "Insurance claim denial analysis", "meta": {"author": "billing", "tags": "insurance billing"}},
]

DEMO_ORGS = [
    {"name": "Wanderlust Expeditions", "slug": "demo-wanderlust", "industry": "Travel & Tourism",
     "description": "A premium adventure travel company", "objects": _WANDERLUST_OBJECTS},
    {"name": "Precision Components Ltd", "slug": "demo-precision", "industry": "Manufacturing",
     "description": "An industrial components manufacturer", "objects": _PRECISION_OBJECTS},
    {"name": "NovaCare Health Systems", "slug": "demo-novacare", "industry": "Healthcare",
     "description": "A multi-specialty healthcare network", "objects": _NOVACARE_OBJECTS},
]


def _uuid7():
    ts = int(datetime.now(timezone.utc).timestamp() * 1000)
    return f"{ts:016x}{uuid.uuid4().hex[:16]}"


def seed():
    from app import create_app, db
    app = create_app(config_override={"TESTING": True, "SQLALCHEMY_DATABASE_URI": _DB_URL})
    with app.app_context():
        # Runtime database identity check — the pre-execution URL check may match
        # a string pattern against a URL that resolves to a hostile target through
        # aliasing or forwarding.  This second check inspects the actual connected
        # dialect after SQLAlchemy has resolved the full URL and connected.
        _dialect = db.engine.dialect.name
        if _dialect != "sqlite":
            print(f"ERROR: Actual database dialect is '{_dialect}', not 'sqlite'. Refusing to seed.", file=sys.stderr)
            sys.exit(1)
        from app import models  # noqa: F401
        from app.kernel.models import UOPObject
        db.create_all()
        from app.tenant import Tenant
        from app.models import OrgMember
        from app.auth import TeamMember
        admin = TeamMember.query.filter_by(email="admin@shunyaos.com").first()
        if not admin:
            admin = TeamMember(email="admin@shunyaos.com", name="SHUNYA Admin", role="admin", is_active=True, verified=True)
            admin.set_password("demo-admin-pw")
            db.session.add(admin)
            db.session.flush()
        total_new = 0
        for org_def in DEMO_ORGS:
            tenant = Tenant.query.filter_by(slug=org_def["slug"]).first()
            is_new = tenant is None
            if is_new:
                tenant = Tenant(company_name=org_def["name"], slug=org_def["slug"])
                db.session.add(tenant)
                db.session.flush()
                OrgMember(email=admin.email, organization_id=tenant.id,
                          identity_id=admin.identity_id or str(admin.id),
                          name=admin.name, role="owner", is_active=True)
                db.session.flush()
                print(f"CREATED tenant: {org_def['name']} (id={tenant.id})")
            else:
                print(f"EXISTING tenant: {org_def['name']} (id={tenant.id})")
            now = datetime.now(timezone.utc)
            existing = {(o.object_type, o.name) for o in UOPObject.query.filter_by(tenant_id=tenant.id).all()}
            n = 0
            for obj in org_def["objects"]:
                if (obj["type"], obj["name"]) in existing:
                    continue
                m = UOPObject(object_id=_uuid7(), tenant_id=tenant.id, space_id="",
                              object_type=obj["type"], name=obj["name"], status="active",
                              version=1, confidence=1.0,
                              created_at=now.isoformat(), updated_at=now.isoformat(),
                              created_by=str(admin.id), updated_by=str(admin.id),
                              evidence_json="[]", relationships_json="[]",
                              metadata_json=str(obj.get("meta", {})))
                db.session.add(m); n += 1; total_new += 1
            print(f"  New objects: {n} (DB total: {UOPObject.query.filter_by(tenant_id=tenant.id).count()})")
        db.session.commit()
        print(f"\nTotal tenants: {Tenant.query.count()}")
        print(f"New this run: {total_new}")
        print(f"Total UOP objects: {UOPObject.query.count()}")
        for t in Tenant.query.all():
            c = UOPObject.query.filter_by(tenant_id=t.id).count()
            print(f"  {t.company_name}: {c} objects")
        print("Done.")


if __name__ == "__main__":
    seed()