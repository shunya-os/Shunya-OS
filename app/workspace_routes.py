"""
SHUNYA OS — Workspace Routes
Phase Z2: The First Five Minutes
"""

from flask import Blueprint, render_template, request, session, redirect, url_for
from datetime import datetime

workspace_bp = Blueprint("workspace", __name__, url_prefix="/workspace")

# ─── Shared context for the first-five-minutes story ───
# This tells a coherent story across all screens.
# The user's organization is "Nexus Ventures" — a mid-market PE firm.
# SHUNYA has been observing their operations for 3 days.

ORGANIZATION = "Nexus Ventures"
ORG_DESCRIPTION = (
    "Nexus Ventures is a mid-market private equity firm "
    "with 24 active portfolio companies. SHUNYA has been "
    "observing operations for 3 days and has identified "
    "several patterns worth surfacing."
)


@workspace_bp.route("/")
def workspace_home():
    """Main workspace entry point — Morning Zero.
    
    The user's first moment inside SHUNYA. The AI should
    speak first, proactively, like an executive partner.
    """
    now = datetime.utcnow()
    return render_template(
        "shunya_home.html",
        year=now.year,
        org_name=ORGANIZATION,
        org_description=ORG_DESCRIPTION,
    )


@workspace_bp.route("/converse")
def workspace_converse():
    """AI conversation view.
    
    The AI must behave like an executive partner, never a chatbot.
    It should progressively reveal capability, not overwhelm.
    It should answer before the question forms.
    """
    query = request.args.get("q", "").strip()
    now = datetime.utcnow()
    messages = []

    if query:
        # Executive partner responses — never "I'm an AI", never hedging
        responses = {
            "revenue": (
                "Revenue across your portfolio is trending +12% QoQ. "
                "Three companies are driving this: Jupiter Media (+18%), "
                "Atlas Logistics (+9%), and Pine Street Partners (+7%). "
                "I recommend scheduling a review of Atlas — their margin "
                "improvement is outpacing revenue growth, which is unusual."
            ),
            "risk": (
                "I've flagged two portfolio companies for attention. "
                "Northgate Manufacturing has a covenant breach risk in "
                "45 days if their current cash burn continues. "
                "Pine Street Partners has a leadership transition that "
                "needs monitoring — the CFO departure was unexpected. "
                "Want me to prepare a brief on either?"
            ),
            "attention": (
                "Three items need your attention today. "
                "1. Jupiter Media partnership — Q3 deliverables due this week. "
                "2. Northgate Manufacturing — cash flow alert. "
                "3. Budget approval — Q3 engineering allocation pending your sign-off. "
                "I've prepared the context for each. Where would you like to start?"
            ),
            "team": (
                "Your team has 12 active members. Sarah Chen is handling "
                "the Jupiter Media onboarding. Marcus Webb is preparing "
                "the Q3 budget review. Both are on track. "
                "Would you like me to give you a status overview?"
            ),
        }

        # Find the best response
        lower = query.lower()
        response = None
        for keyword, reply in responses.items():
            if keyword in lower:
                response = reply
                break

        if not response:
            response = (
                f"I've been reviewing {ORGANIZATION}'s operations for 3 days now. "
                "I can see patterns in your portfolio, surface risks before they "
                "escalate, and help you make decisions faster. "
                "Try asking about revenue, risk, or what needs your attention today."
            )

        messages = [
            {"role": "human", "content": query, "time": "just now"},
            {"role": "assistant", "content": response, "time": "just now"},
        ]

    return render_template(
        "shunya_converse.html",
        messages=messages,
        query=query,
        year=now.year,
        org_name=ORGANIZATION,
    )


