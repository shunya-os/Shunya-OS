# LB-001 — Founder Acceptance Walkthrough (prepared 2026-10-13)

Executed by the founder against the **deployed production build** at
https://shunyaos.com. Every step records the observed result; acceptance is
explicit and signed, never inferred. `PUBLIC_LAUNCH_READY` flips only after
ALL steps pass AND the founder signs the acceptance line.

Target build: **SHA (fill post-deploy)** — verify first: `curl -sk
https://shunyaos.com/health | jq -r .backend_release_sha` must equal the
deployed SHA recorded below.

## A. Identity + tenancy (certification tenant `ws_certification`, org 278)

| # | Step | Expected | Observed |
|---|------|----------|----------|
| A1 | Login at https://shunyaos.com/login/password with certification credentials | 200, session cookie | |
| A2 | List workspaces: GET /api/v1/orgs/278/workspaces | 200, own workspaces only | |
| A3 | Cross-tenant probe: GET /api/v1/orgs/7/workspaces (same session) | **403 Forbidden** (B4 gate) | |
| A4 | Reality snapshot: GET /api/v1/reality | 200, own-org attention items only | |

## B. AI provider truth (B2)

| # | Step | Expected | Observed |
|---|------|----------|----------|
| B1 | GET /api/v1/content/providers | truthful tiers; NO `dummy` provider; HF = CREDITS_REQUIRED/outage; pollinations = ready | |
| B2 | GET /api/v1/media/status | huggingface + pollinations truthful | |
| B3 | Text generation (Content Studio → generate) | real content (>50 chars), provider+model named | |
| B4 | Image generation | real image via Pollinations (image_generated: true), fallback notice visible when HF down | |
| B5 | Capabilities: GET /api/v1/capabilities/summary | AVAILABLE/UNAVAILABLE with reasons; no fake statuses | |
| B6 | Failure probe: image generate with provider=huggingface | 500 with 402 CREDITS_REQUIRED surfaced, error_class present | |

## C. Data + analytics (B3/L1)

| # | Step | Expected | Observed |
|---|------|----------|----------|
| C1 | GET /api/v1/analytics/dashboard | 200 (was 500 pre-B3) | |
| C2 | Upload a document via Documents, then import a CSV with a NUL byte | NUL rejected truthfully (400 with clear message), no partial write | |

## D. Integrations + alerting (D8/E1)

| # | Step | Expected | Observed |
|---|------|----------|----------|
| D1 | Integration Hub → statuses read "Configured / Not configured" (no fake "Connected") | labels truthful | |
| D2 | GET /api/v1/integrations (v2) → email integration | status reflects real probe (connected only when verified) | |
| D3 | POST /api/v1/system/alerts/test (admin) | alert event fired + delivered (check inbox); then POST /api/v1/system/alerts → delivery_state=delivered | |

## E. Security/ops

| # | Step | Expected | Observed |
|---|------|----------|----------|
| E1 | GET /metrics without token | 403 | |
| E2 | GET /metrics with token | 200 | |
| E3 | GET /health (no auth) | 200 + status + sha (deploy contract) | |
| E4 | /api/v1/system/alerts without admin session | 401/403 | |
| E5 | Spoofed X-Identity-Id header (no session) on /api/v1/sales/pipeline | 401 (B16) | |

## F. UI/UX constitution check

| # | Step | Expected | Observed |
|---|------|----------|----------|
| F1 | Content Studio page: provider status chips truthful; fallback note renders | matches design | |
| F2 | Integration Hub: badges "Configured/Not configured", timestamps "Updated" | matches design | |
| F3 | Overall layout/behavior on the four screens above | no regression vs launch screenshots | |

## G. Certification record

- Target SHA (must match /health): ______________
- Walkthrough date: ______________
- All A1–F3 results: PASS / issues noted (list): ______________
- Known negatives verified as truthful (HF outage, video/embeddings UNAVAILABLE):
  accepted as PROVIDER DEPENDENCIES: yes/no — ______________

**FOUNDER ACCEPTANCE (explicit):** I, Nishesh, have walked through the
deployed build and accept the current launch gate state (known negatives
documented; remaining founder decisions D1–D12 recorded in the master
register). PUBLIC_LAUNCH_READY may be set to TRUE only when this line is
signed and the register's mandatory gates are all verified.

Signature: ______________  Date: ______________

(Until signed: PUBLIC_LAUNCH_READY = FALSE is the default state.)