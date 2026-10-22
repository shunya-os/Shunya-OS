"""Organization → canonical workspace provisioning (G1.19).

Every usable organization owns at least one canonical workspace.

``sh_objects.workspace_id`` is NOT NULL and ``ObjectService.create()`` refuses to
invent a workspace, while ``resolve_current_workspace()`` fails closed for an
identity with zero authorized workspaces. An organization therefore cannot own
business objects until it owns a workspace — yet ``POST /orgs`` created only the
organization, membership and roles, leaving the whole canonical object layer
(``GET /api/v1/objects`` → ``403 no_authorized_workspace``, onboarding seeding,
uploads, media, AI-assisted creation) unreachable for that tenant.

This module is the single provisioning step:

* idempotent — an organization that already owns an active workspace gets that
  workspace back and no second one is created;
* authorization-preserving — the caller must be an ACTIVE member of the
  organization with an owner/admin role; nothing is elevated, no foreign
  organization id is accepted;
* tenant-safe — the workspace is created with the organization id, and the
  membership is created only for that same identity/workspace pair;
* transaction-friendly — ``commit=False`` lets the caller commit the
  organization, membership, roles and workspace atomically.

Multiple workspaces per organization remain supported (``POST
/<org_id>/workspaces``); this function only guarantees the first one exists.
"""

from __future__ import annotations

import uuid

from app import db

# Organization roles allowed to provision the first workspace. A member or
# viewer must never create a workspace — that would be implicit elevation.
_PROVISIONING_ORG_ROLES = {"owner", "admin"}


class WorkspaceProvisioningError(Exception):
    """Raised when the caller may not provision a workspace for an organization."""

    def __init__(self, message: str, code: str = "workspace_provisioning_denied"):
        super().__init__(message)
        self.code = code


def _active_membership(organization_id: int, identity_id: str):
    from app.models import OrgMember

    return (
        OrgMember.query
        .filter_by(organization_id=int(organization_id),
                   identity_id=str(identity_id), is_active=True)
        .first()
    )


def ensure_organization_workspace(organization_id: int, identity_id: str,
                                  name: str = "", *, commit: bool = True) -> dict:
    """Ensure ``organization_id`` owns an active canonical workspace.

    Returns ``{"workspace_id", "name", "created"}``. ``created`` is False when an
    active workspace already existed (idempotent retry).

    Raises ``WorkspaceProvisioningError`` when the organization id is invalid,
    the identity is not an active member, or the member's role is not
    owner/admin.
    """
    from app.objects.legacy_models import Workspace, ShWorkspaceMembership

    if not organization_id or int(organization_id) < 1:
        raise WorkspaceProvisioningError(
            "organization_id must be a positive id", code="invalid_organization")
    org_id = int(organization_id)

    if not identity_id:
        raise WorkspaceProvisioningError(
            "identity_id is required to provision a workspace",
            code="missing_identity")

    member = _active_membership(org_id, identity_id)
    if member is None:
        raise WorkspaceProvisioningError(
            f"identity {identity_id!r} is not an active member of organization {org_id}",
            code="not_a_member")

    org_role = str(getattr(member, "role", "") or "").lower()
    if org_role not in _PROVISIONING_ORG_ROLES:
        raise WorkspaceProvisioningError(
            f"role {org_role!r} may not provision a workspace for organization {org_id}",
            code="insufficient_role")

    existing = (
        Workspace.query
        .filter_by(organization_id=org_id, status="active")
        .order_by(Workspace.id.asc())
        .first()
    )
    if existing is not None:
        # Idempotent: never create a second workspace, but make sure the caller
        # that is entitled to administer the organization can actually use it.
        _ensure_membership(existing.id, identity_id, org_role)
        if commit:
            db.session.commit()
        return {"workspace_id": existing.id, "name": existing.name, "created": False}

    workspace = Workspace(
        id=f"ws_{uuid.uuid4().hex[:16]}",
        name=(name or f"Organization {org_id}").strip()[:255],
        workspace_type="business",
        created_by=str(identity_id),
        organization_id=org_id,
        status="active",
    )
    db.session.add(workspace)
    db.session.flush()

    _ensure_membership(workspace.id, identity_id, org_role)

    if commit:
        db.session.commit()
    return {"workspace_id": workspace.id, "name": workspace.name, "created": True}


# Organization role -> workspace role. Authorization for canonical objects is a
# membership row per (workspace, identity); the organization role decides what
# that membership may be, and the mapping is never upward.
_ORG_TO_WORKSPACE_ROLE = {
    "owner": "owner",
    "admin": "admin",
    "manager": "member",
    "member": "member",
    "viewer": "viewer",
    "agent": "member",
}


def grant_workspace_access(organization_id: int, identity_id: str, *,
                           commit: bool = False) -> list[str]:
    """Grant ``identity_id`` membership of every active workspace in the org.

    Used when an identity *joins* an existing organization (invitation
    acceptance) rather than creating it. Without this, the accepted member holds
    an ``OrgMember`` row and a role grant but no ``ShWorkspaceMembership``, and
    ``resolve_current_workspace()`` fails closed — measured in the G1.21
    invitation journey as ``GET /api/v1/objects`` → ``403
    no_authorized_workspace`` for a member who had just accepted an invitation.

    The workspace role is derived from the organization role and never elevated.
    Idempotent: an existing active membership is left untouched, an inactive one
    is reactivated. Returns the workspace ids granted/confirmed.
    """
    from app.objects.legacy_models import Workspace

    member = _active_membership(int(organization_id), identity_id)
    if member is None:
        raise WorkspaceProvisioningError(
            f"identity {identity_id!r} is not an active member of organization "
            f"{organization_id}", code="not_a_member")

    org_role = str(getattr(member, "role", "") or "").lower()
    workspace_role = _ORG_TO_WORKSPACE_ROLE.get(org_role)
    if workspace_role is None:
        raise WorkspaceProvisioningError(
            f"unknown organization role {org_role!r}", code="invalid_role")

    workspaces = (
        Workspace.query
        .filter_by(organization_id=int(organization_id), status="active")
        .order_by(Workspace.id.asc())
        .all()
    )
    granted = []
    for ws in workspaces:
        _ensure_membership(ws.id, identity_id, org_role)
        granted.append(ws.id)

    if commit:
        db.session.commit()
    else:
        db.session.flush()
    return granted


def _ensure_membership(workspace_id: str, identity_id: str, org_role: str) -> None:
    """Create the owner/admin membership for this identity if it is missing."""
    from app.objects.legacy_models import ShWorkspaceMembership

    row = ShWorkspaceMembership.query.filter_by(
        workspace_id=str(workspace_id), identity_id=str(identity_id)
    ).first()
    if row is not None:
        if not row.is_active:
            row.is_active = True
        return

    # Never elevate: the workspace role is derived from the organization role
    # through the mapping above. Previously any non-owner org role became
    # "admin" here, which would have handed a plain member or viewer
    # administrative rights on the workspace.
    db.session.add(ShWorkspaceMembership(
        workspace_id=str(workspace_id),
        identity_id=str(identity_id),
        role=_ORG_TO_WORKSPACE_ROLE.get(str(org_role).lower(), "member"),
        is_active=True,
    ))
