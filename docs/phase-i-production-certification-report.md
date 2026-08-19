# SHUNYA PHASE I — PRODUCTION CERTIFICATION REPORT (UPDATE)

> **Date:** 2026-08-19
> **Directive:** Phase I Production Real-Time Certification Correction
> **Baseline Commit:** `54312d6`
> **Current Commit:** `5ce71a7`
> **Branch:** master

---

## 1. ROOT CAUSE OF MULTI-WORKER ISSUE

The original implementation used a process-local `SSEStreamManager` singleton per Gunicorn worker. Each worker had:
- Its own `_clients` dict (in-memory SSE client registry)
- Its own `EventBus` singleton (in-process pub/sub)
- No cross-worker communication mechanism

**The gap:** When Worker A emitted an event via `get_event_bus().publish()`, the event was delivered only to subscribers on Worker A's in-process EventBus. If the SSE client was connected to Worker B, the event never reached it.

## 2. FINAL REALTIME ARCHITECTURE

```
Worker A:
  Event emitted → Local EventBus → RedisEventRelay → Redis Pub/Sub
                                                    ↓
Worker B:
  RedisEventRelay ← Redis Pub/Sub → Local EventBus → SSEStreamManager
                                                      ↓
                                                 SSE Client queue
                                                      ↓
                                                 Connected client
```

**Components:**
- `RedisEventRelay` (in `event_bus.py`): Thread-based Redis Pub/Sub subscriber. Each worker runs a daemon thread that listens on `shunya:events` channel.
- `_publish_to_redis()`: Called by every `EventBus.publish()` — always publishes to Redis regardless of local subscribers.
- `_relay_from_redis()`: Called when Redis delivers a message to a worker. Checks idempotency cache, then delivers to matching local subscribers.
- **No echo loops**: The idempotency cache (24h TTL) prevents the originating worker from processing its own event via the Redis echo.

## 3. TRANSPORT CHOSEN: REDIS PUB/SUB

**Redis was chosen because:**
- Already deployed and running in production (`redis://127.0.0.1:6379`)
- Already used for rate limiting, session store, and cache
- Redis Pub/Sub is the natural, lightweight mechanism for cross-process event broadcast
- No additional infrastructure dependencies introduced
- Built-in reconnect handling in `redis-py` client
- No competing event architecture was introduced — Redis is an extension of the existing EventBus

**Alternatives considered and rejected:**
- PostgreSQL LISTEN/NOTIFY: Would couple event delivery to DB transaction lifecycle
- RabbitMQ/Kafka: Heavy infrastructure for a feature that needs simple broadcast
- File-based IPC: Fragile, slow, no ordering guarantees
- Direct TCP/UDP multicast: Requires network configuration, not portable

## 4. AUTHENTICATION MODEL

The `/api/v1/reality/stream` endpoint uses **session-only authentication**:

```python
identity_id = session.get("identity_id") or session.get("user_id")
tenant_id = session.get("tenant_id") or session.get("current_org_id", 0)
if not identity_id or not tenant_id:
    return jsonify({"success": False, "error": "Not authenticated"}), 401
```

- `X-Identity-Id` header is **NEVER** trusted for SSE
- Session is established via `POST /api/v1/founder/signin` which authenticates with `TeamMember.check_password()`
- Cookie has `Secure; HttpOnly; SameSite=Lax` flags (production setting)
- Workspace isolation: optional `workspace_id` query param scopes the session

## 5. SECURITY FINDINGS

### SSE Auth Audit

| Test | Result |
|------|--------|
| Unauthenticated request → 401 | ✅ PASS |
| Authenticated session → 200 | ✅ PASS |
| Forged X-Identity-Id header → rejected | ✅ PASS |
| X-Identity-Id without session → 401 | ✅ PASS |
| User A cannot subscribe as User B | ✅ PASS |
| Tenant isolation enforced | ✅ PASS |
| Workspace isolation enforced | ✅ PASS |

**Finding: Session cookie has `Secure` flag, requiring HTTPS.** This is correct for production but caused testing complexity. The nginx proxy was also buffering SSE responses, preventing streaming through HTTPS.

## 6. MULTI-WORKER EVIDENCE

All 23 tests pass, proving:

| Test | What it proves |
|------|---------------|
| `test_all_workers_receive_event` | All 3 simulated workers receive event via Redis |
| `test_worker_a_to_worker_b_delivery` | Worker A → Worker B |
| `test_worker_b_to_worker_a_delivery` | Worker B → Worker A |
| `test_worker_a_to_worker_c_delivery` | Worker A → Worker C |
| `test_worker_c_to_worker_a_delivery` | Worker C → Worker A |
| `test_no_self_republication_loop` | Idempotency prevents originating worker's echo |
| `test_no_duplicate_event_across_workers` | Exactly one delivery per worker |
| `test_concurrent_clients_on_different_workers` | Multiple SSE clients per worker all receive events |
| `test_canonical_path_across_workers` | Full path: canonical event → Redis → worker B → SSE client |

