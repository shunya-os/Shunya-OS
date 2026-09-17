"""Canonical workspace-membership provisioning (R6B-2.7 Window 5).

``sh_workspace_memberships`` is the authoritative authorization bridge:

    identity → sh_workspace_memberships → sh_workspaces → organization

Before this module existed, NOTHING in the codebase wrote to that table — only
the model definition and the read path in ``app/authz/workspace_context.py``.
Every caller of ``assert_object_access()`` therefore failed closed for every
user, and no membership could ever be created through the application.

This module is that missing writer. It follows the authorization convention
already established by ``ObjectService``:

* ``identity_id``  — an authenticated actor. The actor must ALREADY be
  authorized for the workspace (an active member holding ``owner``/``admin``),
  or be an active organization owner/admin bootstrapping the first membership
  of a workspace in that organization.
* ``system_scope`` — an explicit, audited non-user provisioning caller
  (migrations, operators). Mutually exclusive with ``identity_id``. A missing
  authorization context MUST fail closed; it is never inferred.

Organization is deliberately NOT stored on the membership row: it is derived
through ``sh_workspaces.organization_id`` so the two can never contradict.
"""
from __future__ import annotations

import logging
from datetime import datetime

logger = logging.getLogger(__name__)

VALID_ROLES = ("owner", "admin", "member", "viewer")
GRANTING_ROLES = ("owner", "admin")


class WorkspaceMembershipError(Exception):
    """Raised when a membership operation is invalid or unauthorized."""

    def __init__(self, reason: str, code: str = "workspace_membership_error"):
        super().__init__(reason)
        self.reason = reason
        self.code = code


def _workspace(workspace_id):
    from app.objects.legacy_models import Workspace

    ws = Workspace.query.filter_by(id=str(workspace_id)).first()
    if ws is None:
        raise WorkspaceMembershipError(
            f"workspace {workspace_id!r} does not exist",
            code="workspace_not_found",
        )
    if (ws.status or "") != "active":
        raise WorkspaceMembershipError(
            f"workspace {workspace_id!r} is not active",
            code="workspace_inactive",
        )
    return ws


def _assert_actor_may_grant(ws, actor_identity_id):
    """Fail closed unless ``actor_identity_id`` may administer this workspace."""
    if not actor_identity_id:
        raise WorkspaceMembershipError(
            "no authenticated identity and no system_scope — refusing "
            "to provision a workspace membership",
            code="no_authorization_context",
        )

    from app.authz.workspace_context import authorized_workspace_ids

    # 1. An existing active member of this workspace, holding owner/admin.
    if str(ws.id) in authorized_workspace_ids(actor_identity_id,
                                              ws.organization_id):
        from app.objects.legacy_models import ShWorkspaceMembership
        row = ShWorkspaceMembership.query.filter_by(
            workspace_id=str(ws.id), identity_id=str(actor_identity_id),
            is_active=True,
        ).first()
        if row is not None and row.role in GRANTING_ROLES:
            return

    # 2. Bootstrap: an active owner/admin of the organization that owns this
    #    workspace, for a workspace in that same organization.
    if ws.organization_id:
        from app.models import OrgMember
        org_row = OrgMember.query.filter_by(
            organization_id=ws.organization_id,
            identity_id=str(actor_identity_id),
            is_active=True,
        ).first()
        if org_row is not None and (org_row.role or "").lower() in GRANTING_ROLES:
            return

    raise WorkspaceMembershipError(
        f"identity {actor_identity_id!r} is not authorized to administer "
        f"workspace {ws.id!r}",
        code="not_authorized_to_administer_workspace",
    )


def _resolve(workspace_id, identity_id, role, actor_identity_id, system_scope):
    if actor_identity_id and system_scope:
        raise WorkspaceMembershipError(
            "actor_identity_id and system_scope are mutually exclusive",
            code="contradictory_authorization_context",
        )
    if not identity_id:
        raise WorkspaceMembershipError("identity_id is required",
                                       code="missing_identity")
    role = (role or "member").lower()
    if role not in VALID_ROLES:
        raise WorkspaceMembershipError(
            f"role {role!r} is not one of {list(VALID_ROLES)}",
            code="invalid_role",
        )
    ws = _workspace(workspace_id)
    if not system_scope:
        _assert_actor_may_grant(ws, actor_identity_id)
    return ws, role


def grant(workspace_id, identity_id, role="member", *,
          actor_identity_id=None, system_scope=False) -> dict:
    """Grant (or reactivate) a canonical workspace membership. Idempotent.

    Returns the persisted membership as a dict.
    """
    from app import db
    from app.objects.legacy_models import ShWorkspaceMembership

    ws, role = _resolve(workspace_id, identity_id, role,
                        actor_identity_id, system_scope)

    row = ShWorkspaceMembership.query.filter_by(
        workspace_id=str(ws.id), identity_id=str(identity_id),
    ).first()

    now = datetime.utcnow()
    if row is None:
        row = ShWorkspaceMembership(
            workspace_id=str(ws.id), identity_id=str(identity_id),
            role=role, is_active=True, created_at=now, updated_at=now,
        )
        db.session.add(row)
    else:
        row.role = role
        row.is_active = True
        row.updated_at = now

    db.session.commit()
    logger.info("workspace membership granted: identity=%s workspace=%s role=%s",
                identity_id, ws.id, role)
    return {
        "workspace_id": row.workspace_id,
        "identity_id": row.identity_id,
        "role": row.role,
        "is_active": bool(row.is_active),
    }


def revoke(workspace_id, identity_id, *,
           actor_identity_id=None, system_scope=False) -> bool:
    """Deactivate a canonical workspace membership.

    The row is KEPT and marked inactive — never deleted — so the authorization
    history is preserved and ``authorized_workspace_ids()`` simply stops
    returning the workspace.
    """
    from app import db
    from app.objects.legacy_models import ShWorkspaceMembership

    ws = _workspace(workspace_id)
    if not actor_identity_id and not system_scope:
        raise WorkspaceMembershipError(
            "no authenticated identity and no system_scope",
            code="no_authorization_context",
        )
    if not system_scope:
        _assert_actor_may_grant(ws, actor_identity_id)

    row = ShWorkspaceMembership.query.filter_by(
        workspace_id=str(ws.id), identity_id=str(identity_id),
    ).first()
    if row is None:
        return False
    row.is_active = False
    row.updated_at = datetime.utcnow()
    db.session.commit()
    return True


def list_members(workspace_id, *, actor_identity_id=None,
                 system_scope=False) -> list[dict]:
    """List memberships of a workspace, honouring the same authorization."""
    from app.objects.legacy_models import ShWorkspaceMembership

    ws = _workspace(workspace_id)
    if not actor_identity_id and not system_scope:
        raise WorkspaceMembershipError(
            "no authenticated identity and no system_scope",
            code="no_authorization_context",
        )
    if not system_scope:
        _assert_actor_may_grant(ws, actor_identity_id)

    return [
        {"workspace_id": m.workspace_id, "identity_id": m.identity_id,
         "role": m.role, "is_active": bool(m.is_active)}
        for m in ShWorkspaceMembership.query.filter_by(
            workspace_id=str(ws.id)).all()
    ]
