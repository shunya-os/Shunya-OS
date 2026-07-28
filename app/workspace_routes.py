"""SHUNYA Phase B1 — Universal Workspace Routes.

The workspace is the single entry point after authentication.
No future application may bypass or replace this workspace.
"""
from flask import Blueprint, render_template, request, session, redirect, url_for
from datetime import datetime

workspace_bp = Blueprint("workspace", __name__, url_prefix="/workspace")

ORGANIZATION = "SHUNYA"
ORG_DESCRIPTION = "An operating system for human organizations."


@workspace_bp.route("/")
def workspace_home():
    """Main workspace entry point — the universal workspace.

    All authenticated users enter SHUNYA through this surface.
    The workspace renders the universal layout with dynamic
    object rendering in the center panel.
    """
    now = datetime.utcnow()
    return render_template(
        "workspace.html",
        year=now.year,
        org_name=ORGANIZATION,
        org_description=ORG_DESCRIPTION,
        current_user=_get_current_user(),
    )


@workspace_bp.route("/object/<object_id>")
def workspace_object(object_id):
    """Navigate directly to an object's Space."""
    now = datetime.utcnow()
    return render_template(
        "workspace.html",
        year=now.year,
        org_name=ORGANIZATION,
        org_description=ORG_DESCRIPTION,
        current_user=_get_current_user(),
        initial_object=object_id,
    )


def _get_current_user():
    """Get the current user from session, if available."""
    from flask import g
    user = getattr(g, "user", None)
    if user:
        return user
    # Fallback: check session
    user_id = session.get("user_id")
    if user_id:
        try:
            from app.auth import TeamMember
            from app import db
            return db.session.get(TeamMember, user_id)
        except Exception:
            pass
    return None