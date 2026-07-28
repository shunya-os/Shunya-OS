"""Tests for SHUNYA Knowledge Graph — Graph Security (E-003-MOD-005).

Architecture references:
    UNIVERSAL_KNOWLEDGE_GRAPH_ARCHITECTURE.md §13 — Security & Access Control
    UNIVERSAL_KNOWLEDGE_GRAPH_ARCHITECTURE.md §13.2 — Visibility
    UNIVERSAL_KNOWLEDGE_GRAPH_ARCHITECTURE.md §13.3 — Ownership

Constitutional invariants tested:
    Security evaluation is DETERMINISTIC and PURE (same input → same output)
    Security evaluation is SIDE-EFFECT FREE (no mutations, no persistence)
    Every access decision returns a structured PermissionResult (never bare True/False)
    No business logic introduced
"""

import pytest
from app.graph.node import (
    Node, VisibilityLevel, get_node_store, reset_node_store,
)
from app.graph.security import (
    GraphPermission, GraphSecurityPolicy, SecurityContext,
    PermissionResult, GraphAccessDecision, GraphAccessEvaluator,
    get_evaluator, reset_evaluator,
    visibility_level_rank, visibility_inherits, is_visibility_compatible,
    get_effective_visibility, DEFAULT_POLICIES,
)


# =========================================================================
# Fixtures
# =========================================================================


@pytest.fixture(autouse=True)
def reset_stores():
    reset_node_store()
    reset_evaluator()
    yield


@pytest.fixture
def evaluator():
    return GraphAccessEvaluator()


@pytest.fixture
def owner_context():
    return SecurityContext(
        actor_id="user_1",
        teams={"engineering", "platform"},
        organization="shunya",
    )


@pytest.fixture
def other_context():
    return SecurityContext(
        actor_id="user_2",
        teams={"design"},
        organization="shunya",
    )


@pytest.fixture
def stranger_context():
    return SecurityContext(
        actor_id="user_3",
        teams=set(),
        organization="other_corp",
    )


@pytest.fixture
def teamless_context():
    return SecurityContext(
        actor_id="user_4",
        teams=set(),
        organization="",
    )


@pytest.fixture
def private_node():
    return Node(
        node_type="Document",
        owner_id="user_1",
        visibility=VisibilityLevel.PRIVATE.value,
    )


@pytest.fixture
def public_node():
    return Node(
        node_type="Document",
        owner_id="user_1",
        visibility=VisibilityLevel.PUBLIC.value,
    )


@pytest.fixture
def team_node():
    return Node(
        node_type="Document",
        owner_id="user_1",
        visibility=VisibilityLevel.TEAM.value,
    )


@pytest.fixture
def org_node():
    return Node(
        node_type="Document",
        owner_id="user_1",
        visibility=VisibilityLevel.ORGANISATION.value,
    )


@pytest.fixture
def confidential_node():
    return Node(
        node_type="SystemConfig",
        owner_id="user_1",
        visibility=VisibilityLevel.CONFIDENTIAL.value,
    )


# =========================================================================
# PermissionResult Tests
# =========================================================================


class TestPermissionResult:
    """UNIVERSAL_KNOWLEDGE_GRAPH_ARCHITECTURE.md §13 — PermissionResult structure."""

    def test_default_denied(self):
        """PermissionResult defaults to denied."""
        result = PermissionResult()
        assert not result.allowed
        assert result.is_denied
        assert not result.is_allowed

    def test_allowed_property(self):
        """is_allowed reflects the allowed field."""
        result = PermissionResult(allowed=True)
        assert result.is_allowed
        assert not result.is_denied

    def test_to_dict_structure(self):
        """to_dict() returns all fields."""
        result = PermissionResult(
            allowed=True,
            reason="Owner can read",
            rule_applied="owner-full-access",
            permission_checked="read_node",
            visibility_checked="private",
            actor_id="user_1",
            resource_id="n_abc123",
        )
        d = result.to_dict()
        assert d["allowed"] is True
        assert d["reason"] == "Owner can read"
        assert d["rule_applied"] == "owner-full-access"
        assert d["permission_checked"] == "read_node"
        assert d["visibility_checked"] == "private"
        assert d["actor_id"] == "user_1"
        assert d["resource_id"] == "n_abc123"

    def test_denied_to_dict(self):
        """Denied result serializes correctly."""
        result = PermissionResult(
            allowed=False,
            reason="Private node",
            rule_applied="private-restricted",
            permission_checked="read_node",
            visibility_checked="private",
            actor_id="user_2",
            resource_id="n_xyz",
        )
        d = result.to_dict()
        assert d["allowed"] is False
        assert d["rule_applied"] == "private-restricted"


# =========================================================================
# SecurityContext Tests
# =========================================================================


