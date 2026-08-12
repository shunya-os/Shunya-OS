"""SHUNYA Marketing OS — FDA14 Routes."""
from flask import Blueprint, jsonify, request
from datetime import datetime
from app import db
from app.marketing.models import Campaign
from app.marketing_os import service as mo

mkt_bp = Blueprint("marketing_os", __name__, url_prefix="/api/v1/marketing")


@mkt_bp.route("/campaigns", methods=["GET"])
def list_campaigns():
    tenant_id = request.args.get("tenant_id", 1, type=int)
    camps = mo.list_campaigns(tenant_id)
    return jsonify({"campaigns": camps})


@mkt_bp.route("/campaigns", methods=["POST"])
def create_campaign():
    data = request.get_json() or {}
    tenant_id = data.get("tenant_id", 1)
    start = datetime.fromisoformat(data["start_date"]) if data.get("start_date") else None
    end = datetime.fromisoformat(data["end_date"]) if data.get("end_date") else None
    camp = mo.create_campaign(
        name=data.get("name", "Campaign"), tenant_id=tenant_id,
        description=data.get("description"), objective=data.get("objective"),
        owner=data.get("owner"), status=data.get("status", "draft"),
        budget=data.get("budget", 0), budget_type=data.get("budget_type", "total"),
        start_date=start, end_date=end,
        utm_source=data.get("utm_source"), utm_campaign=data.get("utm_campaign"),
        utm_medium=data.get("utm_medium"), created_by=data.get("created_by"),
    )
    return jsonify(camp.to_dict()), 201


@mkt_bp.route("/campaigns/<int:cid>", methods=["GET", "PATCH", "DELETE"])
def campaign(cid):
    tenant_id = request.args.get("tenant_id", 1, type=int)
    if request.method == "DELETE":
        camp = Campaign.query.filter_by(id=cid, tenant_id=tenant_id).first()
        if not camp:
            return jsonify({"error": "Not found"}), 404
        db.session.delete(camp)
        db.session.commit()
        return jsonify({"deleted": True})
    if request.method == "GET":
        result = mo.get_campaign(cid, tenant_id)
        if not result:
            return jsonify({"error": "Not found"}), 404
        return jsonify(result)
    data = request.get_json() or {}
    result = mo.update_campaign(cid, tenant_id, **data)
    if not result:
        return jsonify({"error": "Not found"}), 404
    return jsonify(result)


@mkt_bp.route("/audiences", methods=["GET", "POST"])
def audiences():
    tenant_id = request.args.get("tenant_id", 1, type=int)
    if request.method == "GET":
        campaign_id = request.args.get("campaign_id", type=int)
        result = mo.list_audiences(tenant_id, campaign_id)
        return jsonify({"audiences": result})
    data = request.get_json() or {}
    aud = mo.create_audience(
        campaign_id=data.get("campaign_id"),
        name=data.get("name", "Audience"),
        tenant_id=tenant_id,
        description=data.get("description"),
        criteria_json=data.get("criteria_json", "{}"),
        source=data.get("source", "manual"),
    )
    return jsonify({"id": aud.id, "name": aud.name}), 201


@mkt_bp.route("/content", methods=["GET", "POST"])
def content():
    tenant_id = request.args.get("tenant_id", 1, type=int)
    if request.method == "GET":
        from app.marketing.models import CampaignContent
        items = CampaignContent.query.filter_by(tenant_id=tenant_id).all()
        return jsonify({"content": [{
            "id": c.id, "campaign_id": c.campaign_id, "title": c.title,
            "content_type": c.content_type, "status": c.status,
            "owner": c.owner, "approval_commitment_id": c.approval_commitment_id,
        } for c in items]})
    data = request.get_json() or {}
    content = mo.create_content(
        campaign_id=data.get("campaign_id"),
        title=data.get("title", "Content"),
        tenant_id=tenant_id,
        content_type=data.get("content_type", "post"),
        body=data.get("body", ""),
        asset_url=data.get("asset_url", ""),
        owner=data.get("owner"),
    )
    return jsonify({"id": content.id, "title": content.title, "status": content.status}), 201


@mkt_bp.route("/content/<int:cid>/approve", methods=["POST"])
def approve_content(cid):
    tenant_id = request.args.get("tenant_id", 1, type=int)
    data = request.get_json() or {}
    result = mo.approve_content(cid, tenant_id, data.get("approver", ""))
    if not result:
        return jsonify({"error": "Content not found"}), 404
    return jsonify(result)


@mkt_bp.route("/capture-lead", methods=["POST"])
def capture_lead():
    data = request.get_json() or {}
    tenant_id = data.pop("tenant_id", 1)
    result = mo.capture_lead(tenant_id, **data)
    return jsonify(result), 201