# ES-001: Governance Engine

**Status:** Draft
**Phase:** Phase 2
**Layer:** Governance
**Author:** Chief Software Architect
**Date:** 2026-07-18
**Approver:** (filled on approval)

---

## 1. Objective

### Mission

The Governance Engine validates every proposed action against constitutional principles, business policies, and risk thresholds before execution is permitted. It is the gatekeeper that enforces "AI Proposes, Humans Dispose" — no action reaches the Executor Layer without passing through governance validation.

### Why It Exists

The SHUNYA Constitution requires that no single component can independently compromise correctness, security, or execution. The Governance Engine is the independent validation layer that sits between Planning and Execution. It can stop execution even if the Reasoning Layer made a bad recommendation. It is the architectural guarantee that every action is explainable, policy-compliant, and appropriately risky.

### Architectural Responsibility

The Governance Engine owns the **Judgment** function within the Compounding Intelligence Loop. It does not reason, plan, execute, or learn. It evaluates plans and actions against known rules and returns a verdict: approve, reject, or require human review.

Position in the pipeline:

```
Planner → Governance → Executor → Observer
             ↑
        Reasoning (evidence chain)
```

---

## 2. Scope

### In Scope

- Validate proposed actions against registered policies
- Evaluate evidence chains for completeness and confidence
- Assess risk levels and assign severity
- Return structured verdicts (APPROVE, REVIEW, REJECT)
- Enforce tenant isolation — policies are scoped per tenant
- Maintain an immutable audit trail of all governance decisions
- Support domain-specific policies (travel, healthcare, legal, etc.)
- Support per-action and per-plan validation
- Provide governance statistics and health metrics
- Register and deregister policies at runtime
- Enrich context with computed fields (pax count, lead time, estimated cost, international flag, wedding flag)

### Out of Scope

- **Never execute actions.** The Governance Engine does not send messages, create database records, or call external APIs.
- **Never mutate knowledge.** The Governance Engine does not store facts, update policies, or modify the Knowledge Store.
- **Never reason on behalf of the Reasoning Layer.** The Governance Engine evaluates proposals — it does not generate them.
- **Never access credentials.** The Governance Engine does not read API tokens, passwords, or payment secrets.
- **Never make decisions that require human judgment.** The Governance Engine flags REVIEW-required decisions — it does not simulate human judgment.
- **Never manage policy authoring workflows.** Policy creation, modification, and retirement are out of scope (belong to constitutional administration).
- **Never compute relevance or attention.** Phase 13 (Relevance) owns that function.
- **Never control inference placement.** Phase 14C (Inference Control) owns that function.

---

## 3. Dependencies

### Internal Dependencies

| Dependency | Type | Description |
|------------|------|-------------|
| Planner Layer | Input | Provides the proposed plan/action for validation |
| Reasoning Layer | Input | Provides evidence chain, confidence score, and risk flags |
| Workspace Context (Phase 10) | Input | Provides tenant, actor, purpose, and subject context |
| Policy Registry | Internal | Stores and retrieves governance policies |
| Audit Log | Internal | Records all governance decisions for traceability |
| Tenant Model | Input | Provides tenant identity for policy scoping |
| Observer Layer | Output | Consumes governance decisions for observation records |

### External Dependencies

- None. The Governance Engine is self-contained with no external API calls, no network dependencies, and no third-party libraries.

---

## 4. Inputs

### Input Contract

```
GovernanceInput:
  action_type: string          — "plan" | "action" | "proposal_send" | "data_mutation" | "financial"
  proposal: PlanObject         — The plan or action being proposed (from Planner)
  evidence_chain: Evidence[]   — Evidence supporting the proposal (from Reasoning)
  confidence: float            — 0.0 to 1.0 confidence score from Reasoning
  risk_flags: string[]         — Risk flags identified by Reasoning
  user_intent: string          — The original human intent (from Interface)
  context: WorkspaceContext    — Tenant, actor, purpose, subject (from Phase 10)
  domain: string               — "travel" | "healthcare" | "legal" | etc.
  timestamp: datetime          — When the proposal was generated
```

### Input Sources

