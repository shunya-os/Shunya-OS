# SH-M6→M15 CONTINUE-14 CHECKPOINT — STAGES H (live probes) & I (device audit)

Date: 2026-10-09. Build: c12ffaf (CI-20; /health verified). Docs commit 01b8cfe
(CI-21) in flight at writing; this file rides the next run.

## Stage H — live failure/recovery probes (in addition to CONTINUE-13's matrix)

- Authentication failure: signed out (live), submitted a deliberately wrong
  credential → the login page reports "Invalid email or password", no session
  is created, and the surface stays on login. Recovery: correct sign-in via
  the vaulted credential → workspace restored, URL normalizes to '/'.
  No fake success; no crash; the standard non-enumerating message.
- (Matrix in CONTINUE-13 covers the remaining classes with per-item evidence:
  ingestion, extraction, authorization, events, attention, files, partial
  execution, deployment/restart.)

## Stage I — device & interaction audit (measured, not asserted)

Viewport sweep on the deployed build (CDP device emulation), each checked for
horizontal overflow and control visibility:

| Surface | Desktop 1440 | Tablet 834 | Mobile 390 |
|---|---|---|---|
| Home (+ Sign out control) | clean, visible | clean, visible | clean, visible |
| Relationships (rows render) | — | — | clean |
| Documents | — | — | clean |
| Commercial | — | — | clean |
| Content Studio | — | — | clean |
| Import panel (open) | — | — | clean |

- Viewport meta: `width=device-width, initial-scale=1.0` present.
- Keyboard: Tab traversal reaches the sidebar controls in order
  (Collapse → Home → People → …); the new Sign out control is a native button
  with a focus-visible outline (2px accent, offset 2).
- Contrast (alpha-blended computation): Sign out text 5.37:1 on the Home
  background — passes WCAG AA for normal text.
- Screenshots: STAGE_I_MOBILE_HOME.png, STAGE_I_MOBILE_RELATIONSHIPS.png,
  STAGE_I_MOBILE_IMPORT.png.
- Known limits (unchanged, explicit): these are measurements, not a WCAG
  certification; attention visibility remains refresh-based.

## Defects closed in this block

- Sign out called a nonexistent route (CI-19 contract test) → fixed to
  /founder/logout; verified live end-to-end (session actually cleared).
- Sign out control added to Home (the M9 known limitation).
- URL-after-sign-in normalizes to '/' (verified repeatedly live).
- Chat execute/automate no longer fabricate success (CI-19).
- Human context now changes behavior (Stage G, CONTINUE-13).