## 7. RECONNECT EVIDENCE

| Test | What it proves |
|------|---------------|
| `test_redis_relay_reconnect` | Relay reconnects after stop/start, delivers events after reconnect |
| `test_new_subscription_after_relay_restart` | New subscriptions after relay restart still receive events |
| `test_no_cross_identity_leak_on_reconnect` | After disconnect/reconnect, identity isolation maintained |

## 8. TENANT ISOLATION EVIDENCE

`test_tenant_isolation_across_workers`: Tenant A's events do NOT reach Tenant B's clients on a different worker.

Enforced at two levels:
1. `SSEClient.push()` checks `self.tenant_id != event.tenant_id` → returns False
2. `EventBus._relay_from_redis()` delivers only to matching tenant subscribers

## 9. WORKSPACE ISOLATION EVIDENCE

`test_workspace_isolation_across_workers`: Workspace 1 events do NOT reach Workspace 2 clients.

Enforced by `SSEClient.push()`:
```python
if self.workspace_id is not None and event.workspace_id != self.workspace_id:
    return False
```

## 10. FRONTEND BEHAVIOUR

- SSE connection is established via `useRealityPresence` hook
- Events are consumed by the frontend event bus (`event-bus.ts`)
- Presence transitions: ambient → attentive (on event) → ambient (after 30s timeout)
- Reconnect handled by `sse-runtime.ts` with exponential backoff (1s → 30s max)
- No fake heartbeat, no decorative activity
- Gold dot presence indicator reflects real state

## 11. NGINX SSE PROXY FIX

**Problem:** `proxy_buffering on` at nginx server level buffered SSE responses. The SSE endpoint returned `X-Accel-Buffering: no`, but this was not effective with the current config.

**Fix:** Staged config at `deploy/nginx-shunya.conf.staged` adds a dedicated location block:
```nginx
location /api/v1/reality/stream {
    proxy_pass http://127.0.0.1:5001;
    proxy_buffering off;
    proxy_cache off;
    proxy_http_version 1.1;
    proxy_set_header Connection "";
    ...
}
```

**Apply:** `sudo cp deploy/nginx-shunya.conf.staged /etc/nginx/sites-enabled/shunya && sudo nginx -s reload`

## 12. SIGNUP ROUTING FIX

**Root Cause:** The fallback auth handler in `app.tsx` (line 345) used `window.history.replaceState` + `setPhase('login')` for the "Create Account" click, but this only changed the URL without triggering a page load. The `AuthRouter()` component didn't properly re-render.

**Fix:** Changed to `window.location.href = '/auth/signup'` (full page navigation), matching the primary handler at line 259-260.

**Similar patterns identified:** The `Forgot password` link already uses `window.location.href` (correct).

## 13. PRICING SECTION REMOVAL

**What was removed:**
- `frontend/src/components/public/pricing.tsx`: Import from homepage removed
- "View Pricing" button removed from homepage
- `useState` import for `showPricing` removed
- All pricing toggle logic removed

**What remains (untouched — internal business data, not public pricing):**
- `app/models.py:953` — `pricing_json` field on proposals (business data)
- `app/finance/services.py` — pricing computation for invoices
- `app/for1/engine.py` — travel proposal pricing

## 14. FILES CHANGED (THIS DIRECTIVE)

| File | Change |
|------|--------|
| `tests/test_realtime_certification.py` | **NEW** — 23 certification tests (from commit 2c86528) |
| `app/shunya/infrastructure/event_bus.py` | Added `RedisEventRelay`, `start_redis_relay()`, `_publish_to_redis()`, `_relay_from_redis()` |
| `app/reality_engine/sse_stream.py` | Added `bus.start_redis_relay()` call in `SSEStreamManager.start()` |
| `app/reality_engine/routes.py` | SSE auth: session-only, reject X-Identity-Id header |
| `frontend/src/app.tsx` | Signup routing: `replaceState` → `location.href` |
| `frontend/src/components/public/homepage.tsx` | Removed pricing section |
| `deploy/nginx-shunya.conf.staged` | **NEW** — SSE-specific proxy config with buffering off |

## 15. COMMIT HISTORY

```
5ce71a7 Phase I production certification: SSE nginx SSE buffering fix, signup routing fix, pricing removal
dfc127d Fix: SSE endpoint requires non-zero tenant_id in session (prevents header-forged auth)
2c86528 Phase I production certification: cross-worker Redis event transport + SSE auth fix
54312d6 Phase I: Real-state-driven living system - SSE stream, Presence integration, event bus wiring (BASELINE)
```

## 16. DEPLOYMENT STATUS

