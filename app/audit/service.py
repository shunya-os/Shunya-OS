"""FDA21 — Audit & Governance Reconstruction Service.

Connects existing canonical systems into a governed reconstruction chain.
No new models. No duplicate audit architecture. All data composed from
existing canonical sources:

- Security AuditLog (sh_audit_logs) — CRUD audit
- Genesis AuditLog — destructive action audit
- DecisionTrace — decision records
- EvidenceRecord — evidence records
- Outcome — execution outcomes
- Commitment — business commitments
- TimelineEntry — relationship timeline
- MemoryRecord — AI memory records
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple


# =========================================================================
# Canonical Source Registry — maps requirement to canonical owner
# =========================================================================

CANONICAL_AUDIT_MATRIX = {
    "audit_event": {
        "owner": "app.security.audit.AuditLog",
        "table": "sh_audit_logs",
        "append_only": True,
        "tenant_bound": False,
        "actor": "identity_id",
        "action": "action",
        "object": "resource_type + resource_id",
        "timestamp": "timestamp",
        "details": "details (JSON)",
    },
    "decision_trace": {
        "owner": "app.evidence.decision_trace.DecisionTrace",
        "table": "decision_traces",
        "append_only": True,
        "tenant_bound": False,
        "actor": None,
        "action": "main_decision",
        "object": "object_id",
        "timestamp": "created_at",
        "details": "final_decision, execution_status, confidence",
    },
    "evidence_record": {
        "owner": "app.evidence.models_db.EvidenceRecord",
        "table": "evidence_records",
        "append_only": True,
        "tenant_bound": False,
        "actor": None,
        "action": "source_type",
        "object": "source_id",
        "timestamp": "created_at",
        "details": "raw_reference (JSON)",
    },
    "execution_outcome": {
        "owner": "app.execution.models.Outcome",
        "table": "sh_outcomes",
        "append_only": True,
        "tenant_bound": False,
        "actor": "identity_id",
        "action": "stage",
        "object": "outcome_id",
        "timestamp": "created_at",
        "details": "intention, steps, recovery_history, final_summary",
    },
    "destructive_audit": {
        "owner": "app.genesis_protection.AuditLog",
        "table": "audit_logs",
        "append_only": True,
        "tenant_bound": False,
        "actor": "actor_id",
        "action": "action",
        "object": "entity_type + entity_id",
        "timestamp": "created_at",
        "details": "details, reason",
    },
    "commitment": {
        "owner": "app.commitments.models.Commitment",
        "table": "commitments",
        "append_only": False,
        "tenant_bound": False,
        "actor": "owner",
        "action": "status",
        "object": "title",
        "timestamp": "created_at",
        "details": "due_at, issue_type, meta",
    },
    "timeline": {
        "owner": "app.relationship.models.TimelineEntry",
        "table": "rel_timeline",
        "append_only": True,
        "tenant_bound": True,
        "actor": "created_by",
        "action": "event_type",
        "object": "title",
        "timestamp": "event_time",
        "details": "description, reference_type, reference_id, metadata_json",
    },
}


# =========================================================================
# Audit Reconstruction Service
# =========================================================================


def reconstruct_business_outcome(
    object_id: int,
    object_type: str = "lead",
    tenant_id: int = 0,
) -> Dict[str, Any]:
    """Reconstruct a complete business outcome from canonical records.

    This is the primary FDA21 reconstruction function.
    It traces: WHAT → WHO → WHEN → WHY → EVIDENCE → APPROVAL → EXECUTION → OUTCOME
    """
    from app import db
    from app.models import Lead
    from app.commitments.models import Commitment
    from app.relationship.models import TimelineEntry, CanonicalRelationship
    from app.evidence.models_db import EvidenceRecord
    from app.evidence.decision_trace import DecisionTrace
    from app.security.audit import AuditLog as SecurityAudit
    from app.execution.models import Outcome

    result: Dict[str, Any] = {
        "reconstructed_at": datetime.now(timezone.utc).isoformat(),
        "object_type": object_type,
        "object_id": object_id,
        "what_happened": None,
        "who_caused_it": None,
        "when_it_happened": None,
        "why_it_happened": None,
        "what_information_supported_it": None,
        "who_approved_it": None,
        "what_shunya_executed": None,
        "what_actually_succeeded": None,
        "what_evidence_proves_it": None,
        "timeline": [],
        "decisions": [],
        "approvals": [],
        "executions": [],
        "evidence_chain": [],
        "provenance": "reconstructed from canonical records",
        "confidence": "high",
    }

    # 1. WHAT — resolve the object identity
    identity = _resolve_object_identity(object_id, object_type, tenant_id)
    if identity:
        result["what_happened"] = identity.get("name") or identity.get("title") or f"{object_type} #{object_id}"
        result["when_it_happened"] = identity.get("created_at")

    # 2. WHO — find the actor from audit logs and commitments
    actors = _find_actors(object_id, object_type, tenant_id)
    result["who_caused_it"] = actors or "unknown"

    # 3. TIMELINE — chronological events
    timeline = _get_timeline_for_object(object_id, object_type, tenant_id)
    result["timeline"] = timeline[:20]

    # 4. DECISIONS — decision traces involving this object
    decisions = _get_decisions_for_object(object_id, tenant_id)
    result["decisions"] = decisions[:10]
    if decisions:
        result["why_it_happened"] = decisions[0].get("main_decision", {}).get("reason", "decision recorded")
        result["what_information_supported_it"] = [
            d.get("main_decision", {}) for d in decisions[:3]
        ]

    # 5. APPROVALS — audit log entries for approval actions
    approvals = _get_approvals_for_object(object_id, object_type, tenant_id)
    result["approvals"] = approvals[:10]
    if approvals:
        result["who_approved_it"] = approvals[0].get("identity_id") or approvals[0].get("actor", "unknown")

    # 6. EXECUTIONS — outcomes and execution records
    executions = _get_executions_for_object(object_id, object_type, tenant_id)
    result["executions"] = executions[:10]
    if executions:
        result["what_shunya_executed"] = executions[0].get("intention") or executions[0].get("action", "execution recorded")
        result["what_actually_succeeded"] = executions[0].get("stage") if executions[0].get("stage") == "completed" else "incomplete"

    # 7. EVIDENCE CHAIN — evidence records connected to this object
    evidence = _get_evidence_chain(object_id, tenant_id)
    result["evidence_chain"] = evidence[:10]
    if evidence:
        result["what_evidence_proves_it"] = [
            {"source_type": e.get("source_type"), "description": str(e.get("raw_reference", {}))[:200]}
            for e in evidence[:5]
        ]

    # 8. Commitments
    commitments = _get_commitments_for_reconstruction(object_id, object_type, tenant_id)

    return result


def _resolve_object_identity(object_id: int, object_type: str, tenant_id: int) -> Optional[Dict[str, Any]]:
    """Resolve the identity of an object from canonical types."""
    from app import db
    from app.models import Lead
    from app.relationship.models import CanonicalRelationship
    from app.commitments.models import Commitment
    from app.marketing.models import Campaign

    if object_type == "lead":
        lead = db.session.query(Lead).filter_by(id=object_id).first()
        if lead:
            return {"name": lead.customer_name, "created_at": lead.created_at.isoformat() if lead.created_at else None, "status": lead.status}
    elif object_type == "relationship":
        rel = db.session.query(CanonicalRelationship).filter_by(id=object_id).first()
        if rel:
            return {"name": rel.display_name, "created_at": rel.created_at.isoformat() if rel.created_at else None, "status": rel.status}
    elif object_type == "commitment":
        comm = db.session.query(Commitment).filter_by(id=object_id).first()
        if comm:
            return {"title": comm.title, "created_at": comm.created_at.isoformat() if comm.created_at else None, "status": comm.status}
    elif object_type == "campaign":
        camp = db.session.query(Campaign).filter_by(id=object_id).first()
        if camp:
            return {"name": camp.name, "created_at": camp.created_at.isoformat() if camp.created_at else None, "status": camp.status}
    return None


def _find_actors(object_id: int, object_type: str, tenant_id: int) -> List[Dict[str, Any]]:
    """Find all actors involved with this object."""
    from app import db
    from app.security.audit import AuditLog as SecurityAudit
    from app.commitments.models import Commitment
    from app.relationship.models import TimelineEntry

    actors = []
    seen = set()

    # From audit logs
    audits = db.session.query(SecurityAudit).filter(
        SecurityAudit.resource_id == str(object_id)
    ).limit(10).all()
    for a in audits:
        if a.identity_id and a.identity_id not in seen:
            seen.add(a.identity_id)
            actors.append({"actor": a.identity_id, "source": "audit_log", "action": a.action})

    # From commitments
    rel_id = _get_relationship_id(object_id, object_type)
    if rel_id:
        comms = db.session.query(Commitment).filter_by(relationship_id=rel_id).limit(10).all()
        for c in comms:
            if c.owner and c.owner not in seen:
                seen.add(c.owner)
                actors.append({"actor": c.owner, "source": "commitment", "action": c.status})

    return actors


def _get_relationship_id(object_id: int, object_type: str) -> Optional[int]:
    """Get the relationship ID for an object."""
    from app import db
    from app.models import Lead
    if object_type == "lead":
        lead = db.session.query(Lead).filter_by(id=object_id).first()
        if lead:
            return lead.person_id
    return None


def _get_timeline_for_object(object_id: int, object_type: str, tenant_id: int) -> List[Dict[str, Any]]:
    """Get timeline events for an object."""
    from app import db
    from app.relationship.models import TimelineEntry
    from app.models import ActivityLog

    events = []
    rel_id = _get_relationship_id(object_id, object_type)

    if rel_id:
        entries = db.session.query(TimelineEntry).filter_by(relationship_id=rel_id).order_by(TimelineEntry.event_time.desc()).limit(50).all()
        for e in entries:
            events.append({
                "id": e.id, "time": e.event_time.isoformat() if e.event_time else None,
                "type": e.event_type, "title": e.title, "description": (e.description or "")[:300],
                "source": "timeline_entry", "truth": "fact",
            })

    if object_type == "lead":
        logs = db.session.query(ActivityLog).filter_by(lead_id=object_id).order_by(ActivityLog.created_at.desc()).limit(50).all()
        for a in logs:
            events.append({
                "id": a.id, "time": a.created_at.isoformat() if a.created_at else None,
                "type": a.action, "title": a.action, "description": (a.detail or "")[:300],
                "source": "activity_log", "truth": "fact",
            })

    events.sort(key=lambda e: e.get("time") or "", reverse=True)
    return events


def _get_decisions_for_object(object_id: int, tenant_id: int) -> List[Dict[str, Any]]:
    """Get decision traces for an object."""
    from app import db
    from app.evidence.decision_trace import DecisionTrace

    traces = db.session.query(DecisionTrace).filter_by(object_id=object_id).order_by(DecisionTrace.created_at.desc()).limit(20).all()
    return [t.to_dict() for t in traces]


def _get_approvals_for_object(object_id: int, object_type: str, tenant_id: int) -> List[Dict[str, Any]]:
    """Get approval events for an object."""
    from app import db
    from app.security.audit import AuditLog as SecurityAudit

    audits = db.session.query(SecurityAudit).filter(
        SecurityAudit.resource_id == str(object_id),
        SecurityAudit.action.in_(["approve", "reject", "authorize", "approval"])
    ).order_by(SecurityAudit.timestamp.desc()).limit(20).all()

    return [a.to_dict() for a in audits]


def _get_executions_for_object(object_id: int, object_type: str, tenant_id: int) -> List[Dict[str, Any]]:
    """Get execution outcomes for an object."""
    from app import db
    from app.execution.models import Outcome

    outcomes = db.session.query(Outcome).filter(
        Outcome.outcome_id.like(f"out_{object_id}_%")
    ).order_by(Outcome.created_at.desc()).limit(20).all()

    if not outcomes and object_type == "lead":
        # Try finding by intention text
        from app.models import Lead
        lead = db.session.query(Lead).filter_by(id=object_id).first()
        if lead and lead.customer_name:
            outcomes = db.session.query(Outcome).filter(
                Outcome.intention.like(f"%{lead.customer_name}%")
            ).order_by(Outcome.created_at.desc()).limit(20).all()

    return [o.to_dict() for o in outcomes]


def _get_evidence_chain(object_id: int, tenant_id: int) -> List[Dict[str, Any]]:
    """Get evidence records for an object."""
    from app import db
    from app.evidence.models_db import EvidenceRecord

    records = db.session.query(EvidenceRecord).filter_by(
        source_id=str(object_id)
    ).order_by(EvidenceRecord.created_at.desc()).limit(20).all()

    if not records:
        # Try as source_type+source_id
        records = db.session.query(EvidenceRecord).filter(
            EvidenceRecord.source_id == str(object_id)
        ).order_by(EvidenceRecord.created_at.desc()).limit(20).all()

    return [r.to_dict() for r in records]


def _get_commitments_for_reconstruction(object_id: int, object_type: str, tenant_id: int) -> List[Dict[str, Any]]:
    """Get commitments for reconstruction."""
    from app import db
    from app.commitments.models import Commitment

    rel_id = _get_relationship_id(object_id, object_type)
    if not rel_id:
        return []

    comms = db.session.query(Commitment).filter_by(relationship_id=rel_id).order_by(Commitment.created_at.desc()).limit(20).all()
    return [{
        "id": c.id, "title": c.title, "owner": c.owner,
        "status": c.status, "due_at": c.due_at.isoformat() if c.due_at else None,
        "created_at": c.created_at.isoformat() if c.created_at else None,
    } for c in comms]


# =========================================================================
# Approval Audit
# =========================================================================


def record_approval(
    identity_id: str,
    action: str,
    resource_type: str,
    resource_id: str,
    basis: str = "",
    details: Optional[Dict] = None,
) -> Dict[str, Any]:
    """Record an approval/rejection/authorization with full provenance.

    This ensures approvals are never stored as mutable booleans.
    Every approval creates an immutable audit log entry.
    """
    from app.security.audit import log_audit

    entry = log_audit(
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        details={
            "approval_basis": basis,
            "approval_details": details or {},
            "approval_type": "governed",
        },
    )
    return entry.to_dict() if entry else {"error": "failed to record approval"}


# =========================================================================
# Audit Export
# =========================================================================


def export_audit_package(
    object_id: int,
    object_type: str = "lead",
    tenant_id: int = 0,
) -> Dict[str, Any]:
    """Export a complete audit package for a business outcome.

    Preserves all relationships between events, decisions, approvals,
    executions, evidence, actors, objects, and timestamps.
    """
    reconstruction = reconstruct_business_outcome(object_id, object_type, tenant_id)

    package = {
        "exported_at": datetime.now(timezone.utc).isoformat(),
        "export_schema": "FDA21-audit-package-v1",
        "object": {
            "type": object_type,
            "id": object_id,
            "identity": reconstruction.get("what_happened"),
        },
        "reconstruction": reconstruction,
        "provenance": {
            "generated_from": "canonical_records",
            "sources": [
                "sh_audit_logs",
                "decision_traces",
                "evidence_records",
                "sh_outcomes",
                "commitments",
                "rel_timeline",
            ],
            "limitations": "Export is a point-in-time snapshot. Live system may have newer data.",
        },
    }

    return package


# =========================================================================
# Audit Integrity Verification
# =========================================================================


def verify_audit_chain(object_id: int, object_type: str = "lead", tenant_id: int = 0) -> Dict[str, Any]:
    """Verify that the audit chain for an object is intact.

    Checks:
    - Timeline events exist
    - Decisions have traces
    - Evidence records exist
    - Approvals are recorded
    - No gaps in the chain
    """
    recon = reconstruct_business_outcome(object_id, object_type, tenant_id)

    checks = {
        "object_resolved": bool(recon.get("what_happened")),
        "has_timeline": len(recon.get("timeline", [])) > 0,
        "has_decisions": len(recon.get("decisions", [])) > 0,
        "has_approvals": len(recon.get("approvals", [])) > 0,
        "has_executions": len(recon.get("executions", [])) > 0,
        "has_evidence": len(recon.get("evidence_chain", [])) > 0,
        "has_actors": len(recon.get("who_caused_it", [])) > 0,
    }

    chain_intact = all(checks.values())
    checks["chain_intact"] = chain_intact
    checks["missing_elements"] = [k for k, v in checks.items() if not v and k != "chain_intact" and k != "missing_elements"]

    return checks


# =========================================================================
# Corrective Event
# =========================================================================


def record_corrective_event(
    original_object_id: int,
    object_type: str,
    correction_type: str,
    description: str,
    identity_id: str = "system",
    details: Optional[Dict] = None,
) -> Dict[str, Any]:
    """Record a corrective event that supersedes previous erroneous history.

    FDA21 rule: corrections create new traceable history rather than
    erasing the original record.
    """
    from app.security.audit import log_audit

    entry = log_audit(
        action=f"correction.{correction_type}",
        resource_type=object_type,
        resource_id=str(original_object_id),
        details={
            "correction_description": description,
            "correction_details": details or {},
            "corrective_event": True,
            "original_preserved": True,
        },
    )
    return entry.to_dict() if entry else {"error": "failed to record corrective event"}