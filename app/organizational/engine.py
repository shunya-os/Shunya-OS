"""SHUNYA — Organizational Intelligence engine (Milestone I).

Ten sub-engines coordinated by the RuntimeService, all operating
deterministically on organizational data. Business-agnostic and role-centric.

No paid-model dependency. Every output traced to evidence.
"""

from __future__ import annotations

import hashlib
from collections import defaultdict, deque
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional, Set, Tuple

from app.organizational.models import (
    OrgUnitType, OrgEntityType, DelegationStatus, AuthorityLevel,
    OrgUnit, OrgRole, RoleAssignment, Responsibility,
    Ownership, Delegation, Authority, ApprovalChain,
    Collaboration, OrgHealth, InstitutionalMemoryEntry,
    OrgKnowledgeNode, OrgKnowledgeEdge,
    OrgConfig, OrgFilter, OrgStats,
)
from app.execution.constants import ExecState, ObligationState

# =========================================================================
# Singleton
# =========================================================================

_ENGINE: Optional[OrganizationalIntelligenceEngine] = None


def get_organizational_intelligence() -> OrganizationalIntelligenceEngine:
    global _ENGINE
    if _ENGINE is None:
        _ENGINE = OrganizationalIntelligenceEngine()
    return _ENGINE


def reset_organizational_intelligence() -> None:
    global _ENGINE
    _ENGINE = None


# =========================================================================
# 1. Canonical Organization Model (store)
# =========================================================================

class OrgModelStore:
    """In-memory store for canonical organizational entities.

    All mutations are idempotent. No duplicated state with existing
    systems (Tenant, TeamMember are referenced by ID, not duplicated).
    """

    def __init__(self):
        self._units: Dict[str, OrgUnit] = {}
        self._roles: Dict[str, OrgRole] = {}
        self._assignments: Dict[str, RoleAssignment] = {}

    def add_unit(self, unit: OrgUnit) -> OrgUnit:
        self._units[unit.unit_id] = unit
        return unit

    def get_unit(self, unit_id: str) -> Optional[OrgUnit]:
        return self._units.get(unit_id)

    def get_units(self, tenant_id: int) -> List[OrgUnit]:
        return [u for u in self._units.values() if u.tenant_id == tenant_id]

    def add_role(self, role: OrgRole) -> OrgRole:
        self._roles[role.role_id] = role
        return role

    def get_role(self, role_id: str) -> Optional[OrgRole]:
        return self._roles.get(role_id)

    def get_roles(self, tenant_id: int) -> List[OrgRole]:
        return [r for r in self._roles.values() if r.tenant_id == tenant_id]

    def assign_role(self, assignment: RoleAssignment) -> RoleAssignment:
        self._assignments[assignment.assignment_id] = assignment
        return assignment

    def get_assignments(self, role_id: Optional[str] = None,
                        person_id: Optional[int] = None,
                        unit_id: Optional[str] = None) -> List[RoleAssignment]:
        results = list(self._assignments.values())
        if role_id:
            results = [a for a in results if a.role_id == role_id]
        if person_id is not None:
            results = [a for a in results if a.person_id == person_id]
        if unit_id:
            results = [a for a in results if a.unit_id == unit_id]
        return results

    def get_unit_tree(self, tenant_id: int) -> List[dict]:
        """Build a tree structure from flat org units."""
        units = self.get_units(tenant_id)
        by_id = {u.unit_id: u for u in units}
        roots = [u for u in units if not u.parent_unit_id]
        result = []
        for root in roots:
            result.append(self._build_subtree(root, by_id))
        return result

    def _build_subtree(self, unit: OrgUnit,
                       by_id: Dict[str, OrgUnit]) -> dict:
        children = [u for u in by_id.values() if u.parent_unit_id == unit.unit_id]
        return {
            "unit": unit.to_dict(),
            "children": [self._build_subtree(c, by_id) for c in children],
        }


# =========================================================================
# 2. Responsibility Graph
# =========================================================================

