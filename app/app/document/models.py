"""
SHUNYA — Document & Presentation Intelligence Models (Phase 7A)
"""
from datetime import datetime
from app import db
from sqlalchemy import Index


class DocumentLifecycle:
    RECEIVED = "received"; VALIDATING = "validating"; PARSED = "parsed"
    EXTRACTED = "extracted"; READY = "ready"; REVIEW_REQUIRED = "review_required"
    FAILED = "failed"; REVOKED = "revoked"; INVALIDATED = "invalidated"; SUPERSEDED = "superseded"


class ExtractionStatus:
    EXTRACTED = "extracted"; AMBIGUOUS = "ambiguous"
    MISSING = "missing"; INVALID = "invalid"; REVIEW_REQUIRED = "review_required"


class DocumentClassification:
    CONTRACT = "contract"; POLICY = "policy"; STATEMENT = "statement"
    PROPOSAL = "proposal"; QUOTATION = "quotation"; REPORT = "report"
    CIRCULAR = "circular"; SPREADSHEET = "spreadsheet"
    PRESENTATION = "presentation"; FORM = "form"
    CORRESPONDENCE_ATTACHMENT = "correspondence_attachment"
    OTHER = "other"; UNKNOWN = "unknown"


class OcrState:
    OCR_SUPPORTED_AND_EXECUTED = "ocr_supported_and_executed"
    OCR_REQUIRED_BUT_PROVIDER_UNAVAILABLE = "ocr_required_but_provider_unavailable"
    OCR_FAILED = "ocr_failed"; NO_OCR_REQUIRED = "no_ocr_required"


class DocumentRecord(db.Model):
    __tablename__ = "document_records"
    __table_args__ = (Index("ix_dr_tenant", "tenant_id"), Index("ix_dr_hash", "content_hash"), Index("ix_dr_class", "classification"), Index("ix_dr_lifecycle", "lifecycle"))
    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.Integer, nullable=True, index=True)
    source_reference_id = db.Column(db.Integer, nullable=True)
    original_filename = db.Column(db.String(500), default="")
    safe_display_name = db.Column(db.String(500), default="")
    mime_type = db.Column(db.String(100), default="")
    content_hash = db.Column(db.String(128), nullable=True, index=True)
    file_size = db.Column(db.Integer, default=0)
    page_count = db.Column(db.Integer, default=0)
    sheet_count = db.Column(db.Integer, default=0)
    slide_count = db.Column(db.Integer, default=0)
    classification = db.Column(db.String(60), default="unknown")
    lifecycle = db.Column(db.String(30), nullable=False, default="received")
    ingestion_mechanism = db.Column(db.String(30), default="upload")
    ocr_state = db.Column(db.String(50), default="no_ocr_required")
    parser_mechanism = db.Column(db.String(60), default="")
    parser_version = db.Column(db.String(30), default="")
    storage_reference = db.Column(db.String(500), default="")
    supersedes_id = db.Column(db.Integer, nullable=True)
    superseded_by_id = db.Column(db.Integer, nullable=True)
    privacy_decision_id = db.Column(db.Integer, nullable=True)
    observed_at = db.Column(db.DateTime, nullable=True)
    actor = db.Column(db.String(120), default="")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class DocumentSection(db.Model):
    __tablename__ = "document_sections"
    __table_args__ = (Index("ix_ds_doc", "document_id"), Index("ix_ds_tenant", "tenant_id"), Index("ix_ds_type", "section_type"))
    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.Integer, nullable=True, index=True)
    document_id = db.Column(db.Integer, nullable=False, index=True)
    section_type = db.Column(db.String(30), default="text")
    page_number = db.Column(db.Integer, nullable=True)
    sheet_name = db.Column(db.String(200), default="")
    slide_number = db.Column(db.Integer, nullable=True)
    block_order = db.Column(db.Integer, nullable=True)
    heading = db.Column(db.String(500), default="")
    content_preview = db.Column(db.String(500), default="")
    content_hash = db.Column(db.String(64), default="")
    parser_mechanism = db.Column(db.String(60), default="")
    status = db.Column(db.String(30), default="parsed")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class ExtractedField(db.Model):
    __tablename__ = "extracted_fields"
    __table_args__ = (Index("ix_ef_doc", "document_id"), Index("ix_ef_section", "section_id"), Index("ix_ef_tenant", "tenant_id"), Index("ix_ef_key", "field_key"))
    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.Integer, nullable=True, index=True)
    document_id = db.Column(db.Integer, nullable=False, index=True)
    section_id = db.Column(db.Integer, nullable=True, index=True)
    field_key = db.Column(db.String(255), nullable=False, index=True)
    value = db.Column(db.Text, nullable=False)
    value_type = db.Column(db.String(30), default="string")
    location = db.Column(db.String(200), default="")
    extraction_mechanism = db.Column(db.String(60), default="")
    extraction_status = db.Column(db.String(30), default="extracted")
    status = db.Column(db.String(30), default="active")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class DocumentComparison(db.Model):
    __tablename__ = "document_comparisons"
    __table_args__ = (Index("ix_dc_tenant", "tenant_id"), Index("ix_dc_docs", "left_document_id", "right_document_id"))
    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.Integer, nullable=True, index=True)
    left_document_id = db.Column(db.Integer, nullable=False, index=True)
    right_document_id = db.Column(db.Integer, nullable=False, index=True)
    comparison_state = db.Column(db.String(30), default="pending")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class ComparisonItem(db.Model):
    __tablename__ = "comparison_items"
    __table_args__ = (Index("ix_ci_comparison", "comparison_id"), Index("ix_ci_tenant", "tenant_id"))
    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.Integer, nullable=True, index=True)
    comparison_id = db.Column(db.Integer, nullable=False, index=True)
    field_key = db.Column(db.String(255), nullable=False)
    left_value = db.Column(db.Text, default="")
    right_value = db.Column(db.Text, default="")
    result = db.Column(db.String(30), nullable=False, default="equal")
    location_left = db.Column(db.String(200), default="")
    location_right = db.Column(db.String(200), default="")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)