| Source | Event | Trigger |
|--------|-------|---------|
| Planner Layer | Plan generated | On plan creation, before passing to Executor |
| Reasoning Layer | Evidence chain | Bundled with the plan from Planner |
| Phase 10 (Context Fusion) | Workspace context | On any governance-relevant state change |
| Interface Layer | Direct action request | On explicit action requests (send, mutate, delete) |
| Executor Layer | Pre-execution check | On every outbound action, as a pre-flight gate |

### Input Validation

| Field | Constraint | Default | Rejection |
|-------|-----------|---------|-----------|
| `action_type` | Must be one of: plan, action, proposal_send, data_mutation, financial | None (required) | `INVALID_ACTION_TYPE` |
| `proposal` | Must be non-empty dict | None (required) | `EMPTY_PROPOSAL` |
| `context.tenant_id` | Must be positive integer | None (required) | `MISSING_TENANT` |
| `domain` | Must be recognized in domain registry | "travel" | `UNKNOWN_DOMAIN` |
| `confidence` | 0.0 to 1.0 | 0.0 | Clamped to range |
| `evidence_chain` | May be empty | [] | Warning only — reduced confidence |

---

## 5. Outputs

### Output Contract

```
GovernanceVerdict:
  approved: boolean              — True if action may proceed
  decision: string               — "APPROVE" | "REVIEW" | "REJECT"
  confidence: float              — 0.0 to 1.0 overall governance confidence
  explanation: string            — Human-readable summary of the decision
  blocking_policies: string[]    — Policies that blocked the action
  warnings: string[]             — Policies that produced warnings
  reviews_required: string[]     — Policies that require human review
  evidence_checked: boolean      — Whether evidence chain was evaluated
  policy_violations: PolicyViolation[]  — Structured violation details
  required_human_approval: boolean  — True if REVIEW decision
  audit_id: string               — Unique identifier for this decision
  evaluated_at: datetime         — When the decision was made
  context_snapshot: dict         — Frozen context at time of evaluation
```

### Output Destinations

| Destination | Consumer | Delivery Guarantee |
|-------------|----------|-------------------|
| Planner Layer | Plan rejected → alternative plan generation | Best-effort |
| Executor Layer | APPROVED → proceed with execution | At-least-once (must be received before execution) |
| Observer Layer | Record decision for observation | At-least-once |
| Audit Log | Immutable record | Exactly-once |
| Human Review Queue | REVIEW → surface for human approval | Best-effort |
| Interface Layer | Decision summary for user feedback | Best-effort |

### Output Guarantees

- **Idempotency:** Same input with same policies always produces same verdict. No side effects from repeated evaluation.
- **Determinism:** The Governance Engine is fully deterministic. No randomness, no external state, no time-dependent policies (except explicit date checks).
- **Freshness:** Policies are evaluated at decision time. If a policy is updated, the next evaluation sees the new policy.

---

## 6. State Machine

### States

```
Idle
 │
 │ [proposal_received]
 ▼
Receiving ──[timeout]──→ Error
 │
 │ [input_validated]
 ▼
Validating_Context
 │
 ├──[context_valid]──→ Validating_Constitution
 │
 └──[context_invalid]──→ Error
 │
Validating_Constitution
 │
 ├──[constitutional]──→ Evaluating_Policies
 │
 └──[non_constitutional]──→ Rejected
 │
Evaluating_Policies
 │
 ├──[all_pass]──→ Assessing_Risk
 │
 ├──[blocking_found]──→ Rejected
 │
 └──[review_required]──→ Review_Required
 │
Assessing_Risk
 │
 ├──[low_risk]──→ Approved
 │
 ├──[medium_risk]──→ Review_Required
 │
 └──[high_risk]──→ Rejected
 │
Approved ──[verdict_returned]──→ Idle
 │
Review_Required ──[verdict_returned]──→ Idle
 │
Rejected ──[verdict_returned]──→ Idle
 │
Error ──[error_logged]──→ Idle
```

### State Definitions

| State | Meaning | Is Terminal? |
|-------|---------|-------------|
| Idle | Waiting for a proposal | No |
| Receiving | Validating input structure and required fields | No |
| Validating_Context | Enriching and validating the workspace context | No |
| Validating_Constitution | Checking constitutional compliance | No |
| Evaluating_Policies | Running all applicable policies against the proposal | No |
| Assessing_Risk | Computing overall risk level from policy results | No |
| Approved | Proposal passed all checks | Yes (terminal) |
| Review_Required | Proposal requires human approval | Yes (terminal) |
| Rejected | Proposal blocked by policies or constitutional violation | Yes (terminal) |
| Error | Processing failed before a decision could be reached | Yes (terminal) |

