"""SHUNYA M8 — Executive Intelligence Service.

Reasoning traces, learning feedback loop, explainability, anomaly detection,
and confidence scoring.
"""
from __future__ import annotations

import json
import time
import uuid
from datetime import datetime, timedelta
from typing import Any

from app import db
from app.intelligence.models import AnomalyRecord, LearningEvent, ReasoningTrace

from app.founder.models import FounderObject, FounderSpace, FounderConversation, FounderMessage


# ---------------------------------------------------------------------------
# Reasoning Trace
# ---------------------------------------------------------------------------

def create_reasoning_trace(
    identity_id: str,
    reasoning_type: str,
    query: str,
    ai_response: str,
    context_summary: str = "",
    object_id: str | None = None,
    reasoning_chain: list[dict[str, Any]] | None = None,
    sources: list[dict[str, Any]] | None = None,
    confidence_score: float = 0.0,
    execution_time_ms: int = 0,
) -> ReasoningTrace:
    """Create an immutable reasoning trace for an AI interaction."""
    trace_id = f"trace_{uuid.uuid4().hex[:20]}"

    trace = ReasoningTrace(
        trace_id=trace_id,
        identity_id=identity_id,
        object_id=object_id,
        reasoning_type=reasoning_type,
        query_text=query,
        context_summary=context_summary,
        reasoning_chain=json.dumps(reasoning_chain or []),
        confidence_score=confidence_score,
        ai_response=ai_response,
        sources=json.dumps(sources or []),
        execution_time_ms=execution_time_ms,
    )
    db.session.add(trace)
    db.session.commit()
    return trace


def get_traces(identity_id: str,
               object_id: str | None = None,
               limit: int = 20) -> list[dict[str, Any]]:
    """Get reasoning traces for an identity, optionally filtered by object."""
    query = ReasoningTrace.query.filter_by(identity_id=identity_id)
    if object_id:
        query = query.filter_by(object_id=object_id)
    traces = query.order_by(ReasoningTrace.created_at.desc()).limit(limit).all()
    return [t.to_dict() for t in traces]


def get_trace(trace_id: str) -> dict[str, Any] | None:
    """Get a single trace by trace_id."""
    trace = ReasoningTrace.query.filter_by(trace_id=trace_id).first()
    return trace.to_dict() if trace else None


def correct_trace(trace_id: str, corrected_response: str) -> bool:
    """Record a correction to a reasoning trace."""
    trace = ReasoningTrace.query.filter_by(trace_id=trace_id).first()
    if not trace:
        return False

    trace.is_corrected = True
    trace.corrected_response = corrected_response

    # Create learning event
    learn = LearningEvent(
        identity_id=trace.identity_id,
        learning_type="correction",
        trace_id=trace_id,
        trigger_summary=f"Corrected AI response: {trace.query_text[:100]}",
        before_state=json.dumps({"response": trace.ai_response}),
        after_state=json.dumps({"corrected_response": corrected_response}),
        outcome="positive",
    )
    db.session.add(learn)
    db.session.commit()
    return True


# ---------------------------------------------------------------------------
# Learning Feedback
# ---------------------------------------------------------------------------

def record_learning(
    identity_id: str,
    learning_type: str,
    trigger_summary: str,
    before_state: dict[str, Any] | None = None,
    after_state: dict[str, Any] | None = None,
    outcome: str = "positive",
    trace_id: str | None = None,
) -> None:
    """Record a learning event."""
    event = LearningEvent(
        identity_id=identity_id,
        learning_type=learning_type,
        trace_id=trace_id,
        trigger_summary=trigger_summary,
        before_state=json.dumps(before_state or {}),
        after_state=json.dumps(after_state or {}),
        outcome=outcome,
    )
    db.session.add(event)
    db.session.commit()


def get_learning_history(identity_id: str, limit: int = 30) -> list[dict[str, Any]]:
    """Get learning history for an identity."""
    events = LearningEvent.query.filter_by(identity_id=identity_id).order_by(
        LearningEvent.created_at.desc()
    ).limit(limit).all()
    return [e.to_dict() for e in events]


def get_learning_summary(identity_id: str) -> dict[str, Any]:
    """Get a summary of learning activity."""
    total = LearningEvent.query.filter_by(identity_id=identity_id).count()
    today = LearningEvent.query.filter_by(identity_id=identity_id).filter(
        LearningEvent.created_at >= datetime.utcnow() - timedelta(days=1)
    ).count()
    corrections = LearningEvent.query.filter_by(
        identity_id=identity_id, learning_type="correction"
    ).count()

    return {
        "total_learnings": total,
        "learned_today": today,
        "corrections_received": corrections,
        "last_learning": get_learning_history(identity_id, limit=1)[0] if total > 0 else None,
    }


# ---------------------------------------------------------------------------
# Anomaly Detection
# ---------------------------------------------------------------------------

