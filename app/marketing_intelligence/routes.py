"""SHUNYA Marketing Intelligence — FDA15 Routes."""
from flask import Blueprint, jsonify, request
from app import db
from app.marketing_intelligence import service as mi

analytics_bp = Blueprint("analytics", __name__, url_prefix="/api/v1/analytics")


@analytics_bp.route("/attribution/<int:campaign_id>", methods=["GET"])
def attribution(campaign_id):
    tenant_id = request.args.get("tenant_id", 1, type=int)
    result = mi.get_attribution(campaign_id, tenant_id)
    return jsonify(result)


@analytics_bp.route("/conversion", methods=["GET"])
def conversion():
    tenant_id = request.args.get("tenant_id", 1, type=int)
    result = mi.get_conversion(tenant_id)
    return jsonify(result)


@analytics_bp.route("/channels", methods=["GET"])
def channels():
    tenant_id = request.args.get("tenant_id", 1, type=int)
    result = mi.compare_channels(tenant_id)
    return jsonify({"channels": result})


@analytics_bp.route("/revenue-trace/<int:customer_id>", methods=["GET"])
def revenue_trace(customer_id):
    tenant_id = request.args.get("tenant_id", 1, type=int)
    result = mi.revenue_trace(customer_id, tenant_id)
    if result is None:
        return jsonify({"error": "Customer not found"}), 404
    return jsonify(result)


@analytics_bp.route("/waste/<int:campaign_id>", methods=["GET"])
def waste(campaign_id):
    tenant_id = request.args.get("tenant_id", 1, type=int)
    result = mi.get_waste(campaign_id, tenant_id)
    return jsonify(result)


@analytics_bp.route("/cac", methods=["GET"])
def cac():
    tenant_id = request.args.get("tenant_id", 1, type=int)
    result = mi.get_cac(tenant_id)
    return jsonify(result)


@analytics_bp.route("/experiments", methods=["GET", "POST"])
def experiments():
    from app.marketing.models import Experiment
    tenant_id = request.args.get("tenant_id", 1, type=int)
    if request.method == "GET":
        exps = Experiment.query.filter_by(tenant_id=tenant_id).all()
        return jsonify({"experiments": [{
            "id": e.id, "name": e.name, "campaign_id": e.campaign_id,
            "hypothesis": e.hypothesis, "variant": e.variant,
            "status": e.status, "metric": e.metric,
            "confidence": e.confidence, "sample_size": e.sample_size,
        } for e in exps]})
    data = request.get_json() or {}
    exp = Experiment(
        campaign_id=data.get("campaign_id"),
        name=data.get("name", "Experiment"),
        hypothesis=data.get("hypothesis", ""),
        variant=data.get("variant", "A"),
        status=data.get("status", "planned"),
        metric=data.get("metric", "conversion"),
        tenant_id=tenant_id,
    )
    db.session.add(exp)
    db.session.commit()
    return jsonify({"id": exp.id, "name": exp.name, "status": exp.status}), 201


@analytics_bp.route("/experiments/<int:eid>", methods=["GET", "PATCH"])
def experiment(eid):
    from app.marketing.models import Experiment
    exp = Experiment.query.get(eid)
    if not exp:
        return jsonify({"error": "Experiment not found"}), 404
    if request.method == "GET":
        return jsonify({"id": exp.id, "name": exp.name, "campaign_id": exp.campaign_id,
                        "hypothesis": exp.hypothesis, "variant": exp.variant,
                        "status": exp.status, "metric": exp.metric,
                        "confidence": exp.confidence, "sample_size": exp.sample_size})
    data = request.get_json() or {}
    for k in ("status", "confidence", "sample_size", "variant"):
        if k in data:
            setattr(exp, k, data[k])
    db.session.commit()
    return jsonify({"id": exp.id, "status": exp.status})