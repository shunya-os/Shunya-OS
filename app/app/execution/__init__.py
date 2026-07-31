"""
SHUNYA — Business Execution Instance Runtime (Phase 14E, computation-only)
"""
import hashlib, json
from datetime import datetime
from typing import Optional


class ExecState:
    PENDING = "pending"
    ACTIVE = "active"
    BLOCKED = "blocked"
    AT_RISK = "at_risk"
    PARTIALLY_FULFILLED = "partially_fulfilled"
    FULFILLED = "fulfilled"
    FAILED = "failed"
    CANCELLED = "cancelled"

    VALID_TRANSITIONS = {
        PENDING: [ACTIVE, CANCELLED],
        ACTIVE: [BLOCKED, AT_RISK, PARTIALLY_FULFILLED, FULFILLED, FAILED, CANCELLED],
        BLOCKED: [ACTIVE, AT_RISK, FAILED, CANCELLED],
        AT_RISK: [ACTIVE, BLOCKED, FAILED, CANCELLED],
        PARTIALLY_FULFILLED: [ACTIVE, BLOCKED, AT_RISK, FULFILLED, FAILED, CANCELLED],
        FULFILLED: [],
        FAILED: [],
        CANCELLED: [],
    }


class ObligationState:
    PENDING = "pending"
    READY = "ready"
    IN_PROGRESS = "in_progress"
    BLOCKED = "blocked"
    SATISFIED = "satisfied"
    FAILED = "failed"
    WAIVED = "waived"


class ResourcePositionState:
    SUFFICIENT = "sufficient"
    NEAR_THRESHOLD = "near_threshold"
    SHORTFALL = "shortfall"
    NON_COMPARABLE = "non_comparable"


class BusinessExecutionInstance:
    def __init__(self, exec_id: str, tenant_id: int, commitment_type: str,
                 commitment_id: str, state: str = ExecState.PENDING,
                 provenance: Optional[str] = None):
        self.exec_id = exec_id
        self.tenant_id = tenant_id
        self.commitment_type = commitment_type
        self.commitment_id = commitment_id
        self.state = state
        self.provenance = provenance
        self.created_at = datetime.utcnow().isoformat()
        self.started_at = None
        self.completed_at = None
        self.plan_refs = []
        self.workflow_refs = []
        self.history = []

    def to_dict(self) -> dict:
        return {
            "exec_id": self.exec_id,
            "tenant_id": self.tenant_id,
            "commitment_type": self.commitment_type,
            "commitment_id": self.commitment_id,
            "state": self.state,
            "created_at": self.created_at,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "plan_refs": self.plan_refs,
            "workflow_refs": self.workflow_refs,
        }


class ExecutionObligation:
    def __init__(self, obl_id: str, exec_id: str, tenant_id: int,
                 obl_type: str, description: str,
                 state: str = ObligationState.PENDING,
                 due_at: Optional[str] = None,
                 responsible_party: Optional[str] = None,
                 counterparty: Optional[str] = None,
                 provenance: Optional[str] = None):
        self.obl_id = obl_id
        self.exec_id = exec_id
        self.tenant_id = tenant_id
        self.obl_type = obl_type
        self.description = description
        self.state = state
        self.due_at = due_at
        self.responsible_party = responsible_party
        self.counterparty = counterparty
        self.provenance = provenance
        self.task_refs = []
        self.dependencies = []
        self.created_at = datetime.utcnow().isoformat()

    def to_dict(self) -> dict:
        return {
            "obl_id": self.obl_id,
            "exec_id": self.exec_id,
            "tenant_id": self.tenant_id,
            "obl_type": self.obl_type,
            "description": self.description,
            "state": self.state,
            "due_at": self.due_at,
        }


