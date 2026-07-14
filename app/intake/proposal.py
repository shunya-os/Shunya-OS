"""
ImportProposal — reviewable summary of an intake session before governed commit.
"""
import json
from collections import Counter
from typing import Optional
from app import db
from app.models import IntakeSession, IntakeCandidate


class ImportProposalBuilder:
    """Builds a reviewable ImportProposal from intake session candidates."""

    @staticmethod
    def build(session: IntakeSession, candidates: list[IntakeCandidate]) -> dict:
        """Build a summary proposal from candidate records."""
        total = len(candidates)
        identity_statuses = Counter(c.identity_status for c in candidates)
        validation_statuses = Counter(c.validation_status for c in candidates)
        duplicate_types = Counter(c.duplicate_type for c in candidates if c.duplicate_type)
        classifications = Counter(c.classification for c in candidates)
        import_statuses = Counter(c.import_status for c in candidates)

        blocked = [c for c in candidates if c.import_status == "blocked"]
        ambiguous = [c for c in candidates if c.identity_status == "AMBIGUOUS"]
        insufficient = [c for c in candidates if c.identity_status == "INSUFFICIENT_IDENTITY"]
        matched = [c for c in candidates if c.identity_status == "MATCHED"]
        no_match = [c for c in candidates if c.identity_status == "NO_MATCH"]
        conflicts = [c for c in candidates if c.identity_status == "CONFLICT"]

        proposal = {
            "session_id": session.id,
            "session_status": session.status,
            "total_rows": total,
            "summary": {
                "valid": import_statuses.get("pending", 0),
                "warning": validation_statuses.get("warning", 0),
                "blocked": len(blocked),
                "matched": len(matched),
                "new_person_candidates": len(no_match),
                "ambiguous": len(ambiguous),
                "insufficient_identity": len(insufficient),
                "conflicts": len(conflicts),
                "duplicates": sum(duplicate_types.values()),
            },
            "identity_breakdown": dict(identity_statuses),
            "validation_breakdown": dict(validation_statuses),
            "duplicate_breakdown": dict(duplicate_types),
            "classification_breakdown": dict(classifications),
            "can_import": len(blocked) == 0 and len(ambiguous) == 0
                          and len(insufficient) == 0 and len(conflicts) == 0,
        }

        # Store proposal in session
        session.summary = json.dumps(proposal)
        db.session.commit()

        return proposal

    @staticmethod
    def get_proposal(session_id: int) -> Optional[dict]:
        session = db.session.get(IntakeSession, session_id)
        if not session or not session.summary:
            return None
        return json.loads(session.summary)