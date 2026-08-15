"""Backward-compatible execution state constants.

These are plain string constants, NOT lifecycle enums.
No progression is implied. Execution = f(State, Intent, Evidence, Time).
"""


class ExecState:
    """Execution state constants — no lifecycle progression implied."""
    COMPLETED = "completed"
    FAILED = "failed"
    ACTIVE = "active"
    BLOCKED = "blocked"
    CANCELLED = "cancelled"
    FULFILLED = "fulfilled"


class ObligationState:
    """Obligation state constants — no lifecycle progression implied."""
    PENDING = "pending"
    FULFILLED = "fulfilled"
    SATISFIED = "satisfied"
    WAIVED = "waived"
    BLOCKED = "blocked"
    FAILED = "failed"