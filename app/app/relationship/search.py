"""FOR-2C.1: Universal Search — relationship-centric search across all domains."""

from flask import jsonify, request, session
from app import db
from . import relationship_bp
from .models import (
    CanonicalRelationship as Relationship,
    TimelineEntry, RelationshipMemory, RelationshipDocument,
)
from app.models import Proposal, Organization


@relationship_bp.route("/api/v1/relationships/search", methods=["GET"])
def api_universal_search():
    """Universal Search — returns complete business context for a relationship.

    Searches across display_name, email, phone, company_name, tags.
    Returns profile, timeline, proposals, documents, knowledge, tasks, AI memory.
    """
    uid = session.get("identity_id") or session.get("user_id") or ""
    if not uid:
        return jsonify({"error": "Authentication required"}), 401
    org_id = session.get("current_org_id")
    if not org_id:
        org = Organization.query.filter_by(slug="panchi-club").first()
        if org:
            org_id = org.id
        else:
            return jsonify({"error": "No organization selected"}), 400

    query = request.args.get("q", "").strip()
    if not query:
        return jsonify({"error": "Search query required"}), 400

    like = f"%{query}%"

    rels = Relationship.query.filter(
        Relationship.organization_id == org_id,
        Relationship.status != "archived",
        db.or_(
            Relationship.display_name.ilike(like),
            Relationship.email.ilike(like),
            Relationship.phone.ilike(like),
            Relationship.company_name.ilike(like),
            Relationship.tags.ilike(like),
            Relationship.legal_name.ilike(like),
        )
    ).limit(20).all()

    results = []
    for rel in rels:
        timeline = TimelineEntry.query.filter_by(
            relationship_id=rel.id, organization_id=org_id
        ).order_by(TimelineEntry.event_time.desc()).limit(5).all()

        proposals = Proposal.query.filter_by(
            relationship_id=rel.id
        ).filter(
            Proposal.organization_id == org_id
        ).order_by(Proposal.created_at.desc()).limit(5).all()

        docs = RelationshipDocument.query.filter_by(
            relationship_id=rel.id, organization_id=org_id
        ).order_by(RelationshipDocument.created_at.desc()).limit(5).all()

        memory = RelationshipMemory.query.filter_by(
            relationship_id=rel.id, organization_id=org_id
        ).first()

        results.append({
            "relationship": rel.to_dict(),
            "timeline": [e.to_dict() for e in timeline],
            "timeline_count": TimelineEntry.query.filter_by(relationship_id=rel.id).count(),
            "proposals": [{
                "id": p.id, "title": p.title, "status": p.status,
                "budget": float(p.budget or 0),
                "created_at": p.created_at.isoformat() if p.created_at else None,
            } for p in proposals],
            "proposal_count": Proposal.query.filter_by(relationship_id=rel.id).filter(
                Proposal.organization_id == org_id
            ).count(),
            "documents": [d.to_dict() for d in docs],
            "document_count": RelationshipDocument.query.filter_by(relationship_id=rel.id).count(),
            "ai_memory": memory.to_dict() if memory else None,
        })

    return jsonify({
        "results": results,
        "count": len(results),
        "query": query,
    })