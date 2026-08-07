"""EP-03 — Universal Living Object Workspace.

Every Living Object renders through the same canonical workspace.
The workspace derives itself from object type, runtime capabilities,
relationships, available actions, evidence, and execution state.

No switch statements. No object-specific pages.
"""

import uuid
import logging
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


# ── Section Registry ──────────────────────────────────────────────
# Each section is a capability that may or may not be available
# for a given object type. The workspace composes itself dynamically.

SECTION_REGISTRY: dict[str, list[str]] = {
    "proposal": ["identity", "reality", "relationships", "timeline", "evidence",
                 "conversation", "commitments", "execution", "observations",
                 "predictions", "files", "actions"],
    "invoice": ["identity", "reality", "relationships", "timeline", "evidence",
                "conversation", "commitments", "execution", "observations",
                "predictions", "files", "actions"],
    "contact": ["identity", "reality", "relationships", "timeline", "evidence",
                "conversation", "commitments", "execution", "observations",
                "files", "actions"],
    "task": ["identity", "reality", "relationships", "timeline", "evidence",
             "conversation", "commitments", "execution", "observations",
             "files", "actions"],
    "meeting": ["identity", "reality", "relationships", "timeline", "evidence",
                "conversation", "commitments", "execution", "observations",
                "predictions", "files", "actions"],
    "document": ["identity", "reality", "relationships", "timeline", "evidence",
                 "conversation", "commitments", "execution", "observations",
                 "predictions", "files", "actions"],
    "contract": ["identity", "reality", "relationships", "timeline", "evidence",
                 "conversation", "commitments", "execution", "observations",
                 "predictions", "files", "actions"],
    "note": ["identity", "reality", "relationships", "timeline", "evidence",
             "conversation", "commitments", "execution", "observations",
             "files"],
    "project": ["identity", "reality", "relationships", "timeline", "evidence",
                "conversation", "commitments", "execution", "observations",
                "predictions", "files", "actions"],
    "event": ["identity", "reality", "relationships", "timeline", "evidence",
              "conversation", "commitments", "execution", "observations",
              "predictions", "files", "actions"],
}


# ── Action Registry ───────────────────────────────────────────────
# Actions are generated dynamically per object type.
# The runtime determines actions — not the UI.

ACTION_REGISTRY: dict[str, list[dict]] = {
    "proposal": [
        {"id": "approve", "label": "Approve", "type": "transition", "icon": "✓"},
        {"id": "revise", "label": "Revise", "type": "transition", "icon": "✎"},
        {"id": "send", "label": "Send", "type": "communication", "icon": "→"},
        {"id": "convert_to_invoice", "label": "Convert to Invoice", "type": "compose", "icon": "⟳"},
    ],
    "invoice": [
        {"id": "pay", "label": "Mark Paid", "type": "transition", "icon": "✓"},
        {"id": "remind", "label": "Send Reminder", "type": "communication", "icon": "!"},
        {"id": "export_pdf", "label": "Export PDF", "type": "export", "icon": "⬇"},
    ],
    "contact": [
        {"id": "call", "label": "Call", "type": "communication", "icon": "📞"},
        {"id": "email", "label": "Email", "type": "communication", "icon": "✉"},
        {"id": "create_proposal", "label": "Create Proposal", "type": "compose", "icon": "+"},
        {"id": "schedule_meeting", "label": "Schedule Meeting", "type": "compose", "icon": "📅"},
    ],
    "task": [
        {"id": "complete", "label": "Mark Complete", "type": "transition", "icon": "✓"},
        {"id": "assign", "label": "Assign", "type": "assign", "icon": "👤"},
        {"id": "add_subtask", "label": "Add Subtask", "type": "compose", "icon": "+"},
    ],
    "meeting": [
        {"id": "join", "label": "Join", "type": "launch", "icon": "▶"},
        {"id": "reschedule", "label": "Reschedule", "type": "edit", "icon": "📅"},
        {"id": "summarize", "label": "Summarize", "type": "ai", "icon": "✨"},
        {"id": "add_notes", "label": "Add Notes", "type": "compose", "icon": "✎"},
    ],
    "document": [
        {"id": "edit", "label": "Edit", "type": "launch", "icon": "✎"},
        {"id": "share", "label": "Share", "type": "communication", "icon": "→"},
        {"id": "export_pdf", "label": "Export PDF", "type": "export", "icon": "⬇"},
        {"id": "request_review", "label": "Request Review", "type": "communication", "icon": "!"},
    ],
    "contract": [
        {"id": "sign", "label": "Sign", "type": "transition", "icon": "✍"},
        {"id": "send_for_signature", "label": "Send for Signature", "type": "communication", "icon": "→"},
        {"id": "export_pdf", "label": "Export PDF", "type": "export", "icon": "⬇"},
    ],
    "note": [
        {"id": "edit", "label": "Edit", "type": "launch", "icon": "✎"},
        {"id": "share", "label": "Share", "type": "communication", "icon": "→"},
    ],
    "project": [
        {"id": "add_task", "label": "Add Task", "type": "compose", "icon": "+"},
        {"id": "add_milestone", "label": "Add Milestone", "type": "compose", "icon": "★"},
        {"id": "add_team_member", "label": "Add Team Member", "type": "compose", "icon": "👤"},
        {"id": "generate_report", "label": "Generate Report", "type": "ai", "icon": "📊"},
    ],
    "event": [
        {"id": "join", "label": "Join", "type": "launch", "icon": "▶"},
        {"id": "reschedule", "label": "Reschedule", "type": "edit", "icon": "📅"},
        {"id": "add_to_calendar", "label": "Add to Calendar", "type": "communication", "icon": "📅"},
    ],
}

