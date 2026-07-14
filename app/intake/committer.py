"""
Governed commit — writes approved intake candidates to canonical tables.
Only APPROVED/explicitly committed proposals may write canonical data.
"""
import json
from typing import Optional
from app import db
from app.models import (
    Person, PersonIdentity, IntakeSession, IntakeCandidate,
    EmployeeProfile, CustomerProfile,
)
from app.shunya.identity import normalize_email, normalize_phone
from app.intake.session import IntakeSessionState


class GovernedCommitter:
    """Commits approved intake candidates to canonical tables."""

    def __init__(self, session=None):
        self._session = session or db.session

    def commit(self, session_id: int) -> dict:
        """Execute governed commit for an approved session. Returns commit result."""
        intake_session = self._session.get(IntakeSession, session_id)
        if not intake_session:
            return {"success": False, "error": "Session not found"}
        if intake_session.status != IntakeSessionState.APPROVED:
            return {"success": False, "error": f"Session status is {intake_session.status}, must be approved"}

        candidates = (self._session.query(IntakeCandidate)
                      .filter(IntakeCandidate.session_id == session_id)
                      .all())

        results = []
        for candidate in candidates:
            result = self._commit_candidate(candidate, intake_session)
            results.append(result)

        intake_session.status = IntakeSessionState.IMPORTING
        self._session.commit()

        # Finalize
        errors = [r for r in results if r.get("error")]
        intake_session.status = IntakeSessionState.FAILED if errors else IntakeSessionState.COMPLETED
        self._session.commit()

        return {
            "success": len(errors) == 0,
            "total": len(results),
            "imported": sum(1 for r in results if r.get("imported")),
            "linked": sum(1 for r in results if r.get("linked")),
            "skipped": sum(1 for r in results if r.get("skipped")),
            "errors": len(errors),
            "results": results,
        }

    def _commit_candidate(self, candidate: IntakeCandidate,
                          intake_session: IntakeSession) -> dict:
        """Commit a single candidate based on its identity status."""
        fields = json.loads(candidate.normalized_data) if candidate.normalized_data else {}
        raw = json.loads(candidate.raw_data) if candidate.raw_data else {}

        # Only MATCHED and NO_MATCH can be auto-committed
        if candidate.import_status == "blocked":
            candidate.import_status = "skipped"
            self._session.commit()
            return {"row": candidate.row_index, "skipped": True, "reason": "Blocked by validation"}

        if candidate.identity_status == "MATCHED":
            # Link to existing Person
            candidate.matched_person_id = candidate.matched_person_id
            self._create_customer_profile(candidate, fields, intake_session)
            candidate.import_status = "imported"
            self._session.commit()
            return {"row": candidate.row_index, "linked": True, "person_id": candidate.matched_person_id,
                    "identity_status": "MATCHED"}

        if candidate.identity_status == "NO_MATCH":
            # Create new Person
            person = self._create_person(fields, intake_session)
            candidate.matched_person_id = person.id
            self._create_identities(person, fields)
            self._create_customer_profile(candidate, fields, intake_session)
            candidate.import_status = "imported"
            self._session.commit()
            return {"row": candidate.row_index, "imported": True, "new_person_id": person.id,
                    "identity_status": "NO_MATCH"}

        # AMBIGUOUS, CONFLICT, INSUFFICIENT_IDENTITY — blocked
        candidate.import_status = "skipped"
        self._session.commit()
        return {"row": candidate.row_index, "skipped": True,
                "reason": f"Cannot auto-commit {candidate.identity_status}"}

    def _create_person(self, fields: dict, intake_session: IntakeSession) -> Person:
        name = fields.get("name", "Imported Contact")
        p = Person(
            tenant_id=intake_session.tenant_id,
            canonical_name=name,
            preferred_name=name.split()[0] if name else name,
            status="active",
        )
        self._session.add(p)
        self._session.flush()
        return p

    def _create_identities(self, person: Person, fields: dict):
        if fields.get("email"):
            pi = PersonIdentity(person_id=person.id, identity_type="email",
                                identity_value=fields["email"],
                                normalized_value=normalize_email(fields["email"]),
                                verification_state="verified")
            self._session.add(pi)
        if fields.get("phone"):
            pi = PersonIdentity(person_id=person.id, identity_type="phone",
                                identity_value=fields["phone"],
                                normalized_value=normalize_phone(fields["phone"]),
                                verification_state="verified")
            self._session.add(pi)
        if fields.get("employee_ref"):
            pi = PersonIdentity(person_id=person.id, identity_type="employee_ref",
                                identity_value=fields["employee_ref"],
                                normalized_value=fields["employee_ref"],
                                verification_state="verified")
            self._session.add(pi)
        if fields.get("customer_ref"):
            pi = PersonIdentity(person_id=person.id, identity_type="customer_ref",
                                identity_value=fields["customer_ref"],
                                normalized_value=fields["customer_ref"],
                                verification_state="verified")
            self._session.add(pi)

    def _create_customer_profile(self, candidate: IntakeCandidate, fields: dict,
                                  intake_session: IntakeSession):
        if candidate.classification != "customer":
            return
        person_id = candidate.matched_person_id
        if not person_id:
            return
        existing = self._session.query(CustomerProfile).filter_by(person_id=person_id).first()
        if existing:
            return
        cp = CustomerProfile(
            person_id=person_id,
            tenant_id=intake_session.tenant_id,
        )
        self._session.add(cp)