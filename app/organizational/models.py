"""SHUNYA — Organizational Intelligence canonical models (Milestone I).

Business-agnostic, role-centric organizational entities. Every entity is
traceable to underlying evidence and integrates with existing SHUNYA layers.

Architectural authority: ES-012 — Organizational Intelligence
"""

from __future__ import annotations

import hashlib, uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional


# =========================================================================
# Enums
# =========================================================================

class OrgUnitType(str, Enum):
    """Types of organizational units."""
    COMPANY = "company"
    DIVISION = "division"
    DEPARTMENT = "department"
    TEAM = "team"
    PROJECT = "project"
    COMMITTEE = "committee"
    INDIVIDUAL = "individual"


class OrgEntityType(str, Enum):
    """Types of entities in the organizational knowledge graph."""
    ORG_UNIT = "org_unit"
    ROLE = "role"
    PERSON = "person"
    EXECUTION = "execution"
    OBLIGATION = "obligation"
    COMMITMENT = "commitment"
    RESOURCE = "resource"


class DelegationStatus(str, Enum):
    """Status of a delegation."""
    ACTIVE = "active"
    PENDING = "pending"
    EXPIRED = "expired"
    REVOKED = "revoked"
    COMPLETED = "completed"


class AuthorityLevel(int, Enum):
    """Authority levels for approvals and decisions."""
    NONE = 0
    READ = 1
    CONTRIBUTE = 2
    APPROVE = 3
    REVIEW = 4
    ADMIN = 5
    OWNER = 6


# =========================================================================
# 1. Organization Model
# =========================================================================

@dataclass
class OrgUnit:
    """An organizational unit — department, team, project, etc."""
    unit_id: str = ""
    tenant_id: int = 0
    name: str = ""
    unit_type: str = OrgUnitType.DEPARTMENT.value
    parent_unit_id: Optional[str] = None
    description: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: str = ""

    def __post_init__(self) -> None:
        if not self.unit_id:
            raw = f"{self.tenant_id}:{self.name}:{datetime.now(timezone.utc).isoformat()}"
            self.unit_id = hashlib.sha256(raw.encode()).hexdigest()[:16]
        if not self.created_at:
            self.created_at = datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "unit_id": self.unit_id, "tenant_id": self.tenant_id,
            "name": self.name, "unit_type": self.unit_type,
            "parent_unit_id": self.parent_unit_id,
            "description": self.description, "created_at": self.created_at,
        }


@dataclass
class OrgRole:
    """A role within the organization — role-centric, not person-centric."""
    role_id: str = ""
    tenant_id: int = 0
    name: str = ""
    description: str = ""
    parent_role_id: Optional[str] = None
    authority_level: int = AuthorityLevel.READ.value
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: str = ""

    def __post_init__(self) -> None:
        if not self.role_id:
            raw = f"{self.tenant_id}:{self.name}:{datetime.now(timezone.utc).isoformat()}"
            self.role_id = hashlib.sha256(raw.encode()).hexdigest()[:16]
        if not self.created_at:
            self.created_at = datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "role_id": self.role_id, "tenant_id": self.tenant_id,
            "name": self.name, "description": self.description,
            "parent_role_id": self.parent_role_id,
            "authority_level": self.authority_level,
            "created_at": self.created_at,
        }


@dataclass
class RoleAssignment:
    """Assignment of a person to a role in an organizational unit."""
    assignment_id: str = ""
    tenant_id: int = 0
    role_id: str = ""
    person_id: int = 0
    unit_id: str = ""
    is_primary: bool = True
    assigned_at: str = ""
    expires_at: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.assignment_id:
            raw = f"{self.tenant_id}:{self.role_id}:{self.person_id}:{self.unit_id}"
            self.assignment_id = hashlib.sha256(raw.encode()).hexdigest()[:16]
        if not self.assigned_at:
            self.assigned_at = datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "assignment_id": self.assignment_id,
            "tenant_id": self.tenant_id, "role_id": self.role_id,
            "person_id": self.person_id, "unit_id": self.unit_id,
            "is_primary": self.is_primary,
            "assigned_at": self.assigned_at, "expires_at": self.expires_at,
        }


# =========================================================================
# 2. Responsibility Graph
# =========================================================================

