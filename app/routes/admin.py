"""Admin routes — company profile, brand, team management, permissions."""
import os, json, hashlib
from datetime import datetime, date
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

# ── Bulk Data Import ──

@admin_bp.route("/import", methods=["GET"])
@login_required
@admin_required
def import_page():
    """Data import page — user picks entity type and uploads data."""
    from app.models import EntityDefinition
    definitions = EntityDefinition.query.filter_by(
        tenant_id=g.tenant.id, is_active=True
    ).order_by(EntityDefinition.type).all()
    tenant_vertical = g.tenant.vertical_config.get("vertical", "custom") if g.tenant.vertical_config else "custom"
    return render_template("admin/import.html",
        definitions=definitions,
        tenant_vertical=tenant_vertical,
    )


@admin_bp.route("/api/import/inspect", methods=["POST"])
@login_required
@admin_required
def import_inspect():
    """Inspect uploaded data and match columns to entity schema."""
    from app.shunya.data_import import inspect_data, parse_csv, parse_json
    from app.models import EntityDefinition

    entity_type = request.form.get("entity_type", "")
    definition = EntityDefinition.query.filter_by(
        tenant_id=g.tenant.id, type=entity_type
    ).first()
    if not definition:
        return jsonify({"error": f"Entity type '{entity_type}' not found"}), 400

    file = request.files.get("file")
    json_text = request.form.get("json_data", "")

    data_rows = []

    if file and file.filename:
        raw = file.read().decode("utf-8", errors="replace")
        if file.filename.endswith(".csv"):
            data_rows = parse_csv(raw)
        else:
            try:
                data_rows = parse_json(raw)
            except Exception:
                return jsonify({"error": "Could not parse file. Upload CSV or JSON."}), 400
    elif json_text.strip():
        try:
            data_rows = parse_json(json_text)
        except Exception as e:
            return jsonify({"error": f"Invalid JSON: {str(e)}"}), 400
    else:
        return jsonify({"error": "No data provided. Upload a file or paste JSON."}), 400

    if not data_rows:
        return jsonify({"error": "No rows found in data"}), 400

    preview = inspect_data(data_rows, entity_type, definition.schema, definition.label)

    return jsonify({
        "entity_type": preview.entity_type,
        "entity_label": preview.entity_label,
        "total_rows": preview.total_rows,
        "matched_columns": [
            {"column": m.column, "field_name": m.field_name,
             "field_label": m.field_label, "confidence": m.confidence}
            for m in preview.matched_columns
        ],
        "unmatched_columns": preview.unmatched_columns,
        "sample_rows": preview.sample_rows,
        "missing_required": preview.missing_required,
    })


@admin_bp.route("/api/import/execute", methods=["POST"])
@login_required
@admin_required
def import_execute():
    """Execute import with user-confirmed field mapping."""
    from app.shunya.data_import import import_data
    from app.models import EntityDefinition

    data = request.get_json(silent=True) or {}
    entity_type = data.get("entity_type", "")
    field_mapping = data.get("field_mapping", {})
    rows = data.get("rows", [])

    definition = EntityDefinition.query.filter_by(
        tenant_id=g.tenant.id, type=entity_type
    ).first()
    if not definition:
        return jsonify({"error": f"Entity type '{entity_type}' not found"}), 400

    result = import_data(
        data_rows=rows,
        entity_type=entity_type,
        schema=definition.schema,
        tenant_id=g.tenant.id,
        definition_id=definition.id,
        field_mapping=field_mapping,
        user_id=g.user.id,
        db_session=db.session,
    )

    return jsonify(result)


# ── API Key Management ──


@admin_bp.route("/keys", methods=["GET"])
@login_required
@admin_required
def keys_page():
    """Render the API key management template."""
    return render_template("admin/keys.html")


@admin_bp.route("/api/keys", methods=["GET"])
@login_required
@admin_required
def list_keys():
    """List all API keys for the current tenant."""
    from app.models import ApiKey
    keys = db.session.query(ApiKey).filter_by(tenant_id=g.tenant.id).order_by(
        ApiKey.created_at.desc()
    ).all()
    return jsonify([k.to_dict() for k in keys])


