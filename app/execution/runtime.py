"""
Outcome Runtime — owns business outcomes from acceptance to completion.

Not merely an execution engine. The runtime persists the user's intention
across server restarts, provider outages, and browser closes.

Responsibilities:
- Accept and queue outcomes
- Execute with automatic recovery (5 levels)
- Persist progress across restarts
- Provide status for "What happened to my..." queries
- Record diagnostics
"""
import logging
import uuid
import time
from datetime import datetime, timezone
from typing import Any, Optional
from sqlalchemy import text as sa_text

from app import db
from app.execution.models import Outcome
from app.execution.recovery import RecoveryOrchestrator

logger = logging.getLogger(__name__)


class OutcomeRuntime:
    """The Outcome Runtime — owns the user's intention from acceptance through completion."""

    def __init__(self):
        self._recovery = RecoveryOrchestrator()

    # ── Outcome Lifecycle ──

    def accept(
        self,
        identity_id: str,
        intention: str,
        steps: list[dict],
        expected_seconds: int = 30,
    ) -> Outcome:
        """Accept a new outcome. Creates a persistent record and returns immediately."""
        outcome = Outcome(
            outcome_id=self._generate_id(),
            identity_id=identity_id,
            intention=intention,
            stage="accepted",
            progress="Received",
            expected_completion_seconds=expected_seconds,
            steps=steps,
        )
        db.session.add(outcome)
        db.session.commit()
        logger.info("Outcome %s accepted: %s", outcome.outcome_id, intention[:60])
        return outcome

    def queue(self, outcome_id: str) -> Outcome:
        """Move to queued stage."""
        outcome = self._get(outcome_id)
        outcome.stage = "queued"
        outcome.progress = "Queued for execution"
        db.session.commit()
        return outcome

    def execute(self, outcome_id: str) -> Outcome:
        """Execute the outcome with full recovery hierarchy. May be long-running."""
        outcome = self._get(outcome_id)
        outcome.stage = "executing"
        outcome.progress = "Starting execution"
        db.session.commit()

        start_time = time.time()
        step_results = []
        all_succeeded = True

        for step_idx, step in enumerate(outcome.steps or []):
            action = step.get("action", {})
            action_type = action.get("action", "unknown")

            outcome.progress = f"Step {step_idx + 1}: {action_type.replace('_', ' ')} {action.get('type', '')}"
            outcome.steps[step_idx] = {**step, "status": "executing"}
            db.session.commit()

            # Execute with recovery
            success, result, recovery_log = self._recovery.execute_with_hierarchy(
                action=action,
                identity_id=outcome.identity_id,
                step_idx=step_idx,
                outcome_id=outcome.outcome_id,
            )

            step_result = {
                "action": action_type,
                "type": action.get("type", ""),
                "success": success,
                "result": result,
                "recovery": recovery_log,
            }
            step_results.append(step_result)

            if not success:
                all_succeeded = False
                outcome.last_error = result.get("error", "Unknown error")
                outcome.error_count = outcome.error_count + 1

            # Record recovery attempts
            if recovery_log:
                for entry in recovery_log:
                    outcome.recovery_history = (outcome.recovery_history or []) + [entry]
                db.session.commit()

        # Build final summary
        elapsed = time.time() - start_time
        outcome.actual_completion_seconds = round(elapsed)
        outcome.steps = step_results
        outcome.final_summary = self._build_summary(step_results)
        outcome.stage = "completed" if all_succeeded else "failed"
        outcome.progress = "Completed" if all_succeeded else "Completed with issues"
        db.session.commit()

        logger.info(
            "Outcome %s %s in %.1fs (recoveries: %d)",
            outcome.outcome_id, outcome.stage, elapsed,
            len(outcome.recovery_history or []),
        )
        return outcome

    def monitor(self, outcome_id: str) -> Outcome:
        """Set to monitoring stage (for long-running outcomes)."""
        outcome = self._get(outcome_id)
        outcome.stage = "monitoring"
        outcome.progress = "Monitoring for completion"
        db.session.commit()
        return outcome

    def complete(self, outcome_id: str, summary: dict) -> Outcome:
        """Mark as completed with summary."""
        outcome = self._get(outcome_id)
        outcome.stage = "completed"
        outcome.progress = "Completed"
        outcome.final_summary = summary
        db.session.commit()
        return outcome

    def fail(self, outcome_id: str, error: str) -> Outcome:
        """Mark as failed with error."""
        outcome = self._get(outcome_id)
        outcome.stage = "failed"
        outcome.progress = "Failed"
        outcome.last_error = error
        outcome.error_count = (outcome.error_count or 0) + 1
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

    def _build_summary(self, step_results: list[dict]) -> dict:
        created = []
        modified = []
        monitoring = []
        for sr in step_results:
            if sr["success"] and sr["action"] == "create_object":
                name = sr.get("result", {}).get("data", {}).get("name", "")
                t = sr.get("type", "item")
                created.append(f"{t} \"{name}\"" if name else f"{t}")
                monitoring.append(f"Monitor {t} for updates")
            elif sr["success"] and sr["action"] == "update_object":
                modified.append(f"Updated {sr.get('type', 'item')}")
        return {
            "created": created,
            "modified": modified,
            "monitoring": monitoring,
            "recovered_count": sum(1 for sr in step_results if sr.get("recovery")),
            "total_steps": len(step_results),
        }


# Singleton
_runtime: Optional[OutcomeRuntime] = None


def get_runtime() -> OutcomeRuntime:
    global _runtime
    if _runtime is None:
        _runtime = OutcomeRuntime()
    return _runtime