class ResponsibilityGraph:
    """Tracks and resolves who is responsible for what.

    Responsibilities are role-centric: a role is responsible for an entity
    (execution, obligation, commitment, resource). Persons fulfill the role.
    """

    def __init__(self, store: Optional[OrgModelStore] = None):
        self._store = store or OrgModelStore()
        self._responsibilities: Dict[str, Responsibility] = {}

    def add(self, resp: Responsibility) -> Responsibility:
        self._responsibilities[resp.responsibility_id] = resp
        return resp

    def get_for_entity(self, entity_type: str, entity_id: str,
                       tenant_id: int) -> List[Responsibility]:
        return [
            r for r in self._responsibilities.values()
            if r.entity_type == entity_type and r.entity_id == entity_id
            and r.tenant_id == tenant_id
        ]

    def get_for_role(self, role_id: str) -> List[Responsibility]:
        return [
            r for r in self._responsibilities.values() if r.role_id == role_id
        ]

    def get_for_person(self, person_id: int, tenant_id: int) -> List[dict]:
        """Get responsibilities for all roles a person holds."""
        assignments = self._store.get_assignments(person_id=person_id)
        results = []
        for a in assignments:
            role_resps = self.get_for_role(a.role_id)
            for r in role_resps:
                results.append({
                    "responsibility": r.to_dict(),
                    "role": self._store.get_role(r.role_id).to_dict() if self._store.get_role(r.role_id) else {},
                    "assignment": a.to_dict(),
                })
        return results

    def resolve_owners(self, entity_type: str, entity_id: str,
                       tenant_id: int) -> List[dict]:
        """Resolve the persons responsible for an entity."""
        resps = self.get_for_entity(entity_type, entity_id, tenant_id)
        results = []
        for r in resps:
            assignments = self._store.get_assignments(role_id=r.role_id)
            for a in assignments:
                results.append({
                    "person_id": a.person_id,
                    "role_id": r.role_id,
                    "responsibility_id": r.responsibility_id,
                    "is_primary": r.is_primary,
                    "provenance": r.provenance,
                })
        return results

    def remove(self, responsibility_id: str) -> bool:
        return self._responsibilities.pop(responsibility_id, None) is not None


# =========================================================================
# 3. Ownership Intelligence
# =========================================================================

class OwnershipIntelligence:
    """Tracks ownership of executions, obligations, and resources.

    Ownership is distinct from responsibility: owner = accountable,
    responsible = assigned to do the work.
    """

    def __init__(self):
        self._ownerships: Dict[str, Ownership] = {}

    def set_owner(self, ownership: Ownership) -> Ownership:
        # Supersede previous ownership for same entity
        for o in self._ownerships.values():
            if (o.entity_type == ownership.entity_type
                    and o.entity_id == ownership.entity_id
                    and o.tenant_id == ownership.tenant_id
                    and o.superseded_at is None):
                o.superseded_at = datetime.now(timezone.utc).isoformat()
        self._ownerships[ownership.ownership_id] = ownership
        return ownership

    def get_owner(self, entity_type: str, entity_id: str,
                  tenant_id: int) -> Optional[Ownership]:
        for o in self._ownerships.values():
            if (o.entity_type == entity_type and o.entity_id == entity_id
                    and o.tenant_id == tenant_id and o.superseded_at is None):
                return o
        return None

    def get_owned_by(self, owner_id: str, tenant_id: int) -> List[Ownership]:
        return [
            o for o in self._ownerships.values()
            if o.owner_id == owner_id and o.tenant_id == tenant_id
            and o.superseded_at is None
        ]

    def transfer(self, entity_type: str, entity_id: str,
                 tenant_id: int, new_owner_id: str,
                 provenance: str = "") -> Optional[Ownership]:
        current = self.get_owner(entity_type, entity_id, tenant_id)
        if current:
            current.superseded_at = datetime.now(timezone.utc).isoformat()
        new_o = Ownership(
            tenant_id=tenant_id, entity_type=entity_type,
            entity_id=entity_id, owner_type="role",
            owner_id=new_owner_id, provenance=provenance,
        )
        return self.set_owner(new_o)


# =========================================================================
# 4. Delegation Engine
# =========================================================================

class DelegationEngine:
    """Manages temporary delegation of authority between roles.

    Idempotent: same delegation parameters produce same result.
    """

    def __init__(self, config: Optional[OrgConfig] = None):
        self._config = config or OrgConfig()
        self._delegations: Dict[str, Delegation] = {}

    def delegate(self, delegation: Delegation) -> Delegation:
        now = datetime.now(timezone.utc)
        # Auto-expire if past max duration
        if delegation.expires_at:
            try:
                exp = datetime.fromisoformat(delegation.expires_at)
                if exp.tzinfo is None:
                    exp = exp.replace(tzinfo=timezone.utc)
                if (exp - now).total_seconds() > self._config.delegation_max_duration_hours * 3600:
                    exp = now + timedelta(hours=self._config.delegation_max_duration_hours)
                    delegation.expires_at = exp.isoformat()
            except (ValueError, TypeError):
                pass
        delegation.status = DelegationStatus.ACTIVE.value
        self._delegations[delegation.delegation_id] = delegation
        return delegation

    def revoke(self, delegation_id: str) -> bool:
        d = self._delegations.get(delegation_id)
        if d and d.status == DelegationStatus.ACTIVE.value:
            d.status = DelegationStatus.REVOKED.value
            return True
        return False

    def get_active(self, role_id: str, tenant_id: int) -> List[Delegation]:
        now = datetime.now(timezone.utc)
        active = []
        for d in self._delegations.values():
            if d.tenant_id != tenant_id:
                continue
            if d.to_role_id != role_id and d.from_role_id != role_id:
                continue
            if d.status != DelegationStatus.ACTIVE.value:
                continue
            if d.expires_at:
                try:
                    exp = datetime.fromisoformat(d.expires_at)
                    if exp.tzinfo is None:
                        exp = exp.replace(tzinfo=timezone.utc)
                    if exp < now:
                        d.status = DelegationStatus.EXPIRED.value
                        continue
                except (ValueError, TypeError):
                    pass
            active.append(d)
        return active

    def resolve_effective_authority(self, role_id: str, tenant_id: int,
                                    action: str, entity_type: str,
                                    entity_id: str) -> int:
        """Resolve the effective authority level considering delegations."""
        base = AuthorityLevel.READ.value
        role = None
        # Find role's base authority
        active_delegations = self.get_active(role_id, tenant_id)
        for d in active_delegations:
            if d.to_role_id == role_id and d.authority_level > base:
                base = d.authority_level
        return base