### Transition Table

| From State | Event | Condition | To State | Action |
|------------|-------|-----------|----------|--------|
| Idle | proposal_received | Input structure valid | Receiving | Begin validation |
| Idle | proposal_received | Input structure invalid | Error | Log validation error |
| Receiving | input_validated | All required fields present | Validating_Context | Enrich context |
| Receiving | timeout | 30s elapsed | Error | Log timeout |
| Validating_Context | context_valid | Tenant and domain recognized | Validating_Constitution | Check constitutional rules |
| Validating_Context | context_invalid | Tenant/domain unknown | Error | Log context error |
| Validating_Constitution | constitutional | No constitutional principles violated | Evaluating_Policies | Run policy registry |
| Validating_Constitution | non_constitutional | Constitutional principle violated | Rejected | Record constitutional violation |
| Evaluating_Policies | all_pass | No BLOCK or REVIEW severity | Assessing_Risk | Compute risk score |
| Evaluating_Policies | blocking_found | Any BLOCK severity policy triggered | Rejected | Record blocking policies |
| Evaluating_Policies | review_required | Any REVIEW severity policy triggered | Review_Required | Flag for human review |
| Assessing_Risk | low_risk | Risk score < 0.3 | Approved | Return APPROVE verdict |
| Assessing_Risk | medium_risk | Risk score 0.3–0.7 | Review_Required | Flag for human review |
| Assessing_Risk | high_risk | Risk score > 0.7 | Rejected | Return REJECT verdict |
| Approved | verdict_returned | Verdict delivered to consumer | Idle | Log completion |
| Review_Required | verdict_returned | Verdict delivered to consumer | Idle | Log completion |
| Rejected | verdict_returned | Verdict delivered to consumer | Idle | Log completion |
| Error | error_logged | Error recorded in audit log | Idle | Log completion |

---

## 7. Events

### Events Consumed

| Event | Source | Payload | Action Taken |
|-------|--------|---------|-------------|
| `action.proposed` | Planner Layer / Interface Layer | `{action_type, proposal, context}` | Begin governance validation |
| `policy.registry.updated` | Policy administration | `{policies_added, policies_removed}` | Refresh in-memory policy cache |
| `workspace.context.changed` | Phase 10 (Context Fusion) | `{tenant_id, actor_id, new_context}` | Update context enrichment data |
| `domain.registered` | Domain administration | `{domain, policies}` | Register domain-specific policies |
| `human.review.completed` | Human Review UI | `{audit_id, decision, notes}` | Record human decision in audit trail |

### Events Produced

| Event | Destination | Payload | Trigger Condition |
|-------|-------------|---------|-------------------|
| `governance.action.approved` | Executor Layer, Observer Layer | `{audit_id, decision, explanation}` | Verdict = APPROVED |
| `governance.human.review.required` | Human Review Queue, Observer Layer | `{audit_id, proposal, context, policies_triggered}` | Verdict = REVIEW |
| `governance.policy.violation` | Observer Layer, Alerting | `{audit_id, policy_name, severity, detail}` | Any policy violation detected |
| `governance.decision.logged` | Audit Log, Observer Layer | `{audit_id, verdict, timestamp, policies_evaluated}` | Every governance decision |
| `governance.error` | Observer Layer, Alerting | `{error_type, detail, context_snapshot}` | Any processing error |

---

## 8. Failure Modes

