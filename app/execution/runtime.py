"""Outcome Runtime — thin persistence wrapper around canonical execution.

NOT an execution engine. The canonical execution authority is:

    runtime/entry.py → execution_engine → Object / Execution / ExecutionLog

OutcomeRuntime persists the user's intention and current state across
server restarts. It does NOT execute workflows, iterate steps, or
manage a lifecycle progression.

Responsibilities:
- Accept and persist outcomes
- Provide status for "What happened to my..." queries
- Record current state
"""
import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Optional

from app import db
from app.execution.models import Outcome

logger = logging.getLogger(__name__)


class OutcomeRuntime:
    """Thin persistence wrapper around canonical execution.
    
    Executes outcomes via the canonical execution engine, not via
    step-based iteration. The state-driven model is:
    
        Execution = f(State, Intent, Evidence, Time)
    """

    # ── Outcome Persistence ──

    def accept(
        self,
        identity_id: str,
        intention: str,
        state: dict | None = None,
    ) -> Outcome:
        """Accept a new outcome. Creates a persistent record and returns immediately."""
        outcome = Outcome(
            outcome_id=self._generate_id(),
            identity_id=identity_id,
            intention=intention,
            state=state or {},
        )
        db.session.add(outcome)
        db.session.commit()
        logger.info("Outcome %s accepted: %s", outcome.outcome_id, intention[:60])
        return outcome

    def update_state(self, outcome_id: str, state_updates: dict) -> Outcome:
        """Update outcome state atomically. Pure state mutation — no lifecycle."""
        outcome = self._get(outcome_id)
        current = dict(outcome.state or {})
        current.update(state_updates)
        outcome.state = current
        outcome.updated_at = datetime.now(timezone.utc)
        db.session.commit()
        return outcome

    # ── Query ──

    def get(self, outcome_id: str) -> Optional[Outcome]:
        """Get an outcome by its user-facing ID."""
        return Outcome.query.filter_by(outcome_id=outcome_id).first()

    def get_by_identity(self, identity_id: str, limit: int = 20) -> list[Outcome]:
        """Get recent outcomes for an identity."""
        return (
            Outcome.query
            .filter_by(identity_id=identity_id)
            .order_by(Outcome.created_at.desc())
            .limit(limit)
            .all()
        )

    def search_intention(self, identity_id: str, query: str) -> list[Outcome]:
        """Search outcomes by intention text (for 'What happened to my...' queries)."""
        return (
            Outcome.query
            .filter(
                Outcome.identity_id == identity_id,
                Outcome.intention.ilike(f"%{query}%"),
            )
            .order_by(Outcome.created_at.desc())
            .limit(5)
            .all()
        )

    # ── Helpers ──

    def _generate_id(self) -> str:
        """Generate a short, user-friendly outcome ID."""
        return "out_" + uuid.uuid4().hex[:8]

    def _get(self, outcome_id: str) -> Outcome:
        outcome = Outcome.query.filter_by(outcome_id=outcome_id).first()
        if not outcome:
            raise ValueError(f"Outcome {outcome_id} not found")
        return outcome


# Singleton
_runtime: Optional[OutcomeRuntime] = None


def get_runtime() -> OutcomeRuntime:
    global _runtime
    if _runtime is None:
        _runtime = OutcomeRuntime()
    return _runtime