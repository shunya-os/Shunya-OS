"""SHUNYA — Invitation System (Milestone X, D1.4).

Email-based invitation workflow for adding users to organizations.
Uses canonical OrgInvitation model and creates OrgMember on acceptance.
"""

import logging
import secrets
from datetime import datetime, timedelta

from flask import jsonify, request, session
from werkzeug.exceptions import BadRequest, Forbidden, NotFound, Unauthorized

from app import db
from app.auth_routes import login_required
from app.models import Organization, OrgMember, OrgInvitation
from app.production.identity import identity_bp

# Only these organization roles may see or issue invitations. An invitation
# carries a capability token: whoever reads it can accept and join the tenant, so
# listing invitations is an administrative operation, not a member one.
_INVITE_ROLES = {"owner", "admin"}


def _generate_token() -> str:
    return secrets.token_urlsafe(32)


def _caller_identity_id() -> str:
    """Canonical identity id from the session, or raise Unauthorized."""
    sid = session.get("identity_id")
    if sid:
        return str(sid)
    uid = session.get("user_id")
    if not uid:
        raise Unauthorized("Authentication required")
    from app.auth import TeamMember
    member = db.session.get(TeamMember, uid)
    if member and getattr(member, "identity_id", None):
        return member.identity_id
    return str(uid)


def _require_org_admin(org_id: int) -> str:
    """Require the caller to be an ACTIVE owner/admin of ``org_id``.

    G1.21: ``list_invitations``, ``create_invitation`` and ``revoke_invitation``
    were guarded by ``@login_required`` alone, so **any** authenticated user could
    (a) enumerate another tenant's invitations together with their acceptance
    tokens, (b) invite themselves into any organization, and (c) revoke another
    tenant's invitations. The list endpoint returned the raw ``token`` for every
    invitation, which turns (a) into a direct account-takeover path for the
    invited address.

    Membership is the canonical ``OrgMember`` row; the role gate prevents a plain
    member from managing invitations. Returns the canonical identity id.
    """
    identity_id = _caller_identity_id()
    membership = OrgMember.query.filter_by(
        organization_id=org_id, identity_id=identity_id, is_active=True
    ).first()
    if membership is None:
        raise Forbidden("You are not a member of this organization")
    if str(membership.role or "").lower() not in _INVITE_ROLES:
        raise Forbidden("Only organization owners or admins can manage invitations")
    return identity_id


def _get_org_or_404(org_id: int) -> Organization:
    """Get an organization by ID or raise NotFound."""
    org = db.session.get(Organization, org_id)
    if not org or not org.is_active:
        raise NotFound("Organization not found")
    return org


def _validate_role(role: str) -> str:
    valid = {"viewer", "member", "manager", "admin", "owner", "agent"}
    if role not in valid:
        raise BadRequest(
            f"Invalid role '{role}'. Valid roles: {', '.join(sorted(valid))}"
        )
    return role


def _require_json() -> dict:
    data = request.get_json(silent=True)
    if data is None:
        raise BadRequest("Request body must be valid JSON")
    return data


def _invitation_to_dict(inv: OrgInvitation) -> dict:
    """Invitation payload for both the admin list and the accept screen.

    ``org_name`` is included because an invitee must be able to see WHICH
    organization invited them before setting a password; an invitation payload
    that cannot name the organization made the accept screen incomplete.
    """
    org_name = ""
    try:
        from app.models import Organization
        org = db.session.get(Organization, inv.organization_id)
        org_name = getattr(org, "name", "") or ""
    except Exception:  # never let a display field break the invitation
        org_name = ""
    return {
        "id": inv.id,
        "org_id": inv.organization_id,
        "org_name": org_name,
        "email": inv.email,
        "name": inv.name,
        "role": inv.role,
        "token": inv.token,
        "status": inv.status,
        "invited_by": inv.invited_by,
        "expires_at": inv.expires_at.isoformat() if inv.expires_at else None,
        "accepted_at": inv.accepted_at.isoformat() if inv.accepted_at else None,
        "created_at": inv.created_at.isoformat() if inv.created_at else None,
    }


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------


@identity_bp.route("/<int:org_id>/invitations", methods=["GET"])
@login_required
def list_invitations(org_id: int):
    """List invitations for an organization (owner/admin only)."""
    _get_org_or_404(org_id)
    _require_org_admin(org_id)
    invites = OrgInvitation.query.filter_by(organization_id=org_id).order_by(
        OrgInvitation.created_at.desc()
    ).all()
    # The raw acceptance token is a capability, not list metadata: it is returned
    # once, to the admin who created the invitation, and never re-broadcast.
    payload = []
    for inv in invites:
        item = _invitation_to_dict(inv)
        item.pop("token", None)
        item["token_present"] = bool(inv.token)
        payload.append(item)
    return jsonify({
        "success": True,
        "data": payload,
    })


