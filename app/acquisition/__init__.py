"""
SHUNYA — Acquisition Source & Paid Lead Intake (Phase 14D, computation-only)
"""
import hashlib, json
from datetime import datetime
from typing import Optional

# Authenticity states
class AuthState:
    VERIFIED = "verified"
    UNVERIFIED = "unverified"
    UNSUPPORTED = "verification_not_supported"
    FAILED = "verification_failed"
    REPLAY_DETECTED = "replay_detected"
    MALFORMED = "malformed"

# Intake lifecycle
class IntakeState:
    RECEIVED = "received"
    AUTH_CHECKED = "authenticity_pending"
    REJECTED = "rejected"
    NORMALIZED = "normalized"
    DUPLICATE_DELIVERY = "duplicate_delivery"
    IDENTITY_PENDING = "identity_resolution_pending"
    ACCEPTED = "accepted"
    HANDED_OFF = "handed_off"
    FAILED = "failed"

# Failure states
class IntakeFailure:
    MALFORMED_PAYLOAD = "malformed_payload"
    ADAPTER_UNSUPPORTED = "adapter_unsupported"
    SOURCE_UNKNOWN = "source_unknown"
    SOURCE_DISABLED = "source_disabled"
    AUTH_FAILED = "authenticity_failed"
    REPLAY_DUPLICATE = "replay_duplicate"
    NORMALIZATION_FAILED = "normalization_failed"
    IDENTITY_UNRESOLVED = "identity_unresolved"
    HANDOFF_FAILED = "handoff_failed"
    POLICY_DENIED = "policy_denied"

# Source types
class SourceType:
    REFERRAL = "referral"
    DIRECT = "direct"
    ORGANIC = "organic"
    PAID = "paid"
    PARTNER = "partner"
    IMPORT = "import"
    API = "api"


class AcquisitionSource:
    def __init__(self, source_id: str, tenant_id: int, source_type: str,
                 name: str, provider: Optional[str] = None,
                 status: str = "active", channel: Optional[str] = None,
                 paid: bool = False, provenance: Optional[str] = None):
        self.source_id = source_id
        self.tenant_id = tenant_id
        self.source_type = source_type
        self.name = name
        self.provider = provider
        self.status = status
        self.channel = channel
        self.paid = paid
        self.provenance = provenance

    def to_dict(self) -> dict:
        return {
            "source_id": self.source_id,
            "tenant_id": self.tenant_id,
            "source_type": self.source_type,
            "name": self.name,
            "provider": self.provider,
            "status": self.status,
            "channel": self.channel,
            "paid": self.paid,
        }


class AcquisitionAttribution:
    def __init__(self, source_id: str, channel: Optional[str] = None,
                 campaign_id: Optional[str] = None, campaign_name: Optional[str] = None,
                 ad_id: Optional[str] = None, ad_set_id: Optional[str] = None,
                 creative_id: Optional[str] = None, form_id: Optional[str] = None,
                 landing_page: Optional[str] = None,
                 referrer_id: Optional[str] = None,
                 utm_source: Optional[str] = None, utm_medium: Optional[str] = None,
                 utm_campaign: Optional[str] = None, utm_term: Optional[str] = None,
                 utm_content: Optional[str] = None):
        self.source_id = source_id
        self.channel = channel
        self.campaign_id = campaign_id
        self.campaign_name = campaign_name
        self.ad_id = ad_id
        self.ad_set_id = ad_set_id
        self.creative_id = creative_id
        self.form_id = form_id
        self.landing_page = landing_page
        self.referrer_id = referrer_id
        self.utm_source = utm_source
        self.utm_medium = utm_medium
        self.utm_campaign = utm_campaign
        self.utm_term = utm_term
        self.utm_content = utm_content

    def to_dict(self) -> dict:
        return {k: v for k, v in self.__dict__.items() if v is not None}


class RawIntakeEvidence:
    def __init__(self, source_id: str, raw_payload: dict, received_at: Optional[str] = None,
                 external_event_id: Optional[str] = None, authenticity: str = AuthState.UNVERIFIED,
                 payload_hash: Optional[str] = None):
        self.source_id = source_id
        self.raw_payload = raw_payload
        self.received_at = received_at or datetime.utcnow().isoformat()
        self.external_event_id = external_event_id
        self.authenticity = authenticity
        self.payload_hash = payload_hash or hashlib.sha256(
            json.dumps(raw_payload, sort_keys=True).encode()).hexdigest()[:16]

    def to_dict(self) -> dict:
        return {
            "source_id": self.source_id,
            "received_at": self.received_at,
            "external_event_id": self.external_event_id,
            "authenticity": self.authenticity,
            "payload_hash": self.payload_hash,
        }


