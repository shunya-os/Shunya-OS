"""SHUNYA Safety Governance — age verification + explicit content policy.

This is the canonical SHUNYA safety boundary. Every AI interaction,
tool action, and integration must pass through this gate.

SHUNYA policy ALWAYS takes precedence over the underlying LLM's permissiveness.

Policy states (explicit, never inferred):
- UNKNOWN     — identity cannot be resolved → treated as unverified (fail closed)
- UNVERIFIED  — account exists but has no age proof → restricted content blocked
- NOT_IN_TENANT — identity is not an active member of the requested tenant
                 → age check does not proceed (fail closed)
- UNDERAGE    — verified birth date shows age < 18 → blocked
- VERIFIED    — age proof recorded (age_verified=True) or birth date shows
                age >= 18 → explicit content allowed with warning

Fail-closed rule: if the governance component itself is unavailable (raised
exception), every caller MUST block the request (503), never allow it.
"""
import re
import hashlib
import logging
from datetime import datetime, timezone, date
from typing import Optional, Tuple

logger = logging.getLogger(__name__)

# ── Policy levels ──────────────────────────────────────────────────────

class SafetyPolicyLevel:
    ALLOW = "allow"
    WARN = "warn"
    BLOCK = "block"
    REVIEW = "review"


class AgePolicyState:
    UNKNOWN = "unknown"
    UNVERIFIED = "unverified"
    NOT_IN_TENANT = "not_in_tenant"
    UNDERAGE = "underage"
    VERIFIED = "verified"


MINIMUM_AGE = 18


# ── Explicit content patterns ──────────────────────────────────────────

EXPLICIT_PATTERNS = [
    re.compile(r"\b(adult\s*content|nsfw|explicit|pornographic)\b", re.IGNORECASE),
    re.compile(r"\b(sexual\s*explicit|hardcore|xxx|erotic)\b", re.IGNORECASE),
]

PROHIBITED_PATTERNS = [
    re.compile(r"\b(generate|create|make|produce)\s+.*(?:child|minor|underage|weapon|explosive|drug|poison|illegal)\b", re.IGNORECASE),
    re.compile(r"\b(how\s+to\s+make|how\s+to\s+build|instructions?\s+for)\s+.*(?:weapon|explosive|bomb|drug|poison|illegal)\b", re.IGNORECASE),
    re.compile(r"\b(instructions?|guide|method|technique)\s+.*(?:self.?harm|suicide|harm)\b", re.IGNORECASE),
    re.compile(r"\b(csam|child\s*(?:abuse|porn|exploit)|underage\s*(?:content|sexual))\b", re.IGNORECASE),
]

PROMPT_INJECTION_PATTERNS = [
    re.compile(r"\b(ignore\s+(?:all\s+)?(?:previous|above|system|instructions|safety))\b", re.IGNORECASE),
    re.compile(r"\b(forget\s+(?:all\s+)?(?:previous|safety|rules))\b", re.IGNORECASE),
    re.compile(r"\b(you\s+are\s+(?:not\s+)?(?:a\s+)?(?:bounded|unbounded|free|unrestricted))\b", re.IGNORECASE),
    re.compile(r"\b(override\s+(?:safety|policy|governance))\b", re.IGNORECASE),
    re.compile(r"\b(act\s+as\s+.*(?:without\s+(?:any\s+)?restrictions|unfiltered))\b", re.IGNORECASE),
]


# ── Safety Verdict ─────────────────────────────────────────────────────

class SafetyVerdict:
    """Result of safety governance check."""

    def __init__(
        self,
        allowed: bool,
        reason: str = "",
        level: str = SafetyPolicyLevel.ALLOW,
        action: str = "proceed",
        blocked_pattern: str = "",
        age_policy_state: str = "",
    ):
        self.allowed = allowed
        self.reason = reason
        self.level = level
        self.action = action
        self.blocked_pattern = blocked_pattern
        self.age_policy_state = age_policy_state
        self.timestamp = datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> dict:
        return {
            "allowed": self.allowed,
            "reason": self.reason,
            "level": self.level,
            "action": self.action,
            "blocked_pattern": self.blocked_pattern,
            "age_policy_state": self.age_policy_state,
            "timestamp": self.timestamp,
        }


# ── Identity resolution ────────────────────────────────────────────────

