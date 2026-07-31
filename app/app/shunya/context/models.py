"""SHUNYA — Context Fusion Engine (Phase E).

Canonical context model: WorkspaceContext with identity reference,
knowledge references, session context, tenant context, request metadata,
provenance, fingerprint, and audit timestamps. Immutable once constructed.

Architectural authority: ES-009, SHUNYA_SYSTEM_FLOW.md §2, §9
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


@dataclass
class ContextSection:
    """A section of context produced by a single provider."""
    provider: str  # "identity", "knowledge", "request"
    items: List[Dict[str, Any]] = field(default_factory=list)
    is_degraded: bool = False
    exclusion_reason: Optional[str] = None
    item_count: int = 0
    elapsed_ms: float = 0.0

    def __post_init__(self) -> None:
        if self.item_count == 0:
            self.item_count = len(self.items)


@dataclass
class BudgetReport:
    """Context budgeting report."""
    total_items: int = 0
    max_items: int = 100
    total_size_bytes: int = 0
    max_size_bytes: int = 102400  # 100KB default
    truncated: bool = False
    sections: Dict[str, int] = field(default_factory=dict)


@dataclass
class ContextProvenance:
    """Provenance information for a context assembly."""
    assembled_by: str = "context_fusion_engine"
    assembled_at: Optional[datetime] = None
    identity_engine_version: str = ""
    knowledge_store_version: str = ""
    request_id: str = ""
    correlation_id: str = ""

    def __post_init__(self) -> None:
        if self.assembled_at is None:
            self.assembled_at = datetime.now(timezone.utc)


@dataclass
class WorkspaceContext:
    """The canonical assembled context. Immutable once constructed.

    Fields:
        context_id: Unique identifier for this context assembly.
        tenant_id: Owning tenant.
        actor_id: The requesting actor.
        purpose_code: Purpose classification for eligibility gating.
        fingerprint: Deterministic hash of context content.
        sections: Context sections from each provider.
        budget: Budget enforcement report.
        provenance: Assembly provenance.
        created_at: When this context was assembled.
        metadata: Additional metadata.
        is_degraded: True if any provider was unavailable or budget was exceeded.
    """

    context_id: str = ""
    tenant_id: int = 0
    actor_id: str = ""
    purpose_code: str = ""
    fingerprint: str = ""
    sections: Dict[str, ContextSection] = field(default_factory=dict)
    budget: Optional[BudgetReport] = None
    provenance: Optional[ContextProvenance] = None
    created_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    is_degraded: bool = False

    def __post_init__(self) -> None:
        if not self.context_id:
            self.context_id = str(uuid.uuid4())
        if self.created_at is None:
            self.created_at = datetime.now(timezone.utc)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "context_id": self.context_id,
            "tenant_id": self.tenant_id,
            "actor_id": self.actor_id,
            "purpose_code": self.purpose_code,
            "fingerprint": self.fingerprint,
            "sections": {
                k: {
                    "provider": v.provider,
                    "items": v.items,
                    "is_degraded": v.is_degraded,
                    "exclusion_reason": v.exclusion_reason,
                    "item_count": v.item_count,
                    "elapsed_ms": v.elapsed_ms,
                }
                for k, v in self.sections.items()
            },
            "budget": {
                "total_items": self.budget.total_items if self.budget else 0,
                "max_items": self.budget.max_items if self.budget else 100,
                "total_size_bytes": self.budget.total_size_bytes if self.budget else 0,
                "truncated": self.budget.truncated if self.budget else False,
            } if self.budget else None,
            "provenance": {
                "assembled_by": self.provenance.assembled_by if self.provenance else "",
                "assembled_at": self.provenance.assembled_at.isoformat() if self.provenance and self.provenance.assembled_at else None,
                "request_id": self.provenance.request_id if self.provenance else "",
                "correlation_id": self.provenance.correlation_id if self.provenance else "",
            } if self.provenance else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "metadata": self.metadata,
            "is_degraded": self.is_degraded,
        }


@dataclass
class ContextRequest:
    """Request to assemble a workspace context."""
    tenant_id: int
    actor_id: str
    purpose_code: str = "default"
    subject_id: str = ""
    max_items: int = 100
    max_size_bytes: int = 102400
    timeout_ms: int = 5000
    metadata: Dict[str, Any] = field(default_factory=dict)
    request_id: str = ""
    correlation_id: str = ""