| Failure Mode | Cause | Detection | Effect | Recovery |
|--------------|-------|-----------|--------|----------|
| Missing evidence | Empty or null evidence chain | Schema validation | Reduced confidence; REVIEW or REJECT based on action type | Return verdict with `evidence_checked: false` |
| Unknown policy reference | Policy name in context does not match any registered policy | Registry lookup | Warning logged; policy skipped | Return verdict with warning |
| Invalid workspace context | Missing tenant_id, actor_id, or purpose_code | Schema validation | REJECT | Return `INVALID_CONTEXT` error |
| Policy conflict | Two policies produce contradictory requirements | Post-evaluation analysis | REVIEW required | Return verdict with conflicting policies listed |
| Timeout | Processing exceeds 30-second budget | Timer | REJECT | Return `PROCESSING_TIMEOUT` error |
| Circular policy dependency | Policy A's condition references Policy B's output | Dependency graph cycle detection | Policy evaluation fails safe | Skip both policies, return REVIEW |
| Context enrichment failure | Date parsing, pax calculation, or cost estimation fails | Per-field try/catch | Default values used; confidence reduced | Return verdict with enrichment warning |
| Policy evaluation exception | eval() raises unexpected exception | Try/catch in policy.evaluate() | Policy treated as failed; BLOCK severity | Return verdict with policy error detail |
| Concurrent policy registry modification | Policy added/removed during evaluation | Read lock on registry | Safe — evaluation uses snapshot | Retry on next evaluation |

---

## 9. Observability

### Logging

| Event | Log Level | Data | Privacy Constraint |
|-------|-----------|------|-------------------|
| Proposal received | INFO | audit_id, action_type, tenant_id, domain | No personal data |
| Policy evaluation started | DEBUG | audit_id, policy count | None |
| Policy evaluation result | INFO | audit_id, policy_name, severity, passed | None |
| Verdict produced | INFO | audit_id, decision, confidence, blocking count | No personal data |
| Human review required | WARN | audit_id, tenant_id, domain, policies_triggered | No personal data |
| Processing error | ERROR | error_type, detail, context snapshot (sanitized) | Strip credentials, PII |
| Policy registration | INFO | policy_name, scope, severity | None |
| Timeout | ERROR | audit_id, elapsed_ms | None |

### Tracing

- **Span: `governance.validate`** — Covers the full validation lifecycle
  - Child span: `governance.enrich_context` — Context enrichment phase
  - Child span: `governance.evaluate_policies` — Policy evaluation phase
  - Child span: `governance.assess_risk` — Risk assessment phase
- Trace context propagated from caller (Planner or Interface)
- audit_id propagated as a trace tag for cross-engine correlation

### Alerting

| Condition | Severity | Threshold |
|-----------|----------|-----------|
| Error rate > 5% | Pager | Per minute |
| Any rejection of a human-approved action | Pager | Immediate |
| Latency p99 > 500ms | Ticket | Per minute |
| Policy evaluation exception | Warning | Per occurrence |
| Rate limit exceeded (if any) | Warning | Per occurrence |

---

## 10. Metrics

| Metric | Type | Unit | Target | Measurement |
|--------|------|------|--------|-------------|
| `governance.requests_total` | Counter | requests | N/A | Per second, by action_type and domain |
| `governance.approved_total` | Counter | approvals | N/A | Per second, by domain |
| `governance.rejected_total` | Counter | rejections | N/A | Per second, by policy_name |
| `governance.review_required_total` | Counter | reviews | N/A | Per second, by domain |
| `governance.latency_p50` | Histogram | ms | < 50ms | Per request |
| `governance.latency_p99` | Histogram | ms | < 200ms | Per request |
| `governance.error_rate` | Gauge | % | < 1% | Per minute |
| `governance.policies_evaluated` | Histogram | policies | N/A | Per request, distribution |
| `governance.policies_registered` | Gauge | count | N/A | Absolute, by scope |
| `governance.audit_log_size` | Gauge | entries | N/A | Absolute |

---

## 11. Rollback Strategy

### Rollback Triggers

- Governance Engine produces incorrect verdicts (false positives or false negatives)
- Policy evaluation error rate exceeds 5% over 5 minutes
- Data corruption detected in the audit log
- Manual rollback authorized by the Chief Software Architect

### Rollback Procedure

1. **Freeze new evaluations:** Stop accepting new proposals at the governance boundary.
2. **Drain in-flight:** Allow current evaluations to complete.
3. **Restore previous policy registry:** Load the policy snapshot from before the faulty deployment.
4. **Verify:** Run the verification checklist against the restored version.
5. **Resume:** Accept new proposals with the restored version.
6. **Audit:** Record the rollback in the governance changelog.

### Rollback Limitations

- Decisions already delivered to the Executor cannot be recalled. The Executor must handle its own rollback.
- The audit log is append-only and cannot be rolled back. Incorrect verdicts remain as historical records.
- Policy changes that are procedural (not schema-based) are fully rollback-safe. Policy schema changes require migration.

