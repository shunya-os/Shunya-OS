"""Action Planner — decides whether to answer, ask, execute, automate, or defer."""

from __future__ import annotations

import re

from .types import ActionType, IntelligenceResponse, PlanStep, UserIntent


# ── Business-action detection (E4) ────────────────────────────────────────
# The chat can EXECUTE real business actions (create customer / create
# supplier) through the registered tool handlers — but only with the user's
# explicit confirmation in the SAME message. Without it, the plan carries a
# truthful preview and NOTHING is executed (no silent side effects).

_CREATE_TARGETS = (
    (
        ActionType.CREATE_CUSTOMER,
        "customer",
        re.compile(
            r"\b(?:create|add|register|set\s+up)\s+(?:a\s+|an\s+|the\s+)?(?:new\s+)?"
            r"customer\b\s*(?:(?:named|called|:)\s*)?(?P<name>[^\n]{1,80})",
            re.IGNORECASE,
        ),
    ),
    (
        ActionType.CREATE_SUPPLIER,
        "supplier",
        re.compile(
            r"\b(?:create|add|register|set\s+up)\s+(?:a\s+|an\s+|the\s+)?(?:new\s+)?"
            r"supplier\b\s*(?:(?:named|called|:)\s*)?(?P<name>[^\n]{1,80})",
            re.IGNORECASE,
        ),
    ),
)

_CONFIRM_RE = re.compile(
    r"\b(?:confirm|confirmed|go\s+ahead|do\s+it|proceed)\b", re.IGNORECASE
)


class ActionPlanner:
    """Decides the best course of action from reasoning results."""

    def decide(self, intent: UserIntent, response: IntelligenceResponse) -> list[PlanStep]:
        """Determine the action plan based on intent and reasoning."""
        if response.requires_clarification:
            return [PlanStep(action=ActionType.CLARIFY, description=response.clarification_question)]

        # Explicit business-action requests are planned from the raw input so
        # the runtime can gate them behind an explicit confirmation (E4).
        business = self.detect_business_action(getattr(intent, "raw_input", "") or "")
        if business is not None:
            return [business]

        if response.actions:
            return response.actions

        # Default: answer
        return [PlanStep(action=ActionType.ANSWER, description="Provide information")]

    def detect_business_action(self, raw_input: str) -> PlanStep | None:
        """Detect an explicit create-request; carries its confirmation state.

        Returns None when the message is not an explicit create request or when
        no usable name can be extracted. ``confirmed`` is True only when the
        SAME message includes an explicit confirmation word; the runtime
        executes nothing otherwise (single-turn confirmation, no hidden state).
        """
        text = (raw_input or "").strip()
        if not text:
            return None
        for action, label, regex in _CREATE_TARGETS:
            m = regex.search(text)
            if not m:
                continue
            name = m.group("name").strip()
            # Trim a trailing confirmation/instruction clause from the name
            # ("create customer Acme Ltd — confirm" -> name "Acme Ltd").
            name = re.split(
                r"\b(?:confirm|confirmed|go\s+ahead|do\s+it|proceed)\b",
                name, maxsplit=1, flags=re.IGNORECASE,
            )[0]
            name = name.strip(' .,;:!?"\u201c\u201d\u2018\u2019\'')
            if not name or not re.match(r"[A-Za-z0-9]", name):
                continue
            confirmed = bool(_CONFIRM_RE.search(text))
            preview = (
                f"I can create this {label}: \u201c{name}\u201d. "
                f"Nothing has been created yet. To proceed, resend the request "
                f"including the word confirm (e.g. \u201cconfirm: create {label} {name}\u201d)."
            )
            return PlanStep(
                action=action,
                description=f"Create {label}: {name}",
                parameters={"name": name, "confirmed": confirmed, "preview": preview},
            )
        return None

    def should_execute(self, intent: UserIntent) -> bool:
        """Determine if a command should be executed immediately."""
        return (intent.category.value == "command"
                and intent.confidence >= 0.7
                and intent.urgency in ("critical", "high", "normal"))

    def should_defer(self, intent: UserIntent, confidence: float) -> bool:
        """Determine if we should defer to a human."""
        return (intent.category.value == "unknown"
                or confidence < 0.3
                or intent.ambiguity > 0.7)
