"""
SHUNYA — Memory Architecture Models (Phase 6)
"""
from datetime import datetime
from app import db
from sqlalchemy import Index


class MemoryType:
    FACT = "fact"
    PREFERENCE = "preference"
    CONSTRAINT = "constraint"
    REQUIREMENT = "requirement"
    INTENT = "intent"
    GOAL = "goal"
    DECISION = "decision"
    COMMITMENT = "commitment"
    OUTCOME = "outcome"
    PROCEDURAL = "procedural"
    TEMPORAL = "temporal"
    RELATIONSHIP_CONTEXT = "relationship_context"
    BUSINESS_CONTEXT = "business_context"
    OTHER = "other"


class TruthClassification:
    """FDA3: Distinguish FACT / OBSERVATION / INFERENCE / MEMORY / DECISION.

    Memory must NEVER silently promote:
    INFERENCE → FACT
    MEMORY → FACT
    DECISION → OUTCOME
    INTENTION → OUTCOME
    """
    FACT = "fact"                     # Directly supported by authoritative evidence
    OBSERVATION = "observation"       # Something SHUNYA observed
    INFERENCE = "inference"           # Something SHUNYA derived
    MEMORY = "memory"                 # Persisted contextual information
    DECISION = "decision"             # Produced by the reasoning system
    OUTCOME = "outcome"              # What actually happened
    EVIDENCE = "evidence"            # Proof of what happened
    INTENTION = "intention"          # Stated intent (not yet outcome)


class MemoryScope:
    PERSON = "person"
    RELATIONSHIP = "relationship"
    TENANT = "tenant"
    CONVERSATION = "conversation"
    SOURCE_OBJECT = "source_object"
    TIME_WINDOW = "time_window"


class MemoryCreationMechanism:
    EXPLICIT = "explicit"
    MANUAL = "manual"
    IMPORTED = "imported"
    DETERMINISTIC_DERIVED = "deterministic_derived"
    CONTEXT_PROMOTED = "context_promoted"


class MemoryStatus:
    """FDA3 memory lifecycle states.

    Explicit lifecycle: candidate → confirmed → active → superseded/invalidated/expired/archived.
    Memory must NOT silently overwrite consequential history.
    """
    CANDIDATE = "candidate"
    CONFIRMED = "confirmed"
    ACTIVE = "active"
    SUPERSEDED = "superseded"
    INVALIDATED = "invalidated"
    EXPIRED = "expired"
    ARCHIVED = "archived"
    REVOKED = "revoked"
    CONSOLIDATED = "consolidated"


class CandidateStatus:
    PROPOSED = "proposed"
    APPROVED = "approved"
    REJECTED = "rejected"
    COMMITTED = "committed"
    STALE = "stale"
    INVALIDATED = "invalidated"


class ValueType:
    STRING = "string"
    BOOLEAN = "boolean"
    NUMBER = "number"
    RANGE = "range"
    ENUM = "enum"
    DATE = "date"
    DATETIME = "datetime"
    DURATION = "duration"
    JSON_STRUCTURED = "json_structured"


# ---------------------------------------------------------------------------
# MemoryConcept
# ---------------------------------------------------------------------------

class MemoryConcept(db.Model):
    __tablename__ = "memory_concepts"
    __table_args__ = (Index("ix_mc_key", "memory_key"),)
    id = db.Column(db.Integer, primary_key=True)
    memory_key = db.Column(db.String(255), nullable=False, unique=True)
    memory_type = db.Column(db.String(60), nullable=False, default="other")
    value_type = db.Column(db.String(30), nullable=False, default="string")
    allowed_scopes = db.Column(db.Text, default="[]")
    sensitivity_expectation = db.Column(db.String(30), default="internal")
    context_promotion_eligible = db.Column(db.Boolean, default=False)
    global_promotion_eligible = db.Column(db.Boolean, default=False)
    description = db.Column(db.Text, default="")
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


# ---------------------------------------------------------------------------
# MemoryCandidate
# ---------------------------------------------------------------------------