@admin_bp.route("/api/keys", methods=["POST"])
@login_required
@admin_required
def create_key():
    """Generate a new API key (returns the full raw key ONCE)."""
    import secrets
    from app.models import ApiKey

    data = request.get_json(silent=True) or {}
    name = (data.get("name") or "").strip()
    scopes = data.get("scopes", ["read:*"])

    if not name:
        return jsonify({"error": "Key name is required"}), 400
    if not isinstance(scopes, list) or not scopes:
        return jsonify({"error": "At least one scope is required"}), 400

    # Generate a random API key — shk_ prefix for Shunya Key
    raw_key = f"shk_{secrets.token_urlsafe(32)}"
    key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
    key_prefix = raw_key[:8]

    api_key = ApiKey(
        tenant_id=g.tenant.id,
        name=name,
        key_hash=key_hash,
        key_prefix=key_prefix,
        scopes=scopes,
        is_active=True,
        created_by=g.user.id,
    )
    db.session.add(api_key)
    db.session.commit()

    return jsonify({
        "success": True,
        "key": raw_key,  # ONLY time the full key is returned
        "message": f"API key '{name}' created. Copy it now — it won't be shown again.",
    }), 201


@admin_bp.route("/api/keys/<int:key_id>", methods=["DELETE"])
@login_required
@admin_required
def revoke_key(key_id):
    """Revoke (deactivate) an API key."""
    from app.models import ApiKey
    api_key = db.session.query(ApiKey).filter_by(
        id=key_id, tenant_id=g.tenant.id
    ).first()
    if not api_key:
        return jsonify({"error": "API key not found"}), 404

    api_key.is_active = False
    db.session.commit()
    return jsonify({"success": True, "message": f"Key '{api_key.name}' revoked"})


# ── Email / SMTP Configuration ──

@admin_bp.route("/email", methods=["GET"])
@login_required
@admin_required
def email_page():
    """Render email config page."""
    return render_template("admin/email.html", tenant=g.tenant)


@admin_bp.route("/api/email", methods=["GET"])
@login_required
def get_email_config():
    """Get current SMTP config and notification triggers."""
    t = g.tenant
    cfg = t.ai_config or {}
    smtp = cfg.get("smtp", {})
    notifications = cfg.get("notifications", {})
    return jsonify({
        "smtp": {
            "host": smtp.get("host", ""),
            "port": smtp.get("port", 587),
            "user": smtp.get("user", ""),
            "password": smtp.get("password", ""),
            "from_email": smtp.get("from_email", ""),
        },
        "notifications": {
            "entity_created_lead": notifications.get("entity_created_lead", []),
            "booking_confirmed": notifications.get("booking_confirmed", []),
            "invoice_paid": notifications.get("invoice_paid", []),
            "ticket_assigned": notifications.get("ticket_assigned", []),
        },
    })


@admin_bp.route("/api/email", methods=["POST"])
@login_required
@admin_required
def save_email_config():
    """Save SMTP config and notification triggers."""
    data = request.get_json(silent=True) or {}
    t = g.tenant
    cfg = dict(t.ai_config or {})

    # SMTP config
    smtp = data.get("smtp", {})
    cfg["smtp"] = {
        "host": (smtp.get("host") or "").strip(),
        "port": int(smtp.get("port", 587)),
        "user": (smtp.get("user") or "").strip(),
        "password": (smtp.get("password") or "").strip(),
        "from_email": (smtp.get("from_email") or "").strip(),
    }

    # Notification triggers
    notif = data.get("notifications", {})
    cfg["notifications"] = {
        "entity_created_lead": notif.get("entity_created_lead", []),
        "booking_confirmed": notif.get("booking_confirmed", []),
        "invoice_paid": notif.get("invoice_paid", []),
        "ticket_assigned": notif.get("ticket_assigned", []),
    }

    t.ai_config = cfg
    db.session.commit()
    return jsonify({"success": True, "message": "Email configuration saved"})