class TestSecurityContext:
    """UNIVERSAL_KNOWLEDGE_GRAPH_ARCHITECTURE.md §13 — SecurityContext."""

    def test_default_context(self):
        """SecurityContext defaults are empty."""
        ctx = SecurityContext()
        assert ctx.actor_id == ""
        assert ctx.teams == set()
        assert ctx.organization == ""
        assert ctx.roles == set()

    def test_list_to_set_conversion(self):
        """Lists are converted to sets on init."""
        ctx = SecurityContext(actor_id="u1", teams=["a", "b"], roles=["admin"])
        assert ctx.teams == {"a", "b"}
        assert ctx.roles == {"admin"}

    def test_to_dict(self):
        """to_dict() returns sorted sets."""
        ctx = SecurityContext(
            actor_id="user_1",
            teams={"b", "a"},
            organization="shunya",
            roles={"admin", "user"},
        )
        d = ctx.to_dict()
        assert d["actor_id"] == "user_1"
        assert d["teams"] == ["a", "b"]
        assert d["organization"] == "shunya"
        assert d["roles"] == ["admin", "user"]


# =========================================================================
# GraphPermission Enum Tests
# =========================================================================


class TestGraphPermission:
    """UNIVERSAL_KNOWLEDGE_GRAPH_ARCHITECTURE.md §13 — Permission enum."""

    def test_all_permissions_defined(self):
        """All required permissions exist."""
        assert GraphPermission.READ_NODE.value == "read_node"
        assert GraphPermission.UPDATE_NODE.value == "update_node"
        assert GraphPermission.DELETE_NODE.value == "delete_node"
        assert GraphPermission.READ_EDGE.value == "read_edge"
        assert GraphPermission.CREATE_EDGE.value == "create_edge"
        assert GraphPermission.DELETE_EDGE.value == "delete_edge"
        assert GraphPermission.TRAVERSE.value == "traverse"
        assert GraphPermission.VIEW_METADATA.value == "view_metadata"
        assert GraphPermission.VIEW_EVIDENCE.value == "view_evidence"
        assert GraphPermission.VIEW_HISTORY.value == "view_history"
        assert GraphPermission.DISCOVER.value == "discover"

    def test_permission_count(self):
        """There are exactly 11 permissions."""
        assert len(GraphPermission) == 11

    def test_no_business_permissions(self):
        """No business permissions exist."""
        values = [p.value for p in GraphPermission]
        assert "create_travel" not in values
        assert "update_crm" not in values
        assert "manage_booking" not in values
        assert "approve_expense" not in values


# =========================================================================
# Visibility Function Tests
# =========================================================================


class TestVisibilityFunctions:
    """UNIVERSAL_KNOWLEDGE_GRAPH_ARCHITECTURE.md §13.2 — Visibility."""

    def test_visibility_level_rank(self):
        """Visibility levels have correct ranks."""
        assert visibility_level_rank("private") == 0
        assert visibility_level_rank("team") == 1
        assert visibility_level_rank("organisation") == 2
        assert visibility_level_rank("confidential") == 3
        assert visibility_level_rank("public") == 4

    def test_visibility_inherits_private(self):
        """Private only inherits to itself."""
        result = visibility_inherits("private")
        assert result == ["private"]

    def test_visibility_inherits_team(self):
        """Team inherits to private and team."""
        result = visibility_inherits("team")
        assert result == ["private", "team"]

    def test_visibility_inherits_public(self):
        """Public inherits to all levels."""
        result = visibility_inherits("public")
        assert result == ["private", "team", "organisation", "confidential", "public"]

    def test_is_visible_public_to_private(self):
        """Public actor can see private content."""
        assert is_visibility_compatible("public", "private")

    def test_is_visible_private_to_public(self):
        """Private actor cannot see public content (via compatibility check)."""
        # This is the inverse: a private-level requestor can't see public
        # because private is more restrictive
        assert not is_visibility_compatible("private", "public")

    def test_is_visible_same_level(self):
        """Same level is compatible."""
        assert is_visibility_compatible("team", "team")
        assert is_visibility_compatible("organisation", "organisation")

    def test_is_visible_higher_to_lower(self):
        """Higher rank can see lower rank."""
        assert is_visibility_compatible("organisation", "team")
        assert is_visibility_compatible("public", "confidential")

    def test_get_effective_visibility(self):
        """Effective visibility returns node's own visibility."""
        node = Node(visibility="public", owner_id="u1")
        assert get_effective_visibility(node) == "public"

    def test_unknown_level_rank(self):
        """Unknown level defaults to 0 (private)."""
        assert visibility_level_rank("unknown") == 0


# =========================================================================
# Private Node Tests
# =========================================================================


class TestPrivateNode:
    """UNIVERSAL_KNOWLEDGE_GRAPH_ARCHITECTURE.md §13.2 — PRIVATE visibility."""

    def test_owner_can_view_private(self, evaluator, owner_context, private_node):
        """Owner can view their own private node."""
        result = evaluator.can_view_node(owner_context, private_node)
        assert result.allowed
        assert result.permission_checked == "read_node"
        assert result.visibility_checked == "private"

    def test_owner_can_update_private(self, evaluator, owner_context, private_node):
        """Owner can update their own private node."""
        result = evaluator.can_update_node(owner_context, private_node)
        assert result.allowed

    def test_owner_can_delete_private(self, evaluator, owner_context, private_node):
        """Owner can delete their own private node."""
        result = evaluator.can_delete_node(owner_context, private_node)
        assert result.allowed

    def test_other_cannot_view_private(self, evaluator, other_context, private_node):
        """Other user cannot view private node."""
        result = evaluator.can_view_node(other_context, private_node)
        assert not result.allowed

    def test_stranger_cannot_view_private(self, evaluator, stranger_context, private_node):
        """Stranger cannot view private node."""
        result = evaluator.can_view_node(stranger_context, private_node)
        assert not result.allowed

    def test_owner_can_read_metadata_private(self, evaluator, owner_context, private_node):
        """Owner can read metadata of private node."""
        result = evaluator.can_read_metadata(owner_context, private_node)
        assert result.allowed

    def test_owner_can_view_evidence_private(self, evaluator, owner_context, private_node):
        """Owner can view evidence of private node."""
        result = evaluator.can_view_evidence(owner_context, private_node)
        assert result.allowed

    def test_owner_can_view_history_private(self, evaluator, owner_context, private_node):
        """Owner can view history of private node."""
        result = evaluator.can_view_history(owner_context, private_node)
        assert result.allowed


# =========================================================================
# Public Node Tests
# =========================================================================


class TestPublicNode:
    """UNIVERSAL_KNOWLEDGE_GRAPH_ARCHITECTURE.md §13.2 — PUBLIC visibility."""

    def test_anyone_can_view_public(self, evaluator, owner_context, stranger_context, public_node):
        """Anyone can view a public node."""
        result = evaluator.can_view_node(owner_context, public_node)
        assert result.allowed
        result2 = evaluator.can_view_node(stranger_context, public_node)
        assert result2.allowed

    def test_anyone_can_discover_public(self, evaluator, stranger_context, public_node):
        """Anyone can discover a public node."""
        result = evaluator.can_discover(stranger_context, public_node)
        assert result.allowed

    def test_anyone_can_read_metadata_public(self, evaluator, stranger_context, public_node):
        """Anyone can read metadata of public node."""
        result = evaluator.can_read_metadata(stranger_context, public_node)
        assert result.allowed

    def test_owner_can_update_public(self, evaluator, owner_context, public_node):
        """Only owner can update public node."""
        result = evaluator.can_update_node(owner_context, public_node)
        assert result.allowed

    def test_other_cannot_update_public(self, evaluator, stranger_context, public_node):
        """Non-owner cannot update public node."""
        result = evaluator.can_update_node(stranger_context, public_node)
        assert not result.allowed

    def test_only_owner_view_evidence_public(self, evaluator, owner_context, stranger_context, public_node):
        """Only owner can view evidence, even on public node."""
        owner_result = evaluator.can_view_evidence(owner_context, public_node)
        assert owner_result.allowed
        stranger_result = evaluator.can_view_evidence(stranger_context, public_node)
        assert not stranger_result.allowed

    def test_only_owner_view_history_public(self, evaluator, owner_context, stranger_context, public_node):
        """Only owner can view history, even on public node."""
        owner_result = evaluator.can_view_history(owner_context, public_node)
        assert owner_result.allowed
        stranger_result = evaluator.can_view_history(stranger_context, public_node)
        assert not stranger_result.allowed


# =========================================================================
# Team Node Tests
# =========================================================================


class TestTeamNode:
    """UNIVERSAL_KNOWLEDGE_GRAPH_ARCHITECTURE.md §13.2 — TEAM visibility."""

    def test_team_member_can_view(self, evaluator, owner_context, team_node):
        """Team member can view team-visible node."""
        result = evaluator.can_view_node(owner_context, team_node)
        assert result.allowed

    def test_non_team_member_cannot_view(self, evaluator, teamless_context, team_node):
        """Non-team member cannot view team-visible node."""
        result = evaluator.can_view_node(teamless_context, team_node)
        assert not result.allowed

    def test_team_member_can_discover(self, evaluator, owner_context, team_node):
        """Team member can discover team-visible node."""
        result = evaluator.can_discover(owner_context, team_node)
        assert result.allowed

    def test_team_member_can_traverse(self, evaluator, owner_context, team_node, public_node):
        """Team member can traverse from team-visible node."""
        result = evaluator.can_traverse_edge(owner_context, team_node, public_node)
        assert result.allowed


