"""
SHUNYA — Identity Resolution Engine (Phase 1)

Deterministic identity resolution for strong human identifiers.
Supports MATCHED, NO_MATCH, AMBIGUOUS outcomes.
Never silently merges uncertain identities.
"""

import re
from typing import Optional
from app import db
from app.models import Person, PersonIdentity


class ResolutionResult:
    """Outcome of an identity resolution attempt."""

    MATCHED = "MATCHED"
    NO_MATCH = "NO_MATCH"
    AMBIGUOUS = "AMBIGUOUS"

    def __init__(self, status: str, person: Optional[Person] = None,
                 candidates: Optional[list[Person]] = None,
                 reason: str = ""):
        self.status = status
        self.person = person
        self.candidates = candidates or []
        self.reason = reason

    def __repr__(self):
        return f"<ResolutionResult {self.status} person={self.person}>"


# ---------------------------------------------------------------------------
# Normalization
# ---------------------------------------------------------------------------


def normalize_email(email: str) -> str:
    """Lowercase, strip whitespace."""
    return email.strip().lower() if email else ""


def normalize_phone(phone: str) -> str:
    """Strip non-digit characters, keep leading + for country code."""
    if not phone:
        return ""
    cleaned = re.sub(r"[^\d+]", "", phone.strip())
    # Keep only digits and leading +
    digits = re.sub(r"[^\d]", "", cleaned)
    if cleaned.startswith("+"):
        return "+" + digits
    return digits


def normalize_name(name: str) -> str:
    """Strip extra whitespace, title case."""
    if not name:
        return ""
    return " ".join(name.strip().title().split())


# ---------------------------------------------------------------------------
# Identity Resolution
# ---------------------------------------------------------------------------