@admin_bp.route("/api/email/test", methods=["POST"])
@login_required
@admin_required
def test_email():
    """Send a test email using the saved SMTP config."""
    data = request.get_json(silent=True) or {}
    recipient = (data.get("to") or "").strip()
    if not recipient:
        return jsonify({"error": "Recipient email required"}), 400

    t = g.tenant
    cfg = t.ai_config or {}
    smtp = cfg.get("smtp", {})
    host = smtp.get("host", "").strip()
    port = int(smtp.get("port", 587))
    user = smtp.get("user", "").strip()
    password = smtp.get("password", "").strip()
    from_email = smtp.get("from_email", "").strip() or user

    if not host or not user or not password or not from_email:
        return jsonify({"error": "SMTP not fully configured. Fill in host, user, password, and from_email first."}), 400

    import smtplib
    from email.mime.text import MIMEText
    from email.mime.multipart import MIMEMultipart

    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"🔔 Test Email from {t.company_name or 'Shunya OS'}"
    msg["From"] = from_email
    msg["To"] = recipient
    text = f"Hi there!\n\nThis is a test email from {t.company_name or 'Shunya OS'}.\n\nYour SMTP configuration is working correctly.\n\n— Shunya OS"
    html = f"""<html><body style="font-family:Inter,sans-serif;background:#0f172a;padding:40px;">
<div style="max-width:480px;margin:0 auto;background:#1e293b;border-radius:16px;padding:32px;border:1px solid #334155;">
<div style="text-align:center;margin-bottom:20px;"><span style="font-size:40px;">✅</span></div>
<h2 style="color:#f1f5f9;margin:0 0 8px;">Test Email</h2>
<p style="color:#94a3b8;margin:0 0 4px;">Your SMTP config works for <strong style="color:#e2e8f0;">{t.company_name or 'Shunya OS'}</strong></p>
<p style="color:#64748b;font-size:0.85rem;margin-top:20px;">— Shunya OS</p>
</div></body></html>"""
    msg.attach(MIMEText(text, "plain"))
    msg.attach(MIMEText(html, "html"))

    try:
        with smtplib.SMTP(host, port, timeout=15) as server:
            server.starttls()
            server.login(user, password)
            server.sendmail(from_email, [recipient], msg.as_string())
        return jsonify({"success": True, "message": f"Test email sent to {recipient}"})
    except smtplib.SMTPAuthenticationError:
        return jsonify({"error": "SMTP authentication failed. Check your username/password."}), 502
    except smtplib.SMTPException as e:
        return jsonify({"error": f"SMTP error: {str(e)}"}), 502
    except Exception as e:
        return jsonify({"error": f"Connection failed: {str(e)}"}), 502


# ── Webhook Management ──

@admin_bp.route("/webhooks", methods=["GET"])
@login_required
@admin_required
def webhooks_page():
    return render_template("admin/webhooks.html",
        events=__import__("app.shunya.webhooks", fromlist=["AVAILABLE_EVENTS"]).AVAILABLE_EVENTS)


@admin_bp.route("/api/webhooks", methods=["GET"])
@login_required
@admin_required
def list_webhooks():
    from app.models import Webhook
    hooks = Webhook.query.filter_by(tenant_id=g.tenant.id).order_by(Webhook.created_at.desc()).all()
    return jsonify([h.to_dict() for h in hooks])


@admin_bp.route("/api/webhooks", methods=["POST"])
@login_required
@admin_required
def create_webhook():
    from app.models import Webhook
    data = request.get_json(silent=True) or {}
    url = data.get("url", "").strip()
    if not url.startswith("https://"):
        return jsonify({"error": "Webhook URL must use HTTPS"}), 400
    hook = Webhook(
        tenant_id=g.tenant.id,
        name=data.get("name", "").strip() or "Untitled",
        url=url,
        event=data.get("event", "entity.created"),
        entity_type=data.get("entity_type", "*"),
        headers=data.get("headers", {}),
        secret=data.get("secret", ""),
    )
    db.session.add(hook)
    db.session.commit()
    return jsonify({"success": True, "webhook": hook.to_dict()}), 201


@admin_bp.route("/api/webhooks/<int:hook_id>", methods=["PUT"])
@login_required
@admin_required
def update_webhook(hook_id):
    from app.models import Webhook
    hook = Webhook.query.filter_by(id=hook_id, tenant_id=g.tenant.id).first_or_404()
    data = request.get_json(silent=True) or {}
    if "url" in data:
        url = data["url"].strip()
        if not url.startswith("https://"):
            return jsonify({"error": "Webhook URL must use HTTPS"}), 400
        hook.url = url
    hook.name = data.get("name", hook.name)
    hook.event = data.get("event", hook.event)
    hook.entity_type = data.get("entity_type", hook.entity_type)
    hook.is_active = data.get("is_active", hook.is_active)
    if "secret" in data:
        hook.secret = data["secret"]
    db.session.commit()
    return jsonify({"success": True, "webhook": hook.to_dict()})