# =========================================================================
# Organization Node Tests
# =========================================================================


class TestOrganizationNode:
    """UNIVERSAL_KNOWLEDGE_GRAPH_ARCHITECTURE.md §13.2 — ORGANISATION visibility.

    Note: The ORG visibility check is conservative — only the owner can
    access org-visible nodes, since org membership cannot be verified
    without a canonical membership lookup. This prevents cross-org access.
    """

    def test_owner_can_view_org(self, evaluator, owner_context, org_node):
        """Organization member (owner) can view org-visible node."""
        result = evaluator.can_view_node(owner_context, org_node)
        assert result.allowed

    def test_stranger_cannot_view_org(self, evaluator, stranger_context, org_node):
        """Stranger from other org cannot view org-visible node."""
        result = evaluator.can_view_node(stranger_context, org_node)
        assert not result.allowed


# =========================================================================
# Confidential Node Tests
# =========================================================================


class TestConfidentialNode:
    """UNIVERSAL_KNOWLEDGE_GRAPH_ARCHITECTURE.md §13.2 — CONFIDENTIAL visibility."""

    def test_owner_can_view_confidential(self, evaluator, owner_context, confidential_node):
        """Owner can view confidential node."""
        result = evaluator.can_view_node(owner_context, confidential_node)
        assert result.allowed

    def test_other_cannot_view_confidential(self, evaluator, other_context, confidential_node):
        """Other user cannot view confidential node."""
        result = evaluator.can_view_node(other_context, confidential_node)
        assert not result.allowed

    def test_stranger_cannot_view_confidential(self, evaluator, stranger_context, confidential_node):
        """Stranger cannot view confidential node."""
        result = evaluator.can_view_node(stranger_context, confidential_node)
        assert not result.allowed

    def test_team_member_cannot_view_confidential(self, evaluator, owner_context, team_node, confidential_node):
        """Team member cannot view confidential node (not owner)."""
        # owner_context has teams, but confidential_node is owned by user_1
        # owner_context IS user_1, so they can see it
        # Use a different context to test
        other = SecurityContext(actor_id="user_5", teams={"engineering"}, organization="shunya")
        result = evaluator.can_view_node(other, confidential_node)
        assert not result.allowed


# =========================================================================
# Traversal Tests
# =========================================================================


class TestTraversal:
    """UNIVERSAL_KNOWLEDGE_GRAPH_ARCHITECTURE.md §13 — Traversal access."""

    def test_can_traverse_public_to_public(self, evaluator, owner_context, public_node):
        """Can traverse between two public nodes."""
        target = Node(node_type="Document", owner_id="user_2", visibility="public")
        result = evaluator.can_traverse_edge(owner_context, public_node, target)
        assert result.allowed

    def test_cannot_traverse_private_to_public(self, evaluator, other_context, private_node, public_node):
        """Cannot traverse from private node you don't own."""
        result = evaluator.can_traverse_edge(other_context, private_node, public_node)
        assert not result.allowed

    def test_can_traverse_owned_private_to_public(self, evaluator, owner_context, private_node, public_node):
        """Owner can traverse from their own private node."""
        result = evaluator.can_traverse_edge(owner_context, private_node, public_node)
        assert result.allowed

    def test_cross_family_traversal(self, evaluator, owner_context):
        """Cross-family traversal is allowed when both endpoints are visible."""
        source = Node(node_type="Person", owner_id="user_1", visibility="team")
        target = Node(node_type="Organization", owner_id="user_1", visibility="team")
        result = evaluator.can_traverse_edge(owner_context, source, target)
        assert result.allowed


# =========================================================================
# Edge Permission Tests
# =========================================================================


class TestEdgePermissions:
    """UNIVERSAL_KNOWLEDGE_GRAPH_ARCHITECTURE.md §13 — Edge permissions."""

    def test_owner_can_read_edge(self, evaluator, owner_context, private_node, public_node):
        """Owner can read edge from their node."""
        result = evaluator.can_read_edge(owner_context, private_node, public_node)
        assert result.allowed

    def test_owner_can_create_edge(self, evaluator, owner_context, private_node, public_node):
        """Owner can create edge from their node."""
        result = evaluator.can_create_edge(owner_context, private_node, public_node)
        assert result.allowed

    def test_owner_can_delete_edge(self, evaluator, owner_context, private_node, public_node):
        """Owner can delete edge from their node."""
        result = evaluator.can_delete_edge(owner_context, private_node, public_node)
        assert result.allowed

    def test_other_cannot_create_edge(self, evaluator, other_context, private_node, public_node):
        """Non-owner cannot create edge from node they don't own."""
        result = evaluator.can_create_edge(other_context, private_node, public_node)
        assert not result.allowed


# =========================================================================
# Discover Tests
# =========================================================================


