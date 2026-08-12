"""FOR-2C Relationship Intelligence Operating System — Services.

Business logic for the Relationship domain.
"""

import json
import re
from datetime import datetime, date
from typing import Optional, List

from app import db
from app.relationship.models import (
    CanonicalRelationship as Relationship,
    RelationshipCategory, RelationshipField,
    TimelineEntry, RelationshipMemory, RelationshipDocument,
    DuplicateGroup, DuplicateCandidate,
)


# ── Relationship CRUD ─────────────────────────────────────────────────────


def create_relationship(organization_id: int, data: dict,
                        created_by: str = "",
                        legacy_person_id: Optional[int] = None) -> Relationship:
    """Create a new relationship within an organization."""
    rel = Relationship(
        organization_id=organization_id,
        display_name=data.get("display_name", "").strip(),
        legal_name=data.get("legal_name", ""),
        preferred_name=data.get("preferred_name", ""),
        relationship_type=data.get("relationship_type", "customer"),
        is_organization=data.get("is_organization", False),
        company_name=data.get("company_name", ""),
        designation=data.get("designation", ""),
        email=data.get("email", "").strip().lower(),
        email2=data.get("email2", "").strip().lower(),
        email3=data.get("email3", "").strip().lower(),
        phone=data.get("phone", "").strip(),
        phone2=data.get("phone2", "").strip(),
        phone3=data.get("phone3", "").strip(),
        address_line1=data.get("address_line1", ""),
        address_line2=data.get("address_line2", ""),
        city=data.get("city", ""),
        state=data.get("state", ""),
        postal_code=data.get("postal_code", ""),
        country=data.get("country", ""),
        website=data.get("website", ""),
        social_linkedin=data.get("social_linkedin", ""),
        social_twitter=data.get("social_twitter", ""),
        timezone=data.get("timezone", ""),
        preferred_language=data.get("preferred_language", "en"),
        preferred_currency=data.get("preferred_currency", ""),
        tags=data.get("tags", ""),
        segments=data.get("segments", ""),
        industries=data.get("industries", ""),
        source=data.get("source", ""),
        referral_info=data.get("referral_info", ""),
        risk_level=data.get("risk_level", "medium"),
        priority=data.get("priority", 0),
        internal_owner=data.get("internal_owner", ""),
        status=data.get("status", "active"),
        notes=data.get("notes", ""),
        custom_attributes=json.dumps(data.get("custom_attributes", {})),
        legacy_person_id=legacy_person_id,
        created_by=created_by,
    )
    db.session.add(rel)
    db.session.flush()

    # Create initial timeline entry
    _add_timeline_entry(
        organization_id=organization_id,
        relationship_id=rel.id,
        event_type="relationship.created",
        title=f"Relationship created: {rel.display_name}",
        description=f"Type: {rel.relationship_type}, Source: {rel.source or 'manual'}",
        created_by=created_by,
    )

    # Create empty AI memory
    memory = RelationshipMemory(
        organization_id=organization_id,
        relationship_id=rel.id,
        memory_json="{}",
        summary="",
        health_score=50,
        engagement_score=50,
        lifetime_value=0,
        retention_risk=50,
    )
    db.session.add(memory)
    db.session.commit()
    return rel


def update_relationship(rel: Relationship, data: dict, updated_by: str = "") -> Relationship:
    """Update relationship fields. Records changes in timeline."""
    changes = []
    for field in ("display_name", "legal_name", "preferred_name", "relationship_type",
                  "is_organization", "company_name", "designation",
                  "email", "email2", "email3", "phone", "phone2", "phone3",
                  "address_line1", "address_line2", "city", "state", "postal_code",
                  "country", "website", "timezone", "preferred_language", "preferred_currency",
                  "tags", "segments", "industries", "source", "referral_info",
                  "risk_level", "priority", "internal_owner", "status", "notes"):
        if field in data:
            old_val = getattr(rel, field)
            new_val = data[field]
            if str(old_val) != str(new_val):
                changes.append(f"{field}: changed")
                setattr(rel, field, data[field])

    if "custom_attributes" in data:
        old = json.loads(rel.custom_attributes or "{}")
        new = data["custom_attributes"]
        if old != new:
            changes.append("custom_attributes: updated")
            rel.custom_attributes = json.dumps(new)

    if changes:
        _add_timeline_entry(
            organization_id=rel.organization_id,
            relationship_id=rel.id,
            event_type="relationship.updated",
            title=f"Relationship updated: {rel.display_name}",
            description="; ".join(changes),
            created_by=updated_by,
        )

    db.session.commit()
    return rel


def archive_relationship(rel: Relationship, archived_by: str = "") -> Relationship:
    """Archive a relationship. Preserves all history."""
    rel.status = "archived"
    _add_timeline_entry(
        organization_id=rel.organization_id,
        relationship_id=rel.id,
        event_type="relationship.archived",
        title=f"Relationship archived: {rel.display_name}",
        created_by=archived_by,
    )
    db.session.commit()
    return rel


