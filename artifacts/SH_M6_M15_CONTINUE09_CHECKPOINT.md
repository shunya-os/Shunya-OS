# SH-M9→M6 CONTINUE-09 CHECKPOINT — HOME ATTENTION → HUMAN ACTION → M9 CLOSURE

Date: 2026-10-08 (session CONTINUE-09)
Candidate SHAs: 170c28f (review action + focus-surface wire) → 4cbae91 (landing HOME integration)
→ 026f2b1 (CI fix: reviewItems mock contract + defensive read)
Certified product SHA: 026f2b1 · CI run 37848178854 (test + deploy SUCCESS) · deployed 2026-10-08 22:01:36Z

## What was built (this session)

1. **Human review action (backend)** — `POST /api/v1/attention/<id>/confirm-review`.
   Canonical prior context: the ingestion is a transient event; the durable canonical record for an
   ingestion-review item IS the item itself. The action persists the human decision as canonical
   state (`provenance.review_decision`: decision/decided_by/decided_at/source_event_id), resolves
   the item in the same transaction, and emits a canonical `attention:review_confirmed` event on
   the EventBus (non-fatal). Tenancy identical to resolve: 404 / 403-with-detail / 409 conflicts.
   Tests: `tests/test_attention_review_action.py` (5) — decision persisted + resolved + auditable;
   anonymous refused; wrong-tenant 403 with detail; already-resolved 409; non-review 409.

2. **One canonical frontend consumption path** — `frontend/src/api/attention-api.ts`
   (fetchAttentionItems / confirmAttentionReview / dismissAttentionItem) over `fetchWithAuth`
   (credentials + X-Identity-Id carrier). Consumed by:
   - **home-store.ts** → `reviewItems` (loaded with the existing 30s list cadence; keep-last on
     failure + truthful error banner; never fabricates).
   - **home-page.tsx (THE landing surface)** → "NEEDS YOUR ATTENTION" section now shows canonical
     persisted AttentionItems above execution-task rows; count/greeting/pulse/capabilities include
     them truthfully. Row click opens an inline review block: "Confirm review" (canonical decision)
     and "Set aside" (canonical dismiss). Success → refresh from server truth; 403/409/404 →
     truthful inline text; stale UI self-heals.
   - **executive-home.tsx (PrimaryFocusArea/WhatMattersNow)** — same module. NOTE: this file's
     PrimaryFocusArea was previously classified LEGACY (dead code within active file) by the
     product audit; it renders only as the DomainWorkspaceRouter fallback. The real post-login
     landing is home-page.tsx (DomainWorkspaceRouter !active / home). The landing integration is
     the load-bearing one for the user journey.

3. **A11y (measured, not redesigned)** — `:focus-visible` gold outline (2px, verified computed
   `solid 2px rgb(164,134,95)` via real Tab presses), 44px touch targets on coarse pointers
   (measured 44px at 390/768), primary button #70583D/#fff ≈ 6.7:1 contrast. Calm fallback on API
   failure — no dead end, retry banner, recovery from server truth.

## Evidence chain (all layers)

- CI: run 37848178854 SUCCESS (test + deploy) for 026f2b1; production health: backend & frontend
  release 026f2b1, build_identity_matches_running_build=true, database connected.
- Runtime (HTTPS, cert tenant): 10/10 closure checks (schedule C0-C9) — artifacts/M9_RUNTIME_PROOF.txt
- Restart survival: item 7 created pre-restart → survived the 026f2b1 deploy restart, correct
  tenant, resolvable, resolved truth persisted (6/6, R0-R5).
- Browser/user journey (founder org 7, real login): item visible (traceable row: reason + ingestion
  id + "From a real business event (ingestion:csv)") → open → "Confirm review" → item resolved +
  decision persisted with the founder's identity → refresh continuity → logout/login continuity →
  cross-tenant 403 in-browser → stale re-action 409.
  Evidence: artifacts/M9_BROWSER_JOURNEY_EVIDENCE.txt · screenshot: artifacts/M9_HOME_FINAL_STATE.png
- DB (independent read-only): items 5/6/7 org-correct, resolved, decision provenance intact,
  zero active items.
- Failure/recovery UI: blocked attention API → truthful reconnecting banner + Retry, no fake item,
  no dead end; unblock → item returns from server truth (no manual DB op).

## Findings surfaced (not silently patched)

- No visible logout control in the SPA (user chip opens nothing; no "Log out" string in the app).
  Logout works via the canonical `/logout` endpoint (used in the journey). Product gap — flag for
  the founder; not redesigned here.
- The SPA's Root URL stays `/auth/login` after sign-in until later navigation code runs; a refresh
  at `/` restores the workspace via sessionStorage/cookie. Observed, reported, not redesigned.
- `PrimaryFocusArea` (previously classified LEGACY) now consumes the canonical attention client —
  harmless; left in place, documented.

## What is proven (layer discipline)

- IMPLEMENTED + TESTED: review action (unit+integration), store/client integration.
- CI VERIFIED: 37848178854.
- RUNTIME VERIFIED: C0-C9 over HTTPS on the deployed build.
- BROWSER VERIFIED: item visibility, open, action, resolution, refresh, logout/login, cross-tenant.
- USER-JOURNEY VERIFIED: the complete loop (event → Home row → human confirmation → canonical state
  change → resolution → continuity).
- RESTART VERIFIED (item 7 across the 026f2b1 restart; resolved truth after logout/login).
- FAILURE/RECOVERY VERIFIED (blocked transport; truthful states; recovery).
- TENANCY VERIFIED (cross-tenant 403 in browser + app-level; anonymous 401).
- ACCESSIBILITY/RESPONSIVE: measured at 3 breakpoints (keyboard focus, focus ring, 44px targets,
  contrast) — not a full WCAG certification.

## Remaining gaps / honesty

- Realtime: attention visibility is refresh-based (load + 30s list cadence + post-action refresh).
  The living presence SSE remains for awareness; no attention push was invented. Documented per
  directive §9 (do not replace refresh model casually).
- PrimaryFocusArea branch (legacy surface) not browser-exercised (router fallback path); landing
  surface (the real one) is browser-exercised.
- M6 semantic ingestion: NOT STARTED (was blocked until M9; the contract is frozen in the
  directive §18-22 and becomes the next execution block).
