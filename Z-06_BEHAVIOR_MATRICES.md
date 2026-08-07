# Universal Behavior Matrix

**Directive:** Z-06
**Purpose:** Map every ontology object against the constitutional behavioural contract.
**Status:** Compliance Audit — Pre-Refactoring

---

## Behavior Matrix

| Ontology Object | Created | Discovery | Ownership | Relationships | History | Search | Observation | Permissions | Versioning | Timeline | Execution | AI | Audit | Deletion | Recovery |
|-----------------|---------|-----------|-----------|---------------|---------|--------|-------------|-------------|------------|----------|-----------|-----|-------|----------|----------|
| Identity(Person) | ✅ Kernel | ✅ Kernel | ✅ Kernel | ✅ Kernel | ⚠️ Custom | ⚠️ Per-model | ❌ None | ⚠️ Basic | ❌ None | ❌ None | ❌ None | ⚠️ Basic | ⚠️ ActivityLog | ❌ None | ❌ None |
| Identity(Organization) | ✅ Kernel | ✅ Kernel | ✅ Kernel | ✅ Kernel | ⚠️ Custom | ⚠️ Per-model | ❌ None | ⚠️ Basic | ❌ None | ❌ None | ❌ None | ⚠️ Basic | ⚠️ ActivityLog | ❌ None | ❌ None |
| Relationship | ✅ Kernel | ✅ Kernel | ✅ Kernel | N/A (is relationship) | ⚠️ Custom | ⚠️ Per-model | ❌ None | ✅ Kernel | ❌ None | ❌ None | ❌ None | ❌ None | ⚠️ ActivityLog | ❌ None | ❌ None |
| Commitment(Customer) | ❌ Custom | ❌ Custom | ✅ Kernel | ❌ Hardcoded | ❌ None | ⚠️ Basic | ❌ None | ⚠️ Basic | ❌ None | ❌ None | ❌ None | ❌ None | ⚠️ ActivityLog | ❌ None | ❌ None |
| Commitment(Invoice) | ❌ Custom | ❌ Custom | ✅ Kernel | ❌ Hardcoded | ❌ None | ⚠️ Basic | ❌ None | ⚠️ Basic | ❌ None | ❌ None | ❌ None | ❌ None | ⚠️ ActivityLog | ❌ None | ❌ None |
| Commitment(Proposal) | ❌ Custom | ❌ Custom | ✅ Kernel | ❌ Hardcoded | ❌ None | ⚠️ Basic | ❌ None | ⚠️ Basic | ❌ None | ❌ None | ❌ None | ❌ None | ⚠️ ActivityLog | ❌ None | ❌ None |
| Commitment(Task) | ❌ Custom | ❌ Custom | ✅ Kernel | ❌ Hardcoded | ❌ None | ⚠️ Basic | ❌ None | ⚠️ Basic | ❌ None | ❌ None | ❌ None | ❌ None | ⚠️ ActivityLog | ❌ None | ❌ None |
| Commitment(Lead) | ❌ Custom | ❌ Custom | ✅ Kernel | ❌ Hardcoded | ❌ None | ⚠️ Basic | ❌ None | ⚠️ Basic | ❌ None | ❌ None | ❌ None | ❌ None | ⚠️ ActivityLog | ❌ None | ❌ None |
| Financial Record(Payment) | ❌ Custom | ❌ Custom | ✅ Kernel | ❌ Hardcoded | ❌ None | ⚠️ Basic | ❌ None | ⚠️ Basic | ❌ None | ❌ None | ❌ None | ❌ None | ⚠️ ActivityLog | ❌ None | ❌ None |
| Document | ❌ Custom | ❌ Custom | ✅ Kernel | ❌ Hardcoded | ❌ None | ⚠️ Basic | ❌ None | ⚠️ Basic | ❌ None | ❌ None | ❌ None | ❌ None | ⚠️ ActivityLog | ❌ None | ❌ None |
| Event | ❌ None | ❌ None | ❌ None | ❌ None | ❌ None | ❌ None | ❌ None | ❌ None | ❌ None | ❌ None | ❌ None | ❌ None | ❌ None | ❌ None | ❌ None |
| Knowledge | ❌ None | ❌ None | ❌ None | ❌ None | ❌ None | ❌ None | ❌ None | ❌ None | ❌ None | ❌ None | ❌ None | ❌ None | ❌ None | ❌ None | ❌ None |
| Observation | ❌ None | ❌ None | ❌ None | ❌ None | ❌ None | ❌ None | ❌ None | ❌ None | ❌ None | ❌ None | ❌ None | ❌ None | ❌ None | ❌ None | ❌ None |
| Decision | ❌ None | ❌ None | ❌ None | ❌ None | ❌ None | ❌ None | ❌ None | ❌ None | ❌ None | ❌ None | ❌ None | ❌ None | ❌ None | ❌ None | ❌ None |
| Memory | ❌ None | ❌ None | ❌ None | ❌ None | ❌ None | ❌ None | ❌ None | ❌ None | ❌ None | ❌ None | ❌ None | ❌ None | ❌ None | ❌ None | ❌ None |
| Place | ❌ None | ❌ None | ❌ None | ❌ None | ❌ None | ❌ None | ❌ None | ❌ None | ❌ None | ❌ None | ❌ None | ❌ None | ❌ None | ❌ None | ❌ None |
| Asset | ❌ None | ❌ None | ❌ None | ❌ None | ❌ None | ❌ None | ❌ None | ❌ None | ❌ None | ❌ None | ❌ None | ❌ None | ❌ None | ❌ None | ❌ None |
| Workflow | ❌ None | ❌ None | ❌ None | ❌ None | ❌ None | ❌ None | ❌ None | ❌ None | ❌ None | ❌ None | ❌ None | ❌ None | ❌ None | ❌ None | ❌ None |
| Communication | ❌ None | ❌ None | ❌ None | ❌ None | ❌ None | ❌ None | ❌ None | ❌ None | ❌ None | ❌ None | ❌ None | ❌ None | ❌ None | ❌ None | ❌ None |
| Capability | ❌ None | ❌ None | ❌ None | ❌ None | ❌ None | ❌ None | ❌ None | ❌ None | ❌ None | ❌ None | ❌ None | ❌ None | ❌ None | ❌ None | ❌ None |

