"""
SHUNYA — Human Context Models (Phase 5)
"""
from datetime import datetime
from app import db
from sqlalchemy import Index


class ContextCategory:
    PREFERENCE = "preference"
    CONSTRAINT = "constraint"
    REQUIREMENT = "requirement"
    INTENT = "intent"
    GOAL = "goal"
    AVERSION = "aversion"
    HABIT_OR_PATTERN = "habit_or_pattern"
    HOUSEHOLD_OR_TRAVEL_PARTY = "household_or_travel_party"
    COMMUNICATION_PREFERENCE = "communication_preference"
    SERVICE_PREFERENCE = "service_preference"
    BUSINESS_RELEVANT_FACT = "business_relevant_fact"
    TEMPORAL_CONTEXT = "temporal_context"
    OTHER = "other"


class ScopeType:
    PERSON_GLOBAL = "person_global"
    RELATIONSHIP = "relationship"
    LEAD_OR_OPPORTUNITY = "lead_or_opportunity"
    JOURNEY_OR_BOOKING = "journey_or_booking"
    CONVERSATION = "conversation"
    SOURCE_OBJECT = "source_object"
    TIME_WINDOW = "time_window"


class AssertionType:
    EXPLICIT = "explicit"
    DETERMINISTIC_DERIVED = "deterministic_derived"
    IMPORTED = "imported"
    MANUAL = "manual"


class ContextStatus:
    ACTIVE = "active"
    SUPERSEDED = "superseded"
    EXPIRED = "expired"
    REVOKED = "revoked"
    INVALIDATED = "invalidated"


class ProposalStatus:
    PROPOSED = "proposed"
    APPROVED = "approved"
    REJECTED = "rejected"
    COMMITTED = "committed"


class ValueType:
    STRING = "string"
    BOOLEAN = "boolean"
    NUMBER = "number"
    RANGE = "range"
    ENUM = "enum"
    DATE = "date"
    DATETIME = "datetime"
    JSON_STRUCTURED = "json_structured"


# ---------------------------------------------------------------------------
# ContextConcept — registry for canonical context keys
# ---------------------------------------------------------------------------

class ContextConcept(db.Model):
    """Registered canonical context concept with validation rules."""
    __tablename__ = "context_concepts"
    __table_args__ = (Index("ix_cc_key", "context_key"),)

    id = db.Column(db.Integer, primary_key=True)
    context_key = db.Column(db.String(255), nullable=False, unique=True)
    value_type = db.Column(db.String(30), nullable=False, default="string")
    allowed_scope_types = db.Column(db.Text, default="[]")  # JSON list
    allowed_values = db.Column(db.Text, default="[]")  # JSON enum list
    sensitivity_expectation = db.Column(db.String(30), default="internal")
    global_promotion_eligible = db.Column(db.Boolean, default=False)
    description = db.Column(db.Text, default="")
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


# ---------------------------------------------------------------------------
# HumanContextItem — canonical context assertion
# ---------------------------------------------------------------------------

class HumanContextItem(db.Model):
    """A scoped, evidenced, privacy-governed piece of business-relevant context about a human."""
    __tablename__ = "human_context_items"
    __table_args__ = (
        Index("ix_hci_person", "person_id", "status"),
        Index("ix_hci_tenant", "tenant_id"),
        Index("ix_hci_key", "context_key"),
        Index("ix_hci_scope", "scope_type", "scope_object_id"),
        Index("ix_hci_source", "source_object_type", "source_object_id"),
        Index("ix_hci_supersedes", "supersedes_id"),
        Index("ix_hci_superseded_by", "superseded_by_id"),
    )

    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.Integer, db.ForeignKey("tenants.id"), nullable=True, index=True)
    person_id = db.Column(db.Integer, db.ForeignKey("persons.id"), nullable=False, index=True)
    relationship_id = db.Column(db.Integer, db.ForeignKey("rel_relationships.id"), nullable=True)

    context_category = db.Column(db.String(60), nullable=False, default="other")
    context_key = db.Column(db.String(255), nullable=False, index=True)
    value = db.Column(db.Text, nullable=False)
    value_type = db.Column(db.String(30), default="string")
    summary = db.Column(db.String(500), default="")

    scope_type = db.Column(db.String(30), nullable=False, default="person_global")
    scope_object_type = db.Column(db.String(60), default="")
    scope_object_id = db.Column(db.Integer, nullable=True)

    valid_from = db.Column(db.DateTime, nullable=True)
    valid_until = db.Column(db.DateTime, nullable=True)
    observed_at = db.Column(db.DateTime, nullable=True)

    source_object_type = db.Column(db.String(60), default="")
    source_object_id = db.Column(db.Integer, nullable=True)

    assertion_type = db.Column(db.String(30), nullable=False, default="explicit")
    status = db.Column(db.String(30), nullable=False, default="active")

    supersedes_id = db.Column(db.Integer, nullable=True)
    superseded_by_id = db.Column(db.Integer, nullable=True)

    privacy_decision_id = db.Column(db.Integer, nullable=True)
    memory_eligibility_state = db.Column(db.String(30), default="ineligible")

    created_by = db.Column(db.String(120), default="")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    person = db.relationship("Person", backref="context_items", lazy="select")

    def __repr__(self):
        return f"<HumanContextItem #{self.id} {self.context_key}={self.value[:30]} [{self.status}]>"


# ---------------------------------------------------------------------------
# ContextProposal — proposal state before commit
# ---------------------------------------------------------------------------

class ContextProposal(db.Model):
    """Proposed context awaiting approval or rejection."""
    __tablename__ = "context_proposals"
    __table_args__ = (
        Index("ix_cp_tenant", "tenant_id"),
        Index("ix_cp_person", "person_id"),
    )

    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.Integer, db.ForeignKey("tenants.id"), nullable=True)
    person_id = db.Column(db.Integer, db.ForeignKey("persons.id"), nullable=False, index=True)
    relationship_id = db.Column(db.Integer, db.ForeignKey("rel_relationships.id"), nullable=True)

    context_category = db.Column(db.String(60), nullable=False, default="other")
    context_key = db.Column(db.String(255), nullable=False)
    value = db.Column(db.Text, nullable=False)
    value_type = db.Column(db.String(30), default="string")
    summary = db.Column(db.String(500), default="")

    scope_type = db.Column(db.String(30), nullable=False, default="person_global")
    source_object_type = db.Column(db.String(60), default="")
    source_object_id = db.Column(db.Integer, nullable=True)
    assertion_type = db.Column(db.String(30), nullable=False, default="explicit")

    status = db.Column(db.String(30), nullable=False, default="proposed")
    approved_by = db.Column(db.String(120), default="")
    approved_at = db.Column(db.DateTime, nullable=True)
    policy_version_at_approval = db.Column(db.Integer, default=1)

    created_by = db.Column(db.String(120), default="")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<ContextProposal #{self.id} {self.context_key} [{self.status}]>"