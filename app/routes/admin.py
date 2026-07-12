"""Admin routes — company profile, brand, team management, permissions."""
import os, json, hashlib
from datetime import datetime
from flask import Blueprint, request, jsonify, render_template, g, redirect, url_for, current_app
from app import db
from app.models import Tenant, TeamMember, UserRole
from app.routes.auth import login_required, admin_required
from app.shunya.theme import THEMES

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")

# ── Brand Profile ──

@admin_bp.route("/brand", methods=["GET"])
@login_required
@admin_required
def brand_page():
    return render_template("admin/brand.html", tenant=g.tenant)

@admin_bp.route("/api/brand", methods=["GET"])
@login_required
def get_brand():
    t = g.tenant
    return jsonify({
        "company_name": t.company_name,
        "slug": t.slug,
        "tagline": t.brand_tagline or "",
        "description": t.brand_description or "",
        "logo_url": t.logo_url or "",
        "brand_color": t.brand_color or "#2563eb",
        "brand_color_secondary": t.brand_color_secondary or "#7c3aed",
        "theme_config": t.theme_config or {},
    })

@admin_bp.route("/api/brand", methods=["POST"])
@login_required
@admin_required
def update_brand():
    data = request.get_json(silent=True) or {}
    t = g.tenant
    if "company_name" in data and data["company_name"]:
        t.company_name = data["company_name"].strip()
    if "tagline" in data:
        t.brand_tagline = data["tagline"].strip()
    if "description" in data:
        t.brand_description = data["description"].strip()
    if "brand_color" in data and data["brand_color"]:
        t.brand_color = data["brand_color"].strip()
    if "brand_color_secondary" in data and data["brand_color_secondary"]:
        t.brand_color_secondary = data["brand_color_secondary"].strip()
    db.session.commit()
    return jsonify({"success": True, "message": "Brand updated"})

# ── Logo Upload + Color Extraction ──

@admin_bp.route("/api/logo", methods=["POST"])
@login_required
@admin_required
def upload_logo():
    if "logo" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400
    f = request.files["logo"]
    if f.filename == "":
        return jsonify({"error": "Empty filename"}), 400

    ext = f.filename.rsplit(".", 1)[-1].lower() if "." in f.filename else "png"
    upload_dir = os.path.join(current_app.root_path, "..", "static", "uploads", "brand")
    os.makedirs(upload_dir, exist_ok=True)

    filename = f"logo_{g.tenant.id}_{int(datetime.utcnow().timestamp())}.{ext}"
    path = os.path.join(upload_dir, filename)
    f.save(path)

    # Extract dominant colors via colorthief
    colors = {"primary": "#2563eb", "secondary": "#7c3aed", "bg": "#0f172a"}
    try:
        from colorthief import ColorThief
        ct = ColorThief(path)
        palette = ct.get_palette(color_count=3, quality=5)
        if palette:
            colors["primary"] = "#{:02x}{:02x}{:02x}".format(*palette[0])
        if len(palette) > 1:
            colors["secondary"] = "#{:02x}{:02x}{:02x}".format(*palette[1])
        if len(palette) > 2:
            colors["bg"] = "#{:02x}{:02x}{:02x}".format(*palette[2])
    except ImportError:
        current_app.logger.warning("colorthief not installed — using defaults")
    except Exception as e:
        current_app.logger.warning(f"Color extraction failed: {e}")

    # Update tenant
    t = g.tenant
    t.logo_url = f"/static/uploads/brand/{filename}"
    t.brand_color = colors["primary"]
    t.brand_color_secondary = colors["secondary"]
    # Auto-set theme_config brandverse colors
    cfg = t.theme_config or {}
    cfg["brandverse"] = {
        "primary": colors["primary"],
        "secondary": colors["secondary"],
        "bg": colors["bg"],
        "logo_url": t.logo_url,
    }
    t.theme_config = cfg
    db.session.commit()

    return jsonify({
        "success": True,
        "logo_url": t.logo_url,
        "colors": colors,
        "message": "Logo uploaded and colors extracted. Try the Brandverse theme!",
    })

# ── Theme Sync (call when theme=brandverse is selected) ──

@admin_bp.route("/api/theme/brandverse", methods=["GET"])
@login_required
def get_brandverse_theme():
    t = g.tenant
    cfg = t.theme_config or {}
    bv = cfg.get("brandverse", {})
    primary = bv.get("primary") or t.brand_color or "#2563eb"
    secondary = bv.get("secondary") or t.brand_color_secondary or "#7c3aed"

    # Generate full intelligent palette from the two brand colors
    from app.shunya.theme import generate_brandverse_palette
    palette = generate_brandverse_palette(primary, secondary)

    palette["logo_url"] = t.logo_url or ""
    # Strip personality metadata from API response
    palette.pop("_personality", None)

    # Cache palette in theme_config so page-load JS can get it
    if not bv.get("_palette"):
        cfg["brandverse"] = {**bv, "_palette": palette}
        t.theme_config = cfg
        db.session.commit()

    return jsonify(palette)


# ── Default Theme Management ──

@admin_bp.route("/api/theme/default", methods=["GET"])
@login_required
def get_default_theme():
    """Get the tenant's default theme setting."""
    t = g.tenant
    cfg = t.theme_config or {}
    default_theme = cfg.get("default_theme", "modern")
    return jsonify({
        "default_theme": default_theme,
        "available_themes": [k for k in THEMES.keys()],
    })


@admin_bp.route("/api/theme/default", methods=["POST"])
@login_required
@admin_required
def set_default_theme():
    """Set the tenant-wide default theme (admin only)."""
    data = request.get_json(silent=True) or {}
    theme = (data.get("theme") or "").strip()
    if theme not in THEMES:
        return jsonify({"error": f"Invalid theme: {theme}"}), 400

    cfg = dict(g.tenant.theme_config or {})
    cfg["default_theme"] = theme
    g.tenant.theme_config = cfg
    db.session.commit()

    return jsonify({"success": True, "default_theme": theme})

# ── Team Management ──

@admin_bp.route("/api/team", methods=["GET"])
@login_required
def list_team():
    members = db.session.query(TeamMember).filter_by(tenant_id=g.tenant.id).all()
    return jsonify([{
        "id": m.id,
        "name": m.name,
        "email": m.email,
        "role": m.role,
        "is_active": m.is_active,
        "last_login": m.last_login.isoformat() if m.last_login else None,
        "created_at": m.created_at.isoformat() if m.created_at else None,
    } for m in members])

@admin_bp.route("/api/team/invite", methods=["POST"])
@login_required
@admin_required
def invite_member():
    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip().lower()
    name = (data.get("name") or "").strip()
    role = (data.get("role") or "agent").strip()

    if not email or not name:
        return jsonify({"error": "Name and email required"}), 400
    if role not in [r.value for r in UserRole]:
        return jsonify({"error": f"Invalid role. Must be one of: {', '.join([r.value for r in UserRole])}"}), 400

    existing = db.session.query(TeamMember).filter_by(tenant_id=g.tenant.id, email=email).first()
    if existing:
        return jsonify({"error": "Member already exists"}), 409

    import secrets
    temp_password = secrets.token_urlsafe(12)
    pw_hash = hashlib.sha256(temp_password.encode()).hexdigest()

    member = TeamMember(
        tenant=g.tenant,
        name=name,
        email=email,
        role=role,
        password_hash=pw_hash,
        is_active=True,
    )
    db.session.add(member)
    db.session.commit()

    return jsonify({
        "success": True,
        "message": f"Invited {name} as {role}",
        "temp_password": temp_password,
    })

@admin_bp.route("/api/team/<int:member_id>/role", methods=["PUT"])
@login_required
@admin_required
def update_role(member_id):
    data = request.get_json(silent=True) or {}
    new_role = (data.get("role") or "").strip()
    if new_role not in [r.value for r in UserRole]:
        return jsonify({"error": "Invalid role"}), 400

    m = db.session.query(TeamMember).filter_by(id=member_id, tenant_id=g.tenant.id).first()
    if not m:
        return jsonify({"error": "Member not found"}), 404
    if m.id == g.user.id:
        return jsonify({"error": "Cannot change your own role"}), 400

    m.role = new_role
    db.session.commit()
    return jsonify({"success": True, "message": f"Role updated to {new_role}"})

@admin_bp.route("/api/team/<int:member_id>", methods=["DELETE"])
@login_required
@admin_required
def remove_member(member_id):
    m = db.session.query(TeamMember).filter_by(id=member_id, tenant_id=g.tenant.id).first()
    if not m:
        return jsonify({"error": "Member not found"}), 404
    if m.id == g.user.id:
        return jsonify({"error": "Cannot remove yourself"}), 400
    db.session.delete(m)
    db.session.commit()
    return jsonify({"success": True, "message": "Member removed"})

# ── Sub-account Management ──

@admin_bp.route("/api/subaccounts", methods=["GET"])
@login_required
@admin_required
def list_subaccounts():
    subs = db.session.query(Tenant).filter_by(parent_id=g.tenant.id).all()
    return jsonify([{
        "id": s.id,
        "company_name": s.company_name,
        "slug": s.slug,
        "is_active": s.is_active,
        "plan": s.plan,
        "team_count": db.session.query(TeamMember).filter_by(tenant_id=s.id).count(),
    } for s in subs])

@admin_bp.route("/api/subaccounts", methods=["POST"])
@login_required
@admin_required
def create_subaccount():
    data = request.get_json(silent=True) or {}
    name = (data.get("company_name") or "").strip()
    slug = (data.get("slug") or name.lower().replace(" ", "-")).strip()
    if not name:
        return jsonify({"error": "Company name required"}), 400

    existing = db.session.query(Tenant).filter_by(slug=slug).first()
    if existing:
        return jsonify({"error": "Slug already taken"}), 409

    sub = Tenant(
        company_name=name,
        slug=slug,
        parent_id=g.tenant.id,
        theme_config=g.tenant.theme_config or {},
        brand_color=g.tenant.brand_color or "#2563eb",
        brand_color_secondary=g.tenant.brand_color_secondary or "#7c3aed",
    )
    db.session.add(sub)
    db.session.flush()

    # Create admin for sub-account
    import secrets
    pw = secrets.token_urlsafe(8)
    admin = TeamMember(
        tenant_id=sub.id,
        name=f"{name} Admin",
        email=f"admin@{slug}.panchi.club",
        role="admin",
        password_hash=hashlib.sha256(pw.encode()).hexdigest(),
    )
    db.session.add(admin)
    db.session.commit()

    return jsonify({
        "success": True,
        "message": f"Sub-account '{name}' created",
        "subaccount": {"id": sub.id, "company_name": name, "slug": slug},
        "admin_login": f"admin@{slug}.panchi.club",
        "temp_password": pw,
    })
