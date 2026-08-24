"""
SHUNYA — Watch / Monitoring (Phase 12A)
"""
import hashlib, json
from datetime import datetime, timedelta, timezone
from typing import Optional

# Capability constants
class Cap:
    WATCH_DEF_READ_OWNED = "watch_definition_read_owned"
    WATCH_EXECUTE_OWNED = "watch_execute_owned"
    INTEL_REQ_EVAL_BOUNDED = "intelligence_requirement_evaluate_bounded"
    WORLD_INTEL_RETRIEVE_BOUNDED = "world_intelligence_retrieve_bounded"
    WATCH_OBSERVATION_WRITE_OWNED = "watch_observation_write_owned"

# Change detection results
class Change:
    FIRST_OBSERVATION = "first_observation"
    NO_MATERIAL_CHANGE = "no_material_change"
    MATERIAL_CHANGE = "material_change"
    COVERAGE_CHANGED = "coverage_changed"
    FRESHNESS_CHANGED = "freshness_changed"
    CONFLICT_CHANGED = "conflict_changed"
    UNAVAILABLE_FAILED = "unavailable_failed"

# Due states
class Due:
    DUE = "due"
    NOT_DUE = "not_due"
    PAUSED = "paused"
    DISABLED = "disabled"


class MachineExecutionPrincipal:
    """Minimum canonical machine execution identity."""

    def __init__(self, principal_id: str, machine_class: str, tenant_id: Optional[int] = None,
                 purpose_code: str = "watch", capabilities: Optional[list] = None,
                 state: str = "active"):
        self.principal_id = principal_id
        self.machine_class = machine_class
        self.tenant_id = tenant_id
        self.purpose_code = purpose_code
        self.capabilities = set(capabilities or [])
        self.state = state  # active, disabled, revoked

    def has_capability(self, cap: str) -> bool:
        return cap in self.capabilities

    def can_access_tenant(self, tenant_id: Optional[int]) -> bool:
        if self.state != "active":
            return False
        if self.tenant_id is None:
            return True  # Platform-level
        if tenant_id is None:
            return False
        return self.tenant_id == tenant_id


