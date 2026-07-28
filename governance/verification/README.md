# Verification

**Path:** `governance/verification/`

**Purpose:** Verification checklists and protocols for ensuring that every engine, phase, and architecture decision is implemented correctly and conforms to the Constitution.

---

## Principles

- **Verification is mandatory.** No engine is complete without a completed verification checklist.
- **Verification is evidence-based.** Every check must cite specific evidence — test outputs, code inspection, document review.
- **Verification is the gate to approval.** An implementation is not approved until its verification checklist is signed off.
- **Verification is not testing.** Testing is a prerequisite. Verification confirms that testing was adequate and that the implementation meets its specification.

---

## Verification Levels

| Level | Applies To | Requirements |
|-------|------------|--------------|
| L1 — Unit | Individual functions, classes | Unit tests covering all state transitions and error paths |
| L2 — Integration | Engine boundaries | Integration tests with real dependencies (or verified mocks) |
| L3 — System | Complete phases | End-to-end tests across the pipeline |
| L4 — Architecture | Cross-layer concerns | Architecture compliance review, ADR verification |

---

## Checklist

The standard verification checklist is defined in [`VERIFICATION_CHECKLIST.md`](./VERIFICATION_CHECKLIST.md).

Each engine spec may extend this checklist with engine-specific items.