"""Shunya Legal & Compliance Routes — Dashboard, Summary, Seed Data."""
from flask import Blueprint, render_template, jsonify, g
from app import db
from app.models import Entity, EntityDefinition
from app.routes.auth import login_required
from app.shunya.legal import LEGAL_ENTITY_TYPES, LegalDashboard, _ensure_legal_types

legal_bp = Blueprint("legal", __name__, url_prefix="/legal")


@legal_bp.route("")
@login_required
def legal_dashboard():
    """Legal & compliance overview."""
    _ensure_legal_types(g.tenant.id)

    # Seed sample data if no entities exist yet
    _seed_sample_data(g.tenant.id)

    overview = LegalDashboard.get_overview(g.tenant.id)

    return render_template("legal/dashboard.html",
        contracts=overview["contracts"],
        templates=overview["templates"],
        compliance=overview["compliance"],
        active_contracts=overview["active_contracts"],
        expiring_soon=overview["expiring_soon"],
        pending_signatures=overview["pending_signatures"],
        total_contract_value=overview["total_contract_value"],
        non_compliant=overview["non_compliant"],
        compliant_count=overview["compliant_count"],
        contract_statuses=overview["contract_statuses"],
    )


@legal_bp.route("/api/summary")
@login_required
def legal_summary():
    """JSON summary endpoint."""
    cont_def = db.session.query(EntityDefinition).filter_by(
        tenant_id=g.tenant.id, type="contract"
    ).first()
    comp_def = db.session.query(EntityDefinition).filter_by(
        tenant_id=g.tenant.id, type="compliance_item"
    ).first()

    contracts = []
    if cont_def:
        contracts = db.session.query(Entity).filter_by(
            tenant_id=g.tenant.id, definition_id=cont_def.id
        ).all()

    compliance = []
    if comp_def:
        compliance = db.session.query(Entity).filter_by(
            tenant_id=g.tenant.id, definition_id=comp_def.id
        ).all()

    return jsonify({
        "total_contracts": len(contracts),
        "active_contracts": len([c for c in contracts if c.status == "active"]),
        "expiring_soon": len([c for c in contracts if c.status == "expiring_soon"]),
        "total_value": sum(float(c.data.get("value", 0) or 0) for c in contracts if c.status == "active"),
        "compliance_compliant": len([c for c in compliance if c.status == "compliant"]),
        "compliance_non_compliant": len([c for c in compliance if c.status in ("non_compliant", "overdue")]),
    })


def _seed_sample_data(tenant_id: int):
    """Create sample legal entities if none exist for this tenant."""
    cont_def = db.session.query(EntityDefinition).filter_by(
        tenant_id=tenant_id, type="contract"
    ).first()
    if not cont_def:
        return

    existing_count = db.session.query(db.func.count(Entity.id)).filter_by(
        tenant_id=tenant_id, definition_id=cont_def.id
    ).scalar() or 0

    if existing_count > 0:
        return  # Already seeded

    now = __import__("datetime").datetime.utcnow()

    contract_data = [
        ("Office Lease - Downtown", "active", "lease", "Prime Properties Inc.", 1200000, "3-year lease for HQ office space."),
        ("NDA - Strategic Partner", "active", "nda", "TechVentures Ltd.", 0, "Mutual non-disclosure for product collaboration."),
        ("Client SLA - Enterprise", "active", "service", "MegaCorp Industries", 4500000, "Annual service level agreement with 99.9% uptime SLA."),
        ("Vendor Supply Agreement", "expiring_soon", "vendor", "Global Supplies Co.", 2800000, "Bulk hardware supply agreement — renew in 45 days."),
        ("Employment - CTO", "pending_signature", "employment", "Dr. Ananya Sharma", 0, "Offer letter pending signature."),
        ("Partnership - JV", "draft", "partnership", "InnovateX Pvt. Ltd.", 0, "Joint venture for AI product line."),
        ("Software License Renewal", "expired", "service", "SaaSCorp Solutions", 850000, "Annual software license — expired last month, negotiating renewal."),
    ]

    sample_contracts = []
    for i, data in enumerate(contract_data):
        sample_contracts.append(Entity(
            tenant_id=tenant_id, definition_id=cont_def.id,
            code=f"CTR-{i:04d}", display_name=data[0],
            status=data[1],
            data={
                "title": data[0],
                "contract_type": data[2],
                "party_a": "Shunya Corp",
                "party_b": data[3],
                "value": data[4],
                "start_date": (now.replace(year=now.year - 1)).strftime("%Y-%m-%d"),
                "end_date": (now.replace(year=now.year + 2)).strftime("%Y-%m-%d"),
                "notes": data[5],
            },
        ))

    tmpl_def = db.session.query(EntityDefinition).filter_by(
        tenant_id=tenant_id, type="document_template"
    ).first()
    sample_templates = []
    if tmpl_def:
        sample_templates = [
            Entity(
                tenant_id=tenant_id, definition_id=tmpl_def.id,
                code=f"TPL-{i:04d}", display_name=data[0],
                status="active",
                data={
                    "name": data[0],
                    "category": data[1],
                    "content": data[2],
                    "version": "1.0",
                },
            )
            for i, data in enumerate([
                ("Standard NDA Agreement", "agreement", "This NDA agreement is entered into by and between..."),
                ("Employee Offer Letter", "letter", "Dear [candidate_name], We are pleased to offer you..."),
                ("Service Level Agreement", "agreement", "This Service Level Agreement outlines the terms..."),
                ("Vendor Contract Template", "agreement", "This Vendor Contract is made on [date] between..."),
            ])
        ]

    comp_def = db.session.query(EntityDefinition).filter_by(
        tenant_id=tenant_id, type="compliance_item"
    ).first()
    sample_compliance = []
    if comp_def:
        sample_compliance = [
            Entity(
                tenant_id=tenant_id, definition_id=comp_def.id,
                code=f"CPL-{i:04d}", display_name=data[0],
                status=data[1],
                data={
                    "regulation": data[0],
                    "category": data[2],
                    "description": data[3],
                    "due_date": data[4],
                    "assigned_to": data[5],
                },
            )
            for i, data in enumerate([
                ("ISO 27001 Certification", "in_progress", "iso", "Information security management system certification.", (now.replace(year=now.year + 1)).strftime("%Y-%m-%d"), "Security Team"),
                ("GDPR Compliance Audit", "pending", "gdpr", "Annual data protection compliance review.", (now.replace(year=now.year)).strftime("%Y-%m-%d"), "DPO Office"),
                ("Tax Filing - FY2026", "non_compliant", "tax", "Quarterly GST and income tax filings.", (now.replace(month=3, day=31)).strftime("%Y-%m-%d"), "Finance Dept"),
                ("Workplace Safety Inspection", "compliant", "safety", "Annual safety audit by regulatory board.", (now.replace(year=now.year + 1, month=6, day=15)).strftime("%Y-%m-%d"), "Facilities"),
                ("Environmental Compliance", "compliant", "environmental", "Waste disposal and emissions compliance report.", (now.replace(year=now.year + 1, month=9, day=1)).strftime("%Y-%m-%d"), "Sustainability Team"),
                ("Labor Law Compliance", "overdue", "labor", "Minimum wage and working hours compliance verification.", (now.replace(month=1, day=15)).strftime("%Y-%m-%d"), "HR"),
            ])
        ]

    all_entities = sample_contracts + sample_templates + sample_compliance
    for entity in all_entities:
        db.session.add(entity)
    db.session.commit()