@admin_bp.route("/api/webhooks/<int:hook_id>", methods=["DELETE"])
@login_required
@admin_required
def delete_webhook(hook_id):
    from app.models import Webhook
    hook = Webhook.query.filter_by(id=hook_id, tenant_id=g.tenant.id).first_or_404()
    db.session.delete(hook)
    db.session.commit()
    return jsonify({"success": True, "message": "Webhook deleted"})


@admin_bp.route("/api/webhooks/<int:hook_id>/test", methods=["POST"])
@login_required
@admin_required
def test_webhook(hook_id):
    from app.models import Webhook
    from app.shunya.webhooks import _send
    hook = Webhook.query.filter_by(id=hook_id, tenant_id=g.tenant.id).first_or_404()
    test_payload = {"event": "test", "message": "This is a test from Shunya OS", "webhook_id": hook.id}
    _send(hook, test_payload)
    return jsonify({"success": True, "last_status": hook.last_status})


# ── WhatsApp Management ──

@admin_bp.route("/whatsapp", methods=["GET"])
@login_required
@admin_required
def whatsapp_page():
    config = g.tenant.ai_config or {}
    wa = config.get("whatsapp", {}) or {}
    return render_template("admin/whatsapp.html", config=wa)


@admin_bp.route("/api/whatsapp", methods=["GET"])
@login_required
@admin_required
def get_whatsapp_config():
    config = g.tenant.ai_config or {}
    wa = config.get("whatsapp", {}) or {}
    return jsonify({
        "token": wa.get("token", ""),
        "phone_id": wa.get("phone_id", ""),
        "verify_token": wa.get("verify_token", ""),
        "auto_reply": wa.get("auto_reply", ""),
    })


@admin_bp.route("/api/whatsapp", methods=["POST"])
@login_required
@admin_required
def save_whatsapp_config():
    data = request.get_json(silent=True) or {}
    config = g.tenant.ai_config or {}
    config["whatsapp"] = {
        "token": data.get("whatsapp_token", ""),
        "phone_id": data.get("whatsapp_phone_id", ""),
        "verify_token": data.get("whatsapp_verify_token", ""),
        "auto_reply": data.get("whatsapp_auto_reply", ""),
    }
    g.tenant.ai_config = config
    db.session.commit()
    return jsonify({"success": True, "message": "WhatsApp settings saved"})


# ── Kanban Pipeline View ──

@admin_bp.route("/kanban/<entity_type>", methods=["GET"])
@login_required
def kanban_page(entity_type):
    """Render kanban pipeline view for an entity type."""
    from app.models import EntityDefinition
    definition = EntityDefinition.query.filter_by(
        tenant_id=g.tenant.id, type=entity_type
    ).first_or_404()
    return render_template("admin/kanban.html", definition=definition)


@admin_bp.route("/api/kanban/<entity_type>", methods=["GET"])
@login_required
def kanban_api(entity_type):
    """Return entities grouped by status for the kanban board."""
    from app.models import EntityDefinition, Entity
    definition = EntityDefinition.query.filter_by(
        tenant_id=g.tenant.id, type=entity_type
    ).first()
    if not definition:
        return jsonify({"error": f"Entity type '{entity_type}' not found"}), 404

    statuses = definition.statuses or []
    if not statuses:
        return jsonify({
            "statuses": [],
            "columns": {},
            "counts": {},
            "definition": {"type": definition.type, "label": definition.label, "icon": definition.icon},
        })

    # Query all non-archived entities for this definition, ordered by created_at desc
    entities = Entity.query.filter_by(
        tenant_id=g.tenant.id, definition_id=definition.id, is_archived=False
    ).order_by(Entity.created_at.desc()).limit(200).all()

    # Group by status
    columns = {s: [] for s in statuses}
    for e in entities:
        s = e.status
        if s not in columns:
            columns[s] = []
        primary_val = e.data.get(definition.primary_field, "") if definition.primary_field else ""
        columns[s].append({
            "id": e.id,
            "code": e.code or f"#{e.id}",
            "display_name": e.display_name,
            "icon": definition.icon or "📄",
            "status": e.status,
            "primary_value": primary_val,
            "data": {k: v for k, v in (e.data or {}).items()
                     if k in (definition.searchable_fields or []) or k == definition.primary_field},
        })

    # Add entities in statuses not in the definition's pipeline (catch-all)
    counts = {}
    for s in statuses:
        counts[s] = len(columns.get(s, []))
    for s in columns:
        if s not in counts:
            counts[s] = len(columns[s])

    return jsonify({
        "statuses": statuses,
        "columns": columns,
        "counts": counts,
        "definition": {
            "type": definition.type,
            "label": definition.label,
            "label_plural": definition.label_plural,
            "icon": definition.icon,
            "primary_field": definition.primary_field,
        },
    })