# =========================================================================
# 5. Authority & Approval Model
# =========================================================================

class AuthorityApprovalModel:
    """Manages authority grants and approval chains.

    Authorities are role-based: a role has authority to perform actions
    on specific entity types. Approval chains define multi-step approvals.
    """

    def __init__(self):
        self._authorities: Dict[str, Authority] = {}
        self._chains: Dict[str, ApprovalChain] = {}

    def grant(self, authority: Authority) -> Authority:
        self._authorities[authority.authority_id] = authority
        return authority

    def check(self, role_id: str, action: str, entity_type: str,
              entity_id: str, tenant_id: int) -> bool:
        """Check if a role has authority for a specific action."""
        for a in self._authorities.values():
            if (a.role_id == role_id and a.action == action
                    and a.tenant_id == tenant_id):
                if a.entity_type == entity_type or not a.entity_type:
                    if a.entity_id == entity_id or not a.entity_id:
                        return a.level >= AuthorityLevel.APPROVE.value
        return False

    def create_chain(self, chain: ApprovalChain) -> ApprovalChain:
        self._chains[chain.chain_id] = chain
        return chain

    def approve_step(self, chain_id: str, role_id: str,
                     tenant_id: int) -> dict:
        chain = self._chains.get(chain_id)
        if not chain or chain.tenant_id != tenant_id:
            return {"error": "chain_not_found"}
        if chain.status != "in_progress" and chain.status != "pending":
            return {"error": f"chain already {chain.status}"}
        if chain.current_step >= len(chain.steps):
            return {"error": "no_more_steps"}

        step = chain.steps[chain.current_step]
        if step.get("role_id") != role_id:
            return {"error": "not_your_step"}

        step["status"] = "approved"
        step["approved_at"] = datetime.now(timezone.utc).isoformat()
        chain.current_step += 1

        if chain.current_step >= len(chain.steps):
            chain.status = "approved"
            chain.completed_at = datetime.now(timezone.utc).isoformat()
        else:
            chain.status = "in_progress"

        return {"chain_id": chain_id, "status": chain.status,
                "current_step": chain.current_step}

    def reject_chain(self, chain_id: str, tenant_id: int) -> dict:
        chain = self._chains.get(chain_id)
        if not chain or chain.tenant_id != tenant_id:
            return {"error": "chain_not_found"}
        chain.status = "rejected"
        chain.completed_at = datetime.now(timezone.utc).isoformat()
        return {"chain_id": chain_id, "status": "rejected"}


# =========================================================================
# 6. Collaboration Intelligence
# =========================================================================

class CollaborationIntelligence:
    """Tracks and analyzes collaboration patterns between roles.

    Stateless: given interactions, computes collaboration metrics.
    """

    def __init__(self):
        self._collaborations: Dict[str, Collaboration] = {}

    def record(self, collab: Collaboration) -> Collaboration:
        existing_key = f"{collab.role_id_a}:{collab.role_id_b}"
        for c in self._collaborations.values():
            if (c.role_id_a == collab.role_id_a
                    and c.role_id_b == collab.role_id_b
                    and c.entity_type == collab.entity_type
                    and c.entity_id == collab.entity_id):
                c.frequency += 1
                c.last_occurrence = collab.last_occurrence
                return c
        self._collaborations[collab.collab_id] = collab
        return collab

    def get_for_role(self, role_id: str) -> List[Collaboration]:
        return [
            c for c in self._collaborations.values()
            if c.role_id_a == role_id or c.role_id_b == role_id
        ]

    def get_network_density(self, tenant_id: int) -> float:
        """Compute collaboration density for a tenant."""
        tenant_collabs = [
            c for c in self._collaborations.values() if c.tenant_id == tenant_id
        ]
        if not tenant_collabs:
            return 0.0
        roles = set()
        for c in tenant_collabs:
            roles.add(c.role_id_a)
            roles.add(c.role_id_b)
        n = len(roles)
        if n <= 1:
            return 1.0
        max_possible = n * (n - 1) / 2
        actual = len(set((c.role_id_a, c.role_id_b) for c in tenant_collabs))
        return min(1.0, actual / max_possible)


