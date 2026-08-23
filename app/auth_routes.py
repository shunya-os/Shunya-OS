"""
SHUNYA — Auth Routes & Middleware

Wired into the Flask app. Handles login, logout, session management,
team CRUD (superadmin only), and route protection middleware.
"""

import functools
import os
import secrets
from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, g, jsonify
from app import db, limiter
from app.auth import TeamMember, UserRole, AuthLayer

auth_bp = Blueprint("auth", __name__)
auth = AuthLayer()

# Paths that don't require authentication
PUBLIC_PATHS = {"/health", "/login", "/logout", "/telegram/webhook",
                "/api/login", "/media", "/static", "/genesis"}


def login_required(view):
    """Decorator: redirect to login if not authenticated."""
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if request.path.startswith("/static/") or request.path.startswith("/health"):
            return view(**kwargs)
        user_id = session.get("user_id")
        if not user_id:
            return redirect(url_for("auth.login_page", next=request.path))
        user = db.session.get(TeamMember, user_id)
        if not user or not user.is_active:
            session.clear()
            return redirect(url_for("auth.login_page"))
        g.user = user
        return view(**kwargs)
    return wrapped_view


def admin_required(view):
    """Decorator: only superadmins can access."""
    @functools.wraps(view)
    @login_required
    def wrapped_view(**kwargs):
        if g.user.role != UserRole.ADMIN.value:
            flash("Admin access required", "error")
            return redirect(url_for("workspace_routes.workspace_home"))
        return view(**kwargs)
    return wrapped_view


def permission_required(resource: str, action: str = "read"):
    """Decorator: check specific permission."""
    def decorator(view):
        @functools.wraps(view)
        @login_required
        def wrapped_view(**kwargs):
            if not auth.check_permission(g.user, resource, action):
                flash(f"No permission to {action} {resource}", "error")
                return redirect(url_for("main.index"))
            return view(**kwargs)
        return wrapped_view
    return decorator


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------


@auth_bp.route("/login", methods=["GET", "POST"])
@limiter.limit("10 per minute")  # Auth rate limiting
def login_page():
    # Handle JSON POST (used by Shunya OS frontend)
    if request.method == "POST" and request.is_json:
        data = request.get_json(silent=True) or {}
        email = data.get("email", "").strip().lower()
        password = data.get("password", "")

        # Handle superadmin creation on first login
        if email == "admin@shunyaos.com":
            existing = TeamMember.query.filter_by(email=email).first()
            if not existing:
                admin = TeamMember(
                    name="Super Admin",
                    email=email,
                    role=UserRole.ADMIN.value,
                    is_active=True,
                )
                admin.set_password(password)
                db.session.add(admin)
                db.session.commit()

        user = TeamMember.query.filter_by(email=email, is_active=True).first()
        if user and user.check_password(password):
            session["user_id"] = user.id
            user.last_login = datetime.utcnow()
            user.generate_token()
            db.session.commit()
            return jsonify({"success": True, "redirect": url_for("workspace_routes.workspace_home")})
        return jsonify({"success": False, "error": "Invalid email or password"}), 401

    # Handle form POST (legacy)
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        # Handle superadmin creation on first login — placeholder for migration
        if email == "admin@shunyaos.com":
            existing = TeamMember.query.filter_by(email=email).first()
            if not existing:
                admin = TeamMember(
                    name="Super Admin",
                    email=email,
                    role=UserRole.ADMIN.value,
                    is_active=True,
                )
                admin.set_password(password)
                db.session.add(admin)
                db.session.commit()

        user = TeamMember.query.filter_by(email=email, is_active=True).first()
        if user and user.check_password(password):
            session["user_id"] = user.id
            user.last_login = datetime.utcnow()
            user.generate_token()
            db.session.commit()
            next_url = request.args.get("next") or url_for("workspace_routes.workspace_home")
            return redirect(next_url)

        flash("Invalid email or password", "error")
        return redirect(url_for("main.index"))

    if session.get("user_id"):
        return redirect(url_for("workspace_routes.workspace_home"))
    return redirect(url_for("main.index"))


