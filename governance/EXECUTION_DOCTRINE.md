# SHUNYA Permanent Execution Doctrine

**Version:** 1.0
**Status:** Ratified — G1.1-R5 (mandatory, permanent)
**Authority:** SHUNYA Constitution → Product Constitution → Technical Constitution → Design System → applicable governance documents
**Applies to:** ALL current and future SHUNYA development, migration, refactor, test, and remediation work. Not limited to G1.1-R5.

---

## 0. THE DOCTRINE

> **SHUNYA IS NOT BUILT TO MAKE TESTS GREEN. SHUNYA IS BUILT TO MAKE THE PRODUCT WORK.**

No implementation may be considered complete merely because:

- code compiles;
- an endpoint returns 200;
- a targeted test passes;
- a database table exists;
- a row count increases;
- a mock succeeds;
- a placeholder is present;
- a frontend component renders;
- a backend service exists;
- a feature appears in source code;
- a migration has been created;
- a local test suite is green.

A capability is complete **only when its intended user journey is fully wired end-to-end**:

```
User intent
→ UI interaction
→ authenticated context
→ canonical backend logic
→ canonical persistence
→ real processing
→ real outputs
→ visible state/progress
→ completion/failure state
→ evidence/trace
→ actionable result
→ next clickable/executable path
```

Every implementation must be backed by explicit product logic, domain logic,
persistence logic, security logic, failure handling, and user-facing behaviour.

- Green tests are **evidence**. They are not the definition of completion.
- Existence is not integration.
- Integration is not completion.
- Completion means the user can actually use the capability from beginning to
  end and receive the intended result without an artificial, broken, dead-end,
  placeholder, mock, hidden manual step, or unexplained transition.

## 1. THE QUESTIONS EVERY EXECUTION MUST ANSWER

For every task, before it may be called complete:

1. What does the user intend to accomplish?
2. Where does that intent enter SHUNYA?
3. Which canonical domain object represents it?
4. Which authenticated identity and organization/workspace context govern it?
5. What deterministic/business logic processes it?
6. What data does SHUNYA use?
7. Which company data is consulted?
8. Which internet data is consulted, if required?
9. Which AI/provider capability is used, if required?
10. Where is the state persisted?
11. How is progress represented?
12. How does the frontend observe that progress?
13. What happens on success?
14. What happens on failure?
15. What happens on timeout?
16. What happens if the operation is retried?
17. What evidence proves what happened?
18. What does the user see?
19. What can the user click/do next?
20. Does the journey continue naturally from that result?

**No task is complete until the complete journey has been demonstrated.**

## 2. EXECUTION RULES

1. **Product over green.** Tests are evidence, never the definition of completion.
2. **No fake progress.** SHUNYA must never display a lifecycle step that did not
   actually happen. No decorative progress, no hard-coded phases, no artificial
   timers, no pretending an LLM or internet source was consulted when it was not.
3. **Company data first.** Company data → internet data → AI/model inference.
   AI is never the source of truth for deterministic business facts.
4. **Persist where persistence is required.** An in-memory Python/dataclass
   representation must never silently become the authoritative source of truth
   for durable business execution.
5. **Deny-by-default security.** No hidden role fallback, no default
   administrator, no implicit founder privilege in ordinary request paths,
   no client-controlled authorization.
6. **Fail closed on uncertainty.** When canonical ownership cannot be determined,
   migrations conflict, or an end-to-end requirement cannot be truthfully
   demonstrated, the correct response is **BLOCK + EVIDENCE + EXPLANATION +
   NEXT REQUIRED DECISION** — never GUESS + IMPLEMENT + PASS.
7. **Mocks are never completion evidence.** Mocks may be used for isolated unit
   testing only. Never convert mock success → production readiness.
8. **No placeholder completion.** TODO, FIXME, placeholder APIs, dummy
   responses, hardcoded results, fake progress, simulated completion, static
   task trackers, decorative "AI thinking" animations, fake internet search,
   fake company retrieval, hardcoded durations, frontend-only state,
   backend-only implementations, and test-only implementations do not count as
   implementation. If such scaffolding is retained intentionally, classify it
   explicitly and identify the production completion gate.
9. **Every major feature is audited as a journey, not a component.**
   Entry → Input → Interpretation → Processing → Persistence → Progress →
   Result → Verification → Presentation → Next action → Related action →
   History → Recovery. A feature with a beautiful frontend and disconnected
   backend is FAIL. A functioning backend with inaccessible frontend is FAIL.
   No dead ends, no dead buttons, no "coming soon" placeholders unless
   explicitly approved as product scope.
10. **Restart-safe and failure-safe.** Apparently complete but not restart-safe,
    or not failure-safe, is not complete.
11. **One coherent SHUNYA system.** Competing runtime truths for the same
    conceptual object are forbidden. Every legacy system must be classified:
    CANONICAL / TRANSITIONAL / ADAPTER / READ-ONLY LEGACY / QUARANTINED /
    DECOMMISSIONED / DEAD CODE. No ambiguous "still used somewhere" status.
12. **SHUNYA must feel alive because meaningful work is happening**, through
    truthful pulse, heartbeat, presence, and real-time activity — not because
    decorative effects were added. No gratuitous animation.

## 3. CLASSIFICATION OF STATUS LANGUAGE

Only one of these may be used for any requirement:

- **PASS** — implemented, integrated, exercised, and evidenced.
- **PARTIAL** — some implementation exists but complete acceptance is not proven.
- **BLOCKED** — cannot be verified/completed due to explicit dependency,
  infrastructure, or decision blocker.
- **FAIL** — tested and does not meet acceptance.
- **QUARANTINED** — legacy/non-canonical implementation isolated and explicitly
  excluded from authoritative runtime.
- **NOT APPLICABLE** — genuinely does not apply, with justification.

"Basically done", "functionally done", "should work", "implemented but not
tested", "green locally" must NEVER be used as substitutes for acceptance status.

## 4. RELATIONSHIP TO OTHER DOCUMENTS

- This doctrine is recorded in `governance/EXECUTION_DOCTRINE.md` and is
  referenced by the Engineering Constitution (`governance/SHUNYA_ENGINEERING_CONSTITUTION.md`).
- It does not override the SHUNYA Constitution, Product Constitution, or
  UI/UX Constitution. It operationalizes the existing constitutional
  requirement that SHUNYA must be a working product, not a collection of
  green subsystems.
- All future milestones (G1.1-FINAL, G1.2, G2, and beyond) inherit this doctrine.

---

*Recorded 2026-09-08 during G1.1-R5 execution. Permanent. Applies to every future execution.*