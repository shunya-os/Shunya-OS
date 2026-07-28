#!/usr/bin/env python3
"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
SHUNYA — Living Demonstration Environment v2
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Phase 1: Creates 3 organizations with 152 objects (customers, suppliers,
          invoices, relationships, commitments, notes, conversations).

Phase 2: Enriches with historical continuity, interconnected workflows,
          AI context, and multi-organization founder journeys.

Usage:
  source .venv/bin/activate
  python3 scripts/seed_demo.py            # Phase 1 + 2
  python3 scripts/seed_demo.py --phase 1  # Phase 1 only
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

import json, hashlib, os, sys, uuid, argparse
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("DATABASE_URL", "postgresql://shunya:Shunya%402026!@localhost:5432/shunya_os")
os.environ.setdefault("SECRET_KEY", "ShunyaSecretKey2026ReplaceThisWithALongRandomString")
os.environ.setdefault("FLASK_ENV", "development")

from app import create_app, db
from app.founder.models import FounderSpace, FounderObject, FounderConversation, FounderMessage, BusinessRelationship

_SEED = 42
FOUNDER_EMAIL = "nishesh@shunyaos.com"
FOUNDER_PASSWORD = "demo123456"

def dh(key: str) -> str:
    return hashlib.sha256(f"{_SEED}{key}".encode()).hexdigest()[:12]

def di(key: str, lo: int, hi: int) -> int:
    return int(dh(key), 16) % (hi - lo + 1) + lo

def dc(key: str, items: list):
    return items[di(key, 0, len(items) - 1)]

def dd(key: str, days_ago: int = 90) -> datetime:
    return datetime(2026, 6, 1) + timedelta(days=di(key, -days_ago, 0))

def da(key: str, lo: float = 1000, hi: float = 500000) -> float:
    return round(di(key, int(lo * 100), int(hi * 100)) / 100, 2)

def sid() -> str:
    return uuid.uuid4().hex[:12]


# ═══════════════════════════════════════════════════════════════════
# PHASE 1 — Organization seed data
# ═══════════════════════════════════════════════════════════════════

class OrgData:
    def __init__(self, name: str, industry: str, desc: str):
        self.name = name; self.industry = industry; self.desc = desc
        self.prefix = dh(name)
    def customers(self): raise NotImplementedError
    def suppliers(self): raise NotImplementedError
    def invoices(self): raise NotImplementedError
    def relationships(self): raise NotImplementedError
    def commits(self): raise NotImplementedError
    def notes(self): raise NotImplementedError
    def conversations(self): raise NotImplementedError


