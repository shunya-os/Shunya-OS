"""
SHUNYA — Creative Intelligence & Brand Runtime (Phase 15B, computation-only)
"""
import hashlib, json
from datetime import datetime
from typing import Optional


class BrandState:
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUPERSEDED = "superseded"


class CreativeState:
    DRAFT = "draft"
    COMPOSED = "composed"
    VALIDATED = "validated"
    APPROVED = "approved"
    HANDED_OFF = "handed_off"
    SUPERSEDED = "superseded"


class ValidationResult:
    VALID = "valid"
    INVALID = "invalid"
    INCOMPLETE = "incomplete"
    INSUFFICIENT_EVIDENCE = "insufficient_evidence"
    CONTRADICTORY_BRAND = "contradictory_brand"
    BLOCKED = "blocked"
    REQUIRES_REVIEW = "requires_review"
    INFERENCE_UNAVAILABLE = "inference_unavailable"


class BrandIdentity:
    def __init__(self, brand_id: str, tenant_id: int, name: str,
                 state: str = BrandState.ACTIVE,
                 provenance: Optional[str] = None):
        self.brand_id = brand_id
        self.tenant_id = tenant_id
        self.name = name
        self.state = state
        self.provenance = provenance
        self.version = 1
        self.created_at = datetime.utcnow().isoformat()

    def to_dict(self) -> dict:
        return {"brand_id": self.brand_id, "tenant_id": self.tenant_id,
                "name": self.name, "state": self.state, "version": self.version}


class BrandVersion:
    def __init__(self, brand_id: str, version: int, tenant_id: int,
                 dimensions: dict, state: str = BrandState.ACTIVE,
                 provenance: Optional[str] = None):
        self.brand_id = brand_id
        self.version = version
        self.tenant_id = tenant_id
        self.dimensions = dimensions
        self.state = state
        self.provenance = provenance
        self.created_at = datetime.utcnow().isoformat()

    def to_dict(self) -> dict:
        return {"brand_id": self.brand_id, "version": self.version,
                "dimensions": self.dimensions, "state": self.state}


class BrandEvidence:
    def __init__(self, evidence_id: str, brand_id: str, version: int,
                 tenant_id: int, dimension: str, value, source: str,
                 evidence_class: str = "tenant_assertion",
                 provenance: Optional[str] = None):
        self.evidence_id = evidence_id
        self.brand_id = brand_id
        self.version = version
        self.tenant_id = tenant_id
        self.dimension = dimension
        self.value = value
        self.source = source
        self.evidence_class = evidence_class
        self.provenance = provenance
        self.recorded_at = datetime.utcnow().isoformat()

    def to_dict(self) -> dict:
        return {"evidence_id": self.evidence_id, "dimension": self.dimension,
                "value": self.value, "source": self.source,
                "class": self.evidence_class}


class CreativeIntent:
    def __init__(self, intent_id: str, tenant_id: int,
                 campaign_ref: Optional[str] = None,
                 objective_ref: Optional[str] = None,
                 cohort_ref: Optional[str] = None,
                 channel: Optional[str] = None,
                 creative_type: str = "generic",
                 provenance: Optional[str] = None):
        self.intent_id = intent_id
        self.tenant_id = tenant_id
        self.campaign_ref = campaign_ref
        self.objective_ref = objective_ref
        self.cohort_ref = cohort_ref
        self.channel = channel
        self.creative_type = creative_type
        self.provenance = provenance

    def to_dict(self) -> dict:
        return {"intent_id": self.intent_id, "campaign_ref": self.campaign_ref,
                "creative_type": self.creative_type}


class Creative:
    def __init__(self, creative_id: str, tenant_id: int, intent_id: str,
                 creative_type: str, brand_id: str, brand_version: int,
                 content: dict, state: str = CreativeState.DRAFT,
                 provenance: Optional[str] = None):
        self.creative_id = creative_id
        self.tenant_id = tenant_id
        self.intent_id = intent_id
        self.creative_type = creative_type
        self.brand_id = brand_id
        self.brand_version = brand_version
        self.content = content
        self.state = state
        self.version = 1
        self.validation = None
        self.provenance = provenance
        self.created_at = datetime.utcnow().isoformat()

    def to_dict(self) -> dict:
        return {"creative_id": self.creative_id, "creative_type": self.creative_type,
                "brand_id": self.brand_id, "brand_version": self.brand_version,
                "state": self.state, "version": self.version}