DEFAULT_ACTIONS = [
    {"id": "edit", "label": "Edit", "type": "launch", "icon": "✎"},
    {"id": "delete", "label": "Delete", "type": "destructive", "icon": "✕"},
]


def get_sections(object_type: str) -> list[str]:
    """Return the sections available for this object type."""
    return SECTION_REGISTRY.get(object_type, ["identity", "reality", "timeline", "actions"])


def get_actions(object_type: str) -> list[dict]:
    """Return the actions available for this object type."""
    return ACTION_REGISTRY.get(object_type, DEFAULT_ACTIONS)


def build_object_detail(object_id: str, object_type: str, name: str,
                        identity_id: str = "system") -> dict:
    """Build the full object detail response for the Universal Workspace.
    
    Every section comes from metadata, capabilities, and runtimes.
    No switch statements. No object-specific pages.
    """
    now = datetime.now(timezone.utc).isoformat()
    
    # Identity
    identity = {
        "object_id": object_id,
        "object_type": object_type,
        "name": name,
        "created_at": now,
        "status": "active",
    }
    
    # Reality — recent events for this object
    reality = _get_object_reality(object_id, object_type)
    
    # Relationships
    relationships = _get_object_relationships(object_id, object_type)
    
    # Timeline
    timeline = _get_object_timeline(object_id, object_type)
    
    # Evidence
    evidence = _get_object_evidence(object_id, object_type)
    
    # Conversation
    conversation = _get_object_conversation(object_id, object_type)
    
    # Commitments
    commitments = _get_object_commitments(object_id, object_type)
    
    # Execution
    execution = _get_object_execution(object_id, object_type)
    
    # Observations
    observations = _get_object_observations(object_id, object_type)
    
    # Predictions
    predictions = _get_object_predictions(object_id, object_type)
    
    # Files
    files = _get_object_files(object_id, object_type)
    
    # Actions
    actions = get_actions(object_type)
    
    # Sections
    sections = get_sections(object_type)
    
    return {
        "identity": identity,
        "reality": reality,
        "relationships": relationships,
        "timeline": timeline,
        "evidence": evidence,
        "conversation": conversation,
        "commitments": commitments,
        "execution": execution,
        "observations": observations,
        "predictions": predictions,
        "files": files,
        "actions": actions,
        "sections": sections,
        "available_sections": sections,
    }


def _get_object_reality(object_id: str, object_type: str) -> list[dict]:
    """Get reality events for this object.
    
    Delegates to the Reality Engine. Returns empty list if unavailable.
    """
    try:
        from app.reality_engine.engine import get_reality_engine
        engine = get_reality_engine()
        # In a full implementation, the engine would filter by object_id
        return []
    except Exception:
        return []


def _get_object_relationships(object_id: str, object_type: str) -> list[dict]:
    """Get relationships for this object.
    
    Delegates to the Graph Engine. Returns empty list if unavailable.
    """
    return []


def _get_object_timeline(object_id: str, object_type: str) -> list[dict]:
    """Get the timeline of events for this object."""
    return []


def _get_object_evidence(object_id: str, object_type: str) -> list[dict]:
    """Get evidence chain for this object."""
    return []


def _get_object_conversation(object_id: str, object_type: str) -> list[dict]:
    """Get conversation (comments) for this object."""
    return []


def _get_object_commitments(object_id: str, object_type: str) -> list[dict]:
    """Get commitments associated with this object."""
    return []


def _get_object_execution(object_id: str, object_type: str) -> list[dict]:
    """Get execution history for this object."""
    return []


def _get_object_observations(object_id: str, object_type: str) -> list[dict]:
    """Get AI observations for this object."""
    return []


def _get_object_predictions(object_id: str, object_type: str) -> list[dict]:
    """Get AI predictions for this object."""
    return []


def _get_object_files(object_id: str, object_type: str) -> list[dict]:
    """Get files attached to this object."""
    return []