class TravelData(OrgData):
    def __init__(self):
        super().__init__("Wanderlust Expeditions", "Travel & Tourism",
            "Premium adventure travel company in Southeast Asia.")
    def customers(self):
        names = ["Aarav Sharma","Priya Mehta","Rohan Kapoor","Ananya Patel",
            "Vikram Singh","Ishita Desai","Arjun Nair","Kavya Reddy","Neha Gupta","Rahul Joshi"]
        return [{"name": n, "type": "customer",
            "email": f"{n.lower().replace(' ','.')}@email.com",
            "city": dc(f"{self.prefix}c{i}", ["Mumbai","Delhi","Bangalore","Jaipur","Chennai"]),
            "tier": dc(f"{self.prefix}ct{i}", ["standard","vip","standard"]),
            "total_spent": da(f"{self.prefix}c{i}", 50000, 1500000),
            "since": dd(f"{self.prefix}c{i}", 365).isoformat()}
            for i, n in enumerate(names)]
    def suppliers(self):
        return [{"name": n, "type": "supplier",
            "category": dc(f"{self.prefix}s{i}", ["accommodation","transport","guide","charter"]),
            "contract": da(f"{self.prefix}s{i}", 200000, 2000000),
            "since": dd(f"{self.prefix}s{i}", 365).isoformat()}
            for i, n in enumerate(["Bali Eco Lodge","Himalayan Guides Co","Silk Road Transfers",
                "Island Hopper Charters","Mountain View Retreats"])]
    def invoices(self):
        descs = ["Bali Adventure 7d","Himalayan Trek 14d","Kerala Retreat 5d",
            "Rajasthan Tour 10d","Andaman Escape 6d","Vietnam Explorer 8d"]
        return [{"invoice_number": f"WL-2026-{1000+i}", "type": "invoice",
            "total": da(f"{self.prefix}i{i}", 15000, 350000),
            "status": dc(f"{self.prefix}ip{i}", ["paid","paid","paid","pending","overdue"]),
            "description": dc(f"{self.prefix}id{i}", descs),
            "issue_date": dd(f"{self.prefix}i{i}", 60).isoformat(),
            "due_date": dd(f"{self.prefix}i{i}", 30).isoformat()}
            for i in range(25)]
    def relationships(self):
        return [{"name": n, "type": "partner",
            "value": da(f"{self.prefix}r{i}", 500000, 5000000),
            "since": dd(f"{self.prefix}r{i}", 365).isoformat()}
            for i, n in enumerate(["Bali Tourism Board","Ministry of Tourism","EcoTourism Alliance",
                "Travel Agents Association","Luxury Hotel Partners","SE Asia Tourism Council"])]
    def commits(self):
        items = [("Launch Vietnam eco-tourism","Expand to 3 Vietnamese destinations by Q3"),
            ("Carbon-neutral certification","Complete carbon audit and offset program"),
            ("Reduce booking cancellation","Implement AI-based demand forecasting"),
            ("5 new boutique hotel partners","Sign agreements in Sri Lanka"),
            ("Customer loyalty program","Launch tiered rewards for repeat travellers")]
        return [{"title": t, "type": "commitment", "objective": o,
            "status": dc(f"{self.prefix}cm{i}", ["active","active","completed","at_risk","active"]),
            "progress": (p := di(f"{self.prefix}cm{i}", 0, 100)/100),
            "confidence": max(0.1, p - di(f"{self.prefix}cm{i}", 0, 30)/100),
            "owner": dc(f"{self.prefix}cm{i}", ["Aarav","Priya","Rohan"]),
            "deadline": dd(f"{self.prefix}cm{i}", -30).isoformat()}
            for i, (t, o) in enumerate(items)]
    def notes(self):
        texts = ["Quarterly revenue up 23% YoY. Bali packages leading growth.",
            "Customer feedback 4.6/5 after express check-in rollout.",
            "New guide partnership in Sikkim — trial next month.",
            "Consider Sri Lanka circuit for winter — high EU demand."]
        return [{"title": f"Note {i+1}", "type": "note", "text": t,
            "author": "Nishesh", "created": dd(f"{self.prefix}n{i}", 45).isoformat()}
            for i, t in enumerate(texts)]
    def conversations(self):
        topics = [("Bali expansion strategy",["Aarav","Priya"]),
            ("Customer feedback review",["Rohan","Nishesh"]),
            ("Q3 marketing budget",["Priya","Ishita"]),
            ("Vendor negotiation — Vietnam",["Aarav","Ananya"])]
        return [{"title": t, "type": "conversation", "participants": p,
            "messages": [f"Let's discuss {t.lower()}","I've prepared the analysis.","Great — schedule a follow-up."],
            "status": "active"} for i, (t, p) in enumerate(topics)]