class TestDiscover:
    """UNIVERSAL_KNOWLEDGE_GRAPH_ARCHITECTURE.md §13 — Discovery permissions."""

    def test_owner_can_discover_private(self, evaluator, owner_context, private_node):
        """Owner can discover their own private node."""
        result = evaluator.can_discover(owner_context, private_node)
        assert result.allowed

    def test_other_cannot_discover_private(self, evaluator, other_context, private_node):
        """Other cannot discover private node."""
        result = evaluator.can_discover(other_context, private_node)
        assert not result.allowed

    def test_anyone_can_discover_public(self, evaluator, stranger_context, public_node):
        """Anyone can discover public node."""
        result = evaluator.can_discover(stranger_context, public_node)
        assert result.allowed


# =========================================================================
# Metadata and Evidence Tests
# =========================================================================


class TestMetadataPermissions:
    """UNIVERSAL_KNOWLEDGE_GRAPH_ARCHITECTURE.md §13 — Metadata permissions."""

    def test_owner_can_read_metadata_private(self, evaluator, owner_context, private_node):
        """Owner can read metadata of private node."""
        result = evaluator.can_read_metadata(owner_context, private_node)
        assert result.allowed

    def test_other_cannot_read_metadata_private(self, evaluator, other_context, private_node):
        """Other cannot read metadata of private node."""
        result = evaluator.can_read_metadata(other_context, private_node)
        assert not result.allowed

    def test_anyone_can_read_metadata_public(self, evaluator, stranger_context, public_node):
        """Anyone can read metadata of public node."""
        result = evaluator.can_read_metadata(stranger_context, public_node)
        assert result.allowed


class TestEvidencePermissions:
    """UNIVERSAL_KNOWLEDGE_GRAPH_ARCHITECTURE.md §13 — Evidence permissions."""

    def test_owner_can_view_evidence_private(self, evaluator, owner_context, private_node):
        """Owner can view evidence of private node."""
        result = evaluator.can_view_evidence(owner_context, private_node)
        assert result.allowed

    def test_other_cannot_view_evidence_private(self, evaluator, other_context, private_node):
        """Other cannot view evidence of private node."""
        result = evaluator.can_view_evidence(other_context, private_node)
        assert not result.allowed

    def test_owner_can_view_evidence_public(self, evaluator, owner_context, public_node):
        """Owner can view evidence of public node."""
        result = evaluator.can_view_evidence(owner_context, public_node)
        assert result.allowed

    def test_other_cannot_view_evidence_public(self, evaluator, stranger_context, public_node):
        """Non-owner cannot view evidence even on public node."""
        result = evaluator.can_view_evidence(stranger_context, public_node)
        assert not result.allowed


class TestHistoryPermissions:
    """UNIVERSAL_KNOWLEDGE_GRAPH_ARCHITECTURE.md §13 — History permissions."""

    def test_owner_can_view_history(self, evaluator, owner_context, private_node):
        """Owner can view history of their node."""
        result = evaluator.can_view_history(owner_context, private_node)
        assert result.allowed

    def test_other_cannot_view_history(self, evaluator, other_context, private_node):
        """Other cannot view history of private node."""
        result = evaluator.can_view_history(other_context, private_node)
        assert not result.allowed


# =========================================================================
# GraphAccessDecision Tests
# =========================================================================


class TestGraphAccessDecision:
    """UNIVERSAL_KNOWLEDGE_GRAPH_ARCHITECTURE.md §13 — Access decision."""

    def test_default_denied(self):
        """Default decision is denied."""
        decision = GraphAccessDecision()
        assert not decision.is_allowed
        assert decision.is_denied

    def test_both_pass(self):
        """Both permission and visibility must pass."""
        pr = PermissionResult(allowed=True)
        vr = PermissionResult(allowed=True)
        decision = GraphAccessDecision(permission=pr, visibility=vr)
        assert decision.is_allowed

    def test_permission_fails(self):
        """Permission failure denies the whole decision."""
        pr = PermissionResult(allowed=False)
        vr = PermissionResult(allowed=True)
        decision = GraphAccessDecision(permission=pr, visibility=vr)
        assert not decision.is_allowed

    def test_visibility_fails(self):
        """Visibility failure denies the whole decision."""
        pr = PermissionResult(allowed=True)
        vr = PermissionResult(allowed=False)
        decision = GraphAccessDecision(permission=pr, visibility=vr)
        assert not decision.is_allowed

    def test_to_dict(self, evaluator, owner_context, private_node):
        """to_dict() returns all fields."""
        decision = evaluator.evaluate(owner_context, "read_node", private_node)
        d = decision.to_dict()
        assert "is_allowed" in d
        assert "permission" in d
        assert "visibility" in d
        assert d["permission"]["allowed"] is True
        assert d["visibility"]["allowed"] is True


# =========================================================================
# GraphAccessEvaluator General Tests
# =========================================================================