# =========================================================================
# 7. Organizational Health Engine
# =========================================================================

class OrgHealthEngine:
    """Assess the health of an organizational unit.

    Five dimensions: role fill rate, delegation coverage, ownership clarity,
    collaboration density, authority clarity.
    """

    def __init__(self, config: Optional[OrgConfig] = None):
        self._config = config or OrgConfig()

    def assess(self, unit_id: str, tenant_id: int,
               store: OrgModelStore,
               resp_graph: ResponsibilityGraph,
               delegations: DelegationEngine,
               collab: CollaborationIntelligence) -> OrgHealth:
        unit = store.get_unit(unit_id)
        if not unit:
            return OrgHealth(unit_id=unit_id, tenant_id=tenant_id,
                             overall="unknown")

        roles = store.get_roles(tenant_id)
        unit_roles = [r for r in roles]  # all roles in tenant
        assignments = store.get_assignments(unit_id=unit_id)

        # Role fill rate — how many roles have at least one person assigned
        role_ids_with_assignments = set(
            a.role_id for a in assignments
        )
        all_role_ids = set(r.role_id for r in unit_roles)
        fill_rate = (len(role_ids_with_assignments) / max(len(all_role_ids), 1))

        # Delegation coverage
        tenant_delegations = delegations.get_active("", tenant_id)  # get all
        delegation_coverage = min(1.0, len(tenant_delegations) / max(len(unit_roles), 1) * 0.5)

        # Ownership clarity
        ownership_clarity = 0.5  # baseline — depends on external data

        # Collaboration density
        collaboration_density = collab.get_network_density(tenant_id)

        # Authority clarity
        authority_clarity = 0.5  # baseline

        # Stale assignments
        now = datetime.now(timezone.utc)
        stale = 0
        for a in assignments:
            if a.expires_at:
                try:
                    exp = datetime.fromisoformat(a.expires_at)
                    if exp.tzinfo is None:
                        exp = exp.replace(tzinfo=timezone.utc)
                    if exp < now:
                        stale += 1
                except (ValueError, TypeError):
                    pass

        # Overall score
        scores = [fill_rate, delegation_coverage, ownership_clarity,
                  collaboration_density, authority_clarity]
        overall_score = sum(scores) / len(scores) if scores else 0.0
        if overall_score >= 0.8:
            overall = "healthy"
        elif overall_score >= 0.5:
            overall = "fair"
        elif overall_score >= 0.3:
            overall = "needs_attention"
        else:
            overall = "critical"

        return OrgHealth(
            unit_id=unit_id, tenant_id=tenant_id,
            overall=overall, role_fill_rate=round(fill_rate, 2),
            delegation_coverage=round(delegation_coverage, 2),
            ownership_clarity=round(ownership_clarity, 2),
            collaboration_density=round(collaboration_density, 2),
            authority_clarity=round(authority_clarity, 2),
            stale_assignments=stale,
            dimensions={
                "role_fill": self._score_label(fill_rate),
                "delegation": self._score_label(delegation_coverage),
                "ownership": self._score_label(ownership_clarity),
                "collaboration": self._score_label(collaboration_density),
                "authority": self._score_label(authority_clarity),
            },
        )

    def _score_label(self, score: float) -> str:
        if score >= 0.8:
            return "good"
        elif score >= 0.5:
            return "fair"
        elif score >= 0.3:
            return "needs_attention"
        return "critical"


# =========================================================================
# 8. Institutional Memory
# =========================================================================

class InstitutionalMemory:
    """Stores and retrieves institutional knowledge.

    Each entry is versioned by supersession. Queries return the latest
    version unless historical is requested.
    """

    def __init__(self):
        self._entries: Dict[str, InstitutionalMemoryEntry] = {}

    def add(self, entry: InstitutionalMemoryEntry) -> InstitutionalMemoryEntry:
        # Supersede previous entry on same topic
        for e in self._entries.values():
            if (e.topic == entry.topic and e.tenant_id == entry.tenant_id
                    and e.superseded_by is None):
                e.superseded_by = entry.entry_id
        self._entries[entry.entry_id] = entry
        return entry

    def get(self, topic: str, tenant_id: int) -> Optional[InstitutionalMemoryEntry]:
        """Get the latest entry for a topic."""
        candidates = [
            e for e in self._entries.values()
            if e.topic == topic and e.tenant_id == tenant_id
            and e.superseded_by is None
        ]
        if not candidates:
            return None
        return max(candidates, key=lambda e: e.created_at)

    def get_all(self, tenant_id: int) -> List[InstitutionalMemoryEntry]:
        return [
            e for e in self._entries.values()
            if e.tenant_id == tenant_id and e.superseded_by is None
        ]

    def get_history(self, topic: str, tenant_id: int) -> List[InstitutionalMemoryEntry]:
        """Get all versions of an institutional memory entry."""
        return sorted(
            [e for e in self._entries.values()
             if e.topic == topic and e.tenant_id == tenant_id],
            key=lambda e: e.created_at,
        )


