#!/usr/bin/env python3
"""One-time canonical OWNER-membership provisioning for existing organizations.

WHY (ZG-03, 2026-10-12): canonical authorization is
    identity → sh_workspace_memberships → sh_workspaces → organization
Every organization owner that predates the membership bridge — notably the
founder (org 7 "Panchi Club", workspace spc_business) — lacks the membership
row, so media / content studio / knowledge surfaces fail closed with
"No canonical workspace context" for the very user who owns the data.

SCOPE — deliberately narrow (this is NOT a bulk populate):
  * Only ACTIVE org members whose role is ``owner`` — the same identity the
    canonical ``grant()`` service itself treats as empowered to administer
    the workspace (its bootstrap rule). Members with other roles stay
    fail-closed until product provisioning flows create their memberships.
  * Only workspaces owned by that same organization with status='active'.
  * Grants go through the audited ``app.authz.workspace_membership.grant``
    (system_scope=True) — idempotent, history-preserving, never deletes.
  * No synthetic identities, no cross-organization grants, no blanket sweep.

RELATIONSHIP TO THE R6B-2.7 RULING: that ruling barred bulk-populating the
production workspaces to make tests pass and required new users to be
provisioned through real flows. The ZG-03 directive requires legitimate
existing users' provisioning to be repaired through a documented, scoped
mechanism. Owner-of-their-own-org is the minimal documented scope; nobody
else is touched and reruns are no-ops.

Usage:
    .venv/bin/python scripts/backfill_owner_workspace_memberships.py            # dry-run
    .venv/bin/python scripts/backfill_owner_workspace_memberships.py --apply    # write
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

from app import create_app, db


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true",
                        help="write memberships (default: dry run)")
    args = parser.parse_args()

    app = create_app(config_override={
        "TESTING": False,
        "SQLALCHEMY_DATABASE_URI": os.environ.get("DATABASE_URL"),
        "SECRET_KEY": os.environ.get("SECRET_KEY", "dev-secret"),
    })

    with app.app_context():
        from app.models import OrgMember
        from app.objects.legacy_models import Workspace, ShWorkspaceMembership
        from app.authz.workspace_membership import grant

        owners = OrgMember.query.filter(
            OrgMember.is_active.is_(True),
            OrgMember.role == "owner",
        ).all()

        planned, skipped_existing = [], 0
        for owner in owners:
            workspaces = Workspace.query.filter_by(
                organization_id=owner.organization_id,
                status="active",
            ).all()
            for ws in workspaces:
                existing = ShWorkspaceMembership.query.filter_by(
                    workspace_id=str(ws.id),
                    identity_id=str(owner.identity_id),
                ).first()
                if existing is not None and existing.is_active:
                    skipped_existing += 1
                    continue
                planned.append((str(ws.id), str(owner.identity_id),
                                owner.organization_id))
                if args.apply:
                    grant(str(ws.id), str(owner.identity_id), role="owner",
                          system_scope=True)

        print(f"active owners scanned: {len(owners)}")
        print(f"memberships already active (skipped): {skipped_existing}")
        print(f"memberships {'GRANTED' if args.apply else 'to grant (dry run)'}: {len(planned)}")
        for ws_id, ident, org_id in planned:
            print(f"  org={org_id} ws={ws_id} identity={ident[:12]}...")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
