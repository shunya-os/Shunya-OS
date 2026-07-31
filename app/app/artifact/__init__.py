"""
SHUNYA — Artifact & Document Generation (Phase 14B, computation-only)
"""
import hashlib, json
from datetime import datetime
from typing import Optional

# Artifact lifecycle states
class ArtifactState:
    DRAFT = "draft"
    VALIDATED = "validated"
    READY_FOR_REVIEW = "ready_for_review"
    APPROVED = "approved"
    HANDED_TO_ACTION = "handed_to_action"
    SUPERSEDED = "superseded"

# Artifact types
class ArtifactType:
    PROPOSAL = "proposal"
    QUOTATION = "quotation"
    REPORT = "report"
    ITINERARY = "itinerary"
    INVOICE = "invoice"
    LETTER = "letter"
    GENERIC = "generic"


class ArtifactService:
    """Artifact & Document Generation.

    Phase 14B. Deterministic generation from source context.
    No paid-model calls. No Phase 14C/17 spillover.
    Handles to Phase 14 governed action.
    """

    def __init__(self, phase4_service=None, template_service=None):
        self._p4 = phase4_service
        self._templates = template_service or {}
        self._version = "14b.1"
        self._generated_ids = set()  # Idempotency tracking

    # ------------------------------------------------------------------
    # Artifact generation
    # ------------------------------------------------------------------
    def generate(self, artifact_type: str, source_context: dict,
                 template_id: Optional[str] = None,
                 tenant_id: int = 1, principal_id: Optional[str] = None,
                 request_id: Optional[str] = None) -> dict:
        """Generate an artifact from source context."""
        # Phase 4 current-use
        if self._p4:
            p4 = self._p4.check_eligibility(source_context.get("purpose_code", "artifact"))
            if not p4.get("eligible", True):
                return self._error("blocked_by_current_use", tenant_id, principal_id)

        # Validate artifact type
        valid_types = [v for v in dir(ArtifactType) if not v.startswith("_")]
        if artifact_type not in valid_types:
            return self._error("invalid_artifact_type", tenant_id, principal_id)

        # Idempotency
        idem_key = request_id or hashlib.sha256(
            f"{tenant_id}:{artifact_type}:{json.dumps(source_context, sort_keys=True)}".encode()
        ).hexdigest()
        if idem_key in self._generated_ids:
            return self._error("duplicate_request", tenant_id, principal_id)

        # Resolve template
        template_content = None
        if template_id and template_id in self._templates:
            template_content = self._templates[template_id]
        elif template_id:
            return self._error("template_not_found", tenant_id, principal_id)

        self._generated_ids.add(idem_key)

        # Build artifact content (deterministic)
        content = self._build_content(artifact_type, source_context, template_content)

        # Generate artifact identity
        artifact_id = hashlib.sha256(
            f"{tenant_id}:{artifact_type}:{idem_key}:{datetime.utcnow().isoformat()}".encode()
        ).hexdigest()[:16]

        # Source snapshot
        source_snapshot = {
            "source_hash": hashlib.sha256(json.dumps(source_context, sort_keys=True).encode()).hexdigest()[:16],
            "source_timestamp": datetime.utcnow().isoformat(),
            "source_tenant": tenant_id,
        }

        return {
            "artifact_id": artifact_id,
            "artifact_type": artifact_type,
            "state": ArtifactState.DRAFT,
            "content": content,
            "template_id": template_id,
            "source_snapshot": source_snapshot,
            "request_id": idem_key,
            "tenant_id": tenant_id,
            "created_by": principal_id,
            "created_at": datetime.utcnow().isoformat(),
            "version": self._version,
        }

    def _build_content(self, artifact_type: str, source_context: dict,
                       template_content: Optional[dict] = None) -> dict:
        """Build deterministic artifact content from source context."""
        if template_content:
            # Template-based: fill template fields from source
            result = {}
            for field, default in template_content.items():
                result[field] = source_context.get(field, default)
            return result

        # Default deterministic content based on type
        if artifact_type == ArtifactType.PROPOSAL:
            return {
                "title": source_context.get("title", "Proposal"),
                "client": source_context.get("client_name", ""),
                "items": source_context.get("items", []),
                "total": source_context.get("total", 0),
            }
        elif artifact_type == ArtifactType.QUOTATION:
            return {
                "title": source_context.get("title", "Quotation"),
                "client": source_context.get("client_name", ""),
                "line_items": source_context.get("line_items", []),
                "subtotal": source_context.get("subtotal", 0),
                "tax": source_context.get("tax", 0),
                "total": source_context.get("total", 0),
            }
        elif artifact_type == ArtifactType.REPORT:
            return {
                "title": source_context.get("title", "Report"),
                "sections": source_context.get("sections", []),
                "summary": source_context.get("summary", ""),
            }
        elif artifact_type == ArtifactType.ITINERARY:
            return {
                "title": source_context.get("title", "Itinerary"),
                "destination": source_context.get("destination", ""),
                "dates": source_context.get("dates", {}),
                "activities": source_context.get("activities", []),
                "accommodations": source_context.get("accommodations", []),
                "notes": source_context.get("notes", ""),
            }
        elif artifact_type == ArtifactType.INVOICE:
            return {
                "invoice_number": source_context.get("invoice_number", ""),
                "client": source_context.get("client_name", ""),
                "line_items": source_context.get("line_items", []),
                "subtotal": source_context.get("subtotal", 0),
                "tax": source_context.get("tax", 0),
                "total": source_context.get("total", 0),
                "due_date": source_context.get("due_date", ""),
            }
        elif artifact_type == ArtifactType.LETTER:
            return {
                "recipient": source_context.get("recipient", ""),
                "subject": source_context.get("subject", ""),
                "body": source_context.get("body", ""),
                "sender": source_context.get("sender", ""),
            }
        else:
            return dict(source_context)  # Generic passthrough

    # ------------------------------------------------------------------
    # Artifact lifecycle
    # ------------------------------------------------------------------
    def validate(self, artifact: dict, principal_id: Optional[str] = None) -> dict:
        if artifact["state"] != ArtifactState.DRAFT:
            return self._error("cannot_validate_non_draft", artifact.get("tenant_id"), principal_id)
        artifact["state"] = ArtifactState.VALIDATED
        return artifact

    def mark_ready_for_review(self, artifact: dict, principal_id: Optional[str] = None) -> dict:
        if artifact["state"] != ArtifactState.VALIDATED:
            return self._error("cannot_review_non_validated", artifact.get("tenant_id"), principal_id)
        artifact["state"] = ArtifactState.READY_FOR_REVIEW
        return artifact

    def approve(self, artifact: dict, principal_id: Optional[str] = None) -> dict:
        if artifact["state"] != ArtifactState.READY_FOR_REVIEW:
            return self._error("cannot_approve_non_reviewable", artifact.get("tenant_id"), principal_id)
        artifact["state"] = ArtifactState.APPROVED
        artifact["approved_at"] = datetime.utcnow().isoformat()
        return artifact

    def handoff_to_action(self, artifact: dict, principal_id: Optional[str] = None) -> dict:
        if artifact["state"] != ArtifactState.APPROVED:
            return self._error("cannot_handoff_non_approved", artifact.get("tenant_id"), principal_id)
        artifact["state"] = ArtifactState.HANDED_TO_ACTION
        artifact["handed_off_at"] = datetime.utcnow().isoformat()
        return artifact

    def supersede(self, artifact: dict, new_artifact_id: str, principal_id: Optional[str] = None) -> dict:
        if artifact["state"] in (ArtifactState.HANDED_TO_ACTION,):
            return self._error("cannot_supersede_handed_off", artifact.get("tenant_id"), principal_id)
        artifact["state"] = ArtifactState.SUPERSEDED
        artifact["superseded_by"] = new_artifact_id
        return artifact

    # ------------------------------------------------------------------
    # Template management
    # ------------------------------------------------------------------
    def register_template(self, template_id: str, content: dict, tenant_id: int = 1) -> dict:
        if not isinstance(content, dict):
            return self._error("invalid_template_content", tenant_id)
        self._templates[template_id] = content
        return {"template_id": template_id, "tenant_id": tenant_id, "registered": True}

    def get_template(self, template_id: str) -> Optional[dict]:
        return self._templates.get(template_id)

    # ------------------------------------------------------------------
    # Inspection
    # ------------------------------------------------------------------
    def inspect(self, artifact: dict) -> dict:
        return {
            "artifact_id": artifact.get("artifact_id"),
            "artifact_type": artifact.get("artifact_type"),
            "state": artifact.get("state"),
            "tenant_id": artifact.get("tenant_id"),
            "created_at": artifact.get("created_at"),
        }

    def explain(self, artifact: dict) -> dict:
        return {
            "artifact_id": artifact.get("artifact_id"),
            "state": artifact.get("state"),
            "source_snapshot": artifact.get("source_snapshot"),
            "template_id": artifact.get("template_id"),
        }

    def _error(self, reason: str, tenant_id: int = 1, principal_id: Optional[str] = None) -> dict:
        return {"error": reason, "tenant_id": tenant_id, "principal_id": principal_id,
                "timestamp": datetime.utcnow().isoformat()}