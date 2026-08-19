"""
SHUNYA — Correction, Preference & Learning Service.

Gate 3.3: Governed correction, preference persistence, and safe learning.

A correction must:
1. preserve the original claim/history
2. record the correction as a governed event
3. identify what was corrected
4. not silently mutate history
5. not automatically treat every human statement as universal truth
6. respect tenant and authorization boundaries

Learning distinctions:
- immutable/historical truth — never modified
- current state — updated by evidence
- user preference — scoped to tenant/user
- learned pattern — derived from repeated observations
- model inference — never becomes evidence
- uncertain hypothesis — explicit confidence
"""

from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════
# Correction Types
# ═══════════════════════════════════════════════════════════════════


class CorrectionType(str, Enum):
    FACTUAL = "factual"               # "This is wrong" — factual correction
    PREFERENCE = "preference"         # "My preference is different"
    FRESHNESS = "freshness"           # "That information is outdated"
    SOURCE = "source"                 # "Do not use this source"
    VALUE = "value"                   # "Use this corrected value"
    COMPLETE = "complete"             # "This is missing information"
    DISAGREE = "disagree"             # "I disagree with this conclusion"


# ═══════════════════════════════════════════════════════════════════
# Correction Record
# ═══════════════════════════════════════════════════════════════════


@dataclass
class CorrectionRecord:
    """A governed correction — preserves history and identifies what
    was corrected."""
    correction_id: str = ""
    correction_type: CorrectionType = CorrectionType.FACTUAL
    target_claim: str = ""          # What was claimed
    original_value: str = ""        # What SHUNYA said
    corrected_value: str = ""       # What the user corrected to
    reason: str = ""                # User's explanation
    tenant_id: int = 0
    actor_id: str = ""
    source: str = "user"            # "user" | "system" | "evidence"
    scope: str = "tenant"           # "tenant" | "user" | "global" (never global without governance)
    created_at: str = ""
    superseded: bool = False         # Later corrections can supersede

    def __post_init__(self) -> None:
        if not self.correction_id:
            self.correction_id = f"corr_{uuid.uuid4().hex[:16]}"
        if not self.created_at:
            self.created_at = datetime.now(timezone.utc).isoformat()


# ═══════════════════════════════════════════════════════════════════
# Preference Record
# ═══════════════════════════════════════════════════════════════════


@dataclass
class PreferenceRecord:
    """A scoped user preference — affects only the appropriate scope."""
    preference_id: str = ""
    key: str = ""                     # e.g., "source:web_search" | "risk_threshold"
    value: str = ""
    tenant_id: int = 0
    actor_id: str = ""
    scope: str = "tenant"            # "tenant" | "user"
    created_at: str = ""
    active: bool = True

    def __post_init__(self) -> None:
        if not self.preference_id:
            self.preference_id = f"pref_{uuid.uuid4().hex[:16]}"
        if not self.created_at:
            self.created_at = datetime.now(timezone.utc).isoformat()


# ═══════════════════════════════════════════════════════════════════
# Outcome Record — connects recommendation to observed outcome
# ═══════════════════════════════════════════════════════════════════


@dataclass
class OutcomeRecord:
    """Connects a recommendation to an observed outcome."""
    outcome_id: str = ""
    recommendation_id: str = ""
    recommendation_summary: str = ""
    action_taken: str = ""            # "accepted" | "rejected" | "modified" | "no_action"
    result: str = ""                  # "success" | "failure" | "partial" | "unknown"
    outcome_description: str = ""
    tenant_id: int = 0
    actor_id: str = ""
    created_at: str = ""

    def __post_init__(self) -> None:
        if not self.outcome_id:
            self.outcome_id = f"out_{uuid.uuid4().hex[:16]}"
        if not self.created_at:
            self.created_at = datetime.now(timezone.utc).isoformat()


# ═══════════════════════════════════════════════════════════════════
# CorrectionService — governs all corrections and learning
# ═══════════════════════════════════════════════════════════════════


