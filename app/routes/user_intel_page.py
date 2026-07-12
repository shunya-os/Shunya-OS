"""Shunya OS — User Intelligence Dashboard page."""
from flask import Blueprint, render_template, g
from app.routes.auth import login_required

user_intel_page_bp = Blueprint("user_intel_page", __name__)

@user_intel_page_bp.route("/user-intel")
@login_required
def user_intel():
    return render_template("user_intelligence.html",
        tenant=g.tenant, user=g.user)