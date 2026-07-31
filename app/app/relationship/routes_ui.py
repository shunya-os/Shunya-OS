"""FOR-2C Relationship Intelligence Operating System — UI Routes."""

from flask import render_template, session, redirect, url_for
from app import db
from . import relationship_bp
from .models import (
    CanonicalRelationship as Relationship,
    RelationshipMemory, TimelineEntry, RelationshipDocument,
)
from app.relationship.services import get_categories, seed_default_categories, get_timeline


def _identity():
    return session.get("identity_id") or session.get("user_id") or ""


def _org():
    return session.get("current_org_id")


@relationship_bp.route("/")
def relationship_list():
    """List all relationships in the current organization."""
    uid = _identity()
    if not uid:
        return redirect(url_for("for2.for2_login"))
    org_id = _org()
    if not org_id:
        return redirect(url_for("for2.for2_home"))

    rels = Relationship.query.filter_by(organization_id=org_id, status="active").order_by(
        Relationship.updated_at.desc()
    ).limit(100).all()

    cats = get_categories(org_id) if org_id else []

    return render_template(
        "relationship_list.html",
        relationships=[r.to_dict() for r in rels],
        categories=cats,
    )


@relationship_bp.route("/<int:rel_id>")
def relationship_workspace(rel_id):
    """Unified Relationship Workspace."""
    uid = _identity()
    if not uid:
        return redirect(url_for("for2.for2_login"))
    rel = db.session.get(Relationship, rel_id)
    if not rel:
        return "Relationship not found", 404
    if rel.organization_id != _org():
        return "Access denied", 403

    timeline, timeline_total = get_timeline(rel_id, limit=50)
    memory = RelationshipMemory.query.filter_by(relationship_id=rel_id).first()
    docs = RelationshipDocument.query.filter_by(relationship_id=rel_id).order_by(
        RelationshipDocument.created_at.desc()
    ).all()

    return render_template(
        "relationship_workspace.html",
        relationship=rel.to_dict(),
        ai_memory=memory.to_dict() if memory else None,
        timeline=[e.to_dict() for e in timeline],
        timeline_total=timeline_total,
        documents=[d.to_dict() for d in docs],
    )