class ExecutionResourceAllocation:
    def __init__(self, alloc_id: str, exec_id: str, tenant_id: int,
                 resource_type: str, quantity: float, unit: str,
                 provenance: Optional[str] = None):
        self.alloc_id = alloc_id
        self.exec_id = exec_id
        self.tenant_id = tenant_id
        self.resource_type = resource_type
        self.quantity = quantity
        self.unit = unit
        self.provenance = provenance
        self.superseded_at = None

    def to_dict(self) -> dict:
        return {"alloc_id": self.alloc_id, "exec_id": self.exec_id,
                "resource_type": self.resource_type, "quantity": self.quantity,
                "unit": self.unit}


class ExecutionResourceConsumption:
    def __init__(self, cons_id: str, alloc_id: str, exec_id: str,
                 tenant_id: int, resource_type: str, quantity: float, unit: str,
                 provenance: Optional[str] = None):
        self.cons_id = cons_id
        self.alloc_id = alloc_id
        self.exec_id = exec_id
        self.tenant_id = tenant_id
        self.resource_type = resource_type
        self.quantity = quantity
        self.unit = unit
        self.provenance = provenance
        self.superseded_at = None

    def to_dict(self) -> dict:
        return {"cons_id": self.cons_id, "alloc_id": self.alloc_id,
                "exec_id": self.exec_id, "quantity": self.quantity, "unit": self.unit}


class ExecutionResourceRequirement:
    def __init__(self, req_id: str, obl_id: str, exec_id: str, tenant_id: int,
                 resource_type: str, expected_quantity: float, unit: str,
                 provenance: Optional[str] = None):
        self.req_id = req_id
        self.obl_id = obl_id
        self.exec_id = exec_id
        self.tenant_id = tenant_id
        self.resource_type = resource_type
        self.expected_quantity = expected_quantity
        self.unit = unit
        self.provenance = provenance
        self.satisfied = False

    def to_dict(self) -> dict:
        return {"req_id": self.req_id, "obl_id": self.obl_id,
                "resource_type": self.resource_type,
                "expected_quantity": self.expected_quantity, "unit": self.unit}


class ExecutionException:
    def __init__(self, exc_id: str, exec_id: str, tenant_id: int,
                 exc_type: str, severity: str = "medium",
                 status: str = "open", provenance: Optional[str] = None):
        self.exc_id = exc_id
        self.exec_id = exec_id
        self.tenant_id = tenant_id
        self.exc_type = exc_type
        self.severity = severity
        self.status = status
        self.provenance = provenance

    def to_dict(self) -> dict:
        return {"exc_id": self.exc_id, "exec_id": self.exec_id,
                "exc_type": self.exc_type, "severity": self.severity,
                "status": self.status}