@dataclass
class Responsibility:
    """A responsibility linking a role to an entity in the system."""
    responsibility_id: str = ""
    tenant_id: int = 0
    role_id: str = ""
    entity_type: str = ""           # execution, obligation, commitment, resource
    entity_id: str = ""
    description: str = ""
    is_primary: bool = True
    provenance: str = ""            # who/what established this responsibility
    established_at: str = ""

    def __post_init__(self) -> None:
        if not self.responsibility_id:
            raw = f"{self.tenant_id}:{self.role_id}:{self.entity_type}:{self.entity_id}"
            self.responsibility_id = hashlib.sha256(raw.encode()).hexdigest()[:16]
        if not self.established_at:
            self.established_at = datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "responsibility_id": self.responsibility_id,
            "tenant_id": self.tenant_id, "role_id": self.role_id,
            "entity_type": self.entity_type, "entity_id": self.entity_id,
            "description": self.description, "is_primary": self.is_primary,
            "provenance": self.provenance,
            "established_at": self.established_at,
        }


# =========================================================================
# 3. Ownership Intelligence
# =========================================================================

@dataclass
class Ownership:
    """Ownership of an entity by a role or person."""
    ownership_id: str = ""
    tenant_id: int = 0
    entity_type: str = ""           # execution, obligation, resource, commitment
    entity_id: str = ""
    owner_type: str = "role"        # role or person
    owner_id: str = ""              # role_id or person_id
    provenance: str = ""
    established_at: str = ""
    superseded_at: Optional[str] = None

    def __post_init__(self) -> None:
        if not self.ownership_id:
            raw = f"{self.tenant_id}:{self.entity_type}:{self.entity_id}:{self.owner_id}"
            self.ownership_id = hashlib.sha256(raw.encode()).hexdigest()[:16]
        if not self.established_at:
            self.established_at = datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "ownership_id": self.ownership_id,
            "tenant_id": self.tenant_id, "entity_type": self.entity_type,
            "entity_id": self.entity_id, "owner_type": self.owner_type,
            "owner_id": self.owner_id, "provenance": self.provenance,
            "established_at": self.established_at,
            "superseded_at": self.superseded_at,
        }


# =========================================================================
# 4. Delegation Engine
# =========================================================================

@dataclass
class Delegation:
    """Temporary transfer of authority from one role to another."""
    delegation_id: str = ""
    tenant_id: int = 0
    from_role_id: str = ""
    to_role_id: str = ""
    authority_level: int = AuthorityLevel.READ.value
    scope_entity_type: str = ""     # execution, obligation, etc.
    scope_entity_id: str = ""
    reason: str = ""
    status: str = DelegationStatus.PENDING.value
    created_at: str = ""
    expires_at: Optional[str] = None
    provenance: str = ""

    def __post_init__(self) -> None:
        if not self.delegation_id:
            raw = f"{self.tenant_id}:{self.from_role_id}:{self.to_role_id}:{datetime.now(timezone.utc).isoformat()}"
            self.delegation_id = hashlib.sha256(raw.encode()).hexdigest()[:16]
        if not self.created_at:
            self.created_at = datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "delegation_id": self.delegation_id,
            "tenant_id": self.tenant_id,
            "from_role_id": self.from_role_id,
            "to_role_id": self.to_role_id,
            "authority_level": self.authority_level,
            "scope_entity_type": self.scope_entity_type,
            "scope_entity_id": self.scope_entity_id,
            "reason": self.reason, "status": self.status,
            "created_at": self.created_at, "expires_at": self.expires_at,
        }


# =========================================================================
# 5. Authority & Approval Model
# =========================================================================

@dataclass
class Authority:
    """Authority granted to a role for specific actions."""
    authority_id: str = ""
    tenant_id: int = 0
    role_id: str = ""
    action: str = ""                # approve, review, execute, modify, delete
    entity_type: str = ""
    entity_id: str = ""
    level: int = AuthorityLevel.NONE.value
    provenance: str = ""
    established_at: str = ""

    def __post_init__(self) -> None:
        if not self.authority_id:
            raw = f"{self.tenant_id}:{self.role_id}:{self.action}:{self.entity_id}"
            self.authority_id = hashlib.sha256(raw.encode()).hexdigest()[:16]
        if not self.established_at:
            self.established_at = datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "authority_id": self.authority_id,
            "tenant_id": self.tenant_id, "role_id": self.role_id,
            "action": self.action, "entity_type": self.entity_type,
            "entity_id": self.entity_id, "level": self.level,
            "provenance": self.provenance,
        }