class MfgData(OrgData):
    def __init__(self):
        super().__init__("Precision Components Ltd", "Manufacturing",
            "Industrial components for automotive and aerospace.")
    def customers(self):
        return [{"name": n, "type": "customer",
            "email": f"proc@{n.lower().replace(' ','')}.com",
            "city": dc(f"{self.prefix}c{i}", ["Pune","Chennai","Ahmedabad","Coimbatore"]),
            "tier": dc(f"{self.prefix}ct{i}", ["standard","vip","standard"]),
            "total_spent": da(f"{self.prefix}c{i}", 200000, 8000000),
            "since": dd(f"{self.prefix}c{i}", 365).isoformat()}
            for i, n in enumerate(["AutoPart Industries","AeroTech Solutions","MechWorks Engineering",
                "DriveLine Systems","Rotary Components Inc","SteelCraft Ltd"])]
    def suppliers(self):
        return [{"name": n, "type": "supplier",
            "category": dc(f"{self.prefix}s{i}", ["raw_material","tooling","heat_treatment","logistics"]),
            "contract": da(f"{self.prefix}s{i}", 1000000, 10000000),
            "since": dd(f"{self.prefix}s{i}", 365).isoformat()}
            for i, n in enumerate(["SteelMelt Corp","AlloyWorks India","ToolingPro Systems",
                "HeatTreat Specialists","RawMaterial Hub"])]
    def invoices(self):
        return [{"invoice_number": f"PC-2026-{2000+i}", "type": "invoice",
            "total": da(f"{self.prefix}i{i}", 50000, 1500000),
            "status": dc(f"{self.prefix}ip{i}", ["paid","paid","paid","pending"]),
            "description": dc(f"{self.prefix}id{i}", ["CNC Batch A7","Precision Gears #8921",
                "Titanium Brackets Aerospace","Assembly Supply Q2","Custom Tooling Proto"]),
            "issue_date": dd(f"{self.prefix}i{i}", 60).isoformat(),
            "due_date": dd(f"{self.prefix}i{i}", 30).isoformat()}
            for i in range(25)]
    def relationships(self):
        return [{"name": n, "type": "partner",
            "value": da(f"{self.prefix}r{i}", 300000, 3000000),
            "since": dd(f"{self.prefix}r{i}", 365).isoformat()}
            for i, n in enumerate(["Automotive Parts Assoc","ISO Certification Board",
                "Industrial Training Institute","Export Promotion Council","Tech Innovation Hub"])]
    def commits(self):
        items = [("AS9100D certification","Complete audit and certification by Q4"),
            ("Defect rate below 0.1%","Implement SPC across all lines"),
            ("EV supply chain expansion","Qualify as Tier 1 supplier for 3 EV makers"),
            ("Predictive maintenance","Deploy IoT sensors on all CNC machines"),
            ("30% capacity increase","New facility in Coimbatore SEZ")]
        return [{"title": t, "type": "commitment", "objective": o,
            "status": dc(f"{self.prefix}cm{i}", ["active","active","at_risk","active","completed"]),
            "progress": (p := di(f"{self.prefix}cm{i}", 0, 100)/100),
            "confidence": max(0.1, p - di(f"{self.prefix}cm{i}", 0, 30)/100),
            "owner": dc(f"{self.prefix}cm{i}", ["Ravi","Sneha","Anand"]),
            "deadline": dd(f"{self.prefix}cm{i}", -30).isoformat()}
            for i, (t, o) in enumerate(items)]
    def notes(self):
        return [{"title": f"Note {i+1}", "type": "note", "text": t,
            "author": "Nishesh", "created": dd(f"{self.prefix}n{i}", 45).isoformat()}
            for i, t in enumerate(["AS9100D audit Oct 15. Pre-audit at 87% readiness.",
                "New CNC machine delivered — 2 weeks calibration.",
                "Raw material costs up 8%. Re-negotiate contracts.",
                "EV supply chain: passed review with 2 manufacturers."])]
    def conversations(self):
        topics = [("AS9100D audit prep",["Ravi","Nishesh"]),
            ("Supplier renegotiation",["Sneha","Anand"]),
            ("EV supply chain qualification",["Anand","Nishesh"]),
            ("Production line expansion",["Ravi","Sneha"])]
        return [{"title": t, "type": "conversation", "participants": p,
            "messages": [f"Status on {t.lower()}","Assessment complete.","Review findings."],
            "status": "active"} for i, (t, p) in enumerate(topics)]


