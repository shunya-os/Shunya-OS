"""FOR-2 Routes — Organization Operating System API."""

import json
import secrets
import uuid
from datetime import datetime, timedelta
from flask import jsonify, render_template, request, session, redirect, url_for

from app import db
from app.for2 import for2_bp
from app.models import Organization, OrgMember, OrgInvitation, Department
from app.tenant import Tenant


# ── Helpers ────────────────────────────────────────────────────────────

def _get_current_identity():
    """Get the current user's SHUNYA Identity ID from session."""
    return session.get("identity_id") or session.get("user_id") or ""


def _require_identity():
    """Require a logged-in identity. Returns error or None."""
    uid = _get_current_identity()
    if not uid:
        return jsonify({"error": "Authentication required"}), 401
    return None


def _current_org_id():
    """Get the currently active organization ID from session."""
    return session.get("current_org_id")


def _require_org():
    """Require an active organization in session."""
    org_id = _current_org_id()
    if not org_id:
        return jsonify({"error": "No organization selected. Create or switch to an organization first."}), 400
    return None


def _check_role(org_id, identity_id, min_role):
    """Check if identity has at least min_role in the organization.
    
    Role hierarchy: viewer < member < manager < admin < owner
    """
    member = OrgMember.query.filter_by(
        organization_id=org_id, identity_id=identity_id, is_active=True
    ).first()
    if not member:
        return None, jsonify({"error": "Not a member of this organization"}), 403

    roles = {"viewer": 0, "member": 1, "manager": 2, "admin": 3, "owner": 4}
    if roles.get(member.role, 0) < roles.get(min_role, 0):
        return None, jsonify({"error": f"'{min_role}' role or higher required"}), 403
    return member, None, None


# ── HTML Pages ─────────────────────────────────────────────────────────


@for2_bp.route("/for2")
def for2_home():
    """FOR-2 landing / org selection page."""
    uid = _get_current_identity()
    if not uid:
        return redirect(url_for("for2.for2_login"))
    orgs = OrgMember.query.filter_by(identity_id=uid, is_active=True).all()
    organizations = []
    for om in orgs:
        org = db.session.get(Organization, om.organization_id)
        if org:
            organizations.append({
                "org": org.to_dict(),
                "my_role": om.role,
                "my_name": om.name,
            })
    return render_template("for2_home.html", organizations=organizations, identity_id=uid)


@for2_bp.route("/for2/org/<int:org_id>")
def for2_workspace(org_id: int):
    """Organization workspace page."""
    uid = _get_current_identity()
    if not uid:
        return redirect(url_for("for2.for2_login"))
    org = db.session.get(Organization, org_id)
    if not org:
        return "Organization not found", 404
    member = OrgMember.query.filter_by(organization_id=org_id, identity_id=uid, is_active=True).first()
    if not member:
        return "Not a member of this organization", 403
    # Set as current org
    session["current_org_id"] = org_id
    members = OrgMember.query.filter_by(organization_id=org_id, is_active=True).all()
    departments = Department.query.filter_by(organization_id=org_id, is_active=True).all()
    return render_template(
        "for2_workspace.html",
        org=org, member=member, members=members, departments=departments,
    )


# ── API: Identity ─────────────────────────────────────────────────────


@for2_bp.route("/api/v1/for2/whoami", methods=["GET"])
def api_whoami():
    """Return current identity and org context."""
    uid = _get_current_identity()
    org_id = _current_org_id()
    result = {
        "identity_id": uid or None,
        "authenticated": bool(uid),
        "current_organization_id": org_id,
    }
    if uid:
        memberships = OrgMember.query.filter_by(identity_id=uid, is_active=True).all()
        result["organizations"] = []
        for m in memberships:
            org = db.session.get(Organization, m.organization_id)
            if org:
                result["organizations"].append({"org": org.to_dict(), "role": m.role, "name": m.name})
        if org_id:
            org = db.session.get(Organization, org_id)
            if org:
                result["current_organization"] = org.to_dict()
                member = OrgMember.query.filter_by(organization_id=org_id, identity_id=uid).first()
                if member:
                    result["my_role"] = member.role
    return jsonify(result)


