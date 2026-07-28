# Architecture Clarification Note — E-003-MOD-005

**Date:** 2026-07-23
**Module:** Knowledge Graph Security
**Author:** Chief Constitutional Architect

---

## 1. Design Decisions That Changed During Implementation

### 1.1. Visibility-Based Permission Policies (REMOVED)

The initial DEFAULT_POLICIES included visibility-based rules such as `public-read`, `public-traverse`, `public-discover`, `public-metadata`, `team-read`, `team-traverse`, `team-discover`, `org-read`, `org-traverse`, and `org-discover`. These duplicated the logic already present in `_check_visibility`.

**Problem:** Two sources of truth for the same visibility rule. If a policy was added or removed, the visibility check would silently compensate — or vice versa. The system had no single authority for visibility decisions.

**Resolution:** Removed all visibility-based policies from DEFAULT_POLICIES. Visibility is now governed exclusively by `_check_visibility`. The permission layer (`_check_permission`) handles only ownership.

### 1.2. Broad TRAVERSE Policy Matching (REMOVED)

The initial `_check_permission` matched policies with `policy.permission == permission or policy.permission == GraphPermission.TRAVERSE.value`. This caused every TRAVERSE policy to match every permission check — `can_view_evidence` matched `public-traverse`, `can_update_node` matched `team-traverse`, etc.

**Problem:** A policy designed to govern edge traversal was accidentally granting evidence reads, metadata views, and node updates. This was a logic error, not a design choice.

**Resolution:** `_check_permission` now matches only the exact permission string. TRAVERSE policies govern only TRAVERSE checks.

### 1.3. Broad Organization Visibility (REMOVED)

The initial `_check_visibility` for ORGANISATION level allowed any actor with a non-empty `organization` field to see the node. This meant `stranger_context` (`organization="other_corp"`) could see an org-visible node owned by a different org.

**Problem:** Without a canonical membership lookup, we could not verify that the actor's organization matched the node owner's organization. The check was effectively a no-op.

**Resolution:** ORGANISATION visibility is now conservative — only the owner can access org-visible nodes. This is documented as a temporary limitation.

---

## 2. Permanent Architecture

The following decisions are permanent and will not change in future modules:

### 2.1. Ownership-First Permission Model

The evaluator checks ownership policies before any other mechanism. If the actor is the owner of the node, they are granted the requested permission (for any permission type — read, update, delete, create edge, etc.).

**Why permanent:** Ownership is the atomic unit of graph authority. The owner of a node has absolute authority over it. This mirrors the constitutional rule that every node must have an owner (§13.3). No future module can override this — the owner is always the final authority.

**Universality preserved:** Ownership is business-agnostic. Every node in every domain has an owner. There is no CRM, travel, or Panchi Club concept here.

### 2.2. Visibility Fallback for Read Operations

After ownership policies are exhausted, read operations (READ_NODE, DISCOVER, VIEW_METADATA, TRAVERSE, READ_EDGE) fall back to a visibility check. If the visibility level permits the actor to see the resource, the read is granted.

**Why permanent:** This is the mechanism that makes visibility meaningful. Without it, PUBLIC visibility would be irrelevant — a non-owner on a public node would be denied by the ownership check alone. The visibility fallback bridges the gap between "who owns this" and "who can see this."

**Universality preserved:** Visibility levels (PUBLIC, TEAM, ORGANISATION, CONFIDENTIAL, PRIVATE) are universal primitives. They describe the graph itself, not the industry using it.

### 2.3. Evidence and History Are Owner-Only

VIEW_EVIDENCE and VIEW_HISTORY are explicitly excluded from the visibility fallback. Even on a PUBLIC node, only the owner can view evidence or history.

**Why permanent:** Evidence and history are provenance data — they describe where the node came from, who created it, and what chain of reasoning supports it. Granting provenance access to non-owners would violate the constitutional principle that provenance is the owner's domain. Evidence privacy is not a security feature — it is a property of the graph's trust model.

**Universality preserved:** Every node has evidence and history regardless of domain. The rule is universal — no business logic can override it.

### 2.4. Structured PermissionResult (Never Bare Boolean)

Every access decision returns a `PermissionResult` with `allowed`, `reason`, `rule_applied`, `permission_checked`, `visibility_checked`, `actor_id`, and `resource_id`. The `evaluate` method returns a `GraphAccessDecision` with both permission and visibility sub-results.

**Why permanent:** The directive explicitly states "Never return only True/False." Structured results enable audit trails, debugging, and governance — the system can explain WHY a decision was made, not just what the decision was.