class HealthData(OrgData):
    def __init__(self):
        super().__init__("NovaCare Health Systems", "Healthcare",
            "Multi-specialty network with 4 hospitals and 12 clinics.")
    def customers(self):
        return [{"name": n, "type": "customer",
            "email": f"{n.lower().replace(' ','').replace('dr.','dr')}@novacare.in",
            "city": dc(f"{self.prefix}c{i}", ["Bangalore","Chennai","Hyderabad"]),
            "tier": dc(f"{self.prefix}ct{i}", ["vip","standard","standard"]),
            "specialty": dc(f"{self.prefix}cs{i}", ["Cardiology","Neurology","Orthopedics","Oncology"]),
            "total_spent": da(f"{self.prefix}c{i}", 200000, 3000000),
            "since": dd(f"{self.prefix}c{i}", 365).isoformat()}
            for i, n in enumerate(["Dr. Meera Krishnan","Dr. Sanjay Verma","Dr. Anita Deshmukh",
                "Dr. Prakash Rao","Dr. Lakshmi Nair","Dr. Arun Khanna","Dr. Deepa Menon","Dr. Vijay Shetty"])]
    def suppliers(self):
        return [{"name": n, "type": "supplier",
            "category": dc(f"{self.prefix}s{i}", ["pharmaceutical","equipment","consumables","furniture"]),
            "contract": da(f"{self.prefix}s{i}", 500000, 5000000),
            "since": dd(f"{self.prefix}s{i}", 365).isoformat()}
            for i, n in enumerate(["MediSupply Pharma","Surgical Instruments Co","DiagnosticLab Partners",
                "Hospital Furniture Ltd","CleanRoom Supplies"])]
    def invoices(self):
        return [{"invoice_number": f"NH-2026-{3000+i}", "type": "invoice",
            "total": da(f"{self.prefix}i{i}", 25000, 800000),
            "status": dc(f"{self.prefix}ip{i}", ["paid","paid","pending","paid","overdue"]),
            "description": dc(f"{self.prefix}id{i}", ["ICU Ventilator Systems","QR Surgery Supplies",
                "Pharma Consignment #4281","Diagnostic Lease Q2","Clinic Renovation Phase 2"]),
            "issue_date": dd(f"{self.prefix}i{i}", 60).isoformat(),
            "due_date": dd(f"{self.prefix}i{i}", 30).isoformat()}
            for i in range(25)]
    def relationships(self):
        return [{"name": n, "type": "partner",
            "value": da(f"{self.prefix}r{i}", 200000, 2000000),
            "since": dd(f"{self.prefix}r{i}", 365).isoformat()}
            for i, n in enumerate(["NABH Accreditation Body","Medical Council of India",
                "Health Insurance Alliance","Pharma Regulation Board","Medical Research Foundation"])]
    def commits(self):
        items = [("NABH re-accreditation","Complete renewal by Dec 2026"),
            ("Telemedicine platform","Virtual consultation for 3 departments"),
            ("Reduce wait time 40%","Optimize scheduling and resources"),
            ("EHR across 12 clinics","Complete digital records migration"),
            ("95% bed occupancy","Optimize patient flow and discharge")]
        return [{"title": t, "type": "commitment", "objective": o,
            "status": dc(f"{self.prefix}cm{i}", ["active","active","at_risk","active","active"]),
            "progress": (p := di(f"{self.prefix}cm{i}", 0, 100)/100),
            "confidence": max(0.1, p - di(f"{self.prefix}cm{i}", 0, 30)/100),
            "owner": dc(f"{self.prefix}cm{i}", ["Dr. Meera","Dr. Arun","Dr. Lakshmi"]),
            "deadline": dd(f"{self.prefix}cm{i}", -30).isoformat()}
            for i, (t, o) in enumerate(items)]
    def notes(self):
        return [{"title": f"Note {i+1}", "type": "note", "text": t,
            "author": "Nishesh", "created": dd(f"{self.prefix}n{i}", 45).isoformat()}
            for i, t in enumerate(["NABH pre-audit 89%. Documentation gaps being addressed.",
                "Telemedicine pilot: 32% reduction in follow-ups.",
                "New MRI at Bangalore Central — operational next week.",
                "EHR migration at 60% — 7 clinics done, 5 remaining."])]
    def conversations(self):
        topics = [("NABH re-accreditation",["Dr. Meera","Nishesh"]),
            ("Telemedicine review",["Dr. Arun","Dr. Lakshmi"]),
            ("EHR migration progress",["Dr. Lakshmi","Nishesh"]),
            ("Q3 equipment budget",["Dr. Meera","Dr. Vijay"])]
        return [{"title": t, "type": "conversation", "participants": p,
            "messages": [f"Update on {t.lower()}","Good progress.","Let's review this week."],
            "status": "active"} for i, (t, p) in enumerate(topics)]


ORGS = [TravelData(), MfgData(), HealthData()]


