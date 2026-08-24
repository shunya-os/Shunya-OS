"""
SHUNYA — Growth & Campaign Intelligence (Phase 15A, computation-only)
"""
import hashlib, json
from datetime import datetime, timezone
from typing import Optional

# Campaign lifecycle
class CampaignState:
    DRAFT = "draft"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

# Attribution states
class AttrState:
    DIRECT = "directly_linked"
    STRONG = "strongly_attributable"
    PLAUSIBLE = "plausibly_attributable"
    CORRELATED = "correlated"
    DISPUTED = "disputed"
    UNKNOWN = "unknown"
    NOT_ATTRIBUTABLE = "not_attributable"


class GrowthInitiative:
    def __init__(self, campaign_id: str, tenant_id: int, name: str,
                 objective_version: int = 1, state: str = CampaignState.DRAFT,
                 provenance: Optional[str] = None):
        self.campaign_id = campaign_id
        self.tenant_id = tenant_id
        self.name = name
        self.objective_version = objective_version
        self.state = state
        self.provenance = provenance
        self.source_refs = []
        self.created_at = datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> dict:
        return {"campaign_id": self.campaign_id, "tenant_id": self.tenant_id,
                "name": self.name, "state": self.state}


class GrowthObjective:
    def __init__(self, campaign_id: str, version: int, description: str,
                 metric: str = "count", provenance: Optional[str] = None):
        self.campaign_id = campaign_id
        self.version = version
        self.description = description
        self.metric = metric
        self.provenance = provenance
        self.effective_at = datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> dict:
        return {"campaign_id": self.campaign_id, "version": self.version,
                "description": self.description, "metric": self.metric}


class CohortDefinition:
    def __init__(self, cohort_id: str, tenant_id: int, name: str,
                 conditions: dict, version: int = 1,
                 provenance: Optional[str] = None):
        self.cohort_id = cohort_id
        self.tenant_id = tenant_id
        self.name = name
        self.conditions = conditions
        self.version = version
        self.provenance = provenance

    def to_dict(self) -> dict:
        return {"cohort_id": self.cohort_id, "name": self.name,
                "conditions": self.conditions, "version": self.version}


class GrowthTouchpoint:
    def __init__(self, tp_id: str, campaign_id: str, tenant_id: int,
                 source_ref: str, tp_type: str, occurred_at: str,
                 identity_ref: Optional[str] = None,
                 provenance: Optional[str] = None):
        self.tp_id = tp_id
        self.campaign_id = campaign_id
        self.tenant_id = tenant_id
        self.source_ref = source_ref
        self.tp_type = tp_type
        self.occurred_at = occurred_at
        self.identity_ref = identity_ref
        self.provenance = provenance
        self.recorded_at = datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> dict:
        return {"tp_id": self.tp_id, "campaign_id": self.campaign_id,
                "source_ref": self.source_ref, "tp_type": self.tp_type,
                "identity_ref": self.identity_ref}


class GrowthAttribution:
    def __init__(self, attr_id: str, campaign_id: str, tenant_id: int,
                 target_type: str, target_id: str, state: str = AttrState.UNKNOWN,
                 policy_version: int = 1, provenance: Optional[str] = None):
        self.attr_id = attr_id
        self.campaign_id = campaign_id
        self.tenant_id = tenant_id
        self.target_type = target_type
        self.target_id = target_id
        self.state = state
        self.policy_version = policy_version
        self.provenance = provenance

    def to_dict(self) -> dict:
        return {"attr_id": self.attr_id, "campaign_id": self.campaign_id,
                "target_type": self.target_type, "target_id": self.target_id,
                "state": self.state, "policy_version": self.policy_version}


