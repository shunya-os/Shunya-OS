"""Shunya OS — Getting Started Wizard (first-run onboarding).

New multi-step flow:
1. What describes you? (I own/manage a business / Starting a venture / Exploring)
2. What type of business? (Vertical selection)
3. Business name + Is this part of a group?
4. Brands? (Single or Multiple)
5. Customize (Logo, tagline, color, theme)
6. 🎉 Done — Tenant created with vertical entity types
"""
from flask import Blueprint, render_template, request, jsonify, redirect, url_for, g, session as flask_session
from app import db
from app.models import Tenant, EntityDefinition, BusinessGroup, Business, Brand, TeamMember
from app.routes.auth import login_required
from app.shunya.verticals import VERTICAL_TEMPLATES, get_vertical, get_vertical_list

onboarding_bp = Blueprint("onboarding", __name__, url_prefix="/onboarding")


@onboarding_bp.route("", methods=["GET"])
@login_required
def onboarding_page():
    """Show the multi-step onboarding wizard."""
    verticals = get_vertical_list()
    # If tenant already has vertical_config, they're already set up
    if g.tenant and g.tenant.vertical_config and g.tenant.vertical_config.get("completed"):
        return redirect(url_for("index"))
    return render_template("onboarding.html", verticals=verticals)


@onboarding_bp.route("/api/verticals", methods=["GET"])
@login_required
def list_verticals():
    """Return available verticals as JSON."""
    return jsonify(get_vertical_list())


@onboarding_bp.route("/api/vertical/<vertical_id>", methods=["GET"])
@login_required
def vertical_detail(vertical_id):
    """Return details of a specific vertical template."""
    v = get_vertical(vertical_id)
    if not v:
        return jsonify({"error": "Vertical not found"}), 404
    # Only send summary, not full schema for UI
    return jsonify({
        "id": vertical_id,
        "label": v["label"],
        "icon": v["icon"],
        "description": v["description"],
        "code_prefix": v.get("code_prefix", "BIZ"),
        "theme_icon": v.get("theme_icon", "🧩"),
        "entity_count": len(v.get("entity_types", [])),
        "entity_types": [
            {"type": e["type"], "label": e["label"], "icon": e["icon"]}
            for e in v.get("entity_types", [])
        ],
    })


@onboarding_bp.route("/start", methods=["POST"])
@login_required
def start_onboarding():
    """Execute onboarding — create business hierarchy + instantiate vertical template."""
    data = request.get_json(silent=True) or {}
    vertical_id = data.get("vertical", "custom")
    company_name = data.get("company_name", "").strip() or "My Business"
    has_group = data.get("has_group", False)
    group_name = data.get("group_name", "").strip()
    brands_input = data.get("brands", [company_name])
    tagline = data.get("tagline", "")
    brand_color = data.get("brand_color", "")
    logo_url = data.get("logo_url", "")

    v = get_vertical(vertical_id)
    if not v:
        return jsonify({"error": f"Vertical '{vertical_id}' not found"}), 400

    user_id = g.user.id
    tenant_id = g.tenant.id  # The user is already logged in with a tenant

    # 1. Create or update BusinessGroup
    group = None
    if has_group and group_name:
        group = BusinessGroup(
            name=group_name,
            owner_id=user_id,
            industry="conglomerate",
        )
        db.session.add(group)
        db.session.flush()

    # 2. Create Business
    biz = Business(
        name=company_name,
        owner_id=user_id,
        group_id=group.id if group else None,
        business_type=vertical_id,
    )
    db.session.add(biz)
    db.session.flush()

    # 3. Create Brand(s) and link Tenant
    for bname in brands_input:
        if not bname.strip():
            continue
        brand = Brand(
            name=bname.strip(),
            business_id=biz.id,
            is_default=(bname.strip() == brands_input[0]),
            brand_color=brand_color or v.get("default_brand_color", "#2563eb"),
            brand_tagline=tagline,
        )
        if logo_url:
            brand.logo_url = logo_url
        db.session.add(brand)
        db.session.flush()

        # Update the current tenant to link to this brand
        if g.tenant:
            g.tenant.company_name = bname.strip()
            g.tenant.business_type = vertical_id
            g.tenant.brand_id = brand.id
            g.tenant.business_id = biz.id
            g.tenant.owner_id = user_id
            if brand_color:
                g.tenant.brand_color = brand_color
            if logo_url:
                g.tenant.logo_url = logo_url
            if tagline:
                g.tenant.brand_tagline = tagline

            # Store vertical config
            vc = g.tenant.vertical_config or {}
            vc["vertical"] = vertical_id
            vc["completed"] = True
            g.tenant.vertical_config = vc
            g.tenant.theme_config = g.tenant.theme_config or {}
            g.tenant.theme_config["icon"] = v.get("theme_icon", "🧩")

    # 4. Instantiate entity types from vertical template
    from app.shunya.verticals import get_entity_types_for_vertical
    entity_defs = get_entity_types_for_vertical(vertical_id)

    # Check if entity types already exist for this tenant
    existing_types = set()
    if entity_defs:
        existing = db.session.query(EntityDefinition.type).filter(
            EntityDefinition.tenant_id == g.tenant.id
        ).all()
        existing_types = {e[0] for e in existing}

    created_types = []
    for et in entity_defs:
        if et["type"] in existing_types:
            continue
        statuses = et.get("statuses", ["new", "active", "completed"])
        definition = EntityDefinition(
            tenant_id=g.tenant.id,
            type=et["type"],
            label=et.get("label", et["type"].title()),
            label_plural=et.get("label_plural", ""),
            icon=et.get("icon", "📋"),
            schema=et.get("schema", []),
            statuses=statuses,
            layout=et.get("layout", "table"),
            primary_field=et.get("primary_field", "name"),
        )
        db.session.add(definition)
        created_types.append(et["type"])
        existing_types.add(et["type"])

    # 5. Mark onboarding as complete
    g.tenant.onboarding_completed = True

    db.session.commit()

    # 6. Compute entity code prefixes for the new types
    from app.models import ensure_entity_prefixes
    ensure_entity_prefixes(db.session, g.tenant.id)

    return jsonify({
        "success": True,
        "vertical": vertical_id,
        "company_name": company_name,
        "entity_types_created": created_types,
        "redirect": url_for("index"),
    })


@onboarding_bp.route("/skip", methods=["GET"])
@login_required
def skip_onboarding():
    """Skip onboarding — use custom/general setup."""
    if g.tenant:
        vc = g.tenant.vertical_config or {}
        vc["completed"] = True
        g.tenant.vertical_config = vc
        g.tenant.onboarding_completed = True
        db.session.commit()
    return redirect(url_for("index"))
