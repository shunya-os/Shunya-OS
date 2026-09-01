# SHUNYA Execution Integrity Constitution

**Status:** Ratified — G1.1-R1
**Authority:** Supersedes informal development notes. Derived from SHUNYA Engineering Constitution.
**Purpose:** Prevent false architectural closure. Enforce evidence-driven milestone completion.
**Applies to:** Every future phase, every Hermes execution, every GPT directive, every developer commit.

---

## Rule 0 — THE FINAL EXECUTION PRINCIPLE

**BUILD IT. PROVE IT. CHALLENGE IT. FIX IT. THEN CLOSE IT.**

This is the single governing discipline of all SHUNYA development. Every phase, every milestone, every commit operates under this cycle:

| Step | Requirement |
|------|-------------|
| **BUILD IT** | Implement the intended architecture against the verified contract |
| **PROVE IT** | Exercise the real system journey; collect evidence at every layer |
| **CHALLENGE IT** | Conduct self-adversarial review (Rule 4). Ask what could be wrong. Attack your own assumptions |
| **FIX IT** | Remediate every discovered gap before proceeding to closure |
| **THEN CLOSE IT** | Only after BUILD→PROVE→CHALLENGE→FIX are complete, and all gates pass, declare closure |

Never:

```
Build it → test it → declare it done.
```

A passing test suite after a build is the *beginning* of verification, not the end. Closure without challenge is false closure.

---

## Rule 1 — GREEN IS NOT COMPLETE

A passing test suite is evidence only. Never declare architectural completion solely because:

- tests pass
- CI passes
- TypeScript passes
- build passes

Completion requires correspondence between:

```
INTENDED ARCHITECTURE
      ↓
IMPLEMENTATION
      ↓
DATABASE STATE
      ↓
RUNTIME BEHAVIOUR
      ↓
REAL CONSUMERS
      ↓
SECURITY BOUNDARY
      ↓
USER JOURNEY
      ↓
GIT/DEPLOYED STATE
```

Each layer must be independently verified. Passing tests at one layer do not substitute for verification at another.

---

## Rule 2 — IMPLEMENTATION ≠ INTENTION

These are never equivalent:

| Claim | Truth |
|-------|-------|
| migration function exists | ≠ migration executed |
| service exists | ≠ consumers migrated |
| endpoint exists | ≠ user journey works |
| table exists | ≠ canonical authority |
| test exists | ≠ requirement satisfied |
| commit exists | ≠ deployment verified |

Every claim of completion must be accompanied by evidence at every level where the claim is non-trivial.

---

## Rule 3 — NEVER PATCH THE ARCHITECTURE TO MAKE A TEST GREEN

When implementation and acceptance contract disagree:

1. Determine which is wrong — the implementation, the contract, or the architecture
2. Preserve the architectural intent
3. Fix the implementation where appropriate
4. Change the test only when the contract itself was legitimately wrong
5. Document that decision in an ADR

Never weaken:

- tenant isolation
- authorization
- provenance
- canonical authority
- data integrity
- execution semantics

merely to obtain a passing test.

---

## Rule 4 — SELF-ADVERSARIAL VERIFICATION

Before declaring any milestone complete, the executing agent must explicitly challenge its own implementation:

1. What assumption did I make?
2. Could that assumption be wrong?
3. Did I implement the requested thing or a shortcut?
4. Did I actually execute migrations?
5. Did I verify persisted state?
6. Did I verify every production consumer?
7. Could another path bypass this authority?
8. Could another tenant see this?
9. Could the frontend bypass this?
10. Does the running application actually exercise this?
11. What would cause me to reject my own implementation?

This is mandatory. Every answer must be recorded in the closure evidence.

---

## Rule 5 — REAL STATE OVER REPORT STATE

When these disagree:

- report
- tests
- documentation
- database
- runtime
- Git

the lower-level observed truth wins. A database query is more true than a test assertion. A runtime observation is more true than a test assertion. A Git SHA on the remote is more true than a local commit.

Never mark a milestone complete merely because a previous report says it is complete. Re-verify independently.

---

## Rule 6 — FALSE CLOSURE IS A BREACH OF INTEGRITY

Declaring a milestone complete when mandatory acceptance gates remain unresolved is a breach of constitutional integrity. Acceptable closure statuses are:

- **PASS** — all gates verified independently
- **FAIL** — one or more gates failed
- **BLOCKED** — a dependency is unresolved
- **UNVERIFIED** — evidence not yet collected

Never acceptable:

- *probably complete*
- *substantially complete*
- *effectively complete*
- *functionally complete*

for certification purposes.

---

## Rule 7 — EVERY CLOSURE REQUIRES GIT TRUTH

Completion requires:

```text
tests PASS
+ validator PASS
+ working tree CLEAN
+ commit
+ push
+ remote SHA verified
+ HEAD == origin/main (or origin/master)
```

No exception. If the remote cannot be verified, the milestone is UNVERIFIED, not PASS.

---

## Rule 8 — PERMANENT INSTITUTIONAL MEMORY

Every structural failure pattern discovered during a phase MUST be recorded in:

`docs/governance/KNOWN_EXECUTION_FAILURE_PATTERNS.md`

This is not optional. The register is the development system's institutional memory. Future phases must review it before beginning execution.

---

## Enforcement

This constitution is enforced by:

1. **Machine-readable rules** — `governance/execution_integrity.yaml`
2. **Automated validator** — `scripts/validate_milestone.py`
3. **Milestone tracker** — `governance/milestone_tracker.yaml`
4. **CI integration** — validation step in `.github/workflows/ci.yml`
5. **Executive override required** — the Founder may override any gate by recording the override and the reason in the milestone evidence

Any override must be:
- Explicitly documented in the milestone closure
- Accompanied by the specific risk accepted
- Subject to re-verification at the next phase