@workspace_bp.route("/object/<object_id>")
def workspace_object(object_id):
    """Object detail page.
    
    The first real object the user sees. Should feel like a
    living document that SHUNYA is actively observing.
    """
    now = datetime.utcnow()

    # Realistic sample objects keyed by ID
    objects = {
        "jupiter-media": {
            "name": "Jupiter Media Partnership",
            "object_type": "Agreement",
            "created_at": "14 Jul 2026",
            "space": "Executive",
            "health_class": "good",
            "health_label": "Healthy",
            "health_pct": 85,
            "description": (
                "Strategic partnership agreement with Jupiter Media, a digital "
                "publishing company with 4M monthly readers. The agreement covers "
                "content distribution, joint marketing initiatives, and shared "
                "analytics infrastructure across 3 regions (NA, EU, APAC). "
                "Both parties have committed to an 18-month engagement with "
                "quarterly performance reviews. Revenue share is 60/40 in our "
                "favour for the first 12 months."
            ),
            "brief_summary": (
                "Partnership performing ahead of expectations. Content "
                "distribution launched in 2 of 3 regions. Q3 milestones "
                "on track. Recommend scheduling the first quarterly "
                "review before 15 Oct to capture early learnings."
            ),
            "timeline": [
                {"type": "decision", "title": "Agreement signed", "date": "14 Jul 2026", "source": "Legal"},
                {"type": "change", "title": "Scope finalized after negotiation", "date": "10 Jul 2026", "source": "Executive"},
                {"type": "evidence", "title": "Due diligence cleared — no material risks", "date": "5 Jul 2026", "source": "Compliance"},
                {"type": "decision", "title": "Board approved initial proposal", "date": "28 Jun 2026", "source": "Board"},
                {"type": "evidence", "title": "Market analysis: 18% QoQ growth projected", "date": "20 Jun 2026", "source": "Strategy"},
            ],
            "evidence": [
                {"source": "Legal Review", "title": "Contract v2.4 — fully executed", "confidence": "High confidence"},
                {"source": "Compliance", "title": "Regulatory clearance — NA and EU regions", "confidence": "High confidence"},
                {"source": "Finance", "title": "Budget allocation confirmed ($1.2M)", "confidence": "Medium confidence"},
                {"source": "Strategy", "title": "Market analysis report", "confidence": "High confidence"},
            ],
            "links": [
                {"type": "Organization", "name": "Jupiter Media"},
                {"type": "Space", "name": "Executive"},
                {"type": "Object", "name": "Q3 Budget Allocation"},
                {"type": "Contact", "name": "Sarah Chen — Lead"},
                {"type": "Object", "name": "Northgate Manufacturing"},
            ],
            "reasoning": [
                {"label": "Strategic alignment", "content": "Partnership aligns with growth objectives. Expands reach into digital publishing vertical. Revenue projection: +18% QoQ with 60/40 revenue share."},
                {"label": "Risk assessment", "content": "Low regulatory risk. Currency exposure in APAC region is hedged. Key-person dependency on Jupiter's editorial director — recommend documenting contingency."},
                {"label": "Recommendation", "content": "Proceed with Q3 deliverables. Schedule first quarterly review before 15 Oct. Monitor APAC rollout closely — regulatory environment is evolving."},
            ],
            "insights": [
                {"label": "Revenue impact", "detail": "Projected +18% QoQ, $1.2M allocated", "confidence": "High confidence"},
                {"label": "Risk score", "detail": "2.3/10 — low, based on 6 risk factors", "confidence": "Medium confidence"},
                {"label": "Next action", "detail": "Schedule quarterly review by 15 Oct", "confidence": "High confidence"},
                {"label": "Velocity", "detail": "Partnership is 3 weeks ahead of typical timeline", "confidence": "Medium confidence"},
            ],
            "related": [
                {"name": "Q3 Budget Allocation", "type": "Object", "relationship": "linked"},
                {"name": "Sarah Chen", "type": "Contact", "relationship": "stakeholder"},
                {"name": "Executive Space", "type": "Space", "relationship": "parent"},
                {"name": "Jupiter Media — Org Profile", "type": "Object", "relationship": "reference"},
            ],
        },
        "northgate-mfg": {
            "name": "Northgate Manufacturing",
            "object_type": "Portfolio Company",
            "created_at": "12 Mar 2026",
            "space": "Portfolio",
            "health_class": "caution",
            "health_label": "Needs attention",
            "health_pct": 62,
            "description": (
                "Northgate Manufacturing is a precision components manufacturer "
                "serving the automotive and aerospace industries. 340 employees, "
                "two facilities (Ohio and Monterrey). Revenue has been stable at "
                "$28M annually, but cash flow has tightened over the last 2 quarters "
                "due to rising raw material costs and a delayed aerospace contract."
            ),
            "brief_summary": (
                "Cash flow is the primary concern. Current burn rate suggests "
                "covenant breach risk within 45 days if untreated. The aerospace "
                "contract delay is the root cause — resolution expected within "
                "30 days. Recommend interim financing conversation."
            ),
            "timeline": [
                {"type": "risk", "title": "Cash flow alert triggered", "date": "22 Jul 2026", "source": "SHUNYA"},
                {"type": "change", "title": "Aerospace contract delayed 60 days", "date": "15 Jul 2026", "source": "Operations"},
                {"type": "evidence", "title": "Q2 financials filed — revenue stable", "date": "10 Jul 2026", "source": "Finance"},
                {"type": "decision", "title": "New CFO appointed", "date": "1 Jul 2026", "source": "Board"},
                {"type": "evidence", "title": "Raw material cost up 12% YoY", "date": "28 Jun 2026", "source": "Procurement"},
            ],
            "evidence": [
                {"source": "SHUNYA", "title": "Cash flow analysis — 45 days to covenant breach", "confidence": "High confidence"},
                {"source": "Finance", "title": "Q2 2026 financial statements", "confidence": "High confidence"},
                {"source": "Operations", "title": "Aerospace contract timeline update", "confidence": "Medium confidence"},
            ],
            "links": [
                {"type": "Space", "name": "Portfolio"},
                {"type": "Contact", "name": "Marcus Webb — Partner"},
                {"type": "Object", "name": "Q3 Covenant Tracker"},
                {"type": "Organization", "name": "Aerospace Dynamics (customer)"},
            ],
            "reasoning": [
                {"label": "Cash flow analysis", "content": "Burn rate is $340K/month above projections. At current trajectory, covenant headroom will be exhausted in 45 days. The aerospace contract delay is the primary driver — once resolved, cash flow normalizes."},
                {"label": "Recommendation", "content": "Two options: (1) Interim financing of $800K to bridge the gap, or (2) negotiate covenant waiver with lender. Option 1 is faster but more expensive. Recommend discussing with Marcus Webb."},
                {"label": "Monitoring", "content": "I'll alert you if the situation changes. Key metrics to watch: accounts receivable days, raw material costs, and the aerospace contract status."},
            ],
            "insights": [
                {"label": "Covenant risk", "detail": "45 days until breach at current burn rate", "confidence": "High confidence"},
                {"label": "Root cause", "detail": "Aerospace contract delay — resolution in ~30 days", "confidence": "Medium confidence"},
                {"label": "Recommendation", "detail": "Discuss interim financing with Marcus Webb", "confidence": "High confidence"},
                {"label": "Trend", "detail": "Revenue stable, margins compressed 4%", "confidence": "High confidence"},
            ],
            "related": [
                {"name": "Marcus Webb", "type": "Contact", "relationship": "partner"},
                {"name": "Q3 Covenant Tracker", "type": "Object", "relationship": "linked"},
                {"name": "Portfolio Review — Jul 2026", "type": "Object", "relationship": "reference"},
            ],
        },
    }

    object_data = objects.get(object_id, objects["jupiter-media"])
    return render_template(
        "shunya_object.html",
        object=object_data,
        year=now.year,
        org_name=ORGANIZATION,
    )