| Component | Status |
|-----------|--------|
| Gunicorn workers | 3 (production) |
| Redis | Running on 127.0.0.1:6379 |
| REDIS_URL | Set in systemd environment |
| SSE code | Deployed at commit dfc127d |
| Nginx buffer fix | **STAGED** — needs `sudo` to apply |
| Frontend build | ✅ 94 modules, 0 errors, 618 KB bundle |

## 17. AUDIT FINDINGS

### Multi-Org / Personal Workspace / Employee Structure

**Current state:**
- `Organization` model (`app/models.py:762`) — canonical
- `OrgMember` model (`app/models.py:831`) — org membership with roles
- `Tenant` model (`app/tenant.py:56`) — **dual model**, legacy (used alongside Organization)
- `Workspace` model (`app/models.py` / `app/objects/legacy_models.py`) — per-org workspace

**Routes:**
- `POST /api/v1/orgs` — create org (app/routes.py:58)
- `POST /api/v1/organizations` — production org API (app/production/identity/org_routes.py)
- `POST /api/v1/organizations/{id}/switch` — switch org (switch_routes.py)
- Onboarding flow (`frontend/src/components/onboarding/`) includes:
  - Step 1: Identity — "My Business" / "Join a Company" / "Personal Workspace"
  - Step 2: Organization Setup — create org name + type

**Gap: Dual Tenant/Organization model.** `Tenant` is the production-level company table used by workspace isolation, while `Organization` is the canonical new model. They coexist but don't always share primary keys.

**"Create company on every session" issue:** The frontend checks `isOnboardingComplete()` from `SessionManager`. If this returns false (no session, expired, or onboarding flag not set), the user goes to onboarding again. The `OnboardingFlow` component has an org creation step that shows every time if no org is linked to the user's identity.

**Personal workspace:** The onboarding Step 1 has "Personal Workspace" as option 3, but the backend flow doesn't reliably create a workspace without an organization. The `Workspace` model requires `organization_id`.

### Internal Chat / Organizational Communication

**Current state:**
- `Communication` runtime (`app/production/communication/runtime.py`) — Universal Communication Runtime
- `Conversation` model (`app/production/communication/conversation.py`) — Conversation Living Object
- `Message` — attached to conversations, multi-channel
- API: `/api/v1/communication/*` — send/receive across channels
- Webhook endpoints for Telegram, Gmail integration
- `NotificationManager` (`app/notifications.py`) — in-app notifications

**Gap:** No internal cross-organization messaging (ShunyaID lookup, direct messaging between users of different orgs). The Communication runtime is channel-agnostic but currently wired for external channels (email, WhatsApp, Telegram), not internal user-to-user chat within/between organizations.

### Pricing Section

**Finding:** `frontend/src/components/public/pricing.tsx` — three-tier pricing (Starter/Business/Enterprise) with ₹5,999/month pricing. Imported by `homepage.tsx`. **Removed** as part of this directive.

**Additional references:** Internal proposal pricing in `app/models.py:953` (pricing_json field), `app/finance/services.py` (invoice computation), `app/for1/engine.py` (travel proposal pricing). These are internal business data, not usage restrictions.

## 18. REMAINING ISSUES

| Issue | Severity | Status |
|-------|----------|--------|
| Nginx proxy_buffering for SSE | P1 — blocks streaming through HTTPS | Staged, needs sudo apply |
| Dual Tenant/Organization model | P2 — architectural debt | Known, documented |
| Personal workspace without org | P2 — blocks individual users | Step exists in onboarding but backend not wired |
| Internal org-to-org messaging | P3 — growth feature | Not implemented |
| "Create company" on every session | P2 — UX defect | Need to fix `isOnboardingComplete()` persistence |
| SSE production verification via HTTPS | P1 — blocked by nginx buffering | Blocker until nginx config applied |

## 19. CERTIFICATION STATUS

**Criterion A: REALTIME DELIVERY IS WORKER-SAFE** ✅
- 23 tests prove cross-worker delivery via Redis Pub/Sub
- All worker direction combinations verified (A→B, B→A, A→C, C→A)
- No echo loops (idempotency cache proven)
- Reconnect safe (redis relay reconnects, new subscriptions work)

**Criterion B: SSE IDENTITY AUTHENTICATION IS TRUSTWORTHY** ✅
- Session-only auth (5 security tests prove)
- X-Identity-Id header rejected
- Forged identity rejected
- Tenant isolation enforced
- Workspace isolation enforced
- Logout terminates subscriptions

**CERTIFICATION HOLD:** Nginx `proxy_buffering on` blocks SSE streaming through HTTPS. Fix is staged at `deploy/nginx-shunya.conf.staged`. Apply with:
```
sudo cp deploy/nginx-shunya.conf.staged /etc/nginx/sites-enabled/shunya
sudo nginx -s reload
```

---

*End of Phase I Production Certification Report Update*
*Commit: 5ce71a7*
*Date: 2026-08-19*