# ── API: Organization CRUD ─────────────────────────────────────────────


@for2_bp.route("/api/v1/for2/organizations", methods=["POST"])
def api_create_organization():
    """Create a new organization. The creator becomes the owner."""
    auth = _require_identity()
    if auth:
        return auth
    data = request.get_json(silent=True) or {}
    name = data.get("name", "").strip()
    if not name:
        return jsonify({"error": "Organization name is required"}), 400

    uid = _get_current_identity()
    slug = data.get("slug", name.lower().replace(" ", "-").replace("'", "")[:80])
    # Ensure unique slug
    base_slug = slug
    counter = 1
    while Organization.query.filter_by(slug=slug).first():
        slug = f"{base_slug}-{counter}"
        counter += 1

    org = Organization(
        name=name,
        slug=slug,
        business_type=data.get("business_type", ""),
        brand_color=data.get("brand_color", "#2563eb"),
        brand_color_secondary=data.get("brand_color_secondary", "#7c3aed"),
        brand_tagline=data.get("brand_tagline", ""),
        brand_description=data.get("brand_description", ""),
        tax_id=data.get("tax_id", ""),
        phone=data.get("phone", ""),
        email=data.get("email", ""),
        website=data.get("website", ""),
        address=data.get("address", ""),
        city=data.get("city", ""),
        country=data.get("country", ""),
        currency=data.get("currency", "INR"),
        created_by=uid,
    )
    db.session.add(org)
    db.session.flush()

    # Creator becomes owner
    member = OrgMember(
        organization_id=org.id,
        identity_id=uid,
        name=data.get("owner_name", "Owner"),
        email=data.get("email", ""),
        role="owner",
        designation="Owner",
    )
    db.session.add(member)
    db.session.commit()

    session["current_org_id"] = org.id
    return jsonify({"success": True, "organization": org.to_dict()}), 201


@for2_bp.route("/api/v1/for2/organizations", methods=["GET"])
def api_list_organizations():
    """List organizations the current identity belongs to."""
    uid = _get_current_identity()
    if not uid:
        return jsonify({"organizations": []})
    memberships = OrgMember.query.filter_by(identity_id=uid, is_active=True).all()
    orgs = []
    for m in memberships:
        org = db.session.get(Organization, m.organization_id)
        if org:
            orgs.append({"org": org.to_dict(), "role": m.role, "name": m.name})
    return jsonify({"organizations": orgs})


@for2_bp.route("/api/v1/for2/organizations/<int:org_id>", methods=["GET"])
def api_get_organization(org_id: int):
    """Get organization details — requires membership."""
    auth = _require_identity()
    if auth:
        return auth
    caller, err, code = _check_role(org_id, _get_current_identity(), "viewer")
    if err:
        return err, code
    org = db.session.get(Organization, org_id)
    if not org:
        return jsonify({"error": "Organization not found"}), 404
    return jsonify({"organization": org.to_dict()})


@for2_bp.route("/api/v1/for2/organizations/<int:org_id>", methods=["PATCH"])
def api_update_organization(org_id: int):
    """Update organization settings."""
    auth = _require_identity()
    if auth:
        return auth
    org = db.session.get(Organization, org_id)
    if not org:
        return jsonify({"error": "Organization not found"}), 404
    member, err, code = _check_role(org_id, _get_current_identity(), "admin")
    if err:
        return err, code

    data = request.get_json(silent=True) or {}
    for field in ("name", "business_type", "brand_color", "brand_color_secondary",
                  "brand_tagline", "brand_description", "tax_id", "registration_number",
                  "phone", "email", "website", "address", "city", "state", "country",
                  "postal_code", "timezone", "currency", "date_format", "logo_url",
                  "max_members", "ai_enabled"):
        if field in data:
            setattr(org, field, data[field])
    db.session.commit()
    return jsonify({"success": True, "organization": org.to_dict()})


