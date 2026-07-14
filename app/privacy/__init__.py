"""
SHUNYA — Privacy, Sensitivity & Memory Eligibility Service (Phase 4)
"""
import json
from datetime import datetime, timedelta
from typing import Optional
from app import db
from app.privacy.models import (
    PrivacyPolicy, SensitivityPolicy, RetentionPolicy, MemoryEligibilityPolicy,
    SensitivityAssessment, PrivacyDecision, Restriction, ForgetRequest,
    PrivacyReviewItem, SensitivityLevel, MemoryEligibility, RetentionDecision,
    ForgetRequestStatus, SYSTEM_NON_OVERRIDABLE_REASONS,
)
from app.shunya.identity import IdentityResolver


class PrivacyService:
    """Canonical privacy, sensitivity and memory eligibility evaluation service."""

    def __init__(self, session=None):
        self._session = session or db.session

    # ------------------------------------------------------------------
    # Sensitivity Assessment
    # ------------------------------------------------------------------

    def assess_sensitivity(self, source_type: str, source_id: int,
                           reason_codes: list = None,
                           tenant_id: Optional[int] = None,
                           is_system_override: bool = False) -> dict:
        """Evaluate sensitivity for a source object. Returns assessment."""
        # Determine level from reason codes
        reasons = reason_codes or []
        tags = list(reasons)

        # System non-overridable check
        for r in reasons:
            if r in SYSTEM_NON_OVERRIDABLE_REASONS:
                level = SensitivityLevel.HIGHLY_SENSITIVE
                return self._save_assessment(source_type, source_id, level, r, tags, tenant_id, 1)

        # Check configured policies
        policies = self._session.query(SensitivityPolicy).filter_by(
            tenant_id=tenant_id, is_active=True
        ).all()

        level = SensitivityLevel.INTERNAL  # Default
        reason_code = ""

        # Apply strictest matching policy
        for p in policies:
            if not p.source_type or p.source_type == source_type:
                if p.sensitivity_level in (SensitivityLevel.HIGHLY_SENSITIVE, SensitivityLevel.RESTRICTED):
                    level = p.sensitivity_level
                    reason_code = p.reason_code
                elif p.sensitivity_level == SensitivityLevel.CONFIDENTIAL and level not in (
                    SensitivityLevel.HIGHLY_SENSITIVE, SensitivityLevel.RESTRICTED):
                    level = p.sensitivity_level
                    reason_code = p.reason_code

        return self._save_assessment(source_type, source_id, level, reason_code, tags, tenant_id, 1)

    def _save_assessment(self, source_type: str, source_id: int,
                         level: str, reason_code: str, tags: list,
                         tenant_id: Optional[int], policy_version: int) -> dict:
        assessment = SensitivityAssessment(
            tenant_id=tenant_id,
            source_type=source_type, source_id=source_id,
            sensitivity_level=level, reason_code=reason_code,
            reason_tags=json.dumps(tags),
            policy_version=policy_version,
        )
        self._session.add(assessment)
        self._session.flush()
        return {
            "assessment_id": assessment.id,
            "sensitivity_level": level,
            "reason_code": reason_code,
            "reason_tags": tags,
        }

    # ------------------------------------------------------------------
    # Memory Eligibility Decision
    # ------------------------------------------------------------------

    def evaluate_memory_eligibility(self, source_type: str, source_id: int,
                                    tenant_id: Optional[int] = None,
                                    sensitivity_level: str = "internal",
                                    reason_codes: list = None,
                                    person_id: Optional[int] = None) -> dict:
        """Evaluate whether a source object is eligible for memory processing.
        Missing verdict → INELIGIBLE (fail-closed)."""
        reasons = reason_codes or []

        # 1. System non-overridable check
        for r in reasons:
            if r in SYSTEM_NON_OVERRIDABLE_REASONS:
                return self._save_decision(
                    source_type, source_id, MemoryEligibility.INELIGIBLE,
                    tenant_id, 1, reasons, "system_non_overridable"
                )

        # 2. Explicit restriction check
        if person_id:
            restrictions = self._session.query(Restriction).filter_by(
                person_id=person_id, restriction_type="do_not_use_for_memory",
                is_active=True,
            ).all()
            if restrictions:
                return self._save_decision(
                    source_type, source_id, MemoryEligibility.INELIGIBLE,
                    tenant_id, 1, reasons, "explicit_restriction"
                )

        # 3. Approved revocation check
        if person_id:
            approved_revocations = self._session.query(ForgetRequest).filter_by(
                person_id=person_id,
                status=ForgetRequestStatus.APPROVED,
            ).all()
            if approved_revocations:
                return self._save_decision(
                    source_type, source_id, MemoryEligibility.INELIGIBLE,
                    tenant_id, 1, reasons, "approved_revocation"
                )

        # 4. Tenant policy check
        tenant_policies = self._session.query(MemoryEligibilityPolicy).filter_by(
            tenant_id=tenant_id, is_active=True,
        ).all()

        for p in tenant_policies:
            if p.is_system:
                continue  # System policies handled above
            if not p.source_type or p.source_type == source_type:
                if p.decision == MemoryEligibility.INELIGIBLE:
                    return self._save_decision(
                        source_type, source_id, MemoryEligibility.INELIGIBLE,
                        tenant_id, 1, reasons, "tenant_policy"
                    )
                if p.decision == MemoryEligibility.REVIEW_REQUIRED:
                    self._create_review_item(source_type, source_id, "memory_eligibility",
                                             p.reason_code, tenant_id, 1)
                    return self._save_decision(
                        source_type, source_id, MemoryEligibility.REVIEW_REQUIRED,
                        tenant_id, 1, reasons, "review_required"
                    )

        # 5. Default: fail closed for sensitive levels
        if sensitivity_level in (SensitivityLevel.HIGHLY_SENSITIVE, SensitivityLevel.RESTRICTED):
            return self._save_decision(
                source_type, source_id, MemoryEligibility.INELIGIBLE,
                tenant_id, 1, reasons, "sensitivity_level_denied"
            )

        if sensitivity_level == SensitivityLevel.CONFIDENTIAL:
            self._create_review_item(source_type, source_id, "memory_eligibility",
                                     "confidential", tenant_id, 1)
            return self._save_decision(
                source_type, source_id, MemoryEligibility.REVIEW_REQUIRED,
                tenant_id, 1, reasons, "confidential_review_required"
            )

        # 6. Default policy
        default_policy = self._session.query(PrivacyPolicy).filter_by(
            tenant_id=tenant_id, is_active=True
        ).first()

        if default_policy:
            default_eligibility = default_policy.default_memory_eligibility
            if default_eligibility == MemoryEligibility.ELIGIBLE:
                return self._save_decision(
                    source_type, source_id, MemoryEligibility.ELIGIBLE,
                    tenant_id, 1, reasons, "default_policy"
                )

        # Fail closed — missing verdict or default
        return self._save_decision(
            source_type, source_id, MemoryEligibility.INELIGIBLE,
            tenant_id, 1, reasons, "fail_closed_no_verdict"
        )

    def _save_decision(self, source_type: str, source_id: int,
                       eligibility: str, tenant_id: Optional[int],
                       policy_version: int, reasons: list,
                       reason_code: str) -> dict:
        decision = PrivacyDecision(
            tenant_id=tenant_id,
            source_type=source_type, source_id=source_id,
            memory_eligibility=eligibility,
            reason_codes=json.dumps([reason_code] + reasons),
            policy_version=policy_version,
            is_active=True,
        )
        self._session.add(decision)
        self._session.flush()
        return {
            "decision_id": decision.id,
            "memory_eligibility": eligibility,
            "reason_code": reason_code,
        }

    # ------------------------------------------------------------------
    # Retention Decision
    # ------------------------------------------------------------------

    def evaluate_retention(self, source_type: str, source_id: int,
                           tenant_id: Optional[int] = None,
                           sensitivity_level: str = "internal") -> dict:
        """Evaluate retention decision."""
        if sensitivity_level in (SensitivityLevel.HIGHLY_SENSITIVE,):
            return {"retention_decision": RetentionDecision.DELETE_OR_ERASE,
                    "reason": "highly_sensitive_default"}

        policies = self._session.query(RetentionPolicy).filter_by(
            tenant_id=tenant_id, is_active=True
        ).all()

        for p in policies:
            if not p.source_type or p.source_type == source_type:
                if p.decision == RetentionDecision.RETAIN_UNTIL and p.retention_days:
                    due = datetime.utcnow() + timedelta(days=p.retention_days)
                    return {"retention_decision": RetentionDecision.RETAIN_UNTIL,
                            "due_at": due.isoformat(), "reason": "policy"}
                return {"retention_decision": p.decision, "reason": "policy"}

        return {"retention_decision": RetentionDecision.RETAIN, "reason": "default"}

    # ------------------------------------------------------------------
    # Restriction Management
    # ------------------------------------------------------------------

    def add_restriction(self, person_id: int, restriction_type: str,
                        tenant_id: Optional[int] = None,
                        scope: str = "", reason: str = "",
                        created_by: str = "") -> Restriction:
        r = Restriction(
            tenant_id=tenant_id, person_id=person_id,
            restriction_type=restriction_type,
            scope=scope, reason=reason, created_by=created_by,
        )
        self._session.add(r)
        self._session.commit()
        return r

    def get_active_restrictions(self, person_id: int,
                                tenant_id: Optional[int] = None) -> list[Restriction]:
        q = self._session.query(Restriction).filter_by(
            person_id=person_id, is_active=True
        )
        if tenant_id:
            q = q.filter(Restriction.tenant_id == tenant_id)
        return q.all()

    # ------------------------------------------------------------------
    # Forget / Revocation
    # ------------------------------------------------------------------

    def create_forget_request(self, person_id: int, request_type: str,
                              tenant_id: Optional[int] = None,
                              subject_scope: str = "",
                              reason: str = "") -> ForgetRequest:
        fr = ForgetRequest(
            tenant_id=tenant_id, person_id=person_id,
            request_type=request_type,
            subject_scope=subject_scope, reason=reason,
            status=ForgetRequestStatus.REQUESTED,
        )
        self._session.add(fr)
        self._session.commit()
        return fr

    def approve_forget_request(self, request_id: int,
                               approved_by: str = "") -> dict:
        fr = self._session.get(ForgetRequest, request_id)
        if not fr:
            return {"success": False, "error": "Request not found"}
        if fr.status not in (ForgetRequestStatus.REQUESTED, ForgetRequestStatus.VALIDATING):
            return {"success": False, "error": f"Cannot approve from {fr.status}"}

        fr.status = ForgetRequestStatus.APPROVED
        fr.approved_by = approved_by
        fr.approved_at = datetime.utcnow()
        self._session.commit()

        # Immediately apply restriction to block new memory
        if fr.person_id:
            self.add_restriction(
                person_id=fr.person_id,
                restriction_type="do_not_use_for_memory",
                tenant_id=fr.tenant_id,
                reason=f"Approved forget request #{fr.id}",
                created_by=approved_by,
            )

        return {"success": True, "status": ForgetRequestStatus.APPROVED}

    def mark_execution_pending(self, request_id: int) -> dict:
        fr = self._session.get(ForgetRequest, request_id)
        if not fr:
            return {"success": False, "error": "Request not found"}
        fr.status = ForgetRequestStatus.EXECUTION_PENDING
        self._session.commit()
        return {"success": True, "status": ForgetRequestStatus.EXECUTION_PENDING}

    # ------------------------------------------------------------------
    # Review Queue
    # ------------------------------------------------------------------

    def _create_review_item(self, source_type: str, source_id: int,
                            decision_type: str, reason_code: str,
                            tenant_id: Optional[int], policy_version: int) -> PrivacyReviewItem:
        item = PrivacyReviewItem(
            tenant_id=tenant_id,
            source_type=source_type, source_id=source_id,
            reason_code=reason_code, decision_type=decision_type,
            status="pending", policy_version=policy_version,
        )
        self._session.add(item)
        self._session.flush()
        return item

    def get_pending_reviews(self, tenant_id: Optional[int] = None) -> list[dict]:
        q = self._session.query(PrivacyReviewItem).filter_by(status="pending")
        if tenant_id:
            q = q.filter(PrivacyReviewItem.tenant_id == tenant_id)
        items = q.order_by(PrivacyReviewItem.created_at.desc()).all()
        return [{
            "id": i.id, "source_type": i.source_type, "source_id": i.source_id,
            "reason_code": i.reason_code, "decision_type": i.decision_type,
            "created_at": i.created_at.isoformat() if i.created_at else None,
        } for i in items]

    def approve_review(self, item_id: int, reviewed_by: str = "",
                       note: str = "") -> dict:
        item = self._session.get(PrivacyReviewItem, item_id)
        if not item:
            return {"success": False, "error": "Review item not found"}
        # Check if system non-overridable
        if item.reason_code in SYSTEM_NON_OVERRIDABLE_REASONS:
            system_policy = self._session.query(MemoryEligibilityPolicy).filter_by(
                reason_code=item.reason_code, is_system=True, is_active=True
            ).first()
            if system_policy and system_policy.decision == MemoryEligibility.INELIGIBLE:
                return {"success": False, "error": "System non-overridable: cannot approve"}
        item.status = "approved"
        item.reviewed_by = reviewed_by
        item.reviewed_at = datetime.utcnow()
        item.review_note = note
        self._session.commit()
        return {"success": True, "status": "approved"}

    def deny_review(self, item_id: int, reviewed_by: str = "",
                    note: str = "") -> dict:
        item = self._session.get(PrivacyReviewItem, item_id)
        if not item:
            return {"success": False, "error": "Review item not found"}
        item.status = "denied"
        item.reviewed_by = reviewed_by
        item.reviewed_at = datetime.utcnow()
        item.review_note = note
        self._session.commit()
        return {"success": True, "status": "denied"}

    # ------------------------------------------------------------------
    # Phase 3 Integration
    # ------------------------------------------------------------------

    def evaluate_communication_message(self, message_id: int,
                                       tenant_id: Optional[int] = None,
                                       person_id: Optional[int] = None) -> dict:
        """Evaluate memory eligibility for a Phase 3 ExternalMessage.
        Called after ALLOWED capture and normalization."""
        from app.communication.models import ExternalMessage
        msg = self._session.get(ExternalMessage, message_id)
        if not msg:
            return {"eligible": False, "reason": "message_not_found"}

        if msg.capture_status != "allowed":
            return {"eligible": False, "reason": "capture_not_allowed"}

        return self.evaluate_memory_eligibility(
            source_type="external_message",
            source_id=message_id,
            tenant_id=tenant_id,
            sensitivity_level=SensitivityLevel.INTERNAL,
            person_id=person_id,
        )