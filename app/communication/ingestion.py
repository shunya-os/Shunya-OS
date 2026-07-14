"""
SHUNYA — Communication Ingestion Service (Phase 3)
Authoritative pipeline enforcing:
CONNECTOR → SOURCE → CAPTURE POLICY → CAPTURE SCOPE → ELIGIBILITY → NORMALIZATION → CONVERSATION DOMAIN → IDENTITY → RELATIONSHIP
"""
from datetime import datetime
from typing import Optional
from app import db
from app.communication.models import (
    CommunicationSource, CommunicationCapturePolicy, CommunicationCaptureScope,
    ExternalConversation, ExternalMessage, ExternalParticipant,
    ExternalAttachmentReference, SyncCursor,
)
from app.communication.policy import CaptureEnforcer, CaptureVerdict
from app.communication.normalizer import MessageNormalizer
from app.communication.adapter import NormalizedMessage, CommunicationAdapter
from app.shunya.identity import IdentityResolver
from app.relationship.service import RelationshipService
from app.models import Lead


class IngestionResult:
    def __init__(self, accepted: bool = False, message: Optional[ExternalMessage] = None,
                 verdict: str = "", reason: str = "", lead_id: Optional[int] = None):
        self.accepted = accepted
        self.message = message
        self.verdict = verdict
        self.reason = reason
        self.lead_id = lead_id


class CommunicationIngestionService:
    """Authoritative ingestion pipeline for all inbound communication.
    Enforces capture governance before any content enters the system."""

    def __init__(self, session=None):
        self._session = session or db.session
        self._enforcer = CaptureEnforcer(session)
        self._normalizer = MessageNormalizer(session)
        self._identity_resolver = IdentityResolver(session)
        self._rel_svc = RelationshipService(session)

    def ingest(self, source_id: int, provider_chat_id: str,
               normalized_messages: list[NormalizedMessage],
               is_group: bool = False,
               tenant_id: Optional[int] = None) -> list[IngestionResult]:
        """
        Full ingestion pipeline:
        1. Resolve source
        2. Evaluate capture policy + scope
        3. If DENIED/PENDING → reject ALL messages for this chat
        4. If ALLOWED → normalize each message
        5. After normalization → safe identity resolution
        6. After identity → safe relationship association
        7. After relationship → deterministic Lead compatibility
        """
        results = []

        # --- STEP 1-3: CAPTURE GOVERNANCE ---
        verdict = self._enforcer.evaluate(source_id, provider_chat_id, is_group)

        if verdict["verdict"] == CaptureVerdict.DENIED:
            for msg in normalized_messages:
                results.append(IngestionResult(
                    accepted=False, verdict="denied",
                    reason=verdict.get("reason", "Chat denied"),
                ))
            return results

        if verdict["verdict"] == CaptureVerdict.PENDING_REVIEW:
            for msg in normalized_messages:
                results.append(IngestionResult(
                    accepted=False, verdict="pending_review",
                    reason=verdict.get("reason", "Chat pending review"),
                ))
            return results

        # --- STEP 4: NORMALIZATION (structural only) ---
        for nm in normalized_messages:
            msg = self._normalizer.normalize_message(
                nm, tenant_id=tenant_id, capture_status="allowed"
            )

            # --- STEP 5: SAFE IDENTITY RESOLUTION ---
            participant = None
            if nm.sender_raw:
                participant = self._normalizer.ensure_participant(
                    source_id=source_id,
                    provider_participant_id=nm.sender_raw,
                    display_name=nm.sender_display_name,
                    raw_identifier=nm.sender_normalized,
                    tenant_id=tenant_id,
                )

            if participant and nm.sender_normalized:
                self._resolve_participant_identity(participant, nm, tenant_id)

            # --- STEP 6: SAFE RELATIONSHIP ASSOCIATION ---
            rel_info = self._associate_relationship(participant, source_id, tenant_id)

            # --- STEP 7: LEAD COMPATIBILITY ---
            lead_id = self._handle_lead_compatibility(msg, nm, participant, source_id, tenant_id)

            self._session.commit()

            results.append(IngestionResult(
                accepted=True, message=msg,
                verdict="allowed", reason="Ingested through governed pipeline",
                lead_id=lead_id,
            ))

        return results

    def _resolve_participant_identity(self, participant: ExternalParticipant,
                                       nm: NormalizedMessage,
                                       tenant_id: Optional[int] = None):
        """Resolve participant identity using Phase 1 IdentityResolver.
        Only MATCHED links to Person. AMBIGUOUS/CONFLICT/INSUFFICIENT remain unresolved."""
        identifier = nm.sender_normalized or nm.sender_raw
        if not identifier:
            return

        # Try email first, then phone
        result = None
        if "@" in identifier:
            result = self._identity_resolver.resolve_by_email(identifier, tenant_id)
        elif identifier.startswith("+"):
            result = self._identity_resolver.resolve_by_phone(identifier, tenant_id)

        if result and result.status == "MATCHED":
            participant.person_id = result.person.id
            participant.identity_resolution_status = "matched"
        elif result and result.status == "AMBIGUOUS":
            participant.identity_resolution_status = "ambiguous"
        elif result and result.status == "CONFLICT":
            participant.identity_resolution_status = "conflict"
        else:
            participant.identity_resolution_status = "unresolved"

    def _associate_relationship(self, participant: Optional[ExternalParticipant],
                                 source_id: int,
                                 tenant_id: Optional[int] = None) -> dict:
        """Associate relationship if participant is MATCHED.
        MIXED_USE: ALLOWED does NOT auto-establish CUSTOMER.
        BUSINESS_DEDICATED: eligible deterministic path may establish CUSTOMER."""
        if not participant or not participant.person_id:
            return {"relationship": None}

        source = self._session.get(CommunicationSource, source_id)
        if not source:
            return {"relationship": None}

        # MIXED_USE: ALLOWED does NOT auto-establish CUSTOMER
        if source.account_mode == "mixed_use":
            return {"relationship": None, "note": "MIXED_USE: no auto-relationship"}

        # BUSINESS_DEDICATED: may ensure CUSTOMER for eligible business contacts
        if source.account_mode == "business_dedicated" and participant.identity_resolution_status == "matched":
            rel = self._rel_svc.ensure_customer_relationship(participant.person_id, tenant_id)
            return {"relationship": rel.id if rel else None}

        return {"relationship": None}

    def _handle_lead_compatibility(self, msg: ExternalMessage, nm: NormalizedMessage,
                                    participant: Optional[ExternalParticipant],
                                    source_id: int,
                                    tenant_id: Optional[int] = None) -> Optional[int]:
        """Deterministic Lead compatibility for eligible business conversations.
        Does NOT create one Lead per message. Checks for existing Lead for this conversation."""
        source = self._session.get(CommunicationSource, source_id)
        if not source or source.account_mode != "business_dedicated":
            return None
        if not participant or not participant.person_id:
            return None

        # Check if Lead already exists for this Person
        existing_lead = self._session.query(Lead).filter(
            Lead.person_id == participant.person_id
        ).first()
        if existing_lead:
            return existing_lead.id  # No duplicate Lead

        # Create Lead only for first eligible business message
        from app.models import next_inquiry_code
        code = next_inquiry_code(self._session)
        lead = Lead(
            code=code, source="whatsapp",
            customer_name=participant.display_name or nm.sender_raw,
            phone=nm.sender_normalized or nm.sender_raw,
            destination="",
            notes=nm.body[:500] if nm.body else "",
            status="new",
            person_id=participant.person_id,
        )
        self._session.add(lead)
        self._session.flush()
        return lead.id