@dataclass
class ApprovalChain:
    """A chain of approvals required for a decision."""
    chain_id: str = ""
    tenant_id: int = 0
    decision_type: str = ""         # execution_approval, budget_approval, etc.
    entity_type: str = ""
    entity_id: str = ""
    steps: List[Dict[str, Any]] = field(default_factory=list)
    # Each step: {"role_id": str, "order": int, "status": str, "approved_at": Optional[str]}
    current_step: int = 0
    status: str = "pending"         # pending, in_progress, approved, rejected
    created_at: str = ""
    completed_at: Optional[str] = None

    def __post_init__(self) -> None:
        if not self.chain_id:
            raw = f"{self.tenant_id}:{self.decision_type}:{self.entity_id}:{datetime.now(timezone.utc).isoformat()}"
            self.chain_id = hashlib.sha256(raw.encode()).hexdigest()[:16]
        if not self.created_at:
            self.created_at = datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "chain_id": self.chain_id, "tenant_id": self.tenant_id,
            "decision_type": self.decision_type,
            "entity_type": self.entity_type, "entity_id": self.entity_id,
            "steps": self.steps, "current_step": self.current_step,
            "status": self.status,
            "created_at": self.created_at, "completed_at": self.completed_at,
        }


# =========================================================================
# 6. Collaboration Intelligence
# =========================================================================

@dataclass
class Collaboration:
    """A recorded collaboration between roles."""
    collab_id: str = ""
    tenant_id: int = 0
    role_id_a: str = ""
    role_id_b: str = ""
    entity_type: str = ""
    entity_id: str = ""
    interaction_type: str = "coordinate"  # coordinate, approve, delegate, inform, escalate
    frequency: int = 1
    last_occurrence: str = ""
    provenance: str = ""

    def __post_init__(self) -> None:
        if not self.collab_id:
            raw = f"{self.tenant_id}:{self.role_id_a}:{self.role_id_b}:{self.entity_id}"
            self.collab_id = hashlib.sha256(raw.encode()).hexdigest()[:16]
        if not self.last_occurrence:
            self.last_occurrence = datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "collab_id": self.collab_id, "tenant_id": self.tenant_id,
            "role_id_a": self.role_id_a, "role_id_b": self.role_id_b,
            "entity_type": self.entity_type, "entity_id": self.entity_id,
            "interaction_type": self.interaction_type,
            "frequency": self.frequency,
            "last_occurrence": self.last_occurrence,
        }


# =========================================================================
# 7. Organizational Health
# =========================================================================

@dataclass
class OrgHealth:
    """Health assessment of an organizational unit."""
    unit_id: str
    tenant_id: int
    overall: str = "unknown"
    role_fill_rate: float = 0.0
    delegation_coverage: float = 0.0
    ownership_clarity: float = 0.0
    collaboration_density: float = 0.0
    authority_clarity: float = 0.0
    stale_assignments: int = 0
    dimensions: Dict[str, str] = field(default_factory=dict)
    assessed_at: str = ""

    def __post_init__(self) -> None:
        if not self.assessed_at:
            self.assessed_at = datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "unit_id": self.unit_id, "tenant_id": self.tenant_id,
            "overall": self.overall,
            "role_fill_rate": self.role_fill_rate,
            "delegation_coverage": self.delegation_coverage,
            "ownership_clarity": self.ownership_clarity,
            "collaboration_density": self.collaboration_density,
            "authority_clarity": self.authority_clarity,
            "stale_assignments": self.stale_assignments,
            "dimensions": self.dimensions,
            "assessed_at": self.assessed_at,
        }


# =========================================================================
# 8. Institutional Memory
# =========================================================================