# ── Telegram Bot Configuration ──


@admin_bp.route("/telegram", methods=["GET"])
@login_required
@admin_required
def telegram_page():
    """Telegram bot config page."""
    return render_template("admin/telegram.html", tenant=g.tenant)


@admin_bp.route("/api/telegram", methods=["GET"])
@login_required
def get_telegram_config():
    """Get current Telegram bot config."""
    cfg = g.tenant.ai_config or {}
    return jsonify({
        "bot_token": cfg.get("telegram_bot_token", ""),
        "chat_ids": cfg.get("telegram_chat_ids", []),
    })


@admin_bp.route("/api/telegram", methods=["POST"])
@login_required
@admin_required
def save_telegram_config():
    """Save Telegram bot token and chat IDs."""
    data = request.get_json(silent=True) or {}
    token = (data.get("bot_token") or "").strip()
    chat_ids = data.get("chat_ids", [])
    if not isinstance(chat_ids, list):
        chat_ids = [str(chat_ids)]

    # Sanitize chat IDs — allow negative values (group/supergroup IDs)
    cleaned = []
    for cid in chat_ids:
        cid = str(cid).strip()
        if not cid:
            continue
        try:
            int(cid)
            cleaned.append(cid)
        except ValueError:
            pass

    cfg = dict(g.tenant.ai_config or {})
    cfg["telegram_bot_token"] = token
    cfg["telegram_chat_ids"] = cleaned
    g.tenant.ai_config = cfg
    db.session.commit()

    return jsonify({
        "success": True,
        "message": f"Telegram config saved ({len(cleaned)} chat ID(s))",
    })


@admin_bp.route("/api/telegram/test", methods=["POST"])
@login_required
@admin_required
def test_telegram_bot():
    """Send a test message through the configured Telegram bot."""
    cfg = g.tenant.ai_config or {}
    token = cfg.get("telegram_bot_token", "")
    chat_ids = cfg.get("telegram_chat_ids", [])

    if not token:
        return jsonify({"error": "Bot token not configured"}), 400
    if not chat_ids:
        return jsonify({"error": "No chat IDs configured"}), 400

    import requests as http

    success_count = 0
    errors = []

    for cid in chat_ids:
        try:
            resp = http.post(
                f"https://api.telegram.org/bot{token}/sendMessage",
                json={
                    "chat_id": int(cid) if cid.lstrip("-").isdigit() else cid,
                    "text": "🤖 *Hermes Bot Test*\n\nYour Telegram bot is configured correctly!",
                    "parse_mode": "Markdown",
                },
                timeout=10,
            )
            if resp.status_code == 200:
                success_count += 1
            else:
                data = resp.json()
                errors.append(f"chat {cid}: {data.get('description', 'unknown error')}")
        except Exception as e:
            errors.append(f"chat {cid}: {str(e)}")

    if success_count > 0:
        msg = f"Test message sent to {success_count} chat ID(s)"
        if errors:
            msg += f" ({len(errors)} failed)"
        return jsonify({"success": True, "message": msg, "errors": errors})
    else:
        return jsonify({
            "error": "Failed to send test message",
            "details": errors,
        }), 400


# ── Entity Relationship Graph ──


@admin_bp.route("/entity-graph/<int:entity_id>")
@login_required
def entity_graph_page(entity_id):
    """Render the entity relationship graph page."""
    from app.models import Entity
    entity = Entity.query.filter_by(
        id=entity_id, tenant_id=g.tenant.id
    ).first_or_404()
    entity_type = entity.definition.type if entity.definition else "entity"
    return render_template(
        "admin/entity_graph.html",
        entity=entity,
        entity_id=entity.id,
        entity_type=entity_type,
    )


