# SHUNYA v1.0 — Convergence Plan

Generated: 2026-07-26
Status: Awaiting approval

## Overview

This plan describes every code change needed to converge SHUNYA into one canonical product.
No changes will be made until this plan is approved.

---

## Phase A: Constitutional Compliance (High Priority)

### A1. Cinematic Homepage (3 missing principles)

**What:** Replace the minimal login page with a cinematic landing experience that explains SHUNYA's philosophy, shows the शून्य identity, and emotionally introduces the operating system concept.

**Files:**
- `frontend/src/components/auth/login-page.tsx` — rewrite to include brand narrative, tagline, the "zero" concept
- `frontend/src/app.tsx` — update boot screen to show brand identity

**Constitutional principles recovered:**
- Emotional introduction
- शून्य identity prominent
- Storytelling before login
- Single OS philosophy

**Risk:** Low — self-contained UI change, no backend impact.

### A2. Founder-First Onboarding (3 missing principles)

**What:** Add first-run guidance when no data exists. The empty state should explain what SHUNYA is, suggest creating a first relationship, and guide the founder toward meaningful work.

**Files:**
- `frontend/src/components/workspace/workspace-container.tsx` — enhance empty state
- `frontend/src/runtimes/modules/business.ts` — add onboarding guidance to empty state panels

**Constitutional principles recovered:**
- Founder should never need documentation
- 30-minute uninterrupted workflow

**Risk:** Low — extends existing empty state handling.

### A3. Calm Workspace (3 missing principles)

**What:** Add CSS transitions between workspace switches, enforce 70/20/10 spacing through the token system, add focus management.

**Files:**
- `frontend/src/tokens/definitions.ts` — add spacing tokens, transition tokens
- `frontend/src/components/workspace/workspace-container.tsx` — add transition classes
- `frontend/src/runtimes/experience/engine.ts` — wire focus preservation

**Constitutional principles recovered:**
- 70% whitespace, 20% context, 10% controls
- Smooth transitions
- Focus preservation

**Risk:** Low — no logic changes, CSS + tokens only.

### A4. Wire ⌘1-⌘9 Keyboard Shortcuts

**What:** Implement workspace switching via keyboard shortcuts. The hint is already shown but the handler is empty.

**Files:**
- `frontend/src/app.tsx` — implement shortcut handler
- `frontend/src/runtimes/workspace/store.ts` — expose workspace activation by index

**Constitutional principles recovered:**
- No misleading keyboard shortcuts

**Risk:** Low — self-contained, only affects keyboard handler.

---

## Phase B: Capability Convergence (Medium Priority)

### B1. Canonicalize Identity Model

**What:** The seed script creates `FounderSpace` objects with `identity_id` but the signin/session system doesn't return the matching identity_id. Fix the identity resolution so the seeded spaces appear in the API response.

**Files:**
- `app/founder/routes.py` — fix `api_list_spaces` to return spaces matching the signed-in identity
- `scripts/seed_demo.py` — ensure identity_id in seed matches signin identity

**Constitutional principles recovered:**
- Organization switching
- Returning founder

**Risk:** Medium — touches auth flow, must not break existing signin.

### B2. Surface Seeded Conversations

**What:** The demo environment seeds 11 conversations with AI summaries and messages, but the frontend doesn't display them. Add a conversation workspace that uses the founder objects API.

**Files:**
- `frontend/src/runtimes/modules/business.ts` — add conversation workspace registration
- `frontend/src/components/conversation/conversation-workspace.tsx` — wire to founder API

**Constitutional principles recovered:**
- Lifetime customer (every interaction preserved)
- AI as embedded layer

**Risk:** Low — extends existing conversation workspace component.

### B3. Surface Commitment Timeline

**What:** Commitments have progression data and confidence factors, but the timeline isn't displayed. Add a timeline panel to the commitment workspace.

**Files:**
- `frontend/src/components/commitment/commitment-workspace.tsx` — add timeline section
- `frontend/src/runtimes/modules/business.ts` — pass timeline data to workspace

**Constitutional principles recovered:**
- AI confidence is transparent
- Object-centric interface

**Risk:** Low — UI-only change.

---

## Phase C: Repository Consolidation (Lower Priority)

### C1. Merge Duplicate Decision Runtimes

**What:** `app/decision/` and `app/decision_runtime/` overlap. Identify canonical implementation, redirect callers, deprecate the other.

**Files:** Analysis needed — likely 10+ files
**Risk:** Medium — unknown callers

### C2. Merge Organization Packages

**What:** `app/organization/` and `app/organizational/` overlap. Merge into `app/organizational/`.

**Files:** Analysis needed — likely 9+ files
**Risk:** Medium — unknown callers

### C3. Deprecate app/kernel/

**What:** `app/kernel/` overlaps with `app/shunya/`. Mark as deprecated, redirect any remaining callers.

**Files:** 10 files in app/kernel/
**Risk:** Low — likely unused

### C4. Merge Graph Packages

**What:** `app/graph/` and `app/graph_universal/` overlap. Merge into `app/graph_universal/`.

**Files:** Analysis needed — likely 15+ files
**Risk:** Medium — unknown callers

---

## Phase D: Production Polish

### D1. Install flask-cors

**What:** `pip install flask-cors` to eliminate the startup warning.

**Risk:** None

### D2. Add Frontend Tests

**What:** Add at least smoke tests for key components (login, search, workspace container).

**Files:** New test files under `frontend/tests/`

### D3. Auth Middleware Cleanup

**What:** The auth middleware exempt list is growing. Consolidate exempt paths.

**Files:** `app/__init__.py`

---

## Implementation Order

```
Phase A (Constitutional) → Phase B (Capability) → Phase C (Consolidation) → Phase D (Polish)
  Priority: High           Priority: Medium        Priority: Lower            Priority: Low
```

Each phase must be validated against the demonstration environment before proceeding.

---

## Validation Checklist

- [ ] Founder can log in, see seeded data, understand what SHUNYA is
- [ ] All constitutional principles classified as "implemented" or "partially implemented"
- [ ] No duplicate implementations remain
- [ ] All backend routes are exposed through the frontend or intentionally hidden
- [ ] Keyboard shortcuts work as advertised
- [ ] Workspace transitions are smooth
- [ ] AI Copilot knows the workspace context and seeded data
- [ ] 20 tests + new frontend tests pass
- [ ] No placeholder content, fake metrics, or dead-end interactions

---

## Estimated Effort

| Phase | Files | Estimated Time |
|-------|-------|---------------|
| A1: Cinematic homepage | 2 | 20 min |
| A2: Founder onboarding | 2 | 15 min |
| A3: Calm workspace | 3 | 20 min |
| A4: Keyboard shortcuts | 2 | 10 min |
| B1: Identity canonicalization | 2 | 20 min |
| B2: Conversation surface | 2 | 15 min |
| B3: Commitment timeline | 2 | 10 min |
| C1-C4: Repository consolidation | 30+ | 60 min (analysis-heavy) |
| D1-D3: Production polish | 3 | 15 min |
| **Total** | **~48** | **~3 hours** |

---

## Approve or Adjust

This plan is ready for your review. I will not begin implementation until you approve the full plan or request adjustments to the scope, order, or approach.