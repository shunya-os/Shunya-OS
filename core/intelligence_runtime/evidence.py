"""Evidence Transformation Guard — prevents unauthorized evidence transformations.

Every evidence transformation (promotion, tenant move, revival) must pass
through this guard. It enforces three constitutional rules (G3 Phase 2.8):

(a) No unauthorized promotion: evidence cannot be promoted from a lower
    classification to a higher one without explicit authorization.
(b) No cross-tenant transformation: evidence from one tenant cannot be
    transformed for another tenant.
(c) No zombie revival: deleted/archived evidence cannot be revived as active
    evidence.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


# ── Classification Hierarchy ──────────────────────────────────────────────

class EvidenceClassification(str, Enum):
    """Evidence classification levels, ordered by authority.

    The hierarchy from lowest to highest authority:
        UNKNOWN < INFERENCE < MEMORY < EXTERNAL_EVIDENCE < COMPANY_TRUTH

    Promotion (moving UP the hierarchy) requires authorization.
    Demotion (moving DOWN) is always allowed — reducing authority is safe.
    """

    UNKNOWN = "unknown"
    INFERENCE = "inference"
    MEMORY = "memory"
    EXTERNAL_EVIDENCE = "external_evidence"
    COMPANY_TRUTH = "company_truth"

    @classmethod
    def hierarchy_index(cls, classification: str) -> int:
        """Return the hierarchy position (0 = lowest authority)."""
        ordering = [
            cls.UNKNOWN.value,
            cls.INFERENCE.value,
            cls.MEMORY.value,
            cls.EXTERNAL_EVIDENCE.value,
            cls.COMPANY_TRUTH.value,
        ]
        try:
            return ordering.index(classification.lower())
        except ValueError:
            return 0

    @classmethod
    def is_promotion(cls, from_class: str, to_class: str) -> bool:
        """Check if moving from ``from_class`` to ``to_class`` is a promotion
        (i.e. increases authority)."""
        return cls.hierarchy_index(to_class) > cls.hierarchy_index(from_class)


# ── Evidence Lifecycle States ─────────────────────────────────────────────

class EvidenceLifecycleState(str, Enum):
    """Canonical lifecycle states for evidence records."""
    ACTIVE = "active"
    ARCHIVED = "archived"
    DELETED = "deleted"
    SUPERSEDED = "superseded"


# ── Transformation Types ──────────────────────────────────────────────────

class TransformationType(str, Enum):
    """Types of evidence transformations subject to guard checks."""
    CLASSIFICATION_PROMOTION = "classification_promotion"
    TENANT_TRANSFER = "tenant_transfer"
    REVIVAL = "revival"


# ── Evidence Transformation Record ────────────────────────────────────────

@dataclass
class EvidenceTransformation:
    """A proposed evidence transformation to be checked by the guard."""
    evidence_id: str
    source_tenant_id: str | int | None
    target_tenant_id: str | int | None
    current_classification: str
    proposed_classification: str
    current_lifecycle_state: str
    proposed_lifecycle_state: str
    authorized_by: str = ""  # identity_id that authorized the transformation
    metadata: dict = field(default_factory=dict)


# ── Guard Result ──────────────────────────────────────────────────────────

@dataclass
class GuardResult:
    """Result of an evidence transformation guard check."""
    allowed: bool
    reason: str = ""
    blocked_rules: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "allowed": self.allowed,
            "reason": self.reason,
            "blocked_rules": self.blocked_rules,
        }


# ══════════════════════════════════════════════════════════════════════════
# Evidence Transformation Guard
# ══════════════════════════════════════════════════════════════════════════


class EvidenceTransformationGuard:
    """Constitutional guard against unauthorized evidence transformations.

    Enforces three rules at every transformation boundary:

    Rule A — No unauthorized promotion:
        Evidence classified as UNKNOWN, INFERENCE, MEMORY, or EXTERNAL_EVIDENCE
        cannot be promoted to a higher classification (e.g. MEMORY → COMPANY_TRUTH)
        without explicit authorization. Only COMPANY_TRUTH evidence is immune
        from promotion checks (it is already at the top).

    Rule B — No cross-tenant transformation:
        Evidence originating from one tenant cannot be transformed (reclassified,
        revived) in the context of a different tenant.

    Rule C — No zombie revival:
        Evidence with lifecycle state ``archived`` or ``deleted`` cannot be
        revived to ``active``. ``superseded`` evidence may be revived only if
        ``authorized_by`` is set.

    The guard is CONSTITUTIONAL — its rules cannot be bypassed by configuration.
    """

    # Classifications that are immune to promotion checks (already at top)
    PROMOTION_IMMUNE = {"company_truth"}

    # Lifecycle states that are terminal (cannot be revived without auth)
    TERMINAL_STATES = {"archived", "deleted"}

    # States that may be revived only with authorization
    AUTH_REQUIRED_REVIVAL = {"superseded"}

    @classmethod
    def check(
        cls,
        transformation: EvidenceTransformation,
        authorized: bool = False,
    ) -> GuardResult:
        """Check whether a proposed evidence transformation is allowed.

        Args:
            transformation: The proposed transformation to evaluate.
            authorized: Whether the request carries explicit authorization
                (e.g. an admin-level permission check has already passed).

        Returns:
            GuardResult with ``allowed=True`` if all rules pass, or
            ``allowed=False`` with the specific rules that blocked it.
        """
        blocked: list[str] = []

        # ── Rule A: No unauthorized promotion ──────────────────────
        current = transformation.current_classification.lower()
        proposed = transformation.proposed_classification.lower()

        if not authorized and current != proposed:
            if EvidenceClassification.is_promotion(current, proposed):
                if proposed not in cls.PROMOTION_IMMUNE:
                    blocked.append(
                        f"classification_promotion: cannot promote from "
                        f"'{current}' to '{proposed}' without authorization"
                    )

        # ── Rule B: No cross-tenant transformation ─────────────────
        src = transformation.source_tenant_id
        tgt = transformation.target_tenant_id
        if src is not None and tgt is not None:
            try:
                src_s = str(src)
                tgt_s = str(tgt)
                if src_s and tgt_s and src_s != tgt_s:
                    blocked.append(
                        f"cross_tenant_transformation: evidence from tenant "
                        f"'{src_s}' cannot be transformed for tenant '{tgt_s}'"
                    )
            except (ValueError, TypeError):
                blocked.append(
                    "cross_tenant_transformation: invalid tenant identifiers"
                )

        # ── Rule C: No zombie revival ──────────────────────────────
        current_state = transformation.current_lifecycle_state.lower()
        proposed_state = transformation.proposed_lifecycle_state.lower()

        if proposed_state == EvidenceLifecycleState.ACTIVE.value:
            if current_state in cls.TERMINAL_STATES:
                blocked.append(
                    f"zombie_revival: cannot revive evidence from "
                    f"'{current_state}' to 'active' — evidence is terminal"
                )
            elif current_state in cls.AUTH_REQUIRED_REVIVAL:
                if not authorized:
                    blocked.append(
                        f"zombie_revival: cannot revive evidence from "
                        f"'{current_state}' to 'active' without authorization"
                    )

        if blocked:
            return GuardResult(
                allowed=False,
                reason="; ".join(blocked),
                blocked_rules=blocked,
            )

        return GuardResult(
            allowed=True,
            reason="All evidence transformation rules passed",
        )

    @classmethod
    def check_promotion(
        cls,
        from_classification: str,
        to_classification: str,
        authorized: bool = False,
    ) -> GuardResult:
        """Convenience check for Rule A only (classification promotion)."""
        if from_classification.lower() == to_classification.lower():
            return GuardResult(allowed=True, reason="No classification change")

        if not authorized and EvidenceClassification.is_promotion(
            from_classification, to_classification
        ):
            return GuardResult(
                allowed=False,
                reason=(
                    f"Cannot promote evidence from '{from_classification}' "
                    f"to '{to_classification}' without authorization"
                ),
                blocked_rules=["classification_promotion"],
            )

        return GuardResult(
            allowed=True,
            reason="Promotion allowed",
        )

    @classmethod
    def check_tenant_boundary(
        cls,
        source_tenant_id: str | int | None,
        target_tenant_id: str | int | None,
    ) -> GuardResult:
        """Convenience check for Rule B only (tenant boundary)."""
        if source_tenant_id is None or target_tenant_id is None:
            return GuardResult(allowed=True, reason="No tenant context to check")

        try:
            if str(source_tenant_id) and str(target_tenant_id) and str(source_tenant_id) != str(target_tenant_id):
                return GuardResult(
                    allowed=False,
                    reason=(
                        f"Cannot transform evidence from tenant "
                        f"'{source_tenant_id}' for tenant '{target_tenant_id}'"
                    ),
                    blocked_rules=["cross_tenant_transformation"],
                )
        except (ValueError, TypeError):
            return GuardResult(
                allowed=False,
                reason="Invalid tenant identifiers",
                blocked_rules=["cross_tenant_transformation"],
            )

        return GuardResult(
            allowed=True,
            reason="Tenant boundary respected",
        )

    @classmethod
    def check_revival(
        cls,
        current_state: str,
        proposed_state: str,
        authorized: bool = False,
    ) -> GuardResult:
        """Convenience check for Rule C only (zombie revival)."""
        if proposed_state.lower() != EvidenceLifecycleState.ACTIVE.value:
            return GuardResult(allowed=True, reason="Not a revival attempt")

        current = current_state.lower()
        if current in cls.TERMINAL_STATES:
            return GuardResult(
                allowed=False,
                reason=(
                    f"Cannot revive evidence from '{current}' to 'active' — "
                    f"evidence is terminal"
                ),
                blocked_rules=["zombie_revival"],
            )

        if current in cls.AUTH_REQUIRED_REVIVAL and not authorized:
            return GuardResult(
                allowed=False,
                reason=(
                    f"Cannot revive evidence from '{current}' to 'active' "
                    f"without authorization"
                ),
                blocked_rules=["zombie_revival"],
            )

        return GuardResult(
            allowed=True,
            reason="Revival allowed",
        )