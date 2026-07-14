"""
Governed commit — writes approved intake candidates to canonical tables.
Only APPROVED/explicitly committed proposals may write canonical data.
Supports safe-only approval, transaction safety, and partial completion.
"""
import json
from datetime import datetime
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

    def approve(self, session_id: int, approved_by: str = "",
                scope: str = IntakeSessionState.APPROVE_ALL) -> dict:
        """Approve a session for import. Records proposal version for audit."""
        intake_session = self._session.get(IntakeSession, session_id)
        if not intake_session:
            return {"success": False, "error": "Session not found"}
        if intake_session.status not in (IntakeSessionState.READY_FOR_REVIEW,
                                          IntakeSessionState.PARTIALLY_COMPLETED):
            return {"success": False, "error": f"Session status is {intake_session.status}, cannot approve"}

        intake_session.approved_by = approved_by
        intake_session.approved_at = datetime.utcnow()
        intake_session.approved_proposal_version = intake_session.proposal_version
        intake_session.status = IntakeSessionState.APPROVED
        self._session.commit()
        return {"success": True, "proposal_version": intake_session.proposal_version,
                "scope": scope}

    def commit(self, session_id: int) -> dict:
        """Execute governed commit for an approved session. Returns commit result."""
        intake_session = self._session.get(IntakeSession, session_id)
        if not intake_session:
            return {"success": False, "error": "Session not found"}
        if intake_session.status != IntakeSessionState.APPROVED:
            return {"success": False, "error": f"Session status is {intake_session.status}, must be approved"}

        # Verify proposal version hasn't changed since approval
        if intake_session.approved_proposal_version != intake_session.proposal_version:
            return {"success": False, "error": "Proposal version changed since approval. Re-approval required."}

        candidates = (self._session.query(IntakeCandidate)
                      .filter(IntakeCandidate.session_id == session_id)
                      .all())

        # Separate safe vs blocked candidates
        safe = [c for c in candidates if c.import_status == "pending"
                and c.identity_status in ("MATCHED", "NO_MATCH")]
        blocked = [c for c in candidates if c.import_status != "pending"
                   or c.identity_status not in ("MATCHED", "NO_MATCH")]

        return self._execute_commit(intake_session, safe, blocked)

    def _execute_commit(self, intake_session: IntakeSession,
                        safe: list[IntakeCandidate],
                        blocked: list[IntakeCandidate]) -> dict:
        """Execute the commit with transaction safety."""
        intake_session.status = IntakeSessionState.IMPORTING
        self._session.flush()

        results = []
        imported_count = 0
        linked_count = 0
        skipped_count = 0
        errors = []

        try:
            for candidate in safe:
                result = self._commit_candidate(candidate, intake_session)
                results.append(result)
                if result.get("imported"):
                    imported_count += 1
                elif result.get("linked"):
                    linked_count += 1
                elif result.get("skipped"):
                    skipped_count += 1
                if result.get("error"):
                    errors.append(result)

            # If any errors, rollback ALL canonical writes
            if errors:
                self._session.rollback()
                intake_session.status = IntakeSessionState.FAILED
                self._session.commit()
                return {
                    "success": False,
                    "total": len(safe),
                    "imported": 0,
                    "linked": 0,
                    "skipped": 0,
                    "errors": len(errors),
                    "results": results,
                    "rolled_back": True,
                }

            self._session.commit()

            # Determine completion state
            has_unresolved = len(blocked) > 0
            intake_session.status = (IntakeSessionState.PARTIALLY_COMPLETED
                                      if has_unresolved else IntakeSessionState.COMPLETED)
            self._session.commit()

            return {
                "success": True,
                "total": len(safe),
                "imported": imported_count,
                "linked": linked_count,
                "skipped": skipped_count,
                "errors": 0,
                "unresolved_remaining": len(blocked),
                "session_status": intake_session.status,
                "results": results,
            }

        except Exception as e:
            self._session.rollback()
            intake_session.status = IntakeSessionState.FAILED
            self._session.commit()
            return {
                "success": False,
                "total": len(safe),
                "imported": 0,
                "linked": 0,
                "skipped": 0,
                "errors": 1,
                "error": str(e),
                "rolled_back": True,
            }

    def _commit_candidate(self, candidate: IntakeCandidate,
                          intake_session: IntakeSession) -> dict:
        """Commit a single candidate based on its identity status."""
        fields = json.loads(candidate.normalized_data) if candidate.normalized_data else {}

        if candidate.identity_status == "MATCHED":
            self._create_customer_profile(candidate, fields, intake_session)
            candidate.import_status = "imported"
            return {"row": candidate.row_index, "linked": True,
                    "person_id": candidate.matched_person_id,
                    "identity_status": "MATCHED"}

        if candidate.identity_status == "NO_MATCH":
            person = self._create_person(fields, intake_session)
            candidate.matched_person_id = person.id
            self._create_identities(person, fields)
            self._create_customer_profile(candidate, fields, intake_session)
            candidate.import_status = "imported"
            return {"row": candidate.row_index, "imported": True,
                    "new_person_id": person.id, "identity_status": "NO_MATCH"}

        candidate.import_status = "skipped"
        return {"row": candidate.row_index, "skipped": True,
                "reason": f"Cannot auto-commit {candidate.identity_status}"}

    def _create_person(self, fields: dict, intake_session: IntakeSession) -> Person:
        name = fields.get("name", "Imported Contact")
        p = Person(tenant_id=intake_session.tenant_id,
                   canonical_name=name,
                   preferred_name=name.split()[0] if name else name,
                   status="active")
        self._session.add(p)
        self._session.flush()
        return p

    def _create_identities(self, person: Person, fields: dict):
        for id_type, value_key in [("email", "email"), ("phone", "phone"),
                                    ("employee_ref", "employee_ref"),
                                    ("customer_ref", "customer_ref")]:
            val = fields.get(value_key)
            if not val:
                continue
            normalized = normalize_email(val) if id_type == "email" else (
                normalize_phone(val) if id_type == "phone" else val)
            pi = PersonIdentity(person_id=person.id, identity_type=id_type,
                                identity_value=val, normalized_value=normalized,
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
        cp = CustomerProfile(person_id=person_id, tenant_id=intake_session.tenant_id)
        self._session.add(cp)