"""
SHUNYA — Privacy, Sensitivity & Memory Eligibility Models (Phase 4)
"""
from datetime import datetime
from app import db
from sqlalchemy import Index


# ---------------------------------------------------------------------------
# Sensitivity Levels & Reasons
# ---------------------------------------------------------------------------

class SensitivityLevel:
    PUBLIC = "public"
    INTERNAL = "internal"
    CONFIDENTIAL = "confidential"
    RESTRICTED = "restricted"
    HIGHLY_SENSITIVE = "highly_sensitive"


SYSTEM_NON_OVERRIDABLE_REASONS = [
    "authentication_secret", "password", "access_token", "refresh_token",
    "api_secret", "session_secret", "private_key", "payment_card_security_code",
    "payment_card_data", "government_identifier",
    "health_information", "sexual_or_intimate_information",
    "religious_information", "race_or_ethnicity_information",
    "political_affiliation_or_belief", "trade_union_information",
    "criminal_history", "biometric_information", "child_or_minor_information",
]


class MemoryEligibility:
    ELIGIBLE = "eligible"
    INELIGIBLE = "ineligible"
    REVIEW_REQUIRED = "review_required"
    RESTRICTED_SCOPE = "restricted_scope"


class RetentionDecision:
    RETAIN = "retain"
    RETAIN_UNTIL = "retain_until"
    REVIEW_REQUIRED = "review_required"
    DELETE_OR_ERASE = "delete_or_erase"


class ForgetRequestStatus:
    REQUESTED = "requested"
    VALIDATING = "validating"
    APPROVED = "approved"
    EXECUTION_PENDING = "execution_pending"
    COMPLETED = "completed"
    REJECTED = "rejected"
    CANCELLED = "cancelled"
    PARTIALLY_COMPLETED = "partially_completed"


# ---------------------------------------------------------------------------
# Privacy Policy
# ---------------------------------------------------------------------------

class PrivacyPolicy(db.Model):
    """Tenant-scoped privacy configuration."""
    __tablename__ = "privacy_policies"
    __table_args__ = (Index("ix_privacy_policy_tenant", "tenant_id"),)

    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.Integer, db.ForeignKey("tenants.id"), nullable=True, index=True)
    policy_version = db.Column(db.Integer, default=1)
    default_sensitivity = db.Column(db.String(30), default="internal")
    default_retention = db.Column(db.String(30), default="retain")
    default_memory_eligibility = db.Column(db.String(30), default="ineligible")
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# ---------------------------------------------------------------------------
# Sensitivity Policy
# ---------------------------------------------------------------------------

class SensitivityPolicy(db.Model):
    """Tenant-configurable sensitivity rules per source/object type."""
    __tablename__ = "sensitivity_policies"
    __table_args__ = (Index("ix_sens_policy_tenant", "tenant_id"),)

    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.Integer, db.ForeignKey("tenants.id"), nullable=True, index=True)
    policy_version = db.Column(db.Integer, default=1)
    source_type = db.Column(db.String(60), default="")  # "communication", "document", "person"
    sensitivity_level = db.Column(db.String(30), nullable=False, default="internal")
    reason_code = db.Column(db.String(60), default="")
    is_system = db.Column(db.Boolean, default=False)  # System non-overridable
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


# ---------------------------------------------------------------------------
# Retention Policy
# ---------------------------------------------------------------------------

class RetentionPolicy(db.Model):
    """Retention rules per source/object type."""
    __tablename__ = "retention_policies"
    __table_args__ = (Index("ix_ret_policy_tenant", "tenant_id"),)

    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.Integer, db.ForeignKey("tenants.id"), nullable=True, index=True)
    policy_version = db.Column(db.Integer, default=1)
    source_type = db.Column(db.String(60), default="")
    decision = db.Column(db.String(30), nullable=False, default="retain")
    retention_days = db.Column(db.Integer, nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


# ---------------------------------------------------------------------------
# Memory Eligibility Policy
# ---------------------------------------------------------------------------

class MemoryEligibilityPolicy(db.Model):
    """Memory eligibility rules per source/object type."""
    __tablename__ = "memory_eligibility_policies"
    __table_args__ = (Index("ix_mem_elig_policy_tenant", "tenant_id"),)

    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.Integer, db.ForeignKey("tenants.id"), nullable=True, index=True)
    policy_version = db.Column(db.Integer, default=1)
    source_type = db.Column(db.String(60), default="")
    reason_code = db.Column(db.String(60), default="")
    decision = db.Column(db.String(30), nullable=False, default="ineligible")
    is_system = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


# ---------------------------------------------------------------------------
# Sensitivity Assessment
# ---------------------------------------------------------------------------

