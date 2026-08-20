"""
Complete demo data seed — uses correct organization/tenant separation.
CRM operations use org_id=6 (organization). G5 models use tenant_id=66.
"""

import sys; sys.path.insert(0, '.')
from dotenv import load_dotenv; load_dotenv()
import os
from datetime import datetime, timezone, timedelta
from decimal import Decimal

from app import create_app, db
from sqlalchemy import text

DEMO_ORG_ID = 6
DEMO_TENANT_ID = 66
DEMO_EMAIL = 'founder@demo.shunyaos.com'

app = create_app(config_override={
    'TESTING': False, 'SQLALCHEMY_DATABASE_URI': os.environ.get('DATABASE_URL'),
    'SECRET_KEY': os.environ.get('SECRET_KEY', 'dev-secret'),
})

with app.app_context():
    print("=== SEEDING DEMO DATA ===\n")
    
    from app.marketing.models import Campaign, AudienceDefinition, CampaignContent, Experiment
    from app.marketing_os.service import create_campaign, create_audience, create_content, capture_lead
    from app.commercial.service import create_opportunity, create_proposal, transition_proposal
    from app.g5.service import (
        record_interaction, create_attribution, create_learning, record_campaign_event
    )
    from app.crm.service import create_lead_with_identity
    from app.models import Lead
    
    # ── Campaign 1: Product Launch ──
    camp1 = create_campaign(
        name="Q3 Product Launch",
        tenant_id=DEMO_TENANT_ID,
        description="Launch of the new SHUNYA Intelligence Engine v3",
        objective="awareness", owner="SHUNYA Founder",
        status="active", budget=500000, budget_type="total",
        start_date=datetime.now(timezone.utc) - timedelta(days=14),
        end_date=datetime.now(timezone.utc) + timedelta(days=30),
        utm_source="multi", utm_campaign="q3_product_launch", utm_medium="multi",
        created_by=DEMO_EMAIL,
    )
    cid1 = camp1.id
    print(f"Campaign 1: {cid1} — Q3 Product Launch (active)")
    
    # Events
    record_campaign_event(cid1, DEMO_TENANT_ID, "campaign_created", new_state="draft", created_by=DEMO_EMAIL)
    record_campaign_event(cid1, DEMO_TENANT_ID, "campaign_activated", new_state="active", created_by=DEMO_EMAIL)
    
    # Audience + Content
    create_audience(cid1, "Tech Decision Makers", DEMO_TENANT_ID, description="CTOs, VPs of Engineering", source="manual")
    create_content(cid1, "Product Launch Announcement", DEMO_TENANT_ID, content_type="post", owner="SHUNYA Founder")
    create_content(cid1, "Technical Whitepaper", DEMO_TENANT_ID, content_type="document", owner="SHUNYA Founder")
    
    # Interactions
    for i in range(8):
        record_interaction(
            tenant_id=DEMO_TENANT_ID, campaign_id=cid1,
            interaction_type="website_visit" if i % 2 == 0 else "email_interaction",
            identity_ref=f"lead_{i+1}@example.com",
            person_name=f"Lead {i+1}", person_email=f"lead_{i+1}@example.com",
            source="google_ads" if i < 4 else "linkedin",
            channel="cpc" if i < 4 else "social",
            utm_source="google" if i < 4 else "linkedin",
            utm_campaign="q3_product_launch",
            utm_medium="cpc" if i < 4 else "paid_social",
            engagement_duration_seconds=120 + (i * 30), engagement_depth=i + 1,
        )
    print(f"  Interactions: 8")
    
    # Leads — direct CRM calls using org_id (6) as tenant_id
    for i in range(5):
        lead = create_lead_with_identity(
            tenant_id=DEMO_ORG_ID,  # CRM uses organization ID
            name=f"Demo Lead {i+1}",
            phone=f"+1-555-DEMO-{i+1:03d}",
            email=f"demo_lead_{i+1}@example.com",
            source="campaign",
        )
        # Attach campaign to lead
        lead.campaign_id = cid1
        lead.utm_source = "google" if i < 3 else "linkedin"
        lead.utm_campaign = "q3_product_launch"
        db.session.commit()
    print(f"  Leads: 5 captured")
    
    # Lead records
    leads = Lead.query.filter_by(campaign_id=cid1).all()
    
    # Opportunities via G4
    opps = []
    for i, lead in enumerate(leads[:3]):
        opp = create_opportunity(
            organization_id=DEMO_ORG_ID,
            title=f"Q3 Product — {lead.customer_name or 'Lead'}",
            campaign_id=cid1, source="campaign", created_by=DEMO_EMAIL,
        )
        opp.estimated_value = Decimal(str(25000 + (i * 10000)))
        opps.append(opp)
    
    # Proposals
    props = []
    for i, opp in enumerate(opps[:2]):
        prop = create_proposal(
            organization_id=DEMO_ORG_ID,
            opportunity_id=opp.id,
            title=f"SHUNYA Enterprise Plan — {opp.title[:40]}",
            total_value=float(opp.estimated_value or 0),
            created_by=DEMO_EMAIL,
        )
        transition_proposal(prop, "sent", "Proposal sent to prospect", triggered_by=DEMO_EMAIL)
        if i == 0:
            transition_proposal(prop, "accepted", "Client accepted the proposal", triggered_by=DEMO_EMAIL)
        props.append(prop)
    print(f"  Opportunities: {len(opps)}, Proposals: {len(props)}")
    
    # Attributions
    create_attribution(
        tenant_id=DEMO_TENANT_ID, campaign_id=cid1,
        target_type="opportunity", target_id=opps[0].id,
        attribution_state="directly_linked", confidence=95,
        is_first_known=True, source="google_ads",
        opportunity_id=opps[0].id,
        target_description="First opportunity from Q3 campaign",
    )
    create_attribution(
        tenant_id=DEMO_TENANT_ID, campaign_id=cid1,
        target_type="proposal", target_id=props[0].id,
        attribution_state="directly_linked", confidence=95,
        revenue_amount=25000.00, is_revenue_outcome=True,
        opportunity_id=opps[0].id, proposal_id=props[0].id,
        target_description="Accepted proposal - revenue outcome",
    )
    record_campaign_event(cid1, DEMO_TENANT_ID, "conversion_occurred",
                          description="Revenue outcome: ₹25,000 from accepted proposal",
                          payload={"revenue_amount": 25000, "proposal_id": props[0].id})
    print(f"  Attributions: 2")
    
    # Learnings
    create_learning(
        tenant_id=DEMO_TENANT_ID, campaign_id=cid1,
        category="channel_effectiveness",
        title="Google Ads driving highest quality leads",
        observation="Google Ads CPA is 40% lower than LinkedIn for Q3 campaign",
        significance="significant", confidence=82,
        recommendation="Increase Google Ads budget by 25%",
        recommendation_confidence=78,
        recommendation_action="Increase Google Ads spend",
        is_actionable=True, created_by=DEMO_EMAIL,
    )
    create_learning(
        tenant_id=DEMO_TENANT_ID, campaign_id=cid1,
        category="campaign_performance",
        title="Q3 Product Launch on track for 200% ROI",
        observation="Campaign produced 5 qualified opportunities and 1 accepted proposal (₹25,000)",
        significance="significant", confidence=85,
        recommendation="Continue current strategy",
        recommendation_confidence=80,
        recommendation_action="Maintain campaign trajectory",
        is_actionable=True, created_by=DEMO_EMAIL,
    )
    
    # ── Campaign 2: Newsletter (draft, empty) ──
    camp2 = create_campaign(
        name="Monthly Newsletter", tenant_id=DEMO_TENANT_ID,
        description="Monthly email newsletter for existing customers",
        objective="retention", owner="SHUNYA Founder",
        status="draft", budget=50000, budget_type="monthly",
        utm_source="email", utm_campaign="monthly_newsletter", utm_medium="email",
        created_by=DEMO_EMAIL,
    )
    record_campaign_event(camp2.id, DEMO_TENANT_ID, "campaign_created", new_state="draft", created_by=DEMO_EMAIL)
    
    # ── Campaign 3: Referral Program (paused, underperforming) ──
    camp3 = create_campaign(
        name="Customer Referral Program", tenant_id=DEMO_TENANT_ID,
        description="Refer a friend and earn 10% commission",
        objective="acquisition", owner="SHUNYA Founder",
        status="paused", budget=150000, budget_type="total",
        start_date=datetime.now(timezone.utc) - timedelta(days=60),
        end_date=datetime.now(timezone.utc) + timedelta(days=30),
        utm_source="referral", utm_campaign="referral_program", utm_medium="referral",
        created_by=DEMO_EMAIL,
    )
    record_campaign_event(camp3.id, DEMO_TENANT_ID, "campaign_created", new_state="draft", created_by=DEMO_EMAIL)
    record_campaign_event(camp3.id, DEMO_TENANT_ID, "campaign_activated", new_state="active", created_by=DEMO_EMAIL)
    record_campaign_event(camp3.id, DEMO_TENANT_ID, "campaign_underperforming",
                          description="Below target: only 2 referrals in 30 days", created_by=DEMO_EMAIL)
    record_campaign_event(camp3.id, DEMO_TENANT_ID, "campaign_paused", new_state="paused",
                          description="Paused for strategy review", created_by=DEMO_EMAIL)
    
    # One referral lead
    lead = create_lead_with_identity(
        tenant_id=DEMO_ORG_ID, name="Referred Lead", email="referred@example.com", source="referral"
    )
    lead.campaign_id = camp3.id
    lead.utm_source = "referral"
    lead.utm_campaign = "referral_program"
    db.session.commit()
    
    create_learning(
        tenant_id=DEMO_TENANT_ID, campaign_id=camp3.id,
        category="waste_detection",
        title="Referral program underperforming",
        observation="Only 2 referrals in 45 days with ₹150k budget allocated",
        significance="critical", confidence=90,
        recommendation="Consider revising referral incentives or pausing program",
        recommendation_confidence=85,
        recommendation_action="Review referral strategy",
        is_actionable=True, created_by=DEMO_EMAIL,
    )
    
    # Experiment
    exp = Experiment(
        campaign_id=cid1, name="Landing Page A/B Test",
        hypothesis="New hero section increases conversion by 15%",
        variant="B", status="running", metric="conversion_rate",
        sample_size=500, tenant_id=DEMO_TENANT_ID,
    )
    db.session.add(exp)
    
    db.session.commit()
    
    print(f"\n=== DEMO DATA SEEDING COMPLETE ===")
    print(f"Campaigns: 3 (1 active with data, 1 draft empty, 1 paused underperforming)")
    print(f"Audiences: 1 | Content: 2 | Interactions: 8 | Leads: 6")
    print(f"Opportunities: 3 | Proposals: 2 (1 accepted)")
    print(f"Attributions: 2 | Learnings: 3 | Experiments: 1")
    print(f"Campaign Events: 9")