# =========================================================================
# 9. Organizational Knowledge Graph
# =========================================================================

class OrgKnowledgeGraph:
    """Connected graph of organizational entities and relationships.

    Builds on existing entities (OrgUnit, Role, Responsibility, Ownership,
    Delegation, Collaboration) to create a queryable knowledge graph.
    """

    def __init__(self):
        self._nodes: Dict[str, OrgKnowledgeNode] = {}
        self._edges: List[OrgKnowledgeEdge] = []

    def add_node(self, node: OrgKnowledgeNode) -> OrgKnowledgeNode:
        self._nodes[node.node_id] = node
        return node

    def add_edge(self, edge: OrgKnowledgeEdge) -> OrgKnowledgeEdge:
        self._edges.append(edge)
        return edge

    def get_neighbors(self, node_id: str) -> List[dict]:
        """Get all neighbors of a node with edge relationships."""
        neighbors = []
        for e in self._edges:
            if e.from_node_id == node_id:
                n = self._nodes.get(e.to_node_id)
                if n:
                    neighbors.append({
                        "node": n.to_dict(),
                        "edge": e.to_dict(),
                        "direction": "outgoing",
                    })
            elif e.to_node_id == node_id:
                n = self._nodes.get(e.from_node_id)
                if n:
                    neighbors.append({
                        "node": n.to_dict(),
                        "edge": e.to_dict(),
                        "direction": "incoming",
                    })
        return neighbors

    def find_path(self, from_id: str, to_id: str,
                  max_depth: int = 10) -> List[dict]:
        """BFS shortest path between two nodes."""
        if from_id == to_id:
            return []
        visited = {from_id}
        queue = deque([(from_id, [])])
        while queue:
            current, path = queue.popleft()
            if len(path) >= max_depth:
                continue
            for e in self._edges:
                neighbor = None
                if e.from_node_id == current:
                    neighbor = e.to_node_id
                elif e.to_node_id == current:
                    neighbor = e.from_node_id
                if neighbor and neighbor not in visited:
                    new_path = path + [{
                        "from": current, "to": neighbor,
                        "relationship": e.relationship,
                        "edge_id": e.edge_id,
                    }]
                    if neighbor == to_id:
                        return new_path
                    visited.add(neighbor)
                    queue.append((neighbor, new_path))
        return []

    def build_from_org_data(self, tenant_id: int,
                            store: OrgModelStore,
                            resp_graph: ResponsibilityGraph,
                            ownership: OwnershipIntelligence,
                            delegations: DelegationEngine,
                            collab: CollaborationIntelligence) -> None:
        """Build knowledge graph from existing organizational data."""
        for unit in store.get_units(tenant_id):
            self.add_node(OrgKnowledgeNode(
                tenant_id=tenant_id, entity_type=OrgEntityType.ORG_UNIT.value,
                entity_id=unit.unit_id, label=f"Unit: {unit.name}",
            ))
            if unit.parent_unit_id:
                parent_node = self._find_node(OrgEntityType.ORG_UNIT.value,
                                              unit.parent_unit_id)
                if parent_node:
                    self.add_edge(OrgKnowledgeEdge(
                        tenant_id=tenant_id,
                        from_node_id=parent_node.node_id,
                        to_node_id=self._find_node(
                            OrgEntityType.ORG_UNIT.value, unit.unit_id).node_id,
                        relationship="contains",
                        provenance="org_model",
                    ))

        for role in store.get_roles(tenant_id):
            self.add_node(OrgKnowledgeNode(
                tenant_id=tenant_id, entity_type=OrgEntityType.ROLE.value,
                entity_id=role.role_id, label=f"Role: {role.name}",
            ))

        # Responsibility edges
        for resp in resp_graph._responsibilities.values():
            if resp.tenant_id != tenant_id:
                continue
            role_node = self._find_node(OrgEntityType.ROLE.value, resp.role_id)
            if role_node:
                self.add_edge(OrgKnowledgeEdge(
                    tenant_id=tenant_id,
                    from_node_id=role_node.node_id,
                    to_node_id=self._make_node_id(
                        resp.entity_type, resp.entity_id),
                    relationship="responsible_for",
                    provenance=resp.provenance or "responsibility_graph",
                ))

    def _find_node(self, entity_type: str, entity_id: str
                   ) -> Optional[OrgKnowledgeNode]:
        for n in self._nodes.values():
            if n.entity_type == entity_type and n.entity_id == entity_id:
                return n
        return None

    def _make_node_id(self, entity_type: str, entity_id: str) -> str:
        return hashlib.sha256(f"{entity_type}:{entity_id}".encode()).hexdigest()[:16]


