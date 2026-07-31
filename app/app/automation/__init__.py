"""
SHUNYA — Automation & Trigger Engine (Phase 14A, computation-only)
"""
import hashlib, json
from datetime import datetime, timedelta
from typing import Optional

# Trigger types
class TriggerType:
    SCHEDULE = "schedule"
    EVENT = "event"
    CONDITION = "condition"

# Trigger lifecycle states
class TriggerState:
    ACTIVE = "active"
    PAUSED = "paused"
    DISABLED = "disabled"
    SUSPENDED = "suspended"
    CANCELLED = "cancelled"
    COMPLETED = "completed"

# Trigger evaluation states
class MatchState:
    OBSERVED = "observed"
    MATCHED = "matched"
    ELIGIBLE = "eligible"
    AUTHORIZED = "authorized"
    EXECUTED = "executed"
    DUPLICATE = "duplicate"
    STALE = "stale"
    BLOCKED = "blocked"
    DENIED = "denied"
    FAILED = "failed"
    SUPPRESSED = "suppressed"


class AutomationService:
    """Automation & Trigger Engine.

    Consumes Phase 14 Plans. Detects triggers, evaluates eligibility,
    authorizes action, and hands off to Phase 14 governed action.
    Does NOT execute actions directly, make provider calls, or implement Phase 14C/17.
    """

    def __init__(self, phase4_service=None, phase14_service=None):
        self._p4 = phase4_service
        self._p14 = phase14_service
        self._version = "14a.1"
        self._executed_keys = set()  # Idempotency tracking

    # ------------------------------------------------------------------
    # Trigger definition
    # ------------------------------------------------------------------
    def define_trigger(self, trigger_type: str, config: dict,
                       tenant_id: int = 1, principal_id: Optional[str] = None) -> dict:
        """Define a new automation trigger."""
        if trigger_type not in (TriggerType.SCHEDULE, TriggerType.EVENT, TriggerType.CONDITION):
            return self._error("invalid_trigger_type", tenant_id, principal_id)

        trigger_id = hashlib.sha256(
            f"{tenant_id}:{trigger_type}:{json.dumps(config, sort_keys=True)}:{datetime.utcnow().isoformat()}".encode()
        ).hexdigest()[:16]

        return {
            "trigger_id": trigger_id,
            "trigger_type": trigger_type,
            "config": config,
            "state": TriggerState.ACTIVE,
            "tenant_id": tenant_id,
            "created_by": principal_id,
            "created_at": datetime.utcnow().isoformat(),
            "version": self._version,
        }

    # ------------------------------------------------------------------
    # Trigger lifecycle
    # ------------------------------------------------------------------
    def pause_trigger(self, trigger: dict, principal_id: Optional[str] = None) -> dict:
        if trigger["state"] not in (TriggerState.ACTIVE, TriggerState.SUSPENDED):
            return self._error("cannot_pause", trigger.get("tenant_id"), principal_id)
        trigger["state"] = TriggerState.PAUSED
        return trigger

    def resume_trigger(self, trigger: dict, principal_id: Optional[str] = None) -> dict:
        if trigger["state"] != TriggerState.PAUSED:
            return self._error("cannot_resume", trigger.get("tenant_id"), principal_id)
        trigger["state"] = TriggerState.ACTIVE
        return trigger

    def disable_trigger(self, trigger: dict, principal_id: Optional[str] = None) -> dict:
        if trigger["state"] in (TriggerState.CANCELLED, TriggerState.COMPLETED):
            return self._error("cannot_disable_terminal", trigger.get("tenant_id"), principal_id)
        trigger["state"] = TriggerState.DISABLED
        return trigger

    def suspend_trigger(self, trigger: dict, reason: str = "", principal_id: Optional[str] = None) -> dict:
        if trigger["state"] not in (TriggerState.ACTIVE, TriggerState.PAUSED):
            return self._error("cannot_suspend", trigger.get("tenant_id"), principal_id)
        trigger["state"] = TriggerState.SUSPENDED
        trigger["suspend_reason"] = reason
        return trigger

    def cancel_trigger(self, trigger: dict, principal_id: Optional[str] = None) -> dict:
        trigger["state"] = TriggerState.CANCELLED
        return trigger

    # ------------------------------------------------------------------
    # Trigger evaluation — Schedule
    # ------------------------------------------------------------------
    def evaluate_schedule(self, trigger: dict, now: Optional[datetime] = None) -> dict:
        """Evaluate a schedule trigger against as_of time."""
        if trigger.get("state") != TriggerState.ACTIVE:
            return {"state": MatchState.SUPPRESSED, "trigger_id": trigger.get("trigger_id")}

        n = now or datetime.utcnow()
        config = trigger.get("config", {})
        cadence_hours = config.get("cadence_hours", 24)
        last_run = config.get("last_run_at")

        if last_run is None:
            return {"state": MatchState.MATCHED, "trigger_id": trigger.get("trigger_id"),
                    "reason": "never_run"}

        next_due = datetime.fromisoformat(last_run) + timedelta(hours=cadence_hours)
        if n >= next_due:
            return {"state": MatchState.MATCHED, "trigger_id": trigger.get("trigger_id"),
                    "reason": "due"}
        return {"state": MatchState.OBSERVED, "trigger_id": trigger.get("trigger_id"),
                "reason": "not_due"}

    # ------------------------------------------------------------------
    # Trigger evaluation — Event
    # ------------------------------------------------------------------
    def evaluate_event(self, trigger: dict, event: dict) -> dict:
        """Evaluate whether an event matches a trigger."""
        if trigger.get("state") != TriggerState.ACTIVE:
            return {"state": MatchState.SUPPRESSED, "trigger_id": trigger.get("trigger_id")}

        config = trigger.get("config", {})
        event_type = event.get("type")
        match_type = config.get("match_type")

        if event_type != match_type:
            return {"state": MatchState.OBSERVED, "trigger_id": trigger.get("trigger_id"),
                    "reason": "type_mismatch"}

        # Check tenant
        if config.get("tenant_id") and event.get("tenant_id") and \
           config["tenant_id"] != event["tenant_id"]:
            return {"state": MatchState.DENIED, "trigger_id": trigger.get("trigger_id"),
                    "reason": "tenant_mismatch"}

        # Check idempotency key
        idempotency_key = event.get("idempotency_key") or \
            hashlib.sha256(json.dumps(event, sort_keys=True).encode()).hexdigest()
        if idempotency_key in self._executed_keys:
            return {"state": MatchState.DUPLICATE, "trigger_id": trigger.get("trigger_id"),
                    "reason": "duplicate_event"}

        self._executed_keys.add(idempotency_key)
        return {"state": MatchState.MATCHED, "trigger_id": trigger.get("trigger_id"),
                "reason": "event_matched", "idempotency_key": idempotency_key}

    # ------------------------------------------------------------------
    # Trigger evaluation — Condition
    # ------------------------------------------------------------------
    def evaluate_condition(self, trigger: dict, prior_state: dict, current_state: dict) -> dict:
        """Evaluate whether a condition transition matches a trigger."""
        if trigger.get("state") != TriggerState.ACTIVE:
            return {"state": MatchState.SUPPRESSED, "trigger_id": trigger.get("trigger_id")}

        config = trigger.get("config", {})
        watch_field = config.get("watch_field")
        trigger_value = config.get("trigger_on")

        if watch_field is None:
            return {"state": MatchState.OBSERVED, "reason": "no_field"}

        prior_val = prior_state.get(watch_field)
        current_val = current_state.get(watch_field)

        # Check for transition: false→true or value change
        if trigger_value == "true":
            if prior_val is False and current_val is True:
                return {"state": MatchState.MATCHED, "trigger_id": trigger.get("trigger_id"),
                        "reason": f"{watch_field}: false→true"}
        elif trigger_value == "changed":
            if prior_val != current_val:
                return {"state": MatchState.MATCHED, "trigger_id": trigger.get("trigger_id"),
                        "reason": f"{watch_field}: changed {prior_val}→{current_val}"}

        return {"state": MatchState.OBSERVED, "trigger_id": trigger.get("trigger_id"),
                "reason": "no_transition"}

    # ------------------------------------------------------------------
    # Eligibility / Authorization / Execution handoff
    # ------------------------------------------------------------------
    def authorize_execution(self, trigger: dict, match_result: dict, plan: dict,
                            tenant_id: int = 1, principal_id: Optional[str] = None) -> dict:
        """Authorize and execute an automation through Phase 14 governed action."""
        if match_result.get("state") != MatchState.MATCHED:
            return self._error("not_matched", tenant_id, principal_id)

        # Phase 4 current-use
        if self._p4:
            p4 = self._p4.check_eligibility(plan.get("purpose_code", "automation"))
            if not p4.get("eligible", True):
                return self._error("blocked_by_current_use", tenant_id, principal_id)

        # Tenant isolation
        if trigger.get("tenant_id") != tenant_id:
            return self._error("tenant_mismatch", tenant_id, principal_id)

        # Idempotency
        idem_key = match_result.get("idempotency_key") or \
            hashlib.sha256(f"{trigger['trigger_id']}:{datetime.utcnow().isoformat()}".encode()).hexdigest()
        if idem_key in self._executed_keys:
            return self._error("duplicate_execution", tenant_id, principal_id)

        self._executed_keys.add(idem_key)

        # Inspect trigger
        ins = self.inspect_trigger(trigger)
        return ins

    def inspect_trigger(self, trigger: dict) -> dict:
        return {
            "trigger_id": trigger.get("trigger_id"),
            "trigger_type": trigger.get("trigger_type"),
            "state": trigger.get("state"),
            "tenant_id": trigger.get("tenant_id"),
        }

    def explain_trigger(self, trigger: dict, match_result: dict = None) -> dict:
        return {
            "trigger_id": trigger.get("trigger_id"),
            "trigger_type": trigger.get("trigger_type"),
            "state": trigger.get("state"),
            "match": match_result,
        }

    def _error(self, reason: str, tenant_id: int = 1, principal_id: Optional[str] = None) -> dict:
        return {"error": reason, "tenant_id": tenant_id, "principal_id": principal_id,
                "timestamp": datetime.utcnow().isoformat()}