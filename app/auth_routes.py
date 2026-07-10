"""
Panchi Club — Auth Routes & Middleware (Phase 3A)

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
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        # Handle superadmin creation on first login
        if email == "admin@panchi.club":
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