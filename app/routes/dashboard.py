"""Shunya OS — Dashboard."""
from flask import Blueprint, render_template, g, jsonify, redirect, url_for
from app import db
from app.routes.auth import login_required

dashboard_bp = Blueprint("dashboard", __name__)


@dashboard_bp.route("/health")
def health():
    """Health check with diagnostics."""
    import time, os as _os, subprocess
    start = time.time()
    status = {"status": "ok"}
    try:
        from sqlalchemy import text
        db.session.execute(text("SELECT 1"))
        db.session.commit()
        status["database"] = "connected"
    except Exception as e:
        status["database"] = f"error: {e}"
        status["status"] = "degraded"

    status["response_ms"] = round((time.time() - start) * 1000, 1)
    try:
        if _os.path.exists("/root/shunya_os/.git"):
            status["version"] = subprocess.check_output(
                ["git", "describe", "--tags", "--always"],
                cwd="/root/shunya_os", stderr=subprocess.DEVNULL
            ).decode().strip()
    except Exception:
        status["version"] = "dev"
    return jsonify(status)


@dashboard_bp.route("/owner")
@login_required
def owner_dashboard():
    """Owner view — all businesses across all brands."""
    from app.models import Business, Brand, Tenant
    user = g.user
    businesses = db.session.query(Business).filter_by(owner_id=user.id).all()
    biz_data = []
    for biz in businesses:
        brands = db.session.query(Brand).filter_by(business_id=biz.id).all()
        brand_data = []
        for brand in brands:
            tenant = db.session.query(Tenant).filter_by(brand_id=brand.id).first()
            brand_data.append({
                "id": brand.id, "name": brand.name,
                "logo_url": brand.logo_url or "",
                "brand_color": brand.brand_color or "#2563eb",
                "vertical": biz.business_type,
                "tenant_id": tenant.id if tenant else None,
                "tenant_slug": tenant.slug if tenant else None,
                "is_active": tenant.is_active if tenant else False,
            })
        biz_data.append({
            "id": biz.id, "name": biz.name,
            "business_type": biz.business_type, "brands": brand_data,
        })
    return render_template("owner_dashboard.html",
        user=user, businesses=biz_data,
        total_businesses=len(businesses),
        total_brands=sum(len(b["brands"]) for b in biz_data),
    )


@dashboard_bp.route("/")
@login_required
def index():
    """Home dashboard — context-aware, never dead-end."""
    if not g.tenant.onboarding_completed:
        return redirect(url_for("onboarding.onboarding_page"))

    from app.models import Entity, EntityDefinition, ActivityLog
    from app.shunya.bird import Bird
    from app.shunya.next_best_action import NextBestActionEngine

    tenant = g.tenant
    user = g.user

    definitions = EntityDefinition.query.filter_by(
        tenant_id=tenant.id, is_active=True
    ).all()

    def_counts = {}
    for d in definitions:
        count = Entity.query.filter_by(
            tenant_id=tenant.id, definition_id=d.id, is_archived=False
        ).count()
        def_counts[d.type] = {"label": d.label_plural or d.label, "icon": d.icon, "count": count}

    recent = ActivityLog.query.filter_by(tenant_id=tenant.id)\
        .order_by(ActivityLog.created_at.desc()).limit(10).all()

    bird = Bird(tenant.id, user.id, user.role, user.name)
    greeting = bird.greet()
    next_actions = NextBestActionEngine.get_for_user(tenant.id, user.id, user.role)

    return render_template("dashboard.html",
        tenant=tenant, user=user,
        definitions=definitions,
        def_counts=def_counts,
        recent_activities=recent,
        greeting=greeting,
        next_actions=next_actions,
    )


@dashboard_bp.route("/analytics")
@login_required
def analytics():
    return render_template("analytics.html", tenant=g.tenant)


@dashboard_bp.route("/api/analytics")
@login_required
def analytics_api():
    return jsonify({"entities": {}})


@dashboard_bp.route("/learning")
@login_required
def learning():
    return render_template("analytics.html", tenant=g.tenant)