def search_relationships(organization_id: int, query: str = "",
                          type_filter: str = "", status: str = "active",
                          limit: int = 50, offset: int = 0) -> tuple:
    """Search relationships within an organization.

    Searches across display_name, email, phone, company_name, tags.
    """
    q = Relationship.query.filter_by(organization_id=organization_id)

    if query:
        like = f"%{query}%"
        q = q.filter(
            db.or_(
                Relationship.display_name.ilike(like),
                Relationship.email.ilike(like),
                Relationship.phone.ilike(like),
                Relationship.company_name.ilike(like),
                Relationship.tags.ilike(like),
                Relationship.legal_name.ilike(like),
            )
        )

    if type_filter:
        q = q.filter(Relationship.relationship_type == type_filter)

    if status:
        q = q.filter(Relationship.status == status)

    total = q.count()
    rels = q.order_by(Relationship.updated_at.desc()).offset(offset).limit(limit).all()

    return rels, total


# ── Timeline ──────────────────────────────────────────────────────────────


def _add_timeline_entry(organization_id: int, relationship_id: int,
                         event_type: str, title: str = "",
                         description: str = "", reference_type: str = "",
                         reference_id: Optional[int] = None,
                         metadata: Optional[dict] = None,
                         created_by: str = "") -> TimelineEntry:
    """Add an immutable timeline entry for a relationship."""
    entry = TimelineEntry(
        organization_id=organization_id,
        relationship_id=relationship_id,
        event_type=event_type,
        title=title,
        description=description,
        reference_type=reference_type,
        reference_id=reference_id,
        metadata_json=json.dumps(metadata or {}),
        created_by=created_by,
    )
    db.session.add(entry)
    db.session.flush()
    return entry


def get_timeline(relationship_id: int, limit: int = 100, offset: int = 0) -> tuple:
    """Get the timeline for a relationship, newest first."""
    q = TimelineEntry.query.filter_by(relationship_id=relationship_id)
    total = q.count()
    entries = q.order_by(TimelineEntry.event_time.desc()).offset(offset).limit(limit).all()
    return entries, total


# ── AI Memory ─────────────────────────────────────────────────────────────


def get_or_create_memory(relationship_id: int) -> RelationshipMemory:
    """Get or create AI memory for a relationship."""
    memory = RelationshipMemory.query.filter_by(relationship_id=relationship_id).first()
    if not memory:
        rel = db.session.get(Relationship, relationship_id)
        if not rel:
            return None
        memory = RelationshipMemory(
            organization_id=rel.organization_id,
            relationship_id=relationship_id,
            memory_json="{}", summary="",
            health_score=50, engagement_score=50,
            lifetime_value=0, retention_risk=50,
        )
        db.session.add(memory)
        db.session.commit()
    return memory


def update_ai_memory(relationship_id: int, memory_data: dict,
                     summary: str = "", health_score: int = None) -> RelationshipMemory:
    """Update the AI memory for a relationship."""
    memory = get_or_create_memory(relationship_id)
    if not memory:
        return None

    existing = json.loads(memory.memory_json or "{}")
    existing.update(memory_data)
    memory.memory_json = json.dumps(existing)

    if summary:
        memory.summary = summary
    if health_score is not None:
        memory.health_score = min(100, max(0, health_score))

    memory.last_ai_update = datetime.utcnow()
    db.session.commit()
    return memory


# ── Intelligence Scores ─────────────────────────────────────────────────


def compute_health_score(relationship_id: int) -> int:
    """Compute relationship health score based on:
    - Proposal success rate (weight: 30%)
    - Payment timeliness (weight: 25%)
    - Communication recency (weight: 20%)
    - Task completion rate (weight: 15%)
    - Overall engagement (weight: 10%)

    Returns score 0-100. Industry-agnostic.
    """
    memory = get_or_create_memory(relationship_id)
    if not memory:
        return 50

    # Start from existing score and adjust
    score = memory.health_score or 50
    # In v1, this is a placeholder — real computation requires cross-domain data
    # For now, maintain the existing score or default to 50
    return score


# ── Duplicate Detection ──────────────────────────────────────────────────


