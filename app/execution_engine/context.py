"""DecisionContext — constitutionally complete evaluation input.

    Execution = f(State, Intent, Evidence, Time)

This is the canonical input type for all execution evaluation. No decision
can be made without these four dimensions. The caller (process_event in
runtime/entry.py) constructs a DecisionContext from the incoming event,
and every evaluation function accepts it as its single input.

Four dimensions, two roles:

  DECISION INPUTS (consumed by the canonical decision boundary):
    State:    Current object state (dict). The decision operates on
              what the entity currently is.

    Evidence: Facts, observations, records known about the entity.
              Without evidence, no update decision is permitted —
              the evidence gate enforces this at the decision boundary.

  EXECUTION GATE AND AUDIT DIMENSIONS (consumed at the execution boundary):
    Intent:   Why this evaluation was triggered (event type, source).
              Recorded in the decision trace for full auditability.
              Determines which execution path is valid.

    Time:     When the decision was made (UTC timestamp).
              Protects against stale decisions and provides temporal
              ordering in the decision trace.

This split is intentional in the constitutional architecture:
the structural decision (get_next_action) operates on State + Evidence,
while the execution gate (execute_with_trace) uses all four dimensions
for traceability, scheduling, and audit.

Fields:
    state:    Current object state (dict). Required — represents current truth.
    intent:   What triggered this evaluation. Optional — when absent the
              function can only perform structural checks.
    evidence: Facts, observations, records known about the object. Optional.
    time:     Temporal context. Optional — defaults to UTC now.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional


@dataclass
class DecisionContext:
    """Constitutionally complete input for execution evaluation.

    Four dimensions, two roles:
      Decision inputs:  State, Evidence
      Audit dimensions: Intent, Time

    See module docstring for full contract.
    """

    state: dict[str, Any] = field(default_factory=dict)
    intent: Optional[str] = None
    evidence: Optional[dict[str, Any]] = None
    time: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def with_state(self, new_state: dict) -> DecisionContext:
        """Return a copy with an updated state."""
        return DecisionContext(
            state=new_state,
            intent=self.intent,
            evidence=self.evidence,
            time=self.time,
        )

    def has_intent(self) -> bool:
        """Whether the context carries intent (required for execution)."""
        return bool(self.intent)

    def has_evidence(self) -> bool:
        """Whether the context carries evidence (required for execution)."""
        return bool(self.evidence)

    def to_dict(self) -> dict[str, Any]:
        return {
            "state": self.state,
            "intent": self.intent,
            "evidence": self.evidence,
            "time": self.time.isoformat(),
        }