@admin_bp.route("/api/entity-graph/<int:entity_id>")
@login_required
def entity_graph_api(entity_id):
    """Return JSON of linked entities for the graph."""
    from app.models import Entity, EntityDefinition
    from app.shunya.entity_linker import EntityLinker

    entity = Entity.query.filter_by(
        id=entity_id, tenant_id=g.tenant.id
    ).first_or_404()

    # Central entity info
    center = {
        "id": entity.id,
        "code": entity.code,
        "type": entity.definition.type if entity.definition else "unknown",
        "label": entity.definition.label if entity.definition else "Entity",
        "icon": entity.definition.icon if entity.definition else "📌",
        "status": entity.status,
        "display_name": entity.display_name,
        "url": f"/entities/{entity.definition.type if entity.definition else 'entity'}/{entity.id}",
    }

    # Get linked entities via EntityLinker
    raw_links = EntityLinker.get_linked_entities(entity.id)

    parents = [l for l in raw_links if l["direction"] == "parent"]
    children = [l for l in raw_links if l["direction"] == "child"]

    # Also find ActivityLog cross-references for additional context
    from app.models import ActivityLog
    activity_refs = (
        db.session.query(ActivityLog.entity_id, ActivityLog.detail)
        .filter(
            ActivityLog.tenant_id == g.tenant.id,
            ActivityLog.entity_id != entity.id,
            ActivityLog.detail.ilike(f"%{entity.code}%"),
        )
        .order_by(ActivityLog.created_at.desc())
        .limit(10)
        .all()
    )

    related_ids = set()
    for ref_entity_id, ref_detail in activity_refs:
        related_ids.add(int(ref_entity_id))

    # Fetch referenced entities not already in parents/children
    existing_ids = {l["id"] for l in raw_links}
    extra_entities = []
    for rid in related_ids:
        if rid not in existing_ids:
            ref_entity = db.session.get(Entity, rid)
            if ref_entity and ref_entity.tenant_id == g.tenant.id and not ref_entity.is_archived:
                extra_entities.append({
                    "id": ref_entity.id,
                    "code": ref_entity.code,
                    "type": ref_entity.definition.type if ref_entity.definition else "unknown",
                    "label": ref_entity.definition.label if ref_entity.definition else "Entity",
                    "icon": ref_entity.definition.icon if ref_entity.definition else "📌",
                    "status": ref_entity.status,
                    "display_name": ref_entity.display_name,
                    "url": f"/entities/{ref_entity.definition.type if ref_entity.definition else 'entity'}/{ref_entity.id}",
                    "direction": "activity",
                })

    return jsonify({
        "entity": center,
        "entity_label": f"{center['label']} {center['display_name']}",
        "entity_code": entity.code,
        "parents": parents,
        "children": children,
        "related": extra_entities,
    })


# ── Entity Export (CSV / PDF) ──


