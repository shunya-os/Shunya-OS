# FDA33 — Final Deployment / Product Surface Verification

Date: 2026-08-14
Mode: READ-ONLY (no privileged access, no application/config modification)
Revision under test: b1545c9edd9b691f5c1c17cabd02c8783cd03604

---

## 1. TLS / Certificate SANs

All three domains serve a certificate with SANs:
`DNS:app.shunyaos.com, DNS:shunyaos.com, DNS:www.shunyaos.com`

| Domain | SAN check |
|--------|-----------|
| shunyaos.com | PASS — all 3 SANs present |
| www.shunyaos.com | PASS — all 3 SANs present |
| app.shunyaos.com | PASS — all 3 SANs present |

Issuer: Let's Encrypt YE2 · NotBefore Jul 26 2026 · NotAfter Oct 24 2026

## 2. DNS / HTTPS Connectivity

All domains resolve to 217.76.53.46:

| Domain | DNS A record | HTTPS |
|--------|--------------|-------|
| shunyaos.com | 217.76.53.46 | HTTP 200 |
| www.shunyaos.com | 217.76.53.46 (CNAME → shunyaos.com) | HTTP 200 |
| app.shunyaos.com | 217.76.53.46 | HTTP 200 |

## 3. nginx

Verified through externally observable HTTPS behavior (no privileged inspection):
- All three vhosts answer on 443 with valid TLS
- HTTP→HTTPS redirect works for all domains
- Frontend assets served with correct MIME types
- Backend proxying works (API responds through the same origin)

## 4. Frontend Assets

| Asset | Status | Size |
|-------|--------|------|
| index.html (/) | HTTP 200 | 2195 bytes |
| /assets/index-BzGfdFjp.js | HTTP 200 | 455372 bytes |
| Bundle hash (live) | 5a94bd08c970366e8e8290faa5d7b3e8d115c817dede7a88c8a0d3b3c05e1f8d |
| Bundle hash (local frontend/dist) | 5a94bd08c970366e8e8290faa5d7b3e8d115c817dede7a88c8a0d3b3c05e1f8d |
| Match | IDENTICAL — live bundle == local build |

Stale content scan of served page: "Active Objects"=0, "Choose your path"=0, "Coming Soon"=0, "Lorem ipsum"=0.

## 5. API Routing

| Endpoint | Status |
|----------|--------|
| /health | PASS — {"database":"connected","environment":"development","status":"ok"} |
| /ready | PASS — {"database":"ready","service":"shunya","status":"ok"} |
| POST /login (JSON) | PASS — {"success":true,"redirect":"/workspace/"} |

## 6. Database

Inferred from /health (no direct credential access, per directive):
- database: connected
- /ready reports database: ready

## 7. Authentication

- POST /login with demo credentials (demo@shunyaos.com / Demo2024!): HTTP 200, session cookie issued
- Invalid credentials rejected (HTTP 401, {"success":false,"error":"Invalid email or password"})
- Session cookie: HttpOnly, Path=/ (set by Flask)

## 8. Workspace

Authenticated GET /workspace/ returns the SPA shell (HTTP 200, SHUNYA app HTML).
Session preserved across requests (cookie-based).

## 9. Health

`{"database":"connected","environment":"development","request_id":"...","status":"ok","uptime_seconds":...}` — OK

## 10. Ready

`{"database":"ready","environment":"development","service":"shunya","status":"ok"}` — OK

## 11. Production Configuration (observable only)

- environment reported as "development" in /health and /ready — NOT "production"
- Service name: shunya · version: 1.0.0
- Running via gunicorn (3 workers, bind 127.0.0.1:5001, timeout 60)

## 12. Git Truth

| Check | Value |
|-------|-------|
| HEAD | b1545c9edd9b691f5c1c17cabd02c8783cd03604 |
| origin/master | b1545c9edd9b691f5c1c17cabd02c8783cd03604 |
| HEAD == origin/master | YES |
| Branch | master (tracking origin/master, up to date) |

## 13. Deployed Revision == HEAD

- gunicorn started 2026-08-14 11:59:49 from /home/shunya-deploy/shunya_os
- Live bundle hash == local frontend/dist build at HEAD == b1545c9
- git describe: v0.1-runtime-stable-146-gb1545c9
- Deployed revision matches HEAD: PASS

## 14. Stale Bundle Check

- Live JS bundle byte-for-byte identical to local build (SHA-256 match)
- No stale placeholder content in served page
- PASS

---

## Findings

1. **GET /login returns HTTP 500 (CRITICAL — auth redirect target broken)** — Confirmed on both https://shunyaos.com/login and http://127.0.0.1:5001/login. Root cause: `app/auth_routes.py:133` and `:137` call `url_for("serve_index")` but that endpoint no longer exists — it was renamed to `index` (defined at `app/routes.py:149`). Every unauthenticated redirect that targets `/login` (e.g. `/manifest.json` 302, any auth-gated path) lands on a 500 error page. The SPA login page `/auth/login` still works (HTTP 200), and POST /login (JSON) works — but the legacy GET /login route and all redirects to it are broken.
2. **environment=development in production surface** — /health and /ready report environment "development". The observable production configuration is not set to "production". This is a production-configuration finding, not a functional failure. (Observable read-only; root cause requires privileged env/config inspection — out of scope for this read-only gate.)
3. **/manifest.json is auth-gated** — anonymous request to /manifest.json returns HTTP 302 → /login?next=/manifest.json. The PWA manifest file exists at frontend/dist/manifest.json but is not served publicly. PWA installability for anonymous visitors is affected. (Redirect target itself also broken per finding #1.)
4. **Duplicate nginx HTTPS server blocks** — the nginx config contains two HTTPS server blocks for the same server_name: the manually-crafted block (with security headers, proxy timeouts/buffering) and a Certbot-managed block (missing the security headers and timeout optimizations). Requests may be served by either block. Recommendation: consolidate into one block. (Identified from config content; privileged re-inspection needed for definitive fix.)

## FDA33 VERDICT: CONDITIONAL

Deployment chain is mostly verified and functional:
- TLS/DNS/nginx availability: PASS
- Frontend assets: PASS (bundle hash identical live vs local)
- API routing / database / workspace / health / ready: PASS
- Git HEAD == origin/master == deployed revision: PASS
- Stale bundle: PASS

Blocking findings for launch-grade status:
1. GET /login → 500 (broken auth redirect target) — P0, must fix before launch
2. environment=development instead of production — P1
3. /manifest.json not publicly served (302 to broken login) — P1
4. Duplicate nginx HTTPS server blocks (security headers missing in one) — P1

No files modified except this evidence document. No services restarted.
