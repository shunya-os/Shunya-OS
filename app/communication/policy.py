"""
SHUNYA — Capture Enforcer (Phase 3)
Enforces CapturePolicy and CaptureScope before message ingestion.
"""
from datetime import datetime
from typing import Optional
from app import db
from app.communication.models import (
    CommunicationSource, CommunicationCapturePolicy,
    CommunicationCaptureScope, ExternalConversation, ExternalMessage,
)


class CaptureVerdict:
    ALLOWED = "allowed"
    DENIED = "denied"
    PENDING_REVIEW = "pending_review"


class CaptureEnforcer:
    """Enforces capture governance for inbound communication.
    Pipeline: source → policy → scope → eligibility decision."""

    def __init__(self, session=None):
        self._session = session or db.session

    def evaluate(self, source_id: int, provider_chat_id: str,
                 is_group: bool = False) -> dict:
        """Evaluate capture eligibility for a message source/chat.
        Returns verdict with decision and reason."""
        # Resolve source
        source = self._session.get(CommunicationSource, source_id)
        if not source:
            return {"verdict": CaptureVerdict.DENIED, "reason": "Source not found"}
        if not source.is_active:
            return {"verdict": CaptureVerdict.DENIED, "reason": "Source inactive"}

        # Resolve policy
        policy = self._session.query(CommunicationCapturePolicy).filter_by(
            source_id=source_id
        ).first()

        if not policy:
            return {"verdict": CaptureVerdict.DENIED, "reason": "No capture policy configured"}

        # Check explicit scope
        scope = self._session.query(CommunicationCaptureScope).filter_by(
            source_id=source_id,
            external_chat_id=provider_chat_id,
        ).first()

        if scope:
            if scope.status == CaptureVerdict.DENIED:
                return {"verdict": CaptureVerdict.DENIED, "reason": "Chat explicitly denied",
                        "scope_id": scope.id}
            if scope.status == CaptureVerdict.ALLOWED:
                return {"verdict": CaptureVerdict.ALLOWED, "reason": "Chat explicitly allowed",
                        "scope_id": scope.id}
            # PENDING_REVIEW — no auto-approval
            return {"verdict": CaptureVerdict.PENDING_REVIEW, "reason": "Chat is pending review",
                    "scope_id": scope.id}

        # No existing scope — apply defaults
        account_mode = policy.account_mode or source.account_mode

        # MIXED_USE: DEFAULT CAPTURE = NOTHING
        if account_mode == "mixed_use":
            # Create pending scope
            new_scope = CommunicationCaptureScope(
                tenant_id=source.tenant_id,
                source_id=source_id,
                external_chat_id=provider_chat_id,
                status=CaptureVerdict.PENDING_REVIEW,
                reason="MIXED_USE default: chat pending review",
            )
            self._session.add(new_scope)
            self._session.commit()
            return {"verdict": CaptureVerdict.PENDING_REVIEW,
                    "reason": "MIXED_USE default: no capture — chat queued for review",
                    "scope_id": new_scope.id}

        # BUSINESS_DEDICATED: apply defaults
        if is_group:
            default_policy = policy.default_group_policy
        else:
            default_policy = policy.default_chat_policy

        if default_policy == CaptureVerdict.DENIED:
            return {"verdict": CaptureVerdict.DENIED,
                    "reason": "Default policy: denied"}
        elif default_policy == CaptureVerdict.PENDING_REVIEW:
            new_scope = CommunicationCaptureScope(
                tenant_id=source.tenant_id,
                source_id=source_id,
                external_chat_id=provider_chat_id,
                status=CaptureVerdict.PENDING_REVIEW,
                reason="BUSINESS_DEDICATED default: pending review",
            )
            self._session.add(new_scope)
            self._session.commit()
            return {"verdict": CaptureVerdict.PENDING_REVIEW,
                    "reason": "BUSINESS_DEDICATED default: pending review",
                    "scope_id": new_scope.id}

        # ALLOWED by default
        new_scope = CommunicationCaptureScope(
            tenant_id=source.tenant_id,
            source_id=source_id,
            external_chat_id=provider_chat_id,
            status=CaptureVerdict.ALLOWED,
            reason="BUSINESS_DEDICATED default: allowed",
        )
        self._session.add(new_scope)
        self._session.commit()
        return {"verdict": CaptureVerdict.ALLOWED,
                "reason": "BUSINESS_DEDICATED default: allowed",
                "scope_id": new_scope.id}

    def get_pending_reviews(self, tenant_id: Optional[int] = None) -> list[dict]:
        """List all PENDING_REVIEW scopes."""
        q = self._session.query(CommunicationCaptureScope).filter_by(
            status=CaptureVerdict.PENDING_REVIEW
        )
        if tenant_id:
            q = q.filter(CommunicationCaptureScope.tenant_id == tenant_id)
        scopes = q.order_by(CommunicationCaptureScope.created_at.desc()).all()
        return [{
            "id": s.id, "source_id": s.source_id,
            "external_chat_id": s.external_chat_id,
            "status": s.status, "reason": s.reason,
            "created_at": s.created_at.isoformat() if s.created_at else None,
        } for s in scopes]

    def approve_scope(self, scope_id: int, approved_by: str = "",
                      reason: str = "") -> dict:
        """Approve a capture scope for ingestion."""
        scope = self._session.get(CommunicationCaptureScope, scope_id)
        if not scope:
            return {"success": False, "error": "Scope not found"}
        scope.status = CaptureVerdict.ALLOWED
        scope.approved_by = approved_by
        scope.approved_at = datetime.utcnow()
        scope.reason = reason or scope.reason
        self._session.commit()
        return {"success": True, "scope_id": scope.id, "status": CaptureVerdict.ALLOWED}

    def deny_scope(self, scope_id: int, approved_by: str = "",
                   reason: str = "") -> dict:
        """Deny a capture scope permanently."""
        scope = self._session.get(CommunicationCaptureScope, scope_id)
        if not scope:
            return {"success": False, "error": "Scope not found"}
        scope.status = CaptureVerdict.DENIED
        scope.approved_by = approved_by
        scope.approved_at = datetime.utcnow()
        scope.reason = reason or scope.reason
        self._session.commit()
        return {"success": True, "scope_id": scope.id, "status": CaptureVerdict.DENIED}