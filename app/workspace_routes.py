"""
SHUNYA OS — Workspace Routes
Phase Z1: First Product Experience
"""

from flask import Blueprint, render_template, request, session, redirect, url_for
from datetime import datetime

workspace_bp = Blueprint("workspace", __name__, url_prefix="/workspace")


@workspace_bp.route("/")
def workspace_home():
    """Main workspace entry point — Morning Zero."""
    return render_template("shunya_home.html", year=datetime.utcnow().year)


@workspace_bp.route("/converse")
def workspace_converse():
    """AI conversation view."""
    query = request.args.get("q", "")
    # In production, this would load the conversation from the database
    # For now, render the conversation template with the query
    messages = []
    if query:
        messages = [
            {"role": "human", "content": query, "time": "just now"},
            {
                "role": "assistant",
                "content": "Let me think about that. I'll surface what I know about your organization.",
                "time": "just now",
            },
        ]
    return render_template(
        "shunya_converse.html",
        messages=messages,
        query=query,
        year=datetime.utcnow().year,
    )


@workspace_bp.route("/object/<object_id>")
def workspace_object(object_id):
    """Object detail page."""
    # In production, this would load from the database
    # For now, render a sample object
    object_data = {
        "name": "Jupiter Media Partnership",
        "object_type": "Agreement",
        "created_at": "14 Jul 2026",
        "space": "Executive",
        "health_class": "good",
        "health_label": "Healthy",
        "health_pct": 85,
        "description": "Strategic partnership agreement with Jupiter Media. Scope includes Q3-Q4 deliverables across 3 regions. The agreement covers content distribution, joint marketing initiatives, and shared analytics infrastructure. Both parties have committed to a minimum 18-month engagement with quarterly performance reviews.",
        "brief_summary": "Strategic partnership performing well. Key milestones on track for Q3 delivery. Recommend scheduling quarterly review.",
        "timeline": [
            {"type": "decision", "title": "Agreement signed", "date": "14 Jul 2026", "source": "Legal"},
            {"type": "change", "title": "Scope finalized", "date": "10 Jul 2026", "source": "Executive"},
            {"type": "evidence", "title": "Due diligence complete", "date": "5 Jul 2026", "source": "Compliance"},
            {"type": "decision", "title": "Initial proposal approved", "date": "28 Jun 2026", "source": "Board"},
        ],
        "evidence": [
            {"source": "Legal Review", "title": "Contract v2.4 — Signed", "confidence": "High confidence"},
            {"source": "Compliance", "title": "Regulatory clearance — Region A", "confidence": "High confidence"},
            {"source": "Finance", "title": "Budget allocation confirmed", "confidence": "Medium confidence"},
        ],
        "links": [
            {"type": "Organization", "name": "Jupiter Media"},
            {"type": "Space", "name": "Executive"},
            {"type": "Object", "name": "Q3 Budget Allocation"},
            {"type": "Contact", "name": "Sarah Chen"},
        ],
        "reasoning": [
            {"label": "Initial assessment", "content": "Partnership aligns with strategic growth objectives. Revenue projection: +18% QoQ."},
            {"label": "Risk analysis", "content": "Low regulatory risk. Currency exposure hedged. Recommend quarterly review cadence."},
            {"label": "Recommendation", "content": "Proceed with signing. All conditions met. Monitor first 90 days closely."},
        ],
        "insights": [
            {"label": "Revenue impact", "detail": "Projected +18% QoQ from this partnership", "confidence": "High confidence"},
            {"label": "Risk score", "detail": "Low — 2.3/10 based on 6 risk factors", "confidence": "Medium confidence"},
            {"label": "Next action", "detail": "Schedule quarterly review before 15 Oct", "confidence": "High confidence"},
        ],
        "related": [
            {"name": "Q3 Budget Allocation", "type": "Object", "relationship": "linked"},
            {"name": "Sarah Chen", "type": "Contact", "relationship": "stakeholder"},
            {"name": "Executive Space", "type": "Space", "relationship": "parent"},
        ],
    }
    return render_template(
        "shunya_object.html",
        object=object_data,
        year=datetime.utcnow().year,
    )


@workspace_bp.route("/executive")
def workspace_executive():
    """Executive dashboard view."""
    return render_template("shunya_executive.html", year=datetime.utcnow().year)


@workspace_bp.route("/verify")
def workspace_verify():
    """Identity verification page."""
    return render_template("shunya_verify.html", email=request.args.get("email", ""), year=datetime.utcnow().year)


@workspace_bp.route("/loading")
def workspace_loading():
    """Loading screen between auth and workspace."""
    return render_template("shunya_loading.html", redirect=url_for("workspace.workspace_home"), year=datetime.utcnow().year)


@workspace_bp.route("/coherence")
def coherence_board():
    """Visual coherence board showing all screens at 3 sizes."""
    return render_template("coherence_board.html", year=datetime.utcnow().year)