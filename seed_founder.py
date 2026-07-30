"""
SHUNYA — Seed Founder Identity

Creates the initial founder identity, tenant, and team member
so the product can be authenticated and reviewed on shunyaos.com.
"""
import os
import sys
import hashlib
import secrets

# Ensure app can be imported
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ["FLASK_ENV"] = "production"

from app import create_app, db
from app.auth import TeamMember
from app.tenant import Tenant
from app.models import Person, PersonIdentity
from app.production.identity_repository import SHUNYAIdentityModel

app = create_app()

FOUNDER_EMAIL = "nishesh@shunyaos.com"
FOUNDER_PASSWORD = "Founder2024!"
FOUNDER_NAME = "Nishesh"
COMPANY_NAME = "SHUNYA OS"
COMPANY_SLUG = "shunya-os"

with app.app_context():
    print("=== Seeding SHUNYA Founder Identity ===")

    # 1. Check if already seeded
    existing = TeamMember.query.filter_by(email=FOUNDER_EMAIL).first()
    if existing:
        print(f"Founder already exists: {existing.name} (ID: {existing.id})")
        sys.exit(0)

    # 2. Create Tenant (organization)
    tenant = Tenant(
        company_name=COMPANY_NAME,
        slug=COMPANY_SLUG,
        business_type="technology",
        is_active=True,
        plan="enterprise",
        max_team_members=100,
    )
    db.session.add(tenant)
    db.session.flush()
    print(f"Created Tenant: {tenant.company_name} (ID: {tenant.id})")

    # 3. Create Person
    person = Person(
        tenant_id=tenant.id,
        canonical_name=FOUNDER_NAME,
        preferred_name=FOUNDER_NAME,
        status="active",
    )
    db.session.add(person)
    db.session.flush()
    print(f"Created Person: {person.canonical_name} (ID: {person.id})")

    # 4. Create PersonIdentity (email)
    person_identity = PersonIdentity(
        person_id=person.id,
        identity_type="email",
        identity_value=FOUNDER_EMAIL,
        normalized_value=FOUNDER_EMAIL.lower(),
        verification_state="verified",
    )
    db.session.add(person_identity)
    db.session.flush()
    print(f"Created PersonIdentity: {person_identity.identity_value}")

    # 5. Create TeamMember (Flask auth)
    team_member = TeamMember(
        name=FOUNDER_NAME,
        email=FOUNDER_EMAIL,
        role="admin",
        is_active=True,
        person_id=person.id,
    )
    team_member.set_password(FOUNDER_PASSWORD)
    team_member.generate_token()
    db.session.add(team_member)
    db.session.flush()
    print(f"Created TeamMember: {team_member.name} (role: {team_member.role})")

    # 6. Create SHUNYAIdentityModel (OS kernel identity)
    identity_id = f"sid_{secrets.token_hex(16)}"
    auth_methods = [{
        "type": "email",
        "identifier": FOUNDER_EMAIL,
        "is_primary": True,
        "verified_at": None,
    }]
    import json
    shunya_identity = SHUNYAIdentityModel(
        identity_id=identity_id,
        display_name=FOUNDER_NAME,
        primary_email=FOUNDER_EMAIL,
        status="active",
        auth_methods_json=json.dumps(auth_methods),
    )
    db.session.add(shunya_identity)

    # 7. Skip kernel identity engine registration — it's volatile anyway
    # The SHUNYAIdentityModel is the canonical persistence layer

    db.session.commit()
    print(f"Created SHUNYA Identity: {identity_id}")
    print()
    print("=== Seed Complete ===")
    print(f"Email:    {FOUNDER_EMAIL}")
    print(f"Password: {FOUNDER_PASSWORD}")
    print(f"Identity: {identity_id}")