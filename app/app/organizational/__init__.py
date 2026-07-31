"""SHUNYA — Organizational Intelligence (Milestone I)

Represents organizations as living systems: roles, responsibilities,
ownership, authority, delegation, collaboration, health, and institutional
memory — all business-agnostic, role-centric, and evidence-backed.

Architecture:
  OrganizationModel         → Canonical org entities (units, roles, assignments)
  ResponsibilityGraph      → Who is responsible for what
  OwnershipIntelligence    → Ownership tracking for executions/obligations
  DelegationEngine         → Temporary authority transfer
  AuthorityApprovalModel   → Approval chains and authority resolution
  CollaborationIntelligence → Cross-role collaboration patterns
  OrgHealthEngine          → Organizational health assessment
  InstitutionalMemory      → Knowledge about the organization itself
  OrgKnowledgeGraph        → Connected org entities
  ExplainabilityLayer      → Evidence traces for org conclusions
  RuntimeService           → Integration layer
"""

from app.organizational.models import (
    OrgUnitType, OrgEntityType, DelegationStatus, AuthorityLevel,
    OrgUnit, OrgRole, RoleAssignment, Responsibility,
    Ownership, Delegation, Authority, ApprovalChain,
    Collaboration, OrgHealth, InstitutionalMemoryEntry,
    OrgKnowledgeNode, OrgKnowledgeEdge,
    OrgConfig, OrgFilter, OrgStats,
)
from app.organizational.engine import (
    OrganizationalIntelligenceEngine,
    get_organizational_intelligence,
    reset_organizational_intelligence,
    ResponsibilityGraph,
    OwnershipIntelligence,
    DelegationEngine,
    AuthorityApprovalModel,
    CollaborationIntelligence,
    OrgHealthEngine,
    InstitutionalMemory,
    OrgKnowledgeGraph,
    ExplainabilityLayer,
    RuntimeService,
)

__all__ = [
    "OrganizationalIntelligenceEngine",
    "get_organizational_intelligence",
    "reset_organizational_intelligence",
    "ResponsibilityGraph", "OwnershipIntelligence",
    "DelegationEngine", "AuthorityApprovalModel",
    "CollaborationIntelligence", "OrgHealthEngine",
    "InstitutionalMemory", "OrgKnowledgeGraph",
    "ExplainabilityLayer", "RuntimeService",
    # Enums
    "OrgUnitType", "OrgEntityType", "DelegationStatus", "AuthorityLevel",
    # Models
    "OrgUnit", "OrgRole", "RoleAssignment",
    "Responsibility", "Ownership", "Delegation", "Authority",
    "ApprovalChain", "Collaboration", "OrgHealth",
    "InstitutionalMemoryEntry",
    "OrgKnowledgeNode", "OrgKnowledgeEdge",
    "OrgConfig", "OrgFilter", "OrgStats",
]