class ExecutionService:
    def __init__(self):
        self._execs: dict[str, BusinessExecutionInstance] = {}
        self._obls: dict[str, ExecutionObligation] = {}
        self._allocs: dict[str, ExecutionResourceAllocation] = {}
        self._cons: dict[str, ExecutionResourceConsumption] = {}
        self._reqs: dict[str, ExecutionResourceRequirement] = {}
        self._excs: dict[str, ExecutionException] = {}
        self._idempotency: set[str] = set()
        self._version = "14e.1"

    # --- Execution ---
    def activate(self, commitment_type: str, commitment_id: str, tenant_id: int,
                 idempotency_key: Optional[str] = None) -> dict:
        idem = idempotency_key or f"{tenant_id}:{commitment_type}:{commitment_id}"
        if idem in self._idempotency:
            return {"duplicate": True, "exec_id": None}
        if commitment_type == "lead":
            return self._err("lead_not_eligible_for_execution", tenant_id)
        self._idempotency.add(idem)
        eid = hashlib.sha256(idem.encode()).hexdigest()[:16]
        inst = BusinessExecutionInstance(eid, tenant_id, commitment_type, commitment_id)
        inst.state = ExecState.ACTIVE
        inst.started_at = datetime.utcnow().isoformat()
        self._execs[eid] = inst
        return {"exec_id": eid, "state": inst.state, "created": True}

    def transition(self, exec_id: str, new_state: str, tenant_id: int) -> dict:
        inst = self._execs.get(exec_id)
        if not inst:
            return self._err("execution_not_found", tenant_id)
        if inst.tenant_id != tenant_id:
            return self._err("tenant_mismatch", tenant_id)
        valid = ExecState.VALID_TRANSITIONS.get(inst.state, [])
        if new_state not in valid:
            return self._err("invalid_transition", tenant_id)
        inst.history.append({"from": inst.state, "to": new_state, "at": datetime.utcnow().isoformat()})
        inst.state = new_state
        if new_state in (ExecState.FULFILLED, ExecState.FAILED, ExecState.CANCELLED):
            inst.completed_at = datetime.utcnow().isoformat()
        return {"exec_id": exec_id, "state": new_state}

    # --- Obligations ---
    def add_obligation(self, exec_id: str, tenant_id: int, obl_type: str,
                       description: str, due_at: Optional[str] = None,
                       counterparty: Optional[str] = None) -> dict:
        inst = self._execs.get(exec_id)
        if not inst or inst.tenant_id != tenant_id:
            return self._err("execution_not_found", tenant_id)
        oid = hashlib.sha256(f"{exec_id}:{obl_type}:{description}".encode()).hexdigest()[:16]
        obl = ExecutionObligation(oid, exec_id, tenant_id, obl_type, description,
                                  due_at=due_at, counterparty=counterparty)
        self._obls[oid] = obl
        return {"obl_id": oid}

    def satisfy_obligation(self, obl_id: str, tenant_id: int,
                           evidence: Optional[str] = None) -> dict:
        obl = self._obls.get(obl_id)
        if not obl or obl.tenant_id != tenant_id:
            return self._err("obligation_not_found", tenant_id)
        if not evidence:
            return self._err("evidence_required_for_satisfaction", tenant_id)
        obl.state = ObligationState.SATISFIED
        return {"obl_id": obl_id, "state": "satisfied"}

    # --- Dependencies ---
    def add_dependency(self, obl_id: str, depends_on_obl_id: str, tenant_id: int) -> dict:
        obl = self._obls.get(obl_id)
        dep = self._obls.get(depends_on_obl_id)
        if not obl or not dep:
            return self._err("obligation_not_found", tenant_id)
        if obl.tenant_id != tenant_id or dep.tenant_id != tenant_id:
            return self._err("tenant_mismatch", tenant_id)
        if obl_id == depends_on_obl_id:
            return self._err("dependency_cycle", tenant_id)
        if depends_on_obl_id in obl.dependencies:
            return {"duplicate": True}
        # Cycle detection
        visited = set()
        def dfs(current):
            if current in visited:
                return False
            visited.add(current)
            obl = self._obls.get(current)
            if obl:
                for d in obl.dependencies:
                    if d == obl_id or not dfs(d):
                        return False
            return True
        if not dfs(depends_on_obl_id):
            return self._err("dependency_cycle", tenant_id)
        obl.dependencies.append(depends_on_obl_id)
        return {"dependency_added": True}

    # --- Resources ---
    def allocate_resource(self, exec_id: str, tenant_id: int,
                          resource_type: str, quantity: float, unit: str) -> dict:
        aid = hashlib.sha256(f"{exec_id}:{resource_type}:{datetime.utcnow().isoformat()}".encode()).hexdigest()[:16]
        alloc = ExecutionResourceAllocation(aid, exec_id, tenant_id, resource_type, quantity, unit)
        self._allocs[aid] = alloc
        return {"alloc_id": aid, "quantity": quantity, "unit": unit}

    def record_consumption(self, alloc_id: str, exec_id: str, tenant_id: int,
                           quantity: float, unit: str,
                           idempotency_key: Optional[str] = None) -> dict:
        idem = idempotency_key or f"{tenant_id}:{alloc_id}:{quantity}:{unit}"
        if idem in self._idempotency:
            return {"duplicate": True}
        self._idempotency.add(idem)
        # Get resource_type from allocation
        alloc = self._allocs.get(alloc_id)
        rt = alloc.resource_type if alloc else "unknown"
        cid = hashlib.sha256(idem.encode()).hexdigest()[:16]
        cons = ExecutionResourceConsumption(cid, alloc_id, exec_id, tenant_id, rt, quantity, unit)
        self._cons[cid] = cons
        return {"cons_id": cid, "quantity": quantity}

    def add_requirement(self, obl_id: str, exec_id: str, tenant_id: int,
                        resource_type: str, expected_quantity: float, unit: str) -> dict:
        rid = hashlib.sha256(f"{obl_id}:{resource_type}".encode()).hexdigest()[:16]
        req = ExecutionResourceRequirement(rid, obl_id, exec_id, tenant_id,
                                           resource_type, expected_quantity, unit)
        self._reqs[rid] = req
        return {"req_id": rid}

    # --- Resource Position ---
    def compute_resource_position(self, exec_id: str, tenant_id: int) -> dict:
        allocations = [a for a in self._allocs.values()
                       if a.exec_id == exec_id and a.tenant_id == tenant_id and a.superseded_at is None]
        consumptions = [c for c in self._cons.values()
                        if c.exec_id == exec_id and c.tenant_id == tenant_id and c.superseded_at is None]
        requirements = [r for r in self._reqs.values()
                        if r.exec_id == exec_id and r.tenant_id == tenant_id and not r.satisfied]

        # Group by resource type
        types = set(a.resource_type for a in allocations)
        types.update(c.resource_type for c in consumptions)
        types.update(r.resource_type for r in requirements)
        positions = {}
        overall = ResourcePositionState.SUFFICIENT
        for rt in types:
            total_alloc = sum(a.quantity for a in allocations if a.resource_type == rt and a.unit == "USD")
            total_cons = sum(c.quantity for c in consumptions if c.resource_type == rt and c.unit == "USD")
            total_req = sum(r.expected_quantity for r in requirements if r.resource_type == rt and r.unit == "USD")
            remaining = total_alloc - total_cons
            outstanding = total_req
            position = remaining - outstanding
            if position < 0:
                state = ResourcePositionState.SHORTFALL
                overall = ResourcePositionState.SHORTFALL
            elif position == 0:
                state = ResourcePositionState.NEAR_THRESHOLD
                if overall != ResourcePositionState.SHORTFALL:
                    overall = ResourcePositionState.NEAR_THRESHOLD
            else:
                state = ResourcePositionState.SUFFICIENT
            positions[rt] = {"allocated": total_alloc, "consumed": total_cons,
                             "remaining": remaining, "outstanding_demand": outstanding,
                             "position": position, "state": state}
        return {"exec_id": exec_id, "overall": overall, "positions": positions}

    # --- Exceptions ---
    def add_exception(self, exec_id: str, tenant_id: int, exc_type: str,
                      severity: str = "medium") -> dict:
        eid = hashlib.sha256(f"{exec_id}:{exc_type}:{datetime.utcnow().isoformat()}".encode()).hexdigest()[:16]
        exc = ExecutionException(eid, exec_id, tenant_id, exc_type, severity)
        self._excs[eid] = exc
        return {"exc_id": eid}

    # --- Inspection ---
    def inspect(self, exec_id: str, tenant_id: int) -> dict:
        inst = self._execs.get(exec_id)
        if not inst or inst.tenant_id != tenant_id:
            return self._err("execution_not_found", tenant_id)
        obls = [o.to_dict() for o in self._obls.values() if o.exec_id == exec_id]
        excs = [e.to_dict() for e in self._excs.values() if e.exec_id == exec_id]
        pos = self.compute_resource_position(exec_id, tenant_id)
        return {"execution": inst.to_dict(), "obligations": obls,
                "exceptions": excs, "resource_position": pos}

    def _err(self, reason: str, tenant_id: int = 1) -> dict:
        return {"error": reason, "tenant_id": tenant_id, "timestamp": datetime.utcnow().isoformat()}