**Universality preserved:** Structured results are a universal engineering pattern. They are not specific to any business domain.

### 2.5. Visibility Level Hierarchy

The visibility levels have a fixed rank order: PRIVATE (0) < TEAM (1) < ORGANISATION (2) < CONFIDENTIAL (3) < PUBLIC (4). A requestor can see a target if their rank is >= the target's rank. `visibility_inherits()` returns all levels that can see a given level.

**Why permanent:** This is the canonical visibility model. It is a lattice — every level has a defined relationship to every other level. Alternative models (e.g., tag-based visibility) would require a different module, not a modification of this one.

**Universality preserved:** The lattice is a mathematical structure. It has no business content.

### 2.6. No Business Permissions

The `GraphPermission` enum contains exactly 11 permissions: READ_NODE, UPDATE_NODE, DELETE_NODE, READ_EDGE, CREATE_EDGE, DELETE_EDGE, TRAVERSE, VIEW_METADATA, VIEW_EVIDENCE, VIEW_HISTORY, DISCOVER. No business permissions exist.

**Why permanent:** The architecture is the universal intelligence layer for SHUNYA. Business permissions (e.g., "approve_expense", "manage_booking") would couple the graph to a specific industry. This is forbidden by the constitution.

**Universality preserved:** The constitution explicitly prohibits business logic in the kernel.

---

## 3. Temporary Implementation Limitations

The following are acknowledged limitations that will be resolved by future modules. They are NOT permanent architecture.

### 3.1. ORG Visibility Is Conservative (Owner-Only)

**Current behavior:** ORGANISATION-visible nodes are accessible only to the owner.

**Why temporary:** The evaluator has no canonical membership lookup. It cannot verify that an actor's organization matches the node owner's organization. A future module (likely a Membership Service or Identity Governance module) will provide a `membership_check` function that the evaluator can call.

**Expected resolution:** When a membership service exists, the ORG visibility check will call `membership_service.is_member(context.actor_id, node.owner_id, node.organization)` and return allowed if the actor is in the same organization. The evaluator's `_check_visibility` method is designed to accept this extension without structural changes.

### 3.2. No Named Permission Grants

**Current behavior:** The only way to grant permission is through ownership. There is no mechanism for "actor A can read node X" without ownership.

**Why temporary:** Named grants require persistence (a grant store). The directive explicitly forbids persistence in this module. A future module can add a `GrantStore` that the evaluator's `_check_permission` consults as a third pass (after ownership, before visibility fallback).

**Expected resolution:** A future `GrantStore` module with `create_grant(actor_id, permission, node_id)` and `revoke_grant()`. The evaluator will check the grant store between ownership policies and the visibility fallback.

### 3.3. No Hierarchical Visibility Inheritance

**Current behavior:** `get_effective_visibility` returns the node's own visibility. A child node does not inherit visibility from its parent container.

**Why temporary:** Computing inherited visibility requires resolving the containment hierarchy, which depends on the Relationship Engine (E-004 or later). Until then, the conservative default is to use the node's own visibility.

**Expected resolution:** When the Relationship Engine is available, `get_effective_visibility` will traverse the `CONTAINS` / `PARENT_OF` edges upward to find the highest-reaching visibility in the containment chain.

### 3.4. No CI Gate Verification

**Current behavior:** The push to `origin/main` succeeded but CI status could not be verified programmatically.

**Why temporary:** This is a session-level limitation (no GitHub token available). The canonical requirement is CI green before proceeding. Manual verification is needed after push.

---

## 4. Summary Table

| Decision | Status | Rationale | Universality |
|----------|--------|-----------|--------------|
| Ownership-first permission | Permanent | Owner is atomic authority | Every node has an owner |
| Visibility fallback for reads | Permanent | Makes visibility meaningful | Visibility levels are universal |
| Evidence owner-only | Permanent | Provenance is owner's domain | Every node has evidence |
| History owner-only | Permanent | Provenance is owner's domain | Every node has history |
| Structured PermissionResult | Permanent | Never bare True/False | Universal engineering pattern |
| Visibility level hierarchy | Permanent | Canonical lattice model | Mathematical structure |
| No business permissions | Permanent | Constitutional prohibition | Industry-agnostic kernel |
| Conservative ORG visibility | Temporary | No membership lookup yet | Future: membership service |
| No named grants | Temporary | Needs persistence (future) | Future: GrantStore module |
| No hierarchical inheritance | Temporary | Needs Relationship Engine | Future: containment traversal |
| No CI gate | Temporary | No token in session | Future: manual verification |