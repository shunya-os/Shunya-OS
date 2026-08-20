"""
Founder Demo Access Final Remediation — G4 permission grant + dynamic ID resolution.

Fixes:
1. Seeds default roles for the demo organization
2. Assigns the demo user to the admin role (grants rel.view and all G4/G5 permissions)
3. All IDs resolved dynamically from canonical records (no hard-coded IDs)
"""

import sys; sys.path.insert(0, '.')
from dotenv import load_dotenv; load_dotenv()
import os
from datetime import datetime, timezone, timedelta
from decimal import Decimal

app = None

def get_app():
    global app
    if app is None:
        from app import create_app, db
        app = create_app(config_override={
            'TESTING': False,
            'SQLALCHEMY_DATABASE_URI': os.environ.get('DATABASE_URL'),
            'SECRET_KEY': os.environ.get('SECRET_KEY', 'dev-secret'),
        })
    return app

def resolve_demo_org():
    """Dynamically resolve demo organization by slug — no hard-coded IDs."""
    from app import db
    from app.models import Organization
    org = Organization.query.filter_by(slug='shunya-demo-org').first()
    if not org:
        org = Organization(name='SHUNYA Demo Org', slug='shunya-demo-org', business_type='other', is_active=True)
        db.session.add(org)
        db.session.flush()
        print(f'Created org: {org.id} (slug: shunya-demo-org)')
    else:
        print(f'Using existing org: {org.id} ({org.name})')
    return org.id

def resolve_demo_tenant():
    """Dynamically resolve demo tenant by slug — no hard-coded IDs."""
    from app import db
    from app.tenant import Tenant
    tenant = Tenant.query.filter_by(slug='shunya-demo').first()
    if not tenant:
        tenant = Tenant(company_name='SHUNYA Demo', slug='shunya-demo', subdomain='demo', is_active=True)
        db.session.add(tenant)
        db.session.flush()
        print(f'Created tenant: {tenant.id} (slug: shunya-demo)')
    else:
        print(f'Using existing tenant: {tenant.id}')
    return tenant.id

def resolve_demo_email():
    return 'founder@demo.shunyaos.com'

def resolve_demo_password():
    from dotenv import load_dotenv; load_dotenv()
    return os.environ.get('DEMO_FOUNDER_PASSWORD', '')

def provision_identity(org_id, tenant_id):
    """Provision or update the demo identity. Returns (team_member, org_member)."""
    from app import db
    from app.auth import TeamMember, UserRole
    from app.models import OrgMember
    import uuid
    
    email = resolve_demo_email()
    password = resolve_demo_password()
    identity_id = f'sid_demo_{uuid.uuid4().hex[:30]}'
    
    # TeamMember
    tm = TeamMember.query.filter_by(email=email).first()
    if not tm:
        tm = TeamMember(name='SHUNYA Founder', email=email, role=UserRole.ADMIN.value, is_active=True)
        tm.set_password(password)
        db.session.add(tm)
        db.session.flush()
        db.session.execute(
            db.text("UPDATE team_members SET tenant_id = :tid WHERE id = :mid"),
            {'tid': tenant_id, 'mid': tm.id}
        )
        db.session.commit()
        db.session.refresh(tm)
        print(f'Created team member: {tm.id}')
    else:
        print(f'Using existing team member: {tm.id}')
        tm.set_password(password)
        # Check if tenant_id is set via raw SQL
        result = db.session.execute(
            db.text("SELECT tenant_id FROM team_members WHERE id = :mid"),
            {'mid': tm.id}
        ).scalar()
        if not result:
            db.session.execute(
                db.text("UPDATE team_members SET tenant_id = :tid WHERE id = :mid"),
                {'tid': tenant_id, 'mid': tm.id}
            )
            db.session.commit()
    
    # OrgMember
    om = OrgMember.query.filter_by(organization_id=org_id, email=email).first()
    if not om:
        om = OrgMember(organization_id=org_id, identity_id=identity_id, name='SHUNYA Founder', email=email, role='admin', is_active=True)
        db.session.add(om)
        db.session.flush()
        print(f'Created org member: id={om.id}, identity={identity_id}')
    else:
        print(f'Using existing org member: id={om.id}, identity={om.identity_id}')
    
    db.session.commit()
    return tm, om