# Shunya OS frontend posts to /auth/login/password — alias to same handler
@auth_bp.route("/login/password", methods=["POST"])
@limiter.limit("10 per minute")  # Auth rate limiting
def login_password_json():
    """JSON login endpoint (used by Shunya OS frontend)."""
    return login_page()


@auth_bp.route("/logout")
def logout():
    session.clear()
    flash("Logged out", "success")
    return redirect(url_for("auth.login_page"))


@auth_bp.route("/team")
@admin_required
def team_list():
    members = TeamMember.query.order_by(TeamMember.role, TeamMember.name).all()
    return render_template("team.html", members=members, roles=UserRole)


@auth_bp.route("/team/add", methods=["POST"])
@admin_required
def team_add():
    name = request.form.get("name", "").strip()
    email = request.form.get("email", "").strip().lower()
    role = request.form.get("role", UserRole.AGENT.value)
    password = request.form.get("password", "")

    if not name or not email or not password:
        flash("Name, email, and password required", "error")
        return redirect(url_for("auth.team_list"))

    if TeamMember.query.filter_by(email=email).first():
        flash("Email already registered", "error")
        return redirect(url_for("auth.team_list"))

    member = TeamMember(name=name, email=email, role=role, is_active=True)
    member.set_password(password)
    db.session.add(member)
    db.session.commit()
    flash(f"{name} added as {role}", "success")
    return redirect(url_for("auth.team_list"))


@auth_bp.route("/team/<int:member_id>/role", methods=["POST"])
@admin_required
def team_update_role(member_id):
    member = db.session.get(TeamMember, member_id)
    if not member:
        flash("Member not found", "error")
        return redirect(url_for("auth.team_list"))
    new_role = request.form.get("role", UserRole.AGENT.value)
    member.role = new_role
    db.session.commit()
    flash(f"{member.name} role updated to {new_role}", "success")
    return redirect(url_for("auth.team_list"))


@auth_bp.route("/team/<int:member_id>/toggle", methods=["POST"])
@admin_required
def team_toggle(member_id):
    member = db.session.get(TeamMember, member_id)
    if not member:
        flash("Member not found", "error")
        return redirect(url_for("auth.team_list"))
    if member.id == g.user.id:
        flash("Cannot deactivate yourself", "error")
        return redirect(url_for("auth.team_list"))
    member.is_active = not member.is_active
    db.session.commit()
    status = "activated" if member.is_active else "deactivated"
    flash(f"{member.name} {status}", "success")
    return redirect(url_for("auth.team_list"))


# ---------------------------------------------------------------------------
# Inject user into templates
# ---------------------------------------------------------------------------

def inject_auth_globals():
    user = getattr(g, "user", None)
    return {
        "current_user": user,
        "is_admin": user and user.role == UserRole.ADMIN.value,
        "is_manager": user and user.role == UserRole.MANAGER.value,
        "UserRole": UserRole,
    }


# ---------------------------------------------------------------------------
# Signup — Create a new TeamMember account (used by SPA signup flow)
# ---------------------------------------------------------------------------


