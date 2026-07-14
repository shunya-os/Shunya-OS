"""
SHUNYA — Relationship Service (Phase 2)
"""
import json
from datetime import datetime
from typing import Optional
from app import db
from app.models import (
    Person, Relationship, RelationshipEvent, RelationshipCommitment,
    EmployeeProfile, CustomerProfile, SupplierContactProfile, ClientUserProfile,
)


class RelationshipType:
    CUSTOMER = "customer"
    EMPLOYEE = "employee"
    SUPPLIER_CONTACT = "supplier_contact"
    CLIENT_USER = "client_user"


class RelationshipStatus:
    PROSPECTIVE = "prospective"
    ACTIVE = "active"
    DORMANT = "dormant"
    ENDED = "ended"

    VALID_TRANSITIONS = {
        PROSPECTIVE: [ACTIVE, ENDED],
        ACTIVE: [DORMANT, ENDED],
        DORMANT: [ACTIVE, ENDED],
        ENDED: [],
    }


class CommitmentDirection:
    COMPANY_TO_PERSON = "company_to_person"
    PERSON_TO_COMPANY = "person_to_company"


class CommitmentStatus:
    OPEN = "open"
    RESOLVED = "resolved"
    CANCELLED = "cancelled"


class RelationshipService:
    """Tenant-scoped relationship operations."""

    def __init__(self, session=None):
        self._session = session or db.session

    def _verify_tenant(self, tenant_id: int, person_id: int) -> bool:
        person = self._session.get(Person, person_id)
        if not person:
            return False
        if tenant_id and person.tenant_id and person.tenant_id != tenant_id:
            return False
        return True

    # ------------------------------------------------------------------
    # Ensure relationship (idempotent)
    # ------------------------------------------------------------------

    def ensure_relationship(self, person_id: int, relationship_type: str,
                            tenant_id: Optional[int] = None,
                            status: str = RelationshipStatus.ACTIVE,
                            source: str = "") -> Relationship:
        if not self._verify_tenant(tenant_id, person_id):
            raise ValueError(f"Person {person_id} not in tenant {tenant_id}")

        existing = self._session.query(Relationship).filter(
            Relationship.tenant_id == tenant_id,
            Relationship.person_id == person_id,
            Relationship.relationship_type == relationship_type,
        ).first()

        if existing:
            return existing

        rel = Relationship(
            tenant_id=tenant_id,
            person_id=person_id,
            relationship_type=relationship_type,
            status=status,
            source=source,
            started_at=datetime.utcnow(),
        )
        self._session.add(rel)
        self._session.flush()

        self._record_event(rel.id, "RELATIONSHIP_CREATED", source=source)
        return rel

    def ensure_customer_relationship(self, person_id: int, tenant_id: Optional[int] = None) -> Relationship:
        return self.ensure_relationship(person_id, RelationshipType.CUSTOMER, tenant_id, source="customer_profile")

    def ensure_employee_relationship(self, person_id: int, tenant_id: Optional[int] = None) -> Relationship:
        return self.ensure_relationship(person_id, RelationshipType.EMPLOYEE, tenant_id, source="employee_profile")

    def ensure_supplier_contact_relationship(self, person_id: int, tenant_id: Optional[int] = None) -> Relationship:
        return self.ensure_relationship(person_id, RelationshipType.SUPPLIER_CONTACT, tenant_id, source="supplier_contact_profile")

    def ensure_client_user_relationship(self, person_id: int, tenant_id: Optional[int] = None) -> Relationship:
        return self.ensure_relationship(person_id, RelationshipType.CLIENT_USER, tenant_id, source="client_user_profile")

    # ------------------------------------------------------------------
    # Status transitions
    # ------------------------------------------------------------------

    def change_status(self, relationship_id: int, new_status: str, source: str = "") -> Relationship:
        rel = self._session.get(Relationship, relationship_id)
        if not rel:
            raise ValueError(f"Relationship {relationship_id} not found")
        allowed = RelationshipStatus.VALID_TRANSITIONS.get(rel.status, [])
        if new_status not in allowed:
            raise ValueError(f"Cannot transition from {rel.status} to {new_status}")
        rel.status = new_status
        if new_status == RelationshipStatus.ENDED:
            rel.ended_at = datetime.utcnow()
        self._session.flush()
        self._record_event(rel.id, "STATUS_CHANGED", source=source,
                           metadata={"from": rel.status, "to": new_status})
        return rel

    # ------------------------------------------------------------------
    # Role linkage
    # ------------------------------------------------------------------

    def link_role(self, person_id: int, relationship_type: str,
                  tenant_id: Optional[int] = None, source: str = "") -> Relationship:
        rel = self.ensure_relationship(person_id, relationship_type, tenant_id, source=source)
        self._record_event(rel.id, "ROLE_LINKED", source=source)
        return rel

    # ------------------------------------------------------------------
    # Events
    # ------------------------------------------------------------------

    def _record_event(self, relationship_id: int, event_type: str,
                      source: str = "", metadata: dict = None) -> RelationshipEvent:
        event = RelationshipEvent(
            relationship_id=relationship_id,
            event_type=event_type,
            source=source,
            metadata_json=json.dumps(metadata or {}),
        )
        self._session.add(event)
        self._session.flush()
        return event

    def get_events(self, relationship_id: int, limit: int = 50) -> list[dict]:
        events = (self._session.query(RelationshipEvent)
                   .filter(RelationshipEvent.relationship_id == relationship_id)
                   .order_by(RelationshipEvent.event_time.desc())
                   .limit(limit)
                   .all())
        return [e.to_dict() for e in events]

    # ------------------------------------------------------------------
    # Commitments
    # ------------------------------------------------------------------

    def create_commitment(self, relationship_id: int, summary: str,
                          direction: str = CommitmentDirection.COMPANY_TO_PERSON,
                          due_at: Optional[datetime] = None,
                          source: str = "", created_by: str = "") -> RelationshipCommitment:
        c = RelationshipCommitment(
            relationship_id=relationship_id,
            direction=direction,
            summary=summary,
            status=CommitmentStatus.OPEN,
            due_at=due_at,
            source=source,
            created_by=created_by,
        )
        self._session.add(c)
        self._session.flush()
        self._record_event(relationship_id, "COMMITMENT_RECORDED", source=source,
                           metadata={"commitment_id": c.id, "summary": summary[:100]})
        return c

    def resolve_commitment(self, commitment_id: int, note: str = "", source: str = "") -> RelationshipCommitment:
        c = self._session.get(RelationshipCommitment, commitment_id)
        if not c:
            raise ValueError(f"Commitment {commitment_id} not found")
        c.status = CommitmentStatus.RESOLVED
        c.resolved_at = datetime.utcnow()
        c.resolution_note = note
        self._session.flush()
        self._record_event(c.relationship_id, "COMMITMENT_RESOLVED", source=source,
                           metadata={"commitment_id": c.id})
        return c

    def cancel_commitment(self, commitment_id: int, note: str = "", source: str = "") -> RelationshipCommitment:
        c = self._session.get(RelationshipCommitment, commitment_id)
        if not c:
            raise ValueError(f"Commitment {commitment_id} not found")
        c.status = CommitmentStatus.CANCELLED
        c.resolved_at = datetime.utcnow()
        c.resolution_note = note
        self._session.flush()
        self._record_event(c.relationship_id, "COMMITMENT_RESOLVED", source=source,
                           metadata={"commitment_id": c.id, "cancelled": True})
        return c

    # ------------------------------------------------------------------
    # Queries
    # ------------------------------------------------------------------

    def get_open_commitments(self, relationship_id: int) -> list[RelationshipCommitment]:
        return (self._session.query(RelationshipCommitment)
                .filter(
                    RelationshipCommitment.relationship_id == relationship_id,
                    RelationshipCommitment.status == CommitmentStatus.OPEN,
                )
                .order_by(RelationshipCommitment.due_at.asc().nullslast())
                .all())

    def get_overdue_commitments(self, relationship_id: int) -> list[RelationshipCommitment]:
        now = datetime.utcnow()
        return (self._session.query(RelationshipCommitment)
                .filter(
                    RelationshipCommitment.relationship_id == relationship_id,
                    RelationshipCommitment.status == CommitmentStatus.OPEN,
                    RelationshipCommitment.due_at < now,
                )
                .order_by(RelationshipCommitment.due_at.asc())
                .all())

    def get_relationships_for_person(self, person_id: int,
                                     tenant_id: Optional[int] = None) -> list[Relationship]:
        q = self._session.query(Relationship).filter(Relationship.person_id == person_id)
        if tenant_id:
            q = q.filter(Relationship.tenant_id == tenant_id)
        return q.order_by(Relationship.created_at.desc()).all()

    def get_by_type(self, person_id: int, relationship_type: str,
                    tenant_id: Optional[int] = None) -> Optional[Relationship]:
        q = self._session.query(Relationship).filter(
            Relationship.person_id == person_id,
            Relationship.relationship_type == relationship_type,
        )
        if tenant_id:
            q = q.filter(Relationship.tenant_id == tenant_id)
        return q.first()

    # ------------------------------------------------------------------
    # Timeline
    # ------------------------------------------------------------------

    def get_timeline(self, relationship_id: int) -> list[dict]:
        return self.get_events(relationship_id)

    # ------------------------------------------------------------------
    # Summary
    # ------------------------------------------------------------------

    def get_summary(self, relationship_id: int) -> dict:
        """Deterministic relationship summary. No emotional/behavioural scores."""
        rel = self._session.get(Relationship, relationship_id)
        if not rel:
            return {}
        open_commitments = len(self.get_open_commitments(relationship_id))
        overdue_commitments = len(self.get_overdue_commitments(relationship_id))
        latest = (self._session.query(RelationshipEvent)
                   .filter(RelationshipEvent.relationship_id == relationship_id)
                   .order_by(RelationshipEvent.event_time.desc())
                   .first())
        return {
            "relationship_id": rel.id,
            "person_id": rel.person_id,
            "relationship_type": rel.relationship_type,
            "status": rel.status,
            "started_at": rel.started_at.isoformat() if rel.started_at else None,
            "ended_at": rel.ended_at.isoformat() if rel.ended_at else None,
            "open_commitments": open_commitments,
            "overdue_commitments": overdue_commitments,
            "latest_event": latest.to_dict() if latest else None,
        }