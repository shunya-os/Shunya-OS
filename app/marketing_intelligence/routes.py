"""SHUNYA Marketing Intelligence — FDA15 Routes."""
from flask import Blueprint, jsonify, request
from app import db
from app.authz.decorators import _resolve_org_id, require_permission
from app.marketing_intelligence import service as mi

analytics_bp = Blueprint("analytics", __name__, url_prefix="/api/v1/analytics")


def _org_context():
    """Server-resolved organization context — client params are never trusted.

    B18: the historical ``tenant_id`` query parameter (default 1) allowed any
    caller to read or write any tenant's marketing data. Identity and tenant
    are now resolved server-side from the verified session/membership.
    """
    org_id = _resolve_org_id()
    if not org_id:
        return None
    return org_id


@analytics_bp.route("/attribution/<int:campaign_id>", methods=["GET"])
@require_permission("rel.view")
def attribution(campaign_id):
    org_id = _org_context()
    if not org_id:
        return jsonify({"error": "No organization context"}), 400
    result = mi.get_attribution(campaign_id, org_id)
    return jsonify(result)


@analytics_bp.route("/conversion", methods=["GET"])
@require_permission("rel.view")
def conversion():
    org_id = _org_context()
    if not org_id:
        return jsonify({"error": "No organization context"}), 400
    result = mi.get_conversion(org_id)
    return jsonify(result)


@analytics_bp.route("/channels", methods=["GET"])
@require_permission("rel.view")
def channels():
    org_id = _org_context()
    if not org_id:
        return jsonify({"error": "No organization context"}), 400
    result = mi.compare_channels(org_id)
    return jsonify({"channels": result})


@analytics_bp.route("/revenue-trace/<int:customer_id>", methods=["GET"])
@require_permission("rel.view")
def revenue_trace(customer_id):
    org_id = _org_context()
    if not org_id:
        return jsonify({"error": "No organization context"}), 400
    result = mi.revenue_trace(customer_id, org_id)
    if result is None:
        return jsonify({"error": "Customer not found"}), 404
    return jsonify(result)


@analytics_bp.route("/waste/<int:campaign_id>", methods=["GET"])
@require_permission("rel.view")
def waste(campaign_id):
    org_id = _org_context()
    if not org_id:
        return jsonify({"error": "No organization context"}), 400
    result = mi.get_waste(campaign_id, org_id)
    return jsonify(result)


@analytics_bp.route("/cac", methods=["GET"])
@require_permission("rel.view")
def cac():
    org_id = _org_context()
    if not org_id:
        return jsonify({"error": "No organization context"}), 400
    result = mi.get_cac(org_id)
    return jsonify(result)


@analytics_bp.route("/experiments", methods=["GET", "POST"])
@require_permission("rel.view")
def experiments():
    from app.marketing.models import Experiment
    org_id = _org_context()
    if not org_id:
        return jsonify({"error": "No organization context"}), 400
    if request.method == "GET":
        exps = Experiment.query.filter_by(tenant_id=org_id).all()
        return jsonify({"experiments": [{
            "id": e.id, "name": e.name, "campaign_id": e.campaign_id,
            "hypothesis": e.hypothesis, "variant": e.variant,
            "status": e.status, "metric": e.metric,
            "confidence": e.confidence, "sample_size": e.sample_size,
        } for e in exps]})
    if not _has_perm("rel.create"):
        return jsonify({"success": False, "error": "Forbidden: missing permission"}), 403
    data = request.get_json() or {}
    exp = Experiment(
        campaign_id=data.get("campaign_id"),
        name=data.get("name", "Experiment"),
        hypothesis=data.get("hypothesis", ""),
        variant=data.get("variant", "A"),
        status=data.get("status", "planned"),
        metric=data.get("metric", "conversion"),
        tenant_id=org_id,
    )
    db.session.add(exp)
    db.session.commit()
    return jsonify({"id": exp.id, "name": exp.name, "status": exp.status}), 201


@analytics_bp.route("/experiments/<int:eid>", methods=["GET", "PATCH"])
@require_permission("rel.view")
def experiment(eid):
    from app.marketing.models import Experiment
    org_id = _org_context()
    if not org_id:
        return jsonify({"error": "No organization context"}), 400
    exp = Experiment.query.filter_by(id=eid, tenant_id=org_id).first()
    if not exp:
        return jsonify({"error": "Experiment not found"}), 404
    if request.method == "GET":
        return jsonify({"id": exp.id, "name": exp.name, "campaign_id": exp.campaign_id,
                        "hypothesis": exp.hypothesis, "variant": exp.variant,
                        "status": exp.status, "metric": exp.metric,
                        "confidence": exp.confidence, "sample_size": exp.sample_size})
    if not _has_perm("rel.edit"):
        return jsonify({"success": False, "error": "Forbidden: missing permission"}), 403
    data = request.get_json() or {}
    for k in ("status", "confidence", "sample_size", "variant"):
        if k in data:
            setattr(exp, k, data[k])
    db.session.commit()
    return jsonify({"id": exp.id, "status": exp.status})


def _has_perm(permission: str) -> bool:
    """Permission check against the SAME resolved org context (B18)."""
    from app.authz.services import check_permission
    from app.authz.decorators import _resolve_identity
    identity = _resolve_identity()
    if not identity:
        return False
    org_id = _org_context()
    if not org_id:
        return False
    return check_permission(org_id, identity, permission)