class WatchService:
    """Computation-only Watch/Monitoring service. Uses MachinePrincipal for safety."""

    def __init__(self, phase11_service=None, phase12_service=None, phase4_service=None):
        self._p11 = phase11_service
        self._p12 = phase12_service
        self._p4 = phase4_service
        self._version = "12a.1"

    # ------------------------------------------------------------------
    # Machine Principal resolution
    # ------------------------------------------------------------------
    def resolve_principal(self, principal_id: str, tenant_id: Optional[int] = None) -> Optional[MachineExecutionPrincipal]:
        """Resolve a machine principal. In production, this queries a DB."""
        # For testing, we create principals on the fly
        return MachineExecutionPrincipal(
            principal_id=principal_id,
            machine_class="watch_worker",
            tenant_id=tenant_id,
            purpose_code="watch",
            capabilities=[Cap.WATCH_DEF_READ_OWNED, Cap.WATCH_EXECUTE_OWNED,
                          Cap.INTEL_REQ_EVAL_BOUNDED, Cap.WORLD_INTEL_RETRIEVE_BOUNDED,
                          Cap.WATCH_OBSERVATION_WRITE_OWNED],
            state="active",
        )

    # ------------------------------------------------------------------
    # Watch definition
    # ------------------------------------------------------------------
    def create_watch(self, tenant_id: int, requirement: dict, cadence_hours: int = 24,
                     purpose_code: str = "watch", created_by: str = "test") -> dict:
        # Phase 4 gate
        if self._p4:
            p4 = self._p4.check_eligibility(purpose_code)
            if not p4.get("eligible", True):
                return {"error": "blocked_by_phase_4", "watch_id": None}

        if not requirement or not requirement.get("topics"):
            return {"error": "empty_requirement", "watch_id": None}

        watch_id = hashlib.sha256(json.dumps(requirement, sort_keys=True).encode()).hexdigest()[:16]
        return {
            "watch_id": watch_id,
            "tenant_id": tenant_id,
            "requirement": requirement,
            "cadence_hours": cadence_hours,
            "purpose_code": purpose_code,
            "state": "active",
            "created_by": created_by,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }

    def compute_due(self, watch: dict, now: Optional[datetime] = None) -> str:
        if watch.get("state") == "paused":
            return Due.PAUSED
        if watch.get("state") == "disabled":
            return Due.DISABLED
        n = now or datetime.now(timezone.utc)
        last_success = watch.get("last_success_at")
        if last_success is None:
            return Due.DUE  # Never run
        cadence = watch.get("cadence_hours", 24)
        next_due = datetime.fromisoformat(last_success) + timedelta(hours=cadence)
        return Due.DUE if n >= next_due else Due.NOT_DUE

    # ------------------------------------------------------------------
    # Watch execution
    # ------------------------------------------------------------------
    def execute_watch(self, watch: dict, principal: MachineExecutionPrincipal,
                      now: Optional[datetime] = None) -> dict:
        n = now or datetime.now(timezone.utc)

        # Machine principal checks
        if not principal or principal.state != "active":
            return {"error": "machine_disabled", "state": "failed", "observation": None}
        if not principal.can_access_tenant(watch.get("tenant_id")):
            return {"error": "tenant_mismatch", "state": "failed", "observation": None}
        if not principal.has_capability(Cap.WATCH_EXECUTE_OWNED):
            return {"error": "capability_denied", "state": "failed", "observation": None}

        # Due check
        due = self.compute_due(watch, n)
        if due in (Due.PAUSED, Due.DISABLED):
            return {"error": f"watch_{due}", "state": "failed", "observation": None}

        # Phase 4 recheck
        if self._p4:
            p4 = self._p4.check_eligibility(watch.get("purpose_code", "watch"))
            if not p4.get("eligible", True):
                return {"error": "blocked_by_current_use", "state": "failed", "observation": None}

        # Phase 11/12 invocation
        requirement = watch.get("requirement", {})
        resolution = None
        wi_result = None
        if self._p11 and principal.has_capability(Cap.INTEL_REQ_EVAL_BOUNDED):
            resolution = self._p11.resolve(watch.get("tenant_id"), 0,
                                           workspace_context={},
                                           knowledge_topics=requirement.get("topics", []))
        if self._p12 and principal.has_capability(Cap.WORLD_INTEL_RETRIEVE_BOUNDED):
            wi_result = self._p12.execute(requirement, tenant_id=watch.get("tenant_id"))

        # Build observation
        observation = {
            "watch_id": watch.get("watch_id"),
            "tenant_id": watch.get("tenant_id"),
            "execution_id": hashlib.sha256(f"{watch['watch_id']}:{n.isoformat()}".encode()).hexdigest()[:16],
            "observed_as_of": n.isoformat(),
            "requirement_topics": requirement.get("topics", []),
            "coverage": wi_result.get("coverage", {}) if wi_result else {},
            "state": wi_result.get("state") if wi_result else "no_invocation",
            "sources": len(wi_result.get("sources", [])) if wi_result else 0,
            "evaluated_at": n.isoformat(),
        }

        # Change detection
        prior = watch.get("last_observation")
        change = self._detect_change(prior, observation)

        return {
            "state": "success",
            "observation": observation,
            "change": change,
            "resolution": resolution,
            "machine_principal_id": principal.principal_id,
        }

    def _detect_change(self, prior: Optional[dict], current: dict) -> str:
        if prior is None:
            return Change.FIRST_OBSERVATION
        # Check conflict first
        prior_conflict = prior.get("state") == "conflicted"
        curr_conflict = current.get("state") == "conflicted"
        if prior_conflict != curr_conflict:
            return Change.CONFLICT_CHANGED
        # Check state (material change) — but not for stale/freshness transitions
        if prior.get("state") != current.get("state"):
            # Stale transition is a FRESHNESS_CHANGED, not MATERIAL_CHANGE
            if prior.get("state") == "stale_only" or current.get("state") == "stale_only":
                return Change.FRESHNESS_CHANGED
            return Change.MATERIAL_CHANGE
        # Check coverage change
        if prior.get("coverage") != current.get("coverage"):
            return Change.COVERAGE_CHANGED
        # Source count alone is not material
        return Change.NO_MATERIAL_CHANGE

    # ------------------------------------------------------------------
    # Inspection
    # ------------------------------------------------------------------
    def inspect_watch(self, watch: dict) -> dict:
        return {
            "watch_id": watch.get("watch_id"),
            "tenant_id": watch.get("tenant_id"),
            "state": watch.get("state"),
            "cadence_hours": watch.get("cadence_hours"),
            "purpose_code": watch.get("purpose_code"),
        }

    def explain_due(self, watch: dict, now: Optional[datetime] = None) -> dict:
        return {"due": self.compute_due(watch, now)}

    def explain_observation(self, result: dict) -> dict:
        obs = result.get("observation") or {}
        return {
            "change": result.get("change"),
            "coverage": obs.get("coverage"),
            "state": obs.get("state"),
            "sources": obs.get("sources"),
        }