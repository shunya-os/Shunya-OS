"""Canonical organization + workspace authorization boundary (R6B-2.7).

This is the ONE place where an authenticated request's organization and
workspace context is decided. It implements:

    identity → authorized organization → authorized canonical workspace → sh_objects

No other module may decide ownership. Helpers elsewhere must delegate here
rather than selecting a row themselves.

HARD RULES encoded here
-----------------------
* No ``.first()`` is ever used as an authorization decision. Where a single
  result is returned it is because the candidate set was proven to have exactly
  one member, or because an explicit identifier was validated against the
  identity's active membership.
* No synthetic ownership: ``organization_id`` of 0/1/None and workspace
  ``spc_business`` / ``spc_personal`` / ``spc_custom`` / ``spc_default`` are
  never invented. A missing or ambiguous context raises.
* Multiple organizations require an explicit selection.
* Multiple authorized workspaces require an explicit selection.
* Organization is derived through ``sh_workspaces.organization_id``; the
  membership table deliberately does not store it, so the two can never
  contradict.
"""
from __future__ import annotations

import logging

logger = logging.getLogger(__name__)


class OwnershipContextError(Exception):
    """Raised when canonical ownership context cannot be established.

    Callers MUST translate this into a denial (403) — never into a default.
    """

    def __init__(self, reason: str, code: str = "ownership_context_missing"):
        super().__init__(reason)
        self.reason = reason
        self.code = code


def _active_organization_ids(identity_id: str) -> list[int]:
    """All organizations the identity is an ACTIVE member of, ascending.

    Ascending order here is for deterministic reporting only; it is never used
    to pick a winner.
    """
    if not identity_id:
        return []
    from app.models import OrgMember
    rows = (
        OrgMember.query
        .filter_by(identity_id=str(identity_id), is_active=True)
        .all()
    )
    org_ids = {om.organization_id for om in rows if om.organization_id}
    return sorted(org_ids)


def resolve_current_organization(identity_id: str,
                                 requested_org_id=None) -> int:
    """Resolve the caller's authorized organization.

    Contract (R6B-2.7 Window 3):

    1. Zero active organizations            -> fail closed
    2. Exactly one active organization      -> may resolve automatically
    3. Multiple active organizations        -> explicit selection REQUIRED
    4. The requested organization must be an active membership of the identity
    5. Arbitrary row selection is never used

    Returns the authorized ``organization_id`` (a positive int).
    """
    org_ids = _active_organization_ids(identity_id)
    if not org_ids:
        raise OwnershipContextError(
            f"identity {identity_id!r} has no active organization membership",
            code="no_active_organization",
        )

    if requested_org_id is not None:
        try:
            requested = int(requested_org_id)
        except (TypeError, ValueError):
            raise OwnershipContextError(
                f"requested organization {requested_org_id!r} is not a valid id",
                code="invalid_requested_organization",
            )
        if requested not in org_ids:
            raise OwnershipContextError(
                f"identity {identity_id!r} is not an active member of requested "
                f"organization {requested}",
                code="organization_not_authorized",
            )
        return requested

    if len(org_ids) == 1:
        return org_ids[0]

    raise OwnershipContextError(
        f"identity {identity_id!r} belongs to {len(org_ids)} active "
        f"organizations; an explicit organization selection is required",
        code="organization_selection_required",
    )


def authorized_workspace_ids(identity_id: str, organization_id: int) -> list[str]:
    """Canonically authorized ``sh_workspaces.id`` values for the identity.

    Authorized == an active membership row exists AND the workspace itself
    belongs to ``organization_id`` and is active. The three conditions are
    evaluated independently, per the R6B-2.7 authorization predicate.
    """
    if not identity_id or not organization_id:
        return []
    from app.objects.legacy_models import ShWorkspaceMembership, Workspace
    rows = (
        ShWorkspaceMembership.query
        .filter_by(identity_id=str(identity_id), is_active=True)
        .order_by(ShWorkspaceMembership.workspace_id)
        .all()
    )
    candidate_ids = {r.workspace_id for r in rows}
    if not candidate_ids:
        return []
    workspaces = (
        Workspace.query
        .filter(Workspace.id.in_(candidate_ids))
        .filter(Workspace.organization_id == organization_id)
        .filter(Workspace.status == "active")
        .all()
    )
    return sorted(w.id for w in workspaces)