class TestEvaluatorGeneral:
    """General evaluator behavior."""

    def test_default_policies_loaded(self):
        """Default policies are loaded by default."""
        evaluator = GraphAccessEvaluator()
        assert len(evaluator.policies) > 0
        assert evaluator.policies == tuple(sorted(
            DEFAULT_POLICIES,
            key=lambda p: (-p.priority, p.name),
        ))

    def test_custom_policies(self):
        """Custom policies override defaults."""
        custom = [GraphSecurityPolicy(
            name="custom-allow-all",
            permission="read_node",
            condition="actor is the owner of the node",
            effect="allow",
            priority=1000,
        )]
        evaluator = GraphAccessEvaluator(policies=custom)
        assert len(evaluator.policies) == 1
        assert evaluator.policies[0].name == "custom-allow-all"

    def test_policies_immutable(self):
        """Policies tuple is immutable."""
        evaluator = GraphAccessEvaluator()
        with pytest.raises(AttributeError):
            evaluator.policies = ()  # type: ignore

    def test_singleton_get(self):
        """get_evaluator returns the same instance."""
        e1 = get_evaluator()
        e2 = get_evaluator()
        assert e1 is e2

    def test_singleton_reset(self):
        """reset_evaluator clears the singleton."""
        e1 = get_evaluator()
        reset_evaluator()
        e2 = get_evaluator()
        assert e1 is not e2

    def test_evaluate_without_node(self, evaluator, owner_context):
        """Evaluate without a node handles gracefully."""
        decision = evaluator.evaluate(owner_context, "read_node")
        assert decision.is_allowed is False
        assert "No policy" in decision.permission.reason

    def test_unknown_permission(self, evaluator, owner_context, private_node):
        """Unknown permission defaults to denied."""
        result = evaluator.evaluate(owner_context, "unknown_permission", private_node)
        assert not result.is_allowed


# =========================================================================
# Determinism and Purity Tests
# =========================================================================


class TestDeterminism:
    """Determinism and purity guarantees."""

    def test_deterministic_same_input(self, evaluator, owner_context, private_node):
        """Same input always produces the same output."""
        results = []
        for _ in range(5):
            result = evaluator.can_view_node(owner_context, private_node)
            results.append(result)
        for r in results[1:]:
            assert r.allowed == results[0].allowed
            assert r.rule_applied == results[0].rule_applied

    def test_deterministic_denied(self, evaluator, other_context, private_node):
        """Same denied input always produces the same denied output."""
        results = []
        for _ in range(5):
            result = evaluator.can_view_node(other_context, private_node)
            results.append(result)
        for r in results[1:]:
            assert r.allowed == results[0].allowed
            assert r.rule_applied == results[0].rule_applied

    def test_idempotent_public(self, evaluator, stranger_context, public_node):
        """Multiple calls with same input produce identical results."""
        r1 = evaluator.can_view_node(stranger_context, public_node)
        r2 = evaluator.can_view_node(stranger_context, public_node)
        r3 = evaluator.can_view_node(stranger_context, public_node)
        assert r1.allowed == r2.allowed == r3.allowed
        assert r1.rule_applied == r2.rule_applied == r3.rule_applied

    def test_no_side_effects(self, evaluator, other_context, private_node):
        """Evaluator does not mutate nodes."""
        original_visibility = private_node.visibility
        original_owner = private_node.owner_id
        _ = evaluator.can_view_node(other_context, private_node)
        assert private_node.visibility == original_visibility
        assert private_node.owner_id == original_owner

    def test_deterministic_across_evaluators(self, owner_context, private_node):
        """Different evaluator instances with same policies produce same results."""
        e1 = GraphAccessEvaluator()
        e2 = GraphAccessEvaluator()
        r1 = e1.can_view_node(owner_context, private_node)
        r2 = e2.can_view_node(owner_context, private_node)
        assert r1.allowed == r2.allowed
        assert r1.rule_applied == r2.rule_applied


# =========================================================================
# Policy Tests
# =========================================================================


class TestPolicy:
    """GraphSecurityPolicy behavior."""

    def test_policy_to_dict(self):
        """Policy serializes correctly."""
        policy = GraphSecurityPolicy(
            name="test-policy",
            permission="read_node",
            condition="actor is the owner",
            effect="allow",
            priority=50,
        )
        d = policy.to_dict()
        assert d["name"] == "test-policy"
        assert d["permission"] == "read_node"
        assert d["effect"] == "allow"
        assert d["priority"] == 50

    def test_default_deny_effect(self):
        """Default effect is deny."""
        policy = GraphSecurityPolicy(
            name="default-deny",
            permission="read_node",
            condition="nothing",
        )
        assert policy.effect == "deny"

    def test_default_priority(self):
        """Default priority is 0."""
        policy = GraphSecurityPolicy(
            name="low-priority",
            permission="read_node",
            condition="nothing",
        )
        assert policy.priority == 0

    def test_default_policies_count(self):
        """DEFAULT_POLICIES has the expected number of rules."""
        assert len(DEFAULT_POLICIES) == 11

    def test_policy_priority_ordering(self, evaluator):
        """Policies are evaluated in priority order (highest first)."""
        policies = evaluator.policies
        priorities = [p.priority for p in policies]
        for i in range(len(priorities) - 1):
            assert priorities[i] >= priorities[i + 1]


# =========================================================================
# SecurityContext Edge Cases
# =========================================================================


class TestSecurityEdgeCases:
    """Edge cases for security evaluation."""

    def test_empty_actor_id(self, evaluator, private_node):
        """Empty actor_id cannot access anything."""
        ctx = SecurityContext(actor_id="")
        result = evaluator.can_view_node(ctx, private_node)
        assert not result.allowed

    def test_node_no_owner(self, evaluator, owner_context):
        """Node without owner defaults to restrictive."""
        node = Node(node_type="Document", owner_id="", visibility="private")
        result = evaluator.can_view_node(owner_context, node)
        # owner_context.actor_id != "" so it won't match owner_id
        assert not result.allowed

    def test_unknown_visibility_level(self, evaluator, owner_context):
        """Unknown visibility level is denied."""
        node = Node(node_type="Document", owner_id="user_1", visibility="unknown_level")
        result = evaluator.can_view_node(owner_context, node)
        assert not result.allowed
        assert "unknown" in result.reason.lower()

    def test_team_member_without_org(self, evaluator, team_node):
        """Team member without organization can still see team node."""
        ctx = SecurityContext(actor_id="user_1", teams={"engineering"}, organization="")
        result = evaluator.can_view_node(ctx, team_node)
        assert result.allowed

    def test_follow_references(self, evaluator, owner_context, private_node, public_node):
        """Following references requires visibility of both nodes."""
        result = evaluator.can_follow_references(owner_context, private_node, public_node)
        assert result.allowed

    def test_view_descendants(self, evaluator, owner_context, private_node):
        """Viewing descendants uses same visibility as viewing the node."""
        result = evaluator.can_view_descendants(owner_context, private_node)
        assert result.allowed

    def test_other_cannot_follow_references(self, evaluator, other_context, private_node, public_node):
        """Non-owner cannot follow references from private node."""
        result = evaluator.can_follow_references(other_context, private_node, public_node)
        assert not result.allowed


# =========================================================================
# Permission Denied / Granted Tests
# =========================================================================


class TestPermissionDenied:
    """Scenarios where permission is denied."""

    def test_private_node_denied_for_stranger(self, evaluator, stranger_context, private_node):
        """Stranger denied access to private node."""
        result = evaluator.can_view_node(stranger_context, private_node)
        assert not result.allowed
        assert result.rule_applied != ""
        assert result.permission_checked != ""

    def test_private_node_denied_for_other_team(self, evaluator, other_context, private_node):
        """Other team member denied access to private node."""
        result = evaluator.can_view_node(other_context, private_node)
        assert not result.allowed

    def test_confidential_denied_for_team(self, evaluator, confidential_node):
        """Team member without ownership denied access to confidential."""
        ctx = SecurityContext(actor_id="user_5", teams={"engineering"}, organization="shunya")
        result = evaluator.can_view_node(ctx, confidential_node)
        assert not result.allowed

    def test_org_node_denied_for_stranger(self, evaluator, stranger_context, org_node):
        """Stranger denied access to org-visible node."""
        result = evaluator.can_view_node(stranger_context, org_node)
        assert not result.allowed

    def test_team_node_denied_for_teamless(self, evaluator, teamless_context, team_node):
        """Teamless actor denied access to team-visible node."""
        result = evaluator.can_view_node(teamless_context, team_node)
        assert not result.allowed


class TestPermissionGranted:
    """Scenarios where permission is granted."""

    def test_owner_granted_all_read(self, evaluator, owner_context, private_node, public_node, team_node, org_node):
        """Owner is granted read access to all their nodes."""
        assert evaluator.can_view_node(owner_context, private_node).allowed
        assert evaluator.can_view_node(owner_context, public_node).allowed
        assert evaluator.can_view_node(owner_context, team_node).allowed
        assert evaluator.can_view_node(owner_context, org_node).allowed

    def test_owner_granted_all_update(self, evaluator, owner_context, private_node, public_node):
        """Owner is granted update access to their nodes."""
        assert evaluator.can_update_node(owner_context, private_node).allowed
        assert evaluator.can_update_node(owner_context, public_node).allowed

    def test_owner_granted_delete(self, evaluator, owner_context, private_node):
        """Owner is granted delete access."""
        assert evaluator.can_delete_node(owner_context, private_node).allowed

    def test_owner_granted_create_edge(self, evaluator, owner_context, private_node, public_node):
        """Owner is granted create edge from their node."""
        assert evaluator.can_create_edge(owner_context, private_node, public_node).allowed

    def test_owner_granted_delete_edge(self, evaluator, owner_context, private_node, public_node):
        """Owner is granted delete edge from their node."""
        assert evaluator.can_delete_edge(owner_context, private_node, public_node).allowed