def detect_anomalies(identity_id: str) -> list[dict[str, Any]]:
    """Run deterministic anomaly detection rules.

    Checks for:
    - Stalled objects (not updated in 14+ days with active conversations)
    - Inactive spaces
    - Objects with no conversations (orphans)
    """
    anomalies: list[dict[str, Any]] = []
    now = datetime.utcnow()
    threshold_14d = now - timedelta(days=14)
    threshold_7d = now - timedelta(days=7)

    spaces = FounderSpace.query.filter_by(
        identity_id=identity_id, status="active"
    ).all()
    space_ids = [s.space_id for s in spaces]

    if not space_ids:
        return anomalies

    # Stalled objects
    stalled = FounderObject.query.filter(
        FounderObject.space_id.in_(space_ids),
        FounderObject.status == "active",
        FounderObject.updated_at <= threshold_14d,
    ).all()

    for obj in stalled:
        conv = FounderConversation.query.filter_by(
            object_id=obj.object_id, status="active"
        ).first()
        if not conv:
            continue

        # Check if we already have this anomaly
        existing = AnomalyRecord.query.filter_by(
            identity_id=identity_id,
            object_id=obj.object_id,
            anomaly_type="status_stall",
            status="open",
        ).first()
        if existing:
            continue

        days_stalled = (now - (obj.updated_at or now)).days
        anomaly = AnomalyRecord(
            identity_id=identity_id,
            object_id=obj.object_id,
            anomaly_type="status_stall",
            severity="warning" if days_stalled > 21 else "info",
            title=f"'{obj.name}' has been inactive for {days_stalled} days",
            description=f"Object '{obj.name}' has an active conversation but no updates in {days_stalled} days.",
            evidence=json.dumps({
                "object_id": obj.object_id,
                "object_name": obj.name,
                "days_since_update": days_stalled,
                "updated_at": obj.updated_at.isoformat() if obj.updated_at else None,
            }),
        )
        db.session.add(anomaly)
        anomalies.append(anomaly.to_dict())

    # Orphan objects (no conversations, old)
    orphans = FounderObject.query.filter(
        FounderObject.space_id.in_(space_ids),
        FounderObject.status == "active",
        FounderObject.updated_at <= threshold_7d,
    ).all()

    for obj in orphans:
        conv = FounderConversation.query.filter_by(
            object_id=obj.object_id, status="active"
        ).first()
        if conv:
            continue

        existing = AnomalyRecord.query.filter_by(
            identity_id=identity_id,
            object_id=obj.object_id,
            anomaly_type="pattern_break",
            status="open",
        ).first()
        if existing:
            continue

        days_old = (now - (obj.created_at or now)).days
        if days_old < 3:
            continue  # Too new to be anomalous

        anomaly = AnomalyRecord(
            identity_id=identity_id,
            object_id=obj.object_id,
            anomaly_type="pattern_break",
            severity="info",
            title=f"'{obj.name}' has never been discussed",
            description=f"Object created {days_old} days ago with no conversation history.",
            evidence=json.dumps({
                "object_id": obj.object_id,
                "object_name": obj.name,
                "days_since_creation": days_old,
                "has_conversation": False,
            }),
        )
        db.session.add(anomaly)
        anomalies.append(anomaly.to_dict())

    db.session.commit()
    return anomalies


def get_anomalies(identity_id: str,
                  status: str | None = "open",
                  limit: int = 20) -> list[dict[str, Any]]:
    """Get anomaly records for an identity."""
    query = AnomalyRecord.query.filter_by(identity_id=identity_id)
    if status:
        query = query.filter_by(status=status)
    records = query.order_by(AnomalyRecord.created_at.desc()).limit(limit).all()
    return [r.to_dict() for r in records]


def resolve_anomaly(anomaly_id: int) -> bool:
    """Mark an anomaly as resolved."""
    anomaly = AnomalyRecord.query.get(anomaly_id)
    if not anomaly:
        return False
    anomaly.status = "resolved"
    anomaly.resolved_at = datetime.utcnow()
    db.session.commit()
    return True


# ---------------------------------------------------------------------------
# Confidence Scoring
# ---------------------------------------------------------------------------

def compute_confidence(context: dict[str, Any]) -> dict[str, Any]:
    """Compute a deterministic confidence score for AI reasoning.

    Based on: data completeness, conversation history, relationship data,
    recency of activity.
    """
    score = 0.0
    factors = []

    # Data completeness
    if context.get("object_name"):
        score += 0.15
        factors.append("object identified")
    if context.get("object_type"):
        score += 0.10
    if context.get("object_content"):
        score += 0.15
        factors.append("content available")
    if context.get("has_owner"):
        score += 0.10
        factors.append("owner known")

    # Relationship data
    rel_count = context.get("relationship_count", 0)
    if rel_count >= 3:
        score += 0.15
        factors.append(f"{rel_count} relationships")
    elif rel_count >= 1:
        score += 0.08
        factors.append("has relationships")

    # Conversation history
    msg_count = context.get("message_count", 0)
    if msg_count >= 5:
        score += 0.15
        factors.append(f"{msg_count} conversation messages")
    elif msg_count >= 1:
        score += 0.08
        factors.append("has conversation")

    # Recency
    days_since = context.get("days_since_update", 999)
    if days_since <= 1:
        score += 0.15
        factors.append("recently updated")
    elif days_since <= 7:
        score += 0.10
        factors.append(f"updated {days_since}d ago")
    elif days_since <= 30:
        score += 0.05

    score = round(min(score, 1.0), 2)

    if score >= 0.7:
        label = "high"
    elif score >= 0.4:
        label = "medium"
    else:
        label = "low"

    return {
        "score": score,
        "label": label,
        "factors": factors,
    }

# =========================================================================
# PROD-07 — Pattern Recognition Service
# =========================================================================

class IntelligenceService:

    @staticmethod
    def learn_from_execution(obj, decision: str, trigger_state: dict = None):
        from app.intelligence.models import Pattern
        pattern = Pattern(
            object_type=obj.object_type,
            trigger_state=trigger_state or obj.state,
            suggested_decision=decision,
            confidence=1.0
        )
        db.session.add(pattern)
        db.session.commit()
        return pattern

    @staticmethod
    def find_pattern(obj):
        from app.intelligence.models import Pattern
        return Pattern.query.filter_by(
            object_type=obj.object_type,
            trigger_state=obj.state
        ).first()