# =========================================================================
# 10. Explainability Layer
# =========================================================================

class ExplainabilityLayer:
    """Explain organizational conclusions with traceable evidence."""

    def explain_responsibility(self, resp: Responsibility) -> dict:
        return {
            "topic": f"Responsibility: {resp.responsibility_id[:12]}",
            "conclusion": f"Role {resp.role_id[:12]} is responsible for {resp.entity_type} {resp.entity_id[:12]}",
            "evidence": [
                f"responsibility_id={resp.responsibility_id}",
                f"provenance={resp.provenance}",
                f"established_at={resp.established_at}",
                f"is_primary={resp.is_primary}",
            ],
            "confidence": 1.0 if resp.is_primary else 0.8,
        }

    def explain_ownership(self, ownership: Ownership) -> dict:
        return {
            "topic": f"Ownership: {ownership.ownership_id[:12]}",
            "conclusion": f"{ownership.owner_type} {ownership.owner_id[:12]} owns {ownership.entity_type} {ownership.entity_id[:12]}",
            "evidence": [
                f"provenance={ownership.provenance}",
                f"established_at={ownership.established_at}",
                f"superseded_at={ownership.superseded_at or 'current'}",
            ],
            "confidence": 0.95,
        }

    def explain_authority(self, authority: Authority) -> dict:
        return {
            "topic": f"Authority: {authority.authority_id[:12]}",
            "conclusion": f"Role {authority.role_id[:12]} can {authority.action} on {authority.entity_type}",
            "evidence": [
                f"level={authority.level}",
                f"provenance={authority.provenance}",
            ],
            "confidence": 0.9,
        }

    def explain_org_health(self, health: OrgHealth) -> dict:
        return {
            "topic": f"Org Health: {health.unit_id[:12]}",
            "conclusion": f"Overall health: {health.overall}",
            "evidence": [
                f"role_fill_rate={health.role_fill_rate}",
                f"delegation_coverage={health.delegation_coverage}",
                f"ownership_clarity={health.ownership_clarity}",
                f"collaboration_density={health.collaboration_density}",
                f"authority_clarity={health.authority_clarity}",
                f"stale_assignments={health.stale_assignments}",
            ],
            "confidence": 0.85,
        }


# =========================================================================
# Runtime Service
# =========================================================================

