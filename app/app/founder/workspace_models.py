"""SHUNYA M4 — Intelligent Workspace Persistence Models.

Every workspace intelligence artifact is persisted:
- WorkspaceEvent: activity timeline entries (deterministic, from state)
- NextAction: suggested actions derived from runtime state
- MissingContext: identified gaps in business understanding
- WorkspaceHealthSnapshot: point-in-time reproducible health assessment
- EvidenceExplorerEntry: traceable provenance for workspace statements
"""
from datetime import datetime, timezone

from app import db
from sqlalchemy import Index, Text


# ---------------------------------------------------------------------------
# WorkspaceEvent — Activity Timeline
# ---------------------------------------------------------------------------

class WorkspaceEvent(db.Model):
    """A single timeline entry in an object's workspace.

    Every event is deterministic and persisted. Entries derive from
    real runtime state — creation, updates, conversations, evidence,
    intelligence events, commitment changes.
    """

    __tablename__ = "wksp_events"
    __table_args__ = (
        Index("ix_wksp_events_object", "object_id", "created_at"),
        Index("ix_wksp_events_type", "object_id", "event_type"),
    )

    id = db.Column(db.Integer, primary_key=True)
    object_id = db.Column(db.String(64), nullable=False, index=True)
    event_type = db.Column(db.String(40), nullable=False)
    # Types: created, updated, conversation, commitment, evidence, intelligence,
    #        relationship_added, status_changed, next_action_completed
    title = db.Column(db.String(255), nullable=False)
    detail = db.Column(Text, default="")
    provenance = db.Column(Text, default="")
    # JSON: {"source": "object_creation", "object_id": "...", "field": "..."}
    importance = db.Column(db.String(20), default="normal")
    # normal, high, system
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "object_id": self.object_id,
            "event_type": self.event_type,
            "title": self.title,
            "detail": self.detail,
            "provenance": self.provenance,
            "importance": self.importance,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


# ---------------------------------------------------------------------------
# NextAction — Deterministic Suggested Actions
# ---------------------------------------------------------------------------

class NextAction(db.Model):
    """A deterministic next action derived from runtime state.

    Each action includes explanation, supporting evidence, priority,
    and originating runtime. No placeholder recommendations.
    """

    __tablename__ = "wksp_next_actions"
    __table_args__ = (
        Index("ix_wksp_next_action_object", "object_id", "status"),
        Index("ix_wksp_next_action_priority", "object_id", "priority"),
    )

    id = db.Column(db.Integer, primary_key=True)
    object_id = db.Column(db.String(64), nullable=False, index=True)
    action_type = db.Column(db.String(40), nullable=False)
    # Types: start_conversation, add_relationship, update_status,
    #        add_notes, review_object, add_evidence
    label = db.Column(db.String(255), nullable=False)
    explanation = db.Column(Text, default="")
    supporting_evidence = db.Column(Text, default="")  # JSON with evidence links
    priority = db.Column(db.String(20), default="medium")
    # low, medium, high, urgent
    priority_score = db.Column(db.Float, default=0.0)
    originating_runtime = db.Column(db.String(60), default="workspace_intelligence")
    status = db.Column(db.String(20), default="pending")
    # pending, completed, dismissed
    completed_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "object_id": self.object_id,
            "action_type": self.action_type,
            "label": self.label,
            "explanation": self.explanation,
            "supporting_evidence": self.supporting_evidence,
            "priority": self.priority,
            "priority_score": self.priority_score,
            "originating_runtime": self.originating_runtime,
            "status": self.status,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


# ---------------------------------------------------------------------------
# MissingContext — Identified Business Understanding Gaps
# ---------------------------------------------------------------------------

class MissingContext(db.Model):
    """An identified gap in SHUNYA's understanding of an object.

    Missing context is presented as opportunities to improve business
    understanding. No fabricated gaps — only real absences from persisted state.
    """

    __tablename__ = "wksp_missing_context"
    __table_args__ = (
        Index("ix_wksp_missing_object", "object_id", "status"),
    )

    id = db.Column(db.Integer, primary_key=True)
    object_id = db.Column(db.String(64), nullable=False, index=True)
    context_type = db.Column(db.String(40), nullable=False)
    # Types: missing_contact, missing_owner, missing_notes, missing_follow_up,
    #        missing_relationship, incomplete_document, missing_description,
    #        missing_conversation, missing_evidence
    label = db.Column(db.String(255), nullable=False)
    detail = db.Column(Text, default="")
    severity = db.Column(db.String(20), default="info")
    # info, suggestion, recommendation
    status = db.Column(db.String(20), default="open")
    # open, addressed, dismissed
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "object_id": self.object_id,
            "context_type": self.context_type,
            "label": self.label,
            "detail": self.detail,
            "severity": self.severity,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


# ---------------------------------------------------------------------------
# WorkspaceHealthSnapshot — Deterministic Health Assessment
# ---------------------------------------------------------------------------

class WorkspaceHealthSnapshot(db.Model):
    """A point-in-time deterministic health assessment for an object.

    Health is computed from: completeness, activity, relationships,
    commitments, conversations, unresolved issues. Must be explainable
    and reproducible. Persisted so the result can be traced and compared.
    """

    __tablename__ = "wksp_health_snapshots"
    __table_args__ = (
        Index("ix_wksp_health_object", "object_id", "recorded_at"),
    )

    id = db.Column(db.Integer, primary_key=True)
    object_id = db.Column(db.String(64), nullable=False, index=True)
    overall_score = db.Column(db.Float, nullable=False, default=0.0)
    completeness_score = db.Column(db.Float, default=0.0)
    activity_score = db.Column(db.Float, default=0.0)
    relationship_score = db.Column(db.Float, default=0.0)
    conversation_score = db.Column(db.Float, default=0.0)
    commitment_score = db.Column(db.Float, default=0.0)
    description = db.Column(Text, default="")
    breakdown = db.Column(Text, default="")  # JSON with per-dimension details
    recorded_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "object_id": self.object_id,
            "overall_score": self.overall_score,
            "completeness_score": self.completeness_score,
            "activity_score": self.activity_score,
            "relationship_score": self.relationship_score,
            "conversation_score": self.conversation_score,
            "commitment_score": self.commitment_score,
            "description": self.description,
            "breakdown": self.breakdown,
            "recorded_at": self.recorded_at.isoformat() if self.recorded_at else None,
        }


# ---------------------------------------------------------------------------
# WorkspaceNavigation — Context-Preserving Navigation History
# ---------------------------------------------------------------------------

class WorkspaceNavigation(db.Model):
    """Tracks navigation between related objects to preserve context.

    Each navigation entry records source, target, and the relationship
    that connected them. Enables breadcrumb trails and context restoration.
    """

    __tablename__ = "wksp_navigation"
    __table_args__ = (
        Index("ix_wksp_nav_identity", "identity_id", "created_at"),
    )

    id = db.Column(db.Integer, primary_key=True)
    identity_id = db.Column(db.String(64), nullable=False, index=True)
    source_object_id = db.Column(db.String(64), nullable=False)
    target_object_id = db.Column(db.String(64), nullable=False)
    relationship_type = db.Column(db.String(40), default="related")
    # same_space, direct_relationship, via_conversation, searched
    context_label = db.Column(db.String(255), default="")
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "identity_id": self.identity_id,
            "source_object_id": self.source_object_id,
            "target_object_id": self.target_object_id,
            "relationship_type": self.relationship_type,
            "context_label": self.context_label,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }