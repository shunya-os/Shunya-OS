"""
SHUNYA — Evidence, Provenance & Source Intelligence Models (Phase 7)
"""
from datetime import datetime
from app import db
from sqlalchemy import Index


class SourceKind:
    EXTERNAL_MESSAGE = "external_message"; CONVERSATION = "conversation"
    HUMAN_CONTEXT = "human_context"; MEMORY = "memory"
    IMPORT = "import"; MANUAL_ASSERTION = "manual_assertion"; SYSTEM_DERIVATION = "system_derivation"

class ProducerType:
    PERSON = "person"; TENANT_USER = "tenant_user"; EXTERNAL_PARTY = "external_party"
    PROVIDER = "provider"; SYSTEM = "system"; IMPORT = "import"; UNKNOWN = "unknown"

class SourceLifecycle:
    ACTIVE = "active"; STALE = "stale"; REVOKED = "revoked"
    INVALIDATED = "invalidated"; SUPERSEDED = "superseded"

class RelationType:
    SUPPORTS = "supports"; CONTRADICTS = "contradicts"; QUALIFIES = "qualifies"
    SUPERSEDES = "supersedes"; DUPLICATES = "duplicates"; DERIVED_FROM = "derived_from"; REFERENCES = "references"

class ResolutionState:
    SUPPORTED = "supported"; UNSUPPORTED = "unsupported"
    CONTRADICTED = "contradicted"; CONFLICT = "conflict"; NO_EVIDENCE = "no_evidence"

class CreationMechanism:
    EXPLICIT = "explicit"; MANUAL = "manual"; IMPORTED = "imported"
    DETERMINISTIC_DERIVED = "deterministic_derived"; SYSTEM_LINKED = "system_linked"


class SourceReference(db.Model):
    __tablename__ = "source_references"
    __table_args__ = (Index("ix_sr_tenant", "tenant_id"), Index("ix_sr_kind", "source_kind"), Index("ix_sr_object", "source_object_type", "source_object_id"))
    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.Integer, nullable=True, index=True)
    source_kind = db.Column(db.String(60), nullable=False)
    source_object_type = db.Column(db.String(60), nullable=False)
    source_object_id = db.Column(db.Integer, nullable=False)
    producer_type = db.Column(db.String(30), default="unknown")
    producer_id = db.Column(db.Integer, nullable=True)
    channel = db.Column(db.String(120), default="")
    observed_at = db.Column(db.DateTime, nullable=True)
    status = db.Column(db.String(30), nullable=False, default="active")
    content_fingerprint = db.Column(db.String(128), nullable=True)
    privacy_decision_id = db.Column(db.Integer, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class AssertionRecord(db.Model):
    __tablename__ = "assertion_records"
    __table_args__ = (Index("ix_ar_tenant", "tenant_id"), Index("ix_ar_key", "assertion_key"), Index("ix_ar_target", "target_type", "target_id"))
    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.Integer, nullable=True)
    assertion_key = db.Column(db.String(255), nullable=False, index=True)
    value = db.Column(db.Text, nullable=False)
    target_type = db.Column(db.String(60), default="")
    target_id = db.Column(db.Integer, nullable=True)
    scope_type = db.Column(db.String(30), default="person")
    scope_object_id = db.Column(db.Integer, nullable=True)
    status = db.Column(db.String(30), default="active")
    created_by = db.Column(db.String(120), default="")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class EvidenceLink(db.Model):
    __tablename__ = "evidence_links"
    __table_args__ = (Index("ix_el_tenant", "tenant_id"), Index("ix_el_target", "target_type", "target_id"), Index("ix_el_source", "source_reference_id"), Index("ix_el_relation", "relation_type"))
    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.Integer, nullable=True)
    source_reference_id = db.Column(db.Integer, nullable=False, index=True)
    target_type = db.Column(db.String(60), nullable=False)
    target_id = db.Column(db.Integer, nullable=False)
    assertion_id = db.Column(db.Integer, nullable=True)
    relation_type = db.Column(db.String(30), nullable=False, default="references")
    scope = db.Column(db.String(60), default="")
    observed_at = db.Column(db.DateTime, nullable=True)
    status = db.Column(db.String(30), default="active")
    creation_mechanism = db.Column(db.String(30), default="explicit")
    supersedes_id = db.Column(db.Integer, nullable=True)
    superseded_by_id = db.Column(db.Integer, nullable=True)
    created_by = db.Column(db.String(120), default="")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class SourceAssessment(db.Model):
    __tablename__ = "source_assessments"
    __table_args__ = (Index("ix_src_assess_source", "source_reference_id"),)
    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.Integer, nullable=True)
    source_reference_id = db.Column(db.Integer, nullable=False, index=True)
    directness = db.Column(db.String(30), default="unknown")
    origin_class = db.Column(db.String(30), default="unknown")
    recency_state = db.Column(db.String(30), default="unknown")
    corroboration_count = db.Column(db.Integer, default=0)
    contradiction_count = db.Column(db.Integer, default=0)
    producer_resolution_state = db.Column(db.String(30), default="unknown")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)