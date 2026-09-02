"""SHUNYA Sales Intelligence — FDA12 Routes."""
from flask import Blueprint, jsonify, request
from app.sales_intelligence import service as si

sales_bp = Blueprint("sales_intelligence", __name__, url_prefix="/api/v1/sales")


@sales_bp.route("/score/<int:lead_id>", methods=["GET"])
def score(lead_id):
    result = si.lead_scoring(lead_id)
    return jsonify(result)


@sales_bp.route("/opportunities", methods=["GET"])
def sales_opportunities():
    """Alias to commercial opportunities for unified sales surface."""
    from app.commercial.routes import list_opportunities
    return list_opportunities()


@sales_bp.route("/next-action/<int:lead_id>", methods=["GET"])
def next_action(lead_id):
    result = si.next_best_action(lead_id)
    return jsonify({"recommendations": result})


@sales_bp.route("/pipeline", methods=["GET"])
def pipeline():
    from app.authz.decorators import _resolve_org_id
    tenant_id = _resolve_org_id()
    if not tenant_id:
        return jsonify({"error": "No organization context"}), 400
    result = si.pipeline_health(tenant_id)
    return jsonify(result)


@sales_bp.route("/forecast", methods=["GET"])
def forecast():
    from app.authz.decorators import _resolve_org_id
    tenant_id = _resolve_org_id()
    if not tenant_id:
        return jsonify({"error": "No organization context"}), 400
    months = request.args.get("months", 3, type=int)
    result = si.forecast(tenant_id, months)
    return jsonify(result)


@sales_bp.route("/salesperson/<agent_id>", methods=["GET"])
def salesperson(agent_id):
    result = si.salesperson_intel(agent_id)
    return jsonify(result)


@sales_bp.route("/conversion", methods=["GET"])
def conversion():
    from app.authz.decorators import _resolve_org_id
    tenant_id = _resolve_org_id()
    if not tenant_id:
        return jsonify({"error": "No organization context"}), 400
    result = si.conversion_analysis(tenant_id)
    return jsonify(result)