class MemoryCandidate(db.Model):
    __tablename__ = "memory_candidates"
    __table_args__ = (
        Index("ix_mcand_tenant", "tenant_id"),
        Index("ix_mcand_person", "person_id"),
    )
    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.Integer, db.ForeignKey("tenants.id"), nullable=True)
    person_id = db.Column(db.Integer, db.ForeignKey("persons.id"), nullable=True, index=True)
    relationship_id = db.Column(db.Integer, db.ForeignKey("rel_relationships.id"), nullable=True)
    memory_type = db.Column(db.String(60), nullable=False, default="other")
    memory_key = db.Column(db.String(255), nullable=False)
    value = db.Column(db.Text, nullable=False)
    value_type = db.Column(db.String(30), default="string")
    scope_type = db.Column(db.String(30), nullable=False, default="person")
    scope_object_type = db.Column(db.String(60), default="")
    scope_object_id = db.Column(db.Integer, nullable=True)
    source_object_type = db.Column(db.String(60), default="")
    source_object_id = db.Column(db.Integer, nullable=True)
    human_context_item_id = db.Column(db.Integer, nullable=True)
    creation_mechanism = db.Column(db.String(30), nullable=False, default="explicit")
    truth_classification = db.Column(db.String(20), nullable=False, default="memory")
    status = db.Column(db.String(30), nullable=False, default="proposed")
    approved_by = db.Column(db.String(120), default="")
    approved_at = db.Column(db.DateTime, nullable=True)
    policy_version_at_approval = db.Column(db.Integer, default=1)
    created_by = db.Column(db.String(120), default="")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# ---------------------------------------------------------------------------
# MemoryRecord
# ---------------------------------------------------------------------------

class MemoryRecord(db.Model):
    __tablename__ = "memory_records"
    __table_args__ = (
        Index("ix_mr_tenant", "tenant_id"),
        Index("ix_mr_person", "person_id", "status"),
        Index("ix_mr_key", "memory_key"),
        Index("ix_mr_scope", "scope_type", "scope_object_id"),
        Index("ix_mr_type", "memory_type"),
    )
    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.Integer, db.ForeignKey("tenants.id"), nullable=True, index=True)
    person_id = db.Column(db.Integer, db.ForeignKey("persons.id"), nullable=True, index=True)
    relationship_id = db.Column(db.Integer, db.ForeignKey("rel_relationships.id"), nullable=True)
    memory_type = db.Column(db.String(60), nullable=False, default="other", index=True)
    memory_key = db.Column(db.String(255), nullable=False, index=True)
    value = db.Column(db.Text, nullable=False)
    value_type = db.Column(db.String(30), default="string")
    summary = db.Column(db.String(500), default="")
    scope_type = db.Column(db.String(30), nullable=False, default="person")
    scope_object_type = db.Column(db.String(60), default="")
    scope_object_id = db.Column(db.Integer, nullable=True)
    valid_from = db.Column(db.DateTime, nullable=True)
    valid_until = db.Column(db.DateTime, nullable=True)
    effective_from = db.Column(db.DateTime, nullable=True)
    effective_until = db.Column(db.DateTime, nullable=True)
    observed_at = db.Column(db.DateTime, nullable=True)
    source_object_type = db.Column(db.String(60), default="")
    source_object_id = db.Column(db.Integer, nullable=True)
    human_context_item_id = db.Column(db.Integer, nullable=True)
    creation_mechanism = db.Column(db.String(30), nullable=False, default="explicit")
    truth_classification = db.Column(db.String(20), nullable=False, default="memory")
    status = db.Column(db.String(30), nullable=False, default="active")
    supersedes_id = db.Column(db.Integer, nullable=True)
    superseded_by_id = db.Column(db.Integer, nullable=True)
    resolution_type = db.Column(db.String(30), nullable=True)
    resolution_reason = db.Column(db.Text, nullable=True)
    injection_checked = db.Column(db.Boolean, default=False)
    privacy_decision_id = db.Column(db.Integer, nullable=True)
    memory_eligibility_state = db.Column(db.String(30), default="ineligible")
    policy_version = db.Column(db.Integer, default=1)
    created_by = db.Column(db.String(120), default="")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# ---------------------------------------------------------------------------
# MemoryProvenance
# ---------------------------------------------------------------------------

class MemoryProvenance(db.Model):
    __tablename__ = "memory_provenances"
    __table_args__ = (
        Index("ix_mp_memory", "memory_id"),
        Index("ix_mp_source", "source_object_type", "source_object_id"),
        db.UniqueConstraint("provenance_source", "provenance_source_id",
                            name="uq_mp_source_idempotency"),
    )
    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.Integer, db.ForeignKey("tenants.id"), nullable=True)
    memory_id = db.Column(db.Integer, db.ForeignKey("memory_records.id"), nullable=False, index=True)
    source_object_type = db.Column(db.String(60), nullable=False)
    source_object_id = db.Column(db.Integer, nullable=False)
    provenance_source = db.Column(db.String(255), nullable=True)
    provenance_source_id = db.Column(db.String(255), nullable=True)
    provenance_role = db.Column(db.String(30), default="source")
    observed_at = db.Column(db.DateTime, nullable=True)
    creation_mechanism = db.Column(db.String(30), default="explicit")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)