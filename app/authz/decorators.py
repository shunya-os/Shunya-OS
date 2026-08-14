"""Canonical authorization decorators — enforce permissions at the API/service boundary."""
import functools
import logging
from flask import session, jsonify, g, request

logger = logging.getLogger(__name__)


def _resolve_identity() -> str:
    """Resolve the current user's canonical identity (OrgMember.identity_id = email)."""
    # Enterprise cookie first, then header, then Flask session
    from app.auth import TeamMember
    uid = session.get("user_id")
    if not uid:
        return ""
    tm = TeamMember.query.get(uid)
    if tm:
        return tm.email
    return str(uid)


def _resolve_org_id() -> int | None:
    """Resolve the current user's organization."""
    org_id = session.get("current_org_id")
    if org_id:
        return int(org_id)
    # Fallback: first active OrgMember
    identity = _resolve_identity()
    if identity:
        from app.models import OrgMember
        om = OrgMember.query.filter_by(identity_id=identity, is_active=True).first()
        if om:
            return om.organization_id
    return None


def require_permission(permission: str):
    """Decorator: require the given permission for the current user.

    Applies to Flask routes. Denies unauthenticated users (401)
    and users without the permission (403).
    """
    def decorator(fn):
        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            from app.authz.services import check_permission
            identity = _resolve_identity()
            if not identity:
                return jsonify({"error": "Authentication required"}), 401

            org_id = _resolve_org_id()
            if not org_id:
                return jsonify({"error": "No organization selected"}), 400

            if not check_permission(org_id, identity, permission):
                logger.info("AUTHZ DENY: identity=%s org=%s permission=%s path=%s",
                            identity, org_id, permission, request.path)
                return jsonify({"error": "Forbidden: missing permission", "permission": permission}), 403

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
                return jsonify({"error": "Authentication required"}), 401
            org_id = _resolve_org_id()
            if not org_id:
                return jsonify({"error": "No organization selected"}), 400
            for perm in permissions:
                if check_permission(org_id, identity, perm):
                    g.identity_id = identity
                    g.current_org_id = org_id
                    return fn(*args, **kwargs)
            return jsonify({"error": "Forbidden: missing permission"}), 403
        return wrapper
    return decorator