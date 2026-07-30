"""
SHUNYA — Automated Onboarding: PANCHI CLUB

Creates the founder's first space and initial business objects
so the workspace is immediately meaningful — no cold start.

Called automatically after sign-in when no space exists.
"""
import os
import sys
import secrets
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ["FLASK_ENV"] = "production"

from app import create_app, db
from app.founder.models import FounderSpace, FounderObject, FounderConversation
from app.models import Organization, OrgMember


def _now() -> datetime:
    return datetime.now(timezone.utc)


def onboard(identity_id: str) -> dict:
    """Run the full onboarding for a founder identity.

    Returns a dict with what was created and the org context.
    """
    app = create_app()
    with app.app_context():
        # Find the founder's organization
        member = OrgMember.query.filter_by(identity_id=identity_id).first()
        if not member:
            return {"success": False, "reason": "No organization membership found"}

        org = Organization.query.get(member.organization_id)
        if not org:
            return {"success": False, "reason": "Organization not found"}

        # Check if space already exists
        existing_space = FounderSpace.query.filter_by(
            identity_id=identity_id, status="active"
        ).first()
        if existing_space:
            return {
                "success": True,
                "space": existing_space.to_dict(),
                "organization": org.to_dict() if hasattr(org, 'to_dict') else {"name": org.name},
                "note": "Space already exists",
            }

        # Create the FounderSpace for PANCHI CLUB
        space_id = f"space_{secrets.token_hex(8)}"
        space = FounderSpace(
            space_id=space_id,
            name=org.name or "Panchi Club",
            space_type=org.business_type or "organization",
            description=org.brand_description or f"{org.name} — {org.business_type}",
            identity_id=identity_id,
            member_count=1,
            status="active",
        )
        db.session.add(space)
        db.session.flush()

        # Create initial business objects based on business type
        objects_created = []
        initial_objects = _get_initial_objects(org.business_type or "organization")

        for obj_data in initial_objects:
            obj = FounderObject(
                object_id=f"obj_{secrets.token_hex(8)}",
                space_id=space_id,
                object_type=obj_data["type"],
                name=obj_data["name"],
                content=obj_data.get("content", ""),
                status="active",
                created_by=identity_id,
                created_at=_now(),
            )
            db.session.add(obj)
            objects_created.append(obj_data["name"])

        db.session.commit()

        return {
            "success": True,
            "space": space.to_dict(),
            "organization": org.to_dict() if hasattr(org, 'to_dict') else {"name": org.name},
            "objects_created": objects_created,
            "note": "Onboarding complete",
        }


def _get_initial_objects(business_type: str) -> list[dict]:
    """Return relevant initial objects based on business type."""
    common = [
        {
            "type": "Document",
            "name": "Company Overview",
            "content": "Overview of the business, mission, and team structure.",
        },
        {
            "type": "Document",
            "name": "Getting Started Guide",
            "content": "First steps and initial priorities for the organization.",
        },
    ]

    type_specific = {
        "travel": [
            {
                "type": "Project",
                "name": "Travel Packages & Experiences",
                "content": "Current travel packages, destinations, and experiences offered.",
            },
            {
                "type": "Lead",
                "name": "Recent Inquiries",
                "content": "Recent customer inquiries and trip requests.",
            },
        ],
        "technology": [
            {
                "type": "Project",
                "name": "Product Roadmap",
                "content": "Current product development milestones and priorities.",
            },
            {
                "type": "Lead",
                "name": "Prospective Clients",
                "content": "Active sales pipeline and prospect tracking.",
            },
        ],
    }

    return common + type_specific.get(business_type, [
        {
            "type": "Project",
            "name": "Business Initiatives",
            "content": "Key business initiatives and ongoing projects.",
        },
    ])


if __name__ == "__main__":
    import sys
    identity_id = sys.argv[1] if len(sys.argv) > 1 else None
    if not identity_id:
        print("Usage: python3 onboard.py <identity_id>")
        sys.exit(1)
    result = onboard(identity_id)
    print(f"Onboarding result: {result}")