**Legend:** ✅ = Kernel (constitutional contract) exists | ⚠️ = Partial/custom | ❌ = Missing entirely

---

## Lifecycle Matrix

| Object | Created | Identified | Understood | Related | Active | Observed | Updated | Executed | Completed | Archived | Recoverable | Deleted |
|--------|---------|------------|------------|---------|--------|----------|---------|----------|-----------|----------|-------------|---------|
| Identity(Person) | ✅ Kernel | ❌ None | ❌ None | ✅ Kernel | ✅ Kernel | ❌ None | ✅ Kernel | ❌ None | ❌ None | ❌ None | ❌ None | ❌ None |
| Customer | ✅ Custom | ❌ None | ❌ None | ❌ Hardcoded | ✅ Custom | ❌ None | ✅ Custom | ❌ None | ❌ None | ❌ None | ❌ None | ❌ None |
| Invoice | ✅ Custom | ❌ None | ❌ None | ❌ Hardcoded | ✅ Custom | ❌ None | ✅ Custom | ❌ None | ❌ None | ❌ None | ❌ None | ❌ None |
| Proposal | ✅ Custom | ❌ None | ❌ None | ❌ Hardcoded | ✅ Custom | ❌ None | ✅ Custom | ❌ None | ❌ None | ❌ None | ❌ None | ❌ None |
| Task | ✅ Custom | ❌ None | ❌ None | ❌ Hardcoded | ✅ Custom | ❌ None | ✅ Custom | ❌ None | ❌ None | ❌ None | ❌ None | ❌ None |
| Lead | ✅ Custom | ❌ None | ❌ None | ❌ Hardcoded | ✅ Custom | ❌ None | ✅ Custom | ❌ None | ❌ Custom | ❌ None | ❌ None | ❌ None |
| Payment | ✅ Custom | ❌ None | ❌ None | ❌ Hardcoded | ✅ Custom | ❌ None | ✅ Custom | ❌ None | ❌ None | ❌ None | ❌ None | ❌ None |

