"""
SHUNYA — LLM Intelligence Runtime Models (Phase 9)
"""
from datetime import datetime
from app import db


class ModelRun(db.Model):
    __tablename__ = "model_runs"
    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.Integer, nullable=True, index=True)
    correlation_key = db.Column(db.String(128), nullable=True, index=True)
    purpose_code = db.Column(db.String(60), default="general")
    provider = db.Column(db.String(60), nullable=False)
    provider_model_id = db.Column(db.String(120), default="")
    canonical_model = db.Column(db.String(60), default="")
    adapter_mechanism = db.Column(db.String(60), default="")
    adapter_version = db.Column(db.String(30), default="")
    status = db.Column(db.String(30), nullable=False, default="created")
    finish_reason = db.Column(db.String(60), default="")
    output_mode = db.Column(db.String(30), default="text")
    response_text = db.Column(db.Text, default="")
    structured_result = db.Column(db.Text, default="")
    tool_requests = db.Column(db.Text, default="")
    usage_prompt_tokens = db.Column(db.Integer, nullable=True)
    usage_completion_tokens = db.Column(db.Integer, nullable=True)
    usage_cost = db.Column(db.Float, nullable=True)
    error_class = db.Column(db.String(60), default="")
    error_reason_code = db.Column(db.String(60), default="")
    prompt_template_id = db.Column(db.String(60), default="")
    prompt_template_version = db.Column(db.String(30), default="")
    retry_count = db.Column(db.Integer, default=0)
    parent_run_id = db.Column(db.Integer, nullable=True)
    provider_reference_id = db.Column(db.String(120), default="")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime, nullable=True)