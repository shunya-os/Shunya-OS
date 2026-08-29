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
    from flask import session, g
    # Get tenant from authenticated user's team_member record
    user_id = session.get("user_id") or g.get("user_id")
    if user_id:
        from app.auth import TeamMember
        tm = TeamMember.query.get(user_id)
        tenant_id = tm.tenant_id if tm else 1
    else:
        tenant_id = request.args.get("tenant_id", 89, type=int)
    result = si.pipeline_health(tenant_id)
    return jsonify(result)


@sales_bp.route("/forecast", methods=["GET"])
def forecast():
    from flask import session, g
    from app.auth import TeamMember
    user_id = session.get("user_id") or g.get("user_id")
    if user_id:
        tm = TeamMember.query.get(user_id)
        tenant_id = tm.tenant_id if tm else 1
    else:
        tenant_id = request.args.get("tenant_id", 89, type=int)
    months = request.args.get("months", 3, type=int)
    result = si.forecast(tenant_id, months)
    return jsonify(result)


@sales_bp.route("/salesperson/<agent_id>", methods=["GET"])
def salesperson(agent_id):
    result = si.salesperson_intel(agent_id)
    return jsonify(result)


@sales_bp.route("/conversion", methods=["GET"])
def conversion():
    from flask import session
    tenant_id = session.get("current_org_id") or request.args.get("tenant_id", 89, type=int)
    result = si.conversion_analysis(tenant_id)
    return jsonify(result)