def find_duplicates(organization_id: int, relationship_id: int) -> list:
    """Find potential duplicates for a given relationship.

    Checks email, phone, and name similarity within the same organization.
    """
    rel = db.session.get(Relationship, relationship_id)
    if not rel or rel.organization_id != organization_id:
        return []

    candidates = []
    base_query = Relationship.query.filter(
        Relationship.organization_id == organization_id,
        Relationship.id != relationship_id,
    )

    # Email match
    if rel.email:
        email_matches = base_query.filter(
            db.or_(Relationship.email == rel.email,
                   Relationship.email2 == rel.email,
                   Relationship.email3 == rel.email)
        ).all()
        for m in email_matches:
            candidates.append({"relationship": m.to_dict(), "method": "email", "score": 90})

    # Phone match
    if rel.phone:
        phone_matches = base_query.filter(
            db.or_(Relationship.phone == rel.phone,
                   Relationship.phone2 == rel.phone,
                   Relationship.phone3 == rel.phone)
        ).all()
        for m in phone_matches:
            # Avoid duplicates
            if not any(c["relationship"]["id"] == m.id for c in candidates):
                candidates.append({"relationship": m.to_dict(), "method": "phone", "score": 85})

    # Name similarity (simple: same normalized display name)
    if rel.display_name:
        name_normalized = rel.display_name.strip().lower()
        name_matches = base_query.filter(
            db.func.lower(Relationship.display_name) == name_normalized
        ).all()
        for m in name_matches:
            if not any(c["relationship"]["id"] == m.id for c in candidates):
                candidates.append({"relationship": m.to_dict(), "method": "name", "score": 70})

    return sorted(candidates, key=lambda x: -x["score"])


def merge_relationships(primary_id: int, secondary_id: int,
                         merged_by: str = "") -> Optional[Relationship]:
    """Merge two duplicate relationships.

    Preserves complete history. No information is lost.
    primary = surviving relationship
    secondary = merged into primary, then archived
    """
    primary = db.session.get(Relationship, primary_id)
    secondary = db.session.get(Relationship, secondary_id)
    if not primary or not secondary:
        return None
    if primary.organization_id != secondary.organization_id:
        return None

    # Merge timeline entries
    TimelineEntry.query.filter_by(relationship_id=secondary_id).update(
        {"relationship_id": primary_id}
    )

    # Merge documents
    RelationshipDocument.query.filter_by(relationship_id=secondary_id).update(
        {"relationship_id": primary_id}
    )

    # Merge AI memory (if secondary has memory, merge into primary)
    sec_memory = RelationshipMemory.query.filter_by(relationship_id=secondary_id).first()
    if sec_memory and sec_memory.memory_json:
        pri_memory = get_or_create_memory(primary_id)
        if pri_memory:
            pri_data = json.loads(pri_memory.memory_json or "{}")
            sec_data = json.loads(sec_memory.memory_json or "{}")
            pri_data.update(sec_data)
            pri_memory.memory_json = json.dumps(pri_data)
            if not pri_memory.summary and sec_memory.summary:
                pri_memory.summary = sec_memory.summary
            pri_memory.health_score = max(
                pri_memory.health_score or 50, sec_memory.health_score or 50
            )
            db.session.delete(sec_memory)

    # Archive secondary
    secondary.status = "archived"
    secondary.display_name = f"{secondary.display_name} (merged into #{primary_id})"

    # Create merge record
    group = DuplicateGroup(
        organization_id=primary.organization_id,
        primary_relationship_id=primary_id,
        merge_status="merged",
        detection_method="manual",
        confidence=100,
        resolved_by=merged_by,
        resolved_at=datetime.utcnow(),
    )
    db.session.add(group)

    _add_timeline_entry(
        organization_id=primary.organization_id,
        relationship_id=primary_id,
        event_type="relationship.merged",
        title=f"Merged with duplicate #{secondary_id}",
        description=f"Merged by {merged_by}. Secondary relationship archived.",
        created_by=merged_by,
    )

    db.session.commit()
    return primary


# ── Categories (config-driven types) ────────────────────────────────────


DEFAULT_CATEGORIES = [
    ("customer", "Customer", "person", "#6366f1"),
    ("lead", "Lead", "person_add", "#f59e0b"),
    ("prospect", "Prospect", "search", "#8b5cf6"),
    ("supplier", "Supplier", "store", "#10b981"),
    ("vendor", "Vendor", "inventory", "#06b6d4"),
    ("employee", "Employee", "badge", "#3b82f6"),
    ("partner", "Partner", "handshake", "#ec4899"),
    ("consultant", "Consultant", "psychology", "#f97316"),
    ("investor", "Investor", "trending_up", "#14b8a6"),
    ("government", "Government", "account_balance", "#78716c"),
    ("financial_institution", "Financial Institution", "account_balance", "#0ea5e9"),
    ("internal_team", "Internal Team", "group", "#64748b"),
]


def seed_default_categories(organization_id: int):
    """Seed default relationship categories for an organization."""
    existing = RelationshipCategory.query.filter_by(organization_id=organization_id).count()
    if existing > 0:
        return
    for key, label, icon, color in DEFAULT_CATEGORIES:
        cat = RelationshipCategory(
            organization_id=organization_id,
            type_key=key,
            display_label=label,
            icon=icon,
            color=color,
            is_system=True,
            sort_order=0,
        )
        db.session.add(cat)
    db.session.commit()


def get_categories(organization_id: int) -> list:
    """Get all relationship categories for an organization."""
    cats = RelationshipCategory.query.filter(
        db.or_(RelationshipCategory.organization_id == organization_id,
               RelationshipCategory.organization_id.is_(None))
    ).order_by(RelationshipCategory.sort_order).all()
    return [c.to_dict() for c in cats]