def grant_permissions(org_id, om):
    """Seed default roles and grant admin role to the demo user."""
    from app import db
    from app.authz.services import seed_default_roles
    from app.authz.models import Role, OrgMemberRole
    
    # Seed default roles for this org (no-op if already seeded)
    seed_default_roles(org_id)
    db.session.commit()
    
    # Find the admin role for this org
    admin_role = Role.query.filter_by(organization_id=org_id, name='admin').first()
    if not admin_role:
        print(f'ERROR: admin role not found for org {org_id}!')
        return False
    
    # Check if already assigned
    existing = OrgMemberRole.query.filter_by(
        organization_id=org_id,
        member_id=om.id,
        role_id=admin_role.id,
    ).first()
    
    if not existing:
        assignment = OrgMemberRole(
            organization_id=org_id,
            member_id=om.id,
            role_id=admin_role.id,
            granted_by='system',
        )
        db.session.add(assignment)
        db.session.commit()
        print(f'Granted admin role {admin_role.id} to member {om.id}')
    else:
        print(f'Member {om.id} already has admin role {admin_role.id}')
    
    # Verify
    from app.authz.services import check_permission
    has_rel_view = check_permission(org_id, om.identity_id, 'rel.view')
    has_rel_create = check_permission(org_id, om.identity_id, 'rel.create')
    has_proposal_view = check_permission(org_id, om.identity_id, 'proposal.view')
    print(f'  rel.view: {has_rel_view}')
    print(f'  rel.create: {has_rel_create}')
    print(f'  proposal.view: {has_proposal_view}')
    
    return has_rel_view

