"""
Identity matching — resolves intake rows against Phase 1 Person foundation.
"""
import json
from typing import Optional
from app import db
from app.models import IntakeCandidate
from app.shunya.identity import IdentityResolver, normalize_email, normalize_phone


class IdentityMatchResult:
    MATCHED = "MATCHED"
    NO_MATCH = "NO_MATCH"
    AMBIGUOUS = "AMBIGUOUS"
    INSUFFICIENT_IDENTITY = "INSUFFICIENT_IDENTITY"
    CONFLICT = "CONFLICT"


class IdentityMatcher:
    """Matches intake rows against Phase 1 Person identities."""

    def __init__(self, session=None):
        self._session = session or db.session
        self._resolver = IdentityResolver(session=session)

    def resolve_row(self, row: dict, field_mappings: list[dict],
                    tenant_id: Optional[int] = None) -> dict:
        """Resolve a single row against Person identities. Returns match result dict."""
        fields = self._extract_fields(row, field_mappings)
        name = fields.get("name", "")
        email = fields.get("email", "")
        phone = fields.get("phone", "")
        employee_ref = fields.get("employee_ref", "")
        customer_ref = fields.get("customer_ref", "")

        # Check if we have any identity to resolve
        has_strong_id = bool(email or phone)
        has_weak_id = bool(name) and not has_strong_id

        if not email and not phone and not employee_ref and not customer_ref:
            if has_weak_id:
                return {
                    "status": IdentityMatchResult.INSUFFICIENT_IDENTITY,
                    "reason": "Name only — no strong identifier for resolution",
                    "fields": fields,
                }
            return {
                "status": IdentityMatchResult.INSUFFICIENT_IDENTITY,
                "reason": "No identifiable fields found in row",
                "fields": fields,
            }

        # Try both email and phone independently
        email_result = None
        phone_result = None

        if email:
            email_result = self._resolver.resolve_by_email(email, tenant_id)

        if phone:
            phone_result = self._resolver.resolve_by_phone(phone, tenant_id)

        # Check for conflict: email → Person A, phone → Person B
        if email_result and phone_result:
            if (email_result.status == IdentityMatchResult.MATCHED
                    and phone_result.status == IdentityMatchResult.MATCHED
                    and email_result.person.id != phone_result.person.id):
                return {
                    "status": IdentityMatchResult.CONFLICT,
                    "reason": f"Email resolves to Person #{email_result.person.id}, "
                              f"phone resolves to Person #{phone_result.person.id}",
                    "email_person_id": email_result.person.id,
                    "phone_person_id": phone_result.person.id,
                    "conflict_type": "email_phone_mismatch",
                    "fields": fields,
                }

        # Try email (strongest)
        if email_result and email_result.status == IdentityMatchResult.MATCHED:
            return {
                "status": IdentityMatchResult.MATCHED,
                "person_id": email_result.person.id,
                "method": "email",
                "fields": fields,
            }

        # Try phone
        if phone_result and phone_result.status == IdentityMatchResult.MATCHED:
            return {
                "status": IdentityMatchResult.MATCHED,
                "person_id": phone_result.person.id,
                "method": "phone",
                "fields": fields,
            }

        # Try reference
        if employee_ref:
            ref_result = self._resolver.resolve_by_reference("employee_ref", employee_ref, tenant_id)
            if ref_result.status == IdentityMatchResult.MATCHED:
                return {
                    "status": IdentityMatchResult.MATCHED,
                    "person_id": ref_result.person.id,
                    "method": "employee_ref",
                    "fields": fields,
                }

        if customer_ref:
            ref_result = self._resolver.resolve_by_reference("customer_ref", customer_ref, tenant_id)
            if ref_result.status == IdentityMatchResult.MATCHED:
                return {
                    "status": IdentityMatchResult.MATCHED,
                    "person_id": ref_result.person.id,
                    "method": "customer_ref",
                    "fields": fields,
                }

        # Check for AMBIGUOUS
        if email_result and email_result.status == IdentityMatchResult.AMBIGUOUS:
            return {
                "status": IdentityMatchResult.AMBIGUOUS,
                "reason": f"Email resolves to multiple Persons ({len(email_result.candidates)})",
                "candidate_count": len(email_result.candidates),
                "fields": fields,
            }

        # Valid strong identity but no match
        if has_strong_id:
            return {
                "status": IdentityMatchResult.NO_MATCH,
                "reason": f"Strong identifier found but no Person match in tenant",
                "fields": fields,
            }

        return {
            "status": IdentityMatchResult.INSUFFICIENT_IDENTITY,
            "reason": "Insufficient identity for deterministic resolution",
            "fields": fields,
        }

    def _extract_fields(self, row: dict, field_mappings: list[dict]) -> dict:
        """Extract canonical fields from row using mappings."""
        fields = {}
        for m in field_mappings:
            col = m["source_column"]
            target = m["target_field"]
            value = row.get(col, "")
            if not value or str(value).strip() == "":
                continue
            if target == "person.canonical_name" or target == "person.first_name":
                fields["name"] = str(value).strip()
            elif target == "identity.email":
                fields["email"] = normalize_email(str(value))
            elif target == "identity.phone":
                fields["phone"] = normalize_phone(str(value))
            elif target == "identity.employee_ref":
                fields["employee_ref"] = str(value).strip()
            elif target == "identity.customer_ref":
                fields["customer_ref"] = str(value).strip()
        return fields