def _resolve_team_member(identity_id):
    """Resolve the TeamMember row for a canonical identity_id.

    Search order (canonical first):
      1. TeamMember.identity_id == identity_id  (canonical sid_xxx string)
      2. TeamMember.id == int(identity_id)       (legacy numeric fallback)
      3. TeamMember.email == identity_id         (legacy email fallback)

    None is returned when the identity cannot be resolved — the caller must
    treat that as UNKNOWN and fail closed. Errors propagate to the caller
    (fail closed at the request boundary); they are never silently swallowed
    into a "not found".
    """
    if not identity_id:
        return None
    from app.auth import TeamMember

    tm = TeamMember.query.filter_by(identity_id=str(identity_id)).first()
    if tm is not None:
        return tm
    if str(identity_id).isdigit():
        tm = TeamMember.query.filter_by(id=int(identity_id)).first()
        if tm is not None:
            return tm
    if isinstance(identity_id, str) and "@" in identity_id:
        tm = TeamMember.query.filter_by(email=identity_id.strip().lower()).first()
        if tm is not None:
            return tm
    return None


def _is_tenant_member(identity_id: str, team_member, tenant_id) -> bool:
    """Whether the identity is an active member of the requested tenant (org).

    Membership is matched on canonical identity_id OR the account email —
    the same linkage the signin flow uses (org memberships were historically
    bridged by email). tenant_id 0/None means personal scope: no membership
    requirement applies.
    """
    if not tenant_id:
        return True
    try:
        tenant_id = int(tenant_id)
    except (TypeError, ValueError):
        return False
    if tenant_id <= 0:
        return True
    from app.models import OrgMember

    q = OrgMember.query.filter_by(organization_id=tenant_id, is_active=True)
    member = q.filter(OrgMember.identity_id == str(identity_id)).first()
    if member is not None:
        return True
    member = q.filter(OrgMember.email.ilike(team_member.email or "")).first()
    return member is not None


def _age_from_birth_date(birth_date) -> Optional[int]:
    """Whole years from birth_date to today, or None when unset/invalid."""
    if not birth_date:
        return None
    try:
        today = date.today()
        bd = birth_date
        if hasattr(bd, "date"):  # datetime → date
            bd = bd.date()
        years = today.year - bd.year - ((today.month, today.day) < (bd.month, bd.day))
        return years
    except Exception:  # invalid date value — treat as unprovable, not verified
        return None


# ── Age verification ───────────────────────────────────────────────────

def check_age_verification(identity_id: str, tenant_id) -> Tuple[bool, str]:
    """Check the user's age verification state against SHUNYA policy.

    Returns (is_verified, reason). Every non-verified state is fail-closed:
    UNKNOWN, UNVERIFIED, NOT_IN_TENANT and UNDERAGE all deny.
    """
    from app.auth import TeamMember

    if not identity_id:
        return False, "Identity not provided"
    tm = _resolve_team_member(identity_id)
    if tm is None:
        return False, "Identity not found (unknown identity — fail closed)"

    if not _is_tenant_member(str(identity_id), tm, tenant_id):
        return False, "Identity is not an active member of this tenant (fail closed)"

    age = _age_from_birth_date(getattr(tm, "birth_date", None))
    if age is not None and age < MINIMUM_AGE:
        return False, f"User is under {MINIMUM_AGE}"

    age_verified = bool(getattr(tm, "age_verified", False))
    if age_verified:
        return True, "Age verified"
    if age is not None and age >= MINIMUM_AGE:
        return True, "Age verified (birth date shows adult age)"
    return False, "Age not verified"


# ── Content safety check ───────────────────────────────────────────────

def check_content_safety(text: str, age_verified: bool = False,
                         age_deny_reason: str = "", age_policy_state: str = "") -> SafetyVerdict:
    """Check text against safety policies.

    Returns SafetyVerdict: allowed=True/False with reason.
    """
    if not text or not text.strip():
        return SafetyVerdict(
            allowed=True, reason="Empty text — nothing to check",
            level=SafetyPolicyLevel.ALLOW, action="proceed",
        )

    # 1. Check prohibited patterns first (always blocked)
    for pattern in PROHIBITED_PATTERNS:
        match = pattern.search(text)
        if match:
            return SafetyVerdict(
                allowed=False,
                reason="Prohibited content detected",
                level=SafetyPolicyLevel.BLOCK,
                action="blocked",
                blocked_pattern=pattern.pattern[:60],
            )

    # 2. Check prompt injection
    for pattern in PROMPT_INJECTION_PATTERNS:
        match = pattern.search(text)
        if match:
            return SafetyVerdict(
                allowed=False,
                reason="Policy override attempt detected",
                level=SafetyPolicyLevel.BLOCK,
                action="blocked",
                blocked_pattern=pattern.pattern[:60],
            )

    # 3. Check explicit content
    for pattern in EXPLICIT_PATTERNS:
        match = pattern.search(text)
        if match:
            if not age_verified:
                return SafetyVerdict(
                    allowed=False,
                    reason=age_deny_reason or "Age verification required for this content",
                    level=SafetyPolicyLevel.REVIEW,
                    action="require_age_verification",
                    blocked_pattern=pattern.pattern[:60],
                    age_policy_state=age_policy_state or AgePolicyState.UNVERIFIED,
                )
            # Age verified — warn but allow
            return SafetyVerdict(
                allowed=True,
                reason="Explicit content: age verified, proceed with warning",
                level=SafetyPolicyLevel.WARN,
                action="warn",
                blocked_pattern=pattern.pattern[:60],
                age_policy_state=AgePolicyState.VERIFIED,
            )

    # Everything passed
    return SafetyVerdict(
        allowed=True,
        reason="Safety check passed",
        level=SafetyPolicyLevel.ALLOW,
        action="proceed",
    )


