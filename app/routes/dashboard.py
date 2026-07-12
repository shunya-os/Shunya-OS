"""Shunya OS — Dashboard."""
from flask import Blueprint, render_template, g, jsonify, redirect, url_for
from app import db
from app.routes.auth import login_required

dashboard_bp = Blueprint("dashboard", __name__)


@dashboard_bp.route("/api/vertical/metrics")
@login_required
def vertical_metrics_api():
    """Return computed metrics for the current tenant's vertical."""
    from app.shunya.verticals import get_vertical
    from app.models import Entity, EntityDefinition

    vertical_id = (g.tenant.vertical_config or {}).get("vertical", "custom")
    v = get_vertical(vertical_id)
    if not v:
        return jsonify({})

    metrics = v.get("dashboard_metrics", [])
    result = {}

    for m in metrics:
        key = m.get("key", "")
        prefix = m.get("prefix", "")
        suffix = m.get("suffix", "")

        if key in ("total_bookings", "total_trips"):
            for et in ["booking", "trip", "order", "admission"]:
                ed = EntityDefinition.query.filter_by(tenant_id=g.tenant.id, type=et).first()
                if ed:
                    cnt = Entity.query.filter_by(tenant_id=g.tenant.id, definition_id=ed.id, is_archived=False).count()
                    result[key] = f"{prefix}{cnt}{suffix}"
                    break
            else:
                result[key] = f"{prefix}0{suffix}"
        elif key == "active_leads":
            ed = EntityDefinition.query.filter_by(tenant_id=g.tenant.id, type="lead").first()
            if ed:
                cnt = Entity.query.filter_by(tenant_id=g.tenant.id, definition_id=ed.id, is_archived=False).filter(~Entity.status.in_(["converted", "lost"])).count()
                result[key] = f"{prefix}{cnt}{suffix}"
            else:
                result[key] = f"{prefix}0{suffix}"
        elif key in ("monthly_revenue", "today_earnings", "revenue", "fees_collected", "outstanding"):
            result[key] = f"{prefix}—{suffix}"
        elif key == "active_cases":
            ed = EntityDefinition.query.filter_by(tenant_id=g.tenant.id, type="case").first()
            cnt = Entity.query.filter_by(tenant_id=g.tenant.id, definition_id=ed.id, is_archived=False).count() if ed else 0
            result[key] = f"{prefix}{cnt}{suffix}"
        elif key.endswith("_count") or key.startswith("total_"):
            tname = key.replace("total_", "").replace("_count", "").rstrip("s")
            ed = EntityDefinition.query.filter_by(tenant_id=g.tenant.id, type=tname).first()
            cnt = Entity.query.filter_by(tenant_id=g.tenant.id, definition_id=ed.id, is_archived=False).count() if ed else 0
            result[key] = f"{prefix}{cnt}{suffix}"
        elif key in ("pending_invoices", "pending_bills", "pending"):
            ed = EntityDefinition.query.filter_by(tenant_id=g.tenant.id, type="invoice").first()
            if ed:
                cnt = Entity.query.filter_by(tenant_id=g.tenant.id, definition_id=ed.id, is_archived=False).filter(Entity.status.in_(["draft", "sent", "pending"])).count()
                result[key] = f"{prefix}{cnt}{suffix}"
            else:
                result[key] = f"{prefix}0{suffix}"
        elif key == "active_drivers":
            ed = EntityDefinition.query.filter_by(tenant_id=g.tenant.id, type="driver").first()
            cnt = Entity.query.filter_by(tenant_id=g.tenant.id, definition_id=ed.id, is_archived=False).count() if ed else 0
            result[key] = f"{prefix}{cnt}{suffix}"
        elif key == "fleet_size":
            ed = EntityDefinition.query.filter_by(tenant_id=g.tenant.id, type="vehicle").first()
            cnt = Entity.query.filter_by(tenant_id=g.tenant.id, definition_id=ed.id, is_archived=False).count() if ed else 0
            result[key] = f"{prefix}{cnt}{suffix}"
        else:
            result[key] = f"{prefix}—{suffix}"

    return jsonify(result)


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
    from app.models import Business, Brand, Tenant
    user = g.user
    businesses = db.session.query(Business).filter_by(owner_id=user.id).all()
    biz_data = []
    for biz in businesses:
        brands = db.session.query(Brand).filter_by(business_id=biz.id).all()
        brand_data = []
        for brand in brands:
            t = db.session.query(Tenant).filter_by(brand_id=brand.id).first()
            brand_data.append({
                "id": brand.id, "name": brand.name,
                "logo_url": brand.logo_url or "",
                "brand_color": brand.brand_color or "#2563eb",
                "vertical": biz.business_type,
                "tenant_id": t.id if t else None,
                "tenant_slug": t.slug if t else None,
                "is_active": t.is_active if t else False,
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
    if not g.tenant.onboarding_completed:
        return redirect(url_for("onboarding.onboarding_page"))

    from app.models import Entity, EntityDefinition, ActivityLog
    from app.shunya.bird import Bird
    from app.shunya.next_best_action import NextBestActionEngine
    from app.shunya.verticals import get_vertical

    tenant = g.tenant
    user = g.user
    definitions = EntityDefinition.query.filter_by(tenant_id=tenant.id, is_active=True).all()

    def_counts = {}
    for d in definitions:
        count = Entity.query.filter_by(tenant_id=tenant.id, definition_id=d.id, is_archived=False).count()
        def_counts[d.type] = {"label": d.label_plural or d.label, "icon": d.icon, "count": count}

    recent = ActivityLog.query.filter_by(tenant_id=tenant.id)\
        .order_by(ActivityLog.created_at.desc()).limit(10).all()
    bird = Bird(tenant.id, user.id, user.role, user.name)
    greeting = bird.greet()
    next_actions = NextBestActionEngine.get_for_user(tenant.id, user.id, user.role)

    vertical_metrics = []
    vertical_actions = []
    try:
        vid = (tenant.vertical_config or {}).get("vertical", "custom")
        vc = get_vertical(vid)
        if vc:
            vertical_metrics = vc.get("dashboard_metrics", [])
            vertical_actions = vc.get("quick_actions", [])
    except Exception:
        pass

    return render_template("dashboard.html",
        tenant=tenant, user=user,
        definitions=definitions, def_counts=def_counts,
        recent_activities=recent,
        greeting=greeting, next_actions=next_actions,
        vertical_metrics=vertical_metrics, vertical_actions=vertical_actions,
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