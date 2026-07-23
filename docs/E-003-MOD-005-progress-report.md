# Engineering Progress Report — E-003-MOD-005

**Date:** 2026-07-23
**Epic:** E-003 — Knowledge Graph
**Module:** MOD-005 — Knowledge Graph Security (security.py)
**Commit:** `c7a034c`
**Author:** Hermes Agent

---

## Architectural Objective

This is the FINAL module of the Knowledge Graph epic. It answers Question #4 from the graph architecture:

1. What exists? — Node (MOD-001)
2. How are things connected? — Edge (MOD-002)
3. Are those connections valid? — Consistency (MOD-004)
4. **Who is allowed to know or change them? — Security (MOD-005)**

The module implements universal graph security primitives — a deterministic, side-effect-free access evaluation model for the Knowledge Graph. It is NOT cybersecurity. It is UNIVERSAL GRAPH SECURITY — defining WHO may see, traverse, modify, or discover graph knowledge.

---

## Implementation Summary

Created a read-only deterministic graph security model with:

- **GraphPermission** — 11 universal graph permissions (READ_NODE, UPDATE_NODE, DELETE_NODE, READ_EDGE, CREATE_EDGE, DELETE_EDGE, TRAVERSE, VIEW_METADATA, VIEW_EVIDENCE, VIEW_HISTORY, DISCOVER). No business permissions.
- **SecurityContext** — Pure data object describing who is asking (actor_id, teams, organization, roles).
- **PermissionResult** — Structured result with allowed/denied, reason, rule_applied, permission_checked, visibility_checked, actor_id, resource_id. Never returns bare True/False.
- **GraphAccessDecision** — Combined decision with permission + visibility sub-results.
- **GraphSecurityPolicy** — Single policy rule with name, permission, condition, effect, priority.
- **GraphAccessEvaluator** — Ownership-first with visibility-based fallback for read operations. Pure, deterministic, side-effect free.
- **Visibility functions** — visibility_level_rank, visibility_inherits, is_visibility_compatible, get_effective_visibility.

---

## Classes Added

| Class | Purpose |
|-------|---------|
| `GraphPermission` | Enum of 11 universal graph permissions |
| `GraphSecurityPolicy` | Single policy rule definition |
| `SecurityContext` | Actor context (who is asking) |
| `PermissionResult` | Structured access decision |
| `GraphAccessDecision` | Combined permission + visibility decision |
| `GraphAccessEvaluator` | Main evaluator with 15+ public methods |

---

## Public API

| Method | Description |
|--------|-------------|
| `can_view_node(context, node)` | View a node |
| `can_traverse_edge(context, source, target)` | Traverse an edge |
| `can_modify_relationship(context, source, target)` | Modify a relationship |
| `can_discover(context, node)` | Discover a node via search |
| `can_read_metadata(context, node)` | Read node metadata |
| `can_view_evidence(context, node)` | View node evidence |
| `can_view_descendants(context, node)` | View descendants |
| `can_follow_references(context, source, target)` | Follow references |
| `can_view_history(context, node)` | View node history |
| `can_read_edge(context, source, target)` | Read an edge |
| `can_create_edge(context, source, target)` | Create an edge |
| `can_delete_edge(context, source, target)` | Delete an edge |
| `can_update_node(context, node)` | Update a node |
| `can_delete_node(context, node)` | Delete a node |
| `evaluate(context, permission, node)` | Full access decision |
| `visibility_level_rank(level)` | Numeric rank of a visibility level |
| `visibility_inherits(level)` | All levels that can see this level |
| `is_visibility_compatible(requestor, target)` | Visibility compatibility check |

---

## Design Rationale

### Permission Model
The permission model is **ownership-first with visibility-based fallback** for read operations. Ownership policies are checked first. If no ownership policy matches and the operation is a READ-type operation (read_node, discover, view_metadata, traverse), the visibility of the resource is checked as a fallback. This ensures PUBLIC nodes are readable by anyone while MODIFY operations remain owner-only.

### Evidence and History
VIEW_EVIDENCE and VIEW_HISTORY are **excluded from the visibility fallback** — they remain owner-only. Non-owners cannot view evidence or history even on PUBLIC nodes. This protects the privacy of provenance data.

### ORG Visibility
The ORGANISATION visibility check is **conservative (owner-only)** since org membership cannot be verified without a canonical membership lookup. This prevents cross-org access when org membership cannot be verified. Future work can add a membership lookup service.

### Visibility Inheritance
Visibility levels have a rank-based hierarchy: PRIVATE (0) < TEAM (1) < ORGANISATION (2) < CONFIDENTIAL (3) < PUBLIC (4). A requestor can see a target if their visibility level rank is >= the target's rank. `visibility_inherits()` returns all levels that can see a given level.

---

## Deterministic Guarantees

- **Deterministic**: Same input always produces the same output. Tested with 5 repeated calls on both allowed and denied scenarios.
- **Pure**: No side effects. The evaluator never mutates nodes, edges, or stores.
- **Idempotent**: Multiple calls with the same input produce identical results.
- **No persistence**: No caching, no database, no background jobs.
- **No mutations**: No repair, no auto-heal, no state changes.

---

## Permission Model

11 universal graph permissions:

