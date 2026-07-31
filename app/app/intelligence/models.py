"""SHUNYA M8 — Executive Intelligence Models.

Persistence for reasoning traces, learning events, and anomaly records.
"""
from datetime import datetime

from app import db
from sqlalchemy import Index, Text


# ---------------------------------------------------------------------------
# Reasoning Trace — Explainability for every AI action
# ---------------------------------------------------------------------------

class ReasoningTrace(db.Model):
    """An immutable trace of how SHUNYA arrived at a conclusion.

    Records the full chain: intent → identity → context → reasoning → response.
    """

    __tablename__ = "m8_reasoning_traces"
    __table_args__ = (
        Index("ix_m8_trace_object", "object_id", "created_at"),
        Index("ix_m8_trace_type", "reasoning_type", "created_at"),
    )

    id = db.Column(db.Integer, primary_key=True)
    trace_id = db.Column(db.String(64), unique=True, nullable=False, index=True)
    identity_id = db.Column(db.String(64), nullable=False, index=True)
    object_id = db.Column(db.String(64), nullable=True)
    reasoning_type = db.Column(db.String(40), nullable=False)
    # Types: analysis, prediction, recommendation, assessment, summary, anomaly
    query_text = db.Column(Text, default="")
    # The original question or trigger
    context_summary = db.Column(db.String(500), default="")
    # Brief summary of what context was used
    reasoning_chain = db.Column(Text, default="")
    # JSON array: [{"step": "identity_resolution", "data": {...}}, ...]
    confidence_score = db.Column(db.Float, default=0.0)
    ai_response = db.Column(Text, default="")
    sources = db.Column(Text, default="")
    # JSON: [{"type": "object", "id": "...", "field": "..."}, ...]
    is_corrected = db.Column(db.Boolean, default=False)
    corrected_response = db.Column(Text, nullable=True)
    execution_time_ms = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "trace_id": self.trace_id,
            "identity_id": self.identity_id,
            "object_id": self.object_id,
            "reasoning_type": self.reasoning_type,
            "query_text": self.query_text[:200] if self.query_text else "",
            "context_summary": self.context_summary,
            "reasoning_chain": self.reasoning_chain,
            "confidence_score": self.confidence_score,
            "ai_response": self.ai_response[:500] if self.ai_response else "",
            "sources": self.sources,
            "is_corrected": self.is_corrected,
            "corrected_response": self.corrected_response,
            "execution_time_ms": self.execution_time_ms,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


# ---------------------------------------------------------------------------
# Learning Event — Outcome-based learning
# ---------------------------------------------------------------------------

class LearningEvent(db.Model):
    """Records a learning interaction where SHUNYA was corrected or validated.

    Enables the learning feedback loop: observe → decide → act → learn → improve.
    """

    __tablename__ = "m8_learning_events"
    __table_args__ = (
        Index("ix_m8_learn_identity", "identity_id", "created_at"),
        Index("ix_m8_learn_type", "learning_type"),
    )

    id = db.Column(db.Integer, primary_key=True)
    identity_id = db.Column(db.String(64), nullable=False, index=True)
    learning_type = db.Column(db.String(40), nullable=False)
    # Types: correction, validation, new_pattern, outcome_recorded
    trace_id = db.Column(db.String(64), nullable=True)
    trigger_summary = db.Column(db.String(500), default="")
    # What triggered the learning
    before_state = db.Column(Text, default="")
    # JSON: what SHUNYA thought before
    after_state = db.Column(Text, default="")
    # JSON: what SHUNYA learned
    outcome = db.Column(db.String(100), default="")
    # positive, neutral, negative
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "identity_id": self.identity_id,
            "learning_type": self.learning_type,
            "trace_id": self.trace_id,
            "trigger_summary": self.trigger_summary,
            "outcome": self.outcome,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


# ---------------------------------------------------------------------------
# Anomaly Detection Record
# ---------------------------------------------------------------------------

class AnomalyRecord(db.Model):
    """Detected anomaly or pattern deviation in business data."""

    __tablename__ = "m8_anomaly_records"
    __table_args__ = (
        Index("ix_m8_anomaly_status", "anomaly_type", "status"),
    )

    id = db.Column(db.Integer, primary_key=True)
    identity_id = db.Column(db.String(64), nullable=False, index=True)
    object_id = db.Column(db.String(64), nullable=True)
    anomaly_type = db.Column(db.String(40), nullable=False)
    # Types: inactivity_spike, status_stall, relationship_drop, pattern_break
    severity = db.Column(db.String(20), default="info")
    # info, warning, critical
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(Text, default="")
    evidence = db.Column(Text, default="")
    # JSON with supporting data
    status = db.Column(db.String(20), default="open")
    # open, acknowledged, resolved, dismissed
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    resolved_at = db.Column(db.DateTime, nullable=True)

    def to_dict(self):
        return {
            "id": self.id,
            "identity_id": self.identity_id,
            "object_id": self.object_id,
            "anomaly_type": self.anomaly_type,
            "severity": self.severity,
            "title": self.title,
            "description": self.description,
            "evidence": self.evidence,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }