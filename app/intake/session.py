"""
Intake Session — lifecycle orchestration for data intake operations.
"""
import json
import hashlib
from datetime import datetime
from typing import Optional
from app import db
from app.models import IntakeSession, IntakeCandidate, IntakeFieldMapping


class IntakeSessionState:
    RECEIVED = "received"
    PROFILED = "profiled"
    MAPPING_REQUIRED = "mapping_required"
    READY_FOR_REVIEW = "ready_for_review"
    APPROVED = "approved"
    IMPORTING = "importing"
    COMPLETED = "completed"
    PARTIALLY_COMPLETED = "partially_completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

    # Approval scopes
    APPROVE_SAFE_ONLY = "approve_safe_only"
    APPROVE_ALL = "approve_all"

    VALID_TRANSITIONS = {
        RECEIVED: [PROFILED, CANCELLED, FAILED],
        PROFILED: [MAPPING_REQUIRED, READY_FOR_REVIEW, CANCELLED, FAILED],
        MAPPING_REQUIRED: [READY_FOR_REVIEW, CANCELLED, FAILED],
        READY_FOR_REVIEW: [APPROVED, CANCELLED, FAILED],
        APPROVED: [IMPORTING, CANCELLED, FAILED],
        IMPORTING: [COMPLETED, PARTIALLY_COMPLETED, FAILED],
        COMPLETED: [],
        PARTIALLY_COMPLETED: [READY_FOR_REVIEW, CANCELLED],
        FAILED: [],
        CANCELLED: [],
    }


class IntakeOrchestrator:
    """Orchestrates the full intake lifecycle."""

    def __init__(self, session=None):
        self._session = session or db.session

    def create_session(self, source_type: str, source_name: str = "",
                       tenant_id: Optional[int] = None,
                       created_by: str = "") -> IntakeSession:
        session = IntakeSession(
            tenant_id=tenant_id,
            source_type=source_type,
            source_name=source_name,
            status=IntakeSessionState.RECEIVED,
            created_by=created_by,
        )
        self._session.add(session)
        self._session.commit()
        return session

    def transition(self, intake_session: IntakeSession, new_state: str) -> IntakeSession:
        allowed = IntakeSessionState.VALID_TRANSITIONS.get(intake_session.status, [])
        if new_state not in allowed:
            raise ValueError(f"Cannot transition from {intake_session.status} to {new_state}. "
                             f"Allowed: {allowed}")
        intake_session.status = new_state
        self._session.commit()
        return intake_session

    def compute_checksum(self, content: str) -> str:
        return hashlib.sha256(content.encode("utf-8")).hexdigest()

    def get_session(self, session_id: int) -> Optional[IntakeSession]:
        return self._session.get(IntakeSession, session_id)

    def get_by_tenant(self, tenant_id: int, limit: int = 20) -> list[IntakeSession]:
        return (self._session.query(IntakeSession)
                .filter(IntakeSession.tenant_id == tenant_id)
                .order_by(IntakeSession.created_at.desc())
                .limit(limit)
                .all())