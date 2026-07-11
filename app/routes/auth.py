"""Shunya OS — Authentication routes (login, signup, OTP, magic links, OAuth, sessions)."""
import functools
from datetime import datetime
from flask import Blueprint, request, jsonify, render_template, redirect, url_for, session, g, flash
from app import db
from app.models import TeamMember, Tenant, UserSession, LoginCode, OAuthAccount
from app.utils import generate_token, generate_otp, hash_token, minutes_from_now, hours_from_now

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")


# ---------------------------------------------------------------------------
# Decorators
# ---------------------------------------------------------------------------

def login_required(view):
    @functools.wraps(view)
    def wrapped(**kwargs):
        user = _get_current_user()
        if not user:
            if request.path.startswith("/api/") or request.is_json:
                return jsonify({"error": "Authentication required"}), 401
            return redirect(url_for("auth.login_page"))
        g.user = user
        g.tenant = db.session.get(Tenant, user.tenant_id) if user.tenant_id else None
        return view(**kwargs)
    return wrapped


def admin_required(view):
    @functools.wraps(view)
    @login_required
    def wrapped(**kwargs):
        if g.user.role != "admin":
            flash("Admin access required", "error")
            return redirect(url_for("dashboard.index"))
        return view(**kwargs)
    return wrapped


# ---------------------------------------------------------------------------
# Session helpers
# ---------------------------------------------------------------------------

def _get_current_user():
    """Get current user from session token."""
    token = session.get("session_token")
    if not token:
        return None
    token_hash = hash_token(token)
    sess = UserSession.query.filter_by(token=token_hash, is_active=True).first()
    if not sess or sess.expires_at < datetime.utcnow():
        if sess:
            sess.is_active = False
            db.session.commit()
        return None
    return db.session.get(TeamMember, sess.user_id)


def _create_session(user: TeamMember, device_info: str = "", ip: str = "") -> str:
    """Create a new user session."""
    token = generate_token(48)
    token_hash = hash_token(token)
    sess = UserSession(
        user_id=user.id,
        token=token_hash,
        device_info=device_info[:500],
        ip_address=ip[:45],
        expires_at=hours_from_now(24),
    )
    db.session.add(sess)
    user.last_login = datetime.utcnow()
    db.session.commit()
    session["session_token"] = token
    session["user_id"] = user.id
    session["tenant_id"] = user.tenant_id
    return token


# ---------------------------------------------------------------------------
# Public pages
# ---------------------------------------------------------------------------

@auth_bp.route("/login", methods=["GET"])
def login_page():
    if _get_current_user():
        return redirect(url_for("dashboard.index"))
    return render_template("login.html")


@auth_bp.route("/signup", methods=["GET"])
def signup_page():
    if _get_current_user():
        return redirect(url_for("dashboard.index"))
    return render_template("signup.html")


# ---------------------------------------------------------------------------
# Email + Password login
# ---------------------------------------------------------------------------

@auth_bp.route("/login/password", methods=["POST"])
def login_password():
    data = request.get_json(silent=True) or request.form
    email = data.get("email", "").strip().lower()
    password = data.get("password", "")

    if not email or not password:
        return jsonify({"error": "Email and password required"}), 400

    user = TeamMember.query.filter_by(email=email).first()
    if not user or not user.check_password(password):
        return jsonify({"error": "Invalid email or password"}), 401
    if not user.is_active:
        return jsonify({"error": "Account is deactivated"}), 403

    _create_session(user, request.headers.get("User-Agent", ""), request.remote_addr or "")
    return jsonify({"success": True, "redirect": url_for("dashboard.index")})


# ---------------------------------------------------------------------------
# Signup
# ---------------------------------------------------------------------------

@auth_bp.route("/signup", methods=["POST"])
def signup():
    data = request.get_json(silent=True) or request.form
    name = data.get("name", "").strip()
    email = data.get("email", "").strip().lower()
    password = data.get("password", "")
    company_name = data.get("company_name", "").strip()
    business_type = data.get("business_type", "other")

    if not all([name, email, password, company_name]):
        return jsonify({"error": "Name, email, password, and company name required"}), 400

    if TeamMember.query.filter_by(email=email).first():
        return jsonify({"error": "Email already registered"}), 409

    # Create tenant
    from app.utils import slugify
    tenant = Tenant(
        company_name=company_name,
        slug=slugify(company_name) or f"tenant-{generate_token(6).lower()}",
        business_type=business_type,
    )
    db.session.add(tenant)
    db.session.flush()

    # Create admin user
    user = TeamMember(
        tenant_id=tenant.id,
        name=name,
        email=email,
        role="admin",
    )
    user.set_password(password)
    db.session.add(user)
    db.session.commit()

    _create_session(user, request.headers.get("User-Agent", ""), request.remote_addr or "")
    return jsonify({"success": True, "redirect": url_for("dashboard.index")})


# ---------------------------------------------------------------------------
# OTP login (phone)
# ---------------------------------------------------------------------------