def resolve_current_workspace(identity_id: str, organization_id: int,
                              requested_workspace_id=None) -> str:
    """Resolve the caller's authorized canonical workspace (``sh_workspaces.id``).

    Contract (R6B-2.7 Window 4):

    1. Explicit requested workspace  -> must belong to the selected organization
       AND the identity must be actively authorized for it
    2. Explicit persisted current workspace -> validated by the same rules
    3. Exactly one authorized workspace      -> may resolve automatically
    4. Multiple authorized, none selected    -> fail closed
    5. Zero authorized                       -> fail closed

    ``.first()`` / ``order_by(...).first()`` are never used as authorization.
    The returned value is always an ``sh_workspaces.id`` — never a
    ``user_workspaces.workspace_id`` and never a ``FounderSpace.space_id``.
    """
    if not identity_id:
        raise OwnershipContextError("no authenticated identity",
                                    code="no_identity")
    if not organization_id:
        raise OwnershipContextError("no authorized organization",
                                    code="no_active_organization")

    authorized = authorized_workspace_ids(identity_id, organization_id)

    if requested_workspace_id:
        requested = str(requested_workspace_id)
        if requested in authorized:
            return requested
        # Distinguish "not yours" from "does not exist, or belongs elsewhere".
        from app.objects.legacy_models import Workspace
        ws = Workspace.query.filter_by(id=requested).first()
        if not ws:
            raise OwnershipContextError(
                f"requested workspace {requested!r} does not exist",
                code="workspace_not_found",
            )
        if ws.organization_id != organization_id:
            raise OwnershipContextError(
                f"requested workspace {requested!r} belongs to another "
                f"organization",
                code="workspace_other_organization",
            )
        raise OwnershipContextError(
            f"identity {identity_id!r} is not actively authorized for "
            f"workspace {requested!r}",
            code="workspace_not_authorized",
        )

    if len(authorized) == 1:
        return authorized[0]

    if not authorized:
        raise OwnershipContextError(
            f"identity {identity_id!r} has no authorized workspace in "
            f"organization {organization_id}",
            code="no_authorized_workspace",
        )

    raise OwnershipContextError(
        f"identity {identity_id!r} is authorized for {len(authorized)} "
        f"workspaces in organization {organization_id}; an explicit workspace "
        f"selection is required",
        code="workspace_selection_required",
    )


def assert_object_access(identity_id: str, organization_id: int,
                         workspace_id: str) -> None:
    """Raise unless the identity is authorized for this org+workspace pair.

    Server-side safety boundary used by ObjectService and by user-facing routes
    so that no caller-supplied combination can bypass authorization.
    """
    if not identity_id:
        raise OwnershipContextError("no authenticated identity",
                                    code="no_identity")
    authorized = authorized_workspace_ids(identity_id, organization_id)
    if str(workspace_id) not in authorized:
        raise OwnershipContextError(
            f"identity {identity_id!r} is not authorized for workspace "
            f"{workspace_id!r} in organization {organization_id}",
            code="workspace_not_authorized",
        )


import enum


class WorkspaceScope(str, enum.Enum):
    """Canonical workspace scope classification (R6B-2.7 Window 6A)."""
    NONE = "none"
    PERSONAL = "personal"
    ORGANIZATION = "organization"


def _map_legacy_selection(requested) -> int | None:
    """Map a legacy tenant id selection to its bridged organization id."""
    try:
        rid = int(requested)
    except (TypeError, ValueError):
        return None
    from app.models import Organization
    org = Organization.query.filter_by(legacy_tenant_id=rid).first()
    return int(org.id) if org else None


def _is_real_organization(rid) -> bool:
    try:
        rid = int(rid)
    except (TypeError, ValueError):
        return False
    from app.models import Organization
    return Organization.query.filter_by(id=rid).first() is not None