class SensitivityAssessment(db.Model):
    """Deterministic sensitivity evaluation for a source object."""
    __tablename__ = "sensitivity_assessments"
    __table_args__ = (
        Index("ix_sa_source", "source_type", "source_id"),
        Index("ix_sa_tenant", "tenant_id"),
    )

    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.Integer, db.ForeignKey("tenants.id"), nullable=True, index=True)
    source_type = db.Column(db.String(60), nullable=False)
    source_id = db.Column(db.Integer, nullable=False)
    sensitivity_level = db.Column(db.String(30), nullable=False, default="internal")
    reason_code = db.Column(db.String(60), default="")
    reason_tags = db.Column(db.Text, default="[]")  # JSON list of reasons
    policy_version = db.Column(db.Integer, default=1)
    evaluated_at = db.Column(db.DateTime, default=datetime.utcnow)
    evaluation_mechanism = db.Column(db.String(60), default="deterministic_rules")


# ---------------------------------------------------------------------------
# Privacy Decision
# ---------------------------------------------------------------------------

class PrivacyDecision(db.Model):
    """Canonical privacy decision for a source object."""
    __tablename__ = "privacy_decisions"
    __table_args__ = (
        Index("ix_pd_source", "source_type", "source_id"),
        Index("ix_pd_tenant", "tenant_id"),
    )

    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.Integer, db.ForeignKey("tenants.id"), nullable=True, index=True)
    source_type = db.Column(db.String(60), nullable=False)
    source_id = db.Column(db.Integer, nullable=False)
    retention_decision = db.Column(db.String(30), default="retain")
    retention_due_at = db.Column(db.DateTime, nullable=True)
    memory_eligibility = db.Column(db.String(30), nullable=False, default="ineligible")
    sensitivity_level = db.Column(db.String(30), default="internal")
    policy_version = db.Column(db.Integer, default=1)
    reason_codes = db.Column(db.Text, default="[]")  # JSON list
    evaluated_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)


# ---------------------------------------------------------------------------
# Restriction (Consent / Opt-Out)
# ---------------------------------------------------------------------------

class Restriction(db.Model):
    """Explicit governance restriction on a Person or object."""
    __tablename__ = "restrictions"
    __table_args__ = (
        Index("ix_restriction_person", "person_id"),
        Index("ix_restriction_tenant", "tenant_id"),
    )

    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.Integer, db.ForeignKey("tenants.id"), nullable=True, index=True)
    person_id = db.Column(db.Integer, db.ForeignKey("persons.id"), nullable=True, index=True)
    restriction_type = db.Column(db.String(60), nullable=False)
    # do_not_use_for_memory, do_not_use_for_marketing, do_not_contact,
    # restrict_to_operational_purpose, restrict_to_source, restrict_to_relationship_context
    scope = db.Column(db.String(255), default="")
    reason = db.Column(db.Text, default="")
    created_by = db.Column(db.String(120), default="")
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# ---------------------------------------------------------------------------
# Forget / Revocation Request
# ---------------------------------------------------------------------------

class ForgetRequest(db.Model):
    """Governed request to forget, revoke, or restrict data processing."""
    __tablename__ = "forget_requests"
    __table_args__ = (
        Index("ix_fr_tenant", "tenant_id"),
        Index("ix_fr_person", "person_id"),
    )

    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.Integer, db.ForeignKey("tenants.id"), nullable=True, index=True)
    person_id = db.Column(db.Integer, db.ForeignKey("persons.id"), nullable=True, index=True)
    request_type = db.Column(db.String(60), nullable=False)  # forget, revoke_memory, restrict_processing
    subject_scope = db.Column(db.String(255), default="")
    reason = db.Column(db.Text, default="")
    status = db.Column(db.String(30), nullable=False, default="requested")
    approved_by = db.Column(db.String(120), default="")
    approved_at = db.Column(db.DateTime, nullable=True)
    completed_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# ---------------------------------------------------------------------------
# Review Queue
# ---------------------------------------------------------------------------

class PrivacyReviewItem(db.Model):
    """Review-required privacy/sensitivity/memory-eligibility items."""
    __tablename__ = "privacy_review_items"
    __table_args__ = (
        Index("ix_pri_tenant", "tenant_id", "status"),
        Index("ix_pri_source", "source_type", "source_id"),
    )

    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.Integer, db.ForeignKey("tenants.id"), nullable=True, index=True)
    source_type = db.Column(db.String(60), nullable=False)
    source_id = db.Column(db.Integer, nullable=False)
    reason_code = db.Column(db.String(60), default="")
    decision_type = db.Column(db.String(30), nullable=False)  # sensitivity, retention, memory_eligibility
    status = db.Column(db.String(30), nullable=False, default="pending")
    # pending, approved, denied
    reviewed_by = db.Column(db.String(120), default="")
    reviewed_at = db.Column(db.DateTime, nullable=True)
    review_note = db.Column(db.Text, default="")
    policy_version = db.Column(db.Integer, default=1)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)