| Permission | Category | Description |
|------------|----------|-------------|
| READ_NODE | Read | View a node's content |
| UPDATE_NODE | Modify | Update a node's properties |
| DELETE_NODE | Modify | Delete a node |
| READ_EDGE | Read | View an edge's content |
| CREATE_EDGE | Modify | Create a new edge |
| DELETE_EDGE | Modify | Delete an edge |
| TRAVERSE | Traverse | Follow an edge between nodes |
| VIEW_METADATA | Read | Read node metadata |
| VIEW_EVIDENCE | Read | View node evidence (owner-only) |
| VIEW_HISTORY | Read | View node history (owner-only) |
| DISCOVER | Read | Find nodes via search/query |

No business permissions exist. No CRM, travel, or Panchi Club permissions.

---

## Visibility Model

| Level | Rank | Access |
|-------|------|--------|
| PUBLIC | 4 | Anyone can see |
| CONFIDENTIAL | 3 | Owner only |
| ORGANISATION | 2 | Owner only (conservative) |
| TEAM | 1 | Any actor with team membership |
| PRIVATE | 0 | Owner only |

Visibility inheritance: PUBLIC can see everything; PRIVATE can only see PRIVATE.

---

## Tests Added

**File:** `tests/graph/test_security.py`
**Test count:** 115 tests across 25 test classes

| Test Class | Tests | Description |
|------------|-------|-------------|
| TestPermissionResult | 4 | PermissionResult structure, defaults, to_dict |
| TestSecurityContext | 3 | SecurityContext initialization, conversion, to_dict |
| TestGraphPermission | 3 | Enum values, count, no business permissions |
| TestVisibilityFunctions | 10 | Level rank, inheritance, compatibility |
| TestPrivateNode | 8 | Owner can view/update/delete, others cannot |
| TestPublicNode | 7 | Anyone can view/discover/metadata, owner-only evidence/history |
| TestTeamNode | 4 | Team member can view/discover/traverse |
| TestOrganizationNode | 2 | Owner can view, stranger cannot |
| TestConfidentialNode | 4 | Owner can view, others cannot |
| TestTraversal | 4 | Public-to-public, private-to-public, cross-family |
| TestEdgePermissions | 4 | Owner can read/create/delete, non-owner cannot create |
| TestDiscover | 3 | Owner can discover private, anyone can discover public |
| TestMetadataPermissions | 3 | Owner/other/public metadata access |
| TestEvidencePermissions | 4 | Owner/other evidence access |
| TestHistoryPermissions | 2 | Owner/other history access |
| TestGraphAccessDecision | 5 | Default, both pass, one fails, to_dict |
| TestEvaluatorGeneral | 6 | Default policies, custom, singleton, evaluate |
| TestDeterminism | 5 | Same input, denied, idempotent, no side effects, cross-evaluator |
| TestPolicy | 5 | to_dict, default effect, priority, count, ordering |
| TestSecurityEdgeCases | 7 | Empty actor, no owner, unknown visibility, teams, references |
| TestPermissionDenied | 5 | Private/confidential/org/team denied scenarios |
| TestPermissionGranted | 5 | Owner granted all read/update/delete/edge |
| TestConflictingRules | 1 | High priority overrides low |
| TestInvalidPolicy | 2 | No matching policy, empty policies |
| TestVisibilityInheritance | 4 | Inheritance patterns, compatibility |
| TestIntegration | 4 | Full decision scenarios |

---

## Total Test Count

- **Before:** 1732 tests
- **After:** 1847 tests
- **New:** 115 tests (all passing)
- **Regression:** 0 (all existing tests pass)

---

## Files Changed

| File | Status | Lines | Purpose |
|------|--------|-------|---------|
| `app/graph/security.py` | **New** | 1120 | Security model and evaluator |
| `app/graph/__init__.py` | **Modified** | +15 | Export security module |
| `tests/graph/test_security.py` | **New** | 1116 | 115 security tests |

---

## Commit Hashes

- **Implementation commit:** `c7a034c` — "E-003-MOD-005: Knowledge Graph Security — universal graph access control"

---

## Known Limitations

1. **ORG visibility is conservative**: Since org membership cannot be verified without a canonical lookup, ORG-visible nodes are treated as owner-only. Future work can add a `membership_service` parameter to the evaluator.
2. **No named permission grants**: The current model only supports ownership-based grants. Named grants (e.g., "user_2 can read node_x") are not implemented. This is intentional — the directive specifies no persistence, and named grants would require a grant store.
3. **No CI verification**: The push succeeded but CI status could not be verified programmatically due to missing GitHub token. Manual verification of GitHub Actions is required.
4. **No hierarchical visibility inheritance**: `get_effective_visibility` returns the node's own visibility. Future work could compute inherited visibility from parent nodes (container/organization).

---

## Scope Boundaries

The following were explicitly **NOT** implemented (as required by the directive):

- ❌ Login / authentication / OAuth / JWT
- ❌ User accounts / passwords / sessions
- ❌ Web security / API security / HTTP middleware
- ❌ Encryption / rate limiting / tenant billing
- ❌ Cloud IAM / RBAC dashboards
- ❌ Business logic (CRM, travel, Panchi Club)
- ❌ Persistence / caching / background jobs
- ❌ Mutations / repair / auto-heal
- ❌ No business permissions introduced

---

## E-003 Epic Completion

This is the **final module** of the Knowledge Graph epic. The graph now answers all four questions:

1. **What exists?** — Node (MOD-001)
2. **How are things connected?** — Edge (MOD-002)
3. **Are those connections valid?** — Consistency (MOD-004)
4. **Who is allowed to know or change them?** — Security (MOD-005)

---

## Next Task

**STOP.** Do NOT begin E-004 (Evidence Engine), Reasoning, Relationship Engine, Planning, Execution, or Learning. Wait for explicit founder approval before proceeding to the next epic.