class GrowthIntelligenceService:
    def __init__(self):
        self._campaigns: dict[str, GrowthInitiative] = {}
        self._objectives: dict[str, list[GrowthObjective]] = {}
        self._cohorts: dict[str, CohortDefinition] = {}
        self._touchpoints: dict[str, GrowthTouchpoint] = {}
        self._attributions: dict[str, GrowthAttribution] = {}
        self._idempotency: set[str] = set()
        self._version = "15a.1"

    # --- Campaign ---
    def create_campaign(self, name: str, tenant_id: int,
                        objective_desc: str = "",
                        idempotency_key: Optional[str] = None) -> dict:
        idem = idempotency_key or f"{tenant_id}:{name}"
        if idem in self._idempotency:
            return {"duplicate": True}
        self._idempotency.add(idem)
        cid = hashlib.sha256(idem.encode()).hexdigest()[:16]
        camp = GrowthInitiative(cid, tenant_id, name, provenance="growth")
        self._campaigns[cid] = camp
        # Set initial objective
        if objective_desc:
            self.set_objective(cid, 1, objective_desc, tenant_id)
        return {"campaign_id": cid, "state": CampaignState.DRAFT}

    def set_objective(self, campaign_id: str, version: int, description: str,
                       tenant_id: int) -> dict:
        if campaign_id not in self._campaigns:
            return self._err("campaign_not_found", tenant_id)
        if campaign_id not in self._objectives:
            self._objectives[campaign_id] = []
        for o in self._objectives[campaign_id]:
            if o.version == version:
                return self._err("duplicate_objective_version", tenant_id)
        obj = GrowthObjective(campaign_id, version, description)
        self._objectives[campaign_id].append(obj)
        self._campaigns[campaign_id].objective_version = version
        return {"objective_set": True, "version": version}

    def link_source(self, campaign_id: str, source_ref: str, tenant_id: int) -> dict:
        camp = self._campaigns.get(campaign_id)
        if not camp or camp.tenant_id != tenant_id:
            return self._err("campaign_not_found", tenant_id)
        if source_ref not in camp.source_refs:
            camp.source_refs.append(source_ref)
        return {"source_linked": True}

    # --- Cohorts ---
    def define_cohort(self, name: str, tenant_id: int, conditions: dict) -> dict:
        cid = hashlib.sha256(f"{tenant_id}:{name}".encode()).hexdigest()[:16]
        cohort = CohortDefinition(cid, tenant_id, name, conditions)
        self._cohorts[cid] = cohort
        return {"cohort_id": cid}

    def evaluate_cohort_membership(self, cohort_id: str, subject: dict,
                                    tenant_id: int) -> dict:
        cohort = self._cohorts.get(cohort_id)
        if not cohort or cohort.tenant_id != tenant_id:
            return self._err("cohort_not_found", tenant_id)
        # Deterministic evaluation of conditions
        conditions = cohort.conditions
        for key, expected in conditions.items():
            actual = subject.get(key)
            if isinstance(expected, (int, float)) and isinstance(actual, (int, float)):
                if actual < expected:
                    return {"eligible": False, "reason": f"{key}: {actual} < {expected}"}
            elif actual != expected:
                return {"eligible": False, "reason": f"{key}: {actual} != {expected}"}
        return {"eligible": True, "cohort_version": cohort.version}

    # --- Touchpoints ---
    def record_touchpoint(self, campaign_id: str, tenant_id: int,
                          source_ref: str, tp_type: str,
                          occurred_at: Optional[str] = None,
                          identity_ref: Optional[str] = None,
                          idempotency_key: Optional[str] = None) -> dict:
        idem = idempotency_key or hashlib.sha256(
            f"{tenant_id}:{campaign_id}:{source_ref}:{tp_type}".encode()).hexdigest()
        if idem in self._idempotency:
            return {"duplicate": True}
        self._idempotency.add(idem)
        tid = hashlib.sha256(idem.encode()).hexdigest()[:16]
        tp = GrowthTouchpoint(tid, campaign_id, tenant_id, source_ref, tp_type,
                            occurred_at or datetime.now(timezone.utc).isoformat(),
                            identity_ref=identity_ref)
        self._touchpoints[tid] = tp
        return {"touchpoint_id": tid}

    # --- Attribution ---
    def record_attribution(self, campaign_id: str, tenant_id: int,
                           target_type: str, target_id: str,
                           state: str = AttrState.UNKNOWN,
                           policy_version: int = 1) -> dict:
        aid = hashlib.sha256(f"{campaign_id}:{target_type}:{target_id}".encode()).hexdigest()[:16]
        attr = GrowthAttribution(aid, campaign_id, tenant_id, target_type,
                                 target_id, state, policy_version)
        self._attributions[aid] = attr
        return {"attribution_id": aid, "state": state, "policy_version": policy_version}

    def get_attributions_for(self, target_type: str, target_id: str,
                              tenant_id: int) -> list:
        return [a.to_dict() for a in self._attributions.values()
                if a.target_type == target_type and a.target_id == target_id
                and a.tenant_id == tenant_id]

    # --- Snapshot ---
    def snapshot(self, campaign_id: str, tenant_id: int) -> dict:
        camp = self._campaigns.get(campaign_id)
        if not camp or camp.tenant_id != tenant_id:
            return self._err("campaign_not_found", tenant_id)
        objs = [o.to_dict() for o in self._objectives.get(campaign_id, [])]
        tps = [t.to_dict() for t in self._touchpoints.values()
               if t.campaign_id == campaign_id]
        attrs = [a.to_dict() for a in self._attributions.values()
                 if a.campaign_id == campaign_id]
        return {"campaign": camp.to_dict(), "objectives": objs,
                "touchpoints": tps, "attributions": attrs}

    # --- Lifecycle ---
    def transition_campaign(self, campaign_id: str, new_state: str,
                             tenant_id: int) -> dict:
        camp = self._campaigns.get(campaign_id)
        if not camp or camp.tenant_id != tenant_id:
            return self._err("campaign_not_found", tenant_id)
        valid = {CampaignState.DRAFT: [CampaignState.ACTIVE, CampaignState.CANCELLED],
                 CampaignState.ACTIVE: [CampaignState.PAUSED, CampaignState.COMPLETED, CampaignState.CANCELLED],
                 CampaignState.PAUSED: [CampaignState.ACTIVE, CampaignState.CANCELLED],
                 CampaignState.COMPLETED: [], CampaignState.CANCELLED: []}
        if new_state not in valid.get(camp.state, []):
            return self._err("invalid_transition", tenant_id)
        camp.state = new_state
        return {"campaign_id": campaign_id, "state": new_state}

    def _err(self, reason: str, tenant_id: int = 1) -> dict:
        return {"error": reason, "tenant_id": tenant_id,
                "timestamp": datetime.now(timezone.utc).isoformat()}