---

## Relationship Matrix

| Relationship | Current Implementation | Constitutional Required |
|-------------|----------------------|----------------------|
| Customer ↔ Proposal | Hardcoded `customer_id` on Proposal table | Graph: Relationship(source=customer, target=proposal, type="owns") |
| Proposal ↔ Invoice | Hardcoded `proposal_id` on Invoice table | Graph: Relationship(source=proposal, target=invoice, type="produces") |
| Invoice ↔ Payment | Hardcoded `invoice_id` on Payment table | Graph: Relationship(source=invoice, target=payment, type="receives") |
| Lead ↔ Activity | Hardcoded `lead_id` on ActivityLog table | Graph: Relationship(source=lead, target=activity, type="has") |
| Organization ↔ Member | Hardcoded `organization_id` on OrgMember table | Graph: Relationship(source=person, target=org, type="member_of") |
| Identity ↔ Space | Hardcoded `identity_id` on FounderSpace table | Graph: Relationship(source=identity, target=space, type="owns") |
| Object ↔ Space | Hardcoded `space_id` on FounderObject table | Graph: Relationship(source=space, target=object, type="contains") |

---

## Event Matrix

| Event Type | Current Implementation | Constitutional Required |
|------------|----------------------|----------------------|
| Created | ✅ ActivityLog (some objects) + ✅ Created fields | Immutable Event(type=created) on every object |
| Viewed | ❌ Not tracked | Immutable Event(type=viewed) |
| Edited | ⚠️ ActivityLog (lead only) + update timestamp | Immutable Event(type=edited) with previous state |
| Commented | ❌ Not tracked | Immutable Event(type=commented) |
| Shared | ❌ Not tracked | Immutable Event(type=shared) |
| Assigned | ⚠️ Manual field update | Immutable Event(type=assigned) |
| Mentioned | ❌ Not tracked | Immutable Event(type=mentioned) |
| Moved | ⚠️ ActivityLog (lead status) | Immutable Event(type=moved, state transition) |
| Approved | ❌ Not tracked | Immutable Event(type=approved) |
| Rejected | ❌ Not tracked | Immutable Event(type=rejected) |
| Executed | ❌ Not tracked | Immutable Event(type=executed) |
| Completed | ❌ Not tracked | Immutable Event(type=completed) |
| Archived | ❌ Not tracked | Immutable Event(type=archived) |
| Deleted | ❌ Not tracked | Immutable Event(type=deleted) |

---

## Summary

| Dimension | Objects Compliant | Objects Partially Compliant | Objects Non-Compliant | Total |
|-----------|-----------------|----------------------------|----------------------|-------|
| Behaviour Contract | 0 | 7 (Identity, Relationship via Kernel) | 13 | 20 |
| Universal Lifecycle | 0 | 0 | 20 | 20 |
| Graph Relationships | 0 | 0 | 20 | 20 |
| Universal Events | 0 | 0 | 20 | 20 |
| Universal Timelines | 0 | 0 | 20 | 20 |
| Universal Search | 0 | 0 | 20 | 20 |
| Universal Observation | 0 | 0 | 20 | 20 |
| Permissions (Graph) | 0 | 0 | 20 | 20 |
| Versioning | 0 | 0 | 20 | 20 |
| Object Execution | 0 | 0 | 20 | 20 |
| AI Understanding | 0 | 0 | 20 | 20 |
| Audit | 0 | 0 | 20 | 20 |

**Constitutional Compliance: 0%**

This is expected — the constitution is newly ratified. The matrices document the gap that Genesis Reset must close.