class AcquisitionIntakeEnvelope:
    def __init__(self, intake_id: str, source: AcquisitionSource,
                 attribution: AcquisitionAttribution,
                 raw_evidence: RawIntakeEvidence,
                 identity_signals: dict,
                 commercial_fields: dict,
                 consent: Optional[dict] = None,
                 state: str = IntakeState.RECEIVED):
        self.intake_id = intake_id
        self.source = source
        self.attribution = attribution
        self.raw_evidence = raw_evidence
        self.identity_signals = identity_signals
        self.commercial_fields = commercial_fields
        self.consent = consent
        self.state = state
        self.created_at = datetime.utcnow().isoformat()

    def to_dict(self) -> dict:
        return {
            "intake_id": self.intake_id,
            "source": self.source.to_dict(),
            "attribution": self.attribution.to_dict(),
            "raw_evidence": self.raw_evidence.to_dict(),
            "identity_signals": self.identity_signals,
            "commercial_fields": self.commercial_fields,
            "consent": self.consent,
            "state": self.state,
            "created_at": self.created_at,
        }


class AcquisitionService:
    """Acquisition Source & Paid Lead Intake.

    Business-agnostic intake layer. No travel hardcoding.
    No paid-model calls. No Hermes credentials.
    """

    def __init__(self):
        self._sources: dict[str, AcquisitionSource] = {}
        self._evidence_store: dict[str, RawIntakeEvidence] = {}
        self._idempotency: set[str] = set()
        self._version = "14d.1"

    # ------------------------------------------------------------------
    # Source management
    # ------------------------------------------------------------------
    def register_source(self, source: AcquisitionSource) -> dict:
        self._sources[source.source_id] = source
        return {"registered": True, "source_id": source.source_id}

    def get_source(self, source_id: str) -> Optional[AcquisitionSource]:
        return self._sources.get(source_id)

    def list_sources(self, tenant_id: Optional[int] = None) -> list:
        if tenant_id is not None:
            return [s.to_dict() for s in self._sources.values() if s.tenant_id == tenant_id]
        return [s.to_dict() for s in self._sources.values()]

    # ------------------------------------------------------------------
    # Intake processing
    # ------------------------------------------------------------------
    def process_intake(self, source_id: str, raw_payload: dict,
                       adapter_type: str = "generic",
                       external_event_id: Optional[str] = None,
                       tenant_id: int = 1) -> dict:
        """Process an incoming acquisition intake end-to-end."""
        # Source resolution
        source = self._sources.get(source_id)
        if source is None:
            return self._fail(IntakeFailure.SOURCE_UNKNOWN, source_id, tenant_id)
        if source.status != "active":
            return self._fail(IntakeFailure.SOURCE_DISABLED, source_id, tenant_id)

        # Adapter dispatch
        if adapter_type not in ("generic", "webhook", "fake"):
            return self._fail(IntakeFailure.ADAPTER_UNSUPPORTED, source_id, tenant_id)

        # Raw evidence capture
        evidence = RawIntakeEvidence(
            source_id=source_id,
            raw_payload=raw_payload,
            external_event_id=external_event_id,
        )
        self._evidence_store[evidence.payload_hash] = evidence

        # Idempotency check
        idem_key = external_event_id or evidence.payload_hash
        tenant_scoped_key = f"{tenant_id}:{source_id}:{idem_key}"
        if tenant_scoped_key in self._idempotency:
            return self._fail(IntakeFailure.REPLAY_DUPLICATE, source_id, tenant_id,
                              detail="duplicate_external_delivery", evidence=evidence.to_dict())
        self._idempotency.add(tenant_scoped_key)

        # Normalization (deterministic fake adapter)
        norm = self._normalize_payload(source, raw_payload, evidence, adapter_type, tenant_id)
        if "error" in norm:
            return norm

        envelope = norm["envelope"]
        envelope.state = IntakeState.NORMALIZED

        # Identity signals (no blind customer creation)
        identity_signals = envelope.identity_signals
        identity_result = self._resolve_identity(identity_signals, tenant_id)
        if identity_result.get("unresolvable"):
            envelope.state = IntakeState.IDENTITY_PENDING
        else:
            envelope.state = IntakeState.ACCEPTED

        # Build result
        result = {
            "intake_id": envelope.intake_id,
            "state": envelope.state,
            "source_id": source_id,
            "source_type": source.source_type,
            "paid": source.paid,
            "attribution": envelope.attribution.to_dict(),
            "identity_signals": identity_signals,
            "identity_result": identity_result,
            "evidence": evidence.to_dict(),
            "tenant_id": tenant_id,
            "timestamp": datetime.utcnow().isoformat(),
        }

        # Handoff to lead/commercial-interest
        if envelope.state == IntakeState.ACCEPTED:
            handoff = self._handoff_to_lead(envelope, tenant_id)
            result["handoff"] = handoff
            envelope.state = IntakeState.HANDED_OFF
            result["state"] = IntakeState.HANDED_OFF

        return result

    def _normalize_payload(self, source: AcquisitionSource, raw_payload: dict,
                           evidence: RawIntakeEvidence, adapter_type: str,
                           tenant_id: int) -> dict:
        """Normalize a provider payload into an acquisition intake envelope."""
        if not isinstance(raw_payload, dict):
            return self._fail(IntakeFailure.MALFORMED_PAYLOAD, source.source_id, tenant_id)

        # Extract identity signals from payload
        identity_signals = {
            "name": raw_payload.get("name"),
            "email": raw_payload.get("email"),
            "phone": raw_payload.get("phone"),
            "organization": raw_payload.get("organization"),
        }
        # Remove None values — missing is not fabricated
        identity_signals = {k: v for k, v in identity_signals.items() if v is not None}

        # Extract commercial intent fields (business-agnostic)
        commercial_fields = {
            "interest": raw_payload.get("interest"),
            "message": raw_payload.get("message"),
            "budget": raw_payload.get("budget"),
            "timeline": raw_payload.get("timeline"),
        }
        commercial_fields = {k: v for k, v in commercial_fields.items() if v is not None}

        # Extract UTM/attribution fields
        attribution = AcquisitionAttribution(
            source_id=source.source_id,
            channel=raw_payload.get("channel"),
            campaign_id=raw_payload.get("campaign_id"),
            campaign_name=raw_payload.get("campaign_name"),
            ad_id=raw_payload.get("ad_id"),
            ad_set_id=raw_payload.get("ad_set_id"),
            creative_id=raw_payload.get("creative_id"),
            form_id=raw_payload.get("form_id"),
            landing_page=raw_payload.get("landing_page"),
            referrer_id=raw_payload.get("referrer_id"),
            utm_source=raw_payload.get("utm_source"),
            utm_medium=raw_payload.get("utm_medium"),
            utm_campaign=raw_payload.get("utm_campaign"),
            utm_term=raw_payload.get("utm_term"),
            utm_content=raw_payload.get("utm_content"),
        )

        # Consent
        consent = raw_payload.get("consent")

        intake_id = hashlib.sha256(
            f"{source.source_id}:{evidence.payload_hash}:{datetime.utcnow().isoformat()}".encode()
        ).hexdigest()[:16]

        envelope = AcquisitionIntakeEnvelope(
            intake_id=intake_id,
            source=source,
            attribution=attribution,
            raw_evidence=evidence,
            identity_signals=identity_signals,
            commercial_fields=commercial_fields,
            consent=consent,
        )

        return {"envelope": envelope}

    def _resolve_identity(self, identity_signals: dict, tenant_id: int) -> dict:
        """Resolve identity signals against existing customers."""
        if not identity_signals:
            return {"match": None, "confidence": "none", "unresolvable": True,
                    "reason": "no_identity_signals"}
        # Deterministic: by email if present
        email = identity_signals.get("email")
        if email:
            return {"match": "possible", "confidence": "medium",
                    "candidate_email": email, "unresolvable": False}
        phone = identity_signals.get("phone")
        if phone:
            return {"match": "possible", "confidence": "low",
                    "candidate_phone": phone, "unresolvable": False}
        return {"match": None, "confidence": "none", "unresolvable": True,
                "reason": "insufficient_signals"}

    def _handoff_to_lead(self, envelope: AcquisitionIntakeEnvelope, tenant_id: int) -> dict:
        """Handoff normalized intake to existing lead/commercial-interest."""
        return {
            "handoff": "lead_created",
            "intake_id": envelope.intake_id,
            "source_id": envelope.source.source_id,
            "source_type": envelope.source.source_type,
            "paid": envelope.source.paid,
            "attribution": envelope.attribution.to_dict(),
            "identity_signals": envelope.identity_signals,
            "commercial_fields": envelope.commercial_fields,
        }

    # ------------------------------------------------------------------
    # Inspection
    # ------------------------------------------------------------------
    def inspect_intake(self, intake_result: dict) -> dict:
        return {
            "intake_id": intake_result.get("intake_id"),
            "state": intake_result.get("state"),
            "source_id": intake_result.get("source_id"),
            "source_type": intake_result.get("source_type"),
            "paid": intake_result.get("paid"),
            "tenant_id": intake_result.get("tenant_id"),
        }

    def explain_intake(self, intake_result: dict) -> dict:
        return {
            "intake_id": intake_result.get("intake_id"),
            "state": intake_result.get("state"),
            "attribution": intake_result.get("attribution"),
            "identity_result": intake_result.get("identity_result"),
            "handoff": intake_result.get("handoff"),
        }

    def _fail(self, reason: str, source_id: str, tenant_id: int = 1,
              detail: str = "", evidence: Optional[dict] = None) -> dict:
        return {
            "error": reason,
            "detail": detail,
            "source_id": source_id,
            "tenant_id": tenant_id,
            "state": IntakeState.FAILED,
            "evidence": evidence,
            "timestamp": datetime.utcnow().isoformat(),
        }