@identity_bp.route("/<int:org_id>/invitations", methods=["POST"])
@login_required
def create_invitation(org_id: int):
    """Create an invitation to join an organization (owner/admin only)."""
    _get_org_or_404(org_id)
    _require_org_admin(org_id)
    data = _require_json()

    email = data.get("email", "").strip().lower()
    role = data.get("role", "member")  # default "member" IS seeded; "agent" is not in DEFAULT_ROLES

    if not email:
        raise BadRequest("'email' is required")
    role = _validate_role(role)

    # Check user doesn't already exist as a member
    existing_member = OrgMember.query.filter_by(organization_id=org_id, email=email).first()
    if existing_member:
        raise BadRequest(f"User with email '{email}' is already a member")

    token = _generate_token()
    invitation = OrgInvitation(
        organization_id=org_id,
        email=email,
        name=data.get("name", email.split("@")[0]),
        role=role,
        token=token,
        invited_by=str(session.get("identity_id", "") or session.get("user_id", "") or ""),
        expires_at=datetime.utcnow() + timedelta(hours=48),
    )
    db.session.add(invitation)
    db.session.commit()

    # Deliver the invitation by email — the journey is NOT complete until the
    # invitee receives the accept link (mirrors app/team/routes.py invite_member).
    #
    # G1.22: the send result is reported, not assumed. "accepted" means a provider
    # took the message; "logged"/"failed"/"blocked" means it was NOT delivered and
    # the invitation exists only as a record. The response therefore distinguishes
    # provider acceptance from actual delivery instead of implying both.
    delivery = {"status": "not_attempted", "accepted": False, "delivered": False}
    try:
        from app.email_service import build_invitation_email, send_email
        org = db.session.get(Organization, org_id)
        subject, body = build_invitation_email(
            email, token, org_name=org.name if org else ""
        )
        result = send_email(
            to=email,
            subject=subject,
            body=body,
            notification_type="team_invitation",
            business_event_id=f"invite:{org_id}:{token[:8]}",
            category="security",
        )
        status = str(result.get("status") or "unknown")
        # Acceptance is NOT delivery (G1.24 truthfulness): a provider or MTA
        # taking the message proves the send path worked, not that the message
        # reached an inbox. `delivered` therefore stays false until there is
        # real delivery evidence; `accepted` is the honest, narrower claim.
        delivery = {
            "status": status,
            "accepted": status == "accepted",
            "delivered": False,
            "record_id": result.get("record_id"),
        }
        if status != "accepted":
            # Never log the body or the token — the reason is enough.
            logging.getLogger(__name__).warning(
                "invitation %s created but NOT delivered (email status=%s, to=%s)",
                invitation.id, status, email)
    except Exception:
        delivery = {"status": "error", "delivered": False}
        logging.getLogger(__name__).exception(
            "Failed to send invitation email to %s", email)

    payload = _invitation_to_dict(invitation)
    payload["delivery"] = delivery
    return jsonify({
        "success": True,
        "data": payload,
    }), 201


@identity_bp.route("/invitations/<token>", methods=["GET"])
def get_invitation(token: str):
    """Get invitation details by token."""
    inv = OrgInvitation.query.filter_by(token=token).first()
    if not inv:
        raise NotFound("Invitation not found or expired")

    if inv.accepted_at:
        raise NotFound("Invitation has already been accepted")

    now = datetime.utcnow()
    if inv.expires_at and now.replace(tzinfo=None) > inv.expires_at.replace(tzinfo=None):
        raise NotFound("Invitation has expired")

    return jsonify({
        "success": True,
        "data": _invitation_to_dict(inv),
    })