def _age_policy_state(reason: str) -> str:
    """Map a check_age_verification denial reason to its policy state."""
    r = reason.lower()
    if r.startswith("identity not found") or r.startswith("identity not provided"):
        return AgePolicyState.UNKNOWN
    if "not an active member" in r:
        return AgePolicyState.NOT_IN_TENANT
    if "under" in r:
        return AgePolicyState.UNDERAGE
    return AgePolicyState.UNVERIFIED


# ── Full governance check ──────────────────────────────────────────────

def check_safety_governance(
    text: str,
    identity_id: str = "",
    tenant_id=0,
) -> SafetyVerdict:
    """Full safety governance check: age + content safety.

    Called before every AI interaction, tool use, and integration action.
    """
    # Check age verification
    age_verified = False
    age_deny_reason = ""
    age_state = ""
    try:
        if identity_id:
            age_verified, age_deny_reason = check_age_verification(identity_id, tenant_id)
            if not age_verified:
                age_state = _age_policy_state(age_deny_reason)
    except Exception:
        # Age proof cannot be evaluated — fail closed (unverified).
        logger.warning("Age verification evaluation failed — treating as unverified", exc_info=True)
        age_verified = False
        age_deny_reason = "Age verification unavailable — treated as unverified"

    # Content safety check
    return check_content_safety(
        text,
        age_verified=age_verified,
        age_deny_reason=age_deny_reason,
        age_policy_state=age_state,
    )


# ── Request-bound helper for routes ────────────────────────────────────

def check_request_safety(text: str, identity_id: str = "", tenant_id=0):
    """Evaluate safety for an inbound AI request.

    Returns None when the request may proceed, otherwise
    (payload_dict, status_code): 403 when SHUNYA policy blocks the request,
    503 when the governance component is unavailable (fail closed).
    """
    try:
        verdict = check_safety_governance(text, identity_id, tenant_id)
    except Exception as exc:
        logger.warning("Safety governance unavailable — blocking request: %s", exc)
        return (
            {
                "error": "Safety governance unavailable — request blocked",
                "safety": {
                    "allowed": False,
                    "reason": str(exc),
                    "level": SafetyPolicyLevel.BLOCK,
                    "action": "blocked",
                },
            },
            503,
        )
    if not verdict.allowed:
        return (
            {
                "error": "Request blocked by SHUNYA safety policy",
                "safety": verdict.to_dict(),
                "blocked_pattern": verdict.blocked_pattern,
            },
            403,
        )
    return None


# ── Output-side check (LLM responses) ──────────────────────────────────

def check_output_safety(text: str) -> SafetyVerdict:
    """Gate an LLM-produced response.

    Prohibited content and policy-override language in model output are
    always blocked regardless of the caller's age verification: the model
    must never produce content the policy forbids.
    """
    if not text or not text.strip():
        return SafetyVerdict(
            allowed=True, reason="Empty output", level=SafetyPolicyLevel.ALLOW, action="proceed",
        )
    for pattern in PROHIBITED_PATTERNS + PROMPT_INJECTION_PATTERNS:
        match = pattern.search(text)
        if match:
            return SafetyVerdict(
                allowed=False,
                reason="Prohibited content in model output",
                level=SafetyPolicyLevel.BLOCK,
                action="blocked",
                blocked_pattern=pattern.pattern[:60],
            )
    return SafetyVerdict(
        allowed=True, reason="Output safety check passed",
        level=SafetyPolicyLevel.ALLOW, action="proceed",
    )