@for2_bp.route("/api/v1/for2/organizations/<int:org_id>/switch", methods=["POST"])
def api_switch_organization(org_id: int):
    """Switch the current organization context."""
    uid = _get_current_identity()
    if not uid:
        return jsonify({"error": "Authentication required"}), 401
    member = OrgMember.query.filter_by(organization_id=org_id, identity_id=uid, is_active=True).first()
    if not member:
        return jsonify({"error": "Not a member of this organization"}), 403
    session["current_org_id"] = org_id
    return jsonify({"success": True, "organization_id": org_id})


# ── API: Members & Invitations ─────────────────────────────────────────


@for2_bp.route("/api/v1/for2/organizations/<int:org_id>/members", methods=["GET"])
def api_list_members(org_id: int):
    """List members of an organization — filtered by role."""
    auth = _require_identity()
    if auth:
        return auth
    uid = _get_current_identity()
    caller, err, code = _check_role(org_id, uid, "member")
    if err:
        return err, code
    
    # Role-based filtering
    role_hierarchy = {"viewer": 0, "member": 1, "manager": 2, "admin": 3, "owner": 4}
    caller_role_level = role_hierarchy.get(caller.role, 0)
    
    if caller_role_level >= 3:  # admin/owner — see all
        members = OrgMember.query.filter_by(organization_id=org_id, is_active=True).all()
    elif caller_role_level >= 2:  # manager — see their department
        if caller.department_id:
            members = OrgMember.query.filter_by(
                organization_id=org_id, department_id=caller.department_id, is_active=True
            ).all()
        else:
            members = [caller]
    else:  # member/viewer — see only themselves
        members = [caller]
    
    mlist = []
    for m in members:
        d = m.to_dict()
        dept = db.session.get(Department, m.department_id) if m.department_id else None
        d["department_name"] = dept.name if dept else None
        mlist.append(d)
    return jsonify({"members": mlist})


@for2_bp.route("/api/v1/for2/organizations/<int:org_id>/members", methods=["POST"])
def api_invite_member(org_id: int):
    """Invite a person to join the organization."""
    auth = _require_identity()
    if auth:
        return auth
    member, err, code = _check_role(org_id, _get_current_identity(), "admin")
    if err:
        return err, code

    data = request.get_json(silent=True) or {}
    email = data.get("email", "").strip().lower()
    name = data.get("name", "").strip()
    role = data.get("role", "member")
    if not email:
        return jsonify({"error": "Email is required"}), 400

    # Check if already a member
    existing = OrgMember.query.filter_by(organization_id=org_id, email=email).first()
    if existing:
        return jsonify({"error": "This person is already a member of this organization"}), 409

    token = secrets.token_urlsafe(32)
    invitation = OrgInvitation(
        organization_id=org_id,
        email=email,
        name=name or email.split("@")[0],
        role=role,
        token=token,
        invited_by=_get_current_identity(),
        expires_at=datetime.utcnow() + timedelta(days=7),
    )
    db.session.add(invitation)
    db.session.commit()

    # For FOR-2, create the member immediately with a unique identity
    # In production, the invited user would accept via email link
    member_identity = f"invited_{uuid.uuid4().hex[:16]}"
    new_member = OrgMember(
        organization_id=org_id,
        identity_id=member_identity,
        name=name or email.split("@")[0],
        email=email,
        role=role,
        invited_by=_get_current_identity(),
    )
    db.session.add(new_member)
    invitation.status = "accepted"
    invitation.accepted_at = datetime.utcnow()
    db.session.commit()

    return jsonify({
        "success": True,
        "member": new_member.to_dict(),
        "invitation": invitation.to_dict(),
        "note": "In production, an email invitation would be sent."
    }), 201


@for2_bp.route("/api/v1/for2/organizations/<int:org_id>/members/<int:member_id>", methods=["PATCH"])
def api_update_member(org_id: int, member_id: int):
    """Update a member's role or department."""
    auth = _require_identity()
    if auth:
        return auth
    member_rec, err, code = _check_role(org_id, _get_current_identity(), "admin")
    if err:
        return err, code

    target = db.session.get(OrgMember, member_id)
    if not target or target.organization_id != org_id:
        return jsonify({"error": "Member not found"}), 404

    data = request.get_json(silent=True) or {}
    for field in ("role", "designation", "department_id", "is_active"):
        if field in data:
            setattr(target, field, data[field])
    db.session.commit()
    return jsonify({"success": True, "member": target.to_dict()})