# ═══════════════════════════════════════════════════════════════════
# PHASE 2 — Enrichment: narrative depth, interconnection, AI context
# ═══════════════════════════════════════════════════════════════════

def enrich(space: FounderSpace, org: OrgData, identity_id: str):
    """Add historical continuity, AI context, and cross-references."""
    p = org.prefix
    created = 0

    # ── Historical timeline events ──────────────────────────────
    # Past achievements, decisions, and milestones
    history_items = []
    if org.industry == "Travel & Tourism":
        history_items = [
            ("Launched Bali circuit", "Completed first 10 Bali adventure packages with 97% satisfaction."),
            ("Signed Thailand partnership", "Bangkok office opened. 3 new routes in planning."),
            ("Achieved 4.5★ rating", "Crossed 500 reviews on Google with 4.5★ average."),
            ("Hired first COO", "Rohan Kapoor joined as COO. Operations team restructured."),
            ("Q1 revenue milestone", "Q1 FY2026 revenue crossed ₹2.5Cr. 40% YoY growth."),
        ]
    elif org.industry == "Manufacturing":
        history_items = [
            ("ISO 9001:2025 recertified", "Passed recertification audit with 94% score. No non-conformities."),
            ("EV pilot production", "Delivered first EV motor housing batch to AutoPart for testing."),
            ("New 5-axis CNC online", "DMG MORI 5-axis CNC installed. Precision tolerance ±0.002mm."),
            ("Export order secured", "First export order: ₹45L from German automotive Tier 1 supplier."),
            ("Q1 production record", "Produced 12,000 units in Q1. 15% above target."),
        ]
    elif org.industry == "Healthcare":
        history_items = [
            ("NABH accreditation renewed", "Successfully renewed NABH accreditation for all 4 hospitals."),
            ("Robotic surgery launched", "Da Vinci XI system installed. First 50 surgeries completed."),
            ("Telemedicine pilot success", "500+ virtual consultations completed in Cardiology pilot."),
            ("Bangalore Central expansion", "New 50-bed wing opened. ICU capacity doubled."),
            ("Q1 patient milestone", "Served 15,000+ patients across all facilities in Q1."),
        ]

    for i, (title, text) in enumerate(history_items):
        key = f"{p}-hist-{i}"
        obj = FounderObject.query.filter_by(space_id=space.space_id, name=title).first()
        if not obj:
            obj = FounderObject(
                object_id=sid(), space_id=space.space_id,
                name=title, object_type="timeline_event",
                content=json.dumps({"type": "milestone", "text": text,
                    "date": dd(key, 180).isoformat(), "author": "Nishesh"}),
                created_by=identity_id,
            )
            db.session.add(obj)
            created += 1
    print(f"  Timeline: {len(history_items)} milestones ({created} new)")

    # ── AI context: conversation summaries ──────────────────────
    # Enrich existing conversations with summaries and message history
    convs = FounderObject.query.filter_by(
        space_id=space.space_id, object_type="conversation").all()
    summaries = {
        "Bali expansion strategy": "Aarav presented Q3 expansion plan. Priya proposed targeting 3 new Vietnamese destinations. Budget approved at ₹12L. Next: feasibility study by end of month.",
        "Customer feedback review": "Rohan shared Q2 NPS score of 72 (up from 68). Key complaints: check-in delays. Action: express check-in pilot at 3 locations.",
        "Q3 marketing budget": "Priya requested ₹18L for digital campaign. Ishita proposed influencer partnership model. Decision: split 60-40 between digital and events.",
        "Vendor negotiation — Vietnam": "Aarav negotiated with 3 Vietnamese vendors. Shortlisted Hanoi EcoTours and Saigon Adventures. Terms: 15% commission, 30-day payment.",
        "AS9100D audit prep": "Ravi reported 87% readiness. Missing: calibration records for 3 gauges. Sneha assigned to complete documentation by Friday.",
        "Supplier renegotiation": "Sneha presented steel price increase of 8%. Anand recommended 6-month fixed contract with SteelMelt. Agreed: negotiate 5% cap with volume commitment.",
        "EV supply chain qualification": "Anand confirmed technical review passed. AutoPart Industries requesting sample batch of 500 units. Timeline: 3 weeks.",
        "Production line expansion": "Ravi proposed ₹2.5Cr investment for new line. Sneha concerned about ROI timeline. Decision: phased approach — ₹1Cr first phase.",
        "NABH re-accreditation": "Dr. Meera shared pre-audit score of 89%. Documentation gaps identified in 3 areas. Team assigned to close gaps within 2 weeks.",
        "Telemedicine review": "Dr. Arun reported 500+ virtual consults. 32% reduction in follow-up visits. Plan: expand to Neurology and Orthopedics next quarter.",
        "EHR migration progress": "Dr. Lakshmi confirmed 7 of 12 clinics migrated. Remaining 5 on track for Q3 completion. Training sessions scheduled for next week.",
        "Q3 equipment budget": "Dr. Meera requested ₹1.8Cr for new MRI machine. Dr. Vijay proposed leasing instead. Decision: evaluate lease vs buy with finance team.",
        "Update on EHR migration progress": "Good progress. 60% complete. On track for Q3 deadline.",
        "Update on NABH re-accreditation": "Making good progress on all fronts. Pre-audit gaps being closed.",
        "Status on AS9100D audit prep": "Assessment complete. 87% readiness. Minor gaps identified.",
        "Status on supplier renegotiation": "SteelMelt agreed to 5% cap. Contract signed for 6 months.",
        "Status on EV supply chain qualification": "Technical review passed. AutoPart requesting sample batch.",
        "Status on production line expansion": "Phase 1 equipment ordered. Installation in 3 weeks.",
        "Update on telemedicine review": "Pilot successful. Expansion plan approved for Q3.",
        "Update on EHR migration progress": "7 of 12 clinics done. Training underway.",
        "Update on Q3 equipment budget": "Lease vs buy analysis in progress. Finance team engaged.",
    }

    for conv in convs:
        name = conv.name
        summary = summaries.get(name, None)
        if summary and not conv.content:
            conv.content = json.dumps({"summary": summary, "ai_analysis": {
                "sentiment": "positive",
                "key_decisions": summary.split(".")[:2],
                "action_items": 2,
                "confidence": 0.85,
            }})
            # Add messages to the conversation if it has a FounderConversation
            fconv = FounderConversation.query.filter_by(
                object_id=conv.object_id).first()
            if not fconv:
                fconv = FounderConversation(
                    conv_id=sid(), object_id=conv.object_id,
                    title=conv.name, status="active",
                    created_by=identity_id,
                )
                db.session.add(fconv)
                db.session.flush()
                # Add 3-4 messages per conversation
                msg_texts = [
                    f"Starting discussion on {name}: we need to align on the approach.",
                    f"I've reviewed the data. Key findings: {summary[:100]}...",
                    f"Agreed. Let's proceed with the recommended approach.",
                ]
                for j, txt in enumerate(msg_texts):
                    msg = FounderMessage(
                        message_id=sid(), conv_id=fconv.conv_id,
                        sender=dc(f"{p}-msg-{j}", conv.data.get("participants", [identity_id])),
                        content=txt, created_by=identity_id,
                    )
                    db.session.add(msg)
    print(f"  Conversations enriched: {len(convs)}")

    # ── Cross-reference notes to objects ────────────────────────
    notes = FounderObject.query.filter_by(
        space_id=space.space_id, object_type="note").all()
    customers = FounderObject.query.filter_by(
        space_id=space.space_id, object_type="customer").all()
    for note in notes:
        if customers and not note.content:
            ref = dc(f"{p}-xref-{note.object_id}", customers)
            note.content = json.dumps({
                "text": json.loads(note.content or "{}").get("text", note.name),
                "references": [{"type": "customer", "id": ref.object_id, "name": ref.name}],
            })
    print(f"  Notes cross-referenced: {len(notes)}")

    # ── AI confidence explanations for commitments ──────────────
    commits = FounderObject.query.filter_by(
        space_id=space.space_id, object_type="commitment").all()
    for cm in commits:
        data = json.loads(cm.content or "{}") if cm.content else {}
        if "confidence_factors" not in data:
            progress = data.get("progress", 0.5)
            data["confidence_factors"] = [
                f"{round(progress * 100)}% completion progress",
                "3 evidence items verified this week",
                "No overdue dependencies detected",
                "Owner is actively engaged",
            ]
            if progress < 0.3:
                data["confidence_factors"].append("⚠️ Early stage — limited evidence available")
            elif progress > 0.8:
                data["confidence_factors"].append("✅ Near completion — final verification pending")
            data["next_action"] = dc(f"{p}-na-{cm.object_id}", [
                "Review completed work and update status",
                "Schedule checkpoint meeting with stakeholders",
                "Document remaining risks and mitigation plan",
                "Verify evidence completeness before closing",
            ])
            cm.content = json.dumps(data)
    print(f"  Commitments enriched: {len(commits)}")

    db.session.commit()
    return created


