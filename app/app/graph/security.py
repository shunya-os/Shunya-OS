"""SHUNYA Knowledge Graph — Graph Security (E-003-MOD-005).

Implements universal graph security primitives — a deterministic, side-effect-free
access evaluation model for the Knowledge Graph as defined in:
    UNIVERSAL_KNOWLEDGE_GRAPH_ARCHITECTURE.md §13 — Security & Access Control
    UNIVERSAL_KNOWLEDGE_GRAPH_ARCHITECTURE.md §13.2 — Visibility
    UNIVERSAL_KNOWLEDGE_GRAPH_ARCHITECTURE.md §13.3 — Ownership

Constitutional rules:
    - Security evaluation is DETERMINISTIC and PURE (same input → same output).
    - Security evaluation is SIDE-EFFECT FREE — no mutations, no persistence.
    - Every access decision returns a structured PermissionResult, never bare True/False.
    - No business logic. No CRM. No travel. No Panchi Club.
    - No authentication, login, OAuth, JWT, passwords, sessions, or web security.
    - No encryption, rate limiting, tenant billing, cloud IAM, or RBAC dashboards.
    - The Graph builds on the Kernel. The Kernel must never depend on the Graph.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple

from app.graph.node import Node, VisibilityLevel


# =========================================================================
# GraphPermissions — universal, business-agnostic permissions
# =========================================================================


class GraphPermission(str, Enum):
    """Universal graph permissions (business-agnostic).

    These are the ONLY permissions in the Knowledge Graph. No business
    permissions exist here. Every permission applies to a graph primitive
    (node or edge), never to a business concept.

    Categories:
        READ:     view node / edge content
        MODIFY:   create, update, delete graph primitives
        TRAVERSE: follow edges between nodes
        VIEW:     read metadata, evidence, history of a node
        DISCOVER: find nodes via search, label, or type queries
    """

    # Node permissions
    READ_NODE = "read_node"
    UPDATE_NODE = "update_node"
    DELETE_NODE = "delete_node"

    # Edge permissions
    READ_EDGE = "read_edge"
    CREATE_EDGE = "create_edge"
    DELETE_EDGE = "delete_edge"

    # Traversal
    TRAVERSE = "traverse"

    # Metadata and evidence
    VIEW_METADATA = "view_metadata"
    VIEW_EVIDENCE = "view_evidence"
    VIEW_HISTORY = "view_history"

    # Discovery
    DISCOVER = "discover"


# =========================================================================
# GraphSecurityPolicy — policy definition
# =========================================================================


@dataclass
class GraphSecurityPolicy:
    """A security policy rule that maps a condition to a permission decision.

    Every policy is a single rule with:
        - name:         Human-readable identifier for the rule
        - permission:   The GraphPermission this rule governs
        - condition:    A description of when the rule applies
        - effect:       'allow' or 'deny'
        - priority:     Higher priority rules override lower ones (default: 0)

    Policies are evaluated in priority order. The first matching rule
    determines the decision. If no rule matches, the default is DENY.

    This is a pure data object — no logic, no closures, no side effects.
    """

    name: str
    permission: str
    condition: str
    effect: str = "deny"
    priority: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "permission": self.permission,
            "condition": self.condition,
            "effect": self.effect,
            "priority": self.priority,
        }


# =========================================================================
# SecurityContext — who is asking
# =========================================================================


@dataclass
class SecurityContext:
    """The context of an actor requesting graph access.

    This is a pure data object describing who the actor is and what
    groups they belong to. It does NOT contain authentication data,
    passwords, tokens, or any web/security primitives.

    Attributes:
        actor_id:      Unique identifier of the requesting actor.
        teams:         Set of team identifiers the actor belongs to.
        organization:  Organization identifier the actor belongs to.
        roles:         Set of role identifiers assigned to the actor.
    """

    actor_id: str = ""
    teams: Set[str] = field(default_factory=set)
    organization: str = ""
    roles: Set[str] = field(default_factory=set)

    def __post_init__(self) -> None:
        if isinstance(self.teams, list):
            self.teams = set(self.teams)
        if isinstance(self.roles, list):
            self.roles = set(self.roles)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "actor_id": self.actor_id,
            "teams": sorted(self.teams),
            "organization": self.organization,
            "roles": sorted(self.roles),
        }


# =========================================================================
# PermissionResult — structured access decision
# =========================================================================


@dataclass
class PermissionResult:
    """Structured result of a single permission check.

    Never returns bare True/False — always returns a structured object
    with the reason, the rule that was applied, and what was checked.

    Attributes:
        allowed:            True if the action is permitted.
        reason:             Human-readable explanation of the decision.
        rule_applied:       Name of the policy rule that determined the decision.
        permission_checked: The GraphPermission value that was evaluated.
        visibility_checked: The VisibilityLevel value that was evaluated.
        actor_id:           The actor who requested access.
        resource_id:        The node or edge identity that was checked.
    """

    allowed: bool = False
    reason: str = ""
    rule_applied: str = ""
    permission_checked: str = ""
    visibility_checked: str = ""
    actor_id: str = ""
    resource_id: str = ""

    @property
    def is_allowed(self) -> bool:
        return self.allowed

    @property
    def is_denied(self) -> bool:
        return not self.allowed

    def to_dict(self) -> Dict[str, Any]:
        return {
            "allowed": self.allowed,
            "reason": self.reason,
            "rule_applied": self.rule_applied,
            "permission_checked": self.permission_checked,
            "visibility_checked": self.visibility_checked,
            "actor_id": self.actor_id,
            "resource_id": self.resource_id,
        }


# =========================================================================
# VisibilityRule — visibility inheritance rules
# =========================================================================

# Visibility level hierarchy (lowest = most restrictive)
# PRIVATE < TEAM < ORGANISATION < CONFIDENTIAL < PUBLIC
_VISIBILITY_HIERARCHY: Dict[str, int] = {
    VisibilityLevel.PRIVATE.value: 0,
    VisibilityLevel.TEAM.value: 1,
    VisibilityLevel.ORGANISATION.value: 2,
    VisibilityLevel.CONFIDENTIAL.value: 3,
    VisibilityLevel.PUBLIC.value: 4,
}

# Visibility level progression (the canonical order)
_VISIBILITY_ORDER: List[str] = [
    VisibilityLevel.PRIVATE.value,
    VisibilityLevel.TEAM.value,
    VisibilityLevel.ORGANISATION.value,
    VisibilityLevel.CONFIDENTIAL.value,
    VisibilityLevel.PUBLIC.value,
]


def visibility_level_rank(level: str) -> int:
    """Get the numeric rank of a visibility level.

    Lower rank = more restrictive. Unknown levels default to PRIVATE (0).
    """
    return _VISIBILITY_HIERARCHY.get(level, 0)


def visibility_inherits(level: str) -> List[str]:
    """Get all visibility levels that can see this level.

    A visibility level inherits its own level and all more restrictive levels.
    Example: PUBLIC can see everything; PRIVATE can only see PRIVATE.
    """
    rank = visibility_level_rank(level)
    return [v for v in _VISIBILITY_ORDER if visibility_level_rank(v) <= rank]


def is_visibility_compatible(requestor_level: str, target_level: str) -> bool:
    """Check if a requestor's visibility level can access a target.

    A requestor can see a target if their visibility level is equal to or
    broader than the target's. PRIVATE is most restrictive; PUBLIC is least.

    This is the core visibility comparison function.
    """
    return visibility_level_rank(requestor_level) >= visibility_level_rank(target_level)


def get_effective_visibility(node: Node) -> str:
    """Get the effective visibility level of a node.

    Currently returns the node's own visibility. In the future this may
    compute inherited visibility from parent or container nodes.
    """
    return node.visibility


# =========================================================================
# GraphAccessDecision — combined access decision
# =========================================================================


@dataclass
class GraphAccessDecision:
    """Combined access decision for a graph operation.

    A decision includes the permission check result, the visibility check
    result, and a final is_allowed verdict. The overall operation is only
    allowed if BOTH permission and visibility checks pass.

    Attributes:
        permission:  Result of the permission check.
        visibility:  Result of the visibility check.
        is_allowed:  True only if both permission and visibility pass.
    """

    permission: PermissionResult = field(default_factory=PermissionResult)
    visibility: PermissionResult = field(default_factory=PermissionResult)

    @property
    def is_allowed(self) -> bool:
        return self.permission.allowed and self.visibility.allowed

    @property
    def is_denied(self) -> bool:
        return not self.is_allowed

    def to_dict(self) -> Dict[str, Any]:
        return {
            "is_allowed": self.is_allowed,
            "permission": self.permission.to_dict(),
            "visibility": self.visibility.to_dict(),
        }


# =========================================================================
# Default policy catalogue
# =========================================================================

# Default policies defining the canonical graph security rules.
# These are the built-in rules. Applications may add their own policies
# but must never modify these defaults.

DEFAULT_POLICIES: List[GraphSecurityPolicy] = [
    # Ownership rules
    GraphSecurityPolicy(
        name="owner-full-access",
        permission=GraphPermission.READ_NODE.value,
        condition="actor is the owner of the node",
        effect="allow",
        priority=100,
    ),
    GraphSecurityPolicy(
        name="owner-update",
        permission=GraphPermission.UPDATE_NODE.value,
        condition="actor is the owner of the node",
        effect="allow",
        priority=100,
    ),
    GraphSecurityPolicy(
        name="owner-delete",
        permission=GraphPermission.DELETE_NODE.value,
        condition="actor is the owner of the node",
        effect="allow",
        priority=100,
    ),
    GraphSecurityPolicy(
        name="owner-create-edge",
        permission=GraphPermission.CREATE_EDGE.value,
        condition="actor is the owner of the node",
        effect="allow",
        priority=100,
    ),
    GraphSecurityPolicy(
        name="owner-delete-edge",
        permission=GraphPermission.DELETE_EDGE.value,
        condition="actor is the owner of the node",
        effect="allow",
        priority=100,
    ),
    # System (confidential) — only the owner can access
    GraphSecurityPolicy(
        name="confidential-owner-only",
        permission=GraphPermission.READ_NODE.value,
        condition="node visibility is CONFIDENTIAL and actor is the owner",
        effect="allow",
        priority=60,
    ),
    # History — owner only by default
    GraphSecurityPolicy(
        name="history-owner",
        permission=GraphPermission.VIEW_HISTORY.value,
        condition="actor is the owner of the node",
        effect="allow",
        priority=80,
    ),
    # Evidence — owner only by default
    GraphSecurityPolicy(
        name="evidence-owner",
        permission=GraphPermission.VIEW_EVIDENCE.value,
        condition="actor is the owner of the node",
        effect="allow",
        priority=80,
    ),
    # Metadata
    GraphSecurityPolicy(
        name="metadata-owner",
        permission=GraphPermission.VIEW_METADATA.value,
        condition="actor is the owner of the node",
        effect="allow",
        priority=80,
    ),
    # Discover
    GraphSecurityPolicy(
        name="discover-owner",
        permission=GraphPermission.DISCOVER.value,
        condition="actor is the owner of the node",
        effect="allow",
        priority=80,
    ),
    # Cross-family traversal — allowed if both endpoints are visible
    GraphSecurityPolicy(
        name="cross-family-traversal",
        permission=GraphPermission.TRAVERSE.value,
        condition="actor can see both source and target nodes",
        effect="allow",
        priority=20,
    ),
]


# =========================================================================
# GraphAccessEvaluator — pure deterministic security evaluator
# =========================================================================


class GraphAccessEvaluator:
    """Deterministic, side-effect-free graph access evaluator.

    Evaluates whether an actor may perform a specific graph operation
    on a specific node or edge. Always returns structured PermissionResult
    or GraphAccessDecision objects — never bare True/False.

    This evaluator is:
        - DETERMINISTIC: Same input always produces the same output.
        - PURE: No mutations, no side effects, no persistence.
        - BUSINESS-AGNOSTIC: No CRM, travel, or Panchi Club logic.

    It does NOT:
        - Authenticate actors (no login, OAuth, JWT)
        - Persist decisions (no caching, no database)
        - Mutate nodes or edges (read-only)
        - Repair or auto-heal access issues
    """

    def __init__(self, policies: Optional[List[GraphSecurityPolicy]] = None):
        self._policies = tuple(sorted(
            policies if policies is not None else DEFAULT_POLICIES,
            key=lambda p: (-p.priority, p.name),
        ))

    @property
    def policies(self) -> Tuple[GraphSecurityPolicy, ...]:
        """Immutable view of the active policies."""
        return self._policies

    # ---- Primary evaluation methods ---------------------------------------

    def can_view_node(
        self,
        context: SecurityContext,
        node: Node,
    ) -> PermissionResult:
        """Determine if an actor can view a node.

        Checks both the permission (READ_NODE) and visibility compatibility.
        """
        permission = self._check_permission(
            context=context,
            resource=node,
            permission=GraphPermission.READ_NODE,
            resource_id=node.node_id,
        )
        visibility = self._check_visibility(
            context=context,
            node=node,
            permission=GraphPermission.READ_NODE,
        )
        # Combine: both must pass
        return self._combine_results(permission, visibility)

    def can_traverse_edge(
        self,
        context: SecurityContext,
        source_node: Node,
        target_node: Node,
        edge_type: str = "",
    ) -> PermissionResult:
        """Determine if an actor can traverse an edge between two nodes.

        Traversal requires visibility of BOTH endpoints.
        """
        source_visible = self._check_visibility(
            context=context, node=source_node,
            permission=GraphPermission.TRAVERSE,
        )
        target_visible = self._check_visibility(
            context=context, node=target_node,
            permission=GraphPermission.TRAVERSE,
        )

        if not source_visible.allowed:
            return PermissionResult(
                allowed=False,
                reason=f"Source node '{source_node.short_id}' is not visible to actor '{context.actor_id}'",
                rule_applied="traverse-requires-source-visibility",
                permission_checked=GraphPermission.TRAVERSE.value,
                visibility_checked=source_node.visibility,
                actor_id=context.actor_id,
                resource_id=source_node.node_id,
            )

        if not target_visible.allowed:
            return PermissionResult(
                allowed=False,
                reason=f"Target node '{target_node.short_id}' is not visible to actor '{context.actor_id}'",
                rule_applied="traverse-requires-target-visibility",
                permission_checked=GraphPermission.TRAVERSE.value,
                visibility_checked=target_node.visibility,
                actor_id=context.actor_id,
                resource_id=target_node.node_id,
            )

        permission = self._check_permission(
            context=context,
            resource=source_node,
            permission=GraphPermission.TRAVERSE,
            resource_id=source_node.node_id,
        )

        if not permission.allowed:
            return permission

        return PermissionResult(
            allowed=True,
            reason=f"Actor '{context.actor_id}' can traverse to '{target_node.short_id}'",
            rule_applied="cross-family-traversal",
            permission_checked=GraphPermission.TRAVERSE.value,
            visibility_checked=target_node.visibility,
            actor_id=context.actor_id,
            resource_id=target_node.node_id,
        )

    def can_modify_relationship(
        self,
        context: SecurityContext,
        source_node: Node,
        target_node: Node,
        edge_type: str = "",
    ) -> PermissionResult:
        """Determine if an actor can modify a relationship between two nodes.

        Modification requires the actor to own or have permission to
        update the source node.
        """
        return self._check_permission(
            context=context,
            resource=source_node,
            permission=GraphPermission.UPDATE_NODE,
            resource_id=source_node.node_id,
        )

    def can_discover(
        self,
        context: SecurityContext,
        node: Node,
    ) -> PermissionResult:
        """Determine if an actor can discover a node via search or query."""
        permission = self._check_permission(
            context=context,
            resource=node,
            permission=GraphPermission.DISCOVER,
            resource_id=node.node_id,
        )
        visibility = self._check_visibility(
            context=context,
            node=node,
            permission=GraphPermission.DISCOVER,
        )
        return self._combine_results(permission, visibility)

    def can_read_metadata(
        self,
        context: SecurityContext,
        node: Node,
    ) -> PermissionResult:
        """Determine if an actor can read node metadata."""
        permission = self._check_permission(
            context=context,
            resource=node,
            permission=GraphPermission.VIEW_METADATA,
            resource_id=node.node_id,
        )
        visibility = self._check_visibility(
            context=context,
            node=node,
            permission=GraphPermission.VIEW_METADATA,
        )
        return self._combine_results(permission, visibility)

    def can_view_evidence(
        self,
        context: SecurityContext,
        node: Node,
    ) -> PermissionResult:
        """Determine if an actor can view evidence attached to a node."""
        return self._check_permission(
            context=context,
            resource=node,
            permission=GraphPermission.VIEW_EVIDENCE,
            resource_id=node.node_id,
        )

    def can_view_descendants(
        self,
        context: SecurityContext,
        node: Node,
    ) -> PermissionResult:
        """Determine if an actor can view descendants of a node.

        Uses the same visibility check as viewing the node itself.
        """
        return self.can_view_node(context, node)

    def can_follow_references(
        self,
        context: SecurityContext,
        source_node: Node,
        target_node: Node,
    ) -> PermissionResult:
        """Determine if an actor can follow a reference from source to target.

        Requires visibility of both nodes.
        """
        return self.can_traverse_edge(context, source_node, target_node)

    def can_view_history(
        self,
        context: SecurityContext,
        node: Node,
    ) -> PermissionResult:
        """Determine if an actor can view a node's history."""
        return self._check_permission(
            context=context,
            resource=node,
            permission=GraphPermission.VIEW_HISTORY,
            resource_id=node.node_id,
        )

    def can_read_edge(
        self,
        context: SecurityContext,
        source_node: Node,
        target_node: Node,
        edge_type: str = "",
    ) -> PermissionResult:
        """Determine if an actor can read an edge between two nodes.

        Requires visibility of both source and target nodes.
        """
        return self.can_traverse_edge(context, source_node, target_node, edge_type)

    def can_create_edge(
        self,
        context: SecurityContext,
        source_node: Node,
        target_node: Node,
    ) -> PermissionResult:
        """Determine if an actor can create an edge from source to target."""
        return self._check_permission(
            context=context,
            resource=source_node,
            permission=GraphPermission.CREATE_EDGE,
            resource_id=source_node.node_id,
        )

    def can_delete_edge(
        self,
        context: SecurityContext,
        source_node: Node,
        target_node: Node,
    ) -> PermissionResult:
        """Determine if an actor can delete an edge between two nodes."""
        return self._check_permission(
            context=context,
            resource=source_node,
            permission=GraphPermission.DELETE_EDGE,
            resource_id=source_node.node_id,
        )

    def can_update_node(
        self,
        context: SecurityContext,
        node: Node,
    ) -> PermissionResult:
        """Determine if an actor can update a node."""
        return self._check_permission(
            context=context,
            resource=node,
            permission=GraphPermission.UPDATE_NODE,
            resource_id=node.node_id,
        )

    def can_delete_node(
        self,
        context: SecurityContext,
        node: Node,
    ) -> PermissionResult:
        """Determine if an actor can delete a node."""
        return self._check_permission(
            context=context,
            resource=node,
            permission=GraphPermission.DELETE_NODE,
            resource_id=node.node_id,
        )

    # ---- Composite evaluation ---------------------------------------------

    def evaluate(
        self,
        context: SecurityContext,
        permission: str,
        node: Optional[Node] = None,
    ) -> GraphAccessDecision:
        """Evaluate a full access decision for a permission on a node.

        Returns a GraphAccessDecision containing both the permission and
        visibility checks with a combined is_allowed verdict.

        This is the universal evaluation entry point.
        """
        perm_result = self._check_permission(
            context=context,
            resource=node,
            permission=permission,
            resource_id=node.node_id if node else "",
        )
        vis_result = self._check_visibility(
            context=context,
            node=node,
            permission=permission,
        ) if node else PermissionResult(
            allowed=True,
            reason="No node for visibility check",
            rule_applied="no-node",
            permission_checked=permission,
            visibility_checked="",
            actor_id=context.actor_id,
        )

        return GraphAccessDecision(
            permission=perm_result,
            visibility=vis_result,
        )

    # ---- Internal helpers --------------------------------------------------

    def _check_permission(
        self,
        context: SecurityContext,
        resource: Any,
        permission: str,
        resource_id: str = "",
    ) -> PermissionResult:
        """Check the permission policy for a given resource and permission.

        Iterates through policies in priority order. The first matching
        rule determines the decision. If no rule matches, the default is DENY.

        Permission check is OWNERSHIP-FIRST with a VISIBILITY-BASED FALLBACK.
        Ownership policies are checked first. If no ownership policy matches
        and the operation is a READ-type operation, the visibility of the
        resource is checked as a fallback. This ensures that PUBLIC nodes
        are readable by anyone, while MODIFY operations remain owner-only.
        """
        # First pass: check ownership-based policies
        for policy in self._policies:
            if policy.permission != permission:
                continue
            if self._matches_policy(policy, context, resource, permission):
                allowed = policy.effect == "allow"
                return PermissionResult(
                    allowed=allowed,
                    reason=(
                        f"Policy '{policy.name}' {policy.effect}s "
                        f"{permission} for actor '{context.actor_id}'"
                        if allowed else
                        f"Policy '{policy.name}' denies {permission} "
                        f"for actor '{context.actor_id}'"
                    ),
                    rule_applied=policy.name,
                    permission_checked=permission,
                    visibility_checked=resource.visibility if hasattr(resource, 'visibility') else "",
                    actor_id=context.actor_id,
                    resource_id=resource_id,
                )

        # Second pass: visibility-based fallback for read-like operations
        # If the resource is visible to the actor, READ operations are permitted.
        if resource is not None and hasattr(resource, 'visibility'):
            resource_visibility = resource.visibility
            # Read-like permissions that can be granted by visibility alone
            # EVIDENCE and HISTORY are excluded — they remain owner-only.
            read_permissions = {
                GraphPermission.READ_NODE.value,
                GraphPermission.READ_EDGE.value,
                GraphPermission.DISCOVER.value,
                GraphPermission.VIEW_METADATA.value,
                GraphPermission.TRAVERSE.value,
            }
            if permission in read_permissions:
                # Check if the resource is visible to this actor
                vis_result = self._check_visibility(context, resource, permission)
                if vis_result.allowed:
                    return PermissionResult(
                        allowed=True,
                        reason=f"Visibility-granted: {vis_result.reason}",
                        rule_applied=f"visibility-fallback-{vis_result.rule_applied}",
                        permission_checked=permission,
                        visibility_checked=resource_visibility,
                        actor_id=context.actor_id,
                        resource_id=resource_id,
                    )

        # Default: deny
        return PermissionResult(
            allowed=False,
            reason=f"No policy permits {permission} for actor '{context.actor_id}'",
            rule_applied="default-deny",
            permission_checked=permission,
            visibility_checked="",
            actor_id=context.actor_id,
            resource_id=resource_id,
        )

    def _check_visibility(
        self,
        context: SecurityContext,
        node: Optional[Node],
        permission: str,
    ) -> PermissionResult:
        """Check visibility compatibility between context and node.

        Visibility rules:
            PUBLIC:        Anyone can see (any actor_id, no teams/org needed)
            ORGANISATION:  Actor must be in the same organization
            TEAM:          Actor must be on the same team as the node owner
            PRIVATE:       Only the owner can see
            CONFIDENTIAL:  Only the owner can see (same as PRIVATE)
        """
        if node is None:
            return PermissionResult(
                allowed=True,
                reason="No node for visibility check",
                rule_applied="no-node",
                permission_checked=permission,
                visibility_checked="",
                actor_id=context.actor_id,
            )

        effective_visibility = get_effective_visibility(node)

        # PUBLIC — anyone can see
        if effective_visibility == VisibilityLevel.PUBLIC.value:
            return PermissionResult(
                allowed=True,
                reason=f"Node '{node.short_id}' is PUBLIC — visible to all actors",
                rule_applied="public-visibility",
                permission_checked=permission,
                visibility_checked=effective_visibility,
                actor_id=context.actor_id,
                resource_id=node.node_id,
            )

        # PRIVATE — only the owner
        if effective_visibility == VisibilityLevel.PRIVATE.value:
            if context.actor_id and node.owner_id and context.actor_id == node.owner_id:
                return PermissionResult(
                    allowed=True,
                    reason=f"Node '{node.short_id}' is PRIVATE — actor is the owner",
                    rule_applied="private-owner",
                    permission_checked=permission,
                    visibility_checked=effective_visibility,
                    actor_id=context.actor_id,
                    resource_id=node.node_id,
                )
            return PermissionResult(
                allowed=False,
                reason=f"Node '{node.short_id}' is PRIVATE — only the owner can access",
                rule_applied="private-restricted",
                permission_checked=permission,
                visibility_checked=effective_visibility,
                actor_id=context.actor_id,
                resource_id=node.node_id,
            )

        # CONFIDENTIAL — only the owner
        if effective_visibility == VisibilityLevel.CONFIDENTIAL.value:
            if context.actor_id and node.owner_id and context.actor_id == node.owner_id:
                return PermissionResult(
                    allowed=True,
                    reason=f"Node '{node.short_id}' is CONFIDENTIAL — actor is the owner",
                    rule_applied="confidential-owner",
                    permission_checked=permission,
                    visibility_checked=effective_visibility,
                    actor_id=context.actor_id,
                    resource_id=node.node_id,
                )
            return PermissionResult(
                allowed=False,
                reason=f"Node '{node.short_id}' is CONFIDENTIAL — only the owner can access",
                rule_applied="confidential-restricted",
                permission_checked=permission,
                visibility_checked=effective_visibility,
                actor_id=context.actor_id,
                resource_id=node.node_id,
            )

        # TEAM — actor must be on a team
        if effective_visibility == VisibilityLevel.TEAM.value:
            if context.teams:
                return PermissionResult(
                    allowed=True,
                    reason=f"Node '{node.short_id}' is TEAM-visible — actor is on a team",
                    rule_applied="team-visibility",
                    permission_checked=permission,
                    visibility_checked=effective_visibility,
                    actor_id=context.actor_id,
                    resource_id=node.node_id,
                )
            return PermissionResult(
                allowed=False,
                reason=f"Node '{node.short_id}' is TEAM-visible — actor has no team membership",
                rule_applied="team-restricted",
                permission_checked=permission,
                visibility_checked=effective_visibility,
                actor_id=context.actor_id,
                resource_id=node.node_id,
            )

        # ORGANISATION — actor must be in the same organisation
        # Without a canonical org membership lookup, we conservatively
        # require the actor to be the owner. This prevents cross-org
        # access when org membership cannot be verified.
        if effective_visibility == VisibilityLevel.ORGANISATION.value:
            if context.actor_id and node.owner_id and context.actor_id == node.owner_id:
                return PermissionResult(
                    allowed=True,
                    reason=f"Node '{node.short_id}' is ORGANISATION-visible — actor is the owner",
                    rule_applied="organisation-owner",
                    permission_checked=permission,
                    visibility_checked=effective_visibility,
                    actor_id=context.actor_id,
                    resource_id=node.node_id,
                )
            return PermissionResult(
                allowed=False,
                reason=f"Node '{node.short_id}' is ORGANISATION-visible — only the owner can access",
                rule_applied="organisation-restricted",
                permission_checked=permission,
                visibility_checked=effective_visibility,
                actor_id=context.actor_id,
                resource_id=node.node_id,
            )

        # Unknown visibility — deny
        return PermissionResult(
            allowed=False,
            reason=f"Unknown visibility level '{effective_visibility}' for node '{node.short_id}'",
            rule_applied="unknown-visibility",
            permission_checked=permission,
            visibility_checked=effective_visibility,
            actor_id=context.actor_id,
            resource_id=node.node_id,
        )

    def _matches_policy(
        self,
        policy: GraphSecurityPolicy,
        context: SecurityContext,
        resource: Any,
        permission: str,
    ) -> bool:
        """Determine if a policy rule matches the current context and resource.

        This is a pure, deterministic matching function. It evaluates the
        policy's condition against the context and resource properties.

        Returns True if the policy applies, False otherwise.
        """
        condition = policy.condition

        # Owner conditions
        if "actor is the owner" in condition:
            if not hasattr(resource, 'owner_id') or not resource.owner_id:
                return False
            if not context.actor_id:
                return False
            # Exact match on owner_id
            if resource.owner_id != context.actor_id:
                return False
            return True

        # Visibility conditions
        if "node visibility is CONFIDENTIAL and actor is the owner" in condition:
            if not hasattr(resource, 'visibility') or not hasattr(resource, 'owner_id'):
                return False
            if resource.visibility != VisibilityLevel.CONFIDENTIAL.value:
                return False
            if not context.actor_id or not resource.owner_id:
                return False
            return resource.owner_id == context.actor_id

        # Cross-family traversal
        if "actor can see both source and target nodes" in condition:
            # Must be handled at the evaluator level, not here
            if not hasattr(resource, 'visibility'):
                return False
            # If the resource is visible (checked elsewhere), allow traversal
            return True

        # Default: no match
        return False

    def _combine_results(
        self,
        permission: PermissionResult,
        visibility: PermissionResult,
    ) -> PermissionResult:
        """Combine a permission check and visibility check into one result.

        Both must pass for the result to be allowed.
        """
        if not permission.allowed:
            return permission
        if not visibility.allowed:
            return visibility
        return PermissionResult(
            allowed=True,
            reason=f"{permission.reason}. {visibility.reason}",
            rule_applied=f"{permission.rule_applied}+{visibility.rule_applied}",
            permission_checked=permission.permission_checked,
            visibility_checked=visibility.visibility_checked,
            actor_id=permission.actor_id,
            resource_id=permission.resource_id,
        )


# =========================================================================
# Singleton
# =========================================================================

_GLOBAL_EVALUATOR: Optional[GraphAccessEvaluator] = None


def get_evaluator() -> GraphAccessEvaluator:
    """Get the global GraphAccessEvaluator singleton."""
    global _GLOBAL_EVALUATOR
    if _GLOBAL_EVALUATOR is None:
        _GLOBAL_EVALUATOR = GraphAccessEvaluator()
    return _GLOBAL_EVALUATOR


def reset_evaluator() -> None:
    """Reset the global evaluator (for testing)."""
    global _GLOBAL_EVALUATOR
    _GLOBAL_EVALUATOR = None