@workspace_bp.route("/executive")
def workspace_executive():
    """Executive dashboard — the first meaningful success.
    
    The user should feel like SHUNYA has been watching their
    organization and has real, actionable intelligence.
    """
    now = datetime.utcnow()
    return render_template(
        "shunya_executive.html",
        year=now.year,
        org_name=ORGANIZATION,
        org_description=ORG_DESCRIPTION,
    )


@workspace_bp.route("/verify")
def workspace_verify():
    """Identity verification page."""
    return render_template(
        "shunya_verify.html",
        email=request.args.get("email", ""),
        year=datetime.utcnow().year,
    )


@workspace_bp.route("/loading")
def workspace_loading():
    """Loading screen — the transition from auth to workspace."""
    return render_template(
        "shunya_loading.html",
        redirect=url_for("workspace.workspace_home"),
        org_name=ORGANIZATION,
        year=datetime.utcnow().year,
    )


@workspace_bp.route("/founder")
def founder_workspace():
    """Founder Workspace — primary operating interface for SHUNYA."""
    return render_template("founder_workspace.html", year=datetime.utcnow().year)


@workspace_bp.route("/coherence")
def coherence_board():
    """Visual coherence board showing all screens at 3 sizes."""
    return render_template(
        "coherence_board.html",
        year=datetime.utcnow().year,
    )