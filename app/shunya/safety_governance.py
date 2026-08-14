"""SHUNYA Safety Governance — Age verification + explicit content policy.

This is the canonical SHUNYA safety boundary. Every AI interaction,
tool action, and integration must pass through this gate.

SHUNYA policy ALWAYS takes precedence over the underlying LLM's permissiveness.
"""
import re
import hashlib
import logging
from datetime import datetime
from typing import Optional

logger = logging.getLogger(__name__)

# ── Policy levels ──────────────────────────────────────────────────────

class SafetyPolicyLevel:
    ALLOW = "allow"
    WARN = "warn"
    BLOCK = "block"
    REVIEW = "review"


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
    ):
        self.allowed = allowed
        self.reason = reason
        self.level = level
        self.action = action
        self.blocked_pattern = blocked_pattern
        self.timestamp = datetime.utcnow().isoformat()

    def to_dict(self) -> dict:
        return {
            "allowed": self.allowed,
            "reason": self.reason,
            "level": self.level,
            "action": self.action,
            "blocked_pattern": self.blocked_pattern,
            "timestamp": self.timestamp,
        }


# ── Age verification ───────────────────────────────────────────────────

def check_age_verification(identity_id: str, tenant_id: int) -> tuple[bool, str]:
    """Check if the user's age is verified and eligible.

    Returns (is_verified, reason). Unverified identity follows the SAFE policy
    (treated as not verified → restricted content blocked).
    """
    from app.auth import TeamMember

    tm = None
    try:
        tm = TeamMember.query.filter_by(id=identity_id).first()
    except Exception:
        pass
    if not tm:
        return False, "Identity not found"

    # If no explicit age/verification field, default to UNVERIFIED (safe policy)
    verified = getattr(tm, "is_verified", None) or getattr(tm, "age_verified", None)
    age = getattr(tm, "age", None)
    if not verified:
        return False, "Age not verified"
    if age is not None and age < 18:
        return False, "User is under 18"
    return True, "Age verified"


# ── Content safety check ───────────────────────────────────────────────

def check_content_safety(text: str, age_verified: bool = False) -> SafetyVerdict:
    """Check text against safety policies.

    Returns SafetyVerdict: allowed=True/False with reason.
    """
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
                    reason="Age verification required for this content",
                    level=SafetyPolicyLevel.REVIEW,
                    action="require_age_verification",
                    blocked_pattern=pattern.pattern[:60],
                )
            # Age verified — warn but allow
            return SafetyVerdict(
                allowed=True,
                reason="Explicit content: age verified, proceed with warning",
                level=SafetyPolicyLevel.WARN,
                action="warn",
                blocked_pattern=pattern.pattern[:60],
            )

    # Everything passed
    return SafetyVerdict(
        allowed=True,
        reason="Safety check passed",
        level=SafetyPolicyLevel.ALLOW,
        action="proceed",
    )


# ── Full governance check ──────────────────────────────────────────────

def check_safety_governance(
    text: str,
    identity_id: str = "",
    tenant_id: int = 0,
) -> SafetyVerdict:
    """Full safety governance check: age + content safety.

    Called before every AI interaction, tool use, and integration action.
    """
    # Check age verification
    age_verified = False
    if identity_id and tenant_id:
        age_verified, _ = check_age_verification(identity_id, tenant_id)

    # Content safety check
    return check_content_safety(text, age_verified=age_verified)