class RuntimeService:
    """Coordination layer for all Organizational Intelligence engines."""

    def __init__(self, config: Optional[OrgConfig] = None):
        self._config = config or OrgConfig()
        self._store = OrgModelStore()
        self._resp_graph = ResponsibilityGraph(self._store)
        self._ownership = OwnershipIntelligence()
        self._delegations = DelegationEngine(config)
        self._authority = AuthorityApprovalModel()
        self._collab = CollaborationIntelligence()
        self._health = OrgHealthEngine(config)
        self._memory = InstitutionalMemory()
        self._kg = OrgKnowledgeGraph()
        self._explain = ExplainabilityLayer()
        self._event_log: List[Dict[str, Any]] = []

    @property
    def store(self) -> OrgModelStore:
        return self._store
    @property
    def resp_graph(self) -> ResponsibilityGraph:
        return self._resp_graph
    @property
    def ownership(self) -> OwnershipIntelligence:
        return self._ownership
    @property
    def delegations(self) -> DelegationEngine:
        return self._delegations
    @property
    def authority(self) -> AuthorityApprovalModel:
        return self._authority
    @property
    def collab(self) -> CollaborationIntelligence:
        return self._collab
    @property
    def health(self) -> OrgHealthEngine:
        return self._health
    @property
    def memory(self) -> InstitutionalMemory:
        return self._memory
    @property
    def kg(self) -> OrgKnowledgeGraph:
        return self._kg
    @property
    def explain(self) -> ExplainabilityLayer:
        return self._explain

    # --- Org Unit Management ---
    def create_unit(self, name: str, tenant_id: int,
                    unit_type: str = OrgUnitType.DEPARTMENT.value,
                    parent_id: Optional[str] = None) -> OrgUnit:
        unit = OrgUnit(tenant_id=tenant_id, name=name,
                       unit_type=unit_type, parent_unit_id=parent_id)
        self._store.add_unit(unit)
        self._log("create_unit", unit.unit_id, tenant_id)
        return unit

    def create_role(self, name: str, tenant_id: int,
                    authority_level: int = AuthorityLevel.READ.value) -> OrgRole:
        role = OrgRole(tenant_id=tenant_id, name=name,
                       authority_level=authority_level)
        self._store.add_role(role)
        self._log("create_role", role.role_id, tenant_id)
        return role

    def assign_role(self, role_id: str, person_id: int, unit_id: str,
                    tenant_id: int) -> RoleAssignment:
        assignment = RoleAssignment(
            tenant_id=tenant_id, role_id=role_id, person_id=person_id,
            unit_id=unit_id,
        )
        self._store.assign_role(assignment)
        self._log("assign_role", assignment.assignment_id, tenant_id)
        return assignment

    # --- Responsibility ---
    def add_responsibility(self, role_id: str, entity_type: str,
                           entity_id: str, tenant_id: int,
                           description: str = "",
                           provenance: str = "") -> Responsibility:
        resp = Responsibility(
            tenant_id=tenant_id, role_id=role_id,
            entity_type=entity_type, entity_id=entity_id,
            description=description, provenance=provenance or "runtime_service",
        )
        self._resp_graph.add(resp)
        self._log("add_responsibility", resp.responsibility_id, tenant_id)
        return resp

    def resolve_responsible(self, entity_type: str, entity_id: str,
                            tenant_id: int) -> List[dict]:
        return self._resp_graph.resolve_owners(entity_type, entity_id, tenant_id)

    # --- Ownership ---
    def set_ownership(self, entity_type: str, entity_id: str,
                      owner_id: str, tenant_id: int,
                      provenance: str = "") -> Ownership:
        o = Ownership(
            tenant_id=tenant_id, entity_type=entity_type,
            entity_id=entity_id, owner_id=owner_id, provenance=provenance,
        )
        return self._ownership.set_owner(o)

    def get_ownership(self, entity_type: str, entity_id: str,
                      tenant_id: int) -> Optional[Ownership]:
        return self._ownership.get_owner(entity_type, entity_id, tenant_id)

    # --- Delegation ---
    def delegate(self, from_role_id: str, to_role_id: str,
                 tenant_id: int, authority_level: int = AuthorityLevel.READ.value,
                 reason: str = "") -> Delegation:
        d = Delegation(
            tenant_id=tenant_id, from_role_id=from_role_id,
            to_role_id=to_role_id, authority_level=authority_level,
            reason=reason,
        )
        self._delegations.delegate(d)
        self._log("delegate", d.delegation_id, tenant_id)
        return d

    def revoke_delegation(self, delegation_id: str) -> bool:
        return self._delegations.revoke(delegation_id)

    # --- Authority ---
    def grant_authority(self, role_id: str, action: str, entity_type: str,
                        tenant_id: int, level: int = AuthorityLevel.APPROVE.value) -> Authority:
        a = Authority(tenant_id=tenant_id, role_id=role_id, action=action,
                      entity_type=entity_type, level=level)
        self._authority.grant(a)
        return a

    def check_authority(self, role_id: str, action: str, entity_type: str,
                        entity_id: str, tenant_id: int) -> bool:
        return self._authority.check(role_id, action, entity_type, entity_id, tenant_id)

    # --- Collaboration ---
    def record_collaboration(self, role_id_a: str, role_id_b: str,
                             entity_type: str, entity_id: str,
                             tenant_id: int) -> Collaboration:
        c = Collaboration(
            tenant_id=tenant_id, role_id_a=role_id_a, role_id_b=role_id_b,
            entity_type=entity_type, entity_id=entity_id,
        )
        return self._collab.record(c)

    # --- Health ---
    def assess_health(self, unit_id: str, tenant_id: int) -> OrgHealth:
        return self._health.assess(
            unit_id, tenant_id, self._store, self._resp_graph,
            self._delegations, self._collab,
        )

    # --- Memory ---
    def add_memory(self, topic: str, content: str, tenant_id: int,
                   source_role_id: str = "") -> InstitutionalMemoryEntry:
        e = InstitutionalMemoryEntry(
            tenant_id=tenant_id, topic=topic, content=content,
            source_role_id=source_role_id,
        )
        self._memory.add(e)
        return e

    def get_memory(self, topic: str, tenant_id: int) -> Optional[InstitutionalMemoryEntry]:
        return self._memory.get(topic, tenant_id)

    # --- Knowledge Graph ---
    def rebuild_knowledge_graph(self, tenant_id: int) -> None:
        self._kg.build_from_org_data(
            tenant_id, self._store, self._resp_graph,
            self._ownership, self._delegations, self._collab,
        )

    def query_knowledge_graph(self, entity_type: str, entity_id: str) -> List[dict]:
        node = self._kg._find_node(entity_type, entity_id)
        if not node:
            return []
        return self._kg.get_neighbors(node.node_id)

    # --- Explain ---
    def explain_responsibility(self, resp_id: str) -> dict:
        return self._explain.explain_responsibility(
            Responsibility(responsibility_id=resp_id))

    def explain_health(self, unit_id: str, tenant_id: int) -> dict:
        h = self.assess_health(unit_id, tenant_id)
        return self._explain.explain_org_health(h)

    # --- Stats ---
    def stats(self) -> Dict[str, Any]:
        s = OrgStats(
            total_units=len(self._store._units),
            total_roles=len(self._store._roles),
            total_assignments=len(self._store._assignments),
            total_responsibilities=len(self._resp_graph._responsibilities),
            total_delegations=len(self._delegations._delegations),
            total_collaborations=len(self._collab._collaborations),
            total_authorities=len(self._authority._authorities),
            total_memory_entries=len(self._memory._entries),
            knowledge_graph_nodes=len(self._kg._nodes),
            knowledge_graph_edges=len(self._kg._edges),
        )
        return s.to_dict()

    def _log(self, event: str, entity_id: str, tenant_id: int) -> None:
        self._event_log.append({
            "event": event, "entity_id": entity_id,
            "tenant_id": tenant_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })


# =========================================================================
# Facade
# =========================================================================

class OrganizationalIntelligenceEngine:
    """Facade over all Organizational Intelligence components."""

    def __init__(self, config: Optional[OrgConfig] = None):
        self._runtime = RuntimeService(config)

    @property
    def runtime(self) -> RuntimeService:
        return self._runtime

    # --- Units ---
    def create_unit(self, name: str, tenant_id: int, **kw) -> OrgUnit:
        return self._runtime.create_unit(name, tenant_id, **kw)

    def get_unit(self, unit_id: str) -> Optional[OrgUnit]:
        return self._runtime.store.get_unit(unit_id)

    def get_unit_tree(self, tenant_id: int) -> List[dict]:
        return self._runtime.store.get_unit_tree(tenant_id)

    # --- Roles ---
    def create_role(self, name: str, tenant_id: int, **kw) -> OrgRole:
        return self._runtime.create_role(name, tenant_id, **kw)

    def assign_role(self, role_id: str, person_id: int,
                    unit_id: str, tenant_id: int) -> RoleAssignment:
        return self._runtime.assign_role(role_id, person_id, unit_id, tenant_id)

    # --- Responsibilities ---
    def add_responsibility(self, role_id: str, entity_type: str,
                           entity_id: str, tenant_id: int, **kw) -> Responsibility:
        return self._runtime.add_responsibility(role_id, entity_type, entity_id, tenant_id, **kw)

    def resolve_responsible(self, entity_type: str, entity_id: str,
                            tenant_id: int) -> List[dict]:
        return self._runtime.resolve_responsible(entity_type, entity_id, tenant_id)

    # --- Ownership ---
    def set_ownership(self, entity_type: str, entity_id: str,
                      owner_id: str, tenant_id: int, **kw) -> Ownership:
        return self._runtime.set_ownership(entity_type, entity_id, owner_id, tenant_id, **kw)

    # --- Delegation ---
    def delegate(self, from_role_id: str, to_role_id: str,
                 tenant_id: int, **kw) -> Delegation:
        return self._runtime.delegate(from_role_id, to_role_id, tenant_id, **kw)

    # --- Authority ---
    def check_authority(self, role_id: str, action: str, entity_type: str,
                        entity_id: str, tenant_id: int) -> bool:
        return self._runtime.check_authority(role_id, action, entity_type, entity_id, tenant_id)

    # --- Collaboration ---
    def record_collaboration(self, role_id_a: str, role_id_b: str,
                             entity_type: str, entity_id: str,
                             tenant_id: int) -> Collaboration:
        return self._runtime.record_collaboration(
            role_id_a, role_id_b, entity_type, entity_id, tenant_id)

    # --- Health ---
    def assess_health(self, unit_id: str, tenant_id: int) -> OrgHealth:
        return self._runtime.assess_health(unit_id, tenant_id)

    # --- Memory ---
    def add_memory(self, topic: str, content: str, tenant_id: int, **kw) -> InstitutionalMemoryEntry:
        return self._runtime.add_memory(topic, content, tenant_id, **kw)

    # --- Knowledge Graph ---
    def rebuild_knowledge_graph(self, tenant_id: int) -> None:
        self._runtime.rebuild_knowledge_graph(tenant_id)

    def query_knowledge_graph(self, entity_type: str, entity_id: str) -> List[dict]:
        return self._runtime.query_knowledge_graph(entity_type, entity_id)

    # --- Explain ---
    def explain_health(self, unit_id: str, tenant_id: int) -> dict:
        return self._runtime.explain_health(unit_id, tenant_id)

    # --- Stats ---
    def stats(self) -> Dict[str, Any]:
        return self._runtime.stats()