@dataclass
class InstitutionalMemoryEntry:
    """A piece of institutional knowledge about the organization."""
    entry_id: str = ""
    tenant_id: int = 0
    topic: str = ""                 # policy, process, decision, lesson, context
    content: str = ""
    source_role_id: str = ""
    source_entity_type: str = ""
    source_entity_id: str = ""
    tags: List[str] = field(default_factory=list)
    created_at: str = ""
    superseded_by: Optional[str] = None

    def __post_init__(self) -> None:
        if not self.entry_id:
            raw = f"{self.tenant_id}:{self.topic}:{datetime.now(timezone.utc).isoformat()}"
            self.entry_id = hashlib.sha256(raw.encode()).hexdigest()[:16]
        if not self.created_at:
            self.created_at = datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "entry_id": self.entry_id, "tenant_id": self.tenant_id,
            "topic": self.topic, "content": self.content[:100],
            "source_role_id": self.source_role_id,
            "source_entity_type": self.source_entity_type,
            "source_entity_id": self.source_entity_id,
            "tags": self.tags, "created_at": self.created_at,
            "superseded_by": self.superseded_by,
        }


# =========================================================================
# 9. Organizational Knowledge Graph
# =========================================================================

@dataclass
class OrgKnowledgeNode:
    """A node in the organizational knowledge graph."""
    node_id: str = ""
    tenant_id: int = 0
    entity_type: str = ""
    entity_id: str = ""
    label: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.node_id:
            raw = f"{self.tenant_id}:{self.entity_type}:{self.entity_id}"
            self.node_id = hashlib.sha256(raw.encode()).hexdigest()[:16]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "node_id": self.node_id, "tenant_id": self.tenant_id,
            "entity_type": self.entity_type, "entity_id": self.entity_id,
            "label": self.label,
        }


@dataclass
class OrgKnowledgeEdge:
    """An edge in the organizational knowledge graph."""
    edge_id: str = ""
    tenant_id: int = 0
    from_node_id: str = ""
    to_node_id: str = ""
    relationship: str = ""          # reports_to, collaborates_with, delegates_to, owns, responsible_for
    weight: float = 1.0
    provenance: str = ""

    def __post_init__(self) -> None:
        if not self.edge_id:
            raw = f"{self.tenant_id}:{self.from_node_id}:{self.to_node_id}:{self.relationship}"
            self.edge_id = hashlib.sha256(raw.encode()).hexdigest()[:16]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "edge_id": self.edge_id, "tenant_id": self.tenant_id,
            "from_node_id": self.from_node_id,
            "to_node_id": self.to_node_id,
            "relationship": self.relationship,
            "weight": self.weight, "provenance": self.provenance,
        }


# =========================================================================
# 10. Runtime Types
# =========================================================================

@dataclass
class OrgConfig:
    """Configuration for Organizational Intelligence."""
    delegation_max_duration_hours: float = 720.0  # 30 days
    approval_escalation_hours: float = 48.0
    health_role_fill_threshold: float = 0.7
    stale_assignment_threshold_days: int = 90
    knowledge_graph_max_depth: int = 10
    version: str = "mi.1"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "delegation_max_duration_hours": self.delegation_max_duration_hours,
            "approval_escalation_hours": self.approval_escalation_hours,
            "health_role_fill_threshold": self.health_role_fill_threshold,
            "stale_assignment_threshold_days": self.stale_assignment_threshold_days,
            "knowledge_graph_max_depth": self.knowledge_graph_max_depth,
            "version": self.version,
        }


@dataclass
class OrgFilter:
    """Filter for querying organizational intelligence."""
    tenant_id: Optional[int] = None
    unit_ids: Optional[List[str]] = None
    role_ids: Optional[List[str]] = None
    entity_types: Optional[List[str]] = None
    entity_ids: Optional[List[str]] = None
    limit: int = 50
    offset: int = 0


@dataclass
class OrgStats:
    """Organizational intelligence statistics."""
    total_units: int = 0
    total_roles: int = 0
    total_assignments: int = 0
    total_responsibilities: int = 0
    total_delegations: int = 0
    total_collaborations: int = 0
    total_authorities: int = 0
    total_memory_entries: int = 0
    knowledge_graph_nodes: int = 0
    knowledge_graph_edges: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_units": self.total_units,
            "total_roles": self.total_roles,
            "total_assignments": self.total_assignments,
            "total_responsibilities": self.total_responsibilities,
            "total_delegations": self.total_delegations,
            "total_collaborations": self.total_collaborations,
            "total_authorities": self.total_authorities,
            "total_memory_entries": self.total_memory_entries,
            "knowledge_graph_nodes": self.knowledge_graph_nodes,
            "knowledge_graph_edges": self.knowledge_graph_edges,
        }