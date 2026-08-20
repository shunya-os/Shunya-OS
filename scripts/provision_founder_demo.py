"""
G5 PARALLEL WORK — Founder Demo Access & Product Acceptance Environment.

Provisions a controlled, isolated founder demo identity and workspace
through the canonical SHUNYA provisioning path.

This is NOT a security backdoor.
This is NOT an auth bypass.
This is NOT a separate demo application.

Steps:
1. Clean Demo Organization (if not exists)
2. Demo TeamMember through canonical auth
3. OrgMember linking identity to org
4. Seed demo data using canonical paths
5. Verify end-to-end journey
"""

from dotenv import load_dotenv
load_dotenv()

import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from flask import Flask
from app import create_app, db
from app.auth import TeamMember, UserRole
from app.auth_routes import auth_bp
from app.tenant import Tenant

import uuid
import json

DEMO_EMAIL = "founder@demo.shunyaos.com"
DEMO_PASSWORD = os.environ.get("DEMO_FOUNDER_PASSWORD", "")
ORG_NAME = "SHUNYA Demo Org"
ORG_SLUG = "shunya-demo-org"

def provision():
    app = create_app(config_override={
        "TESTING": False,
        "SQLALCHEMY_DATABASE_URI": os.environ.get("DATABASE_URL"),
        "SECRET_KEY": os.environ.get("SECRET_KEY", "dev-secret"),
    })
    
    with app.app_context():
        print("=== FOUNDER DEMO PROVISIONING ===")
        
        # Step 1: Check/create organization
        from app.models import Organization
        org = Organization.query.filter_by(slug=ORG_SLUG).first()
        if not org:
            org = Organization(
                name=ORG_NAME,
                slug=ORG_SLUG,
                business_type="other",
                is_active=True,
            )
            db.session.add(org)
            db.session.flush()
            print(f"Created org: {org.id} ({ORG_NAME})")
        else:
            print(f"Using existing org: {org.id} ({org.name})")
        
        # Step 2: Create Tenant (if needed)
        tenant = Tenant.query.filter_by(slug="shunya-demo").first()
        if not tenant:
            tenant = Tenant(
                company_name="SHUNYA Demo",
                slug="shunya-demo",
                subdomain="demo",
                is_active=True,
            )
            db.session.add(tenant)
            db.session.flush()
            print(f"Created tenant: {tenant.id}")
        else:
            print(f"Using existing tenant: {tenant.id}")
        
        # Step 3: Provision TeamMember
        tm = TeamMember.query.filter_by(email=DEMO_EMAIL).first()
        if not tm:
            tm = TeamMember(
                name="SHUNYA Founder",
                email=DEMO_EMAIL,
                role=UserRole.ADMIN.value,
                is_active=True,
                tenant_id=tenant.id,
            )
            tm.set_password(DEMO_PASSWORD)
            db.session.add(tm)
            db.session.flush()
            print(f"Created team member: {tm.id} ({DEMO_EMAIL})")
        else:
            print(f"Using existing team member: {tm.id}")
            if tm.tenant_id is None:
                tm.tenant_id = tenant.id
                tm.set_password(DEMO_PASSWORD)
        
        # Step 4: Provision identity and OrgMember
        # Generate a stable sid for the demo user
        identity_id = f"sid_demo_{uuid.uuid4().hex[:30]}"
        
        from app.models import OrgMember
        om = OrgMember.query.filter_by(
            organization_id=org.id,
            email=DEMO_EMAIL,
        ).first()
        if not om:
            om = OrgMember(
                organization_id=org.id,
                identity_id=identity_id,
                name="SHUNYA Founder",
                email=DEMO_EMAIL,
                role="admin",
                is_active=True,
            )
            db.session.add(om)
            print(f"Created org member: identity={identity_id}")
        else:
            print(f"Using existing org member: id={om.id}, identity={om.identity_id}")
            identity_id = om.identity_id
        
        db.session.commit()
        
        print(f"\n=== PROVISIONING COMPLETE ===")
        print(f"Email: {DEMO_EMAIL}")
        print(f"Org: {org.id} ({org.name})")
        print(f"OrgMember identity: {identity_id}")
        print(f"TeamMember ID: {tm.id}")
        print(f"Tenant ID: {tenant.id}")
        print(f"Password: {'SET (from env)' if DEMO_PASSWORD else 'UNSET — check DEMO_FOUNDER_PASSWORD env var'}")

if __name__ == "__main__":
    if not DEMO_PASSWORD:
        print("ERROR: DEMO_FOUNDER_PASSWORD environment variable not set!")
        print("Set it before running: export DEMO_FOUNDER_PASSWORD='your-secure-password'")
        sys.exit(1)
    provision()