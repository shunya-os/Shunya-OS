# SHUNYA Known Execution Failure Patterns

*Institutional memory. Every structural failure discovered during a phase is recorded here permanently.
Future phases MUST review this register before beginning execution.*

---

## G1.1 — Canonical Convergence Phase

### Failure 1: JSONB used as tenancy security boundary

**Incident:**
`sh_objects` originally stored `organization_id` as a JSONB field inside `metadata`. There was no dedicated column, no foreign key, no database-level constraint. Tenant isolation relied entirely on application-level filtering of JSONB data.

**Correct Principle:**
Security ownership must be explicit and relational/enforced. Every cross-tenant attribute requires:
- A dedicated database column (not JSONB)
- A foreign key constraint
- A database index
- Runtime verification of isolation

**Fix Applied:**
Added real `organization_id` column to `sh_objects` with FK → `sh_workspaces`, plus backfill migration.

---

### Failure 2: Migration function created but migration not executed

**Incident:**
Alembic migration `g1_1_r1_organization_chain` was created with proper logic but was never executed against the database. The service code expected the column to exist, but the database didn't have it.

**Correct Principle:**
Implementation + execution + reconciliation. Creating a migration is not the same as running it. Verifying the migration ran is not the same as verifying the schema matches expectations. All three are required:
1. Create the migration
2. Execute it
3. Reconcile: inspect the actual database schema and row counts

**Fix Applied:**
Executed the migration. Verified column exists, FK exists, rows are backfilled.

---

### Failure 3: Tests modified to fit implementation

**Incident:**
Tests were relaxed to match the existing (incorrect) implementation rather than holding the implementation to the architectural contract. Specifically, tenant isolation tests were adjusted to pass when the architecture required stricter isolation.

**Correct Principle:**
Contract first; implementation follows contract. When implementation and acceptance contract disagree:
- Determine which is wrong
- Preserve architectural intent
- Fix the implementation (not the test)
- Change the test only when the contract itself was legitimately wrong
- Document that decision

---

### Failure 4: New canonical service created but consumers not migrated

**Incident:**
`IdentityResolutionService` was created as the canonical identity authority. However, approximately 30 production consumer sites continued to use direct `TeamMember` / `OrgMember` ORM queries, creating competing identity resolution paths.

**Correct Principle:**
Canonical authority requires consumer convergence. Creating a service is not sufficient — every production consumer must be migrated away from the duplicate path. The canonical service becomes canonical only when it is the *only* path.

**Fix Applied:**
Audited all consumers. Documented which are canonical, which are legitimate low-level repository access, and which must be refactored.

---

### Failure 5: Green regression suite interpreted as architectural completion

**Incident:**
After introducing the `IdentityResolutionService`, the existing test suite continued to pass. This was presented as evidence of architectural completion. However, the tests exercised the old code paths, not the new canonical service. The green suite was independent of the architectural change.

**Correct Principle:**
Tests are evidence, not certification. A passing regression suite proves only that existing behaviour was not regressed. It does NOT prove:
- That the new architectural intent is correctly implemented
- That all consumers use the canonical path
- That the security boundary holds
- That real user journeys work

Architectural completion requires a new suite of tests that exercise the *intended* architecture, not merely the *existing* behaviour.

---

### Failure 6: Build → Test → Declare without push + remote verification

**Incident:**
G1.1-R1 was declared PASS in the milestone tracker before the commit was pushed to remote and before remote SHA was verified. Closure was asserted based on local state alone. The working tree was clean and tests passed locally, but `HEAD != origin/master` and `git push` had not been executed.

**Correct Principle:**
Closure without remote verification is not closure. Completion requires:
- tests PASS
- validator PASS
- working tree CLEAN
- commit
- push
- remote SHA verified (HEAD == origin/master)
- PART N self-rejection checklist complete

**Fix Applied:**
Reset tracker to UNVERIFIED. Completed push + remote verification. The execution integrity constitution now includes Rule 0 (Final Execution Principle) and Rule 7 (Git Truth) to prevent recurrence.

---

## Generic Patterns (All Phases)

### Pattern: Implementation-only closure

Asserting completion because code was written, without verifying: database state, runtime behaviour, consumer migration, security boundary, Git truth.

**Prevention:**
Install the Execution Integrity Constitution as a permanent control. Run `scripts/validate_milestone.py` before declaring closure.

### Pattern: Report-acceptance without re-verification

Accepting a previous report's closure assertion instead of independently re-verifying.

**Prevention:**
Rule 5 — Real State Over Report State. Every gate opener must independently verify, not inherit.

### Pattern: Single-layer testing

Testing only at the unit level and claiming end-to-end completion.

**Prevention:**
All 8 closure layers must have evidence.

---

## How to Use This Register

1. Before beginning any new phase, read this entire document
2. Check if any previously discovered pattern applies to the current work
3. If a new pattern is discovered during the phase, add it before closure
4. Reference the relevant patterns in your self-adversarial review (Rule 4)