---

## 12. Migration Strategy (when applicable)

### Migration Type

Configuration migration — policy registry definitions.

### Migration Steps

1. **Pre-migration validation:** Verify all existing policies are valid under the new schema.
2. **Dual-write (if applicable):** Evaluate proposals against both old and new policy sets, log discrepancies.
3. **Cutover:** Switch from old policy set to new policy set atomically.
4. **Post-migration verification:** Run a sample of recent proposals through the new policy set, confirm verdicts match expected outcomes.

### Rollback During Migration

- Point-in-time: The policy registry snapshot before migration.
- Data consistency: All historical audit entries remain valid regardless of migration.
- Migration is zero-downtime if dual-write is used. Otherwise, a brief freeze is required.

---

## 13. Verification

### Unit Tests

- State transitions: 14 tests (one per transition in the transition table)
- Error handling: 8 tests (one per failure mode)
- Edge cases: 12 tests (empty evidence, unknown domain, concurrent registry modification, timeout, etc.)

### Integration Tests

- Integration with Planner Layer: 6 tests (plan submission, rejection, review, approval flows)
- Integration with Executor Layer: 4 tests (pre-flight gate, approval propagation, rejection handling)
- Integration with Observer Layer: 3 tests (decision recording, audit log integrity)
- Integration with Phase 10 (Context): 4 tests (context enrichment, tenant isolation, missing context)

### Security Review

- [ ] No eval/exec patterns — the existing implementation uses eval() with restricted globals. This must be replaced with a safe expression evaluator.
- [ ] No credential leakage — verify that the Governance Engine never reads environment variables containing secrets.
- [ ] Input validation — all input fields are validated before processing.
- [ ] Output sanitization — verdict explanations do not leak internal policy details.

### Performance

- Latency budget: 50ms p50, 200ms p99 (excluding human review wait time)
- Memory budget: 256MB steady-state, 512MB peak
- Concurrent capacity: 100 evaluations/second per instance

---

## 14. Security

### Tenant Isolation

Every policy evaluation is scoped to a tenant. Policies are registered with `tenant_id` or marked as `GLOBAL` (applies to all tenants). A tenant's policies never leak into another tenant's evaluation. The context enrichment step enriches per-tenant data only.

### Auditability

Every governance decision produces an immutable audit record containing:

- Unique audit_id
- Full input context (frozen at decision time)
- All policies evaluated and their results
- Final verdict
- Timestamp
- Evaluating instance identity

The audit log is append-only. No record is ever deleted or modified.

### Immutability

Audit records are never modified after creation. If a policy change would produce a different result for the same input, the old result remains in the audit log. New evaluations use the new policies.

### No Credential Access

The Governance Engine never reads:

- API tokens or secrets
- Database passwords
- Encryption keys
- Payment gateway credentials
- OAuth tokens

It has no access to any credential store. The input context may contain credential references (e.g., "source_id: 42"), but the Governance Engine never resolves them.

---

## 15. Constitutional Mapping

| Responsibility | Constitutional Principle | Source |
|---------------|------------------------|--------|
| Validate every action before execution | 6.6 Governance Before Execution | SHUNYA_ARCHITECTURE.md §6.6 |
| Can stop execution even if Reasoning made a bad recommendation | 2.5 Architectural Trust Over Perimeter Security | SHUNYA_ARCHITECTURE.md §2.5 |
| Return APPROVE / REVIEW / REJECT | 2.3 AI Proposes, Humans Dispose | SHUNYA_ARCHITECTURE.md §2.3 |
| Policy check against business rules | 6.3 Governance Layer — Policy check | SHUNYA_ARCHITECTURE.md §5 (Governance Layer) |
| Permission check for authority | 6.3 Governance Layer — Permission check | SHUNYA_ARCHITECTURE.md §5 (Governance Layer) |
| Workflow validation for plan sequencing | 6.3 Governance Layer — Workflow validation | SHUNYA_ARCHITECTURE.md §5 (Governance Layer) |
| Evidence verification | 6.5 Explainable Decisions | SHUNYA_ARCHITECTURE.md §6.5 |
| No single component can independently compromise execution | 6.1 Separation of Responsibilities | SHUNYA_ARCHITECTURE.md §6.1 |
| Audit trail for all governance decisions | 5.3 Governance Audit Trail | SHUNYA_ENGINEERING_CONSTITUTION.md §5.3 |
| Tenants are isolated in policy evaluation | Multi-tenancy requirement | SHUNYA_ARCHITECTURE.md §7 (Universal Ambition) |