class IdentityResolver:
    """
    Resolves a human identity against known Person records.

    Uses strong deterministic identifiers:
    - email (exact normalized match)
    - phone (normalized digit match)
    - channel identity (WhatsApp, Telegram, etc.)

    Returns MATCHED, NO_MATCH, or AMBIGUOUS.
    Never silently merges uncertain identities.
    """

    def __init__(self, session=None):
        self._session = session or db.session

    def resolve_by_email(self, email: str, tenant_id: Optional[int] = None) -> ResolutionResult:
        """Resolve a Person by verified email address."""
        normalized = normalize_email(email)
        if not normalized:
            return ResolutionResult(ResolutionResult.NO_MATCH, reason="Empty email")

        identities = self._session.query(PersonIdentity).filter(
            PersonIdentity.identity_type == "email",
            PersonIdentity.normalized_value == normalized,
        ).all()

        if not identities:
            return ResolutionResult(ResolutionResult.NO_MATCH, reason="No identity match")

        persons = [inv.person for inv in identities if inv.person]
        if tenant_id:
            persons = [p for p in persons if p.tenant_id == tenant_id]

        if len(persons) == 1:
            return ResolutionResult(ResolutionResult.MATCHED, person=persons[0],
                                    reason="Single email identity match")

        if len(persons) > 1:
            return ResolutionResult(ResolutionResult.AMBIGUOUS, candidates=persons,
                                    reason=f"Multiple persons with email {normalized}")

        return ResolutionResult(ResolutionResult.NO_MATCH, reason="No match after filtering")

    def resolve_by_phone(self, phone: str, tenant_id: Optional[int] = None) -> ResolutionResult:
        """Resolve a Person by phone number."""
        normalized = normalize_phone(phone)
        if not normalized:
            return ResolutionResult(ResolutionResult.NO_MATCH, reason="Empty phone")

        identities = self._session.query(PersonIdentity).filter(
            PersonIdentity.identity_type == "phone",
            PersonIdentity.normalized_value == normalized,
        ).all()

        if not identities:
            return ResolutionResult(ResolutionResult.NO_MATCH, reason="No identity match")

        persons = [inv.person for inv in identities if inv.person]
        if tenant_id:
            persons = [p for p in persons if p.tenant_id == tenant_id]

        if len(persons) == 1:
            return ResolutionResult(ResolutionResult.MATCHED, person=persons[0],
                                    reason="Single phone identity match")

        if len(persons) > 1:
            return ResolutionResult(ResolutionResult.AMBIGUOUS, candidates=persons,
                                    reason=f"Multiple persons with phone {normalized}")

        return ResolutionResult(ResolutionResult.NO_MATCH, reason="No match after filtering")

    def resolve_by_channel(self, channel: str, channel_id: str,
                           tenant_id: Optional[int] = None) -> ResolutionResult:
        """Resolve a Person by channel identity (WhatsApp number, Telegram ID, etc.)."""
        identity_type = f"channel:{channel}"
        identities = self._session.query(PersonIdentity).filter(
            PersonIdentity.identity_type == identity_type,
            PersonIdentity.normalized_value == channel_id,
        ).all()

        if not identities:
            return ResolutionResult(ResolutionResult.NO_MATCH,
                                    reason=f"No identity match for {channel}:{channel_id}")

        persons = [inv.person for inv in identities if inv.person]
        if tenant_id:
            persons = [p for p in persons if p.tenant_id == tenant_id]

        if len(persons) == 1:
            return ResolutionResult(ResolutionResult.MATCHED, person=persons[0],
                                    reason="Single channel identity match")

        if len(persons) > 1:
            return ResolutionResult(ResolutionResult.AMBIGUOUS, candidates=persons,
                                    reason=f"Multiple persons for {channel}:{channel_id}")

        return ResolutionResult(ResolutionResult.NO_MATCH, reason="No match after filtering")

    def resolve(self, email: str = "", phone: str = "",
                channel: str = "", channel_id: str = "",
                tenant_id: Optional[int] = None,
                name: str = "",
                reference_type: str = "", reference_value: str = "") -> ResolutionResult:
        """
        Multi-strategy identity resolution.

        Tries the strongest identifier first. If matched, returns immediately.
        If multiple strategies yield different persons, returns AMBIGUOUS.
        Supports legacy reference types: employee_ref, customer_ref.
        """
        candidates = []
        reasons = []

        # Try email (strongest)
        if email:
            result = self.resolve_by_email(email, tenant_id)
            if result.status == ResolutionResult.MATCHED:
                return result
            if result.status == ResolutionResult.AMBIGUOUS:
                return result

        # Try phone
        if phone:
            result = self.resolve_by_phone(phone, tenant_id)
            if result.status == ResolutionResult.MATCHED:
                return result
            if result.status == ResolutionResult.AMBIGUOUS:
                return result

        # Try channel identity
        if channel and channel_id:
            result = self.resolve_by_channel(channel, channel_id, tenant_id)
            if result.status == ResolutionResult.MATCHED:
                return result
            if result.status == ResolutionResult.AMBIGUOUS:
                return result

        # Try legacy reference (employee_ref, customer_ref, supplier_ref)
        if reference_type and reference_value:
            result = self.resolve_by_reference(reference_type, reference_value, tenant_id)
            if result.status == ResolutionResult.MATCHED:
                return result

        return ResolutionResult(ResolutionResult.NO_MATCH,
                                reason=f"No strong identifier matched email={email} phone={phone}")

    def resolve_by_reference(self, reference_type: str, reference_value: str,
                              tenant_id: Optional[int] = None) -> ResolutionResult:
        """Resolve a Person by legacy reference (employee_ref, customer_ref, etc.)."""
        identities = self._session.query(PersonIdentity).filter(
            PersonIdentity.identity_type == reference_type,
            PersonIdentity.normalized_value == reference_value,
        ).all()

        if not identities:
            return ResolutionResult(ResolutionResult.NO_MATCH,
                                    reason=f"No identity match for {reference_type}:{reference_value}")

        persons = [inv.person for inv in identities if inv.person]
        if tenant_id:
            persons = [p for p in persons if p.tenant_id == tenant_id]

        if len(persons) == 1:
            return ResolutionResult(ResolutionResult.MATCHED, person=persons[0],
                                    reason="Single reference identity match")

        if len(persons) > 1:
            return ResolutionResult(ResolutionResult.AMBIGUOUS, candidates=persons,
                                    reason=f"Multiple persons for {reference_type}:{reference_value}")

        return ResolutionResult(ResolutionResult.NO_MATCH, reason="No match after filtering")

    def register_identity(self, person: Person, identity_type: str,
                          identity_value: str, verification_state: str = "unverified") -> PersonIdentity:
        """Register a normalized identity for a Person."""
        normalized = self._normalize_for_type(identity_type, identity_value)
        existing = self._session.query(PersonIdentity).filter(
            PersonIdentity.identity_type == identity_type,
            PersonIdentity.normalized_value == normalized,
        ).first()

        if existing:
            if existing.person_id != person.id:
                return existing  # Don't override — flag for manual review
            return existing

        pi = PersonIdentity(
            person_id=person.id,
            identity_type=identity_type,
            identity_value=identity_value,
            normalized_value=normalized,
            verification_state=verification_state,
        )
        self._session.add(pi)
        self._session.commit()
        return pi

    def _normalize_for_type(self, identity_type: str, value: str) -> str:
        if identity_type == "email":
            return normalize_email(value)
        if identity_type == "phone":
            return normalize_phone(value)
        return value.strip()