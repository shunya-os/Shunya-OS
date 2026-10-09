"""Behavioral guidance from explicitly-recorded human context (Stage G).

The behavioral effect: an explicitly stated user circumstance (recorded via
POST /api/v1/emotional) changes HOW SHUNYA communicates — tone, pacing,
explanation depth — and nothing else. Rules honoured here:

* Only ACTIVE entries with an explicit assertion are used (what the human
  stated). Corrections and expirations take effect immediately because only
  the service's ACTIVE status is read.
* Never a diagnosis; never surfaced as a mood dashboard; the guidance is for
  the model's behavior and is never quoted back to the user.
* Person identity: matched by the identity's email on the Person record.
* At most TWO guidance lines (calm, not overwhelming).
"""
from __future__ import annotations

MAX_LINES = 2

_GUIDANCE = {
    "frustration": ("The user recently expressed frustration. Be patient and "
                    "direct: short, concrete answers, confirm understanding, "
                    "no lecturing."),
    "uncertainty": ("The user recently expressed uncertainty. Explain clearly, "
                    "step by step, and reassure with concrete next actions."),
    "excitement": ("The user recently expressed excitement. Match the positive "
                   "energy briefly while staying factual."),
    "urgent": ("The user recently expressed urgency. Lead with the most direct "
               "path to the answer; skip optional extras."),
    "defer": ("The user asked to defer something. Respect that; do not push or "
              "re-raise it unprompted."),
}


def build_human_context_guidance(identity_email: str = "", tenant_id=None) -> str:
    """Return short, neutral behavior guidance, or "" when none exists.

    Never raises: human-context enrichment must not break the chat path.
    """
    email = (identity_email or "").strip().lower()
    if not email:
        return ""
    try:
        from sqlalchemy import func

        from app.human_context.emotional import (
            EmotionalContextService,
            EmotionalStatus,
        )
        from app.models import PersonIdentity

        match = (
            PersonIdentity.query
            .filter(PersonIdentity.identity_type == "email")
            .filter(func.lower(PersonIdentity.normalized_value) == email)
            .first()
        ) or (
            PersonIdentity.query
            .filter(func.lower(PersonIdentity.identity_value) == email)
            .first()
        )
        if not match:
            return ""
        person_id = match.person_id

        service = EmotionalContextService()
        listing = service.list(
            tenant_id=int(tenant_id) if tenant_id else None,
            person_id=person_id,
            status=EmotionalStatus.ACTIVE,
            limit=10,
        )

        lines = []
        seen = set()
        for item in listing.get("items", []):
            et = item.get("expression_type") or ""
            if et in seen:
                continue
            guidance = _GUIDANCE.get(et)
            if guidance:
                seen.add(et)
                lines.append(guidance)
            if len(lines) >= MAX_LINES:
                break
        return " ".join(lines)
    except Exception:  # noqa: BLE001 — guidance is additive, never blocking
        import logging
        logging.getLogger(__name__).warning(
            "human-context guidance build failed", exc_info=True)
        return ""