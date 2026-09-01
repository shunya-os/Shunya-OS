# SHUNYA PERMANENT EXECUTION RULES

> **Permanent governance artifact.** Saved by directive FCR-01.1-C. Every future Hermes session working on SHUNYA must read this before taking action. No directive may silently bypass these rules.

---

## 0. Authority

These rules are permanent. They govern every future Hermes session working on SHUNYA. No directive may silently bypass them.

## 1. Evidence Over Inference

A capability is VERIFIED only when the real user/system journey has been exercised and the resulting state has been independently checked. Never infer functional completion from:
- existence of a Python/TypeScript file
- existence of a route
- existence of a database table
- non-zero database rows
- unit tests alone
- frontend component existence
- an API returning 200

## 2. No False Closure

Do not classify anything as "maintenance" merely because it is inconvenient to fix. If a launch-promised capability is incomplete, it remains a launch blocker.

Do not mark an item closed because "the code is there." Every failed test must become a tracked remediation item. Every remediation item must map to a milestone/gate and acceptance criterion.

## 3. No Mock Success

Do not create mock success. Do not create fake integrations. Do not replace real end-to-end behaviour with placeholder/demo-only responses. Do not weaken tests, authentication, authorization, security or governance to make a test pass.

## 4. Orphan Classification

Every engine/runtime must receive an individual decision:
- CANONICAL + MUST CONNECT
- INTERNAL ONLY
- DUPLICATE → MERGE
- SUPERSEDED
- DEPRECATED
- REMOVE

Prove the classification. Do not wire every engine blindly simply because it exists.

## 5. Security First

Exposed credentials must be rotated immediately. Never print replacement credentials. Never place credentials directly in shell commands. Use the existing secure environment/secret mechanism.

## 6. Git Hygiene

Keep the repository clean. Commit only coherent changes. At every major checkpoint, record: current SHA, working tree, completed steps, remaining steps, blockers, next action.

## 7. 70-Step Completion

Do not declare FCR complete until the final 70-step matrix itself proves completion with every row having a result, every VERIFIED item having evidence, every failure having remediation, every maintenance classification being justified.

## 8. Construction Freeze

During FCR-01.1-C, do not begin FCR-02 construction. Do not close FCR-01.1. Do not declare any capability certified merely because code, routes, tables, or tests exist.

## 9. Preservation

Preserve all useful findings and documents already created. Do not throw away existing work merely to satisfy this directive. Do not repeat already-valid tests unnecessarily.

## 10. Final Decision

Only after completing the full 70-step evidence matrix, select exactly one:
- PATH A: CERTIFICATION READY
- PATH B: SURGICAL REMEDIATION REQUIRED
- PATH C: SYSTEMIC REMEDIATION REQUIRED

Choose from evidence, not intuition. Then STOP. Do not begin implementation automatically.