def resolve_caller_organization(identity_id: str, requested_org_id=None) -> int | None:
    """Canonical organization for the caller, tolerating LEGACY selections.

    A session may still carry a legacy tenant id (``tenants`` table) in
    ``current_org_id`` — e.g. the founder's session selects 89 ("Panchi Club"
    legacy tenant) while the canonical organization is 7. Strategy:

    1. A selection matching an organization's recorded legacy bridge
       (``organizations.legacy_tenant_id``) maps to that organization and must
       validate as an active membership.
    2. Otherwise the selection itself must validate as a membership.
    3. An INTERPRETABLE selection (a real organization id, or a bridge id whose
       organization the identity is not a member of) is DENIED — never retried.
    4. An uninterpretable stale value falls back to automatic resolution, which
       succeeds only for single-membership identities; multi-membership
       identities still fail closed (an explicit selection is required).

    Never returns an organization the identity is not an active member of.
    """
    requested = requested_org_id
    if requested is not None:
        try:
            rid = int(requested)
        except (TypeError, ValueError):
            rid = None
        mapped = _map_legacy_selection(rid) if rid is not None else None
        candidate = mapped if mapped is not None else rid
        if candidate is not None:
            try:
                return resolve_current_organization(identity_id, candidate)
            except OwnershipContextError:
                if mapped is not None or _is_real_organization(candidate):
                    return None  # interpretable selection, not authorized

    try:
        return resolve_current_organization(identity_id, None)
    except OwnershipContextError:
        return None


def resolve_workspace_scope(identity_id: str) -> WorkspaceScope:
    """Resolve the caller's workspace scope.

    ORGANIZATION:
        Identity is an active member of at least one organization (OrgMember).

    PERSONAL:
        Identity owns at least one personal FounderSpace (space_type='personal',
        status='active'). Only checked when no organization context exists.

    NONE:
        Identity has neither a personal workspace nor any organization
        membership. No scope exists — the caller must be denied.

    ORGANIZATION is checked FIRST: an identity that belongs to an organization
    MUST be resolved through the ORGANIZATION path even if they also have a
    personal workspace. A personal identity must NEVER gain access to org data
    merely because personal scope is allowed.
    """
    if not identity_id:
        return WorkspaceScope.NONE

    from app.models import OrgMember
    org_count = OrgMember.query.filter_by(
        identity_id=str(identity_id), is_active=True,
    ).count()
    if org_count > 0:
        return WorkspaceScope.ORGANIZATION

    from app.founder.models import FounderSpace
    personal = FounderSpace.query.filter_by(
        identity_id=str(identity_id),
        space_type="personal",
        status="active",
    ).first()
    if personal is not None:
        return WorkspaceScope.PERSONAL

    return WorkspaceScope.NONE


def resolve_tenant_scope(identity_id: str, requested_org_id=None):
    """Resolve the canonical tenant scope for a caller (organization + bridge).

    Returns ``(organization_id, accepted_tenant_ids)``:

    * ``organization_id`` — the authorized canonical ``organizations.id``, or
      ``None`` when the caller has no organization context (callers must then
      fall back to identity scope and fail closed).
    * ``accepted_tenant_ids`` — every ``tenant_id`` value legacy data may
      legally carry for this organization: the canonical id, plus the
      organization's recorded legacy bridge (``organizations.legacy_tenant_id``)
      when one exists and differs.

    WHY THE BRIDGE LIST EXISTS (observed live, 2026-10-09): the founder's data
    is split by an unfinished tenancy convergence — legacy subsystems (documents,
    leads, campaigns, memory, ...) wrote the LEGACY tenant id (89, tenants row
    "Panchi Club") while canonical subsystems wrote the ORGANIZATION id (7,
    organizations row "Panchi Club"). A canonical reader that filtered
    ``tenant_id == 7`` found nothing (manual document classification returned
    404 for a document the same human could see), while a legacy reader that
    filtered ``== 89`` found everything. Both surfaces must read the same
    logical tenant while the data converges: the reader accepts the union, the
    writer moves toward canonical, and the bridge itself is recorded in
    ``organizations.legacy_tenant_id`` (migration c_org_legacy_bridge) instead
    of being guessed at each call site.

    Stale legacy selections: a session may still carry a legacy id in
    ``current_org_id`` (e.g. 89). Resolution retries once with no explicit
    selection — identities with exactly ONE active membership resolve
    automatically; identities with several still fail closed, exactly as
    ``resolve_current_organization`` requires.
    """
    org_id = resolve_caller_organization(identity_id, requested_org_id)

    if not org_id:
        return None, []

    accepted = [int(org_id)]
    try:
        from app.models import Organization

        org = Organization.query.filter_by(id=org_id).first()
        bridge = getattr(org, "legacy_tenant_id", None) if org else None
        if bridge and int(bridge) not in accepted:
            accepted.append(int(bridge))
    except Exception:  # noqa: BLE001 — bridge lookup is best-effort by design
        logger.warning("legacy bridge lookup failed for organization %s", org_id)

    return int(org_id), accepted