# =========================================================================
# Conflicting Rules and Invalid Policy Tests
# =========================================================================


class TestConflictingRules:
    """Conflicting policy rules are resolved by priority."""

    def test_high_priority_overrides_low(self):
        """High priority rule overrides low priority."""
        policies = [
            GraphSecurityPolicy(
                name="deny-all",
                permission="read_node",
                condition="actor is the owner of the node",
                effect="deny",
                priority=200,
            ),
            GraphSecurityPolicy(
                name="allow-owner",
                permission="read_node",
                condition="actor is the owner of the node",
                effect="allow",
                priority=100,
            ),
        ]
        evaluator = GraphAccessEvaluator(policies=policies)
        ctx = SecurityContext(actor_id="user_1")
        node = Node(owner_id="user_1", visibility="private")
        result = evaluator.can_view_node(ctx, node)
        # High priority (200) deny rule matches first
        assert not result.allowed
        assert result.rule_applied == "deny-all"


class TestInvalidPolicy:
    """Invalid or unknown policy handling."""

    def test_no_matching_policy_denies(self):
        """No matching policy results in default deny."""
        policies = [
            GraphSecurityPolicy(
                name="only-traverse",
                permission="traverse",
                condition="node visibility is PUBLIC",
                effect="allow",
                priority=100,
            ),
        ]
        evaluator = GraphAccessEvaluator(policies=policies)
        ctx = SecurityContext(actor_id="user_2")
        node = Node(owner_id="user_1", visibility="private")
        result = evaluator.can_view_node(ctx, node)
        # No policy matches READ_NODE for non-owner, and private visibility
        # blocks visibility fallback
        assert not result.allowed
        assert result.rule_applied == "default-deny"

    def test_empty_policies_denies_all(self):
        """Empty policies result in all operations denied."""
        evaluator = GraphAccessEvaluator(policies=[])
        ctx = SecurityContext(actor_id="user_2")
        node = Node(owner_id="user_1", visibility="private")
        result = evaluator.can_view_node(ctx, node)
        assert not result.allowed


# =========================================================================
# Visibility Inheritance Tests
# =========================================================================


class TestVisibilityInheritance:
    """Visibility inheritance patterns."""

    def test_visibility_inherits_org(self):
        """Organisation inherits to private and team."""
        result = visibility_inherits("organisation")
        assert "private" in result
        assert "team" in result
        assert "organisation" in result

    def test_visibility_inherits_confidential(self):
        """Confidential inherits to private, team, org."""
        result = visibility_inherits("confidential")
        assert "private" in result
        assert "team" in result
        assert "organisation" in result
        assert "confidential" in result

    def test_visibility_compatible_narrower_to_broader(self):
        """Narrower visibility cannot see broader."""
        assert not is_visibility_compatible("private", "public")
        assert not is_visibility_compatible("team", "organisation")
        assert not is_visibility_compatible("organisation", "public")

    def test_visibility_compatible_same(self):
        """Same visibility is always compatible."""
        for v in ["private", "team", "organisation", "confidential", "public"]:
            assert is_visibility_compatible(v, v)


# =========================================================================
# GraphPermission and SecurityContext Integration
# =========================================================================


class TestIntegration:
    """Integration tests combining multiple security concepts."""

    def test_full_decision_owner_private(self, evaluator, owner_context, private_node):
        """Full access decision for owner on private node."""
        decision = evaluator.evaluate(owner_context, "read_node", private_node)
        assert decision.is_allowed
        assert decision.permission.allowed
        assert decision.visibility.allowed

    def test_full_decision_stranger_private(self, evaluator, stranger_context, private_node):
        """Full access decision for stranger on private node."""
        decision = evaluator.evaluate(stranger_context, "read_node", private_node)
        assert not decision.is_allowed
        # Either permission or visibility denied
        assert not decision.permission.allowed or not decision.visibility.allowed

    def test_full_decision_stranger_public(self, evaluator, stranger_context, public_node):
        """Full access decision for stranger on public node."""
        decision = evaluator.evaluate(stranger_context, "read_node", public_node)
        assert decision.is_allowed
        assert decision.permission.allowed
        assert decision.visibility.allowed

    def test_team_member_org_member(self):
        """Team member who is also org member can see both."""
        ctx = SecurityContext(
            actor_id="user_1",
            teams={"engineering"},
            organization="shunya",
        )
        assert ctx.organization == "shunya"
        assert "engineering" in ctx.teams