@admin_bp.route("/api/export/<entity_type>/csv", methods=["GET"])
@login_required
@admin_required
def export_entities_csv(entity_type):
    """Export all entities of a given type as CSV."""
    from app.models import EntityDefinition, Entity
    from app.shunya.export import export_csv

    definition = db.session.query(EntityDefinition).filter_by(
        tenant_id=g.tenant.id, type=entity_type
    ).first()
    if not definition:
        return jsonify({"error": f"Entity type '{entity_type}' not found"}), 404

    entities = db.session.query(Entity).filter_by(
        tenant_id=g.tenant.id, definition_id=definition.id, is_archived=False
    ).order_by(Entity.created_at.desc()).all()

    csv_string = export_csv(entity_type, entities, definition.schema)

    filename = f"{entity_type}_{datetime.utcnow().strftime('%Y%m%d')}.csv"
    from flask import Response
    return Response(
        csv_string,
        mimetype="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@admin_bp.route("/api/export/<entity_type>/pdf", methods=["GET"])
@login_required
@admin_required
def export_entities_pdf(entity_type):
    """Export all entities of a given type as JSON list (PDF placeholder)."""
    from app.models import EntityDefinition, Entity
    from app.shunya.export import export_json

    definition = db.session.query(EntityDefinition).filter_by(
        tenant_id=g.tenant.id, type=entity_type
    ).first()
    if not definition:
        return jsonify({"error": f"Entity type '{entity_type}' not found"}), 404

    entities = db.session.query(Entity).filter_by(
        tenant_id=g.tenant.id, definition_id=definition.id, is_archived=False
    ).order_by(Entity.created_at.desc()).all()

    rows = export_json(entity_type, entities, definition.schema)

    return jsonify({
        "entity_type": entity_type,
        "label": definition.label,
        "total": len(rows),
        "rows": rows,
    })


# ── Calendar View ──


@admin_bp.route("/calendar", methods=["GET"])
@login_required
@admin_required
def calendar_page():
    """Render the unified calendar view."""
    today = date.today()
    return render_template("admin/calendar.html",
        tenant=g.tenant,
        year=today.year,
        month=today.month,
        today=today.isoformat(),
    )


@admin_bp.route("/api/calendar", methods=["GET"])
@login_required
def get_calendar_events():
    """Return events for a given month (all date-based entities)."""
    import calendar as cal_mod
    from app.shunya.calendar import get_events_for_month

    year = request.args.get("year", type=int) or date.today().year
    month = request.args.get("month", type=int) or date.today().month

    # Clamp month to valid range
    if month < 1:
        month = 1
        year -= 1
    elif month > 12:
        month = 12
        year += 1

    events = get_events_for_month(g.tenant.id, year, month)

    # Month metadata
    _, days_in_month = cal_mod.monthrange(year, month)
    first_weekday = date(year, month, 1).weekday()  # Monday=0, Sunday=6

    # Build day grid (7 columns: Mon Tue Wed Thu Fri Sat Sun)
    days = []
    # Pad leading empty cells
    for _ in range(first_weekday):
        days.append(None)
    for d in range(1, days_in_month + 1):
        days.append(d)

    return jsonify({
        "year": year,
        "month": month,
        "month_name": date(year, month, 1).strftime("%B"),
        "days_in_month": days_in_month,
        "first_weekday": first_weekday,
        "days": days,
        "events": events,
        "today": date.today().isoformat(),
    })


# ── Global Search ──


@admin_bp.route("/search", methods=["GET"])
@login_required
@admin_required
def global_search_page():
    """Render the global search page."""
    return render_template("admin/global_search.html")


@admin_bp.route("/api/search", methods=["GET"])
@login_required
def global_search_api():
    """Search across ALL entity types for the current tenant."""
    q = request.args.get("q", "").strip()
    if not q or len(q) < 2:
        return jsonify({"results": {}, "total": 0, "query": q})

    from app.models import EntityDefinition, Entity

    # Get all active entity definitions for this tenant
    definitions = EntityDefinition.query.filter_by(
        tenant_id=g.tenant.id, is_active=True
    ).order_by(EntityDefinition.label).all()

    results = {}
    total_count = 0
    max_per_type = 5
    max_total = 50

    search_term = f"%{q}%"

    for definition in definitions:
        if total_count >= max_total:
            break

        # Search by code, status, and data['name'] (JSONB text search)
        search_filter = db.or_(
            Entity.code.ilike(search_term),
            Entity.status.ilike(search_term),
            Entity.data["name"].as_string().ilike(search_term),
        )

        # Also search searchable_fields if defined
        if definition.searchable_fields:
            extra_filters = []
            for field_name in definition.searchable_fields:
                if field_name and field_name != "name":
                    extra_filters.append(
                        Entity.data[field_name].as_string().ilike(search_term)
                    )
            if extra_filters:
                search_filter = db.or_(search_filter, *extra_filters)

        entities = (
            Entity.query.filter_by(
                tenant_id=g.tenant.id,
                definition_id=definition.id,
                is_archived=False,
            )
            .filter(search_filter)
            .order_by(Entity.updated_at.desc())
            .limit(max_per_type)
            .all()
        )

        if entities:
            remaining = max_total - total_count
            if remaining <= 0:
                break
            results[definition.type] = {
                "label": definition.label,
                "label_plural": definition.label_plural or definition.label,
                "icon": definition.icon or "📋",
                "count": len(entities),
                "entities": [
                    {
                        **e.to_dict(),
                        "display_name": e.display_name,
                    }
                    for e in entities
                ],
            }
            total_count += len(entities)

    return jsonify({
        "results": results,
        "total": total_count,
        "query": q,
    })
