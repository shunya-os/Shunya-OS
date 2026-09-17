"""Canonical authorization decorators — enforce permissions at the API/service boundary."""
import functools
import logging
from flask import session, jsonify, g, request

logger = logging.getLogger(__name__)


def _resolve_identity() -> str:
    """Resolve the current user's canonical identity (OrgMember.identity_id)."""
    # Check session identity_id first (set by signin route)
    identity_id = session.get("identity_id")
    if identity_id:
        return identity_id
    # Fallback: TeamMember email
    from app.auth import TeamMember
    uid = session.get("user_id")
    if not uid:
        return ""
    tm = TeamMember.query.get(uid)
    if tm:
        return tm.email
    return str(uid)


def _resolve_org_id() -> int | None:
    """Resolve the current user's organization, canonically.

    Canonical order:
    1. session current_org_id, VALIDATED against the identity's active membership
    2. exactly one active membership → that organization
    3. multiple active memberships with no explicit selection → None (fail closed)

    An arbitrary ``.first()`` is never used to pick an organization: an identity
    that belongs to several organizations must select one explicitly, and an
    identity that belongs to none must be refused.
    """
    from app.authz.workspace_context import (
        OwnershipContextError, resolve_current_organization,
    )
    identity = _resolve_identity()
    if not identity:
        return None
    requested = session.get("current_org_id")
    try:
        return resolve_current_organization(identity, requested)
    except OwnershipContextError:
        return None


def _resolve_org_workspace_ids(org_id: int) -> list:
    """Resolve workspace IDs belonging to an organization.

    Canonical truth is ``sh_workspaces``, scoped by ``organization_id``.

    Returns ``[]`` when the organization owns no workspace, and callers MUST
    fail closed. The historical default workspaces ("spc_personal",
    "spc_business", "spc_custom") are deliberately NOT returned as a fallback:
    they were seeded with ``created_by="system"`` and no organization, so using
    them as workspace context would invent tenant ownership that does not exist.
    """
    from app.objects.legacy_models import Workspace
    return [w.id for w in Workspace.query.filter_by(organization_id=org_id).all()]


def _resolve_org_or_denial(identity: str):
    """``(organization_id, denial_code)`` for the current caller.

    ``organization_id`` is ``None`` only when the caller cannot be given an
    organization context, and ``denial_code`` distinguishes the two very
    different reasons (R6B-2.7 Window 6):

    * ``organization_selection_required`` / ``invalid_requested_organization``
      — the CLIENT can fix the request; the caller is not (yet) denied.
    * ``no_active_organization`` / ``organization_not_authorized`` — the caller
      is genuinely NOT ENTITLED. That is an authorization denial and must be
      reported as 403, never as "Bad request": a denial that looks like a
      malformed request hides an authorization decision from both the operator
      and the audit trail.

    ``_resolve_org_id()`` itself is left unchanged: it is used in ~40 places as
    a nullable tenant lookup, and those callers depend on the ``None``.
    """
    from app.authz.workspace_context import (
        OwnershipContextError,
        resolve_current_organization,
    )
    try:
        return resolve_current_organization(identity, session.get("current_org_id")), None
    except OwnershipContextError as exc:
        return None, getattr(exc, "code", "ownership_context_missing")


# "Auto-select an organization or make the client choose" — never a denial.
_SELECTION_REQUIRED_CODES = {
    "organization_selection_required",
    "invalid_requested_organization",
}


def require_permission(permission: str):
    """Decorator: require the given permission for the current user.

    Applies to Flask routes. Denies unauthenticated users (401) and users
    without the permission or without an authorized organization (403).
    """
    def decorator(fn):
        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            from app.authz.services import check_permission
            identity = _resolve_identity()
            if not identity:
                return jsonify({"success": False, "error": "Authentication required"}), 401

            org_id, denial = _resolve_org_or_denial(identity)
            if not org_id:
                # Personal scope bypass for personal-capable routes
                from app.authz.workspace_context import WorkspaceScope
                ws_scope = getattr(g, "current_workspace_scope", None)
                if ws_scope == WorkspaceScope.PERSONAL:
                    g.identity_id = identity
                    g.current_org_id = None
                    return fn(*args, **kwargs)
                if denial in _SELECTION_REQUIRED_CODES:
                    return jsonify({"success": False, "error": "No organization selected",
                                    "code": denial}), 400
                logger.info("AUTHZ DENY: identity=%s code=%s path=%s",
                            identity, denial, request.path)
                return jsonify({"success": False, "code": denial,
                                "error": "Forbidden: no authorized organization"}), 403

            if not check_permission(org_id, identity, permission):
                logger.info("AUTHZ DENY: identity=%s org=%s permission=%s path=%s",
                            identity, org_id, permission, request.path)
                return jsonify({"success": False, "error": "Forbidden: missing permission", "permission": permission}), 403

            g.identity_id = identity
            g.current_org_id = org_id
            return fn(*args, **kwargs)
        return wrapper
    return decorator


def require_any_permission(*permissions: str):
    """Decorator: require ANY of the given permissions."""
    def decorator(fn):
        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            from app.authz.services import check_permission
            identity = _resolve_identity()
            if not identity:
                return jsonify({"success": False, "error": "Authentication required"}), 401
            org_id, denial = _resolve_org_or_denial(identity)
            if not org_id:
                if denial in _SELECTION_REQUIRED_CODES:
                    return jsonify({"success": False, "error": "No organization selected",
                                    "code": denial}), 400
                logger.info("AUTHZ DENY: identity=%s code=%s path=%s",
                            identity, denial, request.path)
                return jsonify({"success": False, "code": denial,
                                "error": "Forbidden: no authorized organization"}), 403
            for perm in permissions:
                if check_permission(org_id, identity, perm):
                    g.identity_id = identity
                    g.current_org_id = org_id
                    return fn(*args, **kwargs)
            return jsonify({"success": False, "error": "Forbidden: missing permission"}), 403
        return wrapper
    return decorator