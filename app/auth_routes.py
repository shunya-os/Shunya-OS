"""
SHUNYA — Auth Routes & Middleware

Wired into the Flask app. Handles login, logout, session management,
team CRUD (superadmin only), and route protection middleware.
"""

import functools
from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, g, jsonify
from app import db
from app.auth import TeamMember, UserRole, AuthLayer

auth_bp = Blueprint("auth", __name__)
auth = AuthLayer()

# Paths that don't require authentication
PUBLIC_PATHS = {"/health", "/login", "/logout", "/telegram/webhook",
                "/api/login", "/media", "/static"}


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
            return redirect(url_for("main.index"))
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
def login_page():
    # Handle JSON POST (used by Shunya OS frontend)
    if request.method == "POST" and request.is_json:
        data = request.get_json(silent=True) or {}
        email = data.get("email", "").strip().lower()
        password = data.get("password", "")
        user = TeamMember.query.filter_by(email=email, is_active=True).first()
        if user and user.check_password(password):
            session["user_id"] = user.id
            user.last_login = datetime.utcnow()
            user.generate_token()
            db.session.commit()
            return jsonify({"success": True, "redirect": url_for("main.index")})
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
            next_url = request.args.get("next") or url_for("main.index")
            return redirect(next_url)

        flash("Invalid email or password", "error")
        return render_template("login.html")

    if session.get("user_id"):
        return redirect(url_for("main.index"))
    return render_template("login.html")


# Shunya OS frontend posts to /auth/login/password — alias to same handler
@auth_bp.route("/login/password", methods=["POST"])
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
        return redirect(url_for("main.index"))
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