"""Seed rich demo data for M4 founder validation."""
import sys, uuid
sys.path.insert(0, '.')

from app import create_app, db
from app.founder.models import (
    BusinessRelationship, FounderConversation, FounderMessage,
    FounderObject, FounderSpace
)

app = create_app(config_override={
    "TESTING": True,
    "SQLALCHEMY_DATABASE_URI": "sqlite:////home/shunya-deploy/shunya_os/shunya_demo.db",
    "SECRET_KEY": "demo-secret",
    "DISABLE_RATE_LIMIT": "true",
    "WTF_CSRF_ENABLED": False,
})

with app.app_context():
    from app.founder.workspace_models import (
        MissingContext, NextAction, WorkspaceEvent,
        WorkspaceHealthSnapshot, WorkspaceNavigation
    )
    from app import models
    db.drop_all()
    db.create_all()

    # Sign in to create OS identity
    from app.adapters.os_adapter import sign_in
    result = sign_in(email="nishesh@shunyaos.com", password="demo123", name="Nishesh")
    assert result["success"]
    identity_id = result["identity_id"]
    print(f"Identity: {identity_id}")

    # Space 1: Core Business
    space1 = FounderSpace(
        space_id="demo_spc_001", name="Core Business",
        space_type="organization", identity_id=identity_id,
        description="Primary business operations and strategy"
    )
    db.session.add(space1)
    db.session.flush()

    # Object 1: Q3 Marketing Campaign (fully featured)
    obj1 = FounderObject(
        object_id="demo_obj_001", space_id="demo_spc_001",
        name="Q3 Marketing Campaign", object_type="Document",
        content="Strategic marketing plan for Q3 targeting enterprise customers across India and Southeast Asia. Budget: ₹15L. Expected ROI: 3.5x. Campaign includes digital ads, partner outreach, and a launch event.",
        created_by=identity_id,
    )
    db.session.add(obj1)
    db.session.flush()

    conv1 = FounderConversation(
        conv_id="demo_conv_001", object_id="demo_obj_001",
        title="Campaign Strategy", identity_id=identity_id,
    )
    db.session.add(conv1)
    db.session.flush()
    for msg in [
        ("human", "What's the current status of the campaign plan?"),
        ("assistant", "The Q3 Marketing Campaign has a budget of ₹15L targeting enterprise customers. The strategy covers digital ads, partner outreach, and a launch event. Expected ROI is 3.5x. Would you like to review the budget breakdown?"),
        ("human", "Yes, show me the budget allocation"),
        ("assistant", "Budget breakdown: Digital Ads ₹5L (33%), Partner Outreach ₹4L (27%), Launch Event ₹3.5L (23%), Contingency ₹2.5L (17%). The partner outreach allocation could be increased given our strong partner network in Southeast Asia."),
        ("human", "Good point. Increase partner outreach by ₹1L from contingency."),
        ("assistant", "Updated: Partner Outreach ₹5L (33%), Digital Ads ₹5L (33%), Launch Event ₹3.5L (23%), Contingency ₹1.5L (10%). New expected ROI: 3.8x due to stronger partner channel focus."),
    ]:
        db.session.add(FounderMessage(conv_id="demo_conv_001", role=msg[0], content=msg[1]))
    db.session.commit()

    # Object 2: Acme Corp Partnership (relationship-linked)
    obj2 = FounderObject(
        object_id="demo_obj_002", space_id="demo_spc_001",
        name="Acme Corp Partnership", object_type="Contract",
        content="Partnership agreement with Acme Corporation for joint go-to-market in Southeast Asia. Revenue share: 60/40 in our favor. Term: 12 months. Signed: July 2026.",
        created_by=identity_id,
    )
    db.session.add(obj2)
    db.session.flush()

    conv2 = FounderConversation(
        conv_id="demo_conv_002", object_id="demo_obj_002",
        title="Partnership Terms", identity_id=identity_id,
    )
    db.session.add(conv2)
    db.session.flush()
    for msg in [
        ("human", "Have we signed the Acme partnership agreement?"),
        ("assistant", "Yes, the Acme Corp Partnership agreement was signed in July 2026. Terms: 12 months, 60/40 revenue share in our favor, covering joint go-to-market in Southeast Asia. The contract is live and active."),
        ("human", "What are the key deliverables?"),
        ("assistant", "Key deliverables under the partnership: 1) Joint marketing events in 3 cities (Singapore, Bangkok, Jakarta). 2) Co-branded collateral. 3) Shared sales targets: ₹50L combined revenue. 4) Quarterly business reviews. First review is due next month."),
    ]:
        db.session.add(FounderMessage(conv_id="demo_conv_002", role=msg[0], content=msg[1]))
    db.session.commit()

    # Object 3: Budget Spreadsheet (conversation, no content yet)
    obj3 = FounderObject(
        object_id="demo_obj_003", space_id="demo_spc_001",
        name="Q3 Budget Spreadsheet", object_type="Spreadsheet",
        created_by=identity_id,
    )
    db.session.add(obj3)
    db.session.flush()

    # Relationships
    for rel_data in [
        ("demo_rel_001", "customer", "Acme Corporation", "Acme Corp Inc", identity_id),
        ("demo_rel_002", "supplier", "Global Supplies Ltd", "Global Supplies", identity_id),
        ("demo_rel_003", "partner", "TechSolve Partners", "TechSolve", identity_id),
        ("demo_rel_004", "customer", "Bharat Enterprises", "Bharat Ent.", identity_id),
    ]:
        db.session.add(BusinessRelationship(
            rel_id=rel_data[0], space_id="demo_spc_001",
            rel_type=rel_data[1], name=rel_data[2],
            company=rel_data[3], created_by=rel_data[4],
        ))
    db.session.commit()

    # Space 2: Personal Projects
    space2 = FounderSpace(
        space_id="demo_spc_002", name="Personal Projects",
        space_type="personal", identity_id=identity_id,
    )
    db.session.add(space2)
    db.session.flush()

    obj4 = FounderObject(
        object_id="demo_obj_004", space_id="demo_spc_002",
        name="Learning Plan 2026", object_type="Document",
        content="Personal learning roadmap: AI/ML certification, public speaking workshop, and industry conference attendance.",
        created_by=identity_id,
    )
    db.session.add(obj4)
    db.session.commit()

    print(f"Demo data seeded successfully")
    print(f"Users: nishesh@shunyaos.com / demo123")
    print(f"Objects: {obj1.object_id}, {obj2.object_id}, {obj3.object_id}, {obj4.object_id}")
    print(f"Spaces: {space1.space_id}, {space2.space_id}")