@auth_bp.route("/login/otp/send", methods=["POST"])
def send_otp():
    data = request.get_json(silent=True) or request.form
    phone = data.get("phone", "").strip()
    if not phone:
        return jsonify({"error": "Phone number required"}), 400

    user = TeamMember.query.filter_by(phone=phone).first()
    if not user:
        return jsonify({"error": "No account found with this phone"}), 404

    otp = generate_otp()
    code = LoginCode(
        tenant_id=user.tenant_id,
        phone=phone,
        code=hash_token(otp),
        type="otp",
        expires_at=minutes_from_now(5),
    )
    db.session.add(code)
    db.session.commit()

    # TODO: Send OTP via SMS/WhatsApp
    print(f"[OTP] {phone}: {otp}")  # Dev only

    return jsonify({"success": True, "message": "OTP sent to your phone"})


@auth_bp.route("/login/otp/verify", methods=["POST"])
def verify_otp():
    data = request.get_json(silent=True) or request.form
    phone = data.get("phone", "").strip()
    otp = data.get("otp", "").strip()

    if not phone or not otp:
        return jsonify({"error": "Phone and OTP required"}), 400

    code = LoginCode.query.filter_by(phone=phone, type="otp", is_used=False)\
        .order_by(LoginCode.created_at.desc()).first()
    if not code or code.expires_at < datetime.utcnow():
        return jsonify({"error": "OTP expired or invalid"}), 401
    if code.code != hash_token(otp):
        return jsonify({"error": "Invalid OTP"}), 401

    code.is_used = True
    user = TeamMember.query.filter_by(phone=phone).first()
    if not user:
        return jsonify({"error": "No account found"}), 404

    _create_session(user, request.headers.get("User-Agent", ""), request.remote_addr or "")
    db.session.commit()
    return jsonify({"success": True, "redirect": url_for("dashboard.index")})


# ---------------------------------------------------------------------------
# Magic link (email)
# ---------------------------------------------------------------------------

@auth_bp.route("/login/magic-link", methods=["POST"])
def send_magic_link():
    data = request.get_json(silent=True) or request.form
    email = data.get("email", "").strip().lower()
    if not email:
        return jsonify({"error": "Email required"}), 400

    user = TeamMember.query.filter_by(email=email).first()
    if not user:
        return jsonify({"error": "No account found with this email"}), 404

    token = generate_token(32)
    code = LoginCode(
        tenant_id=user.tenant_id,
        email=email,
        code=hash_token(token),
        type="magic_link",
        expires_at=minutes_from_now(15),
    )
    db.session.add(code)
    db.session.commit()

    magic_url = url_for("auth.login_magic_verify", token=token, _external=True)
    # TODO: Send email with magic link
    print(f"[MAGIC] {email}: {magic_url}")  # Dev only

    return jsonify({"success": True, "message": "Magic link sent to your email"})


@auth_bp.route("/login/magic", methods=["GET"])
def login_magic_verify():
    token = request.args.get("token", "")
    if not token:
        flash("Invalid magic link", "error")
        return redirect(url_for("auth.login_page"))

    code = LoginCode.query.filter_by(type="magic_link", is_used=False)\
        .order_by(LoginCode.created_at.desc()).limit(10).all()
    code = next((c for c in code if c.code == hash_token(token)), None)

    if not code or code.expires_at < datetime.utcnow():
        flash("Magic link expired or invalid", "error")
        return redirect(url_for("auth.login_page"))

    code.is_used = True
    user = TeamMember.query.filter_by(email=code.email).first()
    if not user:
        flash("Account not found", "error")
        return redirect(url_for("auth.login_page"))

    _create_session(user, request.headers.get("User-Agent", ""), request.remote_addr or "")
    db.session.commit()
    return redirect(url_for("dashboard.index"))


# ---------------------------------------------------------------------------
# Session management
# ---------------------------------------------------------------------------

@auth_bp.route("/sessions", methods=["GET"])
@login_required
def list_sessions():
    sessions_data = []
    for s in UserSession.query.filter_by(user_id=g.user.id, is_active=True)\
            .order_by(UserSession.created_at.desc()).limit(20).all():
        sessions_data.append({
            "id": s.id, "device_info": s.device_info, "ip_address": s.ip_address,
            "created_at": s.created_at.isoformat() if s.created_at else None,
            "expires_at": s.expires_at.isoformat() if s.expires_at else None,
            "is_current": s.token == hash_token(session.get("session_token", "")),
        })
    if request.is_json:
        return jsonify({"sessions": sessions_data})
    return render_template("settings_sessions.html", sessions=sessions_data)


@auth_bp.route("/sessions/<int:session_id>/revoke", methods=["POST"])
@login_required
def revoke_session(session_id):
    sess = db.session.get(UserSession, session_id)
    if not sess or sess.user_id != g.user.id:
        return jsonify({"error": "Session not found"}), 404
    sess.is_active = False
    db.session.commit()
    return jsonify({"success": True})


@auth_bp.route("/sessions/revoke-all", methods=["POST"])
@login_required
def revoke_all_sessions():
    current_token = hash_token(session.get("session_token", ""))
    for s in UserSession.query.filter_by(user_id=g.user.id, is_active=True).all():
        if s.token != current_token:
            s.is_active = False
    db.session.commit()
    return jsonify({"success": True})


# ---------------------------------------------------------------------------
# Logout
# ---------------------------------------------------------------------------

@auth_bp.route("/logout", methods=["GET", "POST"])
def logout():
    token = session.get("session_token")
    if token:
        token_hash = hash_token(token)
        sess = UserSession.query.filter_by(token=token_hash).first()
        if sess:
            sess.is_active = False
            db.session.commit()
    session.clear()
    return redirect(url_for("auth.login_page"))