def seed_demo_data(org_id, tenant_id, om):
    """Seed demo G4 + G5 data. Uses dynamically resolved IDs."""
    from app import db
    from app.marketing.models import Experiment
    from app.marketing_os.service import create_campaign, create_audience, create_content, capture_lead
    from app.commercial.service import create_opportunity, create_proposal, transition_proposal
    from app.g5.service import (
        record_interaction, create_attribution, create_learning, record_campaign_event
    )
    from app.crm.service import create_lead_with_identity
    from app.models import Lead
    
    email = resolve_demo_email()
    
    # Check if demo data already exists
    from app.marketing.models import Campaign
    existing = Campaign.query.filter_by(tenant_id=tenant_id).count()
    if existing >= 3:
        print(f'Demo data already exists ({existing} campaigns), skipping seed.')
        return
    
    # ── Campaign 1: Product Launch (active) ──
    camp1 = create_campaign(
        name="Q3 Product Launch", tenant_id=tenant_id,
        description="Launch of the new SHUNYA Intelligence Engine v3",
        objective="awareness", owner="SHUNYA Founder",
        status="active", budget=500000, budget_type="total",
        start_date=datetime.now(timezone.utc) - timedelta(days=14),
        end_date=datetime.now(timezone.utc) + timedelta(days=30),
        utm_source="multi", utm_campaign="q3_product_launch", utm_medium="multi",
        created_by=email,
    )
    cid1 = camp1.id
    print(f'Campaign 1: {cid1} — Q3 Product Launch')
    
    record_campaign_event(cid1, tenant_id, "campaign_created", new_state="draft", created_by=email)
    record_campaign_event(cid1, tenant_id, "campaign_activated", new_state="active", created_by=email)
    create_audience(cid1, "Tech Decision Makers", tenant_id, description="CTOs, VPs of Engineering", source="manual")
    create_content(cid1, "Product Launch Announcement", tenant_id, content_type="post", owner="SHUNYA Founder")
    create_content(cid1, "Technical Whitepaper", tenant_id, content_type="document", owner="SHUNYA Founder")
    
    for i in range(8):
        record_interaction(
            tenant_id=tenant_id, campaign_id=cid1,
            interaction_type="website_visit" if i % 2 == 0 else "email_interaction",
            identity_ref=f"lead_{i+1}@example.com", person_name=f"Lead {i+1}",
            person_email=f"lead_{i+1}@example.com",
            source="google_ads" if i < 4 else "linkedin",
            utm_source="google" if i < 4 else "linkedin",
            utm_campaign="q3_product_launch",
            engagement_duration_seconds=120 + (i * 30), engagement_depth=i + 1,
        )
    
    for i in range(5):
        lead = create_lead_with_identity(
            tenant_id=org_id, name=f"Demo Lead {i+1}",
            phone=f"+1-555-DEMO-{i+1:03d}", email=f"demo_lead_{i+1}@example.com",
            source="campaign",
        )
        lead.campaign_id = cid1
        lead.utm_source = "google" if i < 3 else "linkedin"
        lead.utm_campaign = "q3_product_launch"
    db.session.commit()
    
    leads = Lead.query.filter_by(campaign_id=cid1).all()
    opps = []
    for i, lead in enumerate(leads[:3]):
        opp = create_opportunity(
            organization_id=org_id, title=f"Q3 Product — {lead.customer_name or 'Lead'}",
            campaign_id=cid1, source="campaign", created_by=email,
        )
        opp.estimated_value = Decimal(str(25000 + (i * 10000)))
        opps.append(opp)
    
    props = []
    for i, opp in enumerate(opps[:2]):
        prop = create_proposal(
            organization_id=org_id, opportunity_id=opp.id,
            title=f"Enterprise Plan — {opp.title[:40]}",
            total_value=float(opp.estimated_value or 0), created_by=email,
        )
        transition_proposal(prop, "sent", "Sent to prospect", triggered_by=email)
        if i == 0:
            transition_proposal(prop, "accepted", "Accepted", triggered_by=email)
        props.append(prop)
    
    create_attribution(
        tenant_id=tenant_id, campaign_id=cid1,
        target_type="opportunity", target_id=opps[0].id,
        attribution_state="directly_linked", confidence=95,
        is_first_known=True, source="google_ads",
        opportunity_id=opps[0].id, target_description="First opportunity from Q3 campaign",
    )
    create_attribution(
        tenant_id=tenant_id, campaign_id=cid1,
        target_type="proposal", target_id=props[0].id,
        attribution_state="directly_linked", confidence=95,
        revenue_amount=25000.00, is_revenue_outcome=True,
        opportunity_id=opps[0].id, proposal_id=props[0].id,
    )
    
    create_learning(tenant_id=tenant_id, campaign_id=cid1,
        category="channel_effectiveness",
        title="Google Ads driving highest quality leads",
        observation="Google Ads CPA is 40% lower than LinkedIn",
        significance="significant", confidence=82,
        recommendation="Increase Google Ads budget by 25%",
        recommendation_confidence=78, recommendation_action="Increase Google Ads spend",
        is_actionable=True, created_by=email,
    )
    create_learning(tenant_id=tenant_id, campaign_id=cid1,
        category="campaign_performance",
        title="Q3 Product Launch on track for 200% ROI",
        observation="Campaign produced 5 qualified opportunities and 1 accepted proposal (₹25,000)",
        significance="significant", confidence=85,
        recommendation="Continue current strategy", recommendation_confidence=80,
        recommendation_action="Maintain campaign trajectory", is_actionable=True, created_by=email,
    )
    
    # Campaign 2: Newsletter (draft, empty)
    camp2 = create_campaign(name="Monthly Newsletter", tenant_id=tenant_id,
        description="Monthly email newsletter for existing customers",
        objective="retention", owner="SHUNYA Founder", status="draft",
        budget=50000, budget_type="monthly", utm_source="email",
        utm_campaign="monthly_newsletter", utm_medium="email", created_by=email,
    )
    record_campaign_event(camp2.id, tenant_id, "campaign_created", new_state="draft", created_by=email)
    
    # Campaign 3: Referral (paused, underperforming)
    camp3 = create_campaign(name="Customer Referral Program", tenant_id=tenant_id,
        description="Refer a friend and earn 10% commission",
        objective="acquisition", owner="SHUNYA Founder", status="paused",
        budget=150000, budget_type="total", utm_source="referral",
        utm_campaign="referral_program", utm_medium="referral", created_by=email,
    )
    record_campaign_event(camp3.id, tenant_id, "campaign_created", new_state="draft", created_by=email)
    record_campaign_event(camp3.id, tenant_id, "campaign_activated", new_state="active", created_by=email)
    record_campaign_event(camp3.id, tenant_id, "campaign_underperforming",
        description="Below target: only 2 referrals in 30 days", created_by=email)
    record_campaign_event(camp3.id, tenant_id, "campaign_paused", new_state="paused",
        description="Paused for strategy review", created_by=email)
    
    lead = create_lead_with_identity(tenant_id=org_id, name="Referred Lead", email="referred@example.com", source="referral")
    lead.campaign_id = camp3.id
    lead.utm_source = "referral"
    lead.utm_campaign = "referral_program"
    db.session.commit()
    
    create_learning(tenant_id=tenant_id, campaign_id=camp3.id,
        category="waste_detection",
        title="Referral program underperforming",
        observation="Only 2 referrals in 45 days with ₹150k budget allocated",
        significance="critical", confidence=90,
        recommendation="Consider revising referral incentives or pausing program",
        recommendation_confidence=85, recommendation_action="Review referral strategy",
        is_actionable=True, created_by=email,
    )
    
    exp = Experiment(campaign_id=cid1, name="Landing Page A/B Test",
        hypothesis="New hero section increases conversion by 15%",
        variant="B", status="running", metric="conversion_rate",
        sample_size=500, tenant_id=tenant_id)
    db.session.add(exp)
    db.session.commit()
    
    print(f'Demo data seeded: 3 campaigns, 8 interactions, 6 leads, 3 opps, 2 proposals, 2 attributions, 3 learnings')

def run():
    """Run the full remediation."""
    app = get_app()
    with app.app_context():
        print("=== FOUNDER DEMO ACCESS FINAL REMEDIATION ===\n")
        
        # Step 1: Resolve org and tenant dynamically
        org_id = resolve_demo_org()
        tenant_id = resolve_demo_tenant()
        print(f'Org ID: {org_id}, Tenant ID: {tenant_id}')
        
        # Step 2: Provision identity
        tm, om = provision_identity(org_id, tenant_id)
        print(f'Identity: {om.identity_id}')
        
        # Step 3: Grant permissions (FIX FOR ISSUE 1)
        print('\n--- Granting G4 permissions ---')
        success = grant_permissions(org_id, om)
        print(f'Permission grant result: {"SUCCESS" if success else "FAILED"}')
        
        # Step 4: Seed demo data (FIX FOR ISSUE 2 — dynamic IDs)
        print('\n--- Seeding demo data ---')
        seed_demo_data(org_id, tenant_id, om)
        
        print('\n=== REMEDIATION COMPLETE ===')

if __name__ == '__main__':
    run()