---

## 16. Layer Responsibilities

### What the Governance Engine Does

- Validates proposed actions against constitutional principles
- Evaluates registered business policies
- Enriches context with computed fields
- Returns structured verdicts
- Maintains an immutable audit trail
- Enforces tenant isolation

### What the Governance Engine May Never Do

| Prohibited Action | Rationale | Belongs To |
|-------------------|-----------|------------|
| Never execute actions | Would violate Separation of Responsibilities | Executor Layer |
| Never mutate knowledge | Would violate Immutability and Traceability | Knowledge Layer / Immutable Knowledge Store |
| Never reason on behalf of the Reasoning Layer | Would violate Layer Boundaries | Reasoning Layer |
| Never access credentials | Would violate Least Authority Principle | Credential Store / Adapter Layer |
| Never generate plans or proposals | Would violate Layer Boundaries | Planner Layer |
| Never learn from outcomes | Would violate Layer Boundaries | Learning Layer |
| Never observe reality | Would violate Layer Boundaries | Observer Layer |
| Never make human-level judgments | Would violate Human Dignity Principle | Human decision-makers |
| Never modify its own policies | Would violate Auditability | Constitutional administration |
| Never compute relevance or attention | Would violate Layer Boundaries | Phase 13 (Relevance) |

---

## 17. Future Extensions

The following capabilities are anticipated but not specified for implementation. They are documented here to inform the architecture and avoid design decisions that would preclude them.

### 17.1 Policy Authoring Workflow

A future interface for defining, testing, and deploying governance policies through a structured workflow — including version control, staging environments, and approval gates before a policy becomes active.

### 17.2 A/B Policy Testing

The ability to run two policy sets in parallel, directing a percentage of traffic to each, and measuring the impact on approval rates, execution outcomes, and user satisfaction.

### 17.3 Policy Composition and Inheritance

Support for composing policies from sub-policies, inheriting policies from parent tenants, and overriding policies at the child-tenant level without copying.

### 17.4 Machine-Readable Policy Export

Exporting the active policy set in a machine-readable format (JSON Schema, OPA Rego, or similar) for external audit, verification, and integration with third-party compliance tooling.

### 17.5 Policy Impact Simulation

A sandbox mode where a proposed policy change can be evaluated against a historical sample of proposals to predict its impact on approval rates before deployment.

### 17.7 Cross-Engine Governance

Extending governance validation to cover cross-engine workflows — e.g., validating that a plan produced by the Planner, when executed through the Workflow Engine, respects all applicable policies at every step.

### 17.8 Constitutional Rule Engine

A dedicated subsystem for encoding and enforcing SHUNYA Constitution principles as first-class, immutable rules that cannot be overridden by business policies — providing a hard separation between constitutional rules and business policies.

---

## 18. References

- [SHUNYA_ARCHITECTURE.md](/SHUNYA_ARCHITECTURE.md) — Sections 2.3, 2.5, 5 (Governance Layer), 6.1, 6.3, 6.5, 6.6
- [SHUNYA_ENGINEERING_CONSTITUTION.md](/governance/SHUNYA_ENGINEERING_CONSTITUTION.md) — Articles 1, 5, 8
- [SHUNYA_GOVERNANCE_MODEL.md](/governance/SHUNYA_GOVERNANCE_MODEL.md) — Roles, decision types, approval hierarchy
- [VERIFICATION_CHECKLIST.md](/governance/verification/VERIFICATION_CHECKLIST.md) — Standard verification protocol
- [GOVERNANCE_CHANGELOG.md](/governance/GOVERNANCE_CHANGELOG.md) — Governance change history
- `app/shunya/governance.py` — Current GovernanceLayer implementation (411 lines)
- `app/shunya/__init__.py` — Package exports including GovernanceLayer, GovernanceVerdict, Policy, PolicyRegistry, PolicySeverity, PolicyScope