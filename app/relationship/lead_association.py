"""
SHUNYA — Legacy Lead Safe Association Service (Phase 2)
"""
from typing import Optional
from app import db
from app.models import Lead, Person, Relationship
from app.shunya.identity import IdentityResolver, normalize_email, normalize_phone
from app.relationship.service import RelationshipService


class LeadAssociationService:
    """Tenant-scoped service for safely associating legacy Leads with Person and CUSTOMER Relationship."""

    def __init__(self, session=None):
        self._session = session or db.session
        self._resolver = IdentityResolver(session=session)
        self._rel_svc = RelationshipService(session=session)

    def resolve_lead_person(self, lead: Lead, tenant_id: Optional[int] = None) -> dict:
        """Resolve a Lead to a Person using Phase 1 identity resolution.
        Returns MATCHED, NO_MATCH, CONFLICT, or INSUFFICIENT_IDENTITY."""
        email = normalize_email(lead.email or "")
        phone = normalize_phone(lead.phone or "")
        name = lead.customer_name or ""

        # Name only — insufficient
        if not email and not phone:
            return {"status": "INSUFFICIENT_IDENTITY", "reason": "Name only — no strong identifier"}

        # Check for conflict: email → Person A, phone → Person B
        if email and phone:
            email_result = self._resolver.resolve_by_email(email, tenant_id)
            phone_result = self._resolver.resolve_by_phone(phone, tenant_id)

            if (email_result.status == "MATCHED" and phone_result.status == "MATCHED"
                    and email_result.person.id != phone_result.person.id):
                return {
                    "status": "CONFLICT",
                    "reason": f"Email → Person {email_result.person.id}, Phone → Person {phone_result.person.id}",
                    "email_person_id": email_result.person.id,
                    "phone_person_id": phone_result.person.id,
                }

        # Try email (strongest)
        if email:
            result = self._resolver.resolve_by_email(email, tenant_id)
            if result.status == "MATCHED":
                return {"status": "MATCHED", "person_id": result.person.id}

        # Try phone
        if phone:
            result = self._resolver.resolve_by_phone(phone, tenant_id)
            if result.status == "MATCHED":
                return {"status": "MATCHED", "person_id": result.person.id}

        return {"status": "NO_MATCH", "reason": "Strong identifiers found but no Person match"}

    def ensure_customer_relationship_for_lead(self, lead: Lead,
                                              tenant_id: Optional[int] = None) -> dict:
        """Safely associate a Lead with a Person and ensure CUSTOMER Relationship.
        Does NOT modify Lead records."""
        resolution = self.resolve_lead_person(lead, tenant_id)

        if resolution["status"] == "MATCHED":
            person_id = resolution["person_id"]
            rel = self._rel_svc.ensure_customer_relationship(person_id, tenant_id)
            return {
                "status": "MATCHED",
                "person_id": person_id,
                "relationship_id": rel.id,
                "relationship_type": rel.relationship_type,
            }

        if resolution["status"] == "CONFLICT":
            return resolution  # No automatic association

        return resolution  # NO_MATCH or INSUFFICIENT_IDENTITY — no association

    def get_leads_for_person(self, person: Person, tenant_id: Optional[int] = None) -> list[Lead]:
        """Get all Leads safely associated with a Person through identity resolution."""
        person_email = None
        person_phone = None
        for pi in person.identities:
            if pi.identity_type == "email":
                person_email = pi.normalized_value
            elif pi.identity_type == "phone":
                person_phone = pi.normalized_value

        query = self._session.query(Lead)
        filters = []
        if person_email:
            filters.append(Lead.email == person_email)
        if person_phone:
            filters.append(Lead.phone == person_phone)
        if not filters:
            return []

        from sqlalchemy import or_
        return query.filter(or_(*filters)).order_by(Lead.created_at.desc()).all()