class CorrectionService:
    """Canonical correction service.

    Governs corrections, preferences, and outcome feedback.
    Learning is always safe — never silently mutates truth.
    """

    def __init__(self):
        self._corrections: dict[str, CorrectionRecord] = {}
        self._preferences: dict[str, PreferenceRecord] = {}
        self._outcomes: dict[str, OutcomeRecord] = {}

    # ── Corrections ──────────────────────────────────────────────────

    def record_correction(self, correction: CorrectionRecord) -> str:
        """Record a governed correction. Original history is preserved."""
        self._corrections[correction.correction_id] = correction
        logger.info(
            "Correction recorded: %s (type=%s, target=%s)",
            correction.correction_id[:12], correction.correction_type.value,
            correction.target_claim[:50],
        )
        return correction.correction_id

    def get_correction(self, correction_id: str) -> Optional[CorrectionRecord]:
        return self._corrections.get(correction_id)

    def get_corrections_for_claim(self, claim: str, tenant_id: int = 0) -> list[CorrectionRecord]:
        """Get all corrections for a claim, tenant-scoped."""
        return [
            c for c in self._corrections.values()
            if c.target_claim == claim and (c.tenant_id == tenant_id or tenant_id == 0)
        ]

    def get_all_corrections(self, tenant_id: int = 0) -> list[CorrectionRecord]:
        """Get all corrections, tenant-scoped."""
        return [
            c for c in self._corrections.values()
            if c.tenant_id == tenant_id or tenant_id == 0
        ]

    # ── Preferences ──────────────────────────────────────────────────

    def record_preference(self, preference: PreferenceRecord) -> str:
        """Record a scoped user preference."""
        self._preferences[preference.preference_id] = preference
        logger.info(
            "Preference recorded: %s (key=%s, scope=%s)",
            preference.preference_id[:12], preference.key, preference.scope,
        )
        return preference.preference_id

    def get_preference(self, key: str, tenant_id: int = 0,
                       actor_id: str = "") -> Optional[PreferenceRecord]:
        """Get the most relevant preference for a key."""
        # Prefer user-scoped, then tenant-scoped
        candidates = [
            p for p in self._preferences.values()
            if p.key == key and p.active
            and (p.tenant_id == tenant_id or tenant_id == 0)
        ]
        # Prefer user-scoped
        user_prefs = [p for p in candidates if p.actor_id == actor_id and p.scope == "user"]
        if user_prefs:
            return sorted(user_prefs, key=lambda x: x.created_at, reverse=True)[0]
        # Then tenant-scoped
        tenant_prefs = [p for p in candidates if p.scope == "tenant"]
        if tenant_prefs:
            return sorted(tenant_prefs, key=lambda x: x.created_at, reverse=True)[0]
        return None

    def get_all_preferences(self, tenant_id: int = 0,
                             actor_id: str = "") -> list[PreferenceRecord]:
        """Get all preferences for a tenant/user."""
        return [
            p for p in self._preferences.values()
            if p.active and (p.tenant_id == tenant_id or tenant_id == 0)
            and (not actor_id or p.actor_id == actor_id)
        ]

    # ── Outcomes ─────────────────────────────────────────────────────

    def record_outcome(self, outcome: OutcomeRecord) -> str:
        """Record an observed outcome for a recommendation."""
        self._outcomes[outcome.outcome_id] = outcome
        logger.info(
            "Outcome recorded: %s (rec=%s, action=%s, result=%s)",
            outcome.outcome_id[:12], outcome.recommendation_id[:12],
            outcome.action_taken, outcome.result,
        )
        return outcome.outcome_id

    def get_outcome(self, outcome_id: str) -> Optional[OutcomeRecord]:
        return self._outcomes.get(outcome_id)

    def get_outcomes_for_recommendation(self, recommendation_id: str) -> list[OutcomeRecord]:
        """Get all outcomes for a recommendation."""
        return [
            o for o in self._outcomes.values()
            if o.recommendation_id == recommendation_id
        ]

    def get_all_outcomes(self, tenant_id: int = 0) -> list[OutcomeRecord]:
        """Get all outcomes, tenant-scoped."""
        return [
            o for o in self._outcomes.values()
            if o.tenant_id == tenant_id or tenant_id == 0
        ]

    # ── Security ─────────────────────────────────────────────────────

    def is_cross_tenant(self, record: CorrectionRecord | PreferenceRecord,
                        request_tenant_id: int) -> bool:
        """Check if a record would be cross-tenant."""
        return record.tenant_id != request_tenant_id and record.tenant_id != 0

    def validate_correction(self, correction: CorrectionRecord,
                            request_tenant_id: int) -> tuple[bool, str]:
        """Validate a correction before recording."""
        if self.is_cross_tenant(correction, request_tenant_id):
            return False, "Cross-tenant correction not allowed"
        if correction.scope == "global":
            return False, "Global scope corrections require governance approval"
        return True, ""

    # ── Staleness ────────────────────────────────────────────────────

    @staticmethod
    def is_stale(timestamp: str, max_age_seconds: int = 86400) -> bool:
        """Check if a timestamp is stale."""
        try:
            ts = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
            age = (datetime.now(timezone.utc) - ts).total_seconds()
            return age > max_age_seconds
        except (ValueError, TypeError):
            return True

    # ── Clear (for testing) ──────────────────────────────────────────

    def clear(self) -> None:
        self._corrections.clear()
        self._preferences.clear()
        self._outcomes.clear()


# ── Module-level singleton ──────────────────────────────────────────

_service: Optional[CorrectionService] = None


def get_correction_service() -> CorrectionService:
    global _service
    if _service is None:
        _service = CorrectionService()
    return _service


def reset_correction_service() -> None:
    global _service
    _service = None


__all__ = [
    "CorrectionType",
    "CorrectionRecord",
    "PreferenceRecord",
    "OutcomeRecord",
    "CorrectionService",
    "get_correction_service",
    "reset_correction_service",
]