@for2_bp.route("/api/v1/for2/organizations/<int:org_id>/invitations", methods=["GET"])
def api_list_invitations(org_id: int):
    """List pending invitations — admin only."""
    auth = _require_identity()
    if auth:
        return auth
    member, err, code = _check_role(org_id, _get_current_identity(), "admin")
    if err:
        return err, code
    invitations = OrgInvitation.query.filter_by(organization_id=org_id).order_by(
        OrgInvitation.created_at.desc()
    ).all()
    return jsonify({"invitations": [i.to_dict() for i in invitations]})


# ── API: Departments ───────────────────────────────────────────────────


@for2_bp.route("/api/v1/for2/organizations/<int:org_id>/departments", methods=["POST"])
def api_create_department(org_id: int):
    """Create a department within an organization."""
    auth = _require_identity()
    if auth:
        return auth
    member, err, code = _check_role(org_id, _get_current_identity(), "admin")
    if err:
        return err, code

    data = request.get_json(silent=True) or {}
    name = data.get("name", "").strip()
    if not name:
        return jsonify({"error": "Department name is required"}), 400

    dept = Department(
        organization_id=org_id,
        name=name,
        description=data.get("description", ""),
        head_identity_id=data.get("head_identity_id", ""),
        parent_department_id=data.get("parent_department_id"),
    )
    db.session.add(dept)
    db.session.commit()
    return jsonify({"success": True, "department": dept.to_dict()}), 201


@for2_bp.route("/api/v1/for2/organizations/<int:org_id>/departments", methods=["GET"])
def api_list_departments(org_id: int):
    """List departments in an organization — requires membership."""
    auth = _require_identity()
    if auth:
        return auth
    caller, err, code = _check_role(org_id, _get_current_identity(), "viewer")
    if err:
        return err, code
    depts = Department.query.filter_by(organization_id=org_id, is_active=True).all()
    return jsonify({"departments": [d.to_dict() for d in depts]})


# ── Seed: Create Panchi Club for demo ──────────────────────────────────


@for2_bp.route("/api/v1/for2/seed", methods=["POST"])
def api_seed_demo():
    """Seed a demo organization for testing."""
    uid = _get_current_identity()
    if not uid:
        return jsonify({"error": "Authentication required"}), 401

    existing = Organization.query.filter_by(slug="panchi-club").first()
    if existing:
        session["current_org_id"] = existing.id
        # Ensure current user is a member
        member = OrgMember.query.filter_by(organization_id=existing.id, identity_id=uid).first()
        if not member:
            member = OrgMember(
                organization_id=existing.id, identity_id=uid,
                name="Nishesh", email="nishesh@shunyaos.com", role="owner", designation="Founder",
            )
            db.session.add(member)
            db.session.commit()
        return jsonify({"success": True, "organization": existing.to_dict(), "note": "Already exists"})

    org = Organization(
        name="Panchi Club",
        slug="panchi-club",
        business_type="travel",
        brand_color="#0f172a",
        brand_color_secondary="#a4865f",
        brand_tagline="Travel that feels like home",
        brand_description="Premium travel experiences for the modern explorer.",
        currency="INR",
        created_by=uid,
    )
    db.session.add(org)
    db.session.flush()

    member = OrgMember(
        organization_id=org.id,
        identity_id=uid,
        name="Nishesh",
        email="nishesh@shunyaos.com",
        role="owner",
        designation="Founder",
    )
    db.session.add(member)

    # Create departments
    for dept_name in ["Sales", "Operations", "Finance", "Customer Experience"]:
        dept = Department(organization_id=org.id, name=dept_name)
        db.session.add(dept)

    db.session.commit()
    session["current_org_id"] = org.id
    return jsonify({"success": True, "organization": org.to_dict()}), 201