@identity_bp.route("/invitations/<token>/accept", methods=["POST"])
def accept_invitation(token: str):
    """Accept an invitation, create member record and user account."""
    inv = OrgInvitation.query.filter_by(token=token).first()
    if not inv:
        raise NotFound("Invitation not found or expired")

    if inv.accepted_at:
        raise NotFound("Invitation has already been accepted")

    now = datetime.utcnow()
    if inv.expires_at and now.replace(tzinfo=None) > inv.expires_at.replace(tzinfo=None):
        raise NotFound("Invitation has expired")

    data = _require_json()
    name = data.get("name", "").strip()
    password = data.get("password", "")

    if not name:
        raise BadRequest("'name' is required")
    if not password or len(password) < 6:
        raise BadRequest("'password' must be at least 6 characters")

    # Check still no duplicate member
    existing_member = OrgMember.query.filter_by(
        organization_id=inv.organization_id, email=inv.email
    ).first()
    if existing_member:
        raise BadRequest(f"User with email '{inv.email}' is already a member")

    # Create TeamMember
    from app.auth import TeamMember

    existing_user = TeamMember.query.filter_by(email=inv.email).first()
    if existing_user:
        raise BadRequest(f"User with email '{inv.email}' already exists")

    # Normalize the invitation's role label into the canonical org role and the
    # legacy identity-layer role; grants use the canonical name only.
    from app.authz.services import normalize_role
    try:
        canonical_role, legacy_role = normalize_role(inv.role)
    except ValueError:
        canonical_role, legacy_role = "member", "agent"

    user = TeamMember(
        name=name,
        email=inv.email,
        role=legacy_role,
        is_active=True,
        verified=True,  # The emailed accept link proves ownership of the inbox
    )
    user.set_password(password)
    user.generate_token()
    db.session.add(user)
    db.session.flush()

    # Create OrgMember record using the CANONICAL identity id (sid_*), matching
    # what login resolves. Writing str(TeamMember.id) here left accepted
    # invitations unable to resolve their membership in authorization checks.
    identity_id = str(user.id)
    try:
        from app.production.identity_repository import IdentityRepository
        repo = IdentityRepository()
        canonical = repo.find_by_auth("email", inv.email)
        if canonical:
            identity_id = canonical.identity_id
        else:
            identity = repo.create(display_name=name, primary_email=inv.email)
            repo.add_auth_method(identity.identity_id, "email", inv.email, is_primary=True)
            identity_id = identity.identity_id
        user.identity_id = identity_id
    except Exception:  # identity service unavailable — keep legacy id, login repairs it
        pass
    member = OrgMember(
        organization_id=inv.organization_id,
        identity_id=identity_id,
        name=name,
        email=inv.email,
        role=canonical_role,
        invited_by=inv.invited_by,
    )
    db.session.add(member)
    db.session.flush()  # member.id needed for the OrgMemberRole row

    # Ensure default roles exist for this organization (safe no-op if already seeded)
    from app.authz.services import seed_default_roles
    # commit=False: invitation acceptance is one transaction (membership + role
    # grant + invitation state); a partial commit here would leave a member with
    # no role and an invitation still pending.
    seed_default_roles(inv.organization_id, commit=False)

    # Wire the OrgMemberRole immediately so the Team page shows populated
    # roles from the first request — no lazy auto-assignment at first
    # permission check. "agent" is a valid invite role but is NOT seeded
    # in DEFAULT_ROLES; fall back to "member" for the actual grant.
    from app.authz.models import Role as AuthzRole, OrgMemberRole
    role_name = canonical_role
    role = AuthzRole.query.filter_by(
        organization_id=inv.organization_id, name=role_name
    ).first()
    if role:
        existing_grant = OrgMemberRole.query.filter_by(
            organization_id=inv.organization_id,
            member_id=member.id,
            role_id=role.id,
        ).first()
        if not existing_grant:
            db.session.add(OrgMemberRole(
                organization_id=inv.organization_id,
                member_id=member.id,
                role_id=role.id,
                scope="organization",
                granted_by=inv.invited_by or "",
            ))

    # Grant access to the organization's canonical workspace(s) in the same
    # transaction. OrgMember alone is not authorization for canonical objects:
    # resolve_current_workspace() requires an active ShWorkspaceMembership row,
    # so without this an invitee could accept, log in, and still receive
    # `403 no_authorized_workspace` on every object surface (measured in G1.21).
    # A failure here must abort the acceptance (the commit below is the single
    # transaction), so an organisation can never report a joined member who has
    # no access. An organization with zero active workspaces is a pre-existing
    # invariant violation, not an acceptance failure: it is recorded instead of
    # blocking the invitee.
    from app.authz.org_provisioning import grant_workspace_access

    granted = grant_workspace_access(inv.organization_id, identity_id, commit=False)
    if not granted:
        import logging
        logging.getLogger(__name__).warning(
            "invitation %s accepted but organization %s has no active workspace; "
            "member %s will receive no_authorized_workspace until it is repaired",
            inv.id, inv.organization_id, identity_id)

    # Mark invitation as accepted
    inv.accepted_at = datetime.utcnow()
    inv.status = "accepted"
    db.session.commit()

    return jsonify({
        "success": True,
        "data": {
            "user_id": user.id,
            "email": user.email,
            "name": user.name,
            "role": user.role,
        },
    }), 201


@identity_bp.route("/<int:org_id>/invitations/<int:inv_id>", methods=["DELETE"])
@login_required
def revoke_invitation(org_id: int, inv_id: int):
    """Revoke a pending invitation (owner/admin only)."""
    _get_org_or_404(org_id)
    _require_org_admin(org_id)
    inv = db.session.get(OrgInvitation, inv_id)
    if not inv or inv.organization_id != org_id:
        raise NotFound("Invitation not found")
    if inv.accepted_at:
        raise BadRequest("Cannot revoke an accepted invitation")
    db.session.delete(inv)
    db.session.commit()
    return jsonify({
        "success": True,
        "data": {"id": inv_id, "status": "revoked"},
    })