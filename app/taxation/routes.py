"""Taxation API routes."""
from flask import jsonify, request
from app import db
from app.taxation import taxation_bp
from app.taxation.models import TaxRule, BusinessRule, TaxationRefreshLog
from app.taxation.fetcher import seed_baseline_rules, refresh_all_sources
from app.authz.decorators import require_permission


@taxation_bp.route("/rules", methods=["GET"])
@require_permission("finance.view")
def api_list_rules():
    """List tax rules, optionally filtered by category and jurisdiction."""
    category = request.args.get("category")
    jurisdiction = request.args.get("jurisdiction", "IN")
    business_type = request.args.get("business_type", "*")
    q = TaxRule.query.filter_by(jurisdiction=jurisdiction, is_active=True)
    if category:
        q = q.filter_by(category=category)
    if business_type != "*":
        q = q.filter_by(business_type=business_type)
    rules = q.order_by(TaxRule.category, TaxRule.section).all()
    return jsonify({"rules": [r.to_dict() for r in rules], "count": len(rules)})


@taxation_bp.route("/rules/<int:rule_id>", methods=["GET"])
@require_permission("finance.view")
def api_get_rule(rule_id):
    rule = db.session.get(TaxRule, rule_id)
    if not rule:
        return jsonify({"error": "Not found"}), 404
    return jsonify({"rule": rule.to_dict()})


@taxation_bp.route("/business-rules", methods=["GET"])
@require_permission("finance.view")
def api_business_rules():
    category = request.args.get("category")
    jurisdiction = request.args.get("jurisdiction", "IN")
    q = BusinessRule.query.filter_by(jurisdiction=jurisdiction, is_active=True)
    if category:
        q = q.filter_by(category=category)
    rules = q.order_by(BusinessRule.category).all()
    return jsonify({"rules": [r.to_dict() for r in rules], "count": len(rules)})


@taxation_bp.route("/refresh", methods=["POST"])
@require_permission("finance.edit_invoice")
def api_trigger_refresh():
    """Manually trigger a refresh of all tax rule sources."""
    result = refresh_all_sources()
    return jsonify({"success": True, "result": result})


@taxation_bp.route("/seed", methods=["POST"])
@require_permission("finance.edit_invoice")
def api_seed():
    """Seed baseline tax rules (idempotent)."""
    seed_baseline_rules()
    count = TaxRule.query.count()
    return jsonify({"success": True, "rules_count": count})


@taxation_bp.route("/refresh-log", methods=["GET"])
@require_permission("finance.view")
def api_refresh_log():
    logs = TaxationRefreshLog.query.order_by(
        TaxationRefreshLog.started_at.desc()
    ).limit(20).all()
    return jsonify({"logs": [{
        "started_at": l.started_at.isoformat() if l.started_at else None,
        "completed_at": l.completed_at.isoformat() if l.completed_at else None,
        "sources_attempted": l.sources_attempted,
        "sources_success": l.sources_success,
        "rules_created": l.rules_created,
        "error": l.error,
    } for l in logs]})