class BrandService:
    """Phase 15B — Creative Intelligence & Brand Runtime."""

    def __init__(self):
        self._brands: dict[str, BrandIdentity] = {}
        self._brand_versions: dict[str, list[BrandVersion]] = {}
        self._evidence: dict[str, BrandEvidence] = {}
        self._intents: dict[str, CreativeIntent] = {}
        self._creatives: dict[str, Creative] = {}
        self._idempotency: set[str] = set()
        self._version = "15b.1"
        # Phase 14C reference (not instantiated here — owned by Phase 14C)
        self._inference_callback = None

    # --- Brand Identity ---
    def register_brand(self, name: str, tenant_id: int, dimensions: Optional[dict] = None,
                        idempotency_key: Optional[str] = None) -> dict:
        idem = idempotency_key or f"{tenant_id}:{name}"
        if idem in self._idempotency:
            return {"duplicate": True}
        self._idempotency.add(idem)
        bid = hashlib.sha256(idem.encode()).hexdigest()[:16]
        brand = BrandIdentity(bid, tenant_id, name)
        self._brands[bid] = brand
        # Set initial version
        bv = BrandVersion(bid, 1, tenant_id, dimensions or {})
        self._brand_versions[bid] = [bv]
        return {"brand_id": bid, "version": 1}

    def current_brand(self, tenant_id: int) -> dict:
        brands = [b for b in self._brands.values()
                  if b.tenant_id == tenant_id and b.state == BrandState.ACTIVE]
        if not brands:
            return self._err("no_active_brand", tenant_id)
        brand = brands[0]
        versions = self._brand_versions.get(brand.brand_id, [])
        active_ver = [v for v in versions if v.state == BrandState.ACTIVE]
        return {"brand": brand.to_dict(), "current_version": active_ver[0].to_dict() if active_ver else None}

    # --- Brand Version ---
    def new_brand_version(self, brand_id: str, tenant_id: int,
                           dimensions: dict) -> dict:
        brand = self._brands.get(brand_id)
        if not brand or brand.tenant_id != tenant_id:
            return self._err("brand_not_found", tenant_id)
        versions = self._brand_versions.get(brand_id, [])
        new_ver = len(versions) + 1
        bv = BrandVersion(brand_id, new_ver, tenant_id, dimensions)
        self._brand_versions.setdefault(brand_id, []).append(bv)
        return {"version": new_ver}

    def supersede_brand_version(self, brand_id: str, version: int,
                                 tenant_id: int) -> dict:
        versions = self._brand_versions.get(brand_id, [])
        for v in versions:
            if v.version == version and v.tenant_id == tenant_id:
                v.state = BrandState.SUPERSEDED
                return {"superseded": True}
        return self._err("version_not_found", tenant_id)

    # --- Brand Evidence ---
    def record_brand_evidence(self, brand_id: str, tenant_id: int,
                               dimension: str, value, source: str,
                               evidence_class: str = "tenant_assertion") -> dict:
        brand = self._brands.get(brand_id)
        if not brand or brand.tenant_id != tenant_id:
            return self._err("brand_not_found", tenant_id)
        eid = hashlib.sha256(f"{brand_id}:{dimension}:{source}".encode()).hexdigest()[:16]
        ev = BrandEvidence(eid, brand_id, brand.version, tenant_id,
                          dimension, value, source, evidence_class)
        self._evidence[eid] = ev
        return {"evidence_id": eid}

    # --- Creative Intent ---
    def create_intent(self, tenant_id: int, campaign_ref: Optional[str] = None,
                       creative_type: str = "generic",
                       channel: Optional[str] = None) -> dict:
        iid = hashlib.sha256(f"{tenant_id}:{campaign_ref or 'none'}:{creative_type}".encode()).hexdigest()[:16]
        intent = CreativeIntent(iid, tenant_id, campaign_ref=campaign_ref,
                                creative_type=creative_type, channel=channel)
        self._intents[iid] = intent
        return {"intent_id": iid}

    # --- Creative Lifecycle ---
    def create_creative(self, intent_id: str, tenant_id: int,
                         brand_id: str, content: dict,
                         brand_version: Optional[int] = None) -> dict:
        intent = self._intents.get(intent_id)
        if not intent or intent.tenant_id != tenant_id:
            return self._err("intent_not_found", tenant_id)
        brand = self._brands.get(brand_id)
        if not brand or brand.tenant_id != tenant_id:
            return self._err("brand_not_found", tenant_id)
        bv = brand_version or brand.version
        cid = hashlib.sha256(f"{intent_id}:{brand_id}:{bv}:{datetime.utcnow().isoformat()}".encode()).hexdigest()[:16]
        creative = Creative(cid, tenant_id, intent_id, intent.creative_type,
                           brand_id, bv, content, state=CreativeState.DRAFT)
        self._creatives[cid] = creative
        return {"creative_id": cid, "state": CreativeState.DRAFT}

    def validate_creative(self, creative_id: str, tenant_id: int,
                           policy_version: int = 1) -> dict:
        creative = self._creatives.get(creative_id)
        if not creative or creative.tenant_id != tenant_id:
            return self._err("creative_not_found", tenant_id)
        # Deterministic brand validation (no model)
        bv = self._brand_versions.get(creative.brand_id, [])
        active_bv = [v for v in bv if v.state == BrandState.ACTIVE]
        if not active_bv:
            creative.validation = {"result": ValidationResult.INSUFFICIENT_EVIDENCE,
                                    "policy_version": policy_version,
                                    "reason": "no_active_brand_version"}
            return creative.validation
        # Check creative version vs brand version
        if creative.brand_version != active_bv[0].version:
            creative.validation = {"result": ValidationResult.CONTRADICTORY_BRAND,
                                    "policy_version": policy_version,
                                    "reason": f"creative brand v{creative.brand_version} != active brand v{active_bv[0].version}"}
            return creative.validation
        # Basic content checks
        content = creative.content
        if not content or not isinstance(content, dict):
            creative.validation = {"result": ValidationResult.INCOMPLETE,
                                    "policy_version": policy_version,
                                    "reason": "empty_content"}
            return creative.validation
        creative.validation = {"result": ValidationResult.VALID,
                                "policy_version": policy_version,
                                "reason": "deterministic_validation"}
        creative.state = CreativeState.VALIDATED
        return creative.validation

    def approve_creative(self, creative_id: str, tenant_id: int) -> dict:
        creative = self._creatives.get(creative_id)
        if not creative or creative.tenant_id != tenant_id:
            return self._err("creative_not_found", tenant_id)
        if creative.state not in (CreativeState.VALIDATED, CreativeState.DRAFT):
            return self._err("creative_not_validated", tenant_id)
        creative.state = CreativeState.APPROVED
        return {"creative_id": creative_id, "state": CreativeState.APPROVED}

    def supersede_creative(self, creative_id: str, tenant_id: int) -> dict:
        creative = self._creatives.get(creative_id)
        if not creative or creative.tenant_id != tenant_id:
            return self._err("creative_not_found", tenant_id)
        creative.state = CreativeState.SUPERSEDED
        return {"creative_id": creative_id, "state": CreativeState.SUPERSEDED}

    # --- Phase 14C Inference Handoff ---
    def request_inference(self, capability: str, context: dict,
                           tenant_id: int = 1) -> dict:
        """Handoff to Phase 14C — does NOT call a provider directly."""
        if not self._inference_callback:
            return {"phase_14c_status": "not_connected",
                    "inference_required": True,
                    "capability": capability,
                    "result": None,
                    "provenance": {"deferred": True}}
        return self._inference_callback(capability, context, tenant_id)

    def set_inference_callback(self, callback):
        self._inference_callback = callback

    # --- Inspection ---
    def inspect_brand(self, brand_id: str, tenant_id: int) -> dict:
        brand = self._brands.get(brand_id)
        if not brand or brand.tenant_id != tenant_id:
            return self._err("brand_not_found", tenant_id)
        versions = [v.to_dict() for v in self._brand_versions.get(brand_id, [])]
        evs = [e.to_dict() for e in self._evidence.values()
               if e.brand_id == brand_id]
        return {"brand": brand.to_dict(), "versions": versions, "evidence": evs}

    def inspect_creative(self, creative_id: str, tenant_id: int) -> dict:
        creative = self._creatives.get(creative_id)
        if not creative or creative.tenant_id != tenant_id:
            return self._err("creative_not_found", tenant_id)
        return creative.to_dict()

    def _err(self, reason: str, tenant_id: int = 1) -> dict:
        return {"error": reason, "tenant_id": tenant_id,
                "timestamp": datetime.utcnow().isoformat()}