# ═══════════════════════════════════════════════════════════════════
# SEEDER
# ═══════════════════════════════════════════════════════════════════

def seed():
    parser = argparse.ArgumentParser(description="SHUNYA Living Demonstration Environment")
    parser.add_argument("--phase", type=int, default=2, choices=[1, 2],
        help="Seed phase: 1 = basic objects, 2 = +enrichment (default)")
    args = parser.parse_args()

    app = create_app()
    with app.app_context():
        print("╔══════════════════════════════════════════════════════════╗")
        print("║  SHUNYA — Living Demonstration Environment v2           ║")
        print("╚══════════════════════════════════════════════════════════╝")
        print(f"\nSeed: {_SEED}  Phase: {args.phase}")

        existing = FounderObject.query.count()
        print(f"Existing objects: {existing}\n")

        identity_id = "demo-founder-001"

        # ── Create canonical identity via IdentityRepository ─────
        # This ensures the identity_id matches what the signin pipeline
        # produces. No HTTP requests, no cookie decoding, no post-hoc linking.
        try:
            from app.production.identity_repository import IdentityRepository
            repo = IdentityRepository()
            ident = repo.create_core(
                display_name="Nishesh",
                entity_type="human",
                auth_methods=[{"method_type": "email", "identifier": FOUNDER_EMAIL}],
            )
            identity_id = ident.identity_id
            print(f"  ✅ Canonical identity: {FOUNDER_EMAIL} → {identity_id[:20]}...")
        except Exception as e:
            print(f"  ⚠️  Could not create canonical identity: {e}")

        # ── Phase 1: Basic objects ──────────────────────────────
        for org in ORGS:
            print(f"─── {org.name} ({org.industry}) ───")
            space = FounderSpace.query.filter_by(name=org.name).first()
            if not space:
                space = FounderSpace(
                    space_id=f"space-{org.prefix}", name=org.name,
                    description=org.desc, space_type="organization",
                    identity_id=identity_id,
                )
                db.session.add(space)
                db.session.flush()
                print(f"  Created space")

            for kind, items in [
                ("customer", org.customers()), ("supplier", org.suppliers()),
                ("invoice", org.invoices()), ("commitment", org.commits()),
                ("note", org.notes()), ("conversation", org.conversations()),
            ]:
                new = 0
                for item in items:
                    name = item.get("name") or item.get("invoice_number") or item.get("title")
                    if not FounderObject.query.filter_by(space_id=space.space_id, name=name).first():
                        obj = FounderObject(
                            object_id=sid(), space_id=space.space_id,
                            name=name, object_type=kind,
                            content=json.dumps(item), created_by=identity_id,
                        )
                        db.session.add(obj)
                        new += 1
                print(f"  {kind.capitalize()}s: {len(items)} ({new} new)")
            db.session.commit()

        total_p1 = FounderObject.query.count()
        print(f"\nPhase 1 done: {total_p1} objects")

        # ── Phase 2: Enrichment (skip if --phase 1) ─────────────
        if args.phase >= 2:
            print(f"\n─── Phase 2: Enrichment ───")
            enriched = 0
            for org in ORGS:
                space = FounderSpace.query.filter_by(name=org.name).first()
                if space:
                    enriched += enrich(space, org, identity_id)
            print(f"Phase 2 done: {enriched} new items")

        total = FounderObject.query.count()
        print(f"\n Total: {total} objects across {len(ORGS)} orgs")
        print(f" Done.")


if __name__ == "__main__":
    seed()