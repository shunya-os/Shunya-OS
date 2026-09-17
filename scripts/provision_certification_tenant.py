#!/usr/bin/env python3
"""Provision the ISOLATED certification tenant (R6B-2.7 Window 5).

Founder ruling: provision canonical ``sh_workspace_memberships`` ONLY for a
newly created isolated certification tenant required for browser certification.
Do NOT derive memberships from existing ``org_members``. Do NOT bulk-populate
the existing four production workspaces. Existing users stay fail-closed.

Everything here goes through the repository's own models and the canonical
service ``app.authz.workspace_membership.grant()`` — no ad-hoc SQL, no
fixture-only membership, no production bypass.

Creates:
    TeamMember            (login: email + password, verified)
    SHUNYAIdentity        (canonical identity via IdentityRepository)
    Organization          (isolated)
    OrgMember             (owner)
    sh_workspaces row     (canonical, owned by that organization)
    sh_workspace_memberships  (via the canonical service)

Every step is independently idempotent, so an interrupted run can simply be
re-run. The generated password is written to a 0600 file and NEVER printed;
the operator reads it from that file to save the login in the vault.

Usage:
    .venv/bin/python scripts/provision_certification_tenant.py
    .venv/bin/python scripts/provision_certification_tenant.py --verify-only
"""
import argparse
import json
import os
import secrets
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

EMAIL = "certification@shunyaos.com"
TENANT_SLUG = "certification-tenant"
WORKSPACE_ID = "ws_certification"
PASSWORD_FILE = "/home/shunya-deploy/.shunya/certification_login.txt"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--verify-only", action="store_true")
    ap.add_argument("--reset-password", action="store_true",
                    help="set a fresh password for the certification account "
                         "and rewrite the 0600 credential file")
    args = ap.parse_args()

    os.environ.setdefault("SHUNYA_ENVIRONMENT", "production")
    from app import create_app, db
    from app.auth import TeamMember
    from app.models import Organization, OrgMember
    from app.objects.legacy_models import Workspace, ShWorkspaceMembership
    from app.authz.workspace_membership import grant
    from app.authz.workspace_context import (
        authorized_workspace_ids, assert_object_access,
    )
    from app.production.identity_repository import IdentityRepository

    app = create_app()

    with app.app_context():
        if args.verify_only and TeamMember.query.filter_by(email=EMAIL).first() is None:
            print("NOT PROVISIONED: no TeamMember for", EMAIL)
            return 1

        # ── 1. Login record ───────────────────────────────────────────
        member = TeamMember.query.filter_by(email=EMAIL).first()
        password = None
        if member is None:
            password = secrets.token_urlsafe(24)
            member = TeamMember(name="Certification Identity", email=EMAIL,
                                role="admin", is_active=True, verified=True)
            member.set_password(password)
            db.session.add(member)
            db.session.commit()
            print("created TeamMember id=", member.id)
        else:
            print("TeamMember exists id=", member.id)

        if args.reset_password:
            password = secrets.token_urlsafe(24)
            member.set_password(password)
            member.verified = True
            member.is_active = True
            db.session.commit()
            print("password reset for", EMAIL)

        # ── 2. Canonical identity ────────────────────────────────────
        repo = IdentityRepository()
        identity = repo.find_by_auth("email", EMAIL)
        if identity is None:
            identity = repo.create(display_name="Certification Identity",
                                   primary_email=EMAIL)
            repo.add_auth_method(identity.identity_id, "email", EMAIL,
                                 is_primary=True)
        identity_id = identity.identity_id
        if str(member.identity_id or "") != identity_id:
            member.identity_id = identity_id
            db.session.commit()
        print("canonical identity_id=", identity_id)

        # ─ 3. Isolated organization ──────────────────────────────────
        org = Organization.query.filter_by(slug=TENANT_SLUG).first()
        if org is None:
            org = Organization(name="Certification Tenant",
                               slug=TENANT_SLUG, business_type="internal")
            db.session.add(org)
            db.session.commit()
        org_id = org.id
        print("organization_id=", org_id)

        # ─ 4. Organization membership (owner) ────────────────────────
        om = OrgMember.query.filter_by(organization_id=org_id,
                                       identity_id=identity_id).first()
        if om is None:
            om = OrgMember(organization_id=org_id, identity_id=identity_id,
                           name="Certification Identity", email=EMAIL,
                           role="owner", is_active=True)
            db.session.add(om)
            db.session.commit()
        else:
            om.role = "owner"
            om.is_active = True
            db.session.commit()
        print("org_member role=owner")

        # ── 5. Canonical workspace owned by that organization ─────────
        ws = Workspace.query.filter_by(id=WORKSPACE_ID).first()
        if ws is None:
            ws = Workspace(id=WORKSPACE_ID, name="Certification Workspace",
                           workspace_type="custom", icon="🧪",
                           created_by=identity_id,
                           organization_id=org_id, status="active")
            db.session.add(ws)
            db.session.commit()
        print("canonical workspace_id=", ws.id)

        # ─ 6. Canonical membership — through the service, not raw SQL ──
        if not args.verify_only:
            result = grant(ws.id, identity_id, "owner", system_scope=True)
            print("membership granted:", json.dumps(result))

            if password:
                os.makedirs(os.path.dirname(PASSWORD_FILE), exist_ok=True)
                with open(PASSWORD_FILE, "w") as fh:
                    fh.write(f"email: {EMAIL}\npassword: {password}\n")
                os.chmod(PASSWORD_FILE, 0o600)
                print("credential file written:", PASSWORD_FILE, "(0600)")
            else:
                print("credential file NOT rewritten (account already existed)")

        # ── Proof of the authorization chain ─────────────────────────
        checks = [
            ("identity → organization (active OrgMember)",
             OrgMember.query.filter_by(
                 organization_id=org_id, identity_id=identity_id,
                 is_active=True).count() == 1),
            ("identity → active sh_workspace_memberships",
             ShWorkspaceMembership.query.filter_by(
                 workspace_id=WORKSPACE_ID, identity_id=identity_id,
                 is_active=True).count() == 1),
            ("membership → canonical sh_workspace exists",
             Workspace.query.filter_by(id=WORKSPACE_ID).first() is not None),
            ("workspace → correct organization",
             ws.organization_id == org_id),
            ("authorized_workspace_ids resolves exactly this workspace",
             authorized_workspace_ids(identity_id, org_id) == [WORKSPACE_ID]),
        ]

        allowed = True
        try:
            assert_object_access(identity_id, org_id, WORKSPACE_ID)
        except Exception:
            allowed = False
        checks.append(("assert_object_access ALLOWS the certified workspace",
                       allowed))

        denied = False
        try:
            assert_object_access(identity_id, org_id, "spc_business")
        except Exception:
            denied = True
        checks.append(("assert_object_access DENIES an unauthorized workspace",
                       denied))

        print("\n--- authorization chain ---")
        ok = True
        for name, passed in checks:
            print(f"[{'PASS' if passed else 'FAIL'}] {name}")
            ok = ok and passed

        print("\nidentity_id     =", identity_id)
        print("email           =", EMAIL)
        print("workspace_id    =", WORKSPACE_ID)
        print("organization_id =", org_id)
        return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())