@auth_bp.route("/api/v1/auth/signup", methods=["POST"])
@limiter.limit("5 per hour")  # Strict rate limiting for signup
def api_signup():
    """Create a new user account. Returns identity_id on success."""
    data = request.get_json(silent=True) or {}
    name = data.get("name", "").strip()
    email = data.get("email", "").strip().lower()
    password = data.get("password", "")

    if not name or not email or not password:
        return jsonify({"success": False, "error": "Name, email, and password are required."}), 400

    if TeamMember.query.filter_by(email=email).first():
        return jsonify({"success": False, "error": "An account with this email already exists."}), 409

    member = TeamMember(name=name, email=email, role=UserRole.ADMIN.value, is_active=True)
    member.set_password(password)
    # Generate verify token — auto-verify in dev mode
    member.verify_token = secrets.token_hex(32)
    if os.environ.get("FLASK_ENV") == "development" or os.environ.get("DEV_VERIFY") == "true":
        member.verified = True
        member.verify_token = None
    db.session.add(member)
    db.session.commit()

    # Create OrgMember and assign default role for authorization
    try:
        from app.models import OrgMember, Organization
        primary_org = Organization.query.first()
        if primary_org:
            om = OrgMember(
                organization_id=primary_org.id,
                identity_id=member.email,
                name=member.name,
                email=member.email,
                role="member",
                is_active=True,
            )
            db.session.add(om)
            db.session.flush()
            from app.authz.models import Role, OrgMemberRole
            default_role = Role.query.filter_by(organization_id=primary_org.id, name="member").first()
            if default_role:
                db.session.add(OrgMemberRole(
                    organization_id=primary_org.id,
                    member_id=om.id,
                    role_id=default_role.id,
                    granted_by="system",
                ))
        db.session.commit()
    except Exception as e:
        import logging
        logging.getLogger(__name__).warning("Failed to create OrgMember for %s: %s", email, str(e))
        db.session.rollback()

    session["user_id"] = member.id
    session.modified = True

    return jsonify({"success": True, "identity_id": str(member.id), "verified": member.verified}), 201


# ---------------------------------------------------------------------------
# Email Verification Routes
# ---------------------------------------------------------------------------


@auth_bp.route("/api/v1/auth/request-verification", methods=["POST"])
def api_request_verification():
    """Request a new verification email."""
    data = request.get_json(silent=True) or {}
    email = data.get("email", "").strip().lower()
    if not email:
        return jsonify({"success": False, "error": "Email is required."}), 400
    member = TeamMember.query.filter_by(email=email).first()
    if not member:
        return jsonify({"success": False, "error": "Account not found."}), 404
    if member.verified:
        return jsonify({"success": True, "message": "Email already verified."}), 200
    member.verify_token = secrets.token_hex(32)
    db.session.commit()
    # In dev mode, print the verify URL
    verify_url = f"/auth/verify-email?token={member.verify_token}"
    if os.environ.get("FLASK_ENV") == "development" or os.environ.get("DEV_VERIFY") == "true":
        print(f"[DEV] Verify URL: {verify_url}")
    # In production, send email via mail service
    return jsonify({"success": True, "message": "Verification email sent."}), 200


@auth_bp.route("/api/v1/auth/verify-email", methods=["POST"])
def api_verify_email():
    """Verify email address with a token."""
    data = request.get_json(silent=True) or {}
    token = data.get("token", "").strip()
    if not token:
        return jsonify({"success": False, "error": "Verification token is required."}), 400
    member = TeamMember.query.filter_by(verify_token=token).first()
    if not member:
        return jsonify({"success": False, "error": "Invalid or expired verification token."}), 400
    member.verified = True
    member.verify_token = None
    db.session.commit()
    return jsonify({"success": True, "message": "Email verified successfully."}), 200


# ---------------------------------------------------------------------------
# Gmail OAuth Routes
# ---------------------------------------------------------------------------

@auth_bp.route("/gmail/connect", methods=["GET"])
@login_required
def gmail_connect_page():
    """Render Gmail OAuth connection page."""
    from flask import render_template
    return render_template("gmail_connect.html")


@auth_bp.route("/gmail/oauth/initiate", methods=["POST"])
@login_required
def gmail_oauth_initiate():
    """Initiate Gmail OAuth flow for the current tenant."""
    from app.communication.oauth import GmailOAuthService, OAuthConfig

    tenant_id = None
    # Try to get tenant from user context (if multi-tenant)
    try:
        from app.tenant import Tenant
        if hasattr(g, "tenant") and g.tenant:
            tenant_id = g.tenant.id
    except Exception:
        pass

    try:
        service = GmailOAuthService(session=db.session)
        result = service.initiate_flow(tenant_id=tenant_id)
        # Store state in session for callback verification
        session["gmail_oauth_state"] = result["state"]
        return jsonify({"success": True, "authorization_url": result["authorization_url"]})
    except ValueError as e:
        return jsonify({"success": False, "error": str(e)}), 400


@auth_bp.route("/gmail/oauth/callback", methods=["GET"])
def gmail_oauth_callback():
    """Handle Gmail OAuth callback."""
    from app.communication.oauth import GmailOAuthService, OAuthConfig

    error = request.args.get("error")
    if error:
        return redirect(url_for("auth.gmail_connect_page", error=error))

    code = request.args.get("code")
    state = request.args.get("state")
    session_state = session.get("gmail_oauth_state")

    if not code:
        return redirect(url_for("auth.gmail_connect_page", error="no_code"))

    # Verify state matches (CSRF protection)
    if not state or state != session_state:
        flash("OAuth state mismatch - possible security issue", "error")
        return redirect(url_for("auth.gmail_connect_page"))

    tenant_id = None
    try:
        from app.tenant import Tenant
        if hasattr(g, "tenant") and g.tenant:
            tenant_id = g.tenant.id
    except Exception:
        pass

    try:
        service = GmailOAuthService(session=db.session)
        source = service.connect_account(tenant_id, code, state)
        flash(f"Gmail account {source.account_identifier} connected successfully!", "success")
        return redirect(url_for("workspace_routes.workspace_home"))
    except ValueError as e:
        flash(f"Gmail connection failed: {e}", "error")
        return redirect(url_for("auth.gmail_connect_page"))


@auth_bp.route("/gmail/disconnect/<int:source_id>", methods=["POST"])
@login_required
def gmail_disconnect(source_id):
    """Disconnect a Gmail account."""
    from app.communication.oauth import GmailOAuthService

    service = GmailOAuthService(session=db.session)
    if service.disconnect_account(source_id):
        flash("Gmail account disconnected", "success")
    else:
        flash("Could not disconnect account", "error")
    return redirect(url_for("main.settings"))


@auth_bp.route("/api/v1/auth/session", methods=["GET"])
def session_restore():
    """Return current session identity from Flask session cookie.

    This endpoint is called on page load to restore the user's identity
    across tab/refresh boundaries. The Flask signed cookie persists
    across browser sessions within the cookie lifetime.

    Returns:
        200: { authenticated: true, identity_id, org_id, org_name, email, name }
        401: { authenticated: false }
    """
    import json
    from app.models import Organization, OrgMember

    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"authenticated": False}), 401

    from app.auth import TeamMember
    member = db.session.get(TeamMember, user_id)
    if not member or not member.is_active:
        session.clear()
        return jsonify({"authenticated": False}), 401

    # Resolve identity_id and current_org_id (mirrors _resolve_identity_session)
    identity_id = session.get("identity_id", "")
    current_org_id = session.get("current_org_id", 0)
    org_name = ""

    if not identity_id:
        # Try resolving from OrgMember
        org_members = OrgMember.query.filter_by(email=member.email, is_active=True).all()
        if org_members:
            org_counts = {}
            for om in org_members:
                cnt = OrgMember.query.filter_by(
                    organization_id=om.organization_id, is_active=True
                ).count()
                org_counts[om.organization_id] = cnt
            best_org_id = max(org_counts, key=org_counts.get)
            identity_id = next(
                om.identity_id
                for om in org_members
                if om.organization_id == best_org_id
            )
            current_org_id = best_org_id
            session["identity_id"] = identity_id
            session["current_org_id"] = current_org_id

    if current_org_id:
        org = db.session.get(Organization, current_org_id)
        if org:
            org_name = org.name

    return jsonify({
        "authenticated": True,
        "identity_id": identity_id,
        "user_id": user_id,
        "org_id": current_org_id,
        "org_name": org_name,
        "email": member.email,
        "name": member.name,
    })