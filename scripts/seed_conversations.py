"""Seed demo conversation data for ZERO-GAP-01."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db
from datetime import datetime, timezone
import uuid

app = create_app()
with app.app_context():
    from app.founder.models import FounderConversation, FounderMessage, FounderObject, FounderSpace
    from app.auth import TeamMember
    from app.models import OrgMember

    tm = TeamMember.query.filter_by(email='founder@demo.shunyaos.com').first()
    if not tm:
        print("Demo user not found")
        exit()

    om = OrgMember.query.filter_by(email='founder@demo.shunyaos.com').first()
    identity_id = om.identity_id

    # Get or create a space
    spaces = FounderSpace.query.filter_by(identity_id=identity_id, status='active').all()
    if spaces:
        space = spaces[0]
        space_id = space.space_id
    else:
        space_id = f"spc_{uuid.uuid4().hex[:16]}"
        space = FounderSpace(space_id=space_id, name="My Business", space_type="organization", identity_id=identity_id, status="active")
        db.session.add(space)
        db.session.flush()

    # Get an object to attach conversation to — use a known existing object
    obj = FounderObject.query.filter_by(status='active').first()
    obj_id = obj.object_id if obj else None
    if not obj_id:
        print("No active object found")
        exit()

    conv_id = f"conv_{uuid.uuid4().hex[:16]}"
    conv = FounderConversation(conv_id=conv_id, object_id=obj_id, title="Q3 Marketing Strategy Discussion", status="active", identity_id=identity_id)
    db.session.add(conv)
    db.session.flush()

    messages = [
        ("human", "We need to finalize the Q3 marketing strategy. What channels are performing best?"),
        ("assistant", "Based on recent data, LinkedIn and email are driving 73% of qualified leads. LinkedIn has the highest conversion rate at 12.4%."),
        ("human", "Can you prepare a proposal for an expanded LinkedIn campaign?"),
        ("assistant", "I have drafted a proposal for a Q3 LinkedIn expansion. Estimated reach increase: 40%. Budget: 2.5L/month. Would you like to review?"),
    ]

    for role, content in messages:
        msg = FounderMessage(conv_id=conv_id, role=role, content=content, created_at=datetime.now(timezone.utc))
        db.session.add(msg)

    db.session.commit()
    print(f"Created conversation: {conv_id}")
    print(f"  Title: {conv.title}")
    print(f"  Messages: {len(messages)}")

    verify_conv = FounderConversation.query.filter_by(conv_id=conv_id).first()
    msg_count = FounderMessage.query.filter_by(conv_